from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from django.conf import settings as dj_settings

from .models import (
    User, StudentProfile, InstructorProfile, InstructorApplication, Availability, Unavailability, MeetingPoint, Slot,
    Competency, Lesson, CompetencyAssessment, LessonRating, Offer, Package, Invoice, Document, VehicleLog,
)


class InvoiceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_email = serializers.CharField(source='student.user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    amount_ht = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    amount_vat = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Invoice
        fields = ('id', 'number', 'package', 'student', 'student_name', 'student_email', 'label', 'quantity_hours',
                  'amount_ht', 'amount_vat', 'amount_ttc', 'vat_rate', 'status', 'status_display', 'is_overdue',
                  'issued_at', 'due_at', 'paid_at')
        read_only_fields = fields


def validate_upload(f):
    ext = (f.name.rsplit('.', 1)[-1] if '.' in f.name else '').lower()
    if ext not in dj_settings.UPLOAD_ALLOWED_EXTENSIONS:
        raise serializers.ValidationError(f"Format non accepté ({ext or 'inconnu'}). Formats : PDF, JPG, PNG.")
    if f.size > dj_settings.UPLOAD_MAX_BYTES:
        raise serializers.ValidationError("Fichier trop lourd (5 Mo maximum).")
    return f


# ---------- Auth ----------

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Un compte existe déjà avec cet email.")
        return value.lower()

    def create(self, validated_data):
        phone = validated_data.pop('phone', '')
        user = User.objects.create_user(username=validated_data['email'], role='STUDENT', **validated_data)
        if phone:
            user.student_profile.phone = phone
            user.student_profile.save(update_fields=['phone'])
        return user


class UserSerializer(serializers.ModelSerializer):
    teaches = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'also_instructor', 'teaches')
        read_only_fields = ('id', 'also_instructor')


class TeamMemberSerializer(serializers.ModelSerializer):
    """Comptes du back-office (gérant, gestionnaires, superviseurs)."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    has_password = serializers.SerializerMethodField()
    last_login = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'full_name', 'role', 'role_display', 'is_active', 'also_instructor', 'has_password', 'last_login', 'created_at')
        read_only_fields = ('id', 'email', 'created_at')

    def get_has_password(self, obj):
        return obj.has_usable_password()


class TeamInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=['ADMIN', 'SUPERVISOR', 'OWNER'], default='ADMIN')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Un compte existe déjà avec cet email.")
        return value.lower()

    def create(self, validated_data):
        user = User.objects.create_user(username=validated_data['email'], **validated_data)
        user.set_unusable_password()
        user.is_staff = validated_data['role'] == 'OWNER'
        user.save(update_fields=['password', 'is_staff'])
        return user


# ---------- Profils ----------

class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    remaining_hours = serializers.FloatField(read_only=True)
    reserved_hours = serializers.FloatField(read_only=True)
    bookable_hours = serializers.FloatField(read_only=True)
    has_lms_access = serializers.BooleanField(read_only=True)
    referent_instructor_name = serializers.CharField(source='referent_instructor.get_full_name', read_only=True, default=None)
    competency_progress = serializers.SerializerMethodField()
    dossier = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = (
            'id', 'user', 'status', 'status_display', 'neph_number', 'phone', 'purchased_hours', 'used_hours',
            'remaining_hours', 'reserved_hours', 'bookable_hours',
            'lms_access', 'lms_access_until', 'has_lms_access',
            'referent_instructor', 'referent_instructor_name', 'emergency_contact', 'emergency_phone',
            'license_type', 'ready_for_exam', 'competency_progress', 'dossier', 'created_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'status', 'created_at', 'updated_at', 'used_hours', 'purchased_hours', 'referent_instructor',
            'lms_access', 'lms_access_until',
        )

    def get_competency_progress(self, obj):
        return obj.competency_progress()

    def get_dossier(self, obj):
        return Document.dossier(obj)


class InstructorPublicSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    bio = serializers.CharField(source='instructor_profile.bio', read_only=True, default='')

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'full_name', 'bio')


class InstructorProfileSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    gearbox_display = serializers.CharField(source='get_gearbox_display', read_only=True)

    class Meta:
        model = InstructorProfile
        fields = ('id', 'user', 'hourly_rate', 'phone', 'gearbox', 'gearbox_display', 'vehicle', 'zones', 'bio', 'is_bookable')
        read_only_fields = ('id', 'hourly_rate')

    def get_user(self, obj):
        return UserSerializer(obj.user).data


# ---------- Back-office ----------

class InstructorCreateSerializer(serializers.Serializer):
    """Création d'un moniteur par l'admin ; un email d'invitation (création du mot de passe) est envoyé."""
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    hourly_rate = serializers.DecimalField(max_digits=7, decimal_places=2, required=False, default=0)
    gearbox = serializers.ChoiceField(choices=['AUTO', 'MANUAL', 'BOTH'], required=False, default='BOTH')
    vehicle = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Un compte existe déjà avec cet email.")
        return value.lower()

    def create(self, validated_data):
        profile_fields = {k: validated_data.pop(k) for k in ('phone', 'hourly_rate', 'gearbox', 'vehicle') if k in validated_data}
        user = User.objects.create_user(username=validated_data['email'], role='INSTRUCTOR', **validated_data)
        user.set_unusable_password()
        user.save(update_fields=['password'])
        profile, _ = InstructorProfile.objects.get_or_create(user=user)
        for k, v in profile_fields.items():
            setattr(profile, k, v)
        profile.save()
        user.refresh_from_db()  # vide le profil mis en cache par le signal post_save
        return user


