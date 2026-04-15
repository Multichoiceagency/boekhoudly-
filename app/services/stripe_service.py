"""Stripe billing service — wraps the Stripe SDK with FiscaalFlow specifics."""
import logging
from typing import Optional
import stripe
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


def is_configured() -> bool:
    return bool(settings.STRIPE_SECRET_KEY)


def get_or_create_customer(*, email: str, name: str, company_id: str, metadata: Optional[dict] = None) -> stripe.Customer:
    """Find a Stripe customer by company_id metadata or create a new one."""
    if not is_configured():
        raise RuntimeError("Stripe is not configured (STRIPE_SECRET_KEY missing)")

    existing = stripe.Customer.search(query=f"metadata['company_id']:'{company_id}'", limit=1)
    if existing.data:
        return existing.data[0]

    return stripe.Customer.create(
        email=email,
        name=name,
        metadata={"company_id": company_id, "platform": "fiscaalflow", **(metadata or {})},
    )


def create_checkout_session(*, customer_id: str, price_id: str, success_url: str, cancel_url: str, company_id: str, plan_slug: str) -> stripe.checkout.Session:
    """Create a Stripe Checkout Session for a subscription."""
    return stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"company_id": company_id, "plan_slug": plan_slug},
        subscription_data={
            "metadata": {"company_id": company_id, "plan_slug": plan_slug, "platform": "fiscaalflow"},
        },
        allow_promotion_codes=True,
        billing_address_collection="required",
        locale="nl",
    )


def create_portal_session(*, customer_id: str, return_url: str) -> stripe.billing_portal.Session:
    """Create a Stripe Customer Portal session for managing subscription/payment methods."""
    return stripe.billing_portal.Session.create(customer=customer_id, return_url=return_url)


def list_payments(limit: int = 50) -> list:
    """List recent successful payment intents across the whole account."""
    if not is_configured():
        return []
    pis = stripe.PaymentIntent.list(limit=limit)
    return [
        {
            "id": p.id,
            "amount": p.amount / 100,
            "currency": p.currency,
            "status": p.status,
            "customer": p.customer,
            "description": p.description,
            "receipt_email": p.receipt_email,
            "created": p.created,
            "metadata": dict(p.metadata) if p.metadata else {},
        }
        for p in pis.data
    ]


def list_invoices(limit: int = 50) -> list:
    """List recent invoices."""
    if not is_configured():
        return []
    invs = stripe.Invoice.list(limit=limit)
    return [
        {
            "id": inv.id,
            "number": inv.number,
            "customer": inv.customer,
            "customer_email": inv.customer_email,
            "amount_paid": inv.amount_paid / 100,
            "amount_due": inv.amount_due / 100,
            "currency": inv.currency,
            "status": inv.status,
            "hosted_invoice_url": inv.hosted_invoice_url,
            "invoice_pdf": inv.invoice_pdf,
            "created": inv.created,
            "period_start": inv.period_start,
            "period_end": inv.period_end,
            "metadata": dict(inv.metadata) if inv.metadata else {},
        }
        for inv in invs.data
    ]


def list_subscriptions(limit: int = 50) -> list:
    """List active subscriptions."""
    if not is_configured():
        return []
    subs = stripe.Subscription.list(limit=limit, status="all")
    out = []
    for sub in subs.data:
        item = sub["items"]["data"][0] if sub["items"]["data"] else None
        out.append({
            "id": sub.id,
            "customer": sub.customer,
            "status": sub.status,
            "current_period_start": sub.current_period_start,
            "current_period_end": sub.current_period_end,
            "cancel_at_period_end": sub.cancel_at_period_end,
            "price_id": item["price"]["id"] if item else None,
            "amount": (item["price"]["unit_amount"] / 100) if item else 0,
            "currency": item["price"]["currency"] if item else "eur",
            "interval": item["price"]["recurring"]["interval"] if item else "month",
            "metadata": dict(sub.metadata) if sub.metadata else {},
        })
    return out


def verify_webhook(payload: bytes, sig_header: str) -> stripe.Event:
    """Verify and parse a Stripe webhook event."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET not configured")
    return stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
