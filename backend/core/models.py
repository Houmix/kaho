from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
import json

class User(AbstractUser):
    ROLE_CHOICES = [
        ('INSTRUCTOR', 'Monitrice'),
        ('STUDENT', 'Élève'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"


class StudentProfile(models.Model):
    LICENSE_CHOICES = [
        ('AUTO', 'Automatique'),
        ('MANUAL', 'Manuelle'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    neph_number = models.CharField(max_length=50, unique=True, blank=True)
    purchased_hours = models.FloatField(default=0, validators=[MinValueValidator(0)])
    used_hours = models.FloatField(default=0, validators=[MinValueValidator(0)])
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    license_type = models.CharField(max_length=20, choices=LICENSE_CHOICES, default='AUTO')
    ready_for_exam = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - NEPH: {self.neph_number}"

    @property
    def remaining_hours(self):
        return self.purchased_hours - self.used_hours


class MeetingPoint(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Slot(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Disponible'),
        ('BOOKED', 'Réservé'),
        ('CANCELLED', 'Annulé'),
    ]

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    meeting_point = models.ForeignKey(MeetingPoint, on_delete=models.PROTECT, related_name='slots')
    student = models.ForeignKey(StudentProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='booked_slots')
    instructor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='slots', limit_choices_to={'role': 'INSTRUCTOR'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ('date', 'start_time', 'instructor')

    def __str__(self):
        return f"{self.date} {self.start_time} - {self.meeting_point.name} ({self.get_status_display()})"

    @property
    def duration_hours(self):
        from datetime import datetime, timedelta
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        return (end - start).total_seconds() / 3600


class Lesson(models.Model):
    slot = models.OneToOneField(Slot, on_delete=models.CASCADE, related_name='lesson')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='lessons')
    attended = models.BooleanField(default=True)
    remc_skills = models.JSONField(default=dict, help_text="Compétences REMC au format JSON")
    weather_conditions = models.CharField(max_length=255, blank=True, help_text="Ex: Pluie, route mouillée")
    instructor_notes = models.TextField(blank=True)
    voice_memo_url = models.URLField(blank=True, help_text="URL du mémo vocal (Cloudinary, GCS)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Leçon {self.student.user.get_full_name()} - {self.slot.date}"

    def save(self, *args, **kwargs):
        # Décompte des heures uniquement à la création, pas à chaque modification du bilan
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and self.attended:
            self.student.used_hours += self.slot.duration_hours
            self.student.save(update_fields=['used_hours'])


class Offer(models.Model):
    name = models.CharField("Nom", max_length=100)
    description = models.CharField("Description courte", max_length=255, blank=True)
    hours = models.FloatField("Heures incluses", validators=[MinValueValidator(0.5)])
    price = models.DecimalField("Prix TTC (€)", max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    is_featured = models.BooleanField("Mise en avant", default=False)
    is_active = models.BooleanField("Visible sur le site", default=True)
    display_order = models.PositiveIntegerField("Ordre d'affichage", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'price']
        verbose_name = "Offre"

    def __str__(self):
        return f"{self.name} — {self.hours}h / {self.price}€"

    @property
    def price_per_hour(self):
        return round(float(self.price) / self.hours, 2)


class Package(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'En attente de paiement'),
        ('COMPLETED', 'Payé — heures créditées'),
        ('FAILED', 'Annulé'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='packages')
    offer = models.ForeignKey(Offer, on_delete=models.SET_NULL, null=True, blank=True, related_name='packages')
    hours_purchased = models.FloatField(validators=[MinValueValidator(0.5)])
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stripe_payment_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    note = models.TextField("Note interne (ex: virement reçu le …)", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Achat d'heures"

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.hours_purchased}h - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Crédite les heures une seule fois, au passage en COMPLETED
        was_completed = False
        if not self._state.adding:
            was_completed = Package.objects.filter(pk=self.pk, status='COMPLETED').exists()
        super().save(*args, **kwargs)
        if self.status == 'COMPLETED' and not was_completed:
            self.student.purchased_hours += self.hours_purchased
            self.student.save(update_fields=['purchased_hours'])


class Document(models.Model):
    TYPE_CHOICES = [
        ('IDENTITY', 'Pièce d\'identité'),
        ('NEPH_CERTIFICATE', 'Attestation NEPH'),
        ('CONTRACT', 'Contrat de formation'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    file = models.FileField(upload_to='documents/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')

    class Meta:
        ordering = ['-uploaded_at']
        unique_together = ('student', 'document_type')

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.get_document_type_display()}"


class VehicleLog(models.Model):
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicle_logs', limit_choices_to={'role': 'INSTRUCTOR'})
    date = models.DateField()
    kilometers = models.IntegerField(validators=[MinValueValidator(0)])
    fuel_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    maintenance_alert = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ('instructor', 'date')

    def __str__(self):
        return f"{self.instructor.get_full_name()} - {self.date} ({self.kilometers}km)"
