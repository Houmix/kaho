"""Bloc 8 : multi-admins (gérant / gestionnaire), fiche élève 360° (statut, règlements, heures, LMS, contrat, réservation),
fiche moniteur (absences à valider, réattribution, heures), actions groupées, exports, audit."""
from datetime import timedelta

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import ActivityLog, Availability, MeetingPoint, Offer, Package, Slot, StudentProfile, Unavailability, User


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, MEDIA_ROOT='/tmp/kaho_test_media', BOOKING_MIN_NOTICE_HOURS=0)
class Bloc8Tests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='o@kaho.app', email='o@kaho.app', password='pass12345', first_name='Oria', last_name='Owner', role='OWNER')
        self.admin = User.objects.create_user(username='a@kaho.app', email='a@kaho.app', password='pass12345', first_name='Al', last_name='Admin', role='ADMIN')
        self.ins = User.objects.create_user(username='m@kaho.app', email='m@kaho.app', password='pass12345', first_name='Marc', last_name='Moniteur', role='INSTRUCTOR')
        self.ins2 = User.objects.create_user(username='m2@kaho.app', email='m2@kaho.app', password='pass12345', first_name='Mia', last_name='Moniteur', role='INSTRUCTOR')
        for ins in (self.ins, self.ins2):
            ins.instructor_profile.hourly_rate = 20
            ins.instructor_profile.save()
            for wd in range(7):
                Availability.objects.create(instructor=ins, weekday=wd, start_time='08:00', end_time='20:00')
        su = User.objects.create_user(username='eleve@test.fr', email='eleve@test.fr', password='testpass123', first_name='Jean', last_name='Dupont', role='STUDENT')
        self.student = su.student_profile
        self.student.phone = '0612345678'
        self.student.save()
        self.mp = MeetingPoint.objects.create(name='Gare', address='1 place de la gare')
        self.offer = Offer.objects.create(name='Pack 10 h', hours=10, price=450, includes_lms=True, validity_months=6)

    def auth(self, username):
        r = self.client.post('/api/auth/token/', {'username': username, 'password': 'pass12345'})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    # ----- §10 rôles -----

    def test_owner_only_finance_and_team(self):
        self.auth('a@kaho.app')
        self.assertEqual(self.client.get('/api/admin/sales/').status_code, 403)
        self.assertEqual(self.client.get('/api/admin/payroll/').status_code, 403)
        self.assertEqual(self.client.get('/api/admin/team/').status_code, 403)
        self.assertEqual(self.client.get('/api/admin/overview/').status_code, 200)  # exploitation OK
        self.assertEqual(self.client.get('/api/admin/students/').status_code, 200)

        self.auth('o@kaho.app')
        self.assertEqual(self.client.get('/api/admin/sales/').status_code, 200)
        team = self.client.get('/api/admin/team/').data
        self.assertEqual({t['email'] for t in team}, {'o@kaho.app', 'a@kaho.app'})

        mail.outbox.clear()
        r = self.client.post('/api/admin/team/', {'email': 'new@kaho.app', 'first_name': 'Nina', 'last_name': 'Gest', 'role': 'ADMIN'})
        self.assertEqual(r.status_code, 201, r.content)
        self.assertFalse(r.data['has_password'])
        self.assertIn('reset-password?uid=', mail.outbox[-1].alternatives[0][0])
        self.assertIn('invite=1', mail.outbox[-1].alternatives[0][0])
        new_id = r.data['id']
        # promotion gestionnaire → gérant, puis désactivation
        self.assertEqual(self.client.patch(f'/api/admin/team/{new_id}/', {'role': 'OWNER'}).data['role'], 'OWNER')
        self.assertEqual(self.client.patch(f'/api/admin/team/{new_id}/', {'is_active': False}).data['is_active'], False)
        # on ne peut pas se retirer ses propres droits, ni supprimer le dernier gérant
        self.assertEqual(self.client.patch(f'/api/admin/team/{self.owner.id}/', {'role': 'ADMIN'}).status_code, 400)
        self.assertEqual(ActivityLog.objects.filter(kind='TEAM').count(), 3)

    # ----- §11.1 élève -----

    def test_student_status_and_hours_adjustments(self):
        self.auth('a@kaho.app')
        sid = self.student.id
        r = self.client.post(f'/api/admin/students/{sid}/set_status/', {'status': 'CODE'})
        self.assertEqual(r.data['status'], 'CODE')
        self.assertEqual(self.client.post(f'/api/admin/students/{sid}/set_status/', {'status': 'XX'}).status_code, 400)
        self.assertEqual(self.client.get('/api/admin/students/?status=CODE').data['count'], 1)
        # archivé : masqué par défaut, visible avec include_archived, fiche toujours accessible
        self.client.post(f'/api/admin/students/{sid}/set_status/', {'status': 'ARCHIVED'})
        self.assertEqual(self.client.get('/api/admin/students/').data['count'], 0)
        self.assertEqual(self.client.get('/api/admin/students/?include_archived=1').data['count'], 1)
        self.assertEqual(self.client.get(f'/api/admin/students/{sid}/overview/').status_code, 200)

        self.client.post(f'/api/admin/students/{sid}/adjust_hours/', {'hours': 5, 'note': 'geste commercial'})
        r = self.client.post(f'/api/admin/students/{sid}/debit_hours/', {'hours': 2, 'note': 'erreur de saisie'})
        self.assertEqual(r.data['remaining_hours'], 3)
        self.assertEqual(self.client.post(f'/api/admin/students/{sid}/debit_hours/', {'hours': 10, 'note': 'x'}).status_code, 400)

        r = self.client.post(f'/api/admin/students/{sid}/adjust_lms/', {'months': 3, 'note': 'offert'})
        self.assertTrue(r.data['has_lms_access'])
        self.assertIsNotNone(r.data['lms_access_until'])
        r = self.client.post(f'/api/admin/students/{sid}/adjust_lms/', {'enabled': False, 'note': 'fin'})
        self.assertFalse(r.data['has_lms_access'])
        kinds = list(ActivityLog.objects.filter(student=self.student).values_list('kind', flat=True))
        self.assertEqual(kinds.count('STATUS'), 2)
        self.assertEqual(kinds.count('LMS'), 2)
        self.assertTrue(all(e.actor == self.admin for e in ActivityLog.objects.filter(student=self.student)))

    def test_record_manual_payment_creates_receipt(self):
        self.auth('a@kaho.app')
        sid = self.student.id
        mail.outbox.clear()
        r = self.client.post(f'/api/admin/students/{sid}/record_payment/', {'offer': self.offer.id, 'method': 'CASH', 'note': 'reçu en main propre'})
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data['status'], 'COMPLETED')
        self.assertEqual(r.data['payment_method'], 'CASH')
        self.assertTrue(r.data['invoice_number'].startswith('KAHO-'))
        self.student.refresh_from_db()
        self.assertEqual(self.student.purchased_hours, 10)
        self.assertTrue(self.student.has_lms_access)
        self.assertIn('validé', mail.outbox[-1].subject)
        # reçu PDF (facture acquittée)
        r = self.client.get(f"/api/invoices/{r.data['invoice_id']}/pdf/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.content.startswith(b'%PDF'))
        # montant libre (acompte CPF)
        r = self.client.post(f'/api/admin/students/{sid}/record_payment/', {'amount': 120, 'hours': 0, 'label': 'Acompte', 'method': 'CPF'})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['display_label'], 'Acompte')
        self.assertEqual(self.client.post(f'/api/admin/students/{sid}/record_payment/', {'amount': 10, 'method': 'BITCOIN'}).status_code, 400)

    def test_payment_link_requires_stripe(self):
        self.auth('a@kaho.app')
        r = self.client.post(f'/api/admin/students/{self.student.id}/payment_link/', {'offer': self.offer.id, 'channel': 'both'})
        self.assertEqual(r.status_code, 400)
        self.assertIn('STRIPE_SECRET_KEY', r.data['detail'])
        self.assertEqual(Package.objects.count(), 0)  # rien ne traîne

    def test_contract_pdf_and_admin_upload(self):
        self.auth('a@kaho.app')
        sid = self.student.id
        Package.objects.create(student=self.student, offer=self.offer, hours_purchased=10, amount_paid=450, status='PENDING')
        r = self.client.get(f'/api/admin/students/{sid}/contract/')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.content.startswith(b'%PDF'))
        self.assertEqual(ActivityLog.objects.filter(kind='CONTRACT').count(), 1)
        r = self.client.post(f'/api/admin/students/{sid}/upload_document/', {'document_type': 'CONTRACT', 'file': SimpleUploadedFile('contrat.pdf', b'%PDF-1.4 x', content_type='application/pdf')}, format='multipart')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data['status'], 'VERIFIED')
        self.assertEqual(r.data['verified_by_name'], 'Al Admin')
        self.assertEqual(self.client.post(f'/api/admin/students/{sid}/upload_document/', {'document_type': 'CONTRACT', 'file': SimpleUploadedFile('x.exe', b'x')}, format='multipart').status_code, 400)

    def test_admin_books_for_student(self):
        self.auth('a@kaho.app')
        sid = self.student.id
        day = (timezone.localdate() + timedelta(days=2)).isoformat()
        body = {'instructor': self.ins.id, 'meeting_point': self.mp.id, 'date': day, 'start_time': '10:00', 'end_time': '11:00'}
        self.assertEqual(self.client.post(f'/api/admin/students/{sid}/book/', body).status_code, 400)  # pas de crédit
        mail.outbox.clear()
        r = self.client.post(f'/api/admin/students/{sid}/book/', {**body, 'force': True})
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data['status'], 'BOOKED')
        self.assertIn('confirmée', mail.outbox[-1].subject.lower())
        self.assertEqual(self.client.post(f'/api/admin/students/{sid}/book/', {**body, 'force': True}).status_code, 409)

    # ----- §11.2 moniteur -----

    def test_absence_request_blocks_planning_until_reviewed(self):
        self.auth('m@kaho.app')
        from datetime import datetime, time
        start = timezone.make_aware(datetime.combine(timezone.localdate() + timedelta(days=3), time(10, 0)))
        r = self.client.post('/api/unavailabilities/', {'start': start.isoformat(), 'end': (start + timedelta(hours=4)).isoformat(), 'reason': 'Médecin'})
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data['status'], 'PENDING')
        uid = r.data['id']
        day = timezone.localtime(start).date().isoformat()
        free = self.client.get(f'/api/slots/free/?date={day}&instructor={self.ins.id}').data
        blocked_hour = timezone.localtime(start).strftime('%H:%M')
        self.assertNotIn(blocked_hour, [w['start_time'] for w in free])

        self.auth('a@kaho.app')
        self.assertIn('absences', [a['kind'] for a in self.client.get('/api/admin/overview/').data['alerts']])
        self.assertEqual(self.client.get('/api/admin/absences/?status=PENDING').data['count'], 1)
        mail.outbox.clear()
        r = self.client.post(f'/api/admin/absences/{uid}/reject/', {'note': 'journée chargée'})
        self.assertEqual(r.data['status'], 'REJECTED')
        self.assertIn('refusée', mail.outbox[-1].subject)
        free = self.client.get(f'/api/slots/free/?date={day}&instructor={self.ins.id}').data
        self.assertIn(blocked_hour, [w['start_time'] for w in free])
        # saisie directe par l'école → validée d'office
        r = self.client.post(f'/api/admin/instructors/{self.ins.id}/add_absence/', {'start': start.isoformat(), 'end': (start + timedelta(hours=2)).isoformat(), 'reason': 'Formation'})
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data['status'], 'APPROVED')
        self.assertEqual(len(self.client.get(f'/api/admin/instructors/{self.ins.id}/absences/').data), 2)

    def test_bulk_reassign_and_hours_breakdown(self):
        day = timezone.localdate() + timedelta(days=3)
        s1 = Slot.objects.create(instructor=self.ins, student=self.student, meeting_point=self.mp, date=day, start_time='09:00', end_time='10:00', status='BOOKED')
        s2 = Slot.objects.create(instructor=self.ins, student=self.student, meeting_point=self.mp, date=day, start_time='11:00', end_time='12:00', status='BOOKED')
        Slot.objects.create(instructor=self.ins2, meeting_point=self.mp, date=day, start_time='11:00', end_time='12:00', status='BOOKED')  # conflit pour s2
        self.auth('a@kaho.app')
        mail.outbox.clear()
        r = self.client.post(f'/api/admin/instructors/{self.ins.id}/reassign/', {'start': day.isoformat(), 'end': day.isoformat(), 'target': self.ins2.id})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual([m['id'] for m in r.data['moved']], [s1.id])
        self.assertEqual(r.data['failed'][0]['id'], s2.id)
        s1.refresh_from_db()
        self.assertEqual(s1.instructor, self.ins2)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(ActivityLog.objects.filter(kind='PLANNING').count(), 1)

        # heures : faites / absences / annulées hors délai / à venir
        past = timezone.localdate() - timedelta(days=1)
        done = Slot.objects.create(instructor=self.ins, student=self.student, meeting_point=self.mp, date=past, start_time='09:00', end_time='10:00', status='BOOKED')
        done.refresh_from_db()
        from .models import Lesson
        Lesson.objects.create(slot=done, student=self.student, attended=True)
        Slot.objects.create(instructor=self.ins, student=self.student, meeting_point=self.mp, date=past, start_time='14:00', end_time='15:30', status='NO_SHOW')
        Slot.objects.create(instructor=self.ins, student=self.student, meeting_point=self.mp, date=past, start_time='16:00', end_time='17:00', status='CANCELLED_LATE')
        r = self.client.get(f'/api/admin/instructors/{self.ins.id}/hours/?month={past:%Y-%m}').data
        self.assertEqual(r['summary']['done']['hours'], 1)
        self.assertEqual(r['summary']['no_show']['hours'], 1.5)
        self.assertEqual(r['summary']['cancelled_late']['count'], 1)
        self.assertEqual(r['amount'], 20.0)
        # zones sur la fiche
        r = self.client.patch(f'/api/admin/instructors/{self.ins.id}/', {'zones': 'Lyon 3, Villeurbanne'})
        self.assertEqual(r.data['profile']['zones'], 'Lyon 3, Villeurbanne')

    # ----- §11.3 actions groupées, exports, audit -----

    def test_bulk_actions_and_exports(self):
        su2 = User.objects.create_user(username='e2@test.fr', email='e2@test.fr', password='x', first_name='Lina', last_name='Martin', role='STUDENT')
        ids = [self.student.id, su2.student_profile.id]
        self.auth('a@kaho.app')
        mail.outbox.clear()
        r = self.client.post('/api/admin/students/bulk/', {'ids': ids, 'action': 'message', 'subject': 'Fermeture', 'body': 'Bonjour {prenom}, fermeture le 1er mai.', 'channel': 'email'}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(len(mail.outbox), 2)
        self.assertTrue(any('Bonjour Jean' in m.alternatives[0][0] for m in mail.outbox))
        r = self.client.post('/api/admin/students/bulk/', {'ids': ids, 'action': 'status', 'status': 'REGISTERED'}, format='json')
        self.assertEqual(StudentProfile.objects.filter(status='REGISTERED').count(), 2)
        mail.outbox.clear()
        r = self.client.post('/api/admin/students/bulk/', {'ids': ids, 'action': 'remind_documents'}, format='json')
        self.assertIn('2 élève', r.data['detail'])
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(self.client.post('/api/admin/students/bulk/', {'ids': [], 'action': 'status'}, format='json').status_code, 400)

        r = self.client.get('/api/admin/students/export/?status=REGISTERED')
        self.assertEqual(r['Content-Type'], 'text/csv; charset=utf-8')
        body = r.content.decode('utf-8-sig')
        self.assertIn('Dupont;Jean', body)
        self.assertIn('Inscrit / NEPH en attente', body)

        # audit : filtre par auteur, export
        r = self.client.get(f'/api/admin/activity/?actor={self.admin.id}').data
        self.assertTrue(r['count'] >= 3)
        self.assertTrue(all(e['actor_name'] == 'Al Admin' for e in r['results']))
        actors = self.client.get('/api/admin/activity/actors/').data
        self.assertIn('Al Admin', [a['name'] for a in actors])
        r = self.client.get('/api/admin/activity/export/?admin_only=1')
        self.assertIn('Al Admin', r.content.decode('utf-8-sig'))
