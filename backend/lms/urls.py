from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AdminLmsOverviewView, CourseViewSet, DemoView, ExamAttemptViewSet, ExamViewSet, LessonViewSet, QuizViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='lms-course')
router.register(r'lessons', LessonViewSet, basename='lms-lesson')
router.register(r'quizzes', QuizViewSet, basename='lms-quiz')
router.register(r'exams', ExamViewSet, basename='lms-exam')
router.register(r'exam-attempts', ExamAttemptViewSet, basename='lms-exam-attempt')

urlpatterns = router.urls + [
    path('demo/', DemoView.as_view(), name='lms-demo'),
    path('admin/overview/', AdminLmsOverviewView.as_view(), name='lms-admin-overview'),
]
