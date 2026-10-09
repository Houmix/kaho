"""§16–18 : multi-documents (ASSR2), moteur d'offres composable (options, compétences, abonnement, échelonné), webhook Stripe, médias de question."""
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import Competency, Offer, Package, StudentProfile, User


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, MEDIA_ROOT='/tmp/kaho_test_media')
class OfferEngineTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='o@kaho.app', email='o@kaho.app', password='pass12345', role='OWNER')
        su = User.objects.create_user(username='eleve@test.fr', email='eleve@test.fr', password='pass12345', first_name='Jean', last_name='Dupont', role='STUDENT')
        self.student = su.student_profile
        self.base = Offer.objects.create(name='Permis B 20 h', category='PERMIS_B', hours=20, price=1200, includes_lms=True, includes_exams=True, validity_months=12, billing_type='INSTALLMENTS_3')
        self.perf = Offer.objects.create(name='Option 5 h perfectionnement', category='OPTION', hours=5, price=250, is_addon=True, lets_student_pick_skills=True)
        self.perf.skills.set(Competency.objects.filter(code__in=['C3.1', 'C3.2']) or Competency.objects.all()[:2])
        self.exams = Offer.objects.create(name='Option examens blancs', category='OPTION', hours=0, price=19, is_addon=True, includes_exams=True)
        self.sub = Offer.objects.create(name='Code en ligne mensuel', category='CODE', hours=0, price=15, includes_lms=True, billing_type='MONTHLY', billing_interval_months=1)

    def auth(self, username):
        r = self.client.post('/api/auth/token/', {'username': username, 'password': 'pass12345'})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def test_public_offer_exposes_engine_fields(self):
        d = {o['name']: o for o in self.client.get('/api/offers/').data}
        self.assertEqual(d['Permis B 20 h']['installments'], 3)
        self.assertTrue(d['Permis B 20 h']['includes_exams'])
        self.assertTrue(d['Option 5 h perfectionnement']['is_addon'])
        self.assertTrue(d['Option 5 h perfectionnement']['lets_student_pick_skills'])
        self.assertEqual(len(d['Option 5 h perfectionnement']['skill_labels']), 2)

    def test_student_configures_bundle_with_options_and_skills(self):
        self.auth('eleve@test.fr')
        codes = list(self.perf.skills.values_list('code', flat=True))
        r = self.client.post('/api/packages/', {'offer': self.base.id, 'addons': [self.perf.id, self.exams.id], 'skills': codes[:1]}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data['bundle_total'], '1469.00')
        self.assertEqual(len(r.data['addon_items']), 2)
        self.assertEqual(r.data['requested_skills'], codes[:1])
        self.assertEqual(Package.objects.filter(parent__isnull=False).count(), 2)
        # liste élève : la formule regroupe ses options, pas de doublon
        lst = self.client.get('/api/packages/').data
        items = lst['results'] if isinstance(lst, dict) else lst
        self.assertEqual(len(items), 1)
        # compétence hors liste refusée ; compétences sur une offre qui ne le permet pas refusées
        self.assertEqual(self.client.post('/api/packages/', {'offer': self.base.id, 'addons': [self.perf.id], 'skills': ['ZZZ']}, format='json').status_code, 400)
        self.assertEqual(self.client.post('/api/packages/', {'offer': self.exams.id, 'skills': codes[:1]}, format='json').status_code, 400)
        # paiement en ligne non configuré → message clair, rien ne casse
        r = self.client.post(f"/api/packages/{r.data['id']}/checkout/")
        self.assertEqual(r.status_code, 400)
        self.assertIn('école', r.data['detail'])

    def test_manual_validation_credits_whole_bundle(self):
        self.auth('eleve@test.fr')
        pid = self.client.post('/api/packages/', {'offer': self.base.id, 'addons': [self.perf.id]}, format='json').data['id']
        self.auth('o@kaho.app')
        self.client.post(f'/api/admin/packages/{pid}/mark_paid/', {'method': 'TRANSFER'})
        for a in Package.objects.get(pk=pid).addons.all():
            self.client.post(f'/api/admin/packages/{a.id}/mark_paid/', {'method': 'TRANSFER'})
        self.student.refresh_from_db()
        self.assertEqual(self.student.purchased_hours, 25)
        self.assertTrue(self.student.has_lms_access)

    @override_settings(STRIPE_SECRET_KEY='sk_test_x', STRIPE_WEBHOOK_SECRET='whsec_x')
    def test_webhook_installments_and_subscription_renewal(self):
        from .payments import handle_webhook
        self.auth('eleve@test.fr')
        pid = self.client.post('/api/packages/', {'offer': self.base.id, 'addons': [self.exams.id]}, format='json').data['id']
        ids = ','.join(str(p.id) for p in Package.objects.get(pk=pid).bundle)
        session = {'id': 'cs_1', 'payment_status': 'paid', 'subscription': 'sub_1', 'payment_intent': None, 'metadata': {'package_id': str(pid), 'package_ids': ids}}
        with mock.patch('stripe.Webhook.construct_event', return_value={'type': 'checkout.session.completed', 'data': {'object': session}}):
            ok, msg = handle_webhook(b'{}', 'sig')
        self.assertTrue(ok, msg)
        base = Package.objects.get(pk=pid)
        self.assertEqual(base.status, 'COMPLETED')
        self.assertEqual(base.installments_paid, 1)
        self.assertEqual(base.stripe_subscription_id, 'sub_1')
        self.assertTrue(all(a.status == 'COMPLETED' for a in base.addons.all()))
        self.student.refresh_from_db()
        self.assertEqual(self.student.purchased_hours, 20)
        # 2e et 3e échéances : à la dernière, l'échéancier est arrêté
        invoice = {'subscription': 'sub_1', 'billing_reason': 'subscription_cycle'}
        with mock.patch('stripe.Webhook.construct_event', return_value={'type': 'invoice.paid', 'data': {'object': invoice}}), mock.patch('stripe.Subscription.cancel') as cancel:
            handle_webhook(b'{}', 'sig')
            self.assertFalse(cancel.called)
            handle_webhook(b'{}', 'sig')
            self.assertTrue(cancel.called)
        self.assertEqual(Package.objects.get(pk=pid).installments_paid, 3)
        # abonnement mensuel : chaque renouvellement prolonge l'accès code
        sid = self.client.post('/api/packages/', {'offer': self.sub.id}, format='json').data['id']
        session = {'id': 'cs_2', 'payment_status': 'paid', 'subscription': 'sub_2', 'payment_intent': None, 'metadata': {'package_id': str(sid), 'package_ids': str(sid)}}
        with mock.patch('stripe.Webhook.construct_event', return_value={'type': 'checkout.session.completed', 'data': {'object': session}}):
            handle_webhook(b'{}', 'sig')
        until1 = StudentProfile.objects.get(pk=self.student.pk).lms_access_until
        self.assertIsNotNone(until1)
        with mock.patch('stripe.Webhook.construct_event', return_value={'type': 'invoice.paid', 'data': {'object': {'subscription': 'sub_2', 'billing_reason': 'subscription_cycle'}}}):
            handle_webhook(b'{}', 'sig')
        until2 = StudentProfile.objects.get(pk=self.student.pk).lms_access_until
        self.assertGreater(until2, until1)

    def test_assr2_optional_document_and_multi_upload(self):
        self.auth('eleve@test.fr')
        for t in ('IDENTITY', 'ASSR2', 'JDC'):
            r = self.client.post('/api/documents/', {'document_type': t, 'file': SimpleUploadedFile(f'{t}.pdf', b'%PDF-1.4 x', content_type='application/pdf')}, format='multipart')
            self.assertEqual(r.status_code, 201, r.content)
        d = self.client.get('/api/documents/my_dossier/').data
        self.assertEqual(len(d['documents']), 3)
        self.assertEqual(d['dossier']['missing'], 4)  # ASSR2 et JDC ne comptent pas comme manquants
        self.assertEqual(d['dossier']['pending'], 3)
        doc_id = d['documents'][0]['id']
        self.assertEqual(self.client.delete(f'/api/documents/{doc_id}/').status_code, 204)

    def test_question_media_and_upload(self):
        from lms.models import Question
        q = Question.objects.create(kind='TRUE_FALSE', text_md='x', topic='L', in_exam_bank=True, image_url='https://img/x.png', video_url='https://youtu.be/abc123xyz')
        pub = q.public()
        self.assertEqual(pub['video_embed'], 'https://www.youtube-nocookie.com/embed/abc123xyz?rel=0')
        self.assertEqual(pub['image_url'], 'https://img/x.png')
        self.auth('o@kaho.app')
        r = self.client.post('/api/lms/admin/upload/', {'file': SimpleUploadedFile('schema.png', b'\x89PNG x', content_type='image/png')}, format='multipart')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data['kind'], 'image')
        self.assertIn('/media/lms/', r.data['url'])
        self.assertEqual(self.client.post('/api/lms/admin/upload/', {'file': SimpleUploadedFile('x.exe', b'x')}, format='multipart').status_code, 400)
        r = self.client.patch(f'/api/lms/admin/questions/{q.id}/', {'image_url': r.data['url'], 'video_url': 'https://vimeo.com/123'}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertIn('/media/lms/', r.data['image_url'])


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class LoginAndAdminInstructorTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='gerant@kaho.app', email='gerant@kaho.app', password='pass12345', first_name='Gé', last_name='Rant', role='OWNER')

    def test_login_is_case_insensitive_with_french_error(self):
        r = self.client.post('/api/auth/token/', {'username': 'Gerant@KAHO.app ', 'password': 'pass12345'})
        self.assertEqual(r.status_code, 200, r.content)
        r = self.client.post('/api/auth/token/', {'username': 'gerant@kaho.app', 'password': 'faux'})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.data['detail'], 'Email ou mot de passe incorrect.')
        # inscription avec majuscules → compte en minuscules, connexion possible dans les deux sens
        r = self.client.post('/api/auth/register/', {'email': 'Nouvel.Eleve@Test.FR', 'password': 'motdepasse1', 'first_name': 'N', 'last_name': 'E'})
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(self.client.post('/api/auth/token/', {'username': 'NOUVEL.ELEVE@test.fr', 'password': 'motdepasse1'}).status_code, 200)

    def test_owner_can_also_teach(self):
        r = self.client.post('/api/auth/token/', {'username': 'gerant@kaho.app', 'password': 'pass12345'})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
        # sans le drapeau : pas d'espace moniteur
        self.assertEqual(self.client.get('/api/instructors/dashboard/').status_code, 403)
        self.assertFalse(self.client.get('/api/users/me/').data['teaches'])
        r = self.client.patch(f'/api/admin/team/{self.owner.id}/', {'also_instructor': True}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(r.data['also_instructor'])
        me = self.client.get('/api/users/me/').data
        self.assertTrue(me['teaches'])
        self.assertEqual(me['role'], 'OWNER')  # reste gérant
        self.assertEqual(self.client.get('/api/instructors/dashboard/').status_code, 200)
        self.assertEqual(self.client.post('/api/availabilities/', {'weekday': 0, 'start_time': '09:00', 'end_time': '12:00'}).status_code, 201)
        # apparaît comme moniteur (liste admin, réservation élève)
        self.assertIn(self.owner.id, [i['id'] for i in self.client.get('/api/admin/instructors/').data['results']])
        pub = self.client.get('/api/instructors/').data
        self.assertIn(self.owner.id, [i['id'] for i in (pub['results'] if isinstance(pub, dict) else pub)])
        self.assertEqual(self.client.get('/api/admin/sales/').status_code, 200)  # droits gérant conservés
