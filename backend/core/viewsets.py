from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, StudentProfile, MeetingPoint, Slot, Lesson, Package, Document, VehicleLog
from .serializers import (
    UserSerializer, StudentProfileSerializer, MeetingPointSerializer,
    SlotSerializer, LessonSerializer, PackageSerializer, DocumentSerializer, VehicleLogSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'INSTRUCTOR':
            return User.objects.filter(role='STUDENT')
        return User.objects.filter(id=self.request.user.id)


class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'INSTRUCTOR':
            return StudentProfile.objects.all()
        return StudentProfile.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        try:
            profile = StudentProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except StudentProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)


class MeetingPointViewSet(viewsets.ModelViewSet):
    queryset = MeetingPoint.objects.all()
    serializer_class = MeetingPointSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        self.permission_classes = [permissions.IsAdminUser]
        return super().create(request, *args, **kwargs)


class SlotViewSet(viewsets.ModelViewSet):
    queryset = Slot.objects.all()
    serializer_class = SlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'INSTRUCTOR':
            return Slot.objects.filter(instructor=self.request.user)
        return Slot.objects.filter(status='AVAILABLE')

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)

    @action(detail=False, methods=['get'])
    def available_slots(self, request):
        slots = Slot.objects.filter(status='AVAILABLE', student__isnull=True)
        serializer = self.get_serializer(slots, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def book_slot(self, request, pk=None):
        slot = self.get_object()
        if slot.status != 'AVAILABLE':
            return Response({'error': 'Slot not available'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student_profile = StudentProfile.objects.get(user=request.user)
            if student_profile.remaining_hours < slot.duration_hours:
                return Response({'error': 'Not enough hours'}, status=status.HTTP_400_BAD_REQUEST)

            slot.status = 'BOOKED'
            slot.student = student_profile
            slot.save()

            serializer = self.get_serializer(slot)
            return Response(serializer.data)
        except StudentProfile.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def cancel_slot(self, request, pk=None):
        slot = self.get_object()
        if slot.status != 'BOOKED':
            return Response({'error': 'Cannot cancel this slot'}, status=status.HTTP_400_BAD_REQUEST)

        slot.status = 'AVAILABLE'
        slot.student = None
        slot.save()

        serializer = self.get_serializer(slot)
        return Response(serializer.data)


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'INSTRUCTOR':
            return Lesson.objects.filter(slot__instructor=self.request.user)
        return Lesson.objects.filter(student__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()


class PackageViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'INSTRUCTOR':
            return Package.objects.all()
        return Package.objects.filter(student__user=self.request.user)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'INSTRUCTOR':
            return Document.objects.all()
        return Document.objects.filter(student__user=self.request.user)

    def perform_create(self, serializer):
        student_profile = StudentProfile.objects.get(user=self.request.user)
        serializer.save(student=student_profile)


class VehicleLogViewSet(viewsets.ModelViewSet):
    queryset = VehicleLog.objects.all()
    serializer_class = VehicleLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'INSTRUCTOR':
            return VehicleLog.objects.filter(instructor=self.request.user)
        return VehicleLog.objects.none()

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)
