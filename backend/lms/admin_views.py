"""Éditeur de contenu LMS 100 % intégré au back-office (cours, sections, leçons, quiz, questions, examens, banque)."""
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import parsers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import log_activity
from core.permissions import IsSupervisorOrAdmin
from core.serializers import validate_upload
from .models import Course, Exam, Lesson, LessonAsset, Question, Quiz, Section, THEMES, theme_label
from .serializers import (
    CourseAdminSerializer, ExamAdminSerializer, LessonAdminSerializer, QuestionAdminSerializer, QuizAdminSerializer, SectionAdminSerializer,
)


class _Logged:
    """Journalise créations / modifications / suppressions dans l'historique d'activité."""
    label = 'Contenu'

    def perform_create(self, serializer):
        obj = serializer.save()
        log_activity('LMS', f"{self.label} créé : {obj}", actor=self.request.user)

    def perform_update(self, serializer):
        obj = serializer.save()
        log_activity('LMS', f"{self.label} modifié : {obj}", actor=self.request.user)

    def perform_destroy(self, instance):
        log_activity('LMS', f"{self.label} supprimé : {instance}", actor=self.request.user)
        instance.delete()


class AdminCourseViewSet(_Logged, viewsets.ModelViewSet):
    queryset = Course.objects.prefetch_related('sections__lessons', 'sections__quiz')
    serializer_class = CourseAdminSerializer
    permission_classes = [IsSupervisorOrAdmin]
    pagination_class = None
    label = 'Cours'

    @action(detail=True, methods=['post'])
    def seed_themes(self, request, pk=None):
        """Crée les 10 thèmes officiels (sections manquantes) avec leur quiz vide."""
        course = self.get_object()
        existing = set(course.sections.exclude(code='').values_list('code', flat=True))
        created = 0
        for i, (code, title, desc, _) in enumerate(THEMES, start=1):
            if code in existing:
                continue
            s = Section.objects.create(course=course, code=code, title=f"{code} — {title}", order=i, unlock_threshold=0)
            Quiz.objects.create(section=s, title=f"Quiz — {title}", pass_score=80)
            Lesson.objects.create(section=s, title=title, order=1, estimated_minutes=10, content_md=f"## {title}\n\n{desc}.\n\n*Contenu à rédiger.*", is_published=False)
            created += 1
        log_activity('LMS', f"Thèmes officiels ajoutés au cours « {course.title} » : {created}", actor=request.user)
        return Response(CourseAdminSerializer(Course.objects.prefetch_related('sections__lessons', 'sections__quiz').get(pk=course.pk)).data)


class AdminSectionViewSet(_Logged, viewsets.ModelViewSet):
    queryset = Section.objects.select_related('course').prefetch_related('lessons', 'quiz')
    serializer_class = SectionAdminSerializer
    permission_classes = [IsSupervisorOrAdmin]
    pagination_class = None
    label = 'Section'

    @action(detail=True, methods=['post'])
    def add_quiz(self, request, pk=None):
        s = self.get_object()
        if hasattr(s, 'quiz'):
            return Response({'detail': 'Cette section a déjà un quiz.'}, status=400)
        q = Quiz.objects.create(section=s, title=request.data.get('title') or f"Quiz — {s.title}", pass_score=int(request.data.get('pass_score') or 80))
        log_activity('LMS', f"Quiz créé : {q}", actor=request.user)
        return Response(QuizAdminSerializer(q).data, status=201)

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """{ids: [..]} dans le nouvel ordre."""
        for i, sid in enumerate(request.data.get('ids', []), start=1):
            Section.objects.filter(pk=sid).update(order=i)
        return Response({'ok': True})


class AdminLessonViewSet(_Logged, viewsets.ModelViewSet):
    queryset = Lesson.objects.select_related('section__course').prefetch_related('quiz', 'progress')
    serializer_class = LessonAdminSerializer
    permission_classes = [IsSupervisorOrAdmin]
    pagination_class = None
    label = 'Leçon'

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        for i, lid in enumerate(request.data.get('ids', []), start=1):
            Lesson.objects.filter(pk=lid).update(order=i)
        return Response({'ok': True})

    @action(detail=True, methods=['post'])
    def add_quiz(self, request, pk=None):
        l = self.get_object()
        if hasattr(l, 'quiz'):
            return Response({'detail': 'Cette leçon a déjà un quiz.'}, status=400)
        q = Quiz.objects.create(lesson=l, title=request.data.get('title') or f"Quiz — {l.title}", pass_score=int(request.data.get('pass_score') or 80))
        return Response(QuizAdminSerializer(q).data, status=201)

    @action(detail=True, methods=['post'], parser_classes=[parsers.MultiPartParser, parsers.FormParser])
    def upload_asset(self, request, pk=None):
        """Image / schéma à insérer dans le Markdown : renvoie l'URL à coller."""
        l = self.get_object()
        f = request.FILES.get('file')
        if not f:
            return Response({'detail': 'Fichier requis.'}, status=400)
        try:
            validate_upload(f)
        except Exception as e:
            return Response({'detail': str(getattr(e, 'detail', [e])[0])}, status=400)
        a = LessonAsset.objects.create(lesson=l, title=request.data.get('title', ''), file=f)
        url = request.build_absolute_uri(a.file.url)
        return Response({'id': a.id, 'url': url, 'markdown': f"![{a.title or 'schéma'}]({url})"}, status=201)


class AdminQuizViewSet(_Logged, viewsets.ModelViewSet):
    queryset = Quiz.objects.select_related('section', 'lesson').prefetch_related('questions__choices')
    serializer_class = QuizAdminSerializer
    permission_classes = [IsSupervisorOrAdmin]
    pagination_class = None
    label = 'Quiz'

    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        return Response(QuestionAdminSerializer(self.get_object().questions.all(), many=True).data)


