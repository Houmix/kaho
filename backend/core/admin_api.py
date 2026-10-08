"""API du back-office (rôles SUPERVISOR / ADMIN) : tableau de bord, recherche, apprenants, formateurs, candidatures, avis."""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Availability, Document, InstructorApplication, InstructorProfile, Lesson, LessonRating, Package, Slot,
    StudentProfile, User,
)
from .permissions import IsSupervisorOrAdmin
from .serializers import (
    DocumentSerializer, InstructorAdminSerializer, InstructorApplicationSerializer, InstructorCreateSerializer,
    InstructorProfileSerializer, LessonSerializer, PackageSerializer, RatingModerationSerializer, SlotSerializer,
    StudentProfileSerializer, AvailabilitySerializer,
)
from .tasks import send_application_received, send_application_rejected, send_instructor_invite


class AdminPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 200


def invite_link(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}&invite=1"


# ---------- Tableau de bord ----------

class AdminOverviewView(APIView):
    permission_classes = [IsSupervisorOrAdmin]

    def get(self, request):
        now = timezone.now()
        today = timezone.localdate()
        month_start = today.replace(day=1)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        paid = Package.objects.filter(status='COMPLETED', paid_at__date__gte=month_start)
        pending = Package.objects.filter(status='PENDING')
        active_students = StudentProfile.objects.filter(
            Q(booked_slots__date__gte=today - timedelta(days=30)) | Q(packages__status='COMPLETED', packages__paid_at__gte=now - timedelta(days=90))
        ).distinct().count()

        # Taux d'occupation de la semaine : heures réservées / heures ouvertes (disponibilités récurrentes)
        booked = sum(s.duration_hours for s in Slot.objects.filter(status='BOOKED', date__range=(week_start, week_end)))
        opened = 0.0
        for a in Availability.objects.filter(instructor__instructor_profile__is_bookable=True):
            opened += (a.end_time.hour * 60 + a.end_time.minute - a.start_time.hour * 60 - a.start_time.minute) / 60
        occupancy = round(100 * booked / opened) if opened else None

        rating = LessonRating.objects.filter(is_hidden=False).aggregate(avg=Avg('score'), n=Count('id'))
        to_review = sum(1 for s in Slot.objects.filter(status='BOOKED', date__lte=today, lesson__isnull=True) if s.is_past)

        return Response({
            'month': {
                'revenue': float(paid.aggregate(s=Sum('amount_paid'))['s'] or 0),
                'sales': paid.count(),
                'label': today.strftime('%B %Y'),
            },
            'unpaid': {'count': pending.count(), 'amount': float(pending.aggregate(s=Sum('amount_paid'))['s'] or 0)},
            'students': {'active': active_students, 'total': StudentProfile.objects.count()},
            'instructors': {
                'total': User.objects.filter(role='INSTRUCTOR', is_active=True).count(),
                'bookable': InstructorProfile.objects.filter(is_bookable=True, user__is_active=True).count(),
                'pending_applications': InstructorApplication.objects.filter(status='PENDING').count(),
                'without_password': User.objects.filter(role='INSTRUCTOR', is_active=True, password__startswith='!').count(),
            },
            'occupancy': {'percent': occupancy, 'booked_hours': round(booked, 1), 'opened_hours': round(opened, 1)},
            'rating': {'average': round(rating['avg'], 2) if rating['avg'] else None, 'count': rating['n']},
            'today': {
                'lessons': Slot.objects.filter(status='BOOKED', date=today).count(),
                'to_review': to_review,
                'no_shows_week': Slot.objects.filter(status__in=('NO_SHOW', 'CANCELLED_LATE'), date__range=(week_start, week_end)).count(),
            },
            'alerts': self._alerts(today, pending),
        })

    def _alerts(self, today, pending):
        alerts = []
        n = InstructorApplication.objects.filter(status='PENDING').count()
        if n:
            alerts.append({'kind': 'applications', 'count': n, 'text': f"{n} candidature{'s' if n > 1 else ''} de moniteur à examiner", 'href': '/admin/instructors?tab=applications'})
        if pending.exists():
            alerts.append({'kind': 'unpaid', 'count': pending.count(), 'text': f"{pending.count()} achat{'s' if pending.count() > 1 else ''} en attente de paiement", 'href': '/admin/students?filter=unpaid'})
        no_avail = User.objects.filter(role='INSTRUCTOR', is_active=True, instructor_profile__is_bookable=True, availabilities__isnull=True).distinct()
        if no_avail.exists():
            alerts.append({'kind': 'availability', 'count': no_avail.count(), 'text': f"{no_avail.count()} moniteur{'s' if no_avail.count() > 1 else ''} sans disponibilités (invisible{'s' if no_avail.count() > 1 else ''} à la réservation)", 'href': '/admin/instructors'})
        low = StudentProfile.objects.filter(purchased_hours__gt=0).extra(where=['purchased_hours - used_hours <= 1'])
        if low.exists():
            alerts.append({'kind': 'low_hours', 'count': low.count(), 'text': f"{low.count()} élève{'s' if low.count() > 1 else ''} avec ≤ 1 h de crédit", 'href': '/admin/students?filter=low'})
        return alerts