class InstructorAdminSerializer(serializers.ModelSerializer):
    """Vue admin d'un moniteur : identité + profil + activité."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    profile = InstructorProfileSerializer(source='instructor_profile', read_only=True)
    has_password = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'full_name', 'is_active', 'has_password', 'profile', 'stats', 'created_at')

    def get_has_password(self, obj):
        return obj.has_usable_password()

    def get_stats(self, obj):
        from django.db.models import Avg, Count
        from django.utils import timezone
        today = timezone.localdate()
        r = LessonRating.objects.filter(lesson__slot__instructor=obj).aggregate(avg=Avg('score'), n=Count('id'))
        return {
            'upcoming': Slot.objects.filter(instructor=obj, status='BOOKED', date__gte=today).count(),
            'lessons': Lesson.objects.filter(slot__instructor=obj).count(),
            'students': StudentProfile.objects.filter(booked_slots__instructor=obj).distinct().count(),
            'availability_slots': Availability.objects.filter(instructor=obj).count(),
            'rating_average': round(r['avg'], 2) if r['avg'] else None,
            'rating_count': r['n'],
        }


class InstructorApplicationSerializer(serializers.ModelSerializer):
    gearbox_display = serializers.CharField(source='get_gearbox_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True, default=None)

    class Meta:
        model = InstructorApplication
        fields = (
            'id', 'first_name', 'last_name', 'email', 'phone', 'gearbox', 'gearbox_display', 'message',
            'diploma', 'driving_license', 'business_doc', 'status', 'status_display', 'admin_note',
            'reviewed_by_name', 'reviewed_at', 'created_user', 'created_at',
        )
        read_only_fields = ('id', 'status', 'admin_note', 'reviewed_by_name', 'reviewed_at', 'created_user', 'created_at')

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Un compte existe déjà avec cet email. Connectez-vous ou utilisez « mot de passe oublié ».")
        if InstructorApplication.objects.filter(email__iexact=value, status='PENDING').exists():
            raise serializers.ValidationError("Une candidature est déjà en cours d'examen pour cet email.")
        return value

    validate_diploma = staticmethod(validate_upload)
    validate_driving_license = staticmethod(validate_upload)

    def validate_business_doc(self, f):
        return validate_upload(f) if f else f


class RatingModerationSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='lesson.student.user.get_full_name', read_only=True)
    instructor_name = serializers.CharField(source='lesson.slot.instructor.get_full_name', read_only=True)
    instructor_id = serializers.IntegerField(source='lesson.slot.instructor_id', read_only=True)
    lesson_date = serializers.DateField(source='lesson.slot.date', read_only=True)

    class Meta:
        model = LessonRating
        fields = ('id', 'score', 'comment', 'reply', 'is_hidden', 'student_name', 'instructor_name', 'instructor_id', 'lesson_date', 'created_at')
        read_only_fields = ('id', 'score', 'comment', 'created_at')


# ---------- Planning ----------

class AvailabilitySerializer(serializers.ModelSerializer):
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)

    class Meta:
        model = Availability
        fields = ('id', 'weekday', 'weekday_display', 'start_time', 'end_time')

    def validate(self, data):
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError("L'heure de fin doit être après l'heure de début.")
        return data


class UnavailabilitySerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True, default=None)

    class Meta:
        model = Unavailability
        fields = ('id', 'instructor', 'instructor_name', 'start', 'end', 'reason', 'status', 'status_display', 'reviewed_by_name', 'reviewed_at', 'review_note')
        read_only_fields = ('id', 'instructor', 'status', 'reviewed_by_name', 'reviewed_at', 'review_note')

    def validate(self, data):
        if data['end'] <= data['start']:
            raise serializers.ValidationError("La fin doit être après le début.")
        return data


class FreeWindowSerializer(serializers.Serializer):
    instructor_id = serializers.IntegerField()
    instructor_name = serializers.CharField()
    date = serializers.DateField()
    start_time = serializers.TimeField(format='%H:%M')
    end_time = serializers.TimeField(format='%H:%M')


class BookingSerializer(serializers.Serializer):
    instructor = serializers.PrimaryKeyRelatedField(
        queryset=User.instructors().filter(instructor_profile__is_bookable=True)
    )
    meeting_point = serializers.PrimaryKeyRelatedField(queryset=MeetingPoint.objects.all(), required=False, allow_null=True)
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()

    def validate(self, data):
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError("L'heure de fin doit être après l'heure de début.")
        return data


class MeetingPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingPoint
        fields = ('id', 'name', 'description', 'address', 'latitude', 'longitude', 'created_at')
        read_only_fields = ('id', 'created_at')


class SlotSerializer(serializers.ModelSerializer):
    meeting_point_name = serializers.CharField(source='place_label', read_only=True)
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True, allow_null=True)
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    duration_hours = serializers.FloatField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    has_lesson = serializers.SerializerMethodField()
    lesson_id = serializers.SerializerMethodField()

    class Meta:
        model = Slot
        fields = (
            'id', 'date', 'start_time', 'end_time', 'status', 'status_display', 'meeting_point',
            'meeting_point_name', 'student', 'student_name', 'instructor', 'instructor_name',
            'duration_hours', 'is_past', 'has_lesson', 'lesson_id', 'cancelled_at',
            'hours_debited', 'hours_refunded', 'refund_note', 'created_at', 'updated_at',
        )
        read_only_fields = fields

    def get_has_lesson(self, obj):
        return hasattr(obj, 'lesson')

    def get_lesson_id(self, obj):
        return obj.lesson.id if hasattr(obj, 'lesson') else None


# ---------- Suivi pédagogique ----------

class CompetencySerializer(serializers.ModelSerializer):
    group_label = serializers.CharField(source='get_group_display', read_only=True)

    class Meta:
        model = Competency
        fields = ('id', 'code', 'label', 'group', 'group_label', 'order')


class CompetencyAssessmentSerializer(serializers.ModelSerializer):
    competency = serializers.PrimaryKeyRelatedField(queryset=Competency.objects.all())
    code = serializers.CharField(source='competency.code', read_only=True)
    label = serializers.CharField(source='competency.label', read_only=True)
    group = serializers.IntegerField(source='competency.group', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = CompetencyAssessment
        fields = ('competency', 'code', 'label', 'group', 'status', 'status_display')


class LessonRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonRating
        fields = ('score', 'comment', 'reply', 'created_at')
        read_only_fields = ('reply', 'created_at')


class LessonSerializer(serializers.ModelSerializer):
    slot = SlotSerializer(read_only=True)
    slot_id = serializers.PrimaryKeyRelatedField(
        queryset=Slot.objects.filter(status='BOOKED', student__isnull=False), source='slot', write_only=True
    )
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    instructor_name = serializers.CharField(source='slot.instructor.get_full_name', read_only=True)
    assessments = CompetencyAssessmentSerializer(many=True, required=False)
    rating = LessonRatingSerializer(read_only=True)

    class Meta:
        model = Lesson
        fields = (
            'id', 'slot', 'slot_id', 'student', 'student_name', 'instructor_name', 'attended',
            'weather_conditions', 'instructor_notes', 'voice_memo_url', 'assessments', 'rating',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'student', 'created_at', 'updated_at')

    def validate_slot_id(self, slot):
        if hasattr(slot, 'lesson'):
            raise serializers.ValidationError("Un bilan existe déjà pour ce créneau.")
        request = self.context.get('request')
        if request and request.user.role == 'INSTRUCTOR' and slot.instructor_id != request.user.id:
            raise serializers.ValidationError("Ce créneau n'est pas le vôtre.")
        return slot

    @transaction.atomic
    def create(self, validated_data):
        assessments = validated_data.pop('assessments', [])
        validated_data['student'] = validated_data['slot'].student
        lesson = super().create(validated_data)
        CompetencyAssessment.objects.bulk_create(
            [CompetencyAssessment(lesson=lesson, **a) for a in assessments]
        )
        return lesson

    @transaction.atomic
    def update(self, instance, validated_data):
        assessments = validated_data.pop('assessments', None)
        validated_data.pop('slot', None)
        lesson = super().update(instance, validated_data)
        if assessments is not None:
            lesson.assessments.all().delete()
            CompetencyAssessment.objects.bulk_create([CompetencyAssessment(lesson=lesson, **a) for a in assessments])
        return lesson


# ---------- Catalogue ----------

class OfferSerializer(serializers.ModelSerializer):
    price_per_hour = serializers.FloatField(read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    billing_display = serializers.CharField(source='get_billing_type_display', read_only=True)
    installments = serializers.IntegerField(read_only=True)
    skills = serializers.SlugRelatedField(many=True, slug_field='code', queryset=Competency.objects.all(), required=False)
    skill_labels = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = (
            'id', 'name', 'description', 'category', 'category_display', 'hours', 'price', 'price_per_hour',
            'billing_type', 'billing_display', 'billing_interval_months', 'installments', 'includes_lms', 'includes_exams', 'validity_months',
            'is_addon', 'skills', 'skill_labels', 'lets_student_pick_skills',
            'for_code_status', 'for_level', 'gearbox', 'is_featured',
        )

    def get_skill_labels(self, obj):
        return [f"{c.code} {c.label}" for c in obj.skills.all()]


class OfferAdminSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    billing_display = serializers.CharField(source='get_billing_type_display', read_only=True)
    sales = serializers.SerializerMethodField()

    skills = serializers.SlugRelatedField(many=True, slug_field='code', queryset=Competency.objects.all(), required=False)

    class Meta:
        model = Offer
        fields = ('id', 'name', 'description', 'category', 'category_display', 'hours', 'price', 'billing_type', 'billing_display', 'billing_interval_months',
                  'includes_lms', 'includes_exams', 'validity_months', 'is_addon', 'skills', 'lets_student_pick_skills',
                  'for_code_status', 'for_level', 'gearbox', 'is_featured', 'is_active', 'display_order', 'sales', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_sales(self, obj):
        return obj.packages.filter(status='COMPLETED').count()


class RecommendationInputSerializer(serializers.Serializer):
    code_status = serializers.ChoiceField(choices=['TO_PASS', 'OBTAINED'])
    level = serializers.ChoiceField(choices=['BEGINNER', 'REFRESH'])
    gearbox = serializers.ChoiceField(choices=['AUTO', 'MANUAL'], required=False, default='AUTO')


class PackageSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    offer = serializers.PrimaryKeyRelatedField(queryset=Offer.objects.filter(is_active=True))
    addons = serializers.PrimaryKeyRelatedField(queryset=Offer.objects.filter(is_active=True, is_addon=True), many=True, required=False, write_only=True)
    skills = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    addon_items = serializers.SerializerMethodField()
    bundle_total = serializers.SerializerMethodField()
    installments = serializers.IntegerField(source='offer.installments', read_only=True, default=1)
    offer_name = serializers.CharField(source='offer.name', read_only=True)
    offer_category = serializers.CharField(source='offer.category', read_only=True)
    includes_lms = serializers.BooleanField(source='offer.includes_lms', read_only=True)
    display_label = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    invoice_id = serializers.IntegerField(source='invoice.id', read_only=True, default=None)
    invoice_number = serializers.CharField(source='invoice.number', read_only=True, default=None)

    def get_addon_items(self, obj):
        return [{'id': a.id, 'label': a.display_label, 'amount': str(a.amount_paid), 'status': a.status} for a in obj.addons.all()] if obj.parent_id is None else []

    def get_bundle_total(self, obj):
        return str(sum((p.amount_paid for p in obj.bundle), 0)) if obj.parent_id is None else str(obj.amount_paid)

    def validate(self, data):
        offer = data.get('offer')
        skills = data.get('skills') or []
        if skills:
            pickers = [o for o in [offer, *(data.get('addons') or [])] if o and o.lets_student_pick_skills]
            if not pickers:
                raise serializers.ValidationError({'skills': "Cette formule ne permet pas de choisir les compétences."})
            allowed = set()
            for o in pickers:
                allowed |= set(o.skills.values_list('code', flat=True)) or set(Competency.objects.values_list('code', flat=True))
            bad = [c for c in skills if c not in allowed]
            if bad:
                raise serializers.ValidationError({'skills': f"Compétences inconnues : {', '.join(bad)}"})
        return data

    def create(self, validated_data):
        """Formule de base + options (une ligne par option, rattachée à la base) + compétences choisies."""
        addons = validated_data.pop('addons', [])
        skills = validated_data.pop('skills', [])
        offer = validated_data['offer']
        validated_data['hours_purchased'] = offer.hours
        validated_data['amount_paid'] = offer.price
        validated_data['requested_skills'] = skills
        base = super().create(validated_data)
        for a in addons:
            Package.objects.create(student=base.student, offer=a, parent=base, hours_purchased=a.hours, amount_paid=a.price, status=base.status)
        return base

    class Meta:
        model = Package
        fields = (
            'id', 'student', 'student_name', 'offer', 'offer_name', 'offer_category', 'includes_lms', 'label', 'display_label',
            'hours_purchased', 'amount_paid', 'status', 'status_display', 'payment_method', 'payment_method_display', 'installments', 'installments_paid',
            'stripe_checkout_url', 'paid_at', 'expires_at', 'note', 'invoice_id', 'invoice_number', 'parent', 'addons', 'addon_items', 'bundle_total',
            'skills', 'requested_skills', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'student', 'label', 'hours_purchased', 'amount_paid', 'status', 'payment_method', 'stripe_checkout_url', 'paid_at', 'expires_at', 'note', 'parent', 'requested_skills', 'installments_paid', 'created_at', 'updated_at')


# ---------- Divers ----------

class DocumentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True, default=None)
    file_name = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ('id', 'student', 'student_name', 'document_type', 'document_type_display', 'file', 'file_name',
                  'uploaded_at', 'status', 'status_display', 'review_note', 'reviewed_at', 'verified_by', 'verified_by_name')
        read_only_fields = ('id', 'student', 'uploaded_at', 'status', 'review_note', 'reviewed_at', 'verified_by')

    validate_file = staticmethod(validate_upload)

    def get_file_name(self, obj):
        return obj.file.name.rsplit('/', 1)[-1] if obj.file else ''


class VehicleLogSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)

    class Meta:
        model = VehicleLog
        fields = ('id', 'instructor', 'instructor_name', 'date', 'kilometers', 'fuel_cost', 'maintenance_alert', 'notes', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


# ---------- Connexion ----------

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class FrenchTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Messages d'erreur en français ; l'email est insensible à la casse (voir core.auth_backends)."""
    default_error_messages = {'no_active_account': 'Email ou mot de passe incorrect.'}

    def validate(self, attrs):
        attrs[self.username_field] = (attrs.get(self.username_field) or '').strip().lower()
        return super().validate(attrs)
