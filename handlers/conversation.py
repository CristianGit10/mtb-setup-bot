"""ConversationHandler central: menú, recogida de datos y respuesta final."""
import logging
from typing import Optional

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import db
import formatting
import logic
from config import STARS_PRO_PRICE, STARS_SHOP_PRICE
from handlers import keyboards as kb
from handlers.states import (
    MENU, USE_PROFILE, WEIGHT, DISCIPLINE, BIKE_TYPE, TERRAIN,
    FRONT_WIDTH, FRONT_TUBELESS, FRONT_TUBELESS_HELP, FRONT_INSERT,
    REAR_WIDTH, REAR_TUBELESS, REAR_TUBELESS_HELP, REAR_INSERT,
    FORK_TRAVEL, FORK_BRAND, SHOCK_TYPE, RIDING_STYLE, DIAG_SYMPTOM,
    MODE_TIRES, MODE_SUSPENSION, MODE_FULL, MODE_DIAGNOSTIC,
)

log = logging.getLogger(__name__)


# ---------- helpers ----------

async def _send(update: Update, text: str, reply_markup=None, parse_mode=None):
    """Envía texto respondiendo a un mensaje o editando el callback origen."""
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            return
        except Exception:
            pass
    chat = update.effective_chat
    await chat.send_message(text, reply_markup=reply_markup, parse_mode=parse_mode)


def _mode_needs_tires(mode: str) -> bool:
    return mode in (MODE_TIRES, MODE_FULL)


def _mode_needs_suspension(mode: str) -> bool:
    return mode in (MODE_SUSPENSION, MODE_FULL)


def _profile_complete_for_mode(user: dict, mode: str) -> bool:
    base = all(user.get(k) is not None for k in ("weight_kg", "discipline", "bike_type"))
    if not base:
        return False
    if _mode_needs_tires(mode):
        if not all(user.get(k) is not None for k in (
            "front_width", "rear_width", "front_tubeless", "rear_tubeless"
        )):
            return False
    if _mode_needs_suspension(mode):
        if not user.get("fork_travel"):
            return False
        if user.get("bike_type") == "double" and not user.get("shock_type"):
            return False
    return True


# ---------- /start ----------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    db.get_or_create_user(user_tg.id, user_tg.username, user_tg.first_name)
    context.user_data.clear()
    text = (
        f"¡Eh {user_tg.first_name or 'rider'}! 👋\n\n"
        "Soy *MTB Setup Bot*. Te ayudo a clavar la presión de las ruedas y la suspensión "
        "según tu peso, tu bici y el terreno.\n\n"
        "¿Qué quieres configurar hoy?"
    )
    await _send(update, text, reply_markup=kb.main_menu(), parse_mode=ParseMode.MARKDOWN)
    return MENU


# ---------- menú principal ----------

async def on_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    mode = q.data.split(":", 1)[1]
    context.user_data["mode"] = mode
    context.user_data["profile"] = {}

    user_tg = update.effective_user
    user = db.get_or_create_user(user_tg.id, user_tg.username, user_tg.first_name)

    # Paywall: solo aplica al cerrar (calcular). El diagnóstico también cuenta.
    can_query, remaining = db.can_make_query(user)
    if not can_query:
        await _show_paywall(update, context)
        return ConversationHandler.END

    if mode == MODE_DIAGNOSTIC:
        await q.edit_message_text(
            "¿Qué notas? Cuéntame el síntoma:",
            reply_markup=kb.diagnostic_symptoms(),
        )
        return DIAG_SYMPTOM

    # Setup flows
    if db.has_saved_profile(user) and _profile_complete_for_mode(user, mode):
        # cargamos perfil en memoria para reutilizar
        context.user_data["saved_profile_snapshot"] = {
            k: user.get(k) for k in db.PROFILE_FIELDS if user.get(k) is not None
        }
        await q.edit_message_text(
            "Tengo tu perfil guardado. ¿Lo usamos o empezamos de cero?",
            reply_markup=kb.use_profile(),
        )
        return USE_PROFILE

    return await _ask_weight(update, context)


# ---------- perfil guardado ----------

async def on_use_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    action = q.data.split(":", 1)[1]
    if action == "use":
        context.user_data["profile"].update(context.user_data.get("saved_profile_snapshot", {}))
        return await _ask_terrain(update, context)
    return await _ask_weight(update, context)


# ---------- preguntas básicas ----------

