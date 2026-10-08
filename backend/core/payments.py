"""Liens de paiement Stripe Checkout + webhook. Sans STRIPE_SECRET_KEY, les liens ne sont pas disponibles."""
from django.conf import settings
from django.utils import timezone

from .models import Package, log_activity


class StripeNotConfigured(Exception):
    pass


def _client():
    if not settings.STRIPE_SECRET_KEY:
        raise StripeNotConfigured("Stripe n'est pas configuré : renseignez STRIPE_SECRET_KEY (et STRIPE_WEBHOOK_SECRET) sur le serveur.")
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def create_checkout_link(package: Package) -> str:
    """Crée une session Stripe Checkout pour un achat en attente et mémorise son URL."""
    stripe = _client()
    user = package.student.user
    session = stripe.checkout.Session.create(
        mode='payment',
        customer_email=user.email,
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'unit_amount': int(round(float(package.amount_paid) * 100)),
                'product_data': {'name': package.display_label, 'description': f"{settings.COMPANY_NAME} — {user.get_full_name()}"},
            },
            'quantity': 1,
        }],
        metadata={'package_id': str(package.id), 'student_id': str(package.student_id)},
        client_reference_id=str(package.id),
        success_url=f"{settings.FRONTEND_URL}/student/purchases?paid=1&package={package.id}",
        cancel_url=f"{settings.FRONTEND_URL}/student/purchases?cancelled=1",
        expires_at=int((timezone.now() + timezone.timedelta(hours=24)).timestamp()),
    )
    package.stripe_session_id = session.id
    package.stripe_checkout_url = session.url
    package.save(update_fields=['stripe_session_id', 'stripe_checkout_url', 'updated_at'])
    return session.url


def handle_webhook(payload: bytes, signature: str):
    """Valide la signature et marque l'achat payé sur `checkout.session.completed`. Retourne (ok, message)."""
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_WEBHOOK_SECRET:
        return False, 'Stripe non configuré.'
    import stripe
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as e:  # signature invalide, payload corrompu
        return False, f'Signature invalide : {e}'
    if event['type'] not in ('checkout.session.completed', 'checkout.session.async_payment_succeeded'):
        return True, 'ignoré'
    session = event['data']['object']
    if session.get('payment_status') not in ('paid', None) and event['type'] == 'checkout.session.completed':
        return True, 'paiement non confirmé'
    package_id = (session.get('metadata') or {}).get('package_id') or session.get('client_reference_id')
    pkg = Package.objects.filter(pk=package_id).select_related('student__user').first() if package_id else None
    if pkg is None:
        return True, 'achat inconnu'
    if pkg.status == 'COMPLETED':
        return True, 'déjà validé'
    pkg.status = 'COMPLETED'
    pkg.payment_method = 'STRIPE'
    pkg.stripe_payment_id = session.get('payment_intent') or session.get('id')
    pkg.note = ((pkg.note + '\n') if pkg.note else '') + f"Payé en ligne (Stripe) le {timezone.localdate():%d/%m/%Y}"
    pkg.save()
    return True, f'achat #{pkg.id} validé'
