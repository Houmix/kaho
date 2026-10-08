from datetime import date

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


def add_months(d: date, months: int) -> date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date(year, month, day)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('STUDENT', 'Élève'),
        ('INSTRUCTOR', 'Moniteur / Formateur'),
        ('SUPERVISOR', 'Superviseur / Bénévole'),
        ('ADMIN', 'Administrateur'),
    ]
    STAFF_ROLES = ('INSTRUCTOR', 'SUPERVISOR', 'ADMIN')

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
    # NULL (et non '') quand absent : unique=True n'accepte qu'une seule chaîne vide
    neph_number = models.CharField("N° NEPH", max_length=50, unique=True, null=True, blank=True)
    phone = models.CharField("Téléphone mobile (SMS)", max_length=20, blank=True)
    purchased_hours = models.FloatField(default=0, validators=[MinValueValidator(0)])
    used_hours = models.FloatField(default=0, validators=[MinValueValidator(0)])
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    license_type = models.CharField(max_length=20, choices=LICENSE_CHOICES, default='AUTO')
    ready_for_exam = models.BooleanField(default=False)
    referent_instructor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='referent_students', limit_choices_to={'role': 'INSTRUCTOR'},
        verbose_name="Moniteur référent",
    )
    lms_access = models.BooleanField("Accès cours de code / quiz", default=False)
    lms_access_until = models.DateField("Accès LMS jusqu'au (vide = illimité)", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - NEPH: {self.neph_number or '—'}"

    def save(self, *args, **kwargs):
        self.neph_number = (self.neph_number or '').strip() or None
        super().save(*args, **kwargs)

    @property
    def remaining_hours(self):
        return self.purchased_hours - self.used_hours

    @property
    def reserved_hours(self):
        today = timezone.localdate()
        return sum(s.duration_hours for s in self.booked_slots.filter(status='BOOKED', date__gte=today))

    @property
    def bookable_hours(self):
        return self.remaining_hours - self.reserved_hours

    @property
    def has_lms_access(self):
        return self.lms_access and (self.lms_access_until is None or self.lms_access_until >= timezone.localdate())

    def competency_progress(self):
        total = Competency.objects.count()
        if not total:
            return {'acquired': 0, 'in_progress': 0, 'total': 0, 'percent': 0}
        latest = {}
        qs = (CompetencyAssessment.objects.filter(lesson__student=self)
              .order_by('competency_id', '-lesson__slot__date', '-lesson__created_at'))
        for a in qs:
            latest.setdefault(a.competency_id, a.status)
        acquired = sum(1 for s in latest.values() if s == 'ACQUIRED')
        in_progress = sum(1 for s in latest.values() if s == 'IN_PROGRESS')
        return {'acquired': acquired, 'in_progress': in_progress, 'total': total, 'percent': round(100 * acquired / total)}


GEARBOX_CHOICES = [('AUTO', 'Boîte automatique'), ('MANUAL', 'Boîte manuelle'), ('BOTH', 'Les deux')]


class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    hourly_rate = models.DecimalField("Taux horaire (€)", max_digits=7, decimal_places=2, default=0)
    phone = models.CharField("Téléphone", max_length=20, blank=True)
    gearbox = models.CharField("Boîte enseignée", max_length=10, choices=GEARBOX_CHOICES, default='BOTH')
    vehicle = models.CharField("Véhicule", max_length=100, blank=True)
    bio = models.TextField(blank=True)
    is_bookable = models.BooleanField("Réservable par les élèves", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profil moniteur"

    def __str__(self):
        return self.user.get_full_name()


class Availability(models.Model):
    WEEKDAYS = [(0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'), (3, 'Jeudi'), (4, 'Vendredi'), (5, 'Samedi'), (6, 'Dimanche')]

    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availabilities', limit_choices_to={'role': 'INSTRUCTOR'})
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['weekday', 'start_time']
        verbose_name = "Disponibilité récurrente"

    def __str__(self):
        return f"{self.instructor.get_full_name()} — {self.get_weekday_display()} {self.start_time:%H:%M}–{self.end_time:%H:%M}"

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("L'heure de fin doit être après l'heure de début.")


class Unavailability(models.Model):
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unavailabilities', limit_choices_to={'role': 'INSTRUCTOR'})
    start = models.DateTimeField()
    end = models.DateTimeField()
    reason = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ['-start']
        verbose_name = "Indisponibilité / absence"

    def __str__(self):
        return f"{self.instructor.get_full_name()} — {self.start:%d/%m %H:%M} → {self.end:%d/%m %H:%M}"

    def clean(self):
        if self.end <= self.start:
            raise ValidationError("La fin doit être après le début.")


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
        ('CANCELLED_LATE', 'Annulé hors délai'),
        ('NO_SHOW', 'Absent'),
    ]

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    meeting_point = models.ForeignKey(MeetingPoint, on_delete=models.PROTECT, related_name='slots')
    student = models.ForeignKey(StudentProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='booked_slots')
    instructor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='slots', limit_choices_to={'role': 'INSTRUCTOR'})
    cancelled_at = models.DateTimeField(null=True, blank=True)
    hours_debited = models.BooleanField("Heures débitées", default=False)
    hours_refunded = models.BooleanField("Heures re-créditées (dérogation)", default=False)
    refund_note = models.TextField("Justificatif de dérogation", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.date} {self.start_time} - {self.meeting_point.name} ({self.get_status_display()})"

    @property
    def duration_hours(self):
        from datetime import datetime
        return (datetime.combine(self.date, self.end_time) - datetime.combine(self.date, self.start_time)).total_seconds() / 3600

    @property
    def starts_at(self):
        from datetime import datetime
        return timezone.make_aware(datetime.combine(self.date, self.start_time))

    @property
    def is_past(self):
        return self.starts_at <= timezone.now()

    def debit_hours(self):
        """Débite l'heure du solde de l'élève, une seule fois."""
        if self.hours_debited or not self.student:
            return
        self.student.used_hours += self.duration_hours
        self.student.save(update_fields=['used_hours'])
        self.hours_debited = True
        self.save(update_fields=['hours_debited', 'updated_at'])

    def refund_hours(self, note=''):
        """Dérogation : re-crédite l'heure débitée (certificat médical…)."""
        if not self.hours_debited or self.hours_refunded or not self.student:
            return False
        self.student.used_hours = max(0.0, self.student.used_hours - self.duration_hours)
        self.student.save(update_fields=['used_hours'])
        self.hours_refunded = True
        self.refund_note = note
        self.save(update_fields=['hours_refunded', 'refund_note', 'updated_at'])
        return True


class Competency(models.Model):
    """Compétence du REMC (programme officiel)."""
    GROUPS = [
        (1, 'Maîtriser le maniement du véhicule dans un trafic faible ou nul'),
        (2, 'Appréhender la route et circuler dans des conditions normales'),
        (3, 'Circuler dans des conditions difficiles et partager la route'),
        (4, 'Pratiquer une conduite autonome, sûre et économique'),
    ]
    code = models.CharField(max_length=10, unique=True)
    label = models.CharField(max_length=200)
    group = models.PositiveSmallIntegerField(choices=GROUPS)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['group', 'order', 'code']
        verbose_name = "Compétence REMC"

    def __str__(self):
        return f"{self.code} {self.label}"


class Lesson(models.Model):
    slot = models.OneToOneField(Slot, on_delete=models.CASCADE, related_name='lesson')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='lessons')
    attended = models.BooleanField("Élève présent", default=True)
    weather_conditions = models.CharField(max_length=255, blank=True, help_text="Ex: Pluie, route mouillée")
    instructor_notes = models.TextField("Observations", blank=True)
    voice_memo_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Bilan de leçon"

    def __str__(self):
        return f"Leçon {self.student.user.get_full_name()} - {self.slot.date}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            # Présent ou absent : l'heure est due (politique anti no-show)
            if not self.attended and self.slot.status == 'BOOKED':
                self.slot.status = 'NO_SHOW'
                self.slot.save(update_fields=['status', 'updated_at'])
            self.slot.debit_hours()


class CompetencyAssessment(models.Model):
    STATUS_CHOICES = [
        ('NOT_COVERED', 'Non abordé'),
        ('IN_PROGRESS', 'En cours'),
        ('ACQUIRED', 'Acquis'),
    ]
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='assessments')
    competency = models.ForeignKey(Competency, on_delete=models.CASCADE, related_name='assessments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')

    class Meta:
        unique_together = ('lesson', 'competency')
        verbose_name = "Évaluation de compétence"

    def __str__(self):
        return f"{self.competency.code} — {self.get_status_display()}"


