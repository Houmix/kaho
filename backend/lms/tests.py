from datetime import timedelta

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import Offer, User
from .models import Course, Exam, ExamAttempt, Lesson, Question, Quiz, QuizAttempt, Section


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class LmsTests(APITestCase):
    """S'appuie sur le contenu chargé par les migrations 0002 (démo) et 0004 (10 thèmes officiels)."""

    def setUp(self):
        self.course = Course.objects.get(slug='code-de-la-route')
        sections = list(self.course.sections.order_by('order'))
        self.assertEqual([s.code for s in sections], list('LCRUDPMSEA'))
        self.s1, self.s2, self.s3 = sections[0], sections[1], sections[2]
        # verrou par quiz sur le thème L pour tester le déblocage
        Section.objects.filter(pk=self.s1.pk).update(unlock_threshold=80)
        self.s1.refresh_from_db()
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
        self.assertFalse(states[self.s1.title]['locked'])
        self.assertTrue(states[self.s2.title]['locked'])
        free_lesson = self.s1.lessons.first()
        self.assertEqual(self.client.get(f'/api/lms/lessons/{free_lesson.id}/').status_code, 200)
        paid_lesson = self.s2.lessons.first()
        r = self.client.get(f'/api/lms/lessons/{paid_lesson.id}/')
        self.assertEqual(r.status_code, 403)
        self.assertTrue(r.data['locked'])
        demo = self.client.get('/api/lms/demo/').data
        self.assertEqual(demo['chapters'][0]['section']['title'], 'L — La circulation routière')
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
        self.assertEqual(r.data['course_percent'], round(100 / self.course.lesson_count))
        course = self.client.get(f'/api/lms/courses/{self.course.slug}/').data
        self.assertEqual(course['percent'], round(100 / self.course.lesson_count))
        states = {s['title']: s for s in course['sections']}
        self.assertTrue(states[self.s1.title]['lessons'][0]['completed'])
        # Section 2 verrouillée tant que le quiz de la section 1 n'est pas réussi (≥ 80 %)
        self.assertTrue(states[self.s2.title]['locked'])
        self.assertIn('80 %', states[self.s2.title]['lock_reason'])
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
        self.assertEqual(r.data['unlocked_section']['title'], self.s2.title)
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
        self.assertGreater(r.data['attempt']['seconds_left'], 800)  # 40 × 20 s + marge
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
        good2 = self.answers_for(Question.objects.filter(id__in=[q['id'] for q in r.data['questions']]))  # tirage différent du premier
        self.client.patch(f'/api/lms/exam-attempts/{a2_id}/answers/', {'answers': dict(list(good2.items())[:3])}, format='json')
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
        self.assertEqual(len(d['courses'][0]['sections']), 10)
        self.assertEqual(d['bank']['total'], Question.objects.filter(in_exam_bank=True).count())
        r = self.client.post('/api/lms/admin/overview/', {'model': 'course', 'id': self.course.id, 'field': 'is_published', 'value': False}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.get('/api/lms/courses/').data['courses'], [])
        self.assertEqual(self.client.post('/api/lms/admin/overview/', {'model': 'course', 'id': self.course.id, 'field': 'title', 'value': 'x'}, format='json').status_code, 400)
        self.auth('paid@test.fr')
        self.assertEqual(self.client.get('/api/lms/admin/overview/').status_code, 403)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, MEDIA_ROOT='/tmp/kaho_test_media')
