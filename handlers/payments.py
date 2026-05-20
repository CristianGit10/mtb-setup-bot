"""Pagos con PayPal manual + comandos de admin para activar/revocar Pro."""
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

import db
from config import OWNER_TELEGRAM_ID

log = logging.getLogger(__name__)


def _is_owner(update: Update) -> bool:
    return update.effective_user and update.effective_user.id == OWNER_TELEGRAM_ID


async def _resolve_target(arg: str):
    """Devuelve (telegram_user_id, etiqueta) a partir de un ID numérico o @username."""
    arg = arg.strip()
    if arg.startswith("@"):
        user = db.get_user_by_username(arg)
        if not user:
            return None, None
        return user["telegram_user_id"], arg
    try:
        return int(arg), arg
    except ValueError:
        return None, None


# ---------- /grant ----------

async def cmd_grant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update):
        return
    if not context.args:
        await update.message.reply_text("Uso: `/grant <telegram_id>` o `/grant @username`", parse_mode=ParseMode.MARKDOWN)
        return

    uid, label = await _resolve_target(context.args[0])
    if uid is None:
        await update.message.reply_text(
            "No reconozco ese usuario. Si usaste @username, asegúrate de que ya escribió /start al bot."
        )
        return

    affected = db.grant_lifetime(uid)
    if affected == 0:
        await update.message.reply_text(
            f"⚠️ {label} no está en la base de datos todavía. Pídele que envíe /start al bot y reintenta."
        )
        return

    await update.message.reply_text(f"✅ Pro de por vida activado para {label} (ID {uid}).")

    # Avisar al comprador
    try:
        await context.bot.send_message(
            chat_id=uid,
            text="⭐ *¡Tu Pro de por vida está activo!*\n\nGracias por tu compra. "
                 "Ya tienes consultas ilimitadas. 🤙",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        log.warning("No pude avisar al usuario %s: %s", uid, e)
        await update.message.reply_text(
            "(No he podido enviarle el aviso automático, quizá bloqueó el bot. Pero el Pro ya está activo.)"
        )


# ---------- /revoke ----------

async def cmd_revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update):
        return
    if not context.args:
        await update.message.reply_text("Uso: `/revoke <telegram_id>` o `/revoke @username`", parse_mode=ParseMode.MARKDOWN)
        return

    uid, label = await _resolve_target(context.args[0])
    if uid is None:
        await update.message.reply_text("No reconozco ese usuario.")
        return

    affected = db.revoke_plan(uid)
    if affected == 0:
        await update.message.reply_text(f"⚠️ {label} no está en la base de datos.")
        return
    await update.message.reply_text(f"✅ Plan revertido a FREE para {label} (ID {uid}).")


# ---------- /paysupport (requerido por Telegram) ----------

async def cmd_paysupport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💬 *Soporte de pagos*\n\n"
        "Los pagos son por PayPal. Si pagaste y tu Pro no se ha activado en unos minutos, "
        "escríbeme con el comprobante y tu usuario de Telegram y lo soluciono.",
        parse_mode=ParseMode.MARKDOWN,
    )


# ---------- registro ----------

def register(app: Application) -> None:
    app.add_handler(CommandHandler("grant", cmd_grant))
    app.add_handler(CommandHandler("revoke", cmd_revoke))
    app.add_handler(CommandHandler("paysupport", cmd_paysupport))
