"""Pagos con Telegram Stars (currency code XTR)."""
import logging
from datetime import datetime, timedelta, timezone

from telegram import LabeledPrice, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

import db
from config import (
    INVOICE_PAYLOAD_PRO,
    INVOICE_PAYLOAD_SHOP,
    STARS_PRO_PRICE,
    STARS_SHOP_PRICE,
    STARS_SUBSCRIPTION_PERIOD,
)
from handlers import keyboards as kb

log = logging.getLogger(__name__)


# ---------- envío de factura ----------

async def on_upgrade_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Disparado cuando el usuario pulsa 'Suscribirse Pro/Shop' en el paywall."""
    q = update.callback_query
    await q.answer()
    plan = q.data.split(":", 1)[1]  # "pro" o "shop"

    if plan == "pro":
        title = "MTB Setup Bot — Plan Pro"
        description = (
            "Consultas ilimitadas durante 30 días. "
            "Se renueva automáticamente cada mes (puedes cancelar en cualquier momento "
            "desde Telegram → Ajustes → Bots → Suscripciones)."
        )
        prices = [LabeledPrice("Plan Pro · 30 días", STARS_PRO_PRICE)]
        payload = INVOICE_PAYLOAD_PRO
    elif plan == "shop":
        title = "MTB Setup Bot — Plan Tiendas"
        description = (
            "Consultas ilimitadas y prefijo personalizado para tu tienda. "
            "Se renueva automáticamente cada mes."
        )
        prices = [LabeledPrice("Plan Tiendas · 30 días", STARS_SHOP_PRICE)]
        payload = INVOICE_PAYLOAD_SHOP
    else:
        return

    try:
        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title=title,
            description=description,
            payload=payload,
            currency="XTR",
            prices=prices,
            # subscription_period aún no es parámetro nombrado en PTB; lo pasamos
            # vía api_kwargs hasta que lo añadan.
            api_kwargs={"subscription_period": STARS_SUBSCRIPTION_PERIOD},
        )
    except Exception as e:
        log.exception("Error enviando factura: %s", e)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🚧 No he podido lanzar el pago. Inténtalo de nuevo en un minuto.",
        )


# ---------- pre-checkout ----------

async def on_pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telegram pregunta si aceptamos el pago antes de cobrar."""
    q = update.pre_checkout_query
    if q.invoice_payload in (INVOICE_PAYLOAD_PRO, INVOICE_PAYLOAD_SHOP):
        await q.answer(ok=True)
    else:
        await q.answer(ok=False, error_message="Producto no reconocido.")


# ---------- pago exitoso ----------

async def on_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activa el plan en la base de datos."""
    payment = update.message.successful_payment
    user_id = update.effective_user.id

    if payment.invoice_payload == INVOICE_PAYLOAD_PRO:
        plan = "pro"
        label = "Plan Pro"
    elif payment.invoice_payload == INVOICE_PAYLOAD_SHOP:
        plan = "shop"
        label = "Plan Tiendas"
    else:
        log.warning("Pago con payload desconocido: %s", payment.invoice_payload)
        return

    # subscription_expiration_date: Unix timestamp si es suscripción
    if getattr(payment, "subscription_expiration_date", None):
        exp = datetime.fromtimestamp(payment.subscription_expiration_date, tz=timezone.utc)
    else:
        exp = datetime.now(timezone.utc) + timedelta(seconds=STARS_SUBSCRIPTION_PERIOD)

    db.activate_stars_plan(
        user_id,
        plan=plan,
        charge_id=payment.telegram_payment_charge_id,
        expires_at=exp,
    )

    log.info("Plan %s activado para %s hasta %s", plan, user_id, exp.isoformat())

    await update.message.reply_text(
        f"⭐ *¡{label} activado!*\n\n"
        f"Consultas ilimitadas hasta el *{exp.strftime('%d/%m/%Y')}*.\n"
        f"La suscripción se renueva sola. Puedes cancelarla desde Telegram → "
        f"Ajustes → *Bots y Mini Apps* → *Mis Suscripciones*.\n\n"
        f"Disfruta 🤙",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb.back_to_menu(),
    )


# ---------- comando /paysupport ----------
# Telegram requiere que los bots con pagos tengan respuesta a /paysupport.

async def cmd_paysupport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💬 *Soporte de pagos*\n\n"
        "Telegram gestiona los reembolsos de Stars automáticamente dentro de los 21 días "
        "tras la compra. Para reportar un problema, escribe directamente a "
        "@cristianduquemtb (o el contacto que corresponda).\n\n"
        "Si tu plan no se activó correctamente tras pagar, envía /start y luego /perfil. "
        "Si sigue marcando FREE, contáctame con el ID de la transacción.",
        parse_mode=ParseMode.MARKDOWN,
    )


# ---------- registro ----------

def register(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(on_upgrade_click, pattern=r"^upgrade:(pro|shop)$"))
    app.add_handler(PreCheckoutQueryHandler(on_pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, on_successful_payment))
    app.add_handler(CommandHandler("paysupport", cmd_paysupport))
