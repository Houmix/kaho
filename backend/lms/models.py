import random
import re
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


# ---------- Contenu ----------

# Les 10 thèmes officiels de l'épreuve théorique générale (ETG) et la répartition indicative des 40 questions
THEMES = [
    ('L', 'La circulation routière', 'Signalisation, panneaux, règles de priorité, intersections, vitesses', 10),
    ('C', 'Le conducteur', 'Vigilance, fatigue, alcool, drogues, médicaments, vision, temps de réaction', 7),
    ('R', 'La route', 'Conduite nocturne, intempéries, adhérence, chaussée dégradée, autoroute', 4),
    ('U', 'Les autres usagers', 'Partage de la route, piétons, cyclistes, deux-roues, véhicules lourds', 3),
    ('D', 'Réglementation générale', 'Papiers du véhicule, permis à points, infractions, contrôle technique, équipements', 3),
    ('P', 'Prendre et quitter son véhicule', 'Installation au poste de conduite, passagers, sécurité des enfants', 2),
    ('M', 'Éléments mécaniques et de sécurité', 'Commandes, voyants du tableau de bord, pneumatiques, entretien', 3),
    ('S', 'Équipements de sécurité des véhicules', 'Ceinture, airbags, aides à la conduite, ABS, ESP', 3),
    ('E', "L'environnement", 'Éco-conduite, pollution, consommations, choix du véhicule', 3),
    ('A', 'Premiers secours', 'Protéger, Alerter, Secourir (PAS), comportement en cas d’accident', 2),
]
THEME_LABELS = {code: title for code, title, _, _ in THEMES}
DEFAULT_DISTRIBUTION = {code: n for code, _, _, n in THEMES}


def theme_label(code):
    return f"{code} — {THEME_LABELS[code]}" if code in THEME_LABELS else (code or 'Général')

