from datetime import date as date_cls, datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    User, StudentProfile, InstructorProfile, Availability, Unavailability, MeetingPoint, Slot,
    Competency, Lesson, CompetencyAssessment, LessonRating, Offer, Package, Invoice, Document, VehicleLog, log_activity,
)
from .permissions import IsInstructor, IsStaff, IsStudent, IsSupervisorOrAdmin
from .scheduling import availability_meeting_point, free_windows, is_window_free
from .serializers import (
    UserSerializer, StudentProfileSerializer, InstructorPublicSerializer, InstructorProfileSerializer,
    AvailabilitySerializer, UnavailabilitySerializer, FreeWindowSerializer, BookingSerializer,
    MeetingPointSerializer, SlotSerializer, CompetencySerializer, LessonSerializer, LessonRatingSerializer,
    OfferSerializer, RecommendationInputSerializer, PackageSerializer, InvoiceSerializer, DocumentSerializer, VehicleLogSerializer,
)
from .tasks import send_booking_confirmation


# ---------- Utilisateurs & profils ----------

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role in User.STAFF_ROLES:
            return User.objects.filter(role='STUDENT')
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['get'])
    def me(self, request):
        return Response(self.get_serializer(request.user).data)


def _logbook(profile):
    """État courant de chaque compétence = dernière évaluation saisie."""
    latest = {}
    qs = (CompetencyAssessment.objects.filter(lesson__student=profile)
          .select_related('lesson__slot').order_by('-lesson__slot__date', '-lesson__created_at'))
    for a in qs:
        latest.setdefault(a.competency_id, (a.status, a.lesson.slot.date))
    competencies = [
        {
            'id': c.id, 'code': c.code, 'label': c.label, 'group': c.group, 'group_label': c.get_group_display(),
            'status': latest.get(c.id, ('NOT_COVERED', None))[0],
            'last_assessed': latest.get(c.id, (None, None))[1],
        }
        for c in Competency.objects.all()
    ]
    lessons = (Lesson.objects.filter(student=profile)
               .select_related('slot__instructor', 'slot__meeting_point', 'student__user')
               .prefetch_related('assessments__competency').order_by('-slot__date', '-slot__start_time'))
    return {
        'student': StudentProfileSerializer(profile).data,
        'progress': profile.competency_progress(),
        'competencies': competencies,
        'lessons': LessonSerializer(lessons, many=True).data,
    }


class StudentProfileViewSet(viewsets.ModelViewSet):
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        qs = StudentProfile.objects.select_related('user', 'referent_instructor')
        if user.role in User.BACKOFFICE_ROLES:
            return qs
        if user.teaches:
            return qs.filter(Q(referent_instructor=user) | Q(booked_slots__instructor=user)).distinct()
        return qs.filter(user=user)

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        try:
            return Response(self.get_serializer(StudentProfile.objects.get(user=request.user)).data)
        except StudentProfile.DoesNotExist:
            return Response({'detail': 'Profil introuvable'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], permission_classes=[IsStudent])
    def my_logbook(self, request):
        return Response(_logbook(StudentProfile.objects.get(user=request.user)))

    @action(detail=True, methods=['get'], permission_classes=[IsStaff])
    def logbook(self, request, pk=None):
        return Response(_logbook(self.get_object()))


class InstructorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.instructors().filter(instructor_profile__is_bookable=True).order_by('last_name')
    serializer_class = InstructorPublicSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsInstructor])
    def me(self, request):
        profile, _ = InstructorProfile.objects.get_or_create(user=request.user)
        if request.method == 'PATCH':
            s = InstructorProfileSerializer(profile, data=request.data, partial=True)
            s.is_valid(raise_exception=True)
            s.save()
        return Response(InstructorProfileSerializer(profile).data)

    @action(detail=False, methods=['post'], permission_classes=[IsInstructor])
    def message(self, request):
        """Contact direct d'un élève suivi (email et/ou SMS), tracé dans l'historique."""
        from .tasks import send_bulk_message
        try:
            st = StudentProfile.objects.filter(Q(referent_instructor=request.user) | Q(booked_slots__instructor=request.user)).distinct().get(pk=request.data.get('student'))
        except (StudentProfile.DoesNotExist, ValueError, TypeError):
            return Response({'detail': "Cet élève n'est pas dans votre suivi."}, status=404)
        channel = request.data.get('channel', 'email')
        subject, body = (request.data.get('subject') or '').strip(), (request.data.get('body') or '').strip()
        if not body or (channel != 'sms' and not subject):
            return Response({'detail': 'Objet et message requis.'}, status=400)
        if channel in ('sms', 'both') and not st.phone:
            return Response({'detail': "Pas de numéro de mobile pour cet élève."}, status=400)
        send_bulk_message.delay([st.user_id], subject or 'Message de votre moniteur', f"{body}\n\n— {request.user.get_full_name()}", channel)
        log_activity('MESSAGE', f"{'SMS' if channel == 'sms' else 'Email'} de {request.user.get_full_name()} à {st.user.get_full_name()} : {subject or body[:40]}", actor=request.user, student=st, instructor=request.user)
        return Response({'detail': 'Message envoyé.'})

    @action(detail=False, methods=['get'], permission_classes=[IsInstructor])
    def dashboard(self, request):
        user = request.user
        today = timezone.localdate()
        profile, _ = InstructorProfile.objects.get_or_create(user=user)
        upcoming = (Slot.objects.filter(instructor=user, status='BOOKED', date__gte=today)
                    .select_related('student__user', 'meeting_point')[:50])
        to_review = (Slot.objects.filter(instructor=user, status='BOOKED', date__lte=today, lesson__isnull=True)
                     .select_related('student__user', 'meeting_point').order_by('-date', '-start_time'))
        to_review = [s for s in to_review if s.is_past]
        month_lessons = Lesson.objects.filter(
            slot__instructor=user, attended=True, slot__date__year=today.year, slot__date__month=today.month
        ).select_related('slot')
        hours = round(sum(l.slot.duration_hours for l in month_lessons), 2)
        students = (StudentProfile.objects.filter(Q(referent_instructor=user) | Q(booked_slots__instructor=user))
                    .distinct().select_related('user'))
        rating = LessonRating.objects.filter(lesson__slot__instructor=user).aggregate(avg=Avg('score'), n=Count('id'))
        return Response({
            'profile': InstructorProfileSerializer(profile).data,
            'today': SlotSerializer([s for s in upcoming if s.date == today], many=True).data,
            'upcoming': SlotSerializer([s for s in upcoming if s.date > today], many=True).data,
            'to_review': SlotSerializer(to_review, many=True).data,
            'students': StudentProfileSerializer(students, many=True).data,
            'month': {
                'hours': hours, 'lessons': month_lessons.count(),
                'amount': round(hours * float(profile.hourly_rate), 2), 'hourly_rate': float(profile.hourly_rate),
            },
            'rating': {'average': round(rating['avg'], 2) if rating['avg'] else None, 'count': rating['n']},
        })

    @action(detail=False, methods=['get'], permission_classes=[IsSupervisorOrAdmin])
    def performance(self, request):
        """Tableau de performance : avis, leçons, absences par moniteur."""
        rows = []
        for ins in User.instructors().select_related('instructor_profile').order_by('last_name'):
            lessons = Lesson.objects.filter(slot__instructor=ins)
            ratings = LessonRating.objects.filter(lesson__slot__instructor=ins).aggregate(avg=Avg('score'), n=Count('id'))
            rows.append({
                'id': ins.id, 'name': ins.get_full_name(),
                'is_bookable': getattr(ins, 'instructor_profile', None) and ins.instructor_profile.is_bookable,
                'lessons': lessons.count(),
                'hours': round(sum(l.slot.duration_hours for l in lessons.select_related('slot')), 1),
                'no_shows': Slot.objects.filter(instructor=ins, status='NO_SHOW').count(),
                'late_cancellations': Slot.objects.filter(instructor=ins, status='CANCELLED_LATE').count(),
                'students': StudentProfile.objects.filter(booked_slots__instructor=ins).distinct().count(),
                'rating_average': round(ratings['avg'], 2) if ratings['avg'] else None,
                'rating_count': ratings['n'],
                'recent_comments': list(
                    LessonRating.objects.filter(lesson__slot__instructor=ins).exclude(comment='')
                    .order_by('-created_at').values_list('comment', flat=True)[:3]
                ),
            })
        return Response(rows)


class _InstructorOwnedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsInstructor]
    pagination_class = None

    def get_queryset(self):
        return self.queryset.filter(instructor=self.request.user)

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)


class AvailabilityViewSet(_InstructorOwnedViewSet):
    queryset = Availability.objects.all()
    serializer_class = AvailabilitySerializer


