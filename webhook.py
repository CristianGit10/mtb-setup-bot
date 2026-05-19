"""Webhook de Lemon Squeezy para activar/desactivar plan Pro y Tiendas.

Lemon Squeezy firma cada request con HMAC-SHA256 usando el secret del webhook.
Configura el endpoint en https://app.lemonsqueezy.com/settings/webhooks apuntando a:
  https://TU-DOMINIO/lemon-squeezy/webhook

Cuando se crea el checkout desde el bot añade `custom[telegram_user_id]=<id>` en los
parámetros del enlace (puedes pre-configurarlo o construirlo dinámicamente) para
poder asociar la compra al usuario.
"""
import hashlib
import hmac
import logging
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request

import db
from config import (
    LEMON_SQUEEZY_WEBHOOK_SECRET,
    LEMON_SQUEEZY_VARIANT_PRO,
    LEMON_SQUEEZY_VARIANT_SHOP,
)

log = logging.getLogger(__name__)

app = FastAPI()


@app.get("/")
async def health():
    return {"status": "ok"}


def _verify_signature(payload: bytes, signature: Optional[str]) -> bool:
    if not LEMON_SQUEEZY_WEBHOOK_SECRET:
        log.warning("LEMON_SQUEEZY_WEBHOOK_SECRET vacío — rechazando webhook")
        return False
    if not signature:
        return False
    digest = hmac.new(
        LEMON_SQUEEZY_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, signature)


def _telegram_user_id_from(meta: dict) -> Optional[int]:
    custom = (meta or {}).get("custom_data") or {}
    raw = custom.get("telegram_user_id")
    if not raw:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _plan_from_variant(variant_id: Optional[str]) -> Optional[str]:
    if not variant_id:
        return None
    v = str(variant_id)
    if LEMON_SQUEEZY_VARIANT_PRO and v == str(LEMON_SQUEEZY_VARIANT_PRO):
        return "pro"
    if LEMON_SQUEEZY_VARIANT_SHOP and v == str(LEMON_SQUEEZY_VARIANT_SHOP):
        return "shop"
    return None


@app.post("/lemon-squeezy/webhook")
async def lemon_squeezy_webhook(
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
):
    payload = await request.body()
    if not _verify_signature(payload, x_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    body = await request.json()
    meta = body.get("meta", {}) or {}
    event_name = meta.get("event_name")
    data = body.get("data", {}) or {}
    attributes = data.get("attributes", {}) or {}

    telegram_user_id = _telegram_user_id_from(meta)
    variant_id = attributes.get("variant_id") or (data.get("relationships", {}).get("variant", {}).get("data", {}) or {}).get("id")
    plan = _plan_from_variant(variant_id)

    subscription_id = str(data.get("id")) if data.get("id") else None
    customer_id = str(attributes.get("customer_id")) if attributes.get("customer_id") else None
    renews_at = attributes.get("renews_at")

    log.info("LS event=%s plan=%s tg=%s sub=%s", event_name, plan, telegram_user_id, subscription_id)

    if event_name in ("subscription_created", "subscription_resumed", "subscription_updated", "order_created"):
        if telegram_user_id and plan:
            db.activate_plan(
                telegram_user_id,
                plan=plan,
                subscription_id=subscription_id,
                customer_id=customer_id,
                renewal_at=renews_at,
            )
    elif event_name in ("subscription_cancelled", "subscription_expired", "subscription_paused"):
        if subscription_id:
            db.deactivate_plan_by_subscription(subscription_id)

    return {"ok": True}