class AdminSearchView(APIView):
    permission_classes = [IsSupervisorOrAdmin]

    def get(self, request):
        q = (request.query_params.get('q') or '').strip()
        if len(q) < 2:
            return Response({'students': [], 'instructors': [], 'packages': [], 'slots': []})
        name_q = Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) | Q(user__email__icontains=q)
        students = StudentProfile.objects.filter(name_q | Q(phone__icontains=q) | Q(neph_number__icontains=q)).select_related('user')[:6]
        instructors = User.objects.filter(role='INSTRUCTOR').filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))[:6]
        packages = Package.objects.none()
        if q.lstrip('#').isdigit():
            packages = Package.objects.filter(pk=int(q.lstrip('#'))).select_related('student__user', 'offer')
        slots = Slot.objects.none()
        try:
            from datetime import date as date_cls
            d = date_cls.fromisoformat(q)
            slots = Slot.objects.filter(date=d).select_related('student__user', 'instructor', 'meeting_point')[:10]
        except ValueError:
            pass
        return Response({
            'students': [{'id': s.id, 'name': s.user.get_full_name(), 'email': s.user.email, 'remaining_hours': s.remaining_hours, 'href': f'/admin/students/{s.id}'} for s in students],
            'instructors': [{'id': u.id, 'name': u.get_full_name(), 'email': u.email, 'href': f'/admin/instructors/{u.id}'} for u in instructors],
            'packages': [{'id': p.id, 'label': f"#{p.id} · {p.student.user.get_full_name()} · {p.offer.name if p.offer else ''}", 'status': p.get_status_display(), 'href': f'/admin/students/{p.student_id}'} for p in packages],
            'slots': [{'id': s.id, 'label': f"{s.date} {s.start_time:%H:%M} · {s.instructor.get_full_name()} · {s.student.user.get_full_name() if s.student else 'libre'}", 'status': s.get_status_display(), 'href': '/instructor/planning'} for s in slots],
        })


# ---------- Apprenants ----------

class AdminStudentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsSupervisorOrAdmin]
    pagination_class = AdminPagination

    def get_queryset(self):
        qs = StudentProfile.objects.select_related('user', 'referent_instructor').order_by('user__last_name', 'user__first_name')
        p = self.request.query_params
        if p.get('q'):
            q = p['q']
            qs = qs.filter(Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) | Q(user__email__icontains=q) | Q(phone__icontains=q))
        if p.get('referent'):
            qs = qs.filter(referent_instructor_id=p['referent'])
        f = p.get('filter')
        if f == 'unpaid':
            qs = qs.filter(packages__status='PENDING').distinct()
        elif f == 'low':
            qs = qs.filter(purchased_hours__gt=0).extra(where=['purchased_hours - used_hours <= 1'])
        elif f == 'ready':
            qs = qs.filter(ready_for_exam=True)
        elif f == 'lms':
            qs = qs.filter(lms_access=True)
        return qs

    @action(detail=True, methods=['get'])
    def overview(self, request, pk=None):
        """Vue 360° : profil, achats, créneaux, bilans, documents."""
        st = self.get_object()
        today = timezone.localdate()
        slots = Slot.objects.filter(student=st).select_related('instructor', 'meeting_point', 'lesson')
        lessons = Lesson.objects.filter(student=st).select_related('slot__instructor', 'slot__meeting_point').prefetch_related('assessments__competency').order_by('-slot__date')
        return Response({
            'student': StudentProfileSerializer(st).data,
            'packages': PackageSerializer(st.packages.select_related('offer'), many=True).data,
            'upcoming_slots': SlotSerializer(slots.filter(date__gte=today, status='BOOKED').order_by('date', 'start_time'), many=True).data,
            'past_slots': SlotSerializer(slots.filter(date__lt=today).order_by('-date', '-start_time')[:30], many=True).data,
            'lessons': LessonSerializer(lessons, many=True).data,
            'documents': DocumentSerializer(st.documents.all(), many=True).data,
            'progress': st.competency_progress(),
        })

    @action(detail=True, methods=['patch'])
    def update_profile(self, request, pk=None):
        """Champs modifiables par l'admin : référent, NEPH, boîte, prêt examen, contact d'urgence, téléphone."""
        st = self.get_object()
        allowed = {'referent_instructor', 'neph_number', 'license_type', 'ready_for_exam', 'emergency_contact', 'emergency_phone', 'phone', 'lms_access', 'lms_access_until'}
        data = {k: v for k, v in request.data.items() if k in allowed}
        for k, v in data.items():
            setattr(st, k + '_id' if k == 'referent_instructor' else k, v or None if k in ('referent_instructor', 'lms_access_until') else v)
        st.save()
        return Response(StudentProfileSerializer(st).data)

    @action(detail=True, methods=['post'])
    def adjust_hours(self, request, pk=None):
        """Ajout manuel d'heures (geste commercial, régularisation). Crée un achat 'offert' tracé."""
        st = self.get_object()
        try:
            hours = float(request.data.get('hours'))
        except (TypeError, ValueError):
            return Response({'detail': 'Nombre d’heures invalide.'}, status=400)
        note = (request.data.get('note') or '').strip()
        if hours <= 0 or not note:
            return Response({'detail': 'Indiquez un nombre d’heures positif et un motif.'}, status=400)
        pkg = Package.objects.create(student=st, hours_purchased=hours, amount_paid=0, status='COMPLETED', note=f"Ajout manuel par {request.user.get_full_name()} : {note}")
        return Response(PackageSerializer(pkg).data, status=201)


