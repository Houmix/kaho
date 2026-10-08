from datetime import time, timedelta
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Competency, MeetingPoint, Offer, Package, Slot, StudentProfile, User
from .tasks import _normalize_phone


class PhoneNormalizationTests(APITestCase):
    def test_french_numbers_are_converted_for_brevo(self):
        self.assertEqual(_normalize_phone('06 12 34 56 78'), '33612345678')
        self.assertEqual(_normalize_phone('+33 6 12 34 56 78'), '33612345678')
        self.assertEqual(_normalize_phone('0033612345678'), '33612345678')
        self.assertIsNone(_normalize_phone(''))
        self.assertIsNone(_normalize_phone(None))


def make_student(email='eleve@test.fr', hours=10):
    u = User.objects.create_user(username=email, email=email, password='testpass123', first_name='Jean', last_name='Dupont', role='STUDENT')
    p = u.student_profile
    p.purchased_hours = hours
    p.save()
    return u


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class CatalogTests(APITestCase):
    def setUp(self):
        self.permis = Offer.objects.create(name='Permis B', category='PERMIS_B', hours=20, price=1200, includes_lms=True,
                                           validity_months=12, for_code_status='TO_PASS', for_level='BEGINNER')
        self.code = Offer.objects.create(name='Code seul', category='CODE', hours=0, price=30, includes_lms=True,
                                         validity_months=6, for_code_status='TO_PASS')
        self.perf = Offer.objects.create(name='Remise en selle', category='PERFECTIONNEMENT', hours=5, price=250,
                                         for_code_status='OBTAINED', for_level='REFRESH')
        self.recharge = Offer.objects.create(name='Recharge 5h', category='RECHARGE', hours=5, price=240)
        Offer.objects.create(name='Cachée', category='CODE', hours=0, price=1, is_active=False)

    def test_public_catalog_and_category_filter(self):
        self.assertEqual(len(self.client.get('/api/offers/').data), 4)
        self.assertEqual([o['name'] for o in self.client.get('/api/offers/?category=CODE').data], ['Code seul'])

    def test_recommender_matches_profile(self):
        r = self.client.post('/api/offers/recommend/', {'code_status': 'TO_PASS', 'level': 'BEGINNER', 'gearbox': 'AUTO'})
        self.assertEqual(r.data['recommended']['name'], 'Permis B')
        r = self.client.post('/api/offers/recommend/', {'code_status': 'OBTAINED', 'level': 'REFRESH'})
        self.assertEqual(r.data['recommended']['name'], 'Remise en selle')
        names = [r.data['recommended']['name']] + [a['name'] for a in r.data['alternatives']]
        self.assertNotIn('Recharge 5h', names)

    def test_completed_package_credits_hours_and_lms_access_with_expiry(self):
        make_student(hours=0)
        self.client.login(username='eleve@test.fr', password='testpass123')
        r = self.client.post('/api/auth/token/', {'username': 'eleve@test.fr', 'password': 'testpass123'})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
        r = self.client.post('/api/packages/', {'offer': self.permis.id})
        self.assertEqual(r.status_code, 201, r.content)
        pkg = Package.objects.get(pk=r.data['id'])
        st = pkg.student
        self.assertEqual(st.purchased_hours, 0)
        self.assertFalse(st.has_lms_access)

        from django.core import mail
        pkg.status = 'COMPLETED'
        pkg.save()
        st.refresh_from_db()
        self.assertEqual(st.purchased_hours, 20)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Paiement validé', mail.outbox[0].alternatives[0][0])
        self.assertEqual(mail.outbox[0].to, ['eleve@test.fr'])
        self.assertTrue(st.has_lms_access)
        self.assertEqual(st.lms_access_until, timezone.localdate().replace(year=timezone.localdate().year + 1))
        self.assertIsNotNone(pkg.expires_at)
        pkg.note = 'resave'
        pkg.save()
        st.refresh_from_db()
        self.assertEqual(st.purchased_hours, 20)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, BOOKING_CANCEL_DEADLINE_HOURS=48)
