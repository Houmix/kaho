from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from core.admin_api import (
    AdminActivityViewSet, AdminApplicationViewSet, AdminCalendarView, AdminDocumentViewSet, AdminInstructorViewSet, AdminInvoiceViewSet,
    AdminOverviewView, AdminPackageViewSet, AdminPayrollView, AdminRatingViewSet, AdminSalesView, AdminSearchView,
    AdminSlotViewSet, AdminStudentViewSet, InstructorApplicationPublicView,
)
from core.views import InternalRemindersView, PasswordResetConfirmView, PasswordResetRequestView, RegisterView
from core.viewsets import (
    UserViewSet, StudentProfileViewSet, InstructorViewSet, AvailabilityViewSet, UnavailabilityViewSet,
    MeetingPointViewSet, SlotViewSet, CompetencyViewSet, LessonViewSet, OfferViewSet, PackageViewSet,
    InvoiceViewSet, DocumentViewSet, VehicleLogViewSet,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'student-profiles', StudentProfileViewSet, basename='student-profile')
router.register(r'instructors', InstructorViewSet, basename='instructor')
router.register(r'availabilities', AvailabilityViewSet, basename='availability')
router.register(r'unavailabilities', UnavailabilityViewSet, basename='unavailability')
router.register(r'meeting-points', MeetingPointViewSet, basename='meeting-point')
router.register(r'slots', SlotViewSet, basename='slot')
router.register(r'competencies', CompetencyViewSet, basename='competency')
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'offers', OfferViewSet, basename='offer')
router.register(r'packages', PackageViewSet, basename='package')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'admin/invoices', AdminInvoiceViewSet, basename='admin-invoice')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'vehicle-logs', VehicleLogViewSet, basename='vehicle-log')
router.register(r'admin/students', AdminStudentViewSet, basename='admin-student')
router.register(r'admin/packages', AdminPackageViewSet, basename='admin-package')
router.register(r'admin/instructors', AdminInstructorViewSet, basename='admin-instructor')
router.register(r'admin/applications', AdminApplicationViewSet, basename='admin-application')
router.register(r'admin/ratings', AdminRatingViewSet, basename='admin-rating')
router.register(r'admin/slots', AdminSlotViewSet, basename='admin-slot')
router.register(r'admin/activity', AdminActivityViewSet, basename='admin-activity')
router.register(r'admin/documents', AdminDocumentViewSet, basename='admin-document')

urlpatterns = [
    path('', include(router.urls)),
    path('lms/', include('lms.urls')),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('admin/overview/', AdminOverviewView.as_view(), name='admin_overview'),
    path('admin/search/', AdminSearchView.as_view(), name='admin_search'),
    path('admin/calendar/', AdminCalendarView.as_view(), name='admin_calendar'),
    path('admin/sales/', AdminSalesView.as_view(), name='admin_sales'),
    path('admin/payroll/', AdminPayrollView.as_view(), name='admin_payroll'),
    path('internal/reminders/', InternalRemindersView.as_view(), name='internal_reminders'),
    path('instructor-applications/', InstructorApplicationPublicView.as_view(), name='instructor_application'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
