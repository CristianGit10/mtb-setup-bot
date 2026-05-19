"""Plantillas de respuesta del bot."""


def _bike_label(profile: dict) -> str:
    discipline = profile.get("discipline", "")
    weight = profile.get("weight_kg")
    terrain = profile.get("terrain", "")
    parts = [p for p in (discipline, f"{int(weight)}kg" if weight else None, terrain) if p]
    return " · ".join(parts)


def format_tires(profile: dict, tires: dict) -> str:
    fw = profile["front_width"]
    rw = profile["rear_width"]
    f_lo, f_hi = tires["front"]
    r_lo, r_hi = tires["rear"]
    f_tubeless = "tubeless" if profile["front_tubeless"] else "con cámara"
    r_tubeless = "tubeless" if profile["rear_tubeless"] else "con cámara"

    lines = [
        f"🔧 TU SETUP MTB — {_bike_label(profile)}",
        "",
        f"🔵 RUEDA DELANTERA ({fw}\" {f_tubeless})",
        f"→ {f_lo}–{f_hi} psi",
        "",
        f"🟠 RUEDA TRASERA ({rw}\" {r_tubeless})",
        f"→ {r_lo}–{r_hi} psi",
    ]
    return "\n".join(lines)


def format_suspension(profile: dict, sus: dict) -> str:
    fork = f"{profile.get('fork_brand', 'Horquilla')} · {sus['fork_travel']}mm"
    lines = [
        f"⚙️ HORQUILLA ({fork})",
        f"→ Presión: ~{sus['fork_pressure_psi']} psi (ajusta hasta el sag objetivo)",
        f"→ Sag objetivo: {sus['sag_mm']} mm ({sus['sag_pct']}%)",
        f"→ Rebote: {sus['rebound_clicks'][0]}–{sus['rebound_clicks'][1]} clics desde cerrado",
    ]
    if sus.get("has_rear_shock"):
        shock = sus.get("shock_type") or "amortiguador"
        lines += [
            "",
            f"🟣 AMORTIGUADOR ({shock})",
            f"→ Sag objetivo: {sus['sag_pct']}% del recorrido",
            "→ Regla de oro rebote: deja caer la bici sobre la rueda trasera desde ~20 cm.",
            "   Debe rebotar UNA sola vez. Dos = cierra clics. Si no recupera altura = abre clics.",
        ]
    return "\n".join(lines)


def format_full(profile: dict, tires: dict, sus: dict) -> str:
    out = format_tires(profile, tires)
    out += "\n\n" + format_suspension(profile, sus)
    out += "\n\n💡 Recuerda: trasera siempre 2–3 psi más alta que delantera."
    if profile.get("terrain") != "Barro":
        out += "\n💡 Con barro bajarías 2 psi en ambas ruedas."
    return out


def format_tires_block(profile: dict, tires: dict) -> str:
    out = format_tires(profile, tires)
    out += "\n\n💡 Recuerda: trasera siempre 2–3 psi más alta que delantera."
    return out


def format_suspension_block(profile: dict, sus: dict) -> str:
    header = f"🔧 TU SETUP DE SUSPENSIÓN — {_bike_label(profile)}"
    return header + "\n\n" + format_suspension(profile, sus)


def format_diagnostic(symptom_label: str, response: str) -> str:
    return f"🩺 *Diagnóstico*\n\nSíntoma: _{symptom_label}_\n\n→ {response}"
