"""Entry point: arranca el bot de Telegram (polling) y el webhook (FastAPI) en paralelo."""
import asyncio
import logging
import signal

import uvicorn
from telegram.ext import Application

from config import TELEGRAM_BOT_TOKEN, PORT
from handlers import conversation, payments
from webhook import app as fastapi_app


logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("mtb-bot")


async def run() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN en el entorno")

    application: Application = (
        Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    )
    conversation.register(application)
    payments.register(application)

    # Webhook server
    server = uvicorn.Server(
        uvicorn.Config(fastapi_app, host="0.0.0.0", port=PORT, log_level="info")
    )

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    log.info("Bot iniciado (polling). Webhook escuchando en :%d", PORT)

    stop_event = asyncio.Event()

    def _stop(*_):
        stop_event.set()

    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _stop)
    except NotImplementedError:
        pass

    server_task = asyncio.create_task(server.serve())
    stop_task = asyncio.create_task(stop_event.wait())

    done, _ = await asyncio.wait(
        {server_task, stop_task},
        return_when=asyncio.FIRST_COMPLETED,
    )

    log.info("Apagando...")
    server.should_exit = True
    await application.updater.stop()
    await application.stop()
    await application.shutdown()
    for t in (server_task, stop_task):
        if not t.done():
            t.cancel()


if __name__ == "__main__":
    asyncio.run(run())