async def _ask_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💪 *Tu peso con el equipo completo*\n\n"
        "Mándame el peso en kg incluyendo casco, mochila, protecciones y agua.\n"
        "_(Como referencia, suma unos +5 kg a tu peso en ropa.)_\n\n"
        "Escríbelo en números, ej. `82`"
    )
    await _send(update, text, parse_mode=ParseMode.MARKDOWN)
    return WEIGHT


async def on_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = (update.message.text or "").replace(",", ".").strip()
    try:
        weight = float(raw)
    except ValueError:
        await update.message.reply_text("Necesito un número en kg, por ejemplo: 82")
        return WEIGHT
    if weight < 35 or weight > 160:
        await update.message.reply_text("Eso no parece un peso real. Manda algo entre 35 y 160 kg.")
        return WEIGHT
    context.user_data["profile"]["weight_kg"] = weight

    await update.message.reply_text(
        "🚵 ¿Qué disciplina haces principalmente?",
        reply_markup=kb.discipline(),
    )
    return DISCIPLINE


async def on_discipline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["profile"]["discipline"] = q.data.split(":", 1)[1]
    await q.edit_message_text(
        "🚲 ¿Qué tipo de bici tienes?",
        reply_markup=kb.bike_type(),
    )
    return BIKE_TYPE


async def on_bike_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["profile"]["bike_type"] = q.data.split(":", 1)[1]
    return await _ask_terrain(update, context)


async def _ask_terrain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send(
        update,
        "🌦️ ¿Cómo está el terreno hoy?",
        reply_markup=kb.terrain(),
    )
    return TERRAIN


