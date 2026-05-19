"""Cálculo de presiones de rueda, suspensión y diagnóstico por síntomas."""
from typing import Optional


# ---------- PRESIONES DE RUEDA ----------

_BASE_PRESSURE_TABLE = [
    # (peso_min, peso_max, {disciplina: (delantera, trasera)})
    (55, 65,  {"XC": (20, 22), "Trail": (17, 19), "Enduro": (16, 18), "DH": (18, 20)}),
    (65, 75,  {"XC": (22, 24), "Trail": (19, 21), "Enduro": (17, 20), "DH": (20, 22)}),
    (75, 85,  {"XC": (24, 26), "Trail": (21, 24), "Enduro": (19, 22), "DH": (22, 24)}),
    (85, 95,  {"XC": (26, 29), "Trail": (23, 26), "Enduro": (21, 24), "DH": (24, 26)}),
    (95, 110, {"XC": (28, 31), "Trail": (25, 28), "Enduro": (23, 26), "DH": (26, 28)}),
]


def _base_tire_pressure(weight_kg: float, discipline: str) -> tuple[float, float]:
    for lo, hi, table in _BASE_PRESSURE_TABLE:
        if lo <= weight_kg <= hi:
            return table[discipline]
    if weight_kg < 55:
        return _BASE_PRESSURE_TABLE[0][2][discipline]
    return _BASE_PRESSURE_TABLE[-1][2][discipline]


def _width_adjustment(width: float) -> int:
    if width <= 2.2:
        return 3
    if width <= 2.4:
        return 0
    if width <= 2.6:
        return -1
    return -2  # 2.8


def _terrain_adjustment(terrain: str) -> int:
    return {"Seco": 2, "Mixto": 0, "Mojado": -1, "Barro": -2}[terrain]


def calculate_tire_pressures(profile: dict) -> dict:
    weight = profile["weight_kg"]
    discipline = profile["discipline"]
    terrain = profile["terrain"]
    bike_type = profile["bike_type"]  # "double" | "rigid"

    base_f, base_r = _base_tire_pressure(weight, discipline)
    terrain_adj = _terrain_adjustment(terrain)

    front = base_f + _width_adjustment(profile["front_width"]) + terrain_adj
    if not profile["front_tubeless"]:
        front += 4
    if profile.get("front_insert"):
        front -= 1

    rear = base_r + _width_adjustment(profile["rear_width"]) + terrain_adj
    if not profile["rear_tubeless"]:
        rear += 4
    if profile.get("rear_insert"):
        rear -= 1
    if bike_type == "rigid":
        rear += 2

    # Garantizamos trasera 2-3 psi por encima de delantera
    if rear - front < 2:
        rear = front + 2

    return {
        "front": _round_range(front),
        "rear":  _round_range(rear),
    }


def _round_range(psi: float) -> tuple[int, int]:
    low = int(round(psi - 0.5))
    high = low + 1
    return low, high


# ---------- SUSPENSIÓN ----------

_SAG_RANGE = {
    "XC":     (0.20, 0.25),
    "Trail":  (0.25, 0.30),
    "Enduro": (0.30, 0.30),
    "DH":     (0.30, 0.35),
}


def _sag_target_pct(discipline: str, shock_type: Optional[str]) -> float:
    if shock_type == "Solo Air":
        return 0.25
    if shock_type == "DebonAir":
        return 0.30
    lo, hi = _SAG_RANGE[discipline]
    return (lo + hi) / 2


def _starting_fork_pressure_psi(weight_kg: float) -> int:
    return int(round(weight_kg * 2.2046))


def _rebound_clicks_from_closed(weight_kg: float, discipline: str) -> tuple[int, int]:
    if weight_kg < 65:
        return {"XC": (5, 6), "Trail": (6, 7), "Enduro": (7, 8), "DH": (7, 8)}[discipline]
    if weight_kg < 80:
        return {"XC": (6, 7), "Trail": (7, 9), "Enduro": (8, 10), "DH": (8, 10)}[discipline]
    if weight_kg < 95:
        return {"XC": (7, 8), "Trail": (8, 10), "Enduro": (9, 11), "DH": (9, 11)}[discipline]
    return {"XC": (8, 9), "Trail": (9, 11), "Enduro": (10, 12), "DH": (10, 12)}[discipline]


def calculate_suspension(profile: dict) -> dict:
    weight = profile["weight_kg"]
    discipline = profile["discipline"]
    fork_brand = profile.get("fork_brand", "Otra")
    fork_travel = profile["fork_travel"]
    shock_type = profile.get("shock_type")
    riding_style = profile.get("riding_style", "Suave")
    bike_type = profile["bike_type"]

    sag_pct = _sag_target_pct(discipline, shock_type)
    sag_mm = round(fork_travel * sag_pct)

    fork_pressure = _starting_fork_pressure_psi(weight)
    if riding_style == "Agresivo":
        fork_pressure += 5

    rebound_lo, rebound_hi = _rebound_clicks_from_closed(weight, discipline)

    return {
        "fork_pressure_psi": fork_pressure,
        "sag_mm": sag_mm,
        "sag_pct": int(round(sag_pct * 100)),
        "rebound_clicks": (rebound_lo, rebound_hi),
        "fork_brand": fork_brand,
        "fork_travel": fork_travel,
        "has_rear_shock": bike_type == "double",
        "shock_type": shock_type,
    }


# ---------- DIAGNÓSTICO ----------

SYMPTOMS = [
    ("bounce_rocks",       "La bici rebota mucho en rocas",
     "Presión de rueda alta. Baja 2–3 psi y prueba otra vez. Si rebota igual, baja 1 psi más."),
    ("frequent_punctures", "Pinchazos frecuentes",
     "Presión baja con cámara. Sube 3–5 psi. Si vas con cámara y haces enduro/DH, considera pasar a tubeless."),
    ("tubeless_burp",      "El tubeless eructa en curvas",
     "Presión demasiado baja. Sube 1–2 psi. Si pasa solo atrás, sube primero la trasera."),
    ("fork_dive_brake",    "La horquilla se hunde en frenadas",
     "Falta soporte a media carrera. Añade +2 clics de LSC (compresión baja velocidad) o +5 psi a la horquilla."),
    ("fork_harsh_roots",   "La horquilla está muy dura en raíces",
     "Está demasiado rígida. Quita 5 psi o abre 2 clics de LSC. Verifica que el sag esté dentro del objetivo."),
    ("rebound_too_fast",   "El rebote va muy rápido, parece que salta",
     "Cierra +2 clics de rebote. Repite el test de la caída de 20 cm: debe rebotar UNA sola vez."),
    ("rebound_too_slow",   "La suspensión parece lenta o pegajosa",
     "Abre 2 clics de rebote. Si sigue lenta, abre 1 más. Cuidado de no pasarte: si rebota dos veces, has abierto de más."),
    ("bottom_out",         "Toco fondo en bajadas",
     "Falta progresividad. Sube 5–10 psi o añade un token (volume spacer) a la horquilla."),
    ("front_washes",       "La rueda delantera se va en curvas",
     "Falta agarre delantero. Baja 1–2 psi en la rueda delantera. Si llevas tubeless, no bajes de 16 psi."),
]


def diagnostic_response(symptom_key: str) -> str:
    for key, _label, response in SYMPTOMS:
        if key == symptom_key:
            return response
    return "No tengo respuesta para ese síntoma todavía."
