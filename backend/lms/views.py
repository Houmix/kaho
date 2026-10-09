from datetime import timedelta

from django.db.models import Count, F as models_F, Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Offer, StudentProfile, User
from core.permissions import IsStudent, IsSupervisorOrAdmin
from core.permissions import IsStaff
from .models import Course, Exam, ExamAttempt, Lesson, LessonProgress, Question, Quiz, QuizAttempt, Section, StudyTime, THEMES, theme_label
from .serializers import (
    CourseDetailSerializer, CourseSerializer, ExamAttemptSerializer, ExamSerializer, LessonDetailSerializer,
    QuizAttemptSerializer, QuizSerializer, SectionSerializer,
)


# ---------- Accès ----------

def _student(request):
    if request.user.is_authenticated and request.user.role == 'STUDENT':
        return StudentProfile.objects.filter(user=request.user).first()
    return None


def _has_full_access(request):
    u = request.user
    if not u.is_authenticated:
        return False
    if u.role in User.STAFF_ROLES:
        return True
    st = _student(request)
    return bool(st and st.has_lms_access)


def _section_states(course, student, full_access):
    """Pour chaque section : verrouillée ou non (score au quiz de la section précédente), meilleur score."""
    sections = list(course.sections.prefetch_related('lessons', 'quiz__questions').order_by('order', 'id'))
    prev = None
    for s in sections:
        s.best_score = QuizAttempt.best_score(student, s.quiz) if (student and hasattr(s, 'quiz')) else None
        s.locked, s.lock_reason = False, ''
        if not full_access and not s.is_free_preview:
            s.locked, s.lock_reason = True, 'Réservé aux formules incluant le code en ligne.'
        elif prev is not None and prev.unlock_threshold and hasattr(prev, 'quiz') and prev.quiz.is_published and prev.quiz.questions.exists():
            if not student or (prev.best_score or 0) < prev.unlock_threshold:
                s.locked = True
                s.lock_reason = f"Obtenez au moins {prev.unlock_threshold} % au quiz « {prev.quiz.title} » pour débloquer cette section."
        prev = s
    return sections


def _upsell():
    offer = Offer.objects.filter(is_active=True, includes_lms=True).order_by('price').first()
    return {'id': offer.id, 'name': offer.name, 'price': str(offer.price)} if offer else None


# ---------- Cours ----------

class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """Catalogue des cours : visible par tous ; le contenu est filtré selon l'accès."""
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    lookup_field = 'slug'

    def get_queryset(self):
        return Course.objects.filter(is_published=True)

    def _annotate(self, courses, student):
        completed = set(LessonProgress.objects.filter(student=student).values_list('lesson_id', flat=True)) if student else set()
        for c in courses:
            total = c.lesson_count
            done = Lesson.objects.filter(section__course=c, is_published=True, id__in=completed).count()
            c.completed_count, c.percent = done, (round(100 * done / total) if total else 0)
        return completed

    def list(self, request):
        courses = list(self.get_queryset())
        self._annotate(courses, _student(request))
        return Response({'courses': CourseSerializer(courses, many=True).data, 'has_access': _has_full_access(request), 'upsell': _upsell()})

    def retrieve(self, request, slug=None):
        course = get_object_or_404(self.get_queryset(), slug=slug)
        student = _student(request)
        completed = self._annotate([course], student)
        full = _has_full_access(request)
        sections = _section_states(course, student, full)
        data = CourseDetailSerializer(course, context={'sections': sections, 'completed_ids': completed}).data
        data['has_access'] = full
        data['upsell'] = None if full else _upsell()
        return Response(data)


class LessonViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Lesson.objects.filter(is_published=True, section__course__is_published=True).select_related('section__course')

    def _check_access(self, request, lesson):
        student = _student(request)
        sections = _section_states(lesson.section.course, student, _has_full_access(request))
        state = next(s for s in sections if s.id == lesson.section_id)
        return (not state.locked), state.lock_reason, student

    def retrieve(self, request, pk=None):
        lesson = get_object_or_404(self.queryset, pk=pk)
        ok, reason, student = self._check_access(request, lesson)
        if not ok:
            return Response({'detail': reason, 'locked': True, 'upsell': _upsell()}, status=status.HTTP_403_FORBIDDEN)
        ordered = list(Lesson.objects.filter(section__course=lesson.section.course, is_published=True).order_by('section__order', 'section__id', 'order', 'id'))
        idx = next(i for i, l in enumerate(ordered) if l.id == lesson.id)
        nav = lambda l: {'id': l.id, 'title': l.title, 'slug': l.slug} if l else None
        lesson.prev = nav(ordered[idx - 1] if idx > 0 else None)
        lesson.next = nav(ordered[idx + 1] if idx + 1 < len(ordered) else None)
        lesson.completed = bool(student and LessonProgress.objects.filter(student=student, lesson=lesson).exists())
        return Response(LessonDetailSerializer(lesson).data)

    @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    def complete(self, request, pk=None):
        lesson = get_object_or_404(self.queryset, pk=pk)
        ok, reason, student = self._check_access(request, lesson)
        if not ok:
            return Response({'detail': reason}, status=403)
        LessonProgress.objects.get_or_create(student=student, lesson=lesson)
        course = lesson.section.course
        total = course.lesson_count
        done = LessonProgress.objects.filter(student=student, lesson__section__course=course, lesson__is_published=True).count()
        return Response({'completed': True, 'course_percent': round(100 * done / total) if total else 0})


# ---------- Quiz ----------

class QuizViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Quiz.objects.filter(is_published=True).select_related('section__course', 'lesson__section__course')

    def _access(self, request, quiz):
        section = quiz.section or quiz.lesson.section
        student = _student(request)
        sections = _section_states(section.course, student, _has_full_access(request))
        state = next(s for s in sections if s.id == section.id)
        return (not state.locked), state.lock_reason, student

    def retrieve(self, request, pk=None):
        quiz = get_object_or_404(self.queryset, pk=pk)
        ok, reason, student = self._access(request, quiz)
        if not ok:
            return Response({'detail': reason, 'locked': True}, status=403)
        if student:
            quiz.best_score = QuizAttempt.best_score(student, quiz)
            quiz.attempt_count = QuizAttempt.objects.filter(student=student, quiz=quiz).count()
        return Response(QuizSerializer(quiz).data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Correction instantanée. answers = {question_id: [choice_ids] | "texte"}."""
        quiz = get_object_or_404(self.queryset, pk=pk)
        ok, reason, student = self._access(request, quiz)
        if not ok:
            return Response({'detail': reason}, status=403)
        answers = request.data.get('answers') or {}
        questions = list(quiz.questions.filter(is_published=True).prefetch_related('choices'))
        total = sum(q.points for q in questions) or 1
        earned, items = 0, []
        for q in questions:
            correct, good = q.grade_answer(answers.get(str(q.id)))
            if correct:
                earned += q.points
            items.append({'id': q.id, 'correct': correct, 'correct_answer': good, 'explanation_md': q.explanation_md, 'given': answers.get(str(q.id))})
        score = round(100 * earned / total)
        passed = score >= quiz.pass_score
        unlocked = None
        if student:
            QuizAttempt.objects.create(student=student, quiz=quiz, score=score, passed=passed, answers=answers)
            section = quiz.section or quiz.lesson.section
            if quiz.section and section.unlock_threshold and score >= section.unlock_threshold:
                nxt = section.course.sections.filter(order__gt=section.order).order_by('order', 'id').first()
                unlocked = {'id': nxt.id, 'title': nxt.title} if nxt else None
        return Response({'score': score, 'passed': passed, 'pass_score': quiz.pass_score, 'correct': sum(1 for i in items if i['correct']),
                         'total': len(items), 'items': items, 'unlocked_section': unlocked, 'saved': bool(student)})


# ---------- Examens blancs ----------

class ExamViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExamSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = Exam.objects.filter(is_published=True)
        return qs if _has_full_access(self.request) else qs.filter(is_demo=True)

    def list(self, request):
        exams = list(self.get_queryset())
        student = _student(request)
        for e in exams:
            agg = ExamAttempt.objects.filter(student=student, exam=e).exclude(status='IN_PROGRESS').aggregate(n=Count('id'), m=Max('score')) if student else {'n': 0, 'm': None}
            e.attempt_count, e.best_score = agg["n"], agg["m"]
        history = ExamAttemptSerializer(ExamAttempt.objects.filter(student=student).select_related('exam')[:20], many=True).data if student else []
        return Response({'exams': ExamSerializer(exams, many=True).data, 'history': history, 'has_access': _has_full_access(request), 'upsell': _upsell()})

    @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    def start(self, request, pk=None):
        exam = get_object_or_404(self.get_queryset(), pk=pk)
        student = _student(request)
        current = ExamAttempt.objects.filter(student=student, exam=exam, status='IN_PROGRESS').first()
        if current and current.seconds_left > 0:
            return Response(self._payload(current))
        if current:
            current.grade(expired=True)
        questions = exam.draw_questions()
        if not questions:
            return Response({'detail': "Aucune question disponible pour cet examen."}, status=400)
        attempt = ExamAttempt.objects.create(student=student, exam=exam, question_ids=[q.id for q in questions],
                                             deadline=timezone.now() + timedelta(seconds=exam.total_seconds))
        return Response(self._payload(attempt), status=201)

    def _payload(self, attempt):
        by_id = {q.id: q for q in Question.objects.filter(id__in=attempt.question_ids).prefetch_related('choices')}
        return {'attempt': ExamAttemptSerializer(attempt).data, 'questions': [by_id[i].public() for i in attempt.question_ids if i in by_id], 'answers': attempt.answers}

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def demo(self, request):
        """Série d'essai sans compte : questions de l'examen de démo, correction immédiate, rien n'est enregistré."""
        exam = Exam.objects.filter(is_published=True, is_demo=True).first()
        if not exam:
            return Response({'detail': 'Pas de série de démonstration.'}, status=404)
        if 'answers' not in request.data:
            questions = exam.draw_questions()[:10]
            return Response({'exam': ExamSerializer(exam).data, 'questions': [q.public() for q in questions]})
        answers = request.data.get('answers') or {}
        ids = [int(i) for i in answers.keys() if str(i).isdigit()] + [int(i) for i in request.data.get('question_ids', []) if str(i).isdigit()]
        questions = Question.objects.filter(id__in=ids, in_exam_bank=True).prefetch_related('choices')
        items, correct = [], 0
        for q in questions:
            ok, good = q.grade_answer(answers.get(str(q.id)))
            correct += ok
            items.append({**q.public(), 'given': answers.get(str(q.id)), 'correct': ok, 'correct_answer': good, 'explanation_md': q.explanation_md})
        total = len(items) or 1
        score = round(100 * correct / total)
        return Response({'score': score, 'correct': correct, 'total': len(items), 'passed': score >= exam.pass_score, 'items': items, 'upsell': _upsell(),
                         'bank_size': Question.objects.filter(in_exam_bank=True, is_published=True).count()})


class ExamAttemptViewSet(viewsets.GenericViewSet):
    permission_classes = [IsStudent]
    serializer_class = ExamAttemptSerializer

    def get_queryset(self):
        return ExamAttempt.objects.filter(student=_student(self.request)).select_related('exam')

    def retrieve(self, request, pk=None):
        attempt = get_object_or_404(self.get_queryset(), pk=pk)
        if attempt.status == 'IN_PROGRESS' and attempt.seconds_left == 0:
            attempt.grade(expired=True)
        if attempt.status == 'IN_PROGRESS':
            return Response(ExamViewSet()._payload(attempt))
        return Response({'attempt': ExamAttemptSerializer(attempt).data, 'items': attempt.report()})

    @action(detail=True, methods=['patch'])
    def answers(self, request, pk=None):
        """Sauvegarde progressive des réponses (robuste aux coupures)."""
        attempt = get_object_or_404(self.get_queryset(), pk=pk)
        if attempt.status != 'IN_PROGRESS':
            return Response({'detail': 'Examen terminé.'}, status=400)
        if attempt.seconds_left == 0:
            attempt.grade(expired=True)
            return Response({'detail': 'Temps écoulé : copie remise automatiquement.', 'expired': True}, status=409)
        incoming = request.data.get('answers') or {}
        attempt.answers = {**attempt.answers, **{str(k): v for k, v in incoming.items() if int(k) in attempt.question_ids}}
        attempt.save(update_fields=['answers'])
        return Response({'saved': len(attempt.answers), 'seconds_left': attempt.seconds_left})

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        attempt = get_object_or_404(self.get_queryset(), pk=pk)
        if attempt.status != 'IN_PROGRESS':
            return Response({'detail': 'Examen déjà remis.'}, status=400)
        incoming = request.data.get('answers') or {}
        if incoming:
            attempt.answers = {**attempt.answers, **{str(k): v for k, v in incoming.items() if int(k) in attempt.question_ids}}
        attempt.grade(expired=attempt.seconds_left == 0)
        return Response({'attempt': ExamAttemptSerializer(attempt).data, 'items': attempt.report()})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        return Response(student_stats(_student(request)))

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def heartbeat(self, request):
        """Temps passé : +N secondes (max 120) pour la journée. Appelé toutes les 60 s par les pages du LMS."""
        st = _student(request)
        if st:
            sec = min(120, max(0, int(request.data.get('seconds') or 60)))
            row, _ = StudyTime.objects.get_or_create(student=st, day=timezone.localdate())
            StudyTime.objects.filter(pk=row.pk).update(seconds=models_F('seconds') + sec)
        return Response({'ok': True})


def student_stats(student):
    """Analytics d'un élève : examens, préparation (5 derniers), évolution, thèmes, temps passé, séries."""
    if student is None:
        return {'attempts': 0, 'passed': 0, 'average': None, 'best': None, 'readiness': None, 'last_scores': [], 'evolution': [], 'by_topic': [],
                'quiz_attempts': 0, 'time_seconds': 0, 'lessons_done': 0, 'etg_validated_at': None}
    qs = ExamAttempt.objects.filter(student=student).exclude(status='IN_PROGRESS').select_related('exam')
    n = qs.count()
    scores = list(qs.values_list('score', flat=True))
    by_topic = {}
    for a in qs:
        for q in Question.objects.filter(id__in=a.question_ids).prefetch_related('choices'):
            ok, _ = q.grade_answer(a.answers.get(str(q.id)))
            t = by_topic.setdefault(q.topic or '', {'code': q.topic or '', 'topic': theme_label(q.topic), 'correct': 0, 'total': 0})
            t['total'] += 1
            t['correct'] += int(ok)
    # Quiz par thème : on complète les thèmes sans examen avec les quiz de section
    for qa in QuizAttempt.objects.filter(student=student).select_related('quiz__section'):
        code = qa.quiz.section.code if qa.quiz.section_id else ''
        if code and code not in by_topic:
            by_topic[code] = {'code': code, 'topic': theme_label(code), 'correct': 0, 'total': 0}
    ordered = list(qs.order_by('submitted_at'))
    last5 = [a.score for a in ordered[-5:]]
    readiness = round(sum(last5) / len(last5)) if last5 else None
    return {
        'attempts': n, 'passed': qs.filter(passed=True).count(),
        'average': round(sum(scores) / n) if n else None, 'best': max(scores) if scores else None,
        'readiness': readiness, 'readiness_count': len(last5),
        'last_scores': [a.score for a in ordered[-10:]],
        'evolution': [{'date': a.submitted_at.date().isoformat() if a.submitted_at else None, 'score': a.score, 'passed': a.passed, 'exam': a.exam.title} for a in ordered[-30:]],
        'by_topic': sorted([{**t, 'percent': round(100 * t['correct'] / t['total']) if t['total'] else None} for t in by_topic.values()], key=lambda x: (x['percent'] is None, x['percent'] or 0)),
        'quiz_attempts': QuizAttempt.objects.filter(student=student).count(),
        'time_seconds': sum(StudyTime.objects.filter(student=student).values_list('seconds', flat=True)),
        'lessons_done': LessonProgress.objects.filter(student=student).count(),
        'etg_validated_at': student.etg_validated_at,
    }


class RevisionView(APIView):
    """Mode révision ciblée : les questions échouées (quiz et examens) de l'élève, par thème ; correction immédiate."""
    permission_classes = [IsStudent]

    def _failed(self, student):
        failed = {}
        for qa in QuizAttempt.objects.filter(student=student).select_related('quiz'):
            for q in qa.quiz.questions.filter(is_published=True).prefetch_related('choices'):
                ok, _ = q.grade_answer(qa.answers.get(str(q.id)))
                if not ok:
                    failed[q.id] = q
        for a in ExamAttempt.objects.filter(student=student).exclude(status='IN_PROGRESS'):
            for q in Question.objects.filter(id__in=a.question_ids, is_published=True).prefetch_related('choices'):
                ok, _ = q.grade_answer(a.answers.get(str(q.id)))
                if not ok:
                    failed[q.id] = q
        return list(failed.values())

    def get(self, request):
        st = _student(request)
        questions = self._failed(st)
        topic = request.query_params.get('topic')
        if topic:
            questions = [q for q in questions if q.topic == topic]
        by_topic = {}
        for q in questions:
            by_topic.setdefault(q.topic or '', 0)
            by_topic[q.topic or ''] += 1
        return Response({'count': len(questions), 'questions': [q.public() for q in questions[:30]],
                         'topics': [{'code': c, 'label': theme_label(c), 'n': n} for c, n in sorted(by_topic.items(), key=lambda x: -x[1])]})

    def post(self, request):
        answers = request.data.get('answers') or {}
        ids = [int(i) for i in answers.keys() if str(i).isdigit()]
        items, correct = [], 0
        for q in Question.objects.filter(id__in=ids).prefetch_related('choices'):
            ok, good = q.grade_answer(answers.get(str(q.id)))
            correct += ok
            items.append({**q.public(), 'given': answers.get(str(q.id)), 'correct': ok, 'correct_answer': good, 'explanation_md': q.explanation_md})
        total = len(items) or 1
        return Response({'score': round(100 * correct / total), 'correct': correct, 'total': len(items), 'items': items})


class AdminStudentLmsView(APIView):
    """Relevé LMS d'un élève pour le moniteur / l'admin + validation de l'inscription à l'examen ETG."""
    permission_classes = [IsStaff]

    def get(self, request, student_id):
        st = get_object_or_404(StudentProfile, pk=student_id)
        data = student_stats(st)
        data['history'] = ExamAttemptSerializer(ExamAttempt.objects.filter(student=st).exclude(status='IN_PROGRESS').select_related('exam')[:20], many=True).data
        data['quizzes'] = QuizAttemptSerializer(QuizAttempt.objects.filter(student=st).select_related('quiz')[:20], many=True).data
        data['has_lms_access'] = st.has_lms_access
        data['etg_validated_by'] = st.etg_validated_by.get_full_name() if st.etg_validated_by else None
        return Response(data)

    def post(self, request, student_id):
        """Valide (ou annule : {cancel: true}) l'inscription à l'examen officiel du code."""
        from core.models import log_activity
        st = get_object_or_404(StudentProfile, pk=student_id)
        if str(request.data.get('cancel', 'false')).lower() in ('true', '1'):
            st.etg_validated_at, st.etg_validated_by = None, None
            msg = f"{st.user.get_full_name()} — validation ETG annulée"
        else:
            st.etg_validated_at, st.etg_validated_by = timezone.now(), request.user
            msg = f"{st.user.get_full_name()} — niveau atteint, inscription à l'examen du code (ETG) validée"
        st.save(update_fields=['etg_validated_at', 'etg_validated_by'])
        log_activity('STATUS', msg, actor=request.user, student=st)
        return Response({'etg_validated_at': st.etg_validated_at})


# ---------- Démo publique ----------

class DemoView(APIView):
    """Chapitre gratuit (sections « démonstration ») + série d'essai, sans compte."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        sections = Section.objects.filter(is_free_preview=True, course__is_published=True).select_related('course').prefetch_related('lessons')
        data = []
        for s in sections:
            lessons = s.lessons.filter(is_published=True)
            data.append({'course': {'slug': s.course.slug, 'title': s.course.title}, 'section': {'id': s.id, 'title': s.title},
                         'lessons': [{'id': l.id, 'title': l.title, 'slug': l.slug, 'estimated_minutes': l.estimated_minutes} for l in lessons],
                         'quiz_id': s.quiz.id if hasattr(s, 'quiz') and s.quiz.is_published else None})
        demo_exam = Exam.objects.filter(is_published=True, is_demo=True).first()
        return Response({'chapters': data, 'demo_exam': ExamSerializer(demo_exam).data if demo_exam else None, 'upsell': _upsell(),
                         'bank_size': Question.objects.filter(in_exam_bank=True, is_published=True).count()})


# ---------- Back-office ----------

class AdminLmsOverviewView(APIView):
    permission_classes = [IsSupervisorOrAdmin]

    def get(self, request):
        courses = []
        for c in Course.objects.prefetch_related('sections__lessons', 'sections__quiz'):
            courses.append({
                'id': c.id, 'title': c.title, 'slug': c.slug, 'is_published': c.is_published, 'order': c.order,
                'sections': [{
                    'id': s.id, 'title': s.title, 'order': s.order, 'is_free_preview': s.is_free_preview, 'unlock_threshold': s.unlock_threshold,
                    'lessons': [{'id': l.id, 'title': l.title, 'is_published': l.is_published, 'has_video': bool(l.video_url), 'minutes': l.estimated_minutes,
                                 'completions': l.progress.count()} for l in s.lessons.all()],
                    'quiz': ({'id': s.quiz.id, 'title': s.quiz.title, 'questions': s.quiz.questions.count(), 'attempts': s.quiz.attempts.count(),
                              'pass_rate': (round(100 * s.quiz.attempts.filter(passed=True).count() / s.quiz.attempts.count()) if s.quiz.attempts.exists() else None)}
                             if hasattr(s, 'quiz') else None),
                } for s in c.sections.all()],
            })
        exams = [{'id': e.id, 'title': e.title, 'is_published': e.is_published, 'is_demo': e.is_demo, 'question_count': e.question_count,
                  'available': len(e.draw_questions()), 'attempts': e.attempts.exclude(status='IN_PROGRESS').count(),
                  'pass_rate': (round(100 * e.attempts.filter(passed=True).count() / e.attempts.exclude(status='IN_PROGRESS').count()) if e.attempts.exclude(status='IN_PROGRESS').exists() else None)}
                 for e in Exam.objects.all()]
        return Response({
            'courses': courses, 'exams': exams,
            'bank': {'total': Question.objects.filter(in_exam_bank=True).count(),
                     'topics': list(Question.objects.filter(in_exam_bank=True).exclude(topic='').values('topic').annotate(n=Count('id')).order_by('-n'))},
            'learners': {'with_access': StudentProfile.objects.filter(lms_access=True).count(),
                         'active': LessonProgress.objects.filter(completed_at__gte=timezone.now() - timedelta(days=30)).values('student').distinct().count()},
        })

    def post(self, request):
        """Bascules rapides : {model: course|section|lesson|exam, id, field: is_published|is_free_preview|is_demo, value}"""
        models = {'course': Course, 'section': Section, 'lesson': Lesson, 'exam': Exam}
        allowed = {'course': ('is_published',), 'section': ('is_free_preview', 'unlock_threshold'), 'lesson': ('is_published',), 'exam': ('is_published', 'is_demo')}
        m, f = request.data.get('model'), request.data.get('field')
        if m not in models or f not in allowed.get(m, ()):
            return Response({'detail': 'Champ non modifiable.'}, status=400)
        obj = get_object_or_404(models[m], pk=request.data.get('id'))
        setattr(obj, f, request.data.get('value'))
        obj.save(update_fields=[f])
        return Response({'ok': True})