async def on_terrain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["profile"]["terrain"] = q.data.split(":", 1)[1]

    mode = context.user_data["mode"]
    profile = context.user_data["profile"]

    if _mode_needs_tires(mode) and "front_width" not in profile:
        await q.edit_message_text(
            "🛞 *Rueda delantera*\n\n¿Qué anchura de neumático lleva?",
            reply_markup=kb.tire_width("frontw"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return FRONT_WIDTH

    if _mode_needs_suspension(mode) and not profile.get("fork_travel"):
        await q.edit_message_text(
            "⚙️ ¿Qué recorrido tiene la horquilla?",
            reply_markup=kb.fork_travel(),
        )
        return FORK_TRAVEL

    # Perfil cargado: ya tenemos todo, calcula directo
    return await _finish_setup(update, context)


# ---------- ruedas ----------

async def on_front_width(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["profile"]["front_width"] = float(q.data.split(":", 1)[1])
    await q.edit_message_text(
        "¿Va tubelizada la rueda delantera?",
        reply_markup=kb.tubeless("frontt"),
    )
    return FRONT_TUBELESS


async def on_front_tubeless(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    val = q.data.split(":", 1)[1]
    if val == "dunno":
        await q.edit_message_text(
            "🔍 Desinfla un poco con el dedo. ¿Sale líquido blanco o verde?\n"
            "Si sí, es *tubeless*. Si solo aire, lleva *cámara*.",
            reply_markup=kb.tubeless("frontt"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return FRONT_TUBELESS_HELP
    context.user_data["profile"]["front_tubeless"] = (val == "yes")
    await q.edit_message_text(
        "¿Llevas inserto delantero? (CushCore, Tannus, Vittoria Air-Liner)",
        reply_markup=kb.insert("fronti"),
    )
    return FRONT_INSERT


async def on_front_insert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["profile"]["front_insert"] = (q.data.split(":", 1)[1] == "yes")
    await q.edit_message_text(
        "🛞 *Rueda trasera*\n\n¿Qué anchura de neumático lleva?",
        reply_markup=kb.tire_width("rearw"),
        parse_mode=ParseMode.MARKDOWN,
    )
    return REAR_WIDTH


async def on_rear_width(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["profile"]["rear_width"] = float(q.data.split(":", 1)[1])
    await q.edit_message_text(
        "¿Va tubelizada la rueda trasera?",
        reply_markup=kb.tubeless("reart"),
    )
    return REAR_TUBELESS


async def on_rear_tubeless(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    val = q.data.split(":", 1)[1]
    if val == "dunno":
        await q.edit_message_text(
            "🔍 Desinfla un poco con el dedo. ¿Sale líquido blanco o verde?\n"
            "Si sí, es *tubeless*. Si solo aire, lleva *cámara*.",
            reply_markup=kb.tubeless("reart"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return REAR_TUBELESS_HELP
    context.user_data["profile"]["rear_tubeless"] = (val == "yes")
    await q.edit_message_text(
        "¿Llevas inserto trasero? (CushCore, Tannus, Vittoria Air-Liner)",
        reply_markup=kb.insert("reari"),
    )
    return REAR_INSERT


async def on_rear_insert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["profile"]["rear_insert"] = (q.data.split(":", 1)[1] == "yes")
    mode = context.user_data["mode"]
    if _mode_needs_suspension(mode) and not context.user_data["profile"].get("fork_travel"):
        await q.edit_message_text(
            "⚙️ ¿Qué recorrido tiene la horquilla?",
            reply_markup=kb.fork_travel(),
        )
        return FORK_TRAVEL
    return await _finish_setup(update, context)


# ---------- suspensión ----------

async def on_fork_travel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["profile"]["fork_travel"] = int(q.data.split(":", 1)[1])
    await q.edit_message_text(
        "¿Qué marca es la horquilla?",
        reply_markup=kb.fork_brand(),
    )
    return FORK_BRAND


async def on_fork_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["profile"]["fork_brand"] = q.data.split(":", 1)[1]
    if context.user_data["profile"].get("bike_type") == "double":
        await q.edit_message_text(
            "¿Qué tipo de amortiguador trasero llevas?",
            reply_markup=kb.shock_type(),
        )
        return SHOCK_TYPE
    await q.edit_message_text(
        "¿Cómo describirías tu estilo?",
        reply_markup=kb.riding_style(),
    )
    return RIDING_STYLE


async def on_shock_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["profile"]["shock_type"] = q.data.split(":", 1)[1]
    await q.edit_message_text(
        "¿Cómo describirías tu estilo?",
        reply_markup=kb.riding_style(),
    )
    return RIDING_STYLE


async def on_riding_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["profile"]["riding_style"] = q.data.split(":", 1)[1]
    return await _finish_setup(update, context)


# ---------- diagnóstico ----------

async def on_diagnostic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data.startswith("back:"):
        return await _back_to_menu(update, context)
    key = q.data.split(":", 1)[1]
    label = next((l for k, l, _ in logic.SYMPTOMS if k == key), key)
    response = logic.diagnostic_response(key)
    text = formatting.format_diagnostic(label, response)

    # Cuenta como consulta también
    db.increment_query_count(update.effective_user.id)

    await q.edit_message_text(
        text + "\n\n¿Quieres revisar otro síntoma o volver al menú?",
        reply_markup=kb.diagnostic_symptoms(),
        parse_mode=ParseMode.MARKDOWN,
    )
    return DIAG_SYMPTOM


# ---------- cierre del setup ----------

async def _finish_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data["mode"]
    profile = context.user_data["profile"]
    user_tg = update.effective_user

    blocks = []
    if _mode_needs_tires(mode):
        tires = logic.calculate_tire_pressures(profile)
    if _mode_needs_suspension(mode):
        sus = logic.calculate_suspension(profile)

    if mode == MODE_TIRES:
        text = formatting.format_tires_block(profile, tires)
    elif mode == MODE_SUSPENSION:
        text = formatting.format_suspension_block(profile, sus)
    else:  # MODE_FULL
        text = formatting.format_full(profile, tires, sus)

    # Persistencia + contador
    try:
        db.save_profile(user_tg.id, profile)
        db.increment_query_count(user_tg.id)
    except Exception as e:
        log.exception("Error guardando perfil/contador: %s", e)

    await _send(update, text, reply_markup=kb.back_to_menu())
    context.user_data.clear()
    return ConversationHandler.END


# ---------- paywall ----------

async def _show_paywall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🚧 *Has llegado al límite del plan gratuito* (3 consultas este mes).\n\n"
        "Pásate al *Plan Pro* y tendrás consultas ilimitadas durante 30 días. "
        "Pago con Telegram Stars sin salir del chat."
    )
    await _send(
        update,
        text,
        reply_markup=kb.upgrade_options(STARS_PRO_PRICE, STARS_SHOP_PRICE),
        parse_mode=ParseMode.MARKDOWN,
    )


# ---------- volver al menú ----------

async def _back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await _send(
        update,
        "¿Qué quieres configurar?",
        reply_markup=kb.main_menu(),
    )
    return MENU


async def on_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _back_to_menu(update, context)


# ---------- cancel ----------

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Vale, cancelado. Cuando quieras escribe /start.",
    )
    return ConversationHandler.END


# ---------- /perfil ----------

async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    if not user or not db.has_saved_profile(user):
        await update.message.reply_text(
            "Todavía no tengo tu perfil. Escribe /start y haz un setup completo para que lo guarde."
        )
        return
    lines = ["📇 *Tu perfil guardado*", ""]
    pairs = [
        ("Peso", f'{user.get("weight_kg")} kg'),
        ("Disciplina", user.get("discipline")),
        ("Bici", "Doble suspensión" if user.get("bike_type") == "double" else "Rígida"),
        ("Rueda delantera", f'{user.get("front_width")}" {"tubeless" if user.get("front_tubeless") else "cámara"}'),
        ("Rueda trasera", f'{user.get("rear_width")}" {"tubeless" if user.get("rear_tubeless") else "cámara"}'),
        ("Horquilla", f'{user.get("fork_brand") or "—"} · {user.get("fork_travel") or "—"} mm'),
        ("Amortiguador", user.get("shock_type") or "—"),
        ("Estilo", user.get("riding_style") or "—"),
        ("Plan", user.get("plan", "free").upper()),
    ]
    lines += [f"• *{k}:* {v}" for k, v in pairs if v]
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def cmd_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_or_create_user(
        update.effective_user.id,
        update.effective_user.username,
        update.effective_user.first_name,
    )
    plan = user.get("plan", "free")
    if plan in ("pro", "shop"):
        await update.message.reply_text(
            f"⭐ Estás en el plan *{plan.upper()}*. Consultas ilimitadas. ¡A disfrutar!",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    _, remaining = db.can_make_query(user)
    text = (
        f"📊 Plan *FREE* — te quedan *{remaining}* consultas este mes.\n\n"
        "¿Quieres pasar a Pro?"
    )
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb.upgrade_options(STARS_PRO_PRICE, STARS_SHOP_PRICE),
    )


# ---------- registro ----------

def build_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", cmd_start),
            CallbackQueryHandler(cmd_start, pattern=r"^back:menu$"),
        ],
        states={
            MENU: [CallbackQueryHandler(on_menu, pattern=r"^mode:")],
            USE_PROFILE: [CallbackQueryHandler(on_use_profile, pattern=r"^profile:")],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_weight)],
            DISCIPLINE: [CallbackQueryHandler(on_discipline, pattern=r"^discipline:")],
            BIKE_TYPE: [CallbackQueryHandler(on_bike_type, pattern=r"^bike:")],
            TERRAIN: [CallbackQueryHandler(on_terrain, pattern=r"^terrain:")],
            FRONT_WIDTH: [CallbackQueryHandler(on_front_width, pattern=r"^frontw:")],
            FRONT_TUBELESS: [CallbackQueryHandler(on_front_tubeless, pattern=r"^frontt:")],
            FRONT_TUBELESS_HELP: [CallbackQueryHandler(on_front_tubeless, pattern=r"^frontt:")],
            FRONT_INSERT: [CallbackQueryHandler(on_front_insert, pattern=r"^fronti:")],
            REAR_WIDTH: [CallbackQueryHandler(on_rear_width, pattern=r"^rearw:")],
            REAR_TUBELESS: [CallbackQueryHandler(on_rear_tubeless, pattern=r"^reart:")],
            REAR_TUBELESS_HELP: [CallbackQueryHandler(on_rear_tubeless, pattern=r"^reart:")],
            REAR_INSERT: [CallbackQueryHandler(on_rear_insert, pattern=r"^reari:")],
            FORK_TRAVEL: [CallbackQueryHandler(on_fork_travel, pattern=r"^forktravel:")],
            FORK_BRAND: [CallbackQueryHandler(on_fork_brand, pattern=r"^forkbrand:")],
            SHOCK_TYPE: [CallbackQueryHandler(on_shock_type, pattern=r"^shock:")],
            RIDING_STYLE: [CallbackQueryHandler(on_riding_style, pattern=r"^style:")],
            DIAG_SYMPTOM: [
                CallbackQueryHandler(on_diagnostic, pattern=r"^sym:"),
                CallbackQueryHandler(on_back, pattern=r"^back:"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cmd_cancel),
            CommandHandler("start", cmd_start),
            CallbackQueryHandler(on_back, pattern=r"^back:menu$"),
        ],
        allow_reentry=True,
    )


def register(app: Application) -> None:
    app.add_handler(build_conversation())
    app.add_handler(CommandHandler("perfil", cmd_profile))
    app.add_handler(CommandHandler("plan", cmd_plan))
