from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone, translation
from django.utils.formats import date_format
import html as html_lib

from django.utils.html import escape, strip_tags


def _fr_date(d):
    with translation.override('fr'):
        return date_format(d, 'l j F Y')


def _send_email(to_email, subject, html):
    """Envoi via le backend Django configuré (Brevo SMTP en prod, console en dev)."""
    try:
        # Version texte : strip_tags laisse les entités (&amp;) que l'on décode ensuite — les URLs restent intactes
        import re
        text = html_lib.unescape(strip_tags(re.sub(r'</(li|p|h2|div)>|<br\s*/?>', '\n', html)))
        text = re.sub(r'[ \t]+\n', '\n', re.sub(r'\n{3,}', '\n\n', text)).strip()
        msg = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, [to_email])
        msg.attach_alternative(html, 'text/html')
        msg.send()
    except Exception as e:  # ne jamais faire échouer l'action métier à cause d'un email
        print(f"[email] échec d'envoi à {to_email}: {e}")


def _normalize_phone(phone):
    """06 12 34 56 78 → 33612345678 (format attendu par Brevo)."""
    digits = ''.join(ch for ch in (phone or '') if ch.isdigit())
    if digits.startswith('00'):
        digits = digits[2:]
    elif digits.startswith('0') and len(digits) == 10:
        digits = '33' + digits[1:]
    return digits or None


def _send_sms(phone, body):
    recipient = _normalize_phone(phone)
    if not settings.BREVO_API_KEY or not recipient:
        return
    try:
        import requests
        r = requests.post(
            'https://api.brevo.com/v3/transactionalSMS/sms',
            headers={'api-key': settings.BREVO_API_KEY, 'accept': 'application/json'},
            json={'type': 'transactional', 'sender': settings.BREVO_SMS_SENDER, 'recipient': recipient, 'content': body},
            timeout=10,
        )
        if r.status_code >= 400:
            print(f"[sms] Brevo a refusé l'envoi à {recipient}: {r.status_code} {r.text}")
    except Exception as e:
        print(f"[sms] échec d'envoi à {recipient}: {e}")


def _layout(title, body_html):
    return f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:560px;margin:0 auto;color:#2B1D14">
      <div style="background:#5C3D2E;color:#FBF8F3;padding:16px 24px;border-radius:12px 12px 0 0;font-size:20px;font-weight:600">Kaho</div>
      <div style="background:#FBF8F3;padding:24px;border:1px solid #EAE0D2;border-top:0;border-radius:0 0 12px 12px">
        <h2 style="margin-top:0;color:#5C3D2E">{title}</h2>
        {body_html}
        <p style="color:#8B5E3C;font-size:13px;margin-top:24px">Kaho — auto-école &amp; centre de formation</p>
      </div>
    </div>"""


@shared_task
def send_password_reset_email(email, link):
    link = escape(link)
    _send_email(
        email,
        'Réinitialisation de votre mot de passe — Kaho',
        _layout('Nouveau mot de passe', f"""
        <p>Bonjour,</p>
        <p>Pour choisir un nouveau mot de passe, cliquez sur ce lien (valable 1 heure) :</p>
        <p><a href="{link}" style="display:inline-block;background:#5C3D2E;color:#FBF8F3;padding:10px 18px;border-radius:999px;text-decoration:none">Choisir un nouveau mot de passe</a></p>
        <p style="font-size:13px;color:#8B5E3C">Ou copiez ce lien : {link}</p>
        <p>Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.</p>"""),
    )


@shared_task
def send_instructor_invite(email, first_name, link):
    link = escape(link)
    _send_email(
        email,
        'Bienvenue dans l’équipe Kaho — créez votre mot de passe',
        _layout(f'Bienvenue, {first_name} !', f"""
        <p>Votre compte moniteur Kaho est prêt. Il ne reste qu'à choisir votre mot de passe (lien valable 72 h) :</p>
        <p><a href="{link}" style="display:inline-block;background:#5C3D2E;color:#FBF8F3;padding:10px 18px;border-radius:999px;text-decoration:none">Créer mon mot de passe</a></p>
        <p style="font-size:13px;color:#8B5E3C">Ou copiez ce lien : {link}</p>
        <p>Ensuite, renseignez vos disponibilités depuis votre espace pour que les élèves puissent réserver avec vous.</p>"""),
    )


@shared_task
def send_application_received(email, first_name):
    _send_email(
        email,
        'Candidature reçue — Kaho',
        _layout('Merci pour votre candidature', f"""
        <p>Bonjour {first_name},</p>
        <p>Nous avons bien reçu votre candidature et vos pièces justificatives. Nous revenons vers vous rapidement après examen.</p>"""),
    )


@shared_task
def send_application_rejected(email, first_name, note):
    _send_email(
        email,
        'Votre candidature — Kaho',
        _layout('Candidature non retenue', f"""
        <p>Bonjour {first_name},</p>
        <p>Après examen, nous ne pouvons pas donner suite à votre candidature pour le moment.</p>
        {f'<p>{note}</p>' if note else ''}
        <p>Merci de l'intérêt que vous portez à Kaho.</p>"""),
    )


