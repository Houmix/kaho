from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StudentProfile, MeetingPoint, Slot, Lesson, Offer, Package, Document, VehicleLog


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'hours', 'price', 'price_per_hour', 'is_featured', 'is_active', 'display_order')
    list_editable = ('is_featured', 'is_active', 'display_order')
    list_filter = ('is_active', 'is_featured')
    search_fields = ('name',)
    fieldsets = (
        (None, {'fields': ('name', 'description')}),
        ('Contenu & prix', {'fields': ('hours', 'price')}),
        ('Affichage sur le site', {'fields': ('is_active', 'is_featured', 'display_order')}),
    )

    def price_per_hour(self, obj):
        return f"{obj.price_per_hour} €/h"
    price_per_hour.short_description = 'Prix / heure'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'get_full_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Kaho Info', {'fields': ('role',)}),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('get_user_name', 'neph_number', 'purchased_hours', 'used_hours', 'remaining_hours', 'ready_for_exam')
    list_filter = ('license_type', 'ready_for_exam')
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
    list_display = ('date', 'start_time', 'meeting_point', 'status', 'get_student_name', 'get_instructor_name')
    list_filter = ('status', 'date', 'meeting_point')
    search_fields = ('student__user__email', 'instructor__email')
    readonly_fields = ('created_at', 'updated_at')

    def get_student_name(self, obj):
        return obj.student.user.get_full_name() if obj.student else '-'
    get_student_name.short_description = 'Étudiant'

    def get_instructor_name(self, obj):
        return obj.instructor.get_full_name()
    get_instructor_name.short_description = 'Monitrice'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('get_student_name', 'slot', 'attended', 'weather_conditions')
    list_filter = ('attended', 'created_at')
    search_fields = ('student__user__email',)
    readonly_fields = ('created_at', 'updated_at')

    def get_student_name(self, obj):
        return obj.student.user.get_full_name()
    get_student_name.short_description = 'Étudiant'


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('get_student_name', 'offer', 'hours_purchased', 'amount_paid', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'offer', 'created_at')
    autocomplete_fields = ('student',)
    fieldsets = (
        (None, {'fields': ('student', 'offer', 'hours_purchased', 'amount_paid')}),
        ('Paiement', {'fields': ('status', 'stripe_payment_id', 'note'),
                      'description': "Passer en « Payé » crédite automatiquement les heures à l'élève."}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
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