class Course(models.Model):
    title = models.CharField("Titre", max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField("Description", blank=True)
    cover_url = models.URLField("Image de couverture (URL)", blank=True)
    order = models.PositiveIntegerField("Ordre", default=0)
    is_published = models.BooleanField("Publié", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Cours"
        verbose_name_plural = "Cours"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:50] or 'cours'
        super().save(*args, **kwargs)

    @property
    def lesson_count(self):
        return Lesson.objects.filter(section__course=self, is_published=True).count()


class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField("Titre", max_length=150)
    code = models.CharField("Thème officiel", max_length=2, blank=True, choices=[(c, f"{c} — {t}") for c, t, _, _ in THEMES], help_text="Lettre du thème ETG (L, C, R, U, D, P, M, S, E, A)")
    order = models.PositiveIntegerField("Ordre", default=0)
    is_free_preview = models.BooleanField("Chapitre de démonstration (accès libre sans compte)", default=False)
    unlock_threshold = models.PositiveSmallIntegerField(
        "Score minimal au quiz pour débloquer la section suivante (%)", default=80,
        help_text="0 = pas de verrou",
    )

    class Meta:
        ordering = ['course', 'order', 'id']
        verbose_name = "Section"

    def __str__(self):
        return f"{self.course.title} › {self.title}"


class Lesson(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField("Titre", max_length=150)
    slug = models.SlugField(blank=True)
    order = models.PositiveIntegerField("Ordre", default=0)
    video_url = models.URLField("Vidéo (YouTube, Vimeo ou fichier .mp4)", blank=True)
    content_md = models.TextField("Contenu (Markdown : titres, listes, images, blocs de code ```lang)", blank=True)
    estimated_minutes = models.PositiveSmallIntegerField("Durée estimée (min)", default=10)
    is_published = models.BooleanField("Publié", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['section', 'order', 'id']
        verbose_name = "Leçon"
        unique_together = ('section', 'slug')

    def __str__(self):
        return f"{self.section.title} › {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:50] or f'lecon-{self.order}'
        super().save(*args, **kwargs)

    @property
    def embed_url(self):
        """Transforme une URL YouTube/Vimeo « page » en URL d'intégration."""
        return embed_url_for(self.video_url)


def embed_url_for(u):
    """URL « page » YouTube / Vimeo → URL d'intégration ; sinon inchangée."""
    m = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([\w-]{6,})', u or '')
    if m:
        return f"https://www.youtube-nocookie.com/embed/{m.group(1)}?rel=0"
    m = re.search(r'vimeo\.com/(?:video/)?(\d+)', u or '')
    if m:
        return f"https://player.vimeo.com/video/{m.group(1)}"
    return u or ''


def lesson_asset_upload(instance, filename):
    return f"lms/{timezone.localdate():%Y/%m}/{filename}"


class LessonAsset(models.Model):
    """Images et schémas à insérer dans le Markdown (copier l'URL)."""
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    title = models.CharField(max_length=120, blank=True)
    file = models.FileField(upload_to=lesson_asset_upload)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Image / schéma"
        verbose_name_plural = "Images / schémas"

    def __str__(self):
        return self.title or self.file.name


# ---------- Évaluation ----------

class Quiz(models.Model):
    """Quiz de fin de leçon ou de section. Correction instantanée."""
    section = models.OneToOneField(Section, on_delete=models.CASCADE, null=True, blank=True, related_name='quiz')
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, null=True, blank=True, related_name='quiz')
    title = models.CharField("Titre", max_length=150)
    pass_score = models.PositiveSmallIntegerField("Score de réussite (%)", default=80)
    is_published = models.BooleanField("Publié", default=True)

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quiz"

    def __str__(self):
        return self.title

    @property
    def course(self):
        return (self.section or self.lesson.section).course


class Question(models.Model):
    KINDS = [
        ('SINGLE', 'QCM — une seule bonne réponse'),
        ('MULTI', 'QCM — plusieurs bonnes réponses'),
        ('TRUE_FALSE', 'Vrai / Faux'),
        ('SHORT', 'Réponse courte'),
        ('CODE', 'Saisie de code'),
    ]
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, null=True, blank=True, related_name='questions', help_text="Vide = question de la banque d'examen uniquement")
    kind = models.CharField("Type", max_length=12, choices=KINDS, default='SINGLE')
    text_md = models.TextField("Énoncé (Markdown)")
    explanation_md = models.TextField("Explication affichée après correction (Markdown)", blank=True)
    expected_answer = models.CharField("Réponse attendue (réponse courte / code)", max_length=500, blank=True)
    points = models.PositiveSmallIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    topic = models.CharField("Thème (banque d'examen)", max_length=60, blank=True, db_index=True)
    image_url = models.URLField("Illustration (URL de l'image)", max_length=500, blank=True)
    video_url = models.URLField("Vidéo explicative (YouTube, Vimeo, .mp4 / .webm)", max_length=500, blank=True)
    in_exam_bank = models.BooleanField("Dans la banque d'examens blancs", default=False)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['quiz', 'order', 'id']
        verbose_name = "Question"

    def __str__(self):
        return self.text_md[:80]

    @staticmethod
    def _norm(s):
        return re.sub(r'\s+', ' ', (s or '').strip().lower())

    def grade_answer(self, answer):
        """answer : liste d'ids de choix (SINGLE/MULTI/TRUE_FALSE) ou chaîne (SHORT/CODE). Retourne (correct, bonne_réponse)."""
        if self.kind in ('SINGLE', 'MULTI', 'TRUE_FALSE'):
            correct_ids = set(self.choices.filter(is_correct=True).values_list('id', flat=True))
            given = set(int(x) for x in (answer or []) if str(x).isdigit()) if isinstance(answer, (list, tuple)) else ({int(answer)} if str(answer).isdigit() else set())
            return given == correct_ids, sorted(correct_ids)
        if self.kind == 'CODE':
            ok = re.sub(r'\s+', '', (answer or '')).lower() == re.sub(r'\s+', '', self.expected_answer).lower()
            return ok, self.expected_answer
        accepted = [self._norm(a) for a in self.expected_answer.split('|') if a.strip()]
        return self._norm(answer if isinstance(answer, str) else '') in accepted, self.expected_answer.split('|')[0]

    @property
    def video_embed(self):
        return embed_url_for(self.video_url)

    @property
    def video_is_file(self):
        return self.video_url.lower().split('?')[0].endswith(('.mp4', '.webm', '.m4v'))

    def public(self):
        return {
            'id': self.id, 'kind': self.kind, 'text_md': self.text_md, 'points': self.points, 'topic': self.topic,
            'image_url': self.image_url, 'video_url': self.video_url, 'video_embed': self.video_embed, 'video_is_file': self.video_is_file,
            'choices': [{'id': c.id, 'text': c.text} for c in self.choices.all()],
        }


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField("Proposition", max_length=300)
    is_correct = models.BooleanField("Bonne réponse", default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['question', 'order', 'id']
        verbose_name = "Proposition"

    def __str__(self):
        return self.text


class Exam(models.Model):
    """Examen blanc : tirage aléatoire dans la banque, chronomètre, correction différée."""
    title = models.CharField("Titre", max_length=150)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveSmallIntegerField("Durée (min)", default=30)
    question_count = models.PositiveSmallIntegerField("Nombre de questions", default=40)
    pass_score = models.PositiveSmallIntegerField("Score de réussite (%)", default=88, help_text="ETG officiel : 35/40 = 87,5 %")
    topics = models.CharField("Thèmes (séparés par des virgules, vide = tous)", max_length=300, blank=True)
    seconds_per_question = models.PositiveSmallIntegerField("Secondes par question (0 = chrono global uniquement)", default=20)
    distribution = models.JSONField("Répartition par thème (code → nombre de questions)", default=dict, blank=True, help_text="Vide = tirage aléatoire simple")
    is_published = models.BooleanField("Publié", default=True)
    is_demo = models.BooleanField("Série d'essai gratuite (sans compte)", default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Examen blanc"
        verbose_name_plural = "Examens blancs"

    def __str__(self):
        return self.title

    @property
    def total_seconds(self):
        """Temps total alloué : chrono par question × nombre de questions (+ marge), sinon la durée globale."""
        if self.seconds_per_question:
            return self.question_count * self.seconds_per_question + 30
        return self.duration_minutes * 60

    def draw_questions(self):
        """Tirage aléatoire ; si une répartition par thème est définie, même répartition statistique que l'examen national
        (complétée aléatoirement si un thème manque de questions)."""
        qs = Question.objects.filter(in_exam_bank=True, is_published=True).prefetch_related('choices')
        if self.topics.strip():
            qs = qs.filter(topic__in=[t.strip() for t in self.topics.split(',') if t.strip()])
        pool = list(qs)
        random.shuffle(pool)
        if not self.distribution:
            return pool[:self.question_count]
        chosen, used = [], set()
        by_topic = {}
        for q in pool:
            by_topic.setdefault(q.topic, []).append(q)
        for code, n in self.distribution.items():
            for q in by_topic.get(code, [])[:int(n)]:
                chosen.append(q); used.add(q.id)
        for q in pool:
            if len(chosen) >= self.question_count:
                break
            if q.id not in used:
                chosen.append(q); used.add(q.id)
        random.shuffle(chosen)
        return chosen[:self.question_count]


# ---------- Suivi ----------

class LessonProgress(models.Model):
    student = models.ForeignKey('core.StudentProfile', on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'lesson')


class StudyTime(models.Model):
    """Temps passé sur la plateforme (battements de cœur envoyés par les pages de cours / quiz / examens)."""
    student = models.ForeignKey('core.StudentProfile', on_delete=models.CASCADE, related_name='study_time')
    day = models.DateField()
    seconds = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('student', 'day')


class QuizAttempt(models.Model):
    student = models.ForeignKey('core.StudentProfile', on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveSmallIntegerField("Score (%)")
    passed = models.BooleanField()
    answers = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @classmethod
    def best_score(cls, student, quiz):
        return cls.objects.filter(student=student, quiz=quiz).aggregate(m=models.Max('score'))['m']


class ExamAttempt(models.Model):
    STATUS = [('IN_PROGRESS', 'En cours'), ('SUBMITTED', 'Terminé'), ('EXPIRED', 'Temps écoulé')]
    student = models.ForeignKey('core.StudentProfile', on_delete=models.CASCADE, related_name='exam_attempts')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    question_ids = models.JSONField(default=list)
    answers = models.JSONField(default=dict)   # {question_id: answer}
    status = models.CharField(max_length=12, choices=STATUS, default='IN_PROGRESS')
    score = models.PositiveSmallIntegerField(null=True, blank=True)
    passed = models.BooleanField(null=True, blank=True)
    correct_count = models.PositiveSmallIntegerField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    @property
    def seconds_left(self):
        return max(0, int((self.deadline - timezone.now()).total_seconds()))

    def grade(self, expired=False):
        """Corrige avec les réponses enregistrées ; idempotent."""
        if self.status != 'IN_PROGRESS':
            return self
        questions = {q.id: q for q in Question.objects.filter(id__in=self.question_ids).prefetch_related('choices')}
        total = sum(q.points for q in questions.values()) or 1
        earned, correct = 0, 0
        for qid, q in questions.items():
            ok, _ = q.grade_answer(self.answers.get(str(qid)))
            if ok:
                earned += q.points
                correct += 1
        self.score = round(100 * earned / total)
        self.correct_count = correct
        self.passed = self.score >= self.exam.pass_score
        self.status = 'EXPIRED' if expired else 'SUBMITTED'
        self.submitted_at = timezone.now()
        self.save()
        return self

    def report(self):
        questions = Question.objects.filter(id__in=self.question_ids).prefetch_related('choices')
        by_id = {q.id: q for q in questions}
        items = []
        for qid in self.question_ids:
            q = by_id.get(qid)
            if not q:
                continue
            ok, good = q.grade_answer(self.answers.get(str(qid)))
            items.append({**q.public(), 'given': self.answers.get(str(qid)), 'correct': ok, 'correct_answer': good, 'explanation_md': q.explanation_md})
        return items
