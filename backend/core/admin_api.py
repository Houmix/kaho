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

from datetime import date as date_cls, datetime, time as time_cls

from .models import (
    ActivityLog, Availability, Document, InstructorApplication, InstructorProfile, Invoice, Lesson, LessonRating,
    MeetingPoint, Package, Slot, StudentProfile, Unavailability, User, log_activity,
)
from .scheduling import busy_periods
from .permissions import IsOwner, IsSupervisorOrAdmin
from .serializers import (
    DocumentSerializer, InstructorAdminSerializer, InstructorApplicationSerializer, InstructorCreateSerializer,
    InstructorProfileSerializer, InvoiceSerializer, LessonSerializer, PackageSerializer, RatingModerationSerializer,
    SlotSerializer, StudentProfileSerializer, AvailabilitySerializer, BookingSerializer, TeamInviteSerializer,
    TeamMemberSerializer, UnavailabilitySerializer, validate_upload,
)
from .scheduling import is_window_free
from .tasks import (
    send_absence_reviewed, send_application_received, send_application_rejected, send_booking_changed, send_booking_confirmation,
    send_bulk_message, send_instructor_invite, send_payment_link, send_team_invite,
)
import csv
from django.http import HttpResponse


from rest_framework import serializers as drf


class ActivitySerializer(drf.ModelSerializer):
    kind_display = drf.CharField(source='get_kind_display', read_only=True)
    actor_name = drf.CharField(source='actor.get_full_name', read_only=True, default=None)
    student_name = drf.CharField(source='student.user.get_full_name', read_only=True, default=None)
    instructor_name = drf.CharField(source='instructor.get_full_name', read_only=True, default=None)

    class Meta:
        model = ActivityLog
        fields = ('id', 'kind', 'kind_display', 'message', 'actor_name', 'student', 'student_name', 'instructor', 'instructor_name', 'slot', 'created_at')


class AdminPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 200


