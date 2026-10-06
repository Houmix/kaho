import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('kaho')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-lesson-reminders-every-morning': {
        'task': 'core.tasks.send_lesson_reminders',
        'schedule': crontab(hour=10, minute=0),
    },
}
