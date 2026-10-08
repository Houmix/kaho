from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client
from decouple import config
from .models import Slot, StudentProfile

@shared_task
def send_lesson_reminders():
    """Envoyer des rappels email/SMS 24h avant chaque leçon"""
    tomorrow = timezone.now().date() + timedelta(days=1)
    slots = Slot.objects.filter(date=tomorrow, status='BOOKED', student__isnull=False)

    sendgrid_api_key = config('SENDGRID_API_KEY', default='')
    twilio_sid = config('TWILIO_ACCOUNT_SID', default='')
    twilio_token = config('TWILIO_AUTH_TOKEN', default='')
    twilio_phone = config('TWILIO_PHONE_NUMBER', default='')

    for slot in slots:
        if slot.student and slot.student.user.email:
            # Email reminder
            if sendgrid_api_key:
                send_email_reminder.delay(
                    email=slot.student.user.email,
                    student_name=slot.student.user.get_full_name(),
                    slot_date=str(slot.date),
                    slot_time=str(slot.start_time),
                    meeting_point=slot.meeting_point.name
                )

            # SMS reminder
            if twilio_sid and twilio_token and twilio_phone and slot.student.emergency_phone:
                send_sms_reminder.delay(
                    phone=slot.student.emergency_phone,
                    student_name=slot.student.user.get_full_name(),
                    slot_date=str(slot.date),
                    slot_time=str(slot.start_time)
                )


@shared_task
def send_email_reminder(email, student_name, slot_date, slot_time, meeting_point):
    """Envoyer email de rappel via SendGrid"""
    sendgrid_api_key = config('SENDGRID_API_KEY', default='')
    sender_email = config('DEFAULT_FROM_EMAIL', default='noreply@kaho.app')

    if not sendgrid_api_key:
        return

    try:
        message = Mail(
            from_email=sender_email,
            to_emails=email,
            subject=f'Rappel: Votre leçon de conduite demain à {slot_time}',
            html_content=f"""
            <h2>Rappel de votre leçon de conduite</h2>
            <p>Bonjour {student_name},</p>
            <p>Ceci est un rappel de votre leçon de conduite prévue pour:</p>
            <ul>
                <li><strong>Date:</strong> {slot_date}</li>
                <li><strong>Heure:</strong> {slot_time}</li>
                <li><strong>Lieu:</strong> {meeting_point}</li>
            </ul>
            <p>Merci de vous présenter 5 minutes avant l'heure prévue.</p>
            <p>Cordialement,<br>Kaho - Votre monitrice d'auto-école</p>
            """
        )
        sg = SendGridAPIClient(sendgrid_api_key)
        sg.send(message)
    except Exception as e:
        print(f"Error sending email reminder: {e}")


@shared_task
def send_sms_reminder(phone, student_name, slot_date, slot_time):
    """Envoyer SMS de rappel via Twilio"""
    twilio_sid = config('TWILIO_ACCOUNT_SID', default='')
    twilio_token = config('TWILIO_AUTH_TOKEN', default='')
    twilio_phone = config('TWILIO_PHONE_NUMBER', default='')

    if not all([twilio_sid, twilio_token, twilio_phone]):
        return

    try:
        client = Client(twilio_sid, twilio_token)
        message = client.messages.create(
            body=f"Rappel: Votre leçon de conduite {slot_date} à {slot_time}. À bientôt!",
            from_=twilio_phone,
            to=phone
        )
    except Exception as e:
        print(f"Error sending SMS reminder: {e}")


def _fr_date(d):
    from django.utils import translation
    from django.utils.formats import date_format
    with translation.override('fr'):
        return date_format(d, 'l j F Y')


def _send_email(to_email, subject, html):
    """Envoi via SendGrid ; sans clé API, affiche le mail en console (dev)."""
    api_key = config('SENDGRID_API_KEY', default='')
    sender = config('DEFAULT_FROM_EMAIL', default='noreply@kaho.app')
    if not api_key:
        print(f"[email non envoyé — SENDGRID_API_KEY absente] to={to_email} subject={subject}\n{html}")
        return
    try:
        SendGridAPIClient(api_key).send(Mail(from_email=sender, to_emails=to_email, subject=subject, html_content=html))
    except Exception as e:
        print(f"Error sending email: {e}")


@shared_task
def send_password_reset_email(email, link):
    _send_email(
        email,
        'Réinitialisation de votre mot de passe — Kaho',
        f"""<p>Bonjour,</p>
        <p>Pour choisir un nouveau mot de passe, cliquez sur ce lien (valable 1 heure) :</p>
        <p><a href="{link}">{link}</a></p>
        <p>Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.</p>""",
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
        f"""<p>Bonjour {slot.student.user.first_name},</p>
        <p>Votre leçon est confirmée :</p>
        <ul>
          <li><strong>Date :</strong> {_fr_date(slot.date)}</li>
          <li><strong>Heure :</strong> {slot.start_time:%H:%M} – {slot.end_time:%H:%M}</li>
          <li><strong>Moniteur :</strong> {slot.instructor.get_full_name()}</li>
          <li><strong>Lieu :</strong> {slot.meeting_point.name} — {slot.meeting_point.address}</li>
        </ul>
        <p>Annulation possible jusqu'à 48 h avant depuis votre espace.</p>""",
    )


@shared_task
def sync_student_hours():
    """Synchroniser les heures utilisées et achhetées"""
    profiles = StudentProfile.objects.all()
    for profile in profiles:
        profile.save()


@shared_task
def send_payment_confirmation(package_id):
    """Envoyer confirmation de paiement"""
    from .models import Package

    try:
        package = Package.objects.get(id=package_id)
        sendgrid_api_key = config('SENDGRID_API_KEY', default='')
        sender_email = config('DEFAULT_FROM_EMAIL', default='noreply@kaho.app')

        if not sendgrid_api_key:
            return

        message = Mail(
            from_email=sender_email,
            to_emails=package.student.user.email,
            subject='Confirmation de paiement - Kaho',
            html_content=f"""
            <h2>Confirmation de votre achat</h2>
            <p>Bonjour {package.student.user.get_full_name()},</p>
            <p>Votre achat a été validé avec succès:</p>
            <ul>
                <li><strong>Heures achetées:</strong> {package.hours_purchased}h</li>
                <li><strong>Montant:</strong> {package.amount_paid}€</li>
                <li><strong>Référence:</strong> {package.stripe_payment_id}</li>
            </ul>
            <p>Vous pouvez dès maintenant réserver vos leçons de conduite.</p>
            <p>Cordialement,<br>Kaho</p>
            """
        )
        sg = SendGridAPIClient(sendgrid_api_key)
        sg.send(message)
    except Exception as e:
        print(f"Error sending payment confirmation: {e}")
