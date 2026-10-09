from django.urls import path
from rest_framework.routers import DefaultRouter

from .admin_views import (
    AdminCourseViewSet, AdminExamViewSet, AdminLessonViewSet, AdminQuestionViewSet, AdminQuizViewSet, AdminSectionViewSet, ThemesView,
)
from .views import (
    AdminLmsOverviewView, AdminStudentLmsView, CourseViewSet, DemoView, ExamAttemptViewSet, ExamViewSet, LessonViewSet, QuizViewSet, RevisionView,
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='lms-course')
router.register(r'lessons', LessonViewSet, basename='lms-lesson')
router.register(r'quizzes', QuizViewSet, basename='lms-quiz')
router.register(r'exams', ExamViewSet, basename='lms-exam')
router.register(r'exam-attempts', ExamAttemptViewSet, basename='lms-exam-attempt')
router.register(r'admin/courses', AdminCourseViewSet, basename='lms-admin-course')
router.register(r'admin/sections', AdminSectionViewSet, basename='lms-admin-section')
router.register(r'admin/lessons', AdminLessonViewSet, basename='lms-admin-lesson')
router.register(r'admin/quizzes', AdminQuizViewSet, basename='lms-admin-quiz')
router.register(r'admin/questions', AdminQuestionViewSet, basename='lms-admin-question')
router.register(r'admin/exams', AdminExamViewSet, basename='lms-admin-exam')

urlpatterns = router.urls + [
    path('demo/', DemoView.as_view(), name='lms-demo'),
    path('revision/', RevisionView.as_view(), name='lms-revision'),
    path('admin/overview/', AdminLmsOverviewView.as_view(), name='lms-admin-overview'),
    path('admin/themes/', ThemesView.as_view(), name='lms-admin-themes'),
    path('admin/students/<int:student_id>/', AdminStudentLmsView.as_view(), name='lms-admin-student'),
]