@shared_task
def send_booking_confirmation(slot_id):
    from .models import Slot
    try:
        slot = Slot.objects.select_related('student__user', 'instructor', 'meeting_point').get(pk=slot_id)
    except Slot.DoesNotExist:
        return
    if not slot.student:
        return
    _send_email(
        slot.student.user.email,
        f"Leçon confirmée le {slot.date:%d/%m/%Y} à {slot.start_time:%H:%M}",
        _layout('Votre leçon est confirmée', f"""
        <p>Bonjour {slot.student.user.first_name},</p>
        <ul>
          <li><strong>Date :</strong> {_fr_date(slot.date)}</li>
          <li><strong>Heure :</strong> {slot.start_time:%H:%M} – {slot.end_time:%H:%M}</li>
          <li><strong>Moniteur :</strong> {slot.instructor.get_full_name()}</li>
          <li><strong>Lieu :</strong> {slot.meeting_point.name} — {slot.meeting_point.address}</li>
        </ul>
        <p>Annulation gratuite jusqu'à {settings.BOOKING_CANCEL_DEADLINE_HOURS} h avant, depuis votre espace.</p>"""),
    )


@shared_task
def send_document_reviewed(document_id):
    from .models import Document
    try:
        doc = Document.objects.select_related('student__user').get(pk=document_id)
    except Document.DoesNotExist:
        return
    user = doc.student.user
    if doc.status == 'VERIFIED':
        dossier = Document.dossier(doc.student)
        extra = "<p><strong>Votre dossier est maintenant complet.</strong></p>" if dossier['complete'] else f"<p>Il reste {dossier['missing'] + dossier['pending']} pièce(s) à fournir ou en attente de vérification.</p>"
        _send_email(user.email, f"Pièce validée : {doc.get_document_type_display()} — Kaho",
                    _layout('Pièce validée', f"<p>Bonjour {user.first_name},</p><p>Votre <strong>{doc.get_document_type_display().lower()}</strong> a été vérifiée et validée.</p>{extra}"))
    elif doc.status == 'REJECTED':
        _send_email(user.email, f"Pièce à redéposer : {doc.get_document_type_display()} — Kaho",
                    _layout('Pièce refusée', f"""<p>Bonjour {user.first_name},</p>
                    <p>Votre <strong>{doc.get_document_type_display().lower()}</strong> n'a pas pu être validée :</p>
                    <p style="border-left:3px solid #C8A97E;padding-left:12px">{escape(doc.review_note)}</p>
                    <p>Merci de déposer une nouvelle version depuis votre espace, rubrique Documents.</p>"""))


