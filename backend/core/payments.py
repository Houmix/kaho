"""Stripe Checkout : paiement unique, abonnement récurrent (tous les N mois) ou paiement en plusieurs fois, + webhook.
Sans STRIPE_SECRET_KEY, les liens ne sont pas disponibles (règlement manuel à l'école)."""
from decimal import Decimal, ROUND_HALF_UP

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


def _cents(amount):
    return int((Decimal(amount) * 100).quantize(Decimal('1'), ROUND_HALF_UP))


def create_checkout_link(package: Package) -> str:
    """Session Checkout pour une formule (+ ses options). Le mode dépend de la facturation de la formule de base :
    - paiement unique : toutes les lignes en une fois ;
    - abonnement : prélèvement récurrent tous les N mois ;
    - en 3 / 4 fois : prélèvement mensuel du tiers / quart, arrêté automatiquement après la dernière échéance."""
    stripe = _client()
    base = package.parent or package
    items = base.bundle
    user = base.student.user
    offer = base.offer
    total = sum((p.amount_paid for p in items), Decimal('0'))
    common = dict(
        customer_email=user.email,
        metadata={'package_id': str(base.id), 'package_ids': ','.join(str(p.id) for p in items), 'student_id': str(base.student_id)},
        client_reference_id=str(base.id),
        success_url=f"{settings.FRONTEND_URL}/student/purchases?paid=1&package={base.id}",
        cancel_url=f"{settings.FRONTEND_URL}/student/purchases?cancelled=1",
    )
    label = ' + '.join(p.display_label for p in items)
    if offer and offer.is_recurring:
        session = stripe.checkout.Session.create(mode='subscription', **common, line_items=[{
            'price_data': {'currency': 'eur', 'unit_amount': _cents(total), 'recurring': {'interval': 'month', 'interval_count': offer.billing_interval_months or 1},
                           'product_data': {'name': label, 'description': f"{settings.COMPANY_NAME} — abonnement"}}, 'quantity': 1}],
            subscription_data={'metadata': {'package_id': str(base.id), 'kind': 'recurring'}})
    elif offer and offer.installments > 1:
        n = offer.installments
        part = (total / n).quantize(Decimal('0.01'), ROUND_HALF_UP)
        session = stripe.checkout.Session.create(mode='subscription', **common, line_items=[{
            'price_data': {'currency': 'eur', 'unit_amount': _cents(part), 'recurring': {'interval': 'month'},
                           'product_data': {'name': f"{label} — {n} × {part} €", 'description': f"{settings.COMPANY_NAME} — paiement en {n} fois sans frais"}}, 'quantity': 1}],
            subscription_data={'metadata': {'package_id': str(base.id), 'kind': 'installments', 'installments': str(n)}})
    else:
        session = stripe.checkout.Session.create(mode='payment', **common, line_items=[{
            'price_data': {'currency': 'eur', 'unit_amount': _cents(p.amount_paid), 'product_data': {'name': p.display_label, 'description': f"{settings.COMPANY_NAME} — {user.get_full_name()}"}}, 'quantity': 1}
            for p in items if p.amount_paid > 0],
            expires_at=int((timezone.now() + timezone.timedelta(hours=24)).timestamp()))
    for p in items:
        p.stripe_session_id, p.stripe_checkout_url = session.id, session.url
        p.save(update_fields=['stripe_session_id', 'stripe_checkout_url', 'updated_at'])
    return session.url


def _complete(pkg, method='STRIPE', ref='', note=''):
    if pkg.status == 'COMPLETED':
        return
    pkg.status, pkg.payment_method = 'COMPLETED', method
    if ref and not pkg.stripe_payment_id:
        pkg.stripe_payment_id = ref if pkg.parent_id is None else f"{ref}:{pkg.id}"
    pkg.note = ((pkg.note + '\n') if pkg.note else '') + (note or f"Payé en ligne (Stripe) le {timezone.localdate():%d/%m/%Y}")
    pkg.save()


def handle_webhook(payload: bytes, signature: str):
    """Valide la signature et traite : checkout.session.completed (1er paiement), invoice.paid (échéances / renouvellements)."""
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_WEBHOOK_SECRET:
        return False, 'Stripe non configuré.'
    import stripe
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return False, f'Signature invalide : {e}'
    obj = event['data']['object']
    if event['type'] in ('checkout.session.completed', 'checkout.session.async_payment_succeeded'):
        if event['type'] == 'checkout.session.completed' and obj.get('payment_status') not in ('paid', None):
            return True, 'paiement non confirmé'
        meta = obj.get('metadata') or {}
        ids = [int(i) for i in (meta.get('package_ids') or meta.get('package_id') or obj.get('client_reference_id') or '').split(',') if str(i).isdigit()]
        packages = list(Package.objects.filter(pk__in=ids).select_related('student__user', 'offer'))
        if not packages:
            return True, 'achat inconnu'
        sub = obj.get('subscription')
        for p in packages:
            if sub:
                p.stripe_subscription_id, p.installments_paid = sub, 1
            _complete(p, ref=obj.get('payment_intent') or obj.get('id'))
        return True, f"{len(packages)} achat(s) validé(s)"
    if event['type'] == 'invoice.paid':
        sub = obj.get('subscription')
        if not sub or obj.get('billing_reason') == 'subscription_create':
            return True, 'première échéance (déjà traitée au checkout)'
        packages = list(Package.objects.filter(stripe_subscription_id=sub).select_related('student', 'offer'))
        if not packages:
            return True, 'abonnement inconnu'
        base = next((p for p in packages if p.parent_id is None), packages[0])
        offer = base.offer
        for p in packages:
            p.installments_paid += 1
            p.save(update_fields=['installments_paid', 'updated_at'])
        if offer and offer.installments > 1:
            if base.installments_paid >= offer.installments:
                try:
                    stripe.Subscription.cancel(sub)
                except Exception as e:
                    print(f"[stripe] annulation de l'échéancier impossible : {e}")
            log_activity('PAYMENT', f"{base.student.user.get_full_name()} — échéance {base.installments_paid}/{offer.installments} réglée ({base.display_label})", student=base.student)
        elif offer and offer.is_recurring:
            base.extend_period(offer.billing_interval_months or 1)
            log_activity('PAYMENT', f"{base.student.user.get_full_name()} — abonnement renouvelé ({base.display_label}), accès prolongé", student=base.student)
        return True, 'échéance enregistrée'
    return True, 'ignoré'
