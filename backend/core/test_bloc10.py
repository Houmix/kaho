from datetime import datetime, time, timedelta

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Availability, CancellationPolicy, MeetingPoint, Slot, User


def _user(email, role, **kw):
    return User.objects.create_user(username=email, email=email, password='pass12345', first_name=email.split('@')[0].title(), last_name='T', role=role, **kw)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class CancellationRulesAndAssessmentLockTests(APITestCase):
    def setUp(self):
        self.instructor = _user('moni@kaho.app', 'INSTRUCTOR')
        self.admin = _user('admin@kaho.app', 'ADMIN')
        self.supervisor = _user('sup@kaho.app', 'SUPERVISOR')
        self.student_user = _user('eleve@kaho.app', 'STUDENT')
        self.student = self.student_user.student_profile
        self.student.purchased_hours = 10
        self.student.save()
        self.point = MeetingPoint.objects.create(name='Gare', address='1 rue')

    def auth(self, email):
        r = self.client.post('/api/auth/token/', {'username': email, 'password': 'pass12345'})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def slot_in(self, hours, minutes_long=60):
        start = timezone.localtime() + timedelta(hours=hours)
        start = start.replace(second=0, microsecond=0)
        end = start + timedelta(minutes=minutes_long)
        return Slot.objects.create(instructor=self.instructor, student=self.student, meeting_point=self.point, status='BOOKED',
                                   date=start.date(), start_time=start.time(), end_time=end.time())

    # ----- Règles d'annulation -----

    def test_default_policy_readable_by_student_and_editable_only_by_backoffice(self):
        self.auth('eleve@kaho.app')
        r = self.client.get('/api/cancellation-policy/')
        self.assertEqual(r.data['notice_hours'], 48)
        self.assertEqual(self.client.put('/api/cancellation-policy/', {'notice_hours': 1}, format='json').status_code, 403)
        self.auth('sup@kaho.app')
        r = self.client.put('/api/cancellation-policy/', {'notice_hours': 24, 'late_penalty': 'FEE', 'late_fee': '15.00'}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(CancellationPolicy.current().notice_hours, 24)
        # Frais obligatoires si la pénalité en prévoit
        r = self.client.put('/api/cancellation-policy/', {'late_penalty': 'FEE', 'late_fee': '0'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_reason_is_mandatory_for_student(self):
        slot = self.slot_in(100)
        self.auth('eleve@kaho.app')
        self.assertEqual(self.client.post(f'/api/slots/{slot.id}/cancel/', {'reason': '  '}, format='json').status_code, 400)
        r = self.client.post(f'/api/slots/{slot.id}/cancel/', {'reason': 'Malade'}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data['status'], 'CANCELLED')
        self.assertEqual(r.data['cancel_reason'], 'Malade')

    def test_notice_period_is_configurable_and_early_cancel_gives_hour_back(self):
        CancellationPolicy.objects.create(notice_hours=6)
        slot = self.slot_in(10)  # > 6 h : gratuit alors qu'il serait tardif avec 48 h
        self.auth('eleve@kaho.app')
        r = self.client.post(f'/api/slots/{slot.id}/cancel/', {'reason': 'Travail'}, format='json')
        self.assertEqual(r.data['status'], 'CANCELLED')
        self.student.refresh_from_db()
        self.assertEqual(self.student.used_hours, 0)
        self.assertEqual(self.student.bookable_hours, 10)

    def test_late_cancellation_fee_policy_keeps_hour_and_charges_fee_then_waiver(self):
        CancellationPolicy.objects.create(notice_hours=48, late_penalty='FEE', late_fee=20)
        slot = self.slot_in(5)
        self.auth('eleve@kaho.app')
        r = self.client.post(f'/api/slots/{slot.id}/cancel/', {'reason': 'Imprévu'}, format='json')
        self.assertEqual(r.data['status'], 'CANCELLED_LATE')
        self.assertFalse(r.data['hours_debited'])
        self.assertEqual(float(r.data['cancellation_fee']), 20.0)
        self.student.refresh_from_db()
        self.assertEqual(self.student.used_hours, 0)
        # Dérogation : lève les frais, justificatif requis
        self.auth('sup@kaho.app')
        self.assertEqual(self.client.post(f'/api/slots/{slot.id}/refund/', {'note': ''}, format='json').status_code, 400)
        r = self.client.post(f'/api/slots/{slot.id}/refund/', {'note': 'Certificat médical'}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(float(r.data['cancellation_fee']), 0)

    def test_late_cancellation_debit_policy_and_waiver_restores_hour(self):
        slot = self.slot_in(5)
        self.auth('eleve@kaho.app')
        r = self.client.post(f'/api/slots/{slot.id}/cancel/', {'reason': 'Imprévu'}, format='json')
        self.assertTrue(r.data['hours_debited'])
        self.auth('admin@kaho.app')
        self.assertEqual(self.client.post(f'/api/slots/{slot.id}/refund/', {'note': 'Justificatif'}, format='json').status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.used_hours, 0)

    def test_slot_exposes_free_cancel_deadline(self):
        slot = self.slot_in(100)
        self.auth('eleve@kaho.app')
        r = self.client.get(f'/api/slots/{slot.id}/')
        self.assertIsNotNone(r.data['free_cancel_until'])

    # ----- Verrouillage du bilan -----

    def _lesson_payload(self, slot):
        return {'slot_id': slot.id, 'attended': True, 'instructor_notes': 'RAS', 'assessments': []}

    def test_assessment_locked_until_last_ten_minutes(self):
        self.auth('moni@kaho.app')
        future = self.slot_in(3)
        r = self.client.post('/api/lessons/', self._lesson_payload(future), format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('slot_id', r.data)
        self.assertFalse(self.client.get(f'/api/slots/{future.id}/').data['can_assess'])

        # Leçon en cours, il reste 5 minutes : ouvert
        start = timezone.localtime() - timedelta(minutes=55)
        in_progress = Slot.objects.create(instructor=self.instructor, student=self.student, meeting_point=self.point, status='BOOKED',
                                          date=start.date(), start_time=start.time(), end_time=(start + timedelta(minutes=60)).time())
        self.assertTrue(self.client.get(f'/api/slots/{in_progress.id}/').data['can_assess'])
        self.assertEqual(self.client.post('/api/lessons/', self._lesson_payload(in_progress), format='json').status_code, 201)

        # Leçon qui vient de commencer : verrouillé
        start = timezone.localtime() - timedelta(minutes=5)
        started = Slot.objects.create(instructor=self.instructor, student=self.student, meeting_point=self.point, status='BOOKED',
                                      date=start.date(), start_time=start.time(), end_time=(start + timedelta(minutes=60)).time())
        self.assertEqual(self.client.post('/api/lessons/', self._lesson_payload(started), format='json').status_code, 400)

    # ----- Disponibilités : modification d'un lieu -----

    def test_instructor_can_change_meeting_point_of_existing_availability(self):
        av = Availability.objects.create(instructor=self.instructor, weekday=0, start_time=time(9), end_time=time(12))
        other = MeetingPoint.objects.create(name='Lycée', address='2 rue')
        self.auth('moni@kaho.app')
        r = self.client.patch(f'/api/availabilities/{av.id}/', {'meeting_point': other.id}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data['meeting_point_name'], 'Lycée')
        r = self.client.patch(f'/api/availabilities/{av.id}/', {'meeting_point': None}, format='json')
        self.assertEqual(r.status_code, 200)
        r = self.client.patch(f'/api/availabilities/{av.id}/', {'end_time': '08:00'}, format='json')
        self.assertEqual(r.status_code, 400)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class UnifiedPlanningTests(APITestCase):
    def test_instructor_calendar_is_scoped_to_own_slots(self):
        a, b = _user('a@kaho.app', 'INSTRUCTOR'), _user('b@kaho.app', 'INSTRUCTOR')
        admin = _user('adm@kaho.app', 'ADMIN')
        stu = _user('s@kaho.app', 'STUDENT').student_profile
        day = timezone.localdate() + timedelta(days=2)
        for ins in (a, b):
            Slot.objects.create(instructor=ins, student=stu, status='BOOKED', date=day, start_time=time(9), end_time=time(10))
        params = {'start': day.isoformat(), 'end': day.isoformat()}

        def login(email):
            r = self.client.post('/api/auth/token/', {'username': email, 'password': 'pass12345'})
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
        login('a@kaho.app')
        r = self.client.get('/api/admin/calendar/', params)
        self.assertEqual(r.status_code, 200)
        self.assertEqual([s['instructor'] for s in r.data['slots']], [a.id])
        self.assertEqual([i['id'] for i in r.data['instructors']], [a.id])
        login('adm@kaho.app')
        self.assertEqual(len(self.client.get('/api/admin/calendar/', params).data['slots']), 2)
        login('s@kaho.app')
        self.assertEqual(self.client.get('/api/admin/calendar/', params).status_code, 403)
