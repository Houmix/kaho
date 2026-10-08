import core.models
from django.db import migrations, models


def verified_to_status(apps, schema_editor):
    apps.get_model('core', 'Document').objects.filter(verified=True).update(status='VERIFIED')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_backfill_invoices'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='review_note',
            field=models.CharField(blank=True, max_length=255, verbose_name='Motif (si refus)'),
        ),
        migrations.AddField(
            model_name='document',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='document',
            name='status',
            field=models.CharField(choices=[('PENDING', 'À vérifier'), ('VERIFIED', 'Validé'), ('REJECTED', 'Refusé')], default='PENDING', max_length=10),
        ),
        migrations.RunPython(verified_to_status, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='document',
            name='verified',
        ),
        migrations.AlterField(
            model_name='document',
            name='file',
            field=models.FileField(upload_to=core.models.document_upload_to),
        ),
        migrations.AlterField(
            model_name='activitylog',
            name='kind',
            field=models.CharField(choices=[('BOOKING', 'Réservation'), ('CANCELLATION', 'Annulation'), ('LATE_CANCELLATION', 'Annulation tardive'), ('NO_SHOW', 'Absence'), ('REFUND', 'Re-crédit'), ('SLOT_MOVED', 'Créneau déplacé'), ('PAYMENT', 'Paiement'), ('HOURS_ADDED', 'Heures ajoutées'), ('APPLICATION', 'Candidature'), ('INSTRUCTOR', 'Moniteur'), ('LESSON', 'Bilan'), ('REMINDERS', 'Rappels'), ('DOCUMENT', 'Document')], max_length=20),
        ),
    ]
