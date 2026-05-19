"""Teclados inline reutilizables."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from logic import SYMPTOMS


def _kb(rows):
    return InlineKeyboardMarkup(rows)


def main_menu():
    return _kb([
        [InlineKeyboardButton("🛞 Presiones de ruedas", callback_data="mode:tires")],
        [InlineKeyboardButton("⚙️ Suspensión (sag + rebote)", callback_data="mode:suspension")],
        [InlineKeyboardButton("🔧 Setup completo", callback_data="mode:full")],
        [InlineKeyboardButton("🩺 Algo no va bien", callback_data="mode:diagnostic")],
    ])


def use_profile():
    return _kb([
        [InlineKeyboardButton("✅ Usar mi perfil guardado", callback_data="profile:use")],
        [InlineKeyboardButton("🔄 Empezar de cero", callback_data="profile:reset")],
    ])


def discipline():
    return _kb([
        [InlineKeyboardButton("XC", callback_data="discipline:XC"),
         InlineKeyboardButton("Trail", callback_data="discipline:Trail")],
        [InlineKeyboardButton("Enduro", callback_data="discipline:Enduro"),
         InlineKeyboardButton("DH", callback_data="discipline:DH")],
    ])


def bike_type():
    return _kb([
        [InlineKeyboardButton("Doble suspensión", callback_data="bike:double")],
        [InlineKeyboardButton("Rígida (hardtail o fully rígida)", callback_data="bike:rigid")],
    ])


def terrain():
    return _kb([
        [InlineKeyboardButton("Seco", callback_data="terrain:Seco"),
         InlineKeyboardButton("Mixto", callback_data="terrain:Mixto")],
        [InlineKeyboardButton("Mojado", callback_data="terrain:Mojado"),
         InlineKeyboardButton("Barro", callback_data="terrain:Barro")],
    ])


def tire_width(prefix: str):
    widths = ["2.1", "2.3", "2.4", "2.5", "2.6", "2.8"]
    rows = []
    for i in range(0, len(widths), 3):
        rows.append([
            InlineKeyboardButton(f'{w}"', callback_data=f"{prefix}:{w}")
            for w in widths[i:i+3]
        ])
    return _kb(rows)


def tubeless(prefix: str):
    return _kb([
        [InlineKeyboardButton("Sí", callback_data=f"{prefix}:yes"),
         InlineKeyboardButton("No", callback_data=f"{prefix}:no")],
        [InlineKeyboardButton("No sé", callback_data=f"{prefix}:dunno")],
    ])


def insert(prefix: str):
    return _kb([
        [InlineKeyboardButton("Sí", callback_data=f"{prefix}:yes"),
         InlineKeyboardButton("No", callback_data=f"{prefix}:no")],
    ])


def fork_travel():
    travels = [100, 120, 130, 140, 150, 160, 170]
    rows = []
    for i in range(0, len(travels), 4):
        rows.append([
            InlineKeyboardButton(f"{t} mm", callback_data=f"forktravel:{t}")
            for t in travels[i:i+4]
        ])
    return _kb(rows)


def fork_brand():
    return _kb([
        [InlineKeyboardButton("Fox", callback_data="forkbrand:Fox"),
         InlineKeyboardButton("RockShox", callback_data="forkbrand:RockShox")],
        [InlineKeyboardButton("Öhlins", callback_data="forkbrand:Öhlins"),
         InlineKeyboardButton("Otra", callback_data="forkbrand:Otra")],
    ])


def shock_type():
    return _kb([
        [InlineKeyboardButton("Solo Air", callback_data="shock:Solo Air"),
         InlineKeyboardButton("DebonAir", callback_data="shock:DebonAir")],
        [InlineKeyboardButton("Coil", callback_data="shock:Coil"),
         InlineKeyboardButton("No sé", callback_data="shock:No sé")],
    ])


def riding_style():
    return _kb([
        [InlineKeyboardButton("Suave", callback_data="style:Suave"),
         InlineKeyboardButton("Agresivo", callback_data="style:Agresivo")],
    ])


def diagnostic_symptoms():
    rows = []
    for key, label, _resp in SYMPTOMS:
        rows.append([InlineKeyboardButton(label, callback_data=f"sym:{key}")])
    rows.append([InlineKeyboardButton("⬅️ Volver al menú", callback_data="back:menu")])
    return _kb(rows)


def back_to_menu():
    return _kb([
        [InlineKeyboardButton("⬅️ Volver al menú", callback_data="back:menu")],
    ])


def upgrade_options(pro_stars: int, shop_stars: int):
    """Botones que disparan el envío de factura con Telegram Stars."""
    rows = [
        [InlineKeyboardButton(
            f"⭐ Plan Pro · {pro_stars} stars/mes",
            callback_data="upgrade:pro",
        )],
        [InlineKeyboardButton(
            f"🏪 Plan Tiendas · {shop_stars} stars/mes",
            callback_data="upgrade:shop",
        )],
        [InlineKeyboardButton("⬅️ Volver al menú", callback_data="back:menu")],
    ]
    return _kb(rows)
