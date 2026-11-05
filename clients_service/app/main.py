import asyncio

from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from app import messaging
from app.database import Base, engine
from app.endpoints.client_router import router as client_router
from app.errors import register_error_handlers
from app.handlers import HANDLERS, QUEUE
import app.schemas.client  # noqa: F401  регистрация таблиц

app = FastAPI(title="Clients Service", version="1.0.0",
              description="Клиенты и их автомобили")
register_error_handlers(app)
app.include_router(client_router, prefix="/api")


@app.get("/health", tags=["Service"])
def health() -> dict:
    return {"status": "ok", "service": "clients"}


@app.on_event("startup")
async def startup() -> None:
    for _ in range(30):
        try:
            Base.metadata.create_all(engine)
            break
        except OperationalError:
            await asyncio.sleep(1)
    asyncio.ensure_future(messaging.consume(QUEUE, HANDLERS))
