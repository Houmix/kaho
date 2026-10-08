from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, StudentProfile, InstructorProfile, InstructorApplication, Availability, Unavailability, MeetingPoint, Slot,
    Competency, Lesson, CompetencyAssessment, LessonRating, Offer, Package, Document, VehicleLog,
)


@admin.register(InstructorApplication)
class InstructorApplicationAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'email', 'phone', 'gearbox', 'status', 'created_at', 'reviewed_by')
    list_filter = ('status', 'gearbox')
    search_fields = ('first_name', 'last_name', 'email')
    readonly_fields = ('created_at', 'reviewed_at', 'reviewed_by', 'created_user')


@admin.register(Competency)
class CompetencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'label', 'group', 'order')
    list_editable = ('order',)
    list_filter = ('group',)
    search_fields = ('code', 'label')


class CompetencyAssessmentInline(admin.TabularInline):
    model = CompetencyAssessment
    extra = 0
    autocomplete_fields = ('competency',)


class LessonRatingInline(admin.StackedInline):
    model = LessonRating
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(LessonRating)
class LessonRatingAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'get_instructor', 'score', 'comment', 'created_at')
    list_filter = ('score', 'lesson__slot__instructor')
    readonly_fields = ('created_at',)

    def get_instructor(self, obj):
        return obj.lesson.slot.instructor.get_full_name()
    get_instructor.short_description = 'Moniteur'


class AvailabilityInline(admin.TabularInline):
    model = Availability
    extra = 0


class UnavailabilityInline(admin.TabularInline):
    model = Unavailability
    extra = 0


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'gearbox', 'hourly_rate', 'is_bookable')
    list_editable = ('hourly_rate', 'is_bookable')
    list_filter = ('gearbox', 'is_bookable')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('instructor', 'weekday', 'start_time', 'end_time')
    list_filter = ('weekday', 'instructor')


@admin.register(Unavailability)
class UnavailabilityAdmin(admin.ModelAdmin):
    list_display = ('instructor', 'start', 'end', 'reason')
    list_filter = ('instructor',)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'hours', 'price', 'price_per_hour', 'billing_type', 'includes_lms', 'validity_months', 'is_featured', 'is_active', 'display_order')
    list_editable = ('is_featured', 'is_active', 'display_order')
    list_filter = ('category', 'is_active', 'is_featured', 'includes_lms', 'billing_type')
    search_fields = ('name',)
    fieldsets = (
        (None, {'fields': ('name', 'description', 'category')}),
        ('Contenu', {'fields': ('hours', 'includes_lms', 'validity_months')}),
        ('Prix & facturation', {'fields': ('price', 'billing_type')}),
        ('Simulateur (recommandation automatique)', {
            'fields': ('for_code_status', 'for_level', 'gearbox'),
            'description': "Profil d'élève auquel cette offre correspond le mieux. « Indifférent » = ne pèse pas dans le score.",
        }),
        ('Affichage sur le site', {'fields': ('is_active', 'is_featured', 'display_order')}),
    )

    def price_per_hour(self, obj):
        return f"{obj.price_per_hour} €/h" if obj.price_per_hour else '—'
    price_per_hour.short_description = 'Prix / heure'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'get_full_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    inlines = (AvailabilityInline, UnavailabilityInline)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Kaho Info', {'fields': ('role',)}),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('get_user_name', 'phone', 'referent_instructor', 'neph_number', 'purchased_hours', 'used_hours', 'remaining_hours', 'ready_for_exam')
    list_filter = ('license_type', 'ready_for_exam', 'referent_instructor')
    autocomplete_fields = ('referent_instructor',)
    search_fields = ('user__email', 'neph_number', 'user__first_name', 'user__last_name')
    ordering = ('user__last_name',)
    readonly_fields = ('created_at', 'updated_at')

    def get_user_name(self, obj):
        return obj.user.get_full_name()
    get_user_name.short_description = 'Étudiant'


@admin.register(MeetingPoint)
class MeetingPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'latitude', 'longitude')
    search_fields = ('name', 'address')


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ('date', 'start_time', 'meeting_point', 'status', 'get_student_name', 'get_instructor_name', 'hours_debited', 'hours_refunded')
    list_filter = ('status', 'hours_debited', 'hours_refunded', 'date', 'instructor')
    search_fields = ('student__user__email', 'instructor__email')
    readonly_fields = ('hours_debited', 'hours_refunded', 'created_at', 'updated_at')
    actions = ('refund_hours_action',)

    @admin.action(description="Dérogation : re-créditer l'heure débitée (justificatif à renseigner ensuite)")
    def refund_hours_action(self, request, queryset):
        n = sum(1 for s in queryset if s.refund_hours(note=f"Dérogation accordée par {request.user.get_full_name()}"))
        self.message_user(request, f"{n} créneau(x) re-crédité(s).")

    def get_student_name(self, obj):
        return obj.student.user.get_full_name() if obj.student else '-'
    get_student_name.short_description = 'Étudiant'

    def get_instructor_name(self, obj):
        return obj.instructor.get_full_name()
    get_instructor_name.short_description = 'Monitrice'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('get_student_name', 'slot', 'attended', 'weather_conditions')
    list_filter = ('attended', 'created_at', 'slot__instructor')
    search_fields = ('student__user__email',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = (CompetencyAssessmentInline, LessonRatingInline)

    def get_student_name(self, obj):
        return obj.student.user.get_full_name()
    get_student_name.short_description = 'Étudiant'


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('get_student_name', 'offer', 'hours_purchased', 'amount_paid', 'status', 'expires_at', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'offer', 'created_at')
    autocomplete_fields = ('student',)
    readonly_fields = ('expires_at', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('student', 'offer', 'hours_purchased', 'amount_paid')}),
        ('Paiement', {'fields': ('status', 'stripe_payment_id', 'note'),
                      'description': "Passer en « Payé » crédite automatiquement les heures et l'accès LMS à l'élève."}),
        ('Dates', {'fields': ('expires_at', 'created_at', 'updated_at')}),
    )
    search_fields = ('student__user__email',)
    readonly_fields = ('created_at', 'updated_at')

    def get_student_name(self, obj):
        return obj.student.user.get_full_name()
    get_student_name.short_description = 'Étudiant'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('get_student_name', 'document_type', 'verified', 'uploaded_at')
    list_filter = ('document_type', 'verified', 'uploaded_at')
    search_fields = ('student__user__email',)
    readonly_fields = ('uploaded_at',)

    def get_student_name(self, obj):
        return obj.student.user.get_full_name()
    get_student_name.short_description = 'Étudiant'


@admin.register(VehicleLog)
class VehicleLogAdmin(admin.ModelAdmin):
    list_display = ('get_instructor_name', 'date', 'kilometers', 'fuel_cost', 'maintenance_alert')
    list_filter = ('date', 'instructor')
    search_fields = ('instructor__email',)
    readonly_fields = ('created_at', 'updated_at')

    def get_instructor_name(self, obj):
        return obj.instructor.get_full_name()
    get_instructor_name.short_description = 'Monitrice'