def _attribute_last_activity(student, actor):
    """Package.save() journalise sans connaître l'auteur ; on le renseigne après coup."""
    entry = ActivityLog.objects.filter(student=student, kind__in=('PAYMENT', 'HOURS_ADDED'), actor__isnull=True).order_by('-id').first()
    if entry:
        entry.actor = actor
        entry.save(update_fields=['actor'])


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
            'activity': ActivitySerializer(ActivityLog.objects.select_related('actor', 'student__user', 'instructor')[:8], many=True).data,
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
        absences = Unavailability.objects.filter(status='PENDING').count()
        if absences:
            alerts.append({'kind': 'absences', 'count': absences, 'text': f"{absences} demande{'s' if absences > 1 else ''} d'absence de moniteur à valider", 'href': '/admin/instructors?tab=absences'})
        docs = Document.objects.filter(status='PENDING').count()
        if docs:
            alerts.append({'kind': 'documents', 'count': docs, 'text': f"{docs} pièce{'s' if docs > 1 else ''} justificative{'s' if docs > 1 else ''} à vérifier", 'href': '/admin/students?filter=documents'})
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
        if p.get('status'):
            qs = qs.filter(status__in=p['status'].split(','))
        elif p.get('include_archived') != '1' and self.action in ('list', 'export'):
            qs = qs.exclude(status='ARCHIVED')
        if p.get('ids'):
            qs = qs.filter(id__in=[i for i in p['ids'].split(',') if i.isdigit()])
        f = p.get('filter')
        if f == 'unpaid':
            qs = qs.filter(packages__status='PENDING').distinct()
        elif f == 'low':
            qs = qs.filter(purchased_hours__gt=0).extra(where=['purchased_hours - used_hours <= 1'])
        elif f == 'ready':
            qs = qs.filter(ready_for_exam=True)
        elif f == 'lms':
            qs = qs.filter(lms_access=True)
        elif f == 'documents':
            qs = qs.filter(documents__status='PENDING').distinct()
        elif f == 'incomplete':
            verified = Document.objects.filter(status='VERIFIED').values('student').annotate(n=Count('id')).filter(n=len(Document.REQUIRED_TYPES)).values_list('student', flat=True)
            qs = qs.exclude(id__in=verified)
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
            'documents': DocumentSerializer(st.documents.all(), many=True, context={'request': request}).data,
            'dossier': Document.dossier(st),
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
        pkg = Package.objects.create(student=st, hours_purchased=hours, amount_paid=0, status='COMPLETED', payment_method='FREE', label='Ajout manuel d’heures',
                                     note=f"Ajout manuel par {request.user.get_full_name()} : {note}")
        _attribute_last_activity(st, request.user)
        return Response(PackageSerializer(pkg).data, status=201)

    @action(detail=True, methods=['post'])
    def debit_hours(self, request, pk=None):
        """Retrait manuel d'heures (erreur de saisie, régularisation) avec motif obligatoire."""
        st = self.get_object()
        try:
            hours = float(request.data.get('hours'))
        except (TypeError, ValueError):
            return Response({'detail': 'Nombre d’heures invalide.'}, status=400)
        note = (request.data.get('note') or '').strip()
        if hours <= 0 or not note:
            return Response({'detail': 'Indiquez un nombre d’heures positif et un motif.'}, status=400)
        if hours > st.remaining_hours:
            return Response({'detail': f"L'élève n'a que {st.remaining_hours:.1f} h restantes."}, status=400)
        st.purchased_hours = max(0.0, st.purchased_hours - hours)
        st.save(update_fields=['purchased_hours'])
        log_activity('HOURS_ADDED', f"{st.user.get_full_name()} — {hours:g} h retirée(s) : {note}", actor=request.user, student=st)
        return Response(StudentProfileSerializer(st).data)

    @action(detail=True, methods=['post'])
    def adjust_lms(self, request, pk=None):
        """Accès code en ligne : prolonger (months) ou fixer une date (until), ou couper (enabled=false). Motif requis."""
        st = self.get_object()
        note = (request.data.get('note') or '').strip()
        if not note:
            return Response({'detail': 'Indiquez un motif.'}, status=400)
        today = timezone.localdate()
        if str(request.data.get('enabled', 'true')).lower() in ('false', '0'):
            st.lms_access = False
            label = 'accès code en ligne retiré'
        else:
            from .models import add_months
            st.lms_access = True
            if request.data.get('until'):
                try:
                    st.lms_access_until = date_cls.fromisoformat(request.data['until'])
                except ValueError:
                    return Response({'detail': 'Date invalide.'}, status=400)
            elif request.data.get('months'):
                try:
                    months = int(request.data['months'])
                except ValueError:
                    return Response({'detail': 'Nombre de mois invalide.'}, status=400)
                base = st.lms_access_until if (st.lms_access_until and st.lms_access_until > today) else today
                st.lms_access_until = add_months(base, months)
            else:
                st.lms_access_until = None
            label = f"accès code en ligne jusqu'au {st.lms_access_until:%d/%m/%Y}" if st.lms_access_until else 'accès code en ligne illimité'
        st.save(update_fields=['lms_access', 'lms_access_until'])
        log_activity('LMS', f"{st.user.get_full_name()} — {label} : {note}", actor=request.user, student=st)
        return Response(StudentProfileSerializer(st).data)

    @action(detail=True, methods=['post'])
    def set_status(self, request, pk=None):
        """Changement de statut du parcours en 1 clic (tracé)."""
        st = self.get_object()
        new = request.data.get('status')
        if new not in dict(StudentProfile.STATUS_CHOICES):
            return Response({'detail': 'Statut inconnu.'}, status=400)
        if new == st.status:
            return Response(StudentProfileSerializer(st).data)
        old = st.get_status_display()
        st.status = new
        st.save(update_fields=['status', 'updated_at'])
        log_activity('STATUS', f"{st.user.get_full_name()} : {old} → {st.get_status_display()}", actor=request.user, student=st)
        return Response(StudentProfileSerializer(st).data)

    def _package_from_request(self, st, request):
        """Construit un achat à partir d'une offre (offer) ou d'un montant libre (amount, hours, label)."""
        from .models import Offer
        offer = None
        if request.data.get('offer'):
            offer = Offer.objects.filter(pk=request.data['offer']).first()
            if not offer:
                return None, Response({'detail': 'Offre introuvable.'}, status=400)
            hours, amount, label = offer.hours, offer.price, ''
        else:
            try:
                amount = float(request.data.get('amount') or 0)
                hours = float(request.data.get('hours') or 0)
            except (TypeError, ValueError):
                return None, Response({'detail': 'Montant ou heures invalides.'}, status=400)
            label = (request.data.get('label') or '').strip() or (f"Recharge {hours:g} h" if hours else 'Acompte')
            if amount <= 0:
                return None, Response({'detail': 'Indiquez un montant positif.'}, status=400)
        return Package(student=st, offer=offer, hours_purchased=hours, amount_paid=amount, label=label), None

    @action(detail=True, methods=['post'])
    def payment_link(self, request, pk=None):
        """Génère un lien Stripe Checkout (achat en attente) et l'envoie par email / SMS / les deux."""
        from .payments import StripeNotConfigured, create_checkout_link
        st = self.get_object()
        pkg, err = self._package_from_request(st, request)
        if err:
            return err
        pkg.status = 'PENDING'
        pkg.note = f"Lien de paiement généré par {request.user.get_full_name()} le {timezone.localdate():%d/%m/%Y}"
        error = None
        with transaction.atomic():
            pkg.save()  # émet la facture ; annulée (rollback) si Stripe échoue
            try:
                link = create_checkout_link(pkg)
            except StripeNotConfigured as e:
                error = Response({'detail': str(e)}, status=400)
            except Exception as e:
                error = Response({'detail': f"Stripe a refusé la création du lien : {e}"}, status=502)
            if error:
                transaction.set_rollback(True)
        if error:
            return error
        channel = request.data.get('channel', 'email')
        if channel in ('email', 'sms', 'both'):
            send_payment_link.delay(pkg.id, channel)
        log_activity('PAYMENT_LINK', f"{st.user.get_full_name()} — lien de paiement {pkg.amount_paid} € ({pkg.display_label}) envoyé par {channel}", actor=request.user, student=st)
        data = PackageSerializer(pkg).data
        data['link'] = link
        return Response(data, status=201)

    @action(detail=True, methods=['post'])
    def record_payment(self, request, pk=None):
        """Saisie d'un règlement reçu (espèces, chèque, virement, CPF) : achat validé + reçu (facture acquittée)."""
        st = self.get_object()
        method = request.data.get('method')
        if method not in ('CASH', 'CHECK', 'TRANSFER', 'CPF', 'STRIPE'):
            return Response({'detail': 'Mode de règlement invalide.'}, status=400)
        pkg, err = self._package_from_request(st, request)
        if err:
            return err
        pkg.status = 'COMPLETED'
        pkg.payment_method = method
        note = (request.data.get('note') or '').strip()
        pkg.note = f"Règlement {pkg.get_payment_method_display().lower()} saisi par {request.user.get_full_name()} le {timezone.localdate():%d/%m/%Y}" + (f" — {note}" if note else '')
        pkg.save()
        _attribute_last_activity(st, request.user)
        return Response(PackageSerializer(pkg).data, status=201)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_document(self, request, pk=None):
        """Dépôt d'une pièce par l'école pour le compte de l'élève (validée d'office)."""
        st = self.get_object()
        doc_type, f = request.data.get('document_type'), request.FILES.get('file')
        if doc_type not in dict(Document.TYPE_CHOICES) or not f:
            return Response({'detail': 'Type de pièce et fichier requis.'}, status=400)
        try:
            validate_upload(f)
        except Exception as e:
            return Response({'detail': str(getattr(e, 'detail', [e])[0])}, status=400)
        doc = Document.objects.filter(student=st, document_type=doc_type).first()
        if doc:
            doc.file.delete(save=False)
            doc.file = f
        else:
            doc = Document(student=st, document_type=doc_type, file=f)
        doc.status, doc.review_note, doc.reviewed_at, doc.verified_by = 'VERIFIED', '', timezone.now(), request.user
        doc.save()
        log_activity('DOCUMENT', f"{st.user.get_full_name()} — {doc.get_document_type_display()} déposé par l'école", actor=request.user, student=st)
        return Response(DocumentSerializer(doc, context={'request': request}).data, status=201)

    @action(detail=True, methods=['get'])
    def contract(self, request, pk=None):
        """Contrat de formation pré-rempli (PDF). ?package=ID pour une formule précise."""
        from .contracts import build_contract_pdf
        st = self.get_object()
        pkg = st.packages.filter(pk=request.query_params['package']).first() if request.query_params.get('package') else None
        pdf = build_contract_pdf(st, pkg)
        log_activity('CONTRACT', f"{st.user.get_full_name()} — contrat de formation généré", actor=request.user, student=st)
        resp = HttpResponse(pdf, content_type='application/pdf')
        resp['Content-Disposition'] = f'inline; filename="contrat-{st.user.last_name.lower()}-{st.id}.pdf"'
        return resp

    @action(detail=True, methods=['post'])
    def book(self, request, pk=None):
        """Réservation d'une leçon pour le compte de l'élève (même règles : crédit, fenêtre libre)."""
        st = self.get_object()
        s = BookingSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        duration = (datetime.combine(d['date'], d['end_time']) - datetime.combine(d['date'], d['start_time'])).total_seconds() / 3600
        force = str(request.data.get('force', 'false')).lower() in ('true', '1')
        with transaction.atomic():
            st = StudentProfile.objects.select_for_update().get(pk=st.pk)
            if st.bookable_hours < duration and not force:
                return Response({'detail': f"Crédit insuffisant : {st.bookable_hours:.1f} h réservables (cochez « forcer » pour réserver quand même)."}, status=400)
            if not is_window_free(d['instructor'], d['date'], d['start_time'], d['end_time']):
                return Response({'detail': "Le moniteur n'est pas disponible sur ce créneau (hors disponibilités, déjà pris ou préavis trop court)."}, status=409)
            slot = Slot.objects.create(instructor=d['instructor'], student=st, meeting_point=d['meeting_point'], date=d['date'], start_time=d['start_time'], end_time=d['end_time'], status='BOOKED')
        if str(request.data.get('notify', 'true')).lower() not in ('false', '0'):
            send_booking_confirmation.delay(slot.id)
        log_activity('BOOKING', f"{st.user.get_full_name()} — leçon du {slot.date:%d/%m} {slot.start_time:%H:%M} avec {slot.instructor.get_full_name()} réservée par {request.user.get_full_name()}",
                     actor=request.user, student=st, instructor=slot.instructor, slot=slot)
        return Response(SlotSerializer(slot).data, status=201)

    @action(detail=False, methods=['post'])
    def bulk(self, request):
        """Actions groupées sur une sélection : message (email/SMS), changement de statut, relance dossier / paiement."""
        ids = [int(i) for i in request.data.get('ids', []) if str(i).isdigit()]
        students = list(StudentProfile.objects.filter(id__in=ids).select_related('user'))
        if not students:
            return Response({'detail': 'Aucun élève sélectionné.'}, status=400)
        act = request.data.get('action')
        names = ', '.join(s.user.get_full_name() for s in students[:5]) + (f" et {len(students) - 5} autre(s)" if len(students) > 5 else '')
        if act == 'message':
            subject, body, channel = (request.data.get('subject') or '').strip(), (request.data.get('body') or '').strip(), request.data.get('channel', 'email')
            if not body or (channel != 'sms' and not subject):
                return Response({'detail': 'Objet et message requis.'}, status=400)
            send_bulk_message.delay([s.user_id for s in students], subject, body, channel)
            log_activity('MESSAGE', f"{'SMS' if channel == 'sms' else 'Email'} « {subject or body[:40]} » envoyé à {len(students)} élève(s) : {names}", actor=request.user)
        elif act == 'status':
            new = request.data.get('status')
            if new not in dict(StudentProfile.STATUS_CHOICES):
                return Response({'detail': 'Statut inconnu.'}, status=400)
            for st in students:
                if st.status != new:
                    log_activity('STATUS', f"{st.user.get_full_name()} : {st.get_status_display()} → {dict(StudentProfile.STATUS_CHOICES)[new]} (action groupée)", actor=request.user, student=st)
            StudentProfile.objects.filter(id__in=ids).update(status=new)
        elif act == 'remind_documents':
            targets = [s for s in students if not Document.dossier(s)['complete']]
            body = "Bonjour {prenom}, votre dossier administratif est incomplet. Connectez-vous à votre espace Kaho pour déposer les pièces manquantes. Merci !"
            send_bulk_message.delay([s.user_id for s in targets], 'Votre dossier Kaho est incomplet', body, request.data.get('channel', 'email'))
            log_activity('MESSAGE', f"Relance dossier envoyée à {len(targets)} élève(s)", actor=request.user)
            return Response({'detail': f"Relance envoyée à {len(targets)} élève(s) au dossier incomplet."})
        elif act == 'remind_payment':
            targets = [s for s in students if s.packages.filter(status='PENDING').exists()]
            body = "Bonjour {prenom}, un règlement est en attente sur votre espace Kaho. Vos heures seront créditées dès réception. Merci !"
            send_bulk_message.delay([s.user_id for s in targets], 'Règlement en attente — Kaho', body, request.data.get('channel', 'email'))
            log_activity('MESSAGE', f"Relance paiement envoyée à {len(targets)} élève(s)", actor=request.user)
            return Response({'detail': f"Relance envoyée à {len(targets)} élève(s) avec un paiement en attente."})
        else:
            return Response({'detail': 'Action inconnue.'}, status=400)
        return Response({'detail': f"Action appliquée à {len(students)} élève(s)."})

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export CSV complet de la liste filtrée (mêmes paramètres que la liste)."""
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = f'attachment; filename="eleves-{timezone.localdate()}.csv"'
        resp.write('\ufeff')
        w = csv.writer(resp, delimiter=';')
        w.writerow(['Nom', 'Prénom', 'Email', 'Mobile', 'Statut', 'NEPH', 'Boîte', 'Heures achetées', 'Heures faites', 'Restantes', 'Réservées', 'Compétences %', 'Code en ligne', 'Référent', 'Prêt examen', 'Dossier', 'Inscrit le'])
        for s in self.filter_queryset(self.get_queryset()):
            dossier = Document.dossier(s)
            w.writerow([s.user.last_name, s.user.first_name, s.user.email, s.phone, s.get_status_display(), s.neph_number or '', s.get_license_type_display(),
                        s.purchased_hours, s.used_hours, s.remaining_hours, s.reserved_hours, s.competency_progress()['percent'], 'oui' if s.has_lms_access else 'non',
                        s.referent_instructor.get_full_name() if s.referent_instructor else '', 'oui' if s.ready_for_exam else 'non',
                        'complet' if dossier['complete'] else f"{dossier['missing']} manquante(s)", s.created_at.date()])
        return resp


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
        if request.data.get('method') in dict(Package.METHOD_CHOICES):
            pkg.payment_method = request.data['method']
        pkg.note = ((pkg.note + '\n') if pkg.note else '') + f"Paiement validé par {request.user.get_full_name()} le {timezone.localdate():%d/%m/%Y}" + (f" — {request.data.get('note')}" if request.data.get('note') else '')
        pkg.save()
        _attribute_last_activity(pkg.student, request.user)
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
        log_activity('INSTRUCTOR', f"Moniteur créé et invité : {user.get_full_name()}", actor=request.user, instructor=user)
        return Response(InstructorAdminSerializer(user).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        for k in ('first_name', 'last_name', 'is_active'):
            if k in request.data:
                setattr(user, k, request.data[k])
        user.save()
        profile, _ = InstructorProfile.objects.get_or_create(user=user)
        ps = InstructorProfileSerializer(profile, data={k: v for k, v in request.data.items() if k in ('phone', 'gearbox', 'vehicle', 'zones', 'bio', 'is_bookable')}, partial=True)
        ps.is_valid(raise_exception=True)
        ps.save()
        if 'hourly_rate' in request.data:
            profile.hourly_rate = request.data['hourly_rate']
            profile.save(update_fields=['hourly_rate'])
        user.refresh_from_db()
        changed = ', '.join(k for k in request.data.keys() if k in ('first_name', 'last_name', 'is_active', 'phone', 'gearbox', 'vehicle', 'zones', 'bio', 'is_bookable', 'hourly_rate'))
        if changed:
            log_activity('INSTRUCTOR', f"Fiche de {user.get_full_name()} modifiée ({changed})", actor=request.user, instructor=user)
        return Response(InstructorAdminSerializer(user).data)

    @action(detail=True, methods=['get'])
    def absences(self, request, pk=None):
        user = self.get_object()
        qs = Unavailability.objects.filter(instructor=user, end__gte=timezone.now() - timedelta(days=90)).select_related('reviewed_by').order_by('-start')
        return Response(UnavailabilitySerializer(qs, many=True).data)

    @action(detail=True, methods=['post'])
    def add_absence(self, request, pk=None):
        """Absence saisie par l'école (validée d'office)."""
        user = self.get_object()
        s = UnavailabilitySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        u = s.save(instructor=user, status='APPROVED', reviewed_by=request.user, reviewed_at=timezone.now())
        affected = Slot.objects.filter(instructor=user, status='BOOKED', date__range=(timezone.localtime(u.start).date(), timezone.localtime(u.end).date())).count()
        log_activity('ABSENCE', f"Absence de {user.get_full_name()} saisie du {timezone.localtime(u.start):%d/%m %H:%M} au {timezone.localtime(u.end):%d/%m %H:%M}{' : ' + u.reason if u.reason else ''}", actor=request.user, instructor=user)
        data = UnavailabilitySerializer(u).data
        data['affected_slots'] = affected
        return Response(data, status=201)

    @action(detail=True, methods=['get'])
    def hours(self, request, pk=None):
        """Heures réellement effectuées vs annulées / hors délai / absences, par mois (?month=YYYY-MM, défaut : mois courant)."""
        user = self.get_object()
        try:
            y, m = map(int, (request.query_params.get('month') or timezone.localdate().strftime('%Y-%m')).split('-'))
            start = date_cls(y, m, 1)
        except ValueError:
            return Response({'detail': 'Paramètre month invalide.'}, status=400)
        end = date_cls(y + (m // 12), m % 12 + 1, 1)
        slots = Slot.objects.filter(instructor=user, date__gte=start, date__lt=end).select_related('student__user', 'meeting_point', 'lesson').order_by('date', 'start_time')
        today = timezone.localdate()
        buckets = {'done': [], 'no_show': [], 'cancelled_late': [], 'cancelled': [], 'upcoming': [], 'to_review': []}
        for sl in slots:
            if sl.status == 'NO_SHOW':
                key = 'no_show'
            elif sl.status == 'CANCELLED_LATE':
                key = 'cancelled_late'
            elif sl.status == 'CANCELLED':
                key = 'cancelled'
            elif sl.status == 'BOOKED' and hasattr(sl, 'lesson'):
                key = 'done' if sl.lesson.attended else 'no_show'
            elif sl.status == 'BOOKED' and sl.date < today:
                key = 'to_review'
            else:
                key = 'upcoming'
            buckets[key].append(sl)
        rate = float(user.instructor_profile.hourly_rate) if hasattr(user, 'instructor_profile') else 0.0
        summary = {k: {'count': len(v), 'hours': round(sum(x.duration_hours for x in v), 2)} for k, v in buckets.items()}
        paid_hours = summary['done']['hours']
        return Response({
            'month': f"{y:04d}-{m:02d}", 'hourly_rate': rate, 'summary': summary,
            'paid_hours': paid_hours, 'amount': round(paid_hours * rate, 2),
            'details': SlotSerializer(slots, many=True).data,
        })

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def reassign(self, request, pk=None):
        """Réattribution en masse des leçons réservées (start..end) vers un autre moniteur ; refus individuel si conflit."""
        source = self.get_object()
        try:
            start, end = date_cls.fromisoformat(request.data.get('start', '')), date_cls.fromisoformat(request.data.get('end', ''))
            target = User.objects.get(pk=request.data.get('target'), role='INSTRUCTOR', is_active=True)
        except (ValueError, User.DoesNotExist):
            return Response({'detail': 'Dates (YYYY-MM-DD) et moniteur cible requis.'}, status=400)
        if target.id == source.id:
            return Response({'detail': 'Choisissez un autre moniteur.'}, status=400)
        notify = str(request.data.get('notify', 'true')).lower() not in ('false', '0')
        moved, failed = [], []
        for slot in Slot.objects.select_for_update().filter(instructor=source, status='BOOKED', date__range=(start, end)).select_related('student__user', 'meeting_point').order_by('date', 'start_time'):
            w_start, w_end = timezone.make_aware(datetime.combine(slot.date, slot.start_time)), timezone.make_aware(datetime.combine(slot.date, slot.end_time))
            if w_start < timezone.now():
                failed.append({'id': slot.id, 'label': f"{slot.date:%d/%m} {slot.start_time:%H:%M}", 'reason': 'déjà passé'})
                continue
            if any(w_start < b1 and b0 < w_end for b0, b1 in busy_periods(target, slot.date)):
                failed.append({'id': slot.id, 'label': f"{slot.date:%d/%m} {slot.start_time:%H:%M} · {slot.student.user.get_full_name() if slot.student else ''}", 'reason': f"{target.get_full_name()} n'est pas libre"})
                continue
            old_label = f"le {slot.date:%d/%m/%Y} à {slot.start_time:%H:%M} avec {source.get_full_name()}"
            slot.instructor = target
            slot.save(update_fields=['instructor', 'updated_at'])
            moved.append({'id': slot.id, 'label': f"{slot.date:%d/%m} {slot.start_time:%H:%M} · {slot.student.user.get_full_name() if slot.student else ''}"})
            if notify and slot.student:
                send_booking_changed.delay(slot.id, old_label)
        log_activity('PLANNING', f"Réattribution {source.get_full_name()} → {target.get_full_name()} du {start:%d/%m} au {end:%d/%m} : {len(moved)} leçon(s) déplacée(s), {len(failed)} conflit(s)",
                     actor=request.user, instructor=target)
        return Response({'moved': moved, 'failed': failed})

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
        log_activity('APPLICATION', f"Candidature acceptée : {user.get_full_name()}", actor=request.user, instructor=user)
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
        log_activity('APPLICATION', f"Candidature refusée : {app.first_name} {app.last_name}", actor=request.user)
        return Response(InstructorApplicationSerializer(app).data)


# ---------- Planning global ----------

class AdminCalendarView(APIView):
    """Créneaux + absences entre deux dates, pour la vue calendrier. ?start=&end=[&instructor=&meeting_point=&status=]"""
    permission_classes = [IsSupervisorOrAdmin]

    def get(self, request):
        p = request.query_params
        try:
            start, end = date_cls.fromisoformat(p.get('start', '')), date_cls.fromisoformat(p.get('end', ''))
        except ValueError:
            return Response({'detail': 'Paramètres start et end (YYYY-MM-DD) requis.'}, status=400)
        if (end - start).days > 62:
            return Response({'detail': 'Plage maximale : 62 jours.'}, status=400)
        slots = Slot.objects.filter(date__range=(start, end)).select_related('student__user', 'instructor', 'meeting_point', 'lesson')
        unavail = Unavailability.objects.filter(start__date__lte=end, end__date__gte=start).select_related('instructor')
        if p.get('instructor'):
            slots, unavail = slots.filter(instructor_id=p['instructor']), unavail.filter(instructor_id=p['instructor'])
        if p.get('meeting_point'):
            slots = slots.filter(meeting_point_id=p['meeting_point'])
        if p.get('status'):
            slots = slots.filter(status__in=p['status'].split(','))
        instructors = User.objects.filter(role='INSTRUCTOR', is_active=True).select_related('instructor_profile').order_by('last_name')
        return Response({
            'slots': SlotSerializer(slots, many=True).data,
            'unavailabilities': [{'id': u.id, 'instructor': u.instructor_id, 'instructor_name': u.instructor.get_full_name(), 'start': u.start, 'end': u.end, 'reason': u.reason} for u in unavail],
            'availabilities': [{'instructor': a.instructor_id, 'weekday': a.weekday, 'start_time': a.start_time, 'end_time': a.end_time} for a in Availability.objects.filter(instructor__in=instructors)],
            'instructors': [{'id': i.id, 'name': i.get_full_name(), 'is_bookable': i.instructor_profile.is_bookable} for i in instructors],
            'meeting_points': [{'id': m.id, 'name': m.name} for m in MeetingPoint.objects.all()],
        })


class AdminSlotViewSet(viewsets.GenericViewSet):
    queryset = Slot.objects.select_related('student__user', 'instructor', 'meeting_point')
    serializer_class = SlotSerializer
    permission_classes = [IsSupervisorOrAdmin]

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def move(self, request, pk=None):
        """Déplacer / réattribuer un créneau réservé (glisser-déposer). Refus si chevauchement ou absence du moniteur cible."""
        slot = Slot.objects.select_for_update().get(pk=pk)
        if slot.status != 'BOOKED':
            return Response({'detail': 'Seul un créneau réservé peut être déplacé.'}, status=400)
        d = request.data
        try:
            new_date = date_cls.fromisoformat(d.get('date', slot.date.isoformat()))
            new_start = time_cls.fromisoformat(d.get('start_time', slot.start_time.strftime('%H:%M')))
            instructor = User.objects.get(pk=d.get('instructor', slot.instructor_id), role='INSTRUCTOR', is_active=True)
        except (ValueError, User.DoesNotExist):
            return Response({'detail': 'Date, heure ou moniteur invalide.'}, status=400)
        duration = datetime.combine(slot.date, slot.end_time) - datetime.combine(slot.date, slot.start_time)
        new_end = (datetime.combine(new_date, new_start) + duration).time()
        if timezone.make_aware(datetime.combine(new_date, new_start)) < timezone.now():
            return Response({'detail': 'Impossible de déplacer dans le passé.'}, status=400)
        w_start, w_end = timezone.make_aware(datetime.combine(new_date, new_start)), timezone.make_aware(datetime.combine(new_date, new_end))
        for b0, b1 in busy_periods(instructor, new_date):
            if w_start < b1 and b0 < w_end:
                # ignorer le créneau lui-même s'il reste chez le même moniteur
                own = slot.instructor_id == instructor.id and b0 == timezone.make_aware(datetime.combine(slot.date, slot.start_time))
                if not own:
                    return Response({'detail': f"{instructor.get_full_name()} n'est pas libre à ce moment (créneau ou absence)."}, status=409)
        if slot.student:
            clash = Slot.objects.filter(student=slot.student, date=new_date, status='BOOKED').exclude(pk=slot.pk)
            if any(w_start < timezone.make_aware(datetime.combine(c.date, c.end_time)) and timezone.make_aware(datetime.combine(c.date, c.start_time)) < w_end for c in clash):
                return Response({'detail': "L'élève a déjà une leçon à ce moment."}, status=409)
        in_availability = Availability.objects.filter(instructor=instructor, weekday=new_date.weekday(), start_time__lte=new_start, end_time__gte=new_end).exists()

        old_label = f"le {slot.date:%d/%m/%Y} à {slot.start_time:%H:%M} avec {slot.instructor.get_full_name()}"
        changed = (slot.date, slot.start_time, slot.instructor_id) != (new_date, new_start, instructor.id)
        slot.date, slot.start_time, slot.end_time, slot.instructor = new_date, new_start, new_end, instructor
        slot.save(update_fields=['date', 'start_time', 'end_time', 'instructor', 'updated_at'])
        if changed:
            log_activity('SLOT_MOVED', f"{slot.student.user.get_full_name() if slot.student else 'Créneau'} : {old_label} → {new_date:%d/%m} {new_start:%H:%M} avec {instructor.get_full_name()}",
                         actor=request.user, student=slot.student, instructor=instructor, slot=slot)
            if slot.student and str(d.get('notify', 'true')).lower() not in ('false', '0'):
                send_booking_changed.delay(slot.id, old_label)
        data = SlotSerializer(slot).data
        data['warning'] = None if in_availability else f"Hors des disponibilités habituelles de {instructor.get_full_name()}."
        return Response(data)


class AdminActivityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = None
    permission_classes = [IsSupervisorOrAdmin]
    pagination_class = AdminPagination

    def get_queryset(self):
        qs = ActivityLog.objects.select_related('actor', 'student__user', 'instructor')
        p = self.request.query_params
        if p.get('kind'):
            qs = qs.filter(kind__in=p['kind'].split(','))
        if p.get('student'):
            qs = qs.filter(student_id=p['student'])
        if p.get('instructor'):
            qs = qs.filter(instructor_id=p['instructor'])
        if p.get('actor'):
            qs = qs.filter(actor_id=p['actor'])
        if p.get('admin_only') == '1':
            qs = qs.filter(actor__role__in=User.TEAM_ROLES)
        if p.get('q'):
            qs = qs.filter(message__icontains=p['q'])
        if p.get('since'):
            try:
                qs = qs.filter(created_at__date__gte=date_cls.fromisoformat(p['since']))
            except ValueError:
                pass
        return qs

    def get_serializer_class(self):
        return ActivitySerializer

    @action(detail=False, methods=['get'])
    def actors(self, request):
        """Auteurs possibles pour filtrer le journal d'audit (équipe back-office + moniteurs ayant agi)."""
        ids = ActivityLog.objects.exclude(actor__isnull=True).values_list('actor_id', flat=True).distinct()
        users = User.objects.filter(Q(id__in=ids) | Q(role__in=User.TEAM_ROLES)).order_by('role', 'last_name')
        return Response([{'id': u.id, 'name': u.get_full_name(), 'role': u.get_role_display()} for u in users])

    @action(detail=False, methods=['get'])
    def export(self, request):
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = f'attachment; filename="journal-{timezone.localdate()}.csv"'
        resp.write('\ufeff')
        w = csv.writer(resp, delimiter=';')
        w.writerow(['Date', 'Type', 'Message', 'Auteur', 'Élève', 'Moniteur'])
        for e in self.filter_queryset(self.get_queryset())[:5000]:
            w.writerow([timezone.localtime(e.created_at).strftime('%d/%m/%Y %H:%M'), e.get_kind_display(), e.message, e.actor.get_full_name() if e.actor else '',
                        e.student.user.get_full_name() if e.student else '', e.instructor.get_full_name() if e.instructor else ''])
        return resp


