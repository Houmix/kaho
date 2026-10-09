from datetime import time, timedelta

from django.core import mail
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import ActivityLog, Availability, MeetingPoint, Slot, Unavailability, User


def next_weekday(weekday, min_days_ahead=3):
    d = timezone.localdate() + timedelta(days=min_days_ahead)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return d


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CRON_SECRET='s3cret')
class CalendarAndActivityTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='a@kaho.app', email='a@kaho.app', password='pass12345', first_name='Al', last_name='Admin', role='ADMIN')
        self.claire = User.objects.create_user(username='c@kaho.app', email='c@kaho.app', password='pass12345', first_name='Claire', last_name='Martin', role='INSTRUCTOR')
        self.karim = User.objects.create_user(username='k@kaho.app', email='k@kaho.app', password='pass12345', first_name='Karim', last_name='Benali', role='INSTRUCTOR')
        for ins in (self.claire, self.karim):
            Availability.objects.create(instructor=ins, weekday=0, start_time=time(9), end_time=time(12))
        self.point = MeetingPoint.objects.create(name='Gare', address='1 rue')
        su = User.objects.create_user(username='eleve@test.fr', email='eleve@test.fr', password='testpass123', first_name='Jean', last_name='Dupont', role='STUDENT')
        self.student = su.student_profile
        self.student.purchased_hours = 10
        self.student.save()
        self.monday = next_weekday(0)
        self.slot = Slot.objects.create(instructor=self.claire, student=self.student, meeting_point=self.point, status='BOOKED',
                                        date=self.monday, start_time=time(9), end_time=time(10))

    def auth(self, username, password='pass12345'):
        r = self.client.post('/api/auth/token/', {'username': username, 'password': password})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def test_calendar_returns_slots_unavailabilities_and_filters(self):
        Unavailability.objects.create(instructor=self.karim, start=timezone.make_aware(timezone.datetime.combine(self.monday, time(14))),
                                      end=timezone.make_aware(timezone.datetime.combine(self.monday, time(18))), reason='Médecin')
        self.auth('a@kaho.app')
        d = self.client.get('/api/admin/calendar/', {'start': self.monday, 'end': self.monday + timedelta(days=6)}).data
        self.assertEqual(len(d['slots']), 1)
        self.assertEqual(len(d['unavailabilities']), 1)
        self.assertEqual(len(d['instructors']), 2)
        self.assertEqual(len(self.client.get('/api/admin/calendar/', {'start': self.monday, 'end': self.monday, 'instructor': self.karim.id}).data['slots']), 0)
        self.assertEqual(self.client.get('/api/admin/calendar/', {'start': self.monday, 'end': self.monday + timedelta(days=90)}).status_code, 400)
        self.auth('c@kaho.app')
        # Un moniteur accède au calendrier, limité à son propre planning
        r = self.client.get('/api/admin/calendar/', {'start': self.monday, 'end': self.monday})
        self.assertEqual(r.status_code, 200)
        self.assertEqual({s['instructor'] for s in r.data['slots']}, {self.claire.id})
        self.assertEqual(len(r.data['instructors']), 1)

    def test_move_slot_reschedules_reassigns_and_notifies(self):
        self.auth('a@kaho.app')
        mail.outbox.clear()
        r = self.client.post(f'/api/admin/slots/{self.slot.id}/move/', {'start_time': '10:00'})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual((r.data['start_time'], r.data['end_time']), ('10:00:00', '11:00:00'))
        self.assertIsNone(r.data['warning'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('déplacée', mail.outbox[0].subject)

        r = self.client.post(f'/api/admin/slots/{self.slot.id}/move/', {'instructor': self.karim.id, 'notify': False})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data['instructor'], self.karim.id)
        self.assertEqual(len(mail.outbox), 1)  # pas de mail si notify=False

        # Hors disponibilités : accepté avec avertissement
        r = self.client.post(f'/api/admin/slots/{self.slot.id}/move/', {'start_time': '15:00'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('Hors des disponibilités', r.data['warning'])

        kinds = list(ActivityLog.objects.filter(kind='SLOT_MOVED').values_list('kind', flat=True))
        self.assertEqual(len(kinds), 3)

    def test_move_refuses_conflicts_and_past(self):
        other = Slot.objects.create(instructor=self.karim, student=None, meeting_point=self.point, status='BOOKED',
                                    date=self.monday, start_time=time(9), end_time=time(10))
        self.auth('a@kaho.app')
        r = self.client.post(f'/api/admin/slots/{self.slot.id}/move/', {'instructor': self.karim.id})
        self.assertEqual(r.status_code, 409)
        Unavailability.objects.create(instructor=self.claire, start=timezone.make_aware(timezone.datetime.combine(self.monday, time(11))),
                                      end=timezone.make_aware(timezone.datetime.combine(self.monday, time(12))))
        self.assertEqual(self.client.post(f'/api/admin/slots/{self.slot.id}/move/', {'start_time': '11:00'}).status_code, 409)
        self.assertEqual(self.client.post(f'/api/admin/slots/{self.slot.id}/move/', {'date': (timezone.localdate() - timedelta(days=1)).isoformat()}).status_code, 400)
        other.status = 'CANCELLED'
        other.save()
        self.assertEqual(self.client.post(f'/api/admin/slots/{self.slot.id}/move/', {'instructor': self.karim.id}).status_code, 200)

    def test_activity_log_records_booking_cancellation_and_is_listable(self):
        self.auth('eleve@test.fr', 'testpass123')
        r = self.client.post('/api/slots/book/', {'instructor': self.claire.id, 'meeting_point': self.point.id, 'date': self.monday.isoformat(), 'start_time': '10:00', 'end_time': '11:00'})
        self.assertEqual(r.status_code, 201, r.content)
        self.client.post(f"/api/slots/{r.data['id']}/cancel/", {'reason': 'Imprévu'}, format='json')
        self.auth('a@kaho.app')
        d = self.client.get('/api/admin/activity/').data
        self.assertEqual([e['kind'] for e in d['results'][:2]], ['CANCELLATION', 'BOOKING'])
        self.assertEqual(d['results'][1]['actor_name'], 'Jean Dupont')
        self.assertEqual(self.client.get('/api/admin/activity/?kind=BOOKING').data['count'], 1)
        self.assertEqual(len(self.client.get('/api/admin/overview/').data['activity']), 2)

    def test_cron_reminders_endpoint_requires_secret_and_sends(self):
        tomorrow = timezone.localdate() + timedelta(days=1)
        Slot.objects.create(instructor=self.claire, student=self.student, meeting_point=self.point, status='BOOKED', date=tomorrow, start_time=time(9), end_time=time(10))
        self.assertEqual(self.client.post('/api/internal/reminders/').status_code, 403)
        self.assertEqual(self.client.post('/api/internal/reminders/', HTTP_X_CRON_SECRET='wrong').status_code, 403)
        mail.outbox.clear()
        r = self.client.post('/api/internal/reminders/', HTTP_X_CRON_SECRET='s3cret')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data['sent'], 1)
        self.assertIn('Rappel', mail.outbox[0].subject)
        self.assertEqual(ActivityLog.objects.filter(kind='REMINDERS').count(), 1)

    @override_settings(CRON_SECRET='')
    def test_cron_disabled_without_secret(self):
        self.assertEqual(self.client.post('/api/internal/reminders/', HTTP_X_CRON_SECRET='').status_code, 403)
