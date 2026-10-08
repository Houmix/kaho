from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone, translation
from django.utils.formats import date_format
from django.utils.html import strip_tags


def _fr_date(d):
    with translation.override('fr'):
        return date_format(d, 'l j F Y')


def _send_email(to_email, subject, html):
    """Envoi via le backend Django configuré (Brevo SMTP en prod, console en dev)."""
    try:
        msg = EmailMultiAlternatives(subject, strip_tags(html), settings.DEFAULT_FROM_EMAIL, [to_email])
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
def send_lesson_reminders():
    """Rappel email (+ SMS si configuré) la veille de chaque leçon. Lancé par Celery beat chaque matin."""
    from .models import Slot
    tomorrow = timezone.localdate() + timedelta(days=1)
    for slot in Slot.objects.filter(date=tomorrow, status='BOOKED', student__isnull=False).select_related('student__user', 'instructor', 'meeting_point'):
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
