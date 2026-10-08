from django.contrib import admin

from .models import Choice, Course, Exam, ExamAttempt, Lesson, LessonAsset, Question, Quiz, QuizAttempt, Section


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0
    fields = ('order', 'title', 'is_free_preview', 'unlock_threshold')
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'order', 'lesson_count')
    list_editable = ('is_published', 'order')
    prepopulated_fields = {'slug': ('title',)}
    inlines = (SectionInline,)


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ('order', 'title', 'estimated_minutes', 'is_published')
    show_change_link = True


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'is_free_preview', 'unlock_threshold')
    list_filter = ('course', 'is_free_preview')
    list_editable = ('order', 'is_free_preview')
    inlines = (LessonInline,)


class LessonAssetInline(admin.TabularInline):
    model = LessonAsset
    extra = 0
    readonly_fields = ('url',)

    def url(self, obj):
        return obj.file.url if obj.file else ''
    url.short_description = "URL à coller dans le Markdown : ![titre](URL)"


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'order', 'estimated_minutes', 'is_published')
    list_filter = ('section__course', 'is_published')
    list_editable = ('order', 'is_published')
    search_fields = ('title', 'content_md')
    prepopulated_fields = {'slug': ('title',)}
    inlines = (LessonAssetInline,)
    fieldsets = (
        (None, {'fields': ('section', 'title', 'slug', 'order', 'is_published', 'estimated_minutes')}),
        ('Vidéo', {'fields': ('video_url',), 'description': "Lien YouTube / Vimeo ou URL d'un fichier .mp4. La veille de l'écran est bloquée pendant la lecture."}),
        ('Contenu', {'fields': ('content_md',), 'description': "Markdown. Bloc de code : ```python … ```. Image : ![légende](URL)."}),
    )


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2
    fields = ('order', 'text', 'is_correct')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('short', 'kind', 'quiz', 'topic', 'in_exam_bank', 'points', 'is_published')
    list_filter = ('kind', 'in_exam_bank', 'topic', 'quiz__section__course', 'is_published')
    list_editable = ('in_exam_bank', 'is_published')
    search_fields = ('text_md', 'topic')
    inlines = (ChoiceInline,)
    fieldsets = (
        (None, {'fields': ('quiz', 'kind', 'text_md', 'points', 'order', 'is_published')}),
        ('Correction', {'fields': ('expected_answer', 'explanation_md'), 'description': "Réponse courte : plusieurs réponses acceptées séparées par | . QCM : cocher les bonnes propositions ci-dessous."}),
        ("Banque d'examens blancs", {'fields': ('in_exam_bank', 'topic')}),
    )

    def short(self, obj):
        return obj.text_md[:70]
    short.short_description = 'Énoncé'


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0
    fields = ('order', 'kind', 'text_md', 'expected_answer', 'explanation_md', 'points', 'in_exam_bank', 'topic')
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'lesson', 'pass_score', 'is_published', 'question_total')
    list_filter = ('is_published',)
    inlines = (QuestionInline,)

    def question_total(self, obj):
        return obj.questions.count()
    question_total.short_description = 'Questions'


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'duration_minutes', 'question_count', 'pass_score', 'topics', 'is_published', 'is_demo', 'bank_size')
    list_editable = ('is_published', 'is_demo')

    def bank_size(self, obj):
        return len(obj.draw_questions())
    bank_size.short_description = 'Questions disponibles'


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'passed', 'created_at')
    list_filter = ('passed', 'quiz')
    readonly_fields = ('student', 'quiz', 'score', 'passed', 'answers', 'created_at')


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'status', 'score', 'passed', 'started_at', 'submitted_at')
    list_filter = ('status', 'passed', 'exam')
    readonly_fields = ('student', 'exam', 'question_ids', 'answers', 'status', 'score', 'passed', 'correct_count', 'started_at', 'deadline', 'submitted_at')
