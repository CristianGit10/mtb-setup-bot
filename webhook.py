"""Healthcheck HTTP para Railway/Render.

Antes hospedaba el webhook de Lemon Squeezy. Con Telegram Stars los pagos llegan
por el mismo canal de Telegram (pre_checkout_query + successful_payment),
así que solo necesitamos un endpoint que devuelva 200 OK para el healthcheck.
"""
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def health():
    return {"status": "ok"}