class AdminPackageViewSet(viewsets.GenericViewSet):
    """Validation / annulation des paiements depuis le back-office."""
    queryset = Package.objects.select_related('student__user', 'offer')
    serializer_class = PackageSerializer
    permission_classes = [IsSupervisorOrAdmin]

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        pkg = self.get_object()
        if pkg.status == 'COMPLETED':
            return Response({'detail': 'Déjà validé.'}, status=400)
        pkg.status = 'COMPLETED'
        pkg.note = ((pkg.note + '\n') if pkg.note else '') + f"Paiement validé par {request.user.get_full_name()} le {timezone.localdate():%d/%m/%Y}" + (f" — {request.data.get('note')}" if request.data.get('note') else '')
        pkg.save()
        return Response(PackageSerializer(pkg).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        pkg = self.get_object()
        if pkg.status != 'PENDING':
            return Response({'detail': 'Seul un achat en attente peut être annulé.'}, status=400)
        pkg.status = 'FAILED'
        pkg.note = ((pkg.note + '\n') if pkg.note else '') + f"Annulé par {request.user.get_full_name()}"
        pkg.save()
        return Response(PackageSerializer(pkg).data)


# ---------- Formateurs ----------

class AdminInstructorViewSet(viewsets.ModelViewSet):
    serializer_class = InstructorAdminSerializer
    permission_classes = [IsSupervisorOrAdmin]
    pagination_class = AdminPagination
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        qs = User.objects.filter(role='INSTRUCTOR').select_related('instructor_profile').order_by('last_name', 'first_name')
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))
        if self.request.query_params.get('active') == '1':
            qs = qs.filter(is_active=True)
        return qs

    def create(self, request, *args, **kwargs):
        s = InstructorCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        send_instructor_invite.delay(user.email, user.first_name, invite_link(user))
        return Response(InstructorAdminSerializer(user).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        for k in ('first_name', 'last_name', 'is_active'):
            if k in request.data:
                setattr(user, k, request.data[k])
        user.save()
        profile, _ = InstructorProfile.objects.get_or_create(user=user)
        ps = InstructorProfileSerializer(profile, data={k: v for k, v in request.data.items() if k in ('phone', 'gearbox', 'vehicle', 'bio', 'is_bookable')}, partial=True)
        ps.is_valid(raise_exception=True)
        ps.save()
        if 'hourly_rate' in request.data:
            profile.hourly_rate = request.data['hourly_rate']
            profile.save(update_fields=['hourly_rate'])
        user.refresh_from_db()
        return Response(InstructorAdminSerializer(user).data)

    @action(detail=True, methods=['post'])
    def resend_invite(self, request, pk=None):
        user = self.get_object()
        send_instructor_invite.delay(user.email, user.first_name, invite_link(user))
        return Response({'detail': f"Invitation renvoyée à {user.email}."})

    @action(detail=True, methods=['get'])
    def overview(self, request, pk=None):
        user = self.get_object()
        today = timezone.localdate()
        ratings = LessonRating.objects.filter(lesson__slot__instructor=user).select_related('lesson__student__user', 'lesson__slot').order_by('-created_at')[:20]
        return Response({
            'instructor': InstructorAdminSerializer(user).data,
            'availabilities': AvailabilitySerializer(Availability.objects.filter(instructor=user), many=True).data,
            'upcoming_slots': SlotSerializer(Slot.objects.filter(instructor=user, date__gte=today, status='BOOKED').select_related('student__user', 'meeting_point').order_by('date', 'start_time')[:30], many=True).data,
            'students': StudentProfileSerializer(StudentProfile.objects.filter(Q(referent_instructor=user) | Q(booked_slots__instructor=user)).distinct().select_related('user'), many=True).data,
            'ratings': RatingModerationSerializer(ratings, many=True).data,
        })


class InstructorApplicationPublicView(APIView):
    """Dépôt public d'une candidature (multipart avec pièces jointes)."""
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        s = InstructorApplicationSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        app = s.save()
        send_application_received.delay(app.email, app.first_name)
        return Response({'detail': 'Candidature enregistrée. Vous recevrez un email après examen.'}, status=status.HTTP_201_CREATED)


class AdminApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InstructorApplicationSerializer
    permission_classes = [IsSupervisorOrAdmin]
    pagination_class = AdminPagination

    def get_queryset(self):
        qs = InstructorApplication.objects.select_related('reviewed_by', 'created_user')
        st = self.request.query_params.get('status')
        return qs.filter(status=st) if st else qs

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def approve(self, request, pk=None):
        """Validation en 1 clic : crée le compte moniteur et envoie l'invitation."""
        app = self.get_object()
        if app.status != 'PENDING':
            return Response({'detail': 'Candidature déjà traitée.'}, status=400)
        if User.objects.filter(email__iexact=app.email).exists():
            return Response({'detail': 'Un compte existe déjà avec cet email.'}, status=400)
        try:
            hourly_rate = float(request.data.get('hourly_rate') or 0)
        except ValueError:
            hourly_rate = 0
        user = User.objects.create_user(username=app.email, email=app.email, first_name=app.first_name, last_name=app.last_name, role='INSTRUCTOR')
        user.set_unusable_password()
        user.save(update_fields=['password'])
        profile, _ = InstructorProfile.objects.get_or_create(user=user)
        profile.phone, profile.gearbox, profile.hourly_rate = app.phone, app.gearbox, hourly_rate
        profile.save()
        app.status, app.reviewed_by, app.reviewed_at, app.created_user = 'APPROVED', request.user, timezone.now(), user
        app.admin_note = request.data.get('note', '')
        app.save()
        send_instructor_invite.delay(user.email, user.first_name, invite_link(user))
        return Response(InstructorApplicationSerializer(app).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        app = self.get_object()
        if app.status != 'PENDING':
            return Response({'detail': 'Candidature déjà traitée.'}, status=400)
        app.status, app.reviewed_by, app.reviewed_at = 'REJECTED', request.user, timezone.now()
        app.admin_note = request.data.get('note', '')
        app.save()
        send_application_rejected.delay(app.email, app.first_name, app.admin_note if request.data.get('notify_note') else '')
        return Response(InstructorApplicationSerializer(app).data)


# ---------- Avis ----------

class AdminRatingViewSet(viewsets.ModelViewSet):
    serializer_class = RatingModerationSerializer
    permission_classes = [IsSupervisorOrAdmin]
    pagination_class = AdminPagination
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        qs = LessonRating.objects.select_related('lesson__student__user', 'lesson__slot__instructor').order_by('-created_at')
        p = self.request.query_params
        if p.get('instructor'):
            qs = qs.filter(lesson__slot__instructor_id=p['instructor'])
        if p.get('max_score'):
            qs = qs.filter(score__lte=p['max_score'])
        if p.get('unanswered') == '1':
            qs = qs.filter(reply='').exclude(comment='')
        return qs