# ---------- Ventes, factures, paie ----------

class AdminSalesView(APIView):
    """Chiffre d'affaires mensuel (12 derniers mois), impayés, synthèse. Réservé au gérant."""
    permission_classes = [IsOwner]

    def get(self, request):
        today = timezone.localdate()
        months = []
        y, m = today.year, today.month
        for _ in range(12):
            start = date_cls(y, m, 1)
            end = date_cls(y + (m // 12), m % 12 + 1, 1)
            paid = Package.objects.filter(status='COMPLETED', paid_at__date__gte=start, paid_at__date__lt=end)
            months.append({'month': start.strftime('%Y-%m'), 'label': start.strftime('%b %Y'),
                           'revenue': float(paid.aggregate(s=Sum('amount_paid'))['s'] or 0), 'sales': paid.count()})
            m -= 1
            if m == 0:
                y, m = y - 1, 12
        months.reverse()
        unpaid = Invoice.objects.filter(status='ISSUED').select_related('student__user', 'package__offer').order_by('due_at')
        return Response({
            'months': months,
            'year_revenue': float(Package.objects.filter(status='COMPLETED', paid_at__year=today.year).aggregate(s=Sum('amount_paid'))['s'] or 0),
            'unpaid': {'count': unpaid.count(), 'amount': float(unpaid.aggregate(s=Sum('amount_ttc'))['s'] or 0),
                       'overdue': sum(1 for i in unpaid if i.is_overdue), 'items': InvoiceSerializer(unpaid, many=True).data},
            'invoices_count': Invoice.objects.count(),
        })


class AdminInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsOwner]
    pagination_class = AdminPagination

    def get_queryset(self):
        qs = Invoice.objects.select_related('student__user', 'package__offer')
        p = self.request.query_params
        if p.get('status'):
            qs = qs.filter(status=p['status'])
        if p.get('month'):
            try:
                y, m = map(int, p['month'].split('-'))
                qs = qs.filter(issued_at__year=y, issued_at__month=m)
            except ValueError:
                pass
        if p.get('q'):
            q = p['q']
            qs = qs.filter(Q(number__icontains=q) | Q(student__user__first_name__icontains=q) | Q(student__user__last_name__icontains=q) | Q(student__user__email__icontains=q))
        return qs


class AdminPayrollView(APIView):
    """Heures réellement effectuées par moniteur sur un mois (bilans saisis, élève présent) × taux horaire. Réservé au gérant."""
    permission_classes = [IsOwner]

    def get(self, request):
        try:
            y, m = map(int, (request.query_params.get('month') or timezone.localdate().strftime('%Y-%m')).split('-'))
            start = date_cls(y, m, 1)
        except ValueError:
            return Response({'detail': 'Paramètre month (YYYY-MM) invalide.'}, status=400)
        end = date_cls(y + (m // 12), m % 12 + 1, 1)
        rows, total = [], 0.0
        for ins in User.objects.filter(role='INSTRUCTOR').select_related('instructor_profile').order_by('last_name'):
            lessons = Lesson.objects.filter(slot__instructor=ins, attended=True, slot__date__gte=start, slot__date__lt=end).select_related('slot__student__user', 'slot__meeting_point').order_by('slot__date', 'slot__start_time')
            hours = round(sum(l.slot.duration_hours for l in lessons), 2)
            rate = float(ins.instructor_profile.hourly_rate) if hasattr(ins, 'instructor_profile') else 0.0
            amount = round(hours * rate, 2)
            no_shows = Slot.objects.filter(instructor=ins, status='NO_SHOW', date__gte=start, date__lt=end).count()
            if not hours and not no_shows and not ins.is_active:
                continue
            total += amount
            rows.append({
                'id': ins.id, 'name': ins.get_full_name(), 'email': ins.email, 'hourly_rate': rate, 'hours': hours,
                'lessons': lessons.count(), 'no_shows': no_shows, 'amount': amount,
                'details': [{'date': l.slot.date, 'start_time': l.slot.start_time, 'hours': l.slot.duration_hours,
                             'student': l.slot.student.user.get_full_name() if l.slot.student else '', 'place': l.slot.meeting_point.name} for l in lessons],
            })
        return Response({'month': f"{y:04d}-{m:02d}", 'rows': rows, 'total': round(total, 2), 'total_hours': round(sum(r['hours'] for r in rows), 2)})


# ---------- Documents ----------

class AdminDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsSupervisorOrAdmin]
    pagination_class = AdminPagination

    def get_queryset(self):
        qs = Document.objects.select_related('student__user', 'verified_by').order_by('status', '-uploaded_at')
        st = self.request.query_params.get('status')
        return qs.filter(status=st) if st else qs

    def _review(self, request, pk, status_value):
        from .tasks import send_document_reviewed
        doc = self.get_object()
        note = (request.data.get('note') or '').strip()
        if status_value == 'REJECTED' and not note:
            return Response({'detail': 'Indiquez le motif du refus (il est envoyé à l’élève).'}, status=400)
        doc.status, doc.review_note, doc.reviewed_at, doc.verified_by = status_value, note, timezone.now(), request.user
        doc.save(update_fields=['status', 'review_note', 'reviewed_at', 'verified_by'])
        send_document_reviewed.delay(doc.id)
        log_activity('DOCUMENT', f"{doc.student.user.get_full_name()} — {doc.get_document_type_display()} {'validé' if status_value == 'VERIFIED' else 'refusé : ' + note}",
                     actor=request.user, student=doc.student)
        return Response(DocumentSerializer(doc, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        return self._review(request, pk, 'VERIFIED')

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        return self._review(request, pk, 'REJECTED')


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


# ---------- Absences des moniteurs ----------

class AdminAbsenceViewSet(viewsets.ReadOnlyModelViewSet):
    """Demandes de congés / arrêts / indisponibilités à valider."""
    serializer_class = UnavailabilitySerializer
    permission_classes = [IsSupervisorOrAdmin]
    pagination_class = AdminPagination

    def get_queryset(self):
        qs = Unavailability.objects.select_related('instructor', 'reviewed_by').order_by('status', '-start')
        p = self.request.query_params
        if p.get('status'):
            qs = qs.filter(status=p['status'])
        if p.get('instructor'):
            qs = qs.filter(instructor_id=p['instructor'])
        return qs

    def _review(self, request, new_status):
        u = self.get_object()
        note = (request.data.get('note') or '').strip()
        u.status, u.reviewed_by, u.reviewed_at, u.review_note = new_status, request.user, timezone.now(), note
        u.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_note'])
        send_absence_reviewed.delay(u.id)
        log_activity('ABSENCE', f"Absence de {u.instructor.get_full_name()} ({timezone.localtime(u.start):%d/%m %H:%M} → {timezone.localtime(u.end):%d/%m %H:%M}) {'validée' if new_status == 'APPROVED' else 'refusée'}{' : ' + note if note else ''}",
                     actor=request.user, instructor=u.instructor)
        data = UnavailabilitySerializer(u).data
        data['affected_slots'] = Slot.objects.filter(instructor=u.instructor, status='BOOKED', date__range=(timezone.localtime(u.start).date(), timezone.localtime(u.end).date())).count() if new_status == 'APPROVED' else 0
        return Response(data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        return self._review(request, 'APPROVED')

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        return self._review(request, 'REJECTED')


# ---------- Équipe back-office (gérant uniquement) ----------

class AdminTeamViewSet(viewsets.ModelViewSet):
    """Comptes administrateurs : invitation par email, rôle (gérant / gestionnaire / superviseur), activation."""
    serializer_class = TeamMemberSerializer
    permission_classes = [IsOwner]
    pagination_class = None
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        return User.objects.filter(role__in=User.TEAM_ROLES).order_by('-role', 'last_name')

    def create(self, request, *args, **kwargs):
        s = TeamInviteSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        send_team_invite.delay(user.email, user.first_name, invite_link(user), user.get_role_display())
        log_activity('TEAM', f"Compte {user.get_role_display()} créé et invité : {user.get_full_name()}", actor=request.user)
        return Response(TeamMemberSerializer(user).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        is_self = user.id == request.user.id
        owners = User.objects.filter(role='OWNER', is_active=True).exclude(pk=user.pk).count()
        new_role = request.data.get('role', user.role)
        new_active = user.is_active if 'is_active' not in request.data else str(request.data['is_active']).lower() not in ('false', '0', '')
        if new_role not in User.TEAM_ROLES:
            return Response({'detail': 'Rôle invalide.'}, status=400)
        if user.role == 'OWNER' and (new_role != 'OWNER' or not new_active) and owners == 0:
            return Response({'detail': 'Impossible : il doit rester au moins un gérant actif.'}, status=400)
        if is_self and (new_role != 'OWNER' or not new_active):
            return Response({'detail': 'Vous ne pouvez pas retirer vos propres droits de gérant.'}, status=400)
        changes = []
        for k in ('first_name', 'last_name'):
            if k in request.data and request.data[k] != getattr(user, k):
                setattr(user, k, request.data[k]); changes.append(k)
        if new_role != user.role:
            changes.append(f"rôle {user.get_role_display()} → {dict(User.ROLE_CHOICES)[new_role]}")
            user.role = new_role
            user.is_staff = user.is_superuser = new_role == 'OWNER'
        if bool(new_active) != user.is_active:
            user.is_active = bool(new_active)
            changes.append('activé' if user.is_active else 'désactivé')
        user.save()
        if changes:
            log_activity('TEAM', f"Compte {user.get_full_name()} : {', '.join(changes)}", actor=request.user)
        return Response(TeamMemberSerializer(user).data)

    @action(detail=True, methods=['post'])
    def resend_invite(self, request, pk=None):
        user = self.get_object()
        send_team_invite.delay(user.email, user.first_name, invite_link(user), user.get_role_display())
        return Response({'detail': f"Invitation renvoyée à {user.email}."})
