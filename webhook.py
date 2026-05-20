"""Healthcheck HTTP para Railway/Render.

Los pagos son por PayPal manual (el dueño activa el plan con /grant), así que no
hay webhook de pago. Solo necesitamos un endpoint que devuelva 200 OK para el
healthcheck del hosting (y para que un pinger lo mantenga despierto en planes free).
"""
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def health():
    return {"status": "ok"}
