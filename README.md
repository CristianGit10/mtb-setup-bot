# MTB Setup Bot

Bot de Telegram que calcula presiones de neumáticos y ajustes de suspensión para riders de MTB según peso, disciplina, tipo de bici y terreno.

## Funciones

- 🛞 Presiones de rueda (delantera + trasera) ajustadas por anchura, tubeless, insertos, terreno y tipo de bici.
- ⚙️ Suspensión: presión de horquilla aproximada, sag objetivo en mm y clics de rebote desde cerrado.
- 🩺 Diagnóstico por síntomas (rebota, eructa, hunde en frenadas, toca fondo…).
- 📇 Perfil persistido en Supabase: la siguiente vez te pregunta solo el terreno del día.
- 💳 Pagos vía Lemon Squeezy (Free 3 consultas/mes · Pro 4,99€ · Tiendas 29€).

## Stack

- Python 3.11 + `python-telegram-bot` 21 (async, polling)
- Supabase para perfiles y contadores
- FastAPI/uvicorn para el webhook de Lemon Squeezy
- Deploy: Railway o Render (un solo proceso, polling + webhook en el mismo puerto)

## Instalación local

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # rellena los valores reales
python main.py
```

## Configuración

### 1. Telegram

Crea el bot con [@BotFather](https://t.me/BotFather), copia el token a `TELEGRAM_BOT_TOKEN`.

Comandos sugeridos (BotFather → /setcommands):

```
start - Empezar a configurar la bici
perfil - Ver mi perfil guardado
plan - Ver mi plan y consultas restantes
cancel - Cancelar la conversación actual
```

### 2. Supabase

1. Crea un proyecto en [supabase.com](https://supabase.com).
2. SQL Editor → pega el contenido de `supabase_schema.sql` y ejecuta.
3. Settings → API → copia `URL` (→ `SUPABASE_URL`) y `service_role key` (→ `SUPABASE_SERVICE_KEY`).

> El bot usa la *service_role* key porque corre en servidor. Nunca la expongas en cliente.

### 3. Lemon Squeezy

1. Crea dos productos en Lemon Squeezy: **MTB Pro** (4,99€/mes) y **MTB Tiendas** (29€/mes).
2. Copia los IDs de variante a `LEMON_SQUEEZY_VARIANT_PRO` y `LEMON_SQUEEZY_VARIANT_SHOP`.
3. Copia los enlaces de checkout a `LEMON_SQUEEZY_CHECKOUT_URL_PRO` y `..._SHOP`.
4. Settings → Webhooks → nuevo webhook:
   - URL: `https://TU-DOMINIO/lemon-squeezy/webhook`
   - Eventos: `order_created`, `subscription_created`, `subscription_updated`, `subscription_cancelled`, `subscription_resumed`, `subscription_expired`, `subscription_paused`
   - Copia el secret → `LEMON_SQUEEZY_WEBHOOK_SECRET`.
5. **Importante:** al crear los enlaces de checkout añade el `telegram_user_id` como custom data:
   - URL de ejemplo: `https://tutienda.lemonsqueezy.com/checkout/buy/UUID?checkout[custom][telegram_user_id]=123456789`
   - Si quieres botones genéricos (mismos para todos los usuarios), añade un paso intermedio que genere el enlace con el ID del usuario antes de mostrarlo. Una mejora futura es enviar enlaces personalizados desde el propio bot.

### 4. Deploy

#### Railway

1. Crea proyecto desde el repo.
2. Variables → pega las del `.env.example` con los valores reales.
3. Railway asigna `PORT` automáticamente; el `Procfile` ya lo gestiona.
4. El servicio quedará accesible por HTTPS en `*.up.railway.app` — usa esa URL para el webhook.

#### Render

1. Nuevo *Web Service* desde el repo, runtime Python.
2. Build command: `pip install -r requirements.txt`
3. Start command: `python main.py`
4. Añade las variables de entorno.
5. Render asigna `PORT` automáticamente.

## Comandos del bot

- `/start` — abre el menú principal
- `/perfil` — muestra el perfil guardado
- `/plan` — muestra plan actual y consultas restantes
- `/cancel` — sale de la conversación

## Estructura

```
.
├── main.py                 # entrypoint (polling + webhook)
├── config.py               # variables de entorno
├── db.py                   # wrapper Supabase
├── logic.py                # cálculos (ruedas + suspensión + diagnóstico)
├── formatting.py           # plantillas de respuesta con emojis
├── webhook.py              # FastAPI app para Lemon Squeezy
├── handlers/
│   ├── conversation.py     # ConversationHandler completo
│   ├── keyboards.py        # teclados inline
│   └── states.py           # constantes de estado
├── supabase_schema.sql
├── requirements.txt
├── Procfile
├── runtime.txt
└── .env.example
```

## Notas de cálculo

- Las tablas de presión base son para **tubeless**; con cámara se suman 4 psi.
- Si la diferencia trasera/delantera baja de 2 psi tras ajustes, la trasera se fuerza a delantera + 2 psi.
- El sag se da en mm y porcentaje. La presión de horquilla es un punto de partida (≈ peso en lbs). Ajustar siempre con el o-ring tras 3-4 compresiones.
- Para horquillas RockShox la presión es la indicada; para Fox suele ser ligeramente inferior — siempre verifica con la pegatina de la horquilla.

## Próximas mejoras (no implementadas)

- Generación dinámica de checkouts con `telegram_user_id` por usuario.
- Pre-prefijo personalizado en `bot_name` para plan Tiendas.
- Stats por usuario (consultas mensuales gráficas).
- Recordatorios de revisión de suspensión cada X km.
