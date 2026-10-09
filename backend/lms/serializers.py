from rest_framework import serializers

from .models import Course, Exam, ExamAttempt, Lesson, Quiz, QuizAttempt, Section


class LessonListSerializer(serializers.ModelSerializer):
    completed = serializers.BooleanField(read_only=True, default=False)
    has_quiz = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ('id', 'title', 'slug', 'order', 'estimated_minutes', 'completed', 'has_quiz')

    def get_has_quiz(self, obj):
        return hasattr(obj, 'quiz') and obj.quiz.is_published


class SectionSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()
    quiz_id = serializers.SerializerMethodField()
    locked = serializers.BooleanField(read_only=True, default=False)
    lock_reason = serializers.CharField(read_only=True, default='')
    best_score = serializers.IntegerField(read_only=True, allow_null=True, default=None)

    class Meta:
        model = Section
        fields = ('id', 'title', 'order', 'is_free_preview', 'unlock_threshold', 'lessons', 'quiz_id', 'locked', 'lock_reason', 'best_score')

    def get_lessons(self, obj):
        completed = self.context.get('completed_ids', set())
        data = []
        for l in obj.lessons.filter(is_published=True):
            l.completed = l.id in completed
            data.append(LessonListSerializer(l).data)
        return data

    def get_quiz_id(self, obj):
        return obj.quiz.id if hasattr(obj, 'quiz') and obj.quiz.is_published else None


class CourseSerializer(serializers.ModelSerializer):
    lesson_count = serializers.IntegerField(read_only=True)
    completed_count = serializers.IntegerField(read_only=True, default=0)
    percent = serializers.IntegerField(read_only=True, default=0)
    has_free_preview = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ('id', 'title', 'slug', 'description', 'cover_url', 'lesson_count', 'completed_count', 'percent', 'has_free_preview')

    def get_has_free_preview(self, obj):
        return obj.sections.filter(is_free_preview=True).exists()


class CourseDetailSerializer(CourseSerializer):
    sections = serializers.SerializerMethodField()

    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + ('sections',)

    def get_sections(self, obj):
        return SectionSerializer(self.context['sections'], many=True, context=self.context).data


class LessonDetailSerializer(serializers.ModelSerializer):
    section_id = serializers.IntegerField(read_only=True)
    section_title = serializers.CharField(source='section.title', read_only=True)
    course_slug = serializers.CharField(source='section.course.slug', read_only=True)
    course_title = serializers.CharField(source='section.course.title', read_only=True)
    embed_url = serializers.CharField(read_only=True)
    is_mp4 = serializers.SerializerMethodField()
    quiz_id = serializers.SerializerMethodField()
    completed = serializers.BooleanField(read_only=True, default=False)
    prev = serializers.DictField(read_only=True, allow_null=True)
    next = serializers.DictField(read_only=True, allow_null=True)

    class Meta:
        model = Lesson
        fields = ('id', 'title', 'slug', 'section_id', 'section_title', 'course_slug', 'course_title', 'video_url', 'embed_url', 'is_mp4',
                  'content_md', 'estimated_minutes', 'quiz_id', 'completed', 'prev', 'next')

    def get_is_mp4(self, obj):
        return obj.video_url.lower().split('?')[0].endswith(('.mp4', '.webm', '.m4v'))

    def get_quiz_id(self, obj):
        return obj.quiz.id if hasattr(obj, 'quiz') and obj.quiz.is_published else None


class QuizSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    course_slug = serializers.SerializerMethodField()
    best_score = serializers.IntegerField(read_only=True, allow_null=True, default=None)
    attempts = serializers.IntegerField(source='attempt_count', read_only=True, default=0)

    class Meta:
        model = Quiz
        fields = ('id', 'title', 'pass_score', 'section', 'lesson', 'course_slug', 'questions', 'best_score', 'attempts')

    def get_questions(self, obj):
        return [q.public() for q in obj.questions.filter(is_published=True).prefetch_related('choices')]

    def get_course_slug(self, obj):
        return obj.course.slug


class QuizAttemptSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)

    class Meta:
        model = QuizAttempt
        fields = ('id', 'quiz', 'quiz_title', 'score', 'passed', 'created_at')


class ExamSerializer(serializers.ModelSerializer):
    available_questions = serializers.SerializerMethodField()
    attempts = serializers.IntegerField(source='attempt_count', read_only=True, default=0)
    best_score = serializers.IntegerField(read_only=True, allow_null=True, default=None)

    class Meta:
        model = Exam
        fields = ('id', 'title', 'description', 'duration_minutes', 'question_count', 'pass_score', 'seconds_per_question', 'is_demo', 'available_questions', 'attempts', 'best_score')

    def get_available_questions(self, obj):
        return len(obj.draw_questions())


class ExamAttemptSerializer(serializers.ModelSerializer):
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    pass_score = serializers.IntegerField(source='exam.pass_score', read_only=True)
    duration_minutes = serializers.IntegerField(source='exam.duration_minutes', read_only=True)
    seconds_per_question = serializers.IntegerField(source='exam.seconds_per_question', read_only=True)
    seconds_left = serializers.IntegerField(read_only=True)
    total = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ExamAttempt
        fields = ('id', 'exam', 'exam_title', 'pass_score', 'duration_minutes', 'seconds_per_question', 'status', 'status_display', 'score', 'passed', 'correct_count', 'total',
                  'started_at', 'deadline', 'seconds_left', 'submitted_at')

    def get_total(self, obj):
        return len(obj.question_ids)


# ---------- Back-office : éditeur de contenu ----------

class ChoiceAdminSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        from .models import Choice
        model = Choice
        fields = ('id', 'text', 'is_correct', 'order')


class QuestionAdminSerializer(serializers.ModelSerializer):
    choices = ChoiceAdminSerializer(many=True, required=False)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True, default=None)
    topic_label = serializers.SerializerMethodField()

    class Meta:
        from .models import Question
        model = Question
        fields = ('id', 'quiz', 'quiz_title', 'kind', 'text_md', 'explanation_md', 'expected_answer', 'points', 'order', 'topic', 'topic_label', 'in_exam_bank', 'is_published', 'choices')

    def get_topic_label(self, obj):
        from .models import theme_label
        return theme_label(obj.topic)

    def validate(self, data):
        kind = data.get('kind', getattr(self.instance, 'kind', 'SINGLE'))
        choices = data.get('choices')
        if kind in ('SINGLE', 'MULTI', 'TRUE_FALSE') and choices is not None:
            if len(choices) < 2:
                raise serializers.ValidationError({'choices': 'Au moins deux propositions.'})
            good = sum(1 for c in choices if c.get('is_correct'))
            if good == 0:
                raise serializers.ValidationError({'choices': 'Cochez au moins une bonne réponse.'})
            if kind != 'MULTI' and good > 1:
                raise serializers.ValidationError({'choices': 'Une seule bonne réponse pour ce type de question.'})
        if kind in ('SHORT', 'CODE') and not (data.get('expected_answer') or getattr(self.instance, 'expected_answer', '')):
            raise serializers.ValidationError({'expected_answer': 'Indiquez la réponse attendue.'})
        return data

    def _sync_choices(self, question, choices):
        from .models import Choice
        keep = []
        for i, c in enumerate(choices):
            cid = c.get('id')
            obj = Choice.objects.filter(pk=cid, question=question).first() if cid else None
            if obj:
                obj.text, obj.is_correct, obj.order = c['text'], c.get('is_correct', False), i
                obj.save()
            else:
                obj = Choice.objects.create(question=question, text=c['text'], is_correct=c.get('is_correct', False), order=i)
            keep.append(obj.id)
        question.choices.exclude(id__in=keep).delete()

    def create(self, validated):
        choices = validated.pop('choices', [])
        q = super().create(validated)
        self._sync_choices(q, choices)
        return q

    def update(self, instance, validated):
        choices = validated.pop('choices', None)
        q = super().update(instance, validated)
        if choices is not None:
            self._sync_choices(q, choices)
        return q


class QuizAdminSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    section_title = serializers.CharField(source='section.title', read_only=True, default=None)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True, default=None)

    class Meta:
        model = Quiz
        fields = ('id', 'title', 'pass_score', 'is_published', 'section', 'lesson', 'section_title', 'lesson_title', 'question_count')

    def get_question_count(self, obj):
        return obj.questions.count()


class LessonAdminSerializer(serializers.ModelSerializer):
    quiz_id = serializers.SerializerMethodField()
    completions = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ('id', 'section', 'title', 'slug', 'order', 'video_url', 'content_md', 'estimated_minutes', 'is_published', 'quiz_id', 'completions')
        read_only_fields = ('slug',)

    def get_quiz_id(self, obj):
        return obj.quiz.id if hasattr(obj, 'quiz') else None

    def get_completions(self, obj):
        return obj.progress.count()


class SectionAdminSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()
    quiz = serializers.SerializerMethodField()
    code_label = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ('id', 'course', 'title', 'code', 'code_label', 'order', 'is_free_preview', 'unlock_threshold', 'lessons', 'quiz')

    def get_lessons(self, obj):
        return [{'id': l.id, 'title': l.title, 'slug': l.slug, 'order': l.order, 'is_published': l.is_published, 'has_video': bool(l.video_url), 'minutes': l.estimated_minutes, 'completions': l.progress.count()} for l in obj.lessons.all()]

    def get_quiz(self, obj):
        if not hasattr(obj, 'quiz'):
            return None
        q = obj.quiz
        n = q.attempts.count()
        return {'id': q.id, 'title': q.title, 'questions': q.questions.count(), 'is_published': q.is_published, 'attempts': n,
                'pass_rate': round(100 * q.attempts.filter(passed=True).count() / n) if n else None}

    def get_code_label(self, obj):
        from .models import THEME_LABELS
        return THEME_LABELS.get(obj.code, '')


class CourseAdminSerializer(serializers.ModelSerializer):
    sections = SectionAdminSerializer(many=True, read_only=True)
    lesson_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = ('id', 'title', 'slug', 'description', 'cover_url', 'order', 'is_published', 'lesson_count', 'sections')
        read_only_fields = ('slug',)


class ExamAdminSerializer(serializers.ModelSerializer):
    available = serializers.SerializerMethodField()
    attempts = serializers.SerializerMethodField()
    pass_rate = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = ('id', 'title', 'description', 'duration_minutes', 'question_count', 'pass_score', 'topics', 'seconds_per_question', 'distribution',
                  'is_published', 'is_demo', 'order', 'available', 'attempts', 'pass_rate')

    def get_available(self, obj):
        return len(obj.draw_questions())

    def get_attempts(self, obj):
        return obj.attempts.exclude(status='IN_PROGRESS').count()

    def get_pass_rate(self, obj):
        n = obj.attempts.exclude(status='IN_PROGRESS').count()
        return round(100 * obj.attempts.filter(passed=True).count() / n) if n else None

    def validate_distribution(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError('Format attendu : {"L": 10, "C": 7, …}')
        return {str(k): int(v) for k, v in value.items() if str(v).lstrip('-').isdigit() and int(v) > 0}
