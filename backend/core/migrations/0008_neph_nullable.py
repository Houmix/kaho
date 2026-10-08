from django.db import migrations, models


def blank_to_null(apps, schema_editor):
    apps.get_model('core', 'StudentProfile').objects.filter(neph_number='').update(neph_number=None)


class Migration(migrations.Migration):
    dependencies = [('core', '0007_instructorprofile_gearbox_instructorprofile_phone_and_more')]
    operations = [
        migrations.AlterField(
            model_name='studentprofile',
            name='neph_number',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True, verbose_name='N° NEPH'),
        ),
        migrations.RunPython(blank_to_null, migrations.RunPython.noop),
    ]
