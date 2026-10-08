from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import ActivityLog, Document, User


def pdf(name='piece.pdf', content=b'%PDF-1.4 x'):
    return SimpleUploadedFile(name, content, content_type='application/pdf')


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, MEDIA_ROOT='/tmp/kaho_test_media')
class DocumentsTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='a@kaho.app', email='a@kaho.app', password='pass12345', first_name='Al', last_name='Admin', role='ADMIN')
        su = User.objects.create_user(username='eleve@test.fr', email='eleve@test.fr', password='testpass123', first_name='Jean', last_name='Dupont', role='STUDENT')
        self.student = su.student_profile

    def auth(self, username, password='pass12345'):
        r = self.client.post('/api/auth/token/', {'username': username, 'password': password})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def upload(self, doc_type, f=None):
        return self.client.post('/api/documents/', {'document_type': doc_type, 'file': f or pdf()}, format='multipart')

    def test_student_uploads_replaces_and_sees_dossier(self):
        self.auth('eleve@test.fr', 'testpass123')
        d = self.client.get('/api/documents/my_dossier/').data
        self.assertFalse(d['dossier']['complete'])
        self.assertEqual(d['dossier']['missing'], 3)

        r = self.upload('IDENTITY')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data['status'], 'PENDING')
        self.assertTrue(r.data['file_name'].startswith('piece') and r.data['file_name'].endswith('.pdf'))
        self.assertIn(f'documents/{self.student.id}/identity/', Document.objects.get(pk=r.data['id']).file.name)
        first_id = r.data['id']
        # Re-dépôt : remplace la même pièce (pas de doublon), repasse en attente
        r = self.upload('IDENTITY', pdf('cni-v2.pdf'))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['id'], first_id)
        self.assertTrue(r.data['file_name'].startswith('cni-v2'))
        self.assertEqual(Document.objects.filter(student=self.student).count(), 1)

        bad = SimpleUploadedFile('x.exe', b'x', content_type='application/octet-stream')
        self.assertEqual(self.upload('CONTRACT', bad).status_code, 400)
        big = SimpleUploadedFile('big.pdf', b'0' * (5 * 1024 * 1024 + 1), content_type='application/pdf')
        self.assertEqual(self.upload('CONTRACT', big).status_code, 400)

        d = self.client.get('/api/documents/my_dossier/').data
        self.assertEqual(d['dossier']['pending'], 1)
        self.assertEqual(d['dossier']['missing'], 2)
        self.assertEqual(ActivityLog.objects.filter(kind='DOCUMENT').count(), 2)

    def test_admin_verifies_and_rejects_with_emails(self):
        self.auth('eleve@test.fr', 'testpass123')
        ident = self.upload('IDENTITY').data['id']
        neph = self.upload('NEPH_CERTIFICATE').data['id']
        contract = self.upload('CONTRACT').data['id']

        self.auth('a@kaho.app')
        self.assertEqual(self.client.get('/api/admin/documents/?status=PENDING').data['count'], 3)
        self.assertIn('documents', [a['kind'] for a in self.client.get('/api/admin/overview/').data['alerts']])
        self.assertEqual(self.client.get('/api/admin/students/?filter=documents').data['count'], 1)

        mail.outbox.clear()
        r = self.client.post(f'/api/admin/documents/{neph}/reject/', {'note': ''})
        self.assertEqual(r.status_code, 400)
        r = self.client.post(f'/api/admin/documents/{neph}/reject/', {'note': 'Document illisible'})
        self.assertEqual(r.data['status'], 'REJECTED')
        self.assertIn('redéposer', mail.outbox[-1].subject)
        self.assertIn('Document illisible', mail.outbox[-1].alternatives[0][0])

        self.client.post(f'/api/admin/documents/{ident}/verify/')
        r = self.client.post(f'/api/admin/documents/{contract}/verify/')
        self.assertEqual(r.data['status'], 'VERIFIED')
        self.assertEqual(r.data['verified_by_name'], 'Al Admin')
        self.assertIn('validée', mail.outbox[-1].subject)
        self.assertEqual(self.client.get('/api/admin/students/?filter=incomplete').data['count'], 1)

        # L'élève redépose la pièce refusée, l'admin la valide → dossier complet
        self.auth('eleve@test.fr', 'testpass123')
        self.assertEqual(self.upload('NEPH_CERTIFICATE').data['status'], 'PENDING')
        # Une pièce validée ne peut être ni remplacée ni supprimée par l'élève
        self.assertEqual(self.upload('IDENTITY').status_code, 400)
        self.assertEqual(self.client.delete(f'/api/documents/{ident}/').status_code, 403)
        self.auth('a@kaho.app')
        self.client.post(f'/api/admin/documents/{neph}/verify/')
        self.assertIn('dossier est maintenant complet', mail.outbox[-1].alternatives[0][0])
        self.assertEqual(self.client.get('/api/admin/students/?filter=incomplete').data['count'], 0)
        self.assertTrue(self.client.get(f'/api/admin/students/{self.student.id}/overview/').data['dossier']['complete'])

    def test_students_cannot_see_each_other_documents(self):
        self.auth('eleve@test.fr', 'testpass123')
        doc_id = self.upload('IDENTITY').data['id']
        User.objects.create_user(username='o@test.fr', email='o@test.fr', password='testpass123', role='STUDENT')
        self.auth('o@test.fr', 'testpass123')
        self.assertEqual(self.client.get('/api/documents/').data, [])
        self.assertEqual(self.client.get(f'/api/documents/{doc_id}/').status_code, 404)
        self.assertEqual(self.client.get('/api/admin/documents/').status_code, 403)
