from datetime import time, timedelta

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Availability, MeetingPoint, Slot, StudentProfile, Unavailability, User


def next_weekday(weekday, min_days_ahead=3):
    """Prochaine date tombant ce jour de semaine, au moins `min_days_ahead` jours devant (préavis 24 h)."""
    d = timezone.localdate() + timedelta(days=min_days_ahead)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return d


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class BookingFlowTests(APITestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(
            username='moniteur@kaho.app', email='moniteur@kaho.app', password='pass12345',
            first_name='Claire', last_name='Martin', role='INSTRUCTOR',
        )
        self.instructor.instructor_profile.hourly_rate = 30
        self.instructor.instructor_profile.save()
        self.point = MeetingPoint.objects.create(name='Gare', address='1 place de la Gare')
        # Disponible le lundi 9h-12h
        Availability.objects.create(instructor=self.instructor, weekday=0, start_time=time(9), end_time=time(12))
        self.monday = next_weekday(0)

        r = self.client.post('/api/auth/register/', {
            'email': 'eleve@test.fr', 'password': 'testpass123', 'first_name': 'Jean', 'last_name': 'Dupont',
            'phone': '06 12 34 56 78',
        })
        self.assertEqual(r.status_code, 201, r.content)
        self.student_token = r.data['access']
        self.student = StudentProfile.objects.get(user__email='eleve@test.fr')
        self.assertEqual(self.student.phone, '06 12 34 56 78')
        self.student.purchased_hours = 2
        self.student.save()

    def as_student(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')

    def as_instructor(self):
        r = self.client.post('/api/auth/token/', {'username': 'moniteur@kaho.app', 'password': 'pass12345'})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def free(self, day=None):
        return self.client.get('/api/slots/free/', {'date': (day or self.monday).isoformat()}).data

    def test_register_creates_student_profile_and_instructor_profile_exists(self):
        self.assertEqual(self.student.user.role, 'STUDENT')
        self.assertTrue(hasattr(self.instructor, 'instructor_profile'))

    def test_several_students_without_neph_can_register(self):
        """Régression : unique=True sur un champ vide bloquait le 2e inscrit."""
        for i in range(3):
            r = self.client.post('/api/auth/register/', {
                'email': f'eleve{i}@test.fr', 'password': 'testpass123', 'first_name': 'E', 'last_name': str(i)})
            self.assertEqual(r.status_code, 201, r.content)
        self.assertIsNone(StudentProfile.objects.get(user__email='eleve1@test.fr').neph_number)
        p = StudentProfile.objects.get(user__email='eleve2@test.fr')
        p.neph_number = '  '
        p.save()
        self.assertIsNone(p.neph_number)

    def test_free_windows_follow_availability(self):
        self.as_student()
        windows = self.free()
        self.assertEqual([w['start_time'] for w in windows], ['09:00', '10:00', '11:00'])
        self.assertEqual(self.free(self.monday + timedelta(days=1)), [])  # mardi : rien

    def test_unavailability_removes_windows(self):
        self.as_student()
        start = timezone.make_aware(timezone.datetime.combine(self.monday, time(10)))
        Unavailability.objects.create(instructor=self.instructor, start=start, end=start + timedelta(hours=1), reason='Médecin')
        self.assertEqual([w['start_time'] for w in self.free()], ['09:00', '11:00'])

    def test_book_then_window_disappears_and_conflict_is_refused(self):
        self.as_student()
        payload = {'instructor': self.instructor.id, 'meeting_point': self.point.id,
                   'date': self.monday.isoformat(), 'start_time': '09:00', 'end_time': '10:00'}
        r = self.client.post('/api/slots/book/', payload)
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data['status'], 'BOOKED')
        self.assertEqual([w['start_time'] for w in self.free()], ['10:00', '11:00'])
        self.assertEqual(self.client.post('/api/slots/book/', payload).status_code, 409)

    def test_booking_refused_when_not_enough_hours(self):
        self.as_student()
        self.student.purchased_hours = 0.5
        self.student.save()
        r = self.client.post('/api/slots/book/', {
            'instructor': self.instructor.id, 'meeting_point': self.point.id,
            'date': self.monday.isoformat(), 'start_time': '09:00', 'end_time': '10:00'})
        self.assertEqual(r.status_code, 400)
        self.assertIn('Crédit insuffisant', r.data['detail'])

    def test_reserved_hours_reduce_bookable_hours(self):
        self.as_student()
        for start, end in (('09:00', '10:00'), ('10:00', '11:00')):
            self.client.post('/api/slots/book/', {
                'instructor': self.instructor.id, 'meeting_point': self.point.id,
                'date': self.monday.isoformat(), 'start_time': start, 'end_time': end})
        profile = self.client.get('/api/student-profiles/my_profile/').data
        self.assertEqual(profile['reserved_hours'], 2.0)
        self.assertEqual(profile['bookable_hours'], 0.0)

    def test_late_cancellation_is_debited_and_early_cancellation_is_free(self):
        self.as_student()
        soon = Slot.objects.create(
            instructor=self.instructor, student=self.student, meeting_point=self.point, status='BOOKED',
            date=timezone.localdate() + timedelta(days=1), start_time=time(9), end_time=time(10))
        r = self.client.post(f'/api/slots/{soon.id}/cancel/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['status'], 'CANCELLED_LATE')
        self.student.refresh_from_db()
        self.assertEqual(self.student.used_hours, 1)

        later = Slot.objects.create(
            instructor=self.instructor, student=self.student, meeting_point=self.point, status='BOOKED',
            date=timezone.localdate() + timedelta(days=5), start_time=time(9), end_time=time(10))
        r = self.client.post(f'/api/slots/{later.id}/cancel/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['status'], 'CANCELLED')

    def test_instructor_dashboard_and_availability_crud(self):
        self.as_instructor()
        r = self.client.post('/api/availabilities/', {'weekday': 2, 'start_time': '14:00', 'end_time': '18:00'})
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(len(self.client.get('/api/availabilities/').data), 2)
        r = self.client.post('/api/availabilities/', {'weekday': 2, 'start_time': '18:00', 'end_time': '14:00'})
        self.assertEqual(r.status_code, 400)

        dash = self.client.get('/api/instructors/dashboard/').data
        self.assertEqual(dash['month']['hourly_rate'], 30.0)
        self.assertIn('upcoming', dash)

    def test_student_cannot_access_instructor_endpoints(self):
        self.as_student()
        self.assertEqual(self.client.get('/api/instructors/dashboard/').status_code, 403)
        self.assertEqual(self.client.post('/api/availabilities/', {'weekday': 0, 'start_time': '09:00', 'end_time': '10:00'}).status_code, 403)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class PasswordResetTests(APITestCase):
    def test_full_reset_flow(self):
        user = User.objects.create_user(username='x@test.fr', email='x@test.fr', password='oldpass123', role='STUDENT')
        from unittest.mock import patch
        with patch('core.views.send_password_reset_email.delay') as send:
            r = self.client.post('/api/auth/password-reset/', {'email': 'x@test.fr'})
            self.assertEqual(r.status_code, 200)
            link = send.call_args.args[1]
        # Email inconnu : même réponse, pas d'envoi
        with patch('core.views.send_password_reset_email.delay') as send:
            self.assertEqual(self.client.post('/api/auth/password-reset/', {'email': 'nobody@test.fr'}).status_code, 200)
            send.assert_not_called()

        from urllib.parse import parse_qs, urlparse
        q = parse_qs(urlparse(link).query)
        r = self.client.post('/api/auth/password-reset/confirm/', {
            'uid': q['uid'][0], 'token': q['token'][0], 'new_password': 'brandnew456'})
        self.assertEqual(r.status_code, 200, r.content)
        user.refresh_from_db()
        self.assertTrue(user.check_password('brandnew456'))
        self.assertTrue(user.password.startswith('argon2'))
        # Le token ne sert qu'une fois
        r = self.client.post('/api/auth/password-reset/confirm/', {
            'uid': q['uid'][0], 'token': q['token'][0], 'new_password': 'another789'})
        self.assertEqual(r.status_code, 400)
