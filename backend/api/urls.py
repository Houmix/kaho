from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from core.views import RegisterView
from core.viewsets import (
    UserViewSet, StudentProfileViewSet, MeetingPointViewSet, SlotViewSet,
    LessonViewSet, OfferViewSet, PackageViewSet, DocumentViewSet, VehicleLogViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'student-profiles', StudentProfileViewSet, basename='student-profile')
router.register(r'meeting-points', MeetingPointViewSet, basename='meeting-point')
router.register(r'slots', SlotViewSet, basename='slot')
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'offers', OfferViewSet, basename='offer')
router.register(r'packages', PackageViewSet, basename='package')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'vehicle-logs', VehicleLogViewSet, basename='vehicle-log')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
