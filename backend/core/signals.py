from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Package, User, StudentProfile, InstructorProfile
from .tasks import send_payment_confirmation


@receiver(post_save, sender=User)
def create_instructor_profile(sender, instance, **kwargs):
    if instance.role == 'INSTRUCTOR':
        InstructorProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=Package)
def on_package_created(sender, instance, created, **kwargs):
    """Signal when package is created or status changes to COMPLETED"""
    if created:
        # Package created, send confirmation if completed
        if instance.status == 'COMPLETED':
            send_payment_confirmation.delay(instance.id)


@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):
    """Automatically create StudentProfile when Student user is created"""
    if created and instance.role == 'STUDENT':
        StudentProfile.objects.get_or_create(user=instance)