class LmsEditorAndAnalyticsTests(APITestCase):
    """§13–15 : thèmes officiels, éditeur de contenu intégré, examen 40 q / 20 s, révision ciblée, analytics, validation ETG."""

    def setUp(self):
        self.course = Course.objects.get(slug='code-de-la-route')
        self.admin = User.objects.create_user(username='a@kaho.app', email='a@kaho.app', password='pass12345', first_name='Al', last_name='Admin', role='ADMIN')
        self.owner = User.objects.create_user(username='o@kaho.app', email='o@kaho.app', password='pass12345', role='OWNER')
        self.ins = User.objects.create_user(username='m@kaho.app', email='m@kaho.app', password='pass12345', first_name='Marc', last_name='Moniteur', role='INSTRUCTOR')
        su = User.objects.create_user(username='paid@test.fr', email='paid@test.fr', password='pass12345', first_name='Paula', last_name='Payée', role='STUDENT')
        su.student_profile.lms_access = True
        su.student_profile.save()
        self.student = su.student_profile

    def auth(self, username):
        r = self.client.post('/api/auth/token/', {'username': username, 'password': 'pass12345'})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def test_themes_and_exam_distribution(self):
        self.auth('a@kaho.app')
        themes = self.client.get('/api/lms/admin/themes/').data
        self.assertEqual([t['code'] for t in themes], list('LCRUDPMSEA'))
        self.assertEqual(sum(t['default_count'] for t in themes), 40)
        self.assertEqual(themes[0]['bank'], Question.objects.filter(topic='L', in_exam_bank=True, is_published=True).count())
        exam = Exam.objects.get(is_demo=False)
        self.assertEqual((exam.question_count, exam.seconds_per_question, exam.distribution['L']), (40, 20, 10))
        self.assertEqual(exam.total_seconds, 40 * 20 + 30)
        # tirage : 40 questions, réparties selon la répartition nationale (la banque couvre les 10 thèmes)
        drawn = exam.draw_questions()
        self.assertEqual(len(drawn), 40)
        by_topic = {}
        for q in drawn:
            by_topic[q.topic] = by_topic.get(q.topic, 0) + 1
        self.assertEqual(by_topic, exam.distribution)

        # thème appauvri : si la banque d'un thème est trop courte, le tirage complète avec les autres thèmes
        Question.objects.filter(topic='A').update(in_exam_bank=False)
        Question.objects.filter(topic='A', pk=Question.objects.filter(topic='A').first().pk).update(in_exam_bank=True)
        drawn = exam.draw_questions()
        self.assertEqual(len(drawn), 40)
        self.assertEqual(sum(1 for q in drawn if q.topic == 'A'), 1)

    def test_editor_crud_course_section_lesson_quiz_question(self):
        self.auth('a@kaho.app')
        r = self.client.post('/api/lms/admin/courses/', {'title': 'Code moto', 'description': 'ETM'})
        self.assertEqual(r.status_code, 201, r.content)
        cid = r.data['id']
        self.assertEqual(r.data['slug'], 'code-moto')
        r = self.client.post(f'/api/lms/admin/courses/{cid}/seed_themes/')
        self.assertEqual(len(r.data['sections']), 10)
        sec = r.data['sections'][0]
        self.assertEqual(sec['code'], 'L')
        self.assertIsNotNone(sec['quiz'])
        r = self.client.post('/api/lms/admin/lessons/', {'section': sec['id'], 'title': 'Les feux', 'content_md': '## Feux\n\n```text\nrouge = stop\n```', 'video_url': 'https://youtu.be/abc123xyz', 'estimated_minutes': 7})
        self.assertEqual(r.status_code, 201, r.content)
        lid = r.data['id']
        self.assertEqual(self.client.patch(f'/api/lms/admin/lessons/{lid}/', {'title': 'Les feux (v2)'}).data['title'], 'Les feux (v2)')
        # question de quiz avec propositions, validation d'une bonne réponse
        body = {'quiz': sec['quiz']['id'], 'kind': 'SINGLE', 'text_md': 'Feu orange ?', 'topic': 'L', 'in_exam_bank': True, 'explanation_md': "On s'arrête sauf danger.",
                'choices': [{'text': 'Je passe', 'is_correct': False}, {'text': "Je m'arrête", 'is_correct': True}]}
        r = self.client.post('/api/lms/admin/questions/', body, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        qid = r.data['id']
        self.assertEqual(len(r.data['choices']), 2)
        bad = {**body, 'choices': [{'text': 'a', 'is_correct': True}, {'text': 'b', 'is_correct': True}]}
        self.assertEqual(self.client.post('/api/lms/admin/questions/', bad, format='json').status_code, 400)
        # mise à jour des propositions (remplace / ajoute / supprime)
        r = self.client.patch(f'/api/lms/admin/questions/{qid}/', {'choices': [{'id': r.data['choices'][1]['id'], 'text': "Je m'arrête", 'is_correct': True}, {'text': 'Je klaxonne', 'is_correct': False}, {'text': 'J’accélère', 'is_correct': False}]}, format='json')
        self.assertEqual(len(r.data['choices']), 3)
        self.assertEqual(self.client.get(f"/api/lms/admin/questions/?quiz={sec['quiz']['id']}").data[0]['id'], qid)
        self.assertEqual(self.client.post(f'/api/lms/admin/questions/{qid}/duplicate/').status_code, 201)
        self.assertEqual(self.client.get('/api/lms/admin/questions/?topic=L&bank=1').data.__len__(), Question.objects.filter(topic='L', in_exam_bank=True).count())
        # examen blanc créé depuis le back-office
        r = self.client.post('/api/lms/admin/exams/', {'title': 'Série courte', 'question_count': 5, 'seconds_per_question': 20, 'pass_score': 80, 'distribution': {'L': 5}}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data['available'], 5)
        # suppression tracée
        self.assertEqual(self.client.delete(f'/api/lms/admin/lessons/{lid}/').status_code, 204)
        from core.models import ActivityLog
        self.assertTrue(ActivityLog.objects.filter(kind='LMS', message__contains='Leçon supprimé').exists())
        # un élève n'accède pas à l'éditeur
        self.auth('paid@test.fr')
        self.assertEqual(self.client.get('/api/lms/admin/questions/').status_code, 403)

    def test_revision_mode_heartbeat_stats_and_etg_validation(self):
        self.auth('paid@test.fr')
        exam = Exam.objects.get(is_demo=False)
        r = self.client.post(f'/api/lms/exams/{exam.id}/start/')
        aid, qs = r.data['attempt']['id'], r.data['questions']
        # répond faux à tout → questions échouées disponibles en révision
        wrong = {}
        for q in Question.objects.filter(id__in=[x['id'] for x in qs]):
            wrong[str(q.id)] = [q.choices.filter(is_correct=False).first().id] if q.kind != 'SHORT' else 'xxx'
        self.client.post(f'/api/lms/exam-attempts/{aid}/submit/', {'answers': wrong}, format='json')
        rev = self.client.get('/api/lms/revision/').data
        self.assertEqual(rev['count'], len(qs))
        self.assertEqual(rev['topics'][0]['code'], 'L')
        self.assertNotIn('is_correct', str(rev['questions']))
        good = {}
        for q in Question.objects.filter(id__in=[x['id'] for x in rev['questions'][:5]]):
            good[str(q.id)] = list(q.choices.filter(is_correct=True).values_list('id', flat=True)) if q.kind != 'SHORT' else q.expected_answer.split('|')[0]
        r = self.client.post('/api/lms/revision/', {'answers': good}, format='json')
        self.assertEqual(r.data['score'], 100)
        self.assertTrue(all('explanation_md' in i for i in r.data['items']))
        # temps passé
        self.client.post('/api/lms/exam-attempts/heartbeat/', {'seconds': 60})
        self.client.post('/api/lms/exam-attempts/heartbeat/', {'seconds': 60})
        stats = self.client.get('/api/lms/exam-attempts/stats/').data
        self.assertEqual(stats['time_seconds'], 120)
        self.assertEqual(stats['readiness'], 0)
        self.assertEqual(stats['readiness_count'], 1)
        self.assertEqual(stats['evolution'][0]['score'], 0)
        self.assertIn('L', [t['code'] for t in stats['by_topic']])
        # relevé moniteur + validation ETG
        self.auth('m@kaho.app')
        d = self.client.get(f'/api/lms/admin/students/{self.student.id}/').data
        self.assertEqual(d['attempts'], 1)
        self.assertEqual(d['time_seconds'], 120)
        r = self.client.post(f'/api/lms/admin/students/{self.student.id}/')
        self.assertIsNotNone(r.data['etg_validated_at'])
        self.student.refresh_from_db()
        self.assertEqual(self.student.etg_validated_by, self.ins)
        self.auth('paid@test.fr')
        self.assertIsNotNone(self.client.get('/api/lms/exam-attempts/stats/').data['etg_validated_at'])

    def test_offers_admin_crud_owner_only(self):
        self.auth('a@kaho.app')
        self.assertEqual(self.client.get('/api/admin/offers/').status_code, 403)
        self.auth('o@kaho.app')
        r = self.client.post('/api/admin/offers/', {'name': 'Pack 20 h', 'category': 'PERMIS_B', 'hours': 20, 'price': 890, 'includes_lms': True, 'validity_months': 12, 'is_active': True}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        oid = r.data['id']
        self.assertEqual(self.client.patch(f'/api/admin/offers/{oid}/', {'price': 850}).data['price'], '850.00')
        self.assertEqual(self.client.get('/api/offers/').data[0]['price'], '850.00')
        self.assertEqual(self.client.delete(f'/api/admin/offers/{oid}/').status_code, 204)
        self.assertEqual(self.client.get('/api/offers/').data, [])

    @override_settings(DJANGO_ADMIN_ENABLED=False)
    def test_django_admin_disabled_in_production(self):
        from django.urls import clear_url_caches
        import importlib, config.urls
        clear_url_caches(); importlib.reload(config.urls)
        self.assertEqual(self.client.get('/admin/').status_code, 404)
        with override_settings(DJANGO_ADMIN_ENABLED=True):
            clear_url_caches(); importlib.reload(config.urls)
            self.assertIn(self.client.get('/admin/').status_code, (200, 302))
        clear_url_caches(); importlib.reload(config.urls)
