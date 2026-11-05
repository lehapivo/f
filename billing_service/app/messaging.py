"""RabbitMQ: публикация доменных событий и чтение очереди сервиса."""
import asyncio
import json
import logging
import traceback
from typing import Callable

import pika
from aio_pika import ExchangeType, IncomingMessage, connect_robust

from app.settings import settings

log = logging.getLogger("uvicorn.error")


class RabbitPublisher:
    """Публикует событие в topic-обменник autoservice (persistent, с подтверждением)."""

    def publish(self, routing_key: str, payload: dict) -> None:
        connection = pika.BlockingConnection(pika.URLParameters(settings.amqp_url))
        try:
            channel = connection.channel()
            channel.confirm_delivery()
            channel.exchange_declare(exchange=settings.exchange, exchange_type="topic", durable=True)
            channel.basic_publish(
                exchange=settings.exchange,
                routing_key=routing_key,
                body=json.dumps(payload, default=str, ensure_ascii=False).encode(),
                properties=pika.BasicProperties(content_type="application/json",
                                                delivery_mode=pika.DeliveryMode.Persistent),
            )
        finally:
            connection.close()


class MemoryPublisher:
    """Заглушка для unit-тестов: запоминает события вместо отправки."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, dict]] = []

    def publish(self, routing_key: str, payload: dict) -> None:
        self.sent.append((routing_key, payload))

    def keys(self) -> list[str]:
        return [key for key, _ in self.sent]


async def consume(queue_name: str, handlers: dict[str, Callable[[dict], None]]):
    while True:
        try:
            connection = await connect_robust(settings.amqp_url)
            break
        except Exception as exc:  # брокер еще запускается
            log.warning("RabbitMQ is not available yet: %s", exc)
            await asyncio.sleep(2)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)
    exchange = await channel.declare_exchange(settings.exchange, ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue(queue_name, durable=True)
    for routing_key in handlers:
        await queue.bind(exchange, routing_key=routing_key)

    async def process_event(msg: IncomingMessage):
        try:
            data = json.loads(msg.body.decode())
            await asyncio.to_thread(handlers[msg.routing_key], data)
            await msg.ack()
        except Exception:
            traceback.print_exc()
            # одна повторная доставка, затем сообщение отбрасывается
            await msg.nack(requeue=not msg.redelivered)

    await queue.consume(process_event)
    log.info("Started RabbitMQ consuming %s", queue_name)
    return connection
