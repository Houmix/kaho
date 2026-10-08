from datetime import time, timedelta
from urllib.parse import parse_qs, urlparse

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import (
    Availability, Competency, InstructorApplication, Lesson, LessonRating, MeetingPoint, Offer, Package, Slot,
    StudentProfile, User,
)


def pdf(name='doc.pdf'):
    return SimpleUploadedFile(name, b'%PDF-1.4 test', content_type='application/pdf')


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, MEDIA_ROOT='/tmp/kaho_test_media')
class BackOfficeTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='a@kaho.app', email='a@kaho.app', password='pass12345', first_name='Al', last_name='Admin', role='ADMIN')
        self.instructor = User.objects.create_user(username='m@kaho.app', email='m@kaho.app', password='pass12345', first_name='Claire', last_name='Martin', role='INSTRUCTOR')
        Availability.objects.create(instructor=self.instructor, weekday=0, start_time=time(9), end_time=time(12))
        self.point = MeetingPoint.objects.create(name='Gare', address='1 rue')
        self.offer = Offer.objects.create(name='Pack 10h', hours=10, price=450)
        su = User.objects.create_user(username='eleve@test.fr', email='eleve@test.fr', password='testpass123', first_name='Jean', last_name='Dupont', role='STUDENT')
        self.student = su.student_profile
        self.pkg = Package.objects.create(student=self.student, offer=self.offer, hours_purchased=10, amount_paid=450)

    def auth(self, username, password='pass12345'):
        r = self.client.post('/api/auth/token/', {'username': username, 'password': password})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def test_only_supervisor_or_admin_can_use_back_office(self):
        self.auth('m@kaho.app')
        for url in ('/api/admin/overview/', '/api/admin/search/?q=jean', '/api/admin/students/', '/api/admin/instructors/', '/api/admin/applications/', '/api/admin/ratings/'):
            self.assertEqual(self.client.get(url).status_code, 403, url)
        self.auth('eleve@test.fr', 'testpass123')
        self.assertEqual(self.client.get('/api/admin/overview/').status_code, 403)

    def test_overview_kpis_and_alerts(self):
        self.auth('a@kaho.app')
        d = self.client.get('/api/admin/overview/').data
        self.assertEqual(d['unpaid'], {'count': 1, 'amount': 450.0})
        self.assertEqual(d['month']['revenue'], 0.0)
        self.assertEqual(d['occupancy']['opened_hours'], 3.0)
        self.assertIn('unpaid', [a['kind'] for a in d['alerts']])

        self.client.post(f'/api/admin/packages/{self.pkg.id}/mark_paid/', {'note': 'virement'})
        d = self.client.get('/api/admin/overview/').data
        self.assertEqual(d['month']['revenue'], 450.0)
        self.assertEqual(d['unpaid']['count'], 0)
        self.student.refresh_from_db()
        self.assertEqual(self.student.purchased_hours, 10)
        self.assertEqual(self.client.post(f'/api/admin/packages/{self.pkg.id}/mark_paid/').status_code, 400)

    def test_global_search(self):
        self.auth('a@kaho.app')
        d = self.client.get('/api/admin/search/?q=dup').data
        self.assertEqual(d['students'][0]['name'], 'Jean Dupont')
        self.assertEqual(self.client.get('/api/admin/search/?q=mart').data['instructors'][0]['name'], 'Claire Martin')
        self.assertEqual(self.client.get(f'/api/admin/search/?q=%23{self.pkg.id}').data['packages'][0]['id'], self.pkg.id)
        self.assertEqual(self.client.get('/api/admin/search/?q=j').data['students'], [])

    def test_student_list_filters_overview_and_manual_hours(self):
        self.auth('a@kaho.app')
        self.assertEqual(self.client.get('/api/admin/students/?filter=unpaid').data['count'], 1)
        self.assertEqual(self.client.get('/api/admin/students/?q=zzz').data['count'], 0)
        ov = self.client.get(f'/api/admin/students/{self.student.id}/overview/').data
        self.assertEqual(ov['student']['user']['email'], 'eleve@test.fr')
        self.assertEqual(len(ov['packages']), 1)

        r = self.client.post(f'/api/admin/students/{self.student.id}/adjust_hours/', {'hours': 2, 'note': 'Geste commercial'})
        self.assertEqual(r.status_code, 201, r.content)
        self.student.refresh_from_db()
        self.assertEqual(self.student.purchased_hours, 2)
        self.assertEqual(self.client.post(f'/api/admin/students/{self.student.id}/adjust_hours/', {'hours': 2}).status_code, 400)

        r = self.client.patch(f'/api/admin/students/{self.student.id}/update_profile/', {'referent_instructor': self.instructor.id, 'ready_for_exam': True})
        self.assertEqual(r.data['referent_instructor_name'], 'Claire Martin')
        self.assertTrue(r.data['ready_for_exam'])

    def test_admin_creates_instructor_and_invite_sets_password(self):
        self.auth('a@kaho.app')
        r = self.client.post('/api/admin/instructors/', {'email': 'New@Kaho.app', 'first_name': 'Nina', 'last_name': 'Neuve', 'phone': '0612345678', 'hourly_rate': '35', 'gearbox': 'AUTO'})
        self.assertEqual(r.status_code, 201, r.content)
        self.assertFalse(r.data['has_password'])
        self.assertEqual(r.data['profile']['gearbox'], 'AUTO')
        self.assertEqual(float(r.data['profile']['hourly_rate']), 35.0)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Créer mon mot de passe', mail.outbox[0].alternatives[0][0])
        link = next(l for l in mail.outbox[0].body.split() if l.startswith('http'))
        q = parse_qs(urlparse(link).query)
        self.assertEqual(q['invite'], ['1'])

        # Le nouveau moniteur crée son mot de passe via le lien, puis peut se connecter
        self.client.credentials()
        r = self.client.post('/api/auth/password-reset/confirm/', {'uid': q['uid'][0], 'token': q['token'][0], 'new_password': 'monmotdepasse1'})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data['user']['role'], 'INSTRUCTOR')
        self.assertEqual(self.client.post('/api/auth/token/', {'username': 'new@kaho.app', 'password': 'monmotdepasse1'}).status_code, 200)

        # Doublon refusé
        self.auth('a@kaho.app')
        self.assertEqual(self.client.post('/api/admin/instructors/', {'email': 'new@kaho.app', 'first_name': 'X', 'last_name': 'Y'}).status_code, 400)

    def test_public_application_then_admin_approval(self):
        r = self.client.post('/api/instructor-applications/', {
            'first_name': 'Paul', 'last_name': 'Candidat', 'email': 'paul@test.fr', 'phone': '0611111111', 'gearbox': 'MANUAL',
            'message': 'Motivé', 'diploma': pdf('diplome.pdf'), 'driving_license': pdf('permis.pdf'),
        }, format='multipart')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(len(mail.outbox), 1)  # accusé de réception
        app = InstructorApplication.objects.get(email='paul@test.fr')
        self.assertEqual(app.status, 'PENDING')

        # Pièce manquante / mauvais format refusés
        r = self.client.post('/api/instructor-applications/', {'first_name': 'A', 'last_name': 'B', 'email': 'ab@test.fr', 'diploma': pdf()}, format='multipart')
        self.assertEqual(r.status_code, 400)
        bad = SimpleUploadedFile('virus.exe', b'x', content_type='application/octet-stream')
        r = self.client.post('/api/instructor-applications/', {'first_name': 'A', 'last_name': 'B', 'email': 'ab@test.fr', 'diploma': bad, 'driving_license': pdf()}, format='multipart')
        self.assertIn('Format non accepté', str(r.data['diploma'][0]))
        # Doublon en cours refusé
        r = self.client.post('/api/instructor-applications/', {'first_name': 'Paul', 'last_name': 'C', 'email': 'paul@test.fr', 'diploma': pdf(), 'driving_license': pdf()}, format='multipart')
        self.assertEqual(r.status_code, 400)

        self.auth('a@kaho.app')
        self.assertEqual(self.client.get('/api/admin/applications/?status=PENDING').data['count'], 1)
        mail.outbox.clear()
        r = self.client.post(f'/api/admin/applications/{app.id}/approve/', {'hourly_rate': 30})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data['status'], 'APPROVED')
        user = User.objects.get(email='paul@test.fr')
        self.assertEqual(user.role, 'INSTRUCTOR')
        self.assertEqual(user.instructor_profile.gearbox, 'MANUAL')
        self.assertEqual(float(user.instructor_profile.hourly_rate), 30.0)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Bienvenue', mail.outbox[0].subject)
        self.assertEqual(self.client.post(f'/api/admin/applications/{app.id}/approve/').status_code, 400)

    def test_rejection_sends_email(self):
        app = InstructorApplication.objects.create(first_name='Z', last_name='Z', email='z@test.fr', diploma=pdf(), driving_license=pdf())
        self.auth('a@kaho.app')
        r = self.client.post(f'/api/admin/applications/{app.id}/reject/', {'note': 'Diplôme non valide', 'notify_note': 1})
        self.assertEqual(r.data['status'], 'REJECTED')
        self.assertIn('Diplôme non valide', mail.outbox[-1].alternatives[0][0])
        self.assertFalse(User.objects.filter(email='z@test.fr').exists())

    def test_rating_moderation_reply_visible_to_student_and_hidden_excluded(self):
        slot = Slot.objects.create(instructor=self.instructor, student=self.student, meeting_point=self.point, status='BOOKED',
                                   date=timezone.localdate() - timedelta(days=1), start_time=time(9), end_time=time(10))
        lesson = Lesson.objects.create(slot=slot, student=self.student)
        rating = LessonRating.objects.create(lesson=lesson, score=2, comment='Trop rapide')

        self.auth('a@kaho.app')
        self.assertEqual(self.client.get('/api/admin/ratings/?unanswered=1').data['count'], 1)
        r = self.client.patch(f'/api/admin/ratings/{rating.id}/', {'reply': 'Merci, nous en avons parlé avec Claire.'})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(self.client.get('/api/admin/ratings/?unanswered=1').data['count'], 0)
        self.assertEqual(self.client.patch(f'/api/admin/ratings/{rating.id}/', {'score': 5}).data['score'], 2)  # score non modifiable

        self.auth('eleve@test.fr', 'testpass123')
        lb = self.client.get('/api/student-profiles/my_logbook/').data
        self.assertEqual(lb['lessons'][0]['rating']['reply'], 'Merci, nous en avons parlé avec Claire.')

        self.auth('a@kaho.app')
        self.client.patch(f'/api/admin/ratings/{rating.id}/', {'is_hidden': True})
        self.assertIsNone(self.client.get('/api/admin/overview/').data['rating']['average'])