def question_success_stats(questions):
    """{question_id: (réponses, bonnes réponses)} d'après les tentatives de quiz et d'examens blancs terminées."""
    from .models import ExamAttempt, QuizAttempt
    by_id = {q.id: q for q in questions}
    stats = {qid: [0, 0] for qid in by_id}

    def record(qid, answer):
        q = by_id.get(qid)
        if q is None:
            return
        ok, _ = q.grade_answer(answer)
        stats[qid][0] += 1
        stats[qid][1] += 1 if ok else 0

    for a in QuizAttempt.objects.only('answers').iterator():
        for k, v in (a.answers or {}).items():
            if str(k).isdigit():
                record(int(k), v)
    for a in ExamAttempt.objects.exclude(status='IN_PROGRESS').only('question_ids', 'answers').iterator():
        for qid in a.question_ids or []:
            record(int(qid), (a.answers or {}).get(str(qid)))
    return {qid: tuple(v) for qid, v in stats.items()}


class AdminQuestionViewSet(_Logged, viewsets.ModelViewSet):
    """Questions de quiz et banque d'examen.
    Filtres : ?quiz= ?topic= ?bank=1 ?q= ?unassigned=1 ?max_success=50 (taux de réussite ≤ x %) ?min_success= ?unanswered=1"""
    serializer_class = QuestionAdminSerializer
    permission_classes = [IsSupervisorOrAdmin]
    pagination_class = None
    label = 'Question'

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.action == 'list':
            ctx['stats'] = getattr(self, '_stats', None)
        return ctx

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        p = request.query_params
        wants_stats = any(p.get(k) for k in ('max_success', 'min_success', 'unanswered', 'with_stats'))
        items = list(qs)
        if wants_stats:
            self._stats = question_success_stats(items)

            def rate(q):
                n, ok = self._stats.get(q.id, (0, 0))
                return None if n == 0 else 100 * ok / n
            if p.get('unanswered') == '1':
                items = [q for q in items if rate(q) is None]
            if p.get('max_success'):
                items = [q for q in items if rate(q) is not None and rate(q) <= float(p['max_success'])]
            if p.get('min_success'):
                items = [q for q in items if rate(q) is not None and rate(q) >= float(p['min_success'])]
            if p.get('sort') == 'success':
                items.sort(key=lambda q: (rate(q) is None, rate(q) or 0))
        return Response(self.get_serializer(items, many=True).data)

    def get_queryset(self):
        qs = Question.objects.select_related('quiz').prefetch_related('choices')
        p = self.request.query_params
        if p.get('quiz'):
            qs = qs.filter(quiz_id=p['quiz'])
        if p.get('topic'):
            qs = qs.filter(topic=p['topic'])
        if p.get('bank') == '1':
            qs = qs.filter(in_exam_bank=True)
        if p.get('unassigned') == '1':
            qs = qs.filter(quiz__isnull=True)
        if p.get('q'):
            qs = qs.filter(Q(text_md__icontains=p['q']) | Q(explanation_md__icontains=p['q']))
        return qs.order_by('topic', 'quiz', 'order', 'id')

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        for i, qid in enumerate(request.data.get('ids', []), start=1):
            Question.objects.filter(pk=qid).update(order=i)
        return Response({'ok': True})

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        q = self.get_object()
        choices = list(q.choices.all())
        q.pk = None
        q.text_md = q.text_md + ' (copie)'
        q.save()
        for c in choices:
            c.pk, c.question = None, q
            c.save()
        return Response(QuestionAdminSerializer(q).data, status=201)


class AdminExamViewSet(_Logged, viewsets.ModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamAdminSerializer
    permission_classes = [IsSupervisorOrAdmin]
    pagination_class = None
    label = 'Examen blanc'


class MediaUploadView(APIView):
    """Téléversement d'un média (image / vidéo courte) pour une question ou une leçon : renvoie l'URL à enregistrer."""
    permission_classes = [IsSupervisorOrAdmin]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    ALLOWED = ('png', 'jpg', 'jpeg', 'webp', 'gif', 'mp4', 'webm')
    MAX_BYTES = 25 * 1024 * 1024

    def post(self, request):
        f = request.FILES.get('file')
        if not f:
            return Response({'detail': 'Fichier requis.'}, status=400)
        ext = (f.name.rsplit('.', 1)[-1] if '.' in f.name else '').lower()
        if ext not in self.ALLOWED:
            return Response({'detail': f"Format non accepté ({ext or 'inconnu'}). Images : png, jpg, webp, gif — vidéos : mp4, webm."}, status=400)
        if f.size > self.MAX_BYTES:
            return Response({'detail': 'Fichier trop lourd (25 Mo maximum). Pour une longue vidéo, utilisez un lien YouTube / Vimeo.'}, status=400)
        a = LessonAsset.objects.create(title=request.data.get('title', '') or f.name, file=f)
        url = request.build_absolute_uri(a.file.url)
        return Response({'id': a.id, 'url': url, 'kind': 'video' if ext in ('mp4', 'webm') else 'image', 'markdown': f"![{a.title}]({url})"}, status=201)


class ThemesView(APIView):
    """Les 10 thèmes officiels + nombre de questions en banque pour chacun."""
    permission_classes = [IsSupervisorOrAdmin]

    def get(self, request):
        counts = dict(Question.objects.filter(in_exam_bank=True, is_published=True).values_list('topic').annotate(n=Count('id')).values_list('topic', 'n'))
        return Response([{'code': c, 'title': t, 'description': d, 'default_count': n, 'bank': counts.get(c, 0), 'label': theme_label(c)} for c, t, d, n in THEMES])