class LessonRating(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='rating')
    score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    reply = models.TextField("Réponse de l'école", blank=True)
    is_hidden = models.BooleanField("Masqué (modération)", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Avis sur le moniteur"

    def __str__(self):
        return f"{self.score}/5 — {self.lesson}"


class Offer(models.Model):
    CATEGORY_CHOICES = [
        ('PERMIS_B', 'Permis B'),
        ('CODE', 'Code seul'),
        ('PERFECTIONNEMENT', 'Perfectionnement / remise en selle'),
        ('RECHARGE', "Recharge d'heures"),
    ]
    BILLING_CHOICES = [
        ('ONE_TIME', 'Paiement unique'),
        ('MONTHLY', 'Abonnement mensuel'),
        ('INSTALLMENTS_3', 'En 3 fois'),
        ('INSTALLMENTS_4', 'En 4 fois'),
    ]
    CODE_STATUS_CHOICES = [('ANY', 'Indifférent'), ('TO_PASS', 'Code à passer'), ('OBTAINED', 'Code obtenu')]
    LEVEL_CHOICES = [('ANY', 'Indifférent'), ('BEGINNER', 'Débutant'), ('REFRESH', 'Révision / remise à niveau')]
    GEARBOX_CHOICES = [('ANY', 'Indifférent'), ('AUTO', 'Boîte automatique'), ('MANUAL', 'Boîte manuelle')]

    name = models.CharField("Nom", max_length=100)
    description = models.CharField("Description courte", max_length=255, blank=True)
    category = models.CharField("Catégorie", max_length=20, choices=CATEGORY_CHOICES, default='PERMIS_B')
    hours = models.FloatField("Heures de conduite incluses", validators=[MinValueValidator(0)], default=0)
    price = models.DecimalField("Prix TTC (€)", max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    billing_type = models.CharField("Type de facturation", max_length=20, choices=BILLING_CHOICES, default='ONE_TIME')
    includes_lms = models.BooleanField("Accès cours de code / quiz / examens blancs", default=False)
    validity_months = models.PositiveSmallIntegerField("Validité (mois, vide = illimité)", null=True, blank=True)
    for_code_status = models.CharField("Cible : statut du code", max_length=10, choices=CODE_STATUS_CHOICES, default='ANY')
    for_level = models.CharField("Cible : niveau", max_length=10, choices=LEVEL_CHOICES, default='ANY')
    gearbox = models.CharField("Boîte", max_length=10, choices=GEARBOX_CHOICES, default='ANY')
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
        return round(float(self.price) / self.hours, 2) if self.hours else None


class Package(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'En attente de paiement'),
        ('COMPLETED', 'Payé — accès et heures crédités'),
        ('FAILED', 'Annulé'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='packages')
    offer = models.ForeignKey(Offer, on_delete=models.SET_NULL, null=True, blank=True, related_name='packages')
    hours_purchased = models.FloatField(validators=[MinValueValidator(0)])
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stripe_payment_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    paid_at = models.DateTimeField("Payé le", null=True, blank=True)
    expires_at = models.DateField("Fin de validité", null=True, blank=True)
    note = models.TextField("Note interne (ex: virement reçu le …)", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Achat / souscription"

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.hours_purchased}h - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Crédite heures + accès LMS une seule fois, au passage en COMPLETED
        was_completed = False
        if not self._state.adding:
            was_completed = Package.objects.filter(pk=self.pk, status='COMPLETED').exists()
        granted = self.status == 'COMPLETED' and not was_completed
        if granted:
            self._grant()
        super().save(*args, **kwargs)
        if granted:
            from .tasks import send_payment_confirmation
            send_payment_confirmation.delay(self.pk)

    def _grant(self):
        today = timezone.localdate()
        self.paid_at = timezone.now()
        st = self.student
        st.purchased_hours += self.hours_purchased
        update = ['purchased_hours']
        if self.offer:
            months = self.offer.validity_months
            self.expires_at = add_months(today, months) if months else None
            if self.offer.includes_lms:
                st.lms_access = True
                if months:
                    base = st.lms_access_until if (st.lms_access_until and st.lms_access_until > today) else today
                    st.lms_access_until = add_months(base, months)
                else:
                    st.lms_access_until = None
                update += ['lms_access', 'lms_access_until']
        st.save(update_fields=update)


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


def _application_upload(instance, filename):
    return f"applications/{instance.email.replace('@', '_at_')}/{filename}"


class InstructorApplication(models.Model):
    """Candidature spontanée d'un moniteur via /devenir-moniteur."""
    STATUS_CHOICES = [('PENDING', 'À examiner'), ('APPROVED', 'Acceptée'), ('REJECTED', 'Refusée')]

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    gearbox = models.CharField(max_length=10, choices=GEARBOX_CHOICES, default='BOTH')
    message = models.TextField(blank=True)
    diploma = models.FileField("Diplôme / autorisation d'enseigner", upload_to=_application_upload)
    driving_license = models.FileField("Permis de conduire", upload_to=_application_upload)
    business_doc = models.FileField("Kbis / statut auto-entrepreneur", upload_to=_application_upload, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    admin_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='application')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Candidature moniteur"

    def __str__(self):
        return f"{self.first_name} {self.last_name} — {self.get_status_display()}"


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
