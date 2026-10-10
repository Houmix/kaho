"""Programme intégral : chapitres rédigés pour chacun des 10 thèmes ETG et banque de questions d'examen.
Idempotente : une leçon (même titre) ou une question (même énoncé) déjà présente n'est jamais recréée ni écrasée,
de sorte que les contenus modifiés depuis le back-office sont préservés."""
from django.db import migrations

from lms.curriculum import PROGRAMME, shuffled_choices

QUIZ_SIZE = 10  # les 10 premières questions de chaque thème alimentent le quiz de la section, les autres la banque d'examen seule


def forwards(apps, schema_editor):
    Course = apps.get_model('lms', 'Course')
    Section = apps.get_model('lms', 'Section')
    Lesson = apps.get_model('lms', 'Lesson')
    Quiz = apps.get_model('lms', 'Quiz')
    Question = apps.get_model('lms', 'Question')
    Choice = apps.get_model('lms', 'Choice')

    course = Course.objects.filter(slug='code-de-la-route').first() or Course.objects.order_by('id').first()
    if course is None:
        return
    for code, data in PROGRAMME.items():
        section = Section.objects.filter(course=course, code=code).first()
        if section is None:
            continue
        quiz = Quiz.objects.filter(section=section).first()

        order = max([l.order for l in Lesson.objects.filter(section=section)] or [0])
        existing_titles = set(Lesson.objects.filter(section=section).values_list('title', flat=True))
        existing_slugs = set(Lesson.objects.filter(section=section).values_list('slug', flat=True))
        for slug, title, minutes, md in data['lessons']:
            if title in existing_titles or slug in existing_slugs:
                continue
            order += 1
            Lesson.objects.create(section=section, title=title, slug=slug, order=order, estimated_minutes=minutes, content_md=md, is_published=True)

        known = set(Question.objects.filter(topic=code).values_list('text_md', flat=True))
        in_quiz = quiz.questions.count() if quiz else 0
        for text, choices, correct, explanation in data['questions']:
            if text in known:
                continue
            attach = quiz is not None and in_quiz < QUIZ_SIZE
            kind = 'TRUE_FALSE' if [c.lower() for c in choices] == ['vrai', 'faux'] else ('MULTI' if len(correct) > 1 else 'SINGLE')
            q = Question.objects.create(quiz=quiz if attach else None, kind=kind, text_md=text, explanation_md=explanation,
                                        topic=code, in_exam_bank=True, is_published=True, order=in_quiz + 1)
            if attach:
                in_quiz += 1
            for i, (label, ok) in enumerate(shuffled_choices(text, choices, correct), start=1):
                Choice.objects.create(question=q, text=label, is_correct=ok, order=i)


class Migration(migrations.Migration):
    dependencies = [('lms', '0005_question_media')]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
