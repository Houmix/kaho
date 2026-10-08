from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import migrations


def backfill(apps, schema_editor):
    Package = apps.get_model('core', 'Package')
    Invoice = apps.get_model('core', 'Invoice')
    InvoiceSequence = apps.get_model('core', 'InvoiceSequence')
    status_map = {'PENDING': 'ISSUED', 'COMPLETED': 'PAID', 'FAILED': 'CANCELLED'}
    for pkg in Package.objects.filter(amount_paid__gt=0, invoice__isnull=True).order_by('created_at'):
        day = (pkg.paid_at or pkg.created_at).date()
        seq, _ = InvoiceSequence.objects.get_or_create(year=day.year)
        seq.last += 1
        seq.save(update_fields=['last'])
        Invoice.objects.create(
            number=f"{getattr(settings, 'INVOICE_PREFIX', 'KAHO')}-{day.year}-{seq.last:04d}",
            package=pkg, student=pkg.student,
            label=pkg.offer.name if pkg.offer else f"Heures de conduite ({pkg.hours_purchased:g} h)",
            quantity_hours=pkg.hours_purchased, amount_ttc=pkg.amount_paid,
            vat_rate=Decimal(str(getattr(settings, 'INVOICE_VAT_RATE', 20.0))),
            status=status_map[pkg.status], issued_at=day, due_at=day + timedelta(days=30),
            paid_at=pkg.paid_at if pkg.status == 'COMPLETED' else None,
        )


class Migration(migrations.Migration):
    dependencies = [('core', '0010_invoicesequence_invoice')]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
