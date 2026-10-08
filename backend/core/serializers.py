from rest_framework import serializers
from .models import User, StudentProfile, MeetingPoint, Slot, Lesson, Offer, Package, Document, VehicleLog


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Un compte existe déjà avec cet email.")
        return value.lower()

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['email'],
            role='STUDENT',
            **validated_data,
        )


class OfferSerializer(serializers.ModelSerializer):
    price_per_hour = serializers.FloatField(read_only=True)

    class Meta:
        model = Offer
        fields = ('id', 'name', 'description', 'hours', 'price', 'price_per_hour', 'is_featured')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role')
        read_only_fields = ('id',)


class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    remaining_hours = serializers.FloatField(read_only=True)

    class Meta:
        model = StudentProfile
        fields = (
            'id', 'user', 'neph_number', 'purchased_hours', 'used_hours',
            'remaining_hours', 'emergency_contact', 'emergency_phone',
            'license_type', 'ready_for_exam', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'used_hours')


class MeetingPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingPoint
        fields = ('id', 'name', 'description', 'address', 'latitude', 'longitude', 'created_at')
        read_only_fields = ('id', 'created_at')


class SlotSerializer(serializers.ModelSerializer):
    meeting_point_name = serializers.CharField(source='meeting_point.name', read_only=True)
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True, allow_null=True)
    duration_hours = serializers.FloatField(read_only=True)

    class Meta:
        model = Slot
        fields = (
            'id', 'date', 'start_time', 'end_time', 'status', 'meeting_point',
            'meeting_point_name', 'student', 'student_name', 'instructor',
            'duration_hours', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class LessonSerializer(serializers.ModelSerializer):
    slot = SlotSerializer(read_only=True)
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)

    class Meta:
        model = Lesson
        fields = (
            'id', 'slot', 'student', 'student_name', 'attended', 'remc_skills',
            'weather_conditions', 'instructor_notes', 'voice_memo_url',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class PackageSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    offer = serializers.PrimaryKeyRelatedField(queryset=Offer.objects.filter(is_active=True))
    offer_name = serializers.CharField(source='offer.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    def create(self, validated_data):
        offer = validated_data['offer']
        validated_data['hours_purchased'] = offer.hours
        validated_data['amount_paid'] = offer.price
        return super().create(validated_data)

    class Meta:
        model = Package
        fields = (
            'id', 'student', 'student_name', 'offer', 'offer_name', 'hours_purchased',
            'amount_paid', 'status', 'status_display', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'student', 'hours_purchased', 'amount_paid', 'status', 'created_at', 'updated_at')


class DocumentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = Document
        fields = (
            'id', 'student', 'student_name', 'document_type', 'file',
            'uploaded_at', 'verified', 'verified_by', 'verified_by_name'
        )
        read_only_fields = ('id', 'uploaded_at', 'verified_by')


class VehicleLogSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)

    class Meta:
        model = VehicleLog
        fields = (
            'id', 'instructor', 'instructor_name', 'date', 'kilometers',
            'fuel_cost', 'maintenance_alert', 'notes', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
