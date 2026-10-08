from datetime import timedelta

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import Offer, User
from .models import Course, Exam, ExamAttempt, Lesson, Question, Quiz, QuizAttempt, Section


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class LmsTests(APITestCase):
    """S'appuie sur le contenu de démonstration chargé par la migration 0002."""

    def setUp(self):
        self.course = Course.objects.get(slug='code-de-la-route')
        self.s1, self.s2, self.s3 = list(self.course.sections.order_by('order'))
        self.offer = Offer.objects.create(name='Pass Code', hours=0, price=29, includes_lms=True)
        paid = User.objects.create_user(username='paid@test.fr', email='paid@test.fr', password='testpass123', first_name='Paula', last_name='Payée', role='STUDENT')
        paid.student_profile.lms_access = True
        paid.student_profile.save()
        self.paid = paid.student_profile
        free = User.objects.create_user(username='free@test.fr', email='free@test.fr', password='testpass123', first_name='Fred', last_name='Gratuit', role='STUDENT')
        self.free = free.student_profile
        self.admin = User.objects.create_user(username='a@kaho.app', email='a@kaho.app', password='pass12345', role='ADMIN')

    def auth(self, username, password='testpass123'):
        r = self.client.post('/api/auth/token/', {'username': username, 'password': password})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def answers_for(self, questions, correct=True):
        out = {}
        for q in questions:
            if q.kind in ('SINGLE', 'MULTI', 'TRUE_FALSE'):
                ids = list(q.choices.filter(is_correct=correct).values_list('id', flat=True)) if correct else [q.choices.filter(is_correct=False).first().id]
                out[str(q.id)] = ids
            else:
                out[str(q.id)] = q.expected_answer.split('|')[0] if correct else 'xxx'
        return out

    # ---- accès & démo ----

    def test_anonymous_sees_catalog_and_free_chapter_only(self):
        d = self.client.get('/api/lms/courses/').data
        self.assertFalse(d['has_access'])
        self.assertEqual(d['upsell']['name'], 'Pass Code')
        d = self.client.get(f'/api/lms/courses/{self.course.slug}/').data
        states = {s['title']: s for s in d['sections']}
        self.assertFalse(states['Les priorités']['locked'])
        self.assertTrue(states['La signalisation']['locked'])
        free_lesson = self.s1.lessons.first()
        self.assertEqual(self.client.get(f'/api/lms/lessons/{free_lesson.id}/').status_code, 200)
        paid_lesson = self.s2.lessons.first()
        r = self.client.get(f'/api/lms/lessons/{paid_lesson.id}/')
        self.assertEqual(r.status_code, 403)
        self.assertTrue(r.data['locked'])
        demo = self.client.get('/api/lms/demo/').data
        self.assertEqual(demo['chapters'][0]['section']['title'], 'Les priorités')
        self.assertTrue(demo['demo_exam']['is_demo'])
        self.assertGreaterEqual(demo['bank_size'], 15)

    def test_demo_exam_grades_without_saving(self):
        d = self.client.post('/api/lms/exams/demo/').data
        self.assertEqual(len(d['questions']), 10)
        questions = Question.objects.filter(id__in=[q['id'] for q in d['questions']])
        r = self.client.post('/api/lms/exams/demo/', {'answers': self.answers_for(questions), 'question_ids': [q.id for q in questions]}, format='json')
        self.assertEqual(r.data['score'], 100)
        self.assertTrue(r.data['passed'])
        self.assertEqual(r.data['upsell']['name'], 'Pass Code')
        self.assertEqual(ExamAttempt.objects.count(), 0)

    def test_student_without_access_cannot_open_paid_content_or_full_exam(self):
        self.auth('free@test.fr')
        self.assertEqual(self.client.get(f'/api/lms/lessons/{self.s2.lessons.first().id}/').status_code, 403)
        exams = self.client.get('/api/lms/exams/').data['exams']
        self.assertEqual([e['is_demo'] for e in exams], [True])
        full = Exam.objects.get(is_demo=False)
        self.assertEqual(self.client.post(f'/api/lms/exams/{full.id}/start/').status_code, 404)

    # ---- progression & déblocage ----

    def test_lesson_completion_navigation_and_section_unlock_by_quiz(self):
        self.auth('paid@test.fr')
        lessons = list(self.s1.lessons.order_by('order'))
        d = self.client.get(f'/api/lms/lessons/{lessons[0].id}/').data
        self.assertIsNone(d['prev'])
        self.assertEqual(d['next']['id'], lessons[1].id)
        self.assertIn('priorité à droite', d['content_md'])
        d = self.client.get(f'/api/lms/lessons/{lessons[1].id}/').data
        self.assertEqual(d['embed_url'], 'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?rel=0')

        r = self.client.post(f'/api/lms/lessons/{lessons[0].id}/complete/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['course_percent'], 20)  # 1 / 5 leçons
        course = self.client.get(f'/api/lms/courses/{self.course.slug}/').data
        self.assertEqual(course['percent'], 20)
        states = {s['title']: s for s in course['sections']}
        self.assertTrue(states['Les priorités']['lessons'][0]['completed'])
        # Section 2 verrouillée tant que le quiz de la section 1 n'est pas réussi (≥ 80 %)
        self.assertTrue(states['La signalisation']['locked'])
        self.assertIn('80 %', states['La signalisation']['lock_reason'])
        self.assertEqual(self.client.get(f'/api/lms/lessons/{self.s2.lessons.first().id}/').status_code, 403)

        quiz = self.s1.quiz
        qd = self.client.get(f'/api/lms/quizzes/{quiz.id}/').data
        self.assertEqual(len(qd['questions']), quiz.questions.count())
        self.assertNotIn('is_correct', str(qd['questions']))  # pas de fuite des réponses
        # Échec
        r = self.client.post(f'/api/lms/quizzes/{quiz.id}/submit/', {'answers': self.answers_for(quiz.questions.all(), correct=False)}, format='json')
        self.assertEqual(r.data['score'], 0)
        self.assertFalse(r.data['passed'])
        self.assertTrue(all('explanation_md' in i for i in r.data['items']))
        self.assertTrue(self.client.get(f'/api/lms/courses/{self.course.slug}/').data['sections'][1]['locked'])
        # Réussite → section suivante débloquée
        r = self.client.post(f'/api/lms/quizzes/{quiz.id}/submit/', {'answers': self.answers_for(quiz.questions.all())}, format='json')
        self.assertEqual(r.data['score'], 100)
        self.assertEqual(r.data['unlocked_section']['title'], 'La signalisation')
        self.assertEqual(QuizAttempt.objects.filter(student=self.paid).count(), 2)
        self.assertFalse(self.client.get(f'/api/lms/courses/{self.course.slug}/').data['sections'][1]['locked'])
        self.assertEqual(self.client.get(f'/api/lms/lessons/{self.s2.lessons.first().id}/').status_code, 200)

    def test_short_answer_and_code_matching(self):
        q = Question.objects.get(kind='SHORT')
        self.assertTrue(q.grade_answer('  Octogone ')[0])
        self.assertTrue(q.grade_answer('un octogone')[0])
        self.assertFalse(q.grade_answer('cercle')[0])
        code = Question.objects.create(kind='CODE', text_md='x', expected_answer='print("ok")')
        self.assertTrue(code.grade_answer('print( "ok" )')[0])
        self.assertFalse(code.grade_answer('print("ko")')[0])

    # ---- examens blancs ----

    def test_full_exam_flow_with_timer_autosave_and_stats(self):
        self.auth('paid@test.fr')
        exam = Exam.objects.get(is_demo=False)
        r = self.client.post(f'/api/lms/exams/{exam.id}/start/')
        self.assertEqual(r.status_code, 201, r.content)
        attempt_id = r.data['attempt']['id']
        qs = r.data['questions']
        self.assertEqual(len(qs), min(40, Question.objects.filter(in_exam_bank=True).count()))
        self.assertNotIn('is_correct', str(qs))
        self.assertGreater(r.data['attempt']['seconds_left'], 1700)
        # Redémarrer renvoie la même tentative en cours
        self.assertEqual(self.client.post(f'/api/lms/exams/{exam.id}/start/').data['attempt']['id'], attempt_id)
        # Pas de correction avant remise
        self.assertNotIn('items', self.client.get(f'/api/lms/exam-attempts/{attempt_id}/').data)

        questions = Question.objects.filter(id__in=[q['id'] for q in qs])
        good = self.answers_for(questions)
        first_half = dict(list(good.items())[: len(good) // 2])
        r = self.client.patch(f'/api/lms/exam-attempts/{attempt_id}/answers/', {'answers': first_half}, format='json')
        self.assertEqual(r.data['saved'], len(first_half))
        r = self.client.post(f'/api/lms/exam-attempts/{attempt_id}/submit/', {'answers': dict(list(good.items())[len(good) // 2:])}, format='json')
        self.assertEqual(r.data['attempt']['status'], 'SUBMITTED')
        self.assertEqual(r.data['attempt']['score'], 100)
        self.assertTrue(r.data['attempt']['passed'])
        self.assertEqual(len(r.data['items']), len(qs))
        self.assertEqual(self.client.post(f'/api/lms/exam-attempts/{attempt_id}/submit/').status_code, 400)

        # Temps écoulé → copie remise automatiquement avec les réponses sauvegardées
        r = self.client.post(f'/api/lms/exams/{exam.id}/start/')
        a2_id = r.data['attempt']['id']
        self.client.patch(f'/api/lms/exam-attempts/{a2_id}/answers/', {'answers': dict(list(good.items())[:3])}, format='json')
        ExamAttempt.objects.filter(pk=a2_id).update(deadline=timezone.now() - timedelta(seconds=1))
        r = self.client.patch(f'/api/lms/exam-attempts/{a2_id}/answers/', {'answers': {}}, format='json')
        self.assertEqual(r.status_code, 409)
        a2 = ExamAttempt.objects.get(pk=a2_id)
        self.assertEqual(a2.status, 'EXPIRED')
        self.assertEqual(a2.correct_count, 3)

        stats = self.client.get('/api/lms/exam-attempts/stats/').data
        self.assertEqual(stats['attempts'], 2)
        self.assertEqual(stats['passed'], 1)
        self.assertEqual(stats['best'], 100)
        self.assertTrue(stats['by_topic'])
        history = self.client.get('/api/lms/exams/').data
        self.assertEqual(history['exams'][1]['attempts'], 2)
        self.assertEqual(len(history['history']), 2)

    def test_students_cannot_see_others_attempts(self):
        self.auth('paid@test.fr')
        exam = Exam.objects.get(is_demo=False)
        attempt_id = self.client.post(f'/api/lms/exams/{exam.id}/start/').data['attempt']['id']
        other = User.objects.create_user(username='o@test.fr', email='o@test.fr', password='testpass123', role='STUDENT')
        other.student_profile.lms_access = True
        other.student_profile.save()
        self.auth('o@test.fr')
        self.assertEqual(self.client.get(f'/api/lms/exam-attempts/{attempt_id}/').status_code, 404)

    # ---- back-office ----

    def test_admin_overview_and_toggles(self):
        self.auth('a@kaho.app', 'pass12345')
        d = self.client.get('/api/lms/admin/overview/').data
        self.assertEqual(d['courses'][0]['title'], 'Code de la route')
        self.assertEqual(len(d['courses'][0]['sections']), 3)
        self.assertEqual(d['bank']['total'], 16)
        r = self.client.post('/api/lms/admin/overview/', {'model': 'course', 'id': self.course.id, 'field': 'is_published', 'value': False}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.get('/api/lms/courses/').data['courses'], [])
        self.assertEqual(self.client.post('/api/lms/admin/overview/', {'model': 'course', 'id': self.course.id, 'field': 'title', 'value': 'x'}, format='json').status_code, 400)
        self.auth('paid@test.fr')
        self.assertEqual(self.client.get('/api/lms/admin/overview/').status_code, 403)
