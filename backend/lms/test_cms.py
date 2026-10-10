from django.test import override_settings
from rest_framework.test import APITestCase

from core.models import Competency, StudentProfile, User

from .models import Choice, Question, Quiz, QuizAttempt, Section


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class CmsSuccessRateAndProgrammeTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='a@kaho.app', email='a@kaho.app', password='pass12345', role='ADMIN')
        su = User.objects.create_user(username='e@kaho.app', email='e@kaho.app', password='pass12345', role='STUDENT')
        self.student = su.student_profile
        r = self.client.post('/api/auth/token/', {'username': 'a@kaho.app', 'password': 'pass12345'})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def test_programme_covers_the_ten_themes_with_enough_questions(self):
        for code, n in dict(L=10, C=7, R=4, U=3, D=3, P=2, M=3, S=3, E=3, A=2).items():
            self.assertGreaterEqual(Question.objects.filter(topic=code, in_exam_bank=True, is_published=True).count(), n * 2, code)
            self.assertGreaterEqual(Section.objects.get(code=code).lessons.filter(is_published=True).count(), 3, code)
        # chaque question à choix a au moins une bonne réponse, et pas plus de 4 propositions
        for q in Question.objects.filter(kind__in=('SINGLE', 'MULTI', 'TRUE_FALSE')):
            ch = list(q.choices.all())
            self.assertTrue(any(c.is_correct for c in ch), q.text_md)
            self.assertTrue(2 <= len(ch) <= 4, q.text_md)

    def test_remc_grid_has_the_four_competencies_and_twenty_sub_competencies(self):
        self.assertEqual(Competency.objects.count(), 20)
        self.assertEqual({g: Competency.objects.filter(group=g).count() for g in (1, 2, 3, 4)}, {1: 6, 2: 6, 3: 4, 4: 4})
        self.assertEqual(Competency.objects.get(code='1.5').label[:15], 'Démarrer en côt')

    def test_question_list_filters_on_success_rate_and_unanswered(self):
        quiz = Quiz.objects.get(section=Section.objects.get(code='L'))
        quiz.questions.update(quiz=None)  # isole le quiz pour le test
        hard = Question.objects.create(quiz=quiz, text_md='Difficile ?', topic='L', in_exam_bank=True)
        easy = Question.objects.create(quiz=quiz, text_md='Facile ?', topic='L', in_exam_bank=True)
        never = Question.objects.create(quiz=quiz, text_md='Jamais posée ?', topic='L', in_exam_bank=True)
        ids = {}
        for q in (hard, easy, never):
            good = Choice.objects.create(question=q, text='ok', is_correct=True)
            bad = Choice.objects.create(question=q, text='ko')
            ids[q.id] = (good.id, bad.id)
        # 4 tentatives : « facile » toujours juste, « difficile » juste 1 fois sur 4
        for i in range(4):
            QuizAttempt.objects.create(student=self.student, quiz=quiz, score=50, passed=False, answers={
                str(easy.id): [ids[easy.id][0]], str(hard.id): [ids[hard.id][0] if i == 0 else ids[hard.id][1]]})
        r = self.client.get('/api/lms/admin/questions/', {'topic': 'L', 'with_stats': 1})
        rates = {q['id']: q['success_rate'] for q in r.data}
        self.assertEqual(rates[hard.id], 25)
        self.assertEqual(rates[easy.id], 100)
        self.assertIsNone(rates[never.id])
        r = self.client.get('/api/lms/admin/questions/', {'topic': 'L', 'max_success': 50, 'quiz': quiz.id})
        self.assertEqual([q['id'] for q in r.data], [hard.id])
        r = self.client.get('/api/lms/admin/questions/', {'topic': 'L', 'unanswered': 1, 'quiz': quiz.id})
        self.assertEqual([q['id'] for q in r.data], [never.id])

    def test_editor_refuses_more_than_four_propositions(self):
        body = {'kind': 'SINGLE', 'text_md': 'Q ?', 'topic': 'L', 'in_exam_bank': True,
                'choices': [{'text': str(i), 'is_correct': i == 0} for i in range(5)]}
        self.assertEqual(self.client.post('/api/lms/admin/questions/', body, format='json').status_code, 400)
        body['choices'] = body['choices'][:4]
        self.assertEqual(self.client.post('/api/lms/admin/questions/', body, format='json').status_code, 201)
