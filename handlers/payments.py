"""Pagos con Telegram Stars — pago único de por vida."""
import logging

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
from config import INVOICE_PAYLOAD_PRO, STARS_PRO_PRICE
from handlers import keyboards as kb

log = logging.getLogger(__name__)


# ---------- envío de factura ----------

async def on_upgrade_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Disparado cuando el usuario pulsa 'Pro' en el paywall."""
    q = update.callback_query
    await q.answer()

    try:
        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title="MTB Setup Bot — Pro de por vida",
            description="Consultas ilimitadas para siempre. Un único pago, sin renovaciones.",
            payload=INVOICE_PAYLOAD_PRO,
            currency="XTR",
            prices=[LabeledPrice("Pro lifetime", STARS_PRO_PRICE)],
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
    if q.invoice_payload == INVOICE_PAYLOAD_PRO:
        await q.answer(ok=True)
    else:
        await q.answer(ok=False, error_message="Producto no reconocido.")


# ---------- pago exitoso ----------

async def on_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activa el plan permanente en la base de datos."""
    payment = update.message.successful_payment
    user_id = update.effective_user.id

    if payment.invoice_payload != INVOICE_PAYLOAD_PRO:
        log.warning("Pago con payload desconocido: %s", payment.invoice_payload)
        return

    db.activate_lifetime_plan(
        user_id,
        plan="pro",
        charge_id=payment.telegram_payment_charge_id,
    )

    log.info("Plan Pro lifetime activado para %s", user_id)

    await update.message.reply_text(
        "⭐ *¡Pro lifetime activado!*\n\n"
        "Tu plan es de por vida. Consultas ilimitadas, sin renovaciones.\n"
        "Disfruta 🤙",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb.back_to_menu(),
    )


# ---------- comando /paysupport (requerido por Telegram) ----------

async def cmd_paysupport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💬 *Soporte de pagos*\n\n"
        "Telegram gestiona los reembolsos de Stars automáticamente dentro de los 21 días "
        "tras la compra desde Ajustes → *Bots y Mini Apps* → *Mis Compras*.\n\n"
        "Si tu plan no se activó correctamente tras pagar, envía /start y luego /perfil. "
        "Si sigue marcando FREE, contáctame con el ID de la transacción.",
        parse_mode=ParseMode.MARKDOWN,
    )


# ---------- registro ----------

def register(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(on_upgrade_click, pattern=r"^upgrade:pro$"))
    app.add_handler(PreCheckoutQueryHandler(on_pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, on_successful_payment))
    app.add_handler(CommandHandler("paysupport", cmd_paysupport))
