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
        fields = ('id', 'title', 'description', 'duration_minutes', 'question_count', 'pass_score', 'is_demo', 'available_questions', 'attempts', 'best_score')

    def get_available_questions(self, obj):
        return len(obj.draw_questions())


class ExamAttemptSerializer(serializers.ModelSerializer):
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    pass_score = serializers.IntegerField(source='exam.pass_score', read_only=True)
    duration_minutes = serializers.IntegerField(source='exam.duration_minutes', read_only=True)
    seconds_left = serializers.IntegerField(read_only=True)
    total = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ExamAttempt
        fields = ('id', 'exam', 'exam_title', 'pass_score', 'duration_minutes', 'status', 'status_display', 'score', 'passed', 'correct_count', 'total',
                  'started_at', 'deadline', 'seconds_left', 'submitted_at')

    def get_total(self, obj):
        return len(obj.question_ids)