@shared_task
def send_booking_changed(slot_id, old_label):
    from .models import Slot
    try:
        slot = Slot.objects.select_related('student__user', 'instructor', 'meeting_point').get(pk=slot_id)
    except Slot.DoesNotExist:
        return
    if not slot.student:
        return
    _send_email(
        slot.student.user.email,
        f"Votre leçon a été déplacée — {slot.date:%d/%m/%Y} à {slot.start_time:%H:%M}",
        _layout('Changement de leçon', f"""
        <p>Bonjour {slot.student.user.first_name},</p>
        <p>Votre leçon initialement prévue <strong>{old_label}</strong> a été modifiée :</p>
        <ul>
          <li><strong>Nouvelle date :</strong> {_fr_date(slot.date)}</li>
          <li><strong>Heure :</strong> {slot.start_time:%H:%M} – {slot.end_time:%H:%M}</li>
          <li><strong>Moniteur :</strong> {slot.instructor.get_full_name()}</li>
          <li><strong>Lieu :</strong> {slot.meeting_point.name} — {slot.meeting_point.address}</li>
        </ul>
        <p>En cas d'empêchement, annulez depuis votre espace ou contactez-nous.</p>"""),
    )
    _send_sms(slot.student.phone, f"Kaho : votre leçon est déplacée au {slot.date:%d/%m} à {slot.start_time:%H:%M} avec {slot.instructor.first_name}.")


@shared_task
def send_lesson_reminders():
    """Rappel email (+ SMS si configuré) la veille de chaque leçon. Déclenché par Celery beat ou par le cron HTTP."""
    from .models import Slot, log_activity
    tomorrow = timezone.localdate() + timedelta(days=1)
    slots = Slot.objects.filter(date=tomorrow, status='BOOKED', student__isnull=False).select_related('student__user', 'instructor', 'meeting_point')
    sent = 0
    for slot in slots:
        sent += 1
        user = slot.student.user
        _send_email(
            user.email,
            f"Rappel : leçon demain à {slot.start_time:%H:%M}",
            _layout('À demain !', f"""
            <p>Bonjour {user.first_name},</p>
            <p>Petit rappel de votre leçon de conduite :</p>
            <ul>
              <li><strong>Date :</strong> {_fr_date(slot.date)}</li>
              <li><strong>Heure :</strong> {slot.start_time:%H:%M} – {slot.end_time:%H:%M}</li>
              <li><strong>Moniteur :</strong> {slot.instructor.get_full_name()}</li>
              <li><strong>Lieu :</strong> {slot.meeting_point.name} — {slot.meeting_point.address}</li>
            </ul>
            <p>Merci d'arriver 5 minutes avant l'heure.</p>"""),
        )
        _send_sms(slot.student.phone, f"Kaho : rappel de votre leçon demain à {slot.start_time:%H:%M} avec {slot.instructor.first_name}, RDV {slot.meeting_point.name}.")
    log_activity('REMINDERS', f"Rappels envoyés pour le {tomorrow:%d/%m/%Y} : {sent} leçon(s)")
    return sent


@shared_task
def send_payment_confirmation(package_id):
    from .models import Package
    try:
        package = Package.objects.select_related('student__user', 'offer').get(id=package_id)
    except Package.DoesNotExist:
        return
    content = []
    if package.hours_purchased:
        content.append(f"<li><strong>Heures de conduite :</strong> {package.hours_purchased:g} h</li>")
    if package.offer and package.offer.includes_lms:
        content.append("<li><strong>Accès :</strong> cours de code, quiz et examens blancs</li>")
    if package.expires_at:
        content.append(f"<li><strong>Valable jusqu'au :</strong> {_fr_date(package.expires_at)}</li>")
    _send_email(
        package.student.user.email,
        'Votre paiement est validé — Kaho',
        _layout('Paiement validé', f"""
        <p>Bonjour {package.student.user.first_name},</p>
        <p>Votre souscription « {package.offer.name if package.offer else 'heures'} » est active :</p>
        <ul>{''.join(content)}<li><strong>Montant :</strong> {package.amount_paid} €</li></ul>
        <p>Vous pouvez dès maintenant réserver vos leçons depuis votre espace.</p>"""),
    )
