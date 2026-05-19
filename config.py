import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

PORT = int(os.getenv("PORT", "8080"))

FREE_MONTHLY_QUERIES = 3

# --- Pagos con Telegram Stars (currency code XTR) ---
# Precio en stars (no en céntimos). 1 star ≈ $0.013 USD ≈ €0.012.
STARS_PRO_PRICE = int(os.getenv("STARS_PRO_PRICE", "500"))   # ≈ €4.99-€6 con IAP
STARS_SHOP_PRICE = int(os.getenv("STARS_SHOP_PRICE", "2500"))  # ≈ €29-€31

# Periodo de suscripción en segundos. Telegram exige 30 días = 2592000.
STARS_SUBSCRIPTION_PERIOD = 2592000

# Identificadores del payload de la factura (para distinguir pro vs shop)
INVOICE_PAYLOAD_PRO = "subscription:pro"
INVOICE_PAYLOAD_SHOP = "subscription:shop"
