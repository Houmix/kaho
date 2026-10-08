from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from core.views import PasswordResetConfirmView, PasswordResetRequestView, RegisterView
from core.viewsets import (
    UserViewSet, StudentProfileViewSet, InstructorViewSet, AvailabilityViewSet, UnavailabilityViewSet,
    MeetingPointViewSet, SlotViewSet, CompetencyViewSet, LessonViewSet, OfferViewSet, PackageViewSet,
    DocumentViewSet, VehicleLogViewSet,
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
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'vehicle-logs', VehicleLogViewSet, basename='vehicle-log')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
