from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import (
    User, StudentProfile, InstructorProfile, Availability, Unavailability, MeetingPoint, Slot,
    Competency, Lesson, CompetencyAssessment, LessonRating, Offer, Package, Document, VehicleLog,
)


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
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role')
        read_only_fields = ('id',)


# ---------- Profils ----------

class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    remaining_hours = serializers.FloatField(read_only=True)
    reserved_hours = serializers.FloatField(read_only=True)
    bookable_hours = serializers.FloatField(read_only=True)
    has_lms_access = serializers.BooleanField(read_only=True)
    referent_instructor_name = serializers.CharField(source='referent_instructor.get_full_name', read_only=True, default=None)
    competency_progress = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = (
            'id', 'user', 'neph_number', 'phone', 'purchased_hours', 'used_hours',
            'remaining_hours', 'reserved_hours', 'bookable_hours',
            'lms_access', 'lms_access_until', 'has_lms_access',
            'referent_instructor', 'referent_instructor_name', 'emergency_contact', 'emergency_phone',
            'license_type', 'ready_for_exam', 'competency_progress', 'created_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'created_at', 'updated_at', 'used_hours', 'purchased_hours', 'referent_instructor',
            'lms_access', 'lms_access_until',
        )

    def get_competency_progress(self, obj):
        return obj.competency_progress()


class InstructorPublicSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    bio = serializers.CharField(source='instructor_profile.bio', read_only=True, default='')

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'full_name', 'bio')


class InstructorProfileSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = InstructorProfile
        fields = ('id', 'user', 'hourly_rate', 'bio', 'is_bookable')
        read_only_fields = ('id', 'hourly_rate')

    def get_user(self, obj):
        return UserSerializer(obj.user).data


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
    class Meta:
        model = Unavailability
        fields = ('id', 'start', 'end', 'reason')

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
        queryset=User.objects.filter(role='INSTRUCTOR', instructor_profile__is_bookable=True)
    )
    meeting_point = serializers.PrimaryKeyRelatedField(queryset=MeetingPoint.objects.all())
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
    meeting_point_name = serializers.CharField(source='meeting_point.name', read_only=True)
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
        fields = ('score', 'comment', 'created_at')
        read_only_fields = ('created_at',)


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

    class Meta:
        model = Offer
        fields = (
            'id', 'name', 'description', 'category', 'category_display', 'hours', 'price', 'price_per_hour',
            'billing_type', 'billing_display', 'includes_lms', 'validity_months',
            'for_code_status', 'for_level', 'gearbox', 'is_featured',
        )


class RecommendationInputSerializer(serializers.Serializer):
    code_status = serializers.ChoiceField(choices=['TO_PASS', 'OBTAINED'])
    level = serializers.ChoiceField(choices=['BEGINNER', 'REFRESH'])
    gearbox = serializers.ChoiceField(choices=['AUTO', 'MANUAL'], required=False, default='AUTO')


class PackageSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    offer = serializers.PrimaryKeyRelatedField(queryset=Offer.objects.filter(is_active=True))
    offer_name = serializers.CharField(source='offer.name', read_only=True)
    offer_category = serializers.CharField(source='offer.category', read_only=True)
    includes_lms = serializers.BooleanField(source='offer.includes_lms', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    def create(self, validated_data):
        offer = validated_data['offer']
        validated_data['hours_purchased'] = offer.hours
        validated_data['amount_paid'] = offer.price
        return super().create(validated_data)

    class Meta:
        model = Package
        fields = (
            'id', 'student', 'student_name', 'offer', 'offer_name', 'offer_category', 'includes_lms',
            'hours_purchased', 'amount_paid', 'status', 'status_display', 'expires_at', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'student', 'hours_purchased', 'amount_paid', 'status', 'expires_at', 'created_at', 'updated_at')


# ---------- Divers ----------

class DocumentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = Document
        fields = ('id', 'student', 'student_name', 'document_type', 'file', 'uploaded_at', 'verified', 'verified_by', 'verified_by_name')
        read_only_fields = ('id', 'uploaded_at', 'verified_by')


class VehicleLogSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)

    class Meta:
        model = VehicleLog
        fields = ('id', 'instructor', 'instructor_name', 'date', 'kilometers', 'fuel_cost', 'maintenance_alert', 'notes', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
