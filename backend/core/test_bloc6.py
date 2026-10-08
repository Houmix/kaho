from datetime import time, timedelta
from decimal import Decimal

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Invoice, Lesson, MeetingPoint, Offer, Package, Slot, User


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, INVOICE_PREFIX='TEST', INVOICE_VAT_RATE=20.0)
class InvoiceAndPayrollTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='a@kaho.app', email='a@kaho.app', password='pass12345', first_name='Al', last_name='Admin', role='OWNER')
        self.instructor = User.objects.create_user(username='m@kaho.app', email='m@kaho.app', password='pass12345', first_name='Claire', last_name='Martin', role='INSTRUCTOR')
        self.instructor.instructor_profile.hourly_rate = 30
        self.instructor.instructor_profile.save()
        self.point = MeetingPoint.objects.create(name='Gare', address='1 rue')
        self.offer = Offer.objects.create(name='Pack 10h', hours=10, price=Decimal('450.00'))
        su = User.objects.create_user(username='eleve@test.fr', email='eleve@test.fr', password='testpass123', first_name='Jean', last_name='Dupont', role='STUDENT')
        self.student = su.student_profile

    def auth(self, username, password='pass12345'):
        r = self.client.post('/api/auth/token/', {'username': username, 'password': password})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def test_invoice_lifecycle_follows_package(self):
        year = timezone.localdate().year
        pkg = Package.objects.create(student=self.student, offer=self.offer, hours_purchased=10, amount_paid=Decimal('450.00'))
        inv = pkg.invoice
        self.assertEqual(inv.number, f'TEST-{year}-0001')
        self.assertEqual(inv.status, 'ISSUED')
        self.assertEqual(inv.amount_ttc, Decimal('450.00'))
        self.assertEqual(inv.amount_ht, Decimal('375.00'))
        self.assertEqual(inv.amount_vat, Decimal('75.00'))
        self.assertEqual(inv.due_at, inv.issued_at + timedelta(days=30))

        pkg.status = 'COMPLETED'
        pkg.save()
        inv.refresh_from_db()
        self.assertEqual(inv.status, 'PAID')
        self.assertIsNotNone(inv.paid_at)

        pkg2 = Package.objects.create(student=self.student, offer=self.offer, hours_purchased=10, amount_paid=Decimal('450.00'))
        self.assertEqual(pkg2.invoice.number, f'TEST-{year}-0002')
        pkg2.status = 'FAILED'
        pkg2.save()
        self.assertEqual(Invoice.objects.get(package=pkg2).status, 'CANCELLED')

        # Ajout manuel gratuit : pas de facture
        free = Package.objects.create(student=self.student, hours_purchased=2, amount_paid=0, status='COMPLETED')
        self.assertFalse(hasattr(free, 'invoice'))

    def test_student_sees_only_own_invoices_and_can_download_pdf(self):
        pkg = Package.objects.create(student=self.student, offer=self.offer, hours_purchased=10, amount_paid=Decimal('450.00'))
        other = User.objects.create_user(username='o@test.fr', email='o@test.fr', password='testpass123', first_name='O', last_name='T', role='STUDENT')
        Package.objects.create(student=other.student_profile, offer=self.offer, hours_purchased=10, amount_paid=Decimal('450.00'))

        self.auth('eleve@test.fr', 'testpass123')
        r = self.client.get('/api/invoices/')
        self.assertEqual(r.data['count'], 1)
        self.assertEqual(r.data['results'][0]['number'], pkg.invoice.number)
        r = self.client.get(f'/api/invoices/{pkg.invoice.id}/pdf/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertTrue(r.content.startswith(b'%PDF'))
        self.assertIn(pkg.invoice.number, r['Content-Disposition'])
        other_inv = Invoice.objects.get(student=other.student_profile)
        self.assertEqual(self.client.get(f'/api/invoices/{other_inv.id}/pdf/').status_code, 404)
        # L'achat expose le numéro de facture
        self.assertEqual(self.client.get('/api/packages/').data['results'][0]['invoice_number'], pkg.invoice.number)

    def test_admin_sales_invoices_and_unpaid(self):
        p1 = Package.objects.create(student=self.student, offer=self.offer, hours_purchased=10, amount_paid=Decimal('450.00'))
        p1.status = 'COMPLETED'
        p1.save()
        p2 = Package.objects.create(student=self.student, offer=self.offer, hours_purchased=10, amount_paid=Decimal('450.00'))
        Invoice.objects.filter(package=p2).update(due_at=timezone.localdate() - timedelta(days=5))

        self.auth('a@kaho.app')
        d = self.client.get('/api/admin/sales/').data
        self.assertEqual(len(d['months']), 12)
        self.assertEqual(d['months'][-1]['revenue'], 450.0)
        self.assertEqual(d['year_revenue'], 450.0)
        self.assertEqual(d['unpaid']['count'], 1)
        self.assertEqual(d['unpaid']['overdue'], 1)
        self.assertTrue(d['unpaid']['items'][0]['is_overdue'])

        self.assertEqual(self.client.get('/api/admin/invoices/').data['count'], 2)
        self.assertEqual(self.client.get('/api/admin/invoices/?status=PAID').data['count'], 1)
        self.assertEqual(self.client.get('/api/admin/invoices/?q=dupont').data['count'], 2)
        self.assertEqual(self.client.get(f"/api/admin/invoices/?month={timezone.localdate():%Y-%m}").data['count'], 2)
        self.auth('m@kaho.app')
        self.assertEqual(self.client.get('/api/admin/sales/').status_code, 403)

    def test_payroll_counts_attended_hours_only(self):
        today = timezone.localdate()
        d = today.replace(day=1)
        mk = lambda day, h, attended: Lesson.objects.create(
            slot=Slot.objects.create(instructor=self.instructor, student=self.student, meeting_point=self.point, status='BOOKED', date=day, start_time=time(h), end_time=time(h + 1)),
            student=self.student, attended=attended)
        mk(d, 9, True)
        mk(d, 11, True)
        mk(d, 14, False)  # absence : non payée (le créneau passe en NO_SHOW)
        self.auth('a@kaho.app')
        r = self.client.get(f'/api/admin/payroll/?month={d:%Y-%m}').data
        row = next(x for x in r['rows'] if x['id'] == self.instructor.id)
        self.assertEqual(row['hours'], 2.0)
        self.assertEqual(row['lessons'], 2)
        self.assertEqual(row['no_shows'], 1)
        self.assertEqual(row['amount'], 60.0)
        self.assertEqual(r['total'], 60.0)
        self.assertEqual(len(row['details']), 2)
        self.assertEqual(self.client.get('/api/admin/payroll/?month=2020-13').status_code, 400)
