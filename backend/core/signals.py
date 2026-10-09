from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, StudentProfile, InstructorProfile


@receiver(post_save, sender=User)
def create_instructor_profile(sender, instance, **kwargs):
    if instance.teaches:
        InstructorProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):
    """Automatically create StudentProfile when Student user is created"""
    if created and instance.role == 'STUDENT':
        StudentProfile.objects.get_or_create(user=instance)
