from datetime import datetime, timezone
from typing import Optional

from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_KEY, FREE_MONTHLY_QUERIES


_client: Optional[Client] = None


def supabase() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_SERVICE_KEY en el entorno")
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def _current_month_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_ts(ts) -> Optional[datetime]:
    if not ts:
        return None
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


def get_or_create_user(telegram_user_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> dict:
    res = supabase().table("users").select("*").eq("telegram_user_id", telegram_user_id).execute()
    if res.data:
        user = res.data[0]
        return _check_and_expire_plan(user)
    new_user = {
        "telegram_user_id": telegram_user_id,
        "username": username,
        "first_name": first_name,
        "plan": "free",
        "queries_this_month": 0,
        "month_key": _current_month_key(),
    }
    res = supabase().table("users").insert(new_user).execute()
    return res.data[0]


def get_user(telegram_user_id: int) -> Optional[dict]:
    res = supabase().table("users").select("*").eq("telegram_user_id", telegram_user_id).execute()
    if res.data:
        return _check_and_expire_plan(res.data[0])
    return None


def _check_and_expire_plan(user: dict) -> dict:
    """Si el plan Pro/Shop venció, lo revierte a free. Mutates and returns user."""
    if user.get("plan") not in ("pro", "shop"):
        return user
    exp = _parse_ts(user.get("plan_renewal_at"))
    if exp and exp < datetime.now(timezone.utc):
        supabase().table("users").update({"plan": "free"}).eq(
            "telegram_user_id", user["telegram_user_id"]
        ).execute()
        user["plan"] = "free"
    return user


PROFILE_FIELDS = (
    "weight_kg", "discipline", "bike_type",
    "front_width", "rear_width",
    "front_tubeless", "rear_tubeless",
    "front_insert", "rear_insert",
    "fork_brand", "fork_travel", "shock_type",
    "riding_style",
)


def save_profile(telegram_user_id: int, profile: dict) -> None:
    update = {k: profile[k] for k in PROFILE_FIELDS if k in profile and profile[k] is not None}
    if not update:
        return
    update["profile_updated_at"] = _now_iso()
    supabase().table("users").update(update).eq("telegram_user_id", telegram_user_id).execute()


def has_saved_profile(user: dict) -> bool:
    return bool(user and user.get("weight_kg") and user.get("discipline"))


def can_make_query(user: dict) -> tuple[bool, int]:
    """Devuelve (puede_consultar, consultas_restantes_si_aplica)."""
    if user.get("plan") in ("pro", "shop"):
        return True, -1
    month_key = _current_month_key()
    if user.get("month_key") != month_key:
        return True, FREE_MONTHLY_QUERIES
    used = user.get("queries_this_month") or 0
    remaining = max(0, FREE_MONTHLY_QUERIES - used)
    return remaining > 0, remaining


def increment_query_count(telegram_user_id: int) -> None:
    user = get_user(telegram_user_id)
    if not user:
        return
    if user.get("plan") in ("pro", "shop"):
        return
    month_key = _current_month_key()
    if user.get("month_key") != month_key:
        supabase().table("users").update({
            "queries_this_month": 1,
            "month_key": month_key,
        }).eq("telegram_user_id", telegram_user_id).execute()
    else:
        supabase().table("users").update({
            "queries_this_month": (user.get("queries_this_month") or 0) + 1,
        }).eq("telegram_user_id", telegram_user_id).execute()


def activate_stars_plan(telegram_user_id: int, plan: str, charge_id: str, expires_at: datetime) -> None:
    """Activa plan Pro o Shop tras un pago con Telegram Stars."""
    supabase().table("users").update({
        "plan": plan,
        "telegram_stars_charge_id": charge_id,
        "plan_renewal_at": expires_at.astimezone(timezone.utc).isoformat(),
    }).eq("telegram_user_id", telegram_user_id).execute()