class NoShowPolicyTests(APITestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(username='m@kaho.app', email='m@kaho.app', password='pass12345', first_name='Claire', last_name='Martin', role='INSTRUCTOR')
        self.supervisor = User.objects.create_user(username='s@kaho.app', email='s@kaho.app', password='pass12345', first_name='Sam', last_name='Sup', role='SUPERVISOR')
        self.point = MeetingPoint.objects.create(name='Gare', address='1 rue')
        self.student_user = make_student(hours=10)
        self.student = self.student_user.student_profile
        self.soon = self._slot(days=1)
        self.later = self._slot(days=5)

    def _slot(self, days, start=9):
        return Slot.objects.create(instructor=self.instructor, student=self.student, meeting_point=self.point, status='BOOKED',
                                   date=timezone.localdate() + timedelta(days=days), start_time=time(start), end_time=time(start + 1))

    def auth(self, username):
        r = self.client.post('/api/auth/token/', {'username': username, 'password': 'testpass123' if username == 'eleve@test.fr' else 'pass12345'})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def test_cancel_before_deadline_is_free(self):
        self.auth('eleve@test.fr')
        r = self.client.post(f'/api/slots/{self.later.id}/cancel/')
        self.assertEqual(r.data['status'], 'CANCELLED')
        self.student.refresh_from_db()
        self.assertEqual(self.student.used_hours, 0)

    def test_cancel_after_deadline_debits_hour_and_supervisor_can_refund(self):
        self.auth('eleve@test.fr')
        r = self.client.post(f'/api/slots/{self.soon.id}/cancel/')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data['status'], 'CANCELLED_LATE')
        self.assertTrue(r.data['hours_debited'])
        self.student.refresh_from_db()
        self.assertEqual(self.student.used_hours, 1)

        # Instructor cannot refund
        self.auth('m@kaho.app')
        self.assertEqual(self.client.post(f'/api/slots/{self.soon.id}/refund/', {'note': 'x'}).status_code, 403)
        # Supervisor needs a justification
        self.auth('s@kaho.app')
        self.assertEqual(self.client.post(f'/api/slots/{self.soon.id}/refund/', {'note': ''}).status_code, 400)
        r = self.client.post(f'/api/slots/{self.soon.id}/refund/', {'note': 'Certificat médical du 12/10'})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(r.data['hours_refunded'])
        self.student.refresh_from_db()
        self.assertEqual(self.student.used_hours, 0)
        # Only once
        self.assertEqual(self.client.post(f'/api/slots/{self.soon.id}/refund/', {'note': 'again'}).status_code, 400)

    def test_no_show_marks_slot_and_debits(self):
        self.auth('m@kaho.app')
        r = self.client.post(f'/api/slots/{self.later.id}/no_show/', {'note': 'Pas venu'})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data['status'], 'NO_SHOW')
        self.student.refresh_from_db()
        self.assertEqual(self.student.used_hours, 1)
        self.assertFalse(self.later.lesson.attended)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class LogbookAndRatingTests(APITestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(username='m@kaho.app', email='m@kaho.app', password='pass12345', first_name='Claire', last_name='Martin', role='INSTRUCTOR')
        self.other = User.objects.create_user(username='o@kaho.app', email='o@kaho.app', password='pass12345', first_name='Olga', last_name='Autre', role='INSTRUCTOR')
        self.admin = User.objects.create_user(username='a@kaho.app', email='a@kaho.app', password='pass12345', first_name='Al', last_name='Admin', role='ADMIN')
        self.point = MeetingPoint.objects.create(name='Gare', address='1 rue')
        self.student = make_student(hours=10).student_profile
        self.slot = Slot.objects.create(instructor=self.instructor, student=self.student, meeting_point=self.point, status='BOOKED',
                                        date=timezone.localdate() - timedelta(days=1), start_time=time(9), end_time=time(10))
        self.c1 = Competency.objects.get(code='1.1')
        self.c2 = Competency.objects.get(code='1.2')

    def auth(self, username, password='pass12345'):
        r = self.client.post('/api/auth/token/', {'username': username, 'password': password})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def test_competencies_seeded(self):
        self.assertGreaterEqual(Competency.objects.count(), 20)
        self.assertEqual(Competency.objects.filter(group=1).first().code, '1.1')

    def test_instructor_creates_lesson_with_assessments_then_logbook_and_rating(self):
        self.auth('m@kaho.app')
        payload = {
            'slot_id': self.slot.id, 'attended': True, 'weather_conditions': 'Pluie', 'instructor_notes': 'Bon démarrage',
            'assessments': [{'competency': self.c1.id, 'status': 'ACQUIRED'}, {'competency': self.c2.id, 'status': 'IN_PROGRESS'}],
        }
        r = self.client.post('/api/lessons/', payload, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(len(r.data['assessments']), 2)
        self.student.refresh_from_db()
        self.assertEqual(self.student.used_hours, 1)
        # Un seul bilan par créneau
        self.assertEqual(self.client.post('/api/lessons/', payload, format='json').status_code, 400)

        # Un autre moniteur ne peut pas saisir sur ce créneau
        slot2 = Slot.objects.create(instructor=self.instructor, student=self.student, meeting_point=self.point, status='BOOKED',
                                    date=timezone.localdate(), start_time=time(14), end_time=time(15))
        self.auth('o@kaho.app')
        self.assertEqual(self.client.post('/api/lessons/', {'slot_id': slot2.id}, format='json').status_code, 400)

        # Livret élève
        self.auth('eleve@test.fr', 'testpass123')
        lb = self.client.get('/api/student-profiles/my_logbook/').data
        self.assertEqual(lb['progress']['acquired'], 1)
        self.assertEqual(lb['progress']['in_progress'], 1)
        by_code = {c['code']: c['status'] for c in lb['competencies']}
        self.assertEqual(by_code['1.1'], 'ACQUIRED')
        self.assertEqual(by_code['2.1'], 'NOT_COVERED')
        self.assertEqual(len(lb['lessons']), 1)

        # Notation obligatoire : la leçon est à noter, puis notée une seule fois
        to_rate = self.client.get('/api/lessons/to_rate/').data
        self.assertEqual([l['id'] for l in to_rate], [r.data['id']])
        rr = self.client.post(f"/api/lessons/{r.data['id']}/rate/", {'score': 5, 'comment': 'Très pédagogue'})
        self.assertEqual(rr.status_code, 201, rr.content)
        self.assertEqual(self.client.get('/api/lessons/to_rate/').data, [])
        self.assertEqual(self.client.post(f"/api/lessons/{r.data['id']}/rate/", {'score': 1}).status_code, 400)
        self.assertEqual(self.client.post(f"/api/lessons/{r.data['id']}/rate/", {'score': 9}).status_code, 400)

        # Tableau de performance (admin uniquement)
        self.auth('m@kaho.app')
        self.assertEqual(self.client.get('/api/instructors/performance/').status_code, 403)
        self.auth('a@kaho.app')
        rows = {row['name']: row for row in self.client.get('/api/instructors/performance/').data}
        self.assertEqual(rows['Claire Martin']['rating_average'], 5.0)
        self.assertEqual(rows['Claire Martin']['lessons'], 1)
        self.assertEqual(rows['Olga Autre']['rating_count'], 0)
