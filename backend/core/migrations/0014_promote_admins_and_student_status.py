from django.db import migrations


def forwards(apps, schema_editor):
    User = apps.get_model('core', 'User')
    StudentProfile = apps.get_model('core', 'StudentProfile')
    Document = apps.get_model('core', 'Document')
    Unavailability = apps.get_model('core', 'Unavailability')
    # Les administrateurs existants avaient tous les droits : ils deviennent gérants (super admin)
    User.objects.filter(role='ADMIN').update(role='OWNER', is_staff=True, is_superuser=True)
    # Statut de parcours déduit de l'existant
    required = ('IDENTITY', 'PHOTO', 'PROOF_ADDRESS', 'NEPH_CERTIFICATE', 'CONTRACT')
    for sp in StudentProfile.objects.all():
        verified = set(Document.objects.filter(student=sp, status='VERIFIED').values_list('document_type', flat=True))
        if sp.ready_for_exam:
            sp.status = 'EXAM'
        elif sp.used_hours > 0:
            sp.status = 'DRIVING'
        elif sp.lms_access:
            sp.status = 'CODE'
        elif all(t in verified for t in required):
            sp.status = 'REGISTERED'
        else:
            sp.status = 'INCOMPLETE'
        sp.save(update_fields=['status'])
    Unavailability.objects.update(status='APPROVED')


def backwards(apps, schema_editor):
    apps.get_model('core', 'User').objects.filter(role='OWNER').update(role='ADMIN')


class Migration(migrations.Migration):
    dependencies = [('core', '0013_roles_status_payments_absences')]
    operations = [migrations.RunPython(forwards, backwards)]
