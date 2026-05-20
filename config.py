import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

PORT = int(os.getenv("PORT", "8080"))

FREE_MONTHLY_QUERIES = 3

# --- Pagos con PayPal (manual) ---
# El usuario paga al enlace y el dueño activa el plan con /grant.
PAYPAL_ME_LINK = os.getenv("PAYPAL_ME_LINK", "https://paypal.me/CristianDuque315")
PRO_PRICE_EUR = os.getenv("PRO_PRICE_EUR", "3")

# Solo este usuario puede usar los comandos de admin (/grant, /revoke).
OWNER_TELEGRAM_ID = int(os.getenv("OWNER_TELEGRAM_ID", "700883093"))
