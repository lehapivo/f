import asyncio

from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from app.database import Base, engine
from app.endpoints.payment_router import router as payment_router
from app.errors import register_error_handlers
import app.schemas.payment  # noqa: F401  регистрация таблиц

app = FastAPI(title="Payments Service", version="1.0.0", description="Прием оплаты по счетам")
register_error_handlers(app)
app.include_router(payment_router, prefix="/api")


@app.get("/health", tags=["Service"])
def health() -> dict:
    return {"status": "ok", "service": "payments"}


@app.on_event("startup")
async def startup() -> None:
    # сервис только публикует события, собственной очереди у него нет
    for _ in range(30):
        try:
            Base.metadata.create_all(engine)
            break
        except OperationalError:
            await asyncio.sleep(1)