class UnavailabilityViewSet(_InstructorOwnedViewSet):
    """Demandes d'absence du moniteur : créées « à valider », bloquent le planning immédiatement."""
    queryset = Unavailability.objects.all()
    serializer_class = UnavailabilitySerializer

    def perform_create(self, serializer):
        u = serializer.save(instructor=self.request.user, status='PENDING')
        log_activity('ABSENCE', f"{u.instructor.get_full_name()} demande une absence du {timezone.localtime(u.start):%d/%m %H:%M} au {timezone.localtime(u.end):%d/%m %H:%M}{' : ' + u.reason if u.reason else ''}",
                     actor=self.request.user, instructor=u.instructor)

    def perform_update(self, serializer):
        serializer.save(status='PENDING', reviewed_by=None, reviewed_at=None, review_note='')


class MeetingPointViewSet(viewsets.ModelViewSet):
    queryset = MeetingPoint.objects.all()
    serializer_class = MeetingPointSerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        return [IsStaff()]


# ---------- Créneaux ----------

class SlotViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Slot.objects.select_related('student__user', 'meeting_point', 'instructor', 'lesson')
        if user.role in User.BACKOFFICE_ROLES:
            return qs
        if user.teaches:
            return qs.filter(instructor=user)
        return qs.filter(student__user=user)

    @action(detail=False, methods=['get'])
    def free(self, request):
        """Créneaux proposables pour une date : ?date=YYYY-MM-DD[&instructor=ID][&duration=60]"""
        try:
            day = date_cls.fromisoformat(request.query_params.get('date', ''))
            duration = int(request.query_params.get('duration', 60))
        except ValueError:
            return Response({'detail': 'Paramètre date (YYYY-MM-DD) requis.'}, status=400)
        instructors = User.instructors().filter(instructor_profile__is_bookable=True)
        if request.query_params.get('instructor'):
            instructors = instructors.filter(pk=request.query_params['instructor'])
        windows = [
            {
                'instructor_id': w.instructor.id, 'instructor_name': w.instructor.get_full_name(), 'date': day,
                'start_time': timezone.localtime(w.start).time(), 'end_time': timezone.localtime(w.end).time(),
                'meeting_point': w.meeting_point.id if w.meeting_point else None,
                'meeting_point_name': w.meeting_point.name if w.meeting_point else None,
                'meeting_point_address': w.meeting_point.address if w.meeting_point else None,
            }
            for ins in instructors for w in free_windows(ins, day, duration_minutes=duration)
        ]
        windows.sort(key=lambda w: (w['start_time'], w['instructor_name']))
        return Response(FreeWindowSerializer(windows, many=True).data)

    @action(detail=False, methods=['post'], permission_classes=[IsStudent])
    def book(self, request):
        s = BookingSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        duration = (datetime.combine(d['date'], d['end_time']) - datetime.combine(d['date'], d['start_time'])).total_seconds() / 3600

        with transaction.atomic():
            profile = StudentProfile.objects.select_for_update().get(user=request.user)
            if profile.bookable_hours < duration:
                return Response(
                    {'detail': f"Crédit insuffisant : il vous reste {profile.bookable_hours:.1f} h réservables."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            InstructorProfile.objects.select_for_update().get_or_create(user=d['instructor'])
            if not is_window_free(d['instructor'], d['date'], d['start_time'], d['end_time']):
                return Response({'detail': "Ce créneau n'est plus disponible."}, status=status.HTTP_409_CONFLICT)
            # Lieu : celui choisi par l'élève, sinon le lieu de prise en charge de la disponibilité du moniteur
            place = d.get('meeting_point') or availability_meeting_point(d['instructor'], d['date'], d['start_time'], d['end_time'])
            slot = Slot.objects.create(
                instructor=d['instructor'], student=profile, meeting_point=place,
                date=d['date'], start_time=d['start_time'], end_time=d['end_time'], status='BOOKED',
            )
        send_booking_confirmation.delay(slot.id)
        log_activity('BOOKING', f"{profile.user.get_full_name()} a réservé le {slot.date:%d/%m} {slot.start_time:%H:%M} avec {slot.instructor.get_full_name()}",
                     actor=request.user, student=profile, instructor=slot.instructor, slot=slot)
        return Response(SlotSerializer(slot).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Élève : gratuit avant le délai, débité après. Staff : toujours gratuit."""
        slot = self.get_object()
        if slot.status != 'BOOKED':
            return Response({'detail': 'Ce créneau ne peut pas être annulé.'}, status=400)
        late = False
        if request.user.role == 'STUDENT':
            if slot.is_past:
                return Response({'detail': 'Ce créneau est déjà passé.'}, status=400)
            late = slot.starts_at - timezone.now() < timedelta(hours=settings.BOOKING_CANCEL_DEADLINE_HOURS)
        slot.status = 'CANCELLED_LATE' if late else 'CANCELLED'
        slot.cancelled_at = timezone.now()
        slot.save(update_fields=['status', 'cancelled_at', 'updated_at'])
        if late:
            slot.debit_hours()
        who = slot.student.user.get_full_name() if slot.student else 'Créneau'
        log_activity('LATE_CANCELLATION' if late else 'CANCELLATION',
                     f"{who} — leçon du {slot.date:%d/%m} {slot.start_time:%H:%M} annulée{' hors délai (heure débitée)' if late else ''} par {request.user.get_full_name()}",
                     actor=request.user, student=slot.student, instructor=slot.instructor, slot=slot)
        return Response(SlotSerializer(slot).data)

    @action(detail=True, methods=['post'], permission_classes=[IsStaff])
    def no_show(self, request, pk=None):
        slot = self.get_object()
        if slot.status != 'BOOKED':
            return Response({'detail': 'Ce créneau ne peut pas être marqué absent.'}, status=400)
        if not hasattr(slot, 'lesson'):
            Lesson.objects.create(slot=slot, student=slot.student, attended=False,
                                  instructor_notes=request.data.get('note', ''))
        slot.refresh_from_db()
        log_activity('NO_SHOW', f"{slot.student.user.get_full_name()} absent le {slot.date:%d/%m} {slot.start_time:%H:%M} (heure débitée)",
                     actor=request.user, student=slot.student, instructor=slot.instructor, slot=slot)
        return Response(SlotSerializer(slot).data)

    @action(detail=True, methods=['post'], permission_classes=[IsSupervisorOrAdmin])
    def refund(self, request, pk=None):
        """Dérogation : re-crédite une heure débitée (annulation tardive / absence justifiée)."""
        slot = self.get_object()
        note = (request.data.get('note') or '').strip()
        if not note:
            return Response({'detail': 'Un justificatif est requis.'}, status=400)
        if not slot.refund_hours(note):
            return Response({'detail': "Aucune heure débitée à re-créditer sur ce créneau."}, status=400)
        log_activity('REFUND', f"{slot.student.user.get_full_name()} — heure du {slot.date:%d/%m} re-créditée ({note})",
                     actor=request.user, student=slot.student, instructor=slot.instructor, slot=slot)
        return Response(SlotSerializer(slot).data)


# ---------- Pédagogie ----------

class CompetencyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Competency.objects.all()
    serializer_class = CompetencySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        qs = (Lesson.objects.select_related('slot__meeting_point', 'slot__instructor', 'student__user')
              .prefetch_related('assessments__competency'))
        if user.role in User.BACKOFFICE_ROLES:
            return qs
        if user.teaches:
            return qs.filter(slot__instructor=user)
        return qs.filter(student__user=user)

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update'):
            return [IsStaff()]
        return super().get_permissions()

    @action(detail=False, methods=['get'], permission_classes=[IsStudent])
    def to_rate(self, request):
        """Leçons effectuées pas encore notées (évaluation obligatoire post-séance)."""
        qs = self.get_queryset().filter(attended=True, rating__isnull=True).order_by('-slot__date')
        return Response(LessonSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    def rate(self, request, pk=None):
        lesson = self.get_object()
        if hasattr(lesson, 'rating'):
            return Response({'detail': 'Cette leçon a déjà été notée.'}, status=400)
        s = LessonRatingSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save(lesson=lesson)
        return Response(LessonSerializer(lesson).data, status=status.HTTP_201_CREATED)


# ---------- Catalogue ----------

def _recommendation_score(offer, code_status, level, gearbox):
    if offer.category == 'RECHARGE':
        return None
    score = 0.0
    if offer.for_code_status != 'ANY':
        score += 3 if offer.for_code_status == code_status else -5
    if offer.for_level != 'ANY':
        score += 2 if offer.for_level == level else -3
    if offer.gearbox != 'ANY':
        score += 1 if offer.gearbox == gearbox else -2
    if code_status == 'TO_PASS' and offer.includes_lms:
        score += 2
    if code_status == 'OBTAINED' and offer.category == 'CODE':
        score -= 6
    if level == 'REFRESH' and offer.category == 'PERFECTIONNEMENT':
        score += 2
    if level == 'BEGINNER' and offer.category == 'PERMIS_B':
        score += 1
    if offer.is_featured:
        score += 0.5
    return score


class OfferViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OfferSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = Offer.objects.filter(is_active=True)
        category = self.request.query_params.get('category')
        return qs.filter(category=category) if category else qs

    @action(detail=False, methods=['post'])
    def recommend(self, request):
        s = RecommendationInputSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        scored = []
        for offer in Offer.objects.filter(is_active=True):
            sc = _recommendation_score(offer, d['code_status'], d['level'], d['gearbox'])
            if sc is not None:
                scored.append((sc, offer))
        scored.sort(key=lambda x: (-x[0], x[1].display_order, x[1].price))
        return Response({
            'recommended': OfferSerializer(scored[0][1]).data if scored else None,
            'alternatives': OfferSerializer([o for _, o in scored[1:3]], many=True).data,
        })


class PackageViewSet(viewsets.ModelViewSet):
    serializer_class = PackageSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        if user.role in User.STAFF_ROLES:
            return Package.objects.select_related('student__user', 'offer')
        if self.action == 'list':
            return Package.objects.filter(student__user=user, parent__isnull=True).select_related('offer').prefetch_related('addons__offer')
        return Package.objects.filter(student__user=user).select_related('offer')

    def perform_create(self, serializer):
        serializer.save(student=StudentProfile.objects.get(user=self.request.user))

    @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    def checkout(self, request, pk=None):
        """Lien de paiement en ligne (Stripe) pour une demande en attente : formule + options, unique / abonnement / en plusieurs fois."""
        from .payments import StripeNotConfigured, create_checkout_link
        pkg = self.get_object()
        if pkg.status != 'PENDING':
            return Response({'detail': 'Cet achat est déjà réglé ou annulé.'}, status=400)
        try:
            url = create_checkout_link(pkg)
        except StripeNotConfigured:
            return Response({'detail': "Le paiement en ligne n'est pas encore activé : réglez auprès de votre école (virement, chèque, espèces, CPF)."}, status=400)
        except Exception as e:
            return Response({'detail': f"Paiement en ligne indisponible : {e}"}, status=502)
        return Response({'url': url})


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """Factures : l'élève voit les siennes, le staff toutes. /pdf/ renvoie le document."""
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Invoice.objects.select_related('student__user', 'package__offer')
        return qs if user.role in User.STAFF_ROLES else qs.filter(student__user=user)

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        from django.http import HttpResponse
        from .invoices import build_invoice_pdf
        invoice = self.get_object()
        resp = HttpResponse(build_invoice_pdf(invoice), content_type='application/pdf')
        resp['Content-Disposition'] = f'inline; filename="facture-{invoice.number}.pdf"'
        return resp


# ---------- Divers ----------

class DocumentViewSet(viewsets.ModelViewSet):
    """Dossier administratif de l'élève : dépôt (remplace la pièce existante), consultation, suppression si non validé."""
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        qs = Document.objects.select_related('student__user', 'verified_by')
        return qs if user.role in User.STAFF_ROLES else qs.filter(student__user=user)

    def create(self, request, *args, **kwargs):
        if request.user.role != 'STUDENT':
            return Response({'detail': 'Seul un élève dépose ses pièces.'}, status=403)
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        student = StudentProfile.objects.get(user=request.user)
        existing = Document.objects.filter(student=student, document_type=s.validated_data['document_type']).first()
        if existing:
            if existing.status == 'VERIFIED':
                return Response({'detail': 'Cette pièce est déjà validée. Contactez votre école pour la remplacer.'}, status=400)
            existing.file.delete(save=False)
            existing.file = s.validated_data['file']
            existing.status, existing.review_note, existing.reviewed_at, existing.verified_by = 'PENDING', '', None, None
            existing.save()
            doc = existing
        else:
            doc = s.save(student=student)
        log_activity('DOCUMENT', f"{student.user.get_full_name()} a déposé : {doc.get_document_type_display()}", actor=request.user, student=student)
        return Response(self.get_serializer(doc).data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        if self.request.user.role == 'STUDENT' and instance.status == 'VERIFIED':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Une pièce validée ne peut pas être supprimée.')
        instance.file.delete(save=False)
        instance.delete()

    @action(detail=False, methods=['get'], permission_classes=[IsStudent])
    def my_dossier(self, request):
        student = StudentProfile.objects.get(user=request.user)
        return Response({'dossier': Document.dossier(student), 'documents': DocumentSerializer(student.documents.all(), many=True, context={'request': request}).data})


class VehicleLogViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleLogSerializer
    permission_classes = [IsInstructor]

    def get_queryset(self):
        return VehicleLog.objects.filter(instructor=self.request.user)

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)
