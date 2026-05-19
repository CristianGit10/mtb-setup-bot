import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

PORT = int(os.getenv("PORT", "8080"))

FREE_MONTHLY_QUERIES = 3

# --- Pagos con Telegram Stars (currency code XTR) ---
# Pago ÚNICO de por vida. 1 star ≈ $0.013 USD ≈ €0.012.
STARS_PRO_PRICE = int(os.getenv("STARS_PRO_PRICE", "2000"))    # ≈ €25 (lifetime Pro)
STARS_SHOP_PRICE = int(os.getenv("STARS_SHOP_PRICE", "5000"))  # ≈ €65 (lifetime Tiendas)

# Identificadores del payload de la factura (para distinguir pro vs shop)
INVOICE_PAYLOAD_PRO = "lifetime:pro"
INVOICE_PAYLOAD_SHOP = "lifetime:shop"
