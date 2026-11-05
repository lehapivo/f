"""ПР5, вариант 1: потребитель читает авто-удаляемую очередь, привязанную к topic-обменнику.

Запуск: python receiver.py <суффикс очереди> <шаблон привязки> [<шаблон> ...]
Задержка обработки (с) = количество точек в теле сообщения.
"""
import sys
from datetime import datetime
from time import sleep

import pika

EXCHANGE = "ikbo-64-23_sedov_topic"
QUEUE = f"ikbo-64-23_sedov_{sys.argv[1]}"
BINDINGS = sys.argv[2:]

connect = pika.BlockingConnection(pika.ConnectionParameters(
    "localhost", 5672, credentials=pika.PlainCredentials("guest", "guest")))
channel = connect.channel()
channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic")
# авто-удаляемая очередь: несколько потребителей, удаляется после отключения последнего
channel.queue_declare(queue=QUEUE, auto_delete=True)
for pattern in BINDINGS:
    channel.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=pattern)
channel.basic_qos(prefetch_count=1)


def now() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def delayed_callback(ch, method, properties, body):
    text = body.decode()
    delay = text.count(".")
    print(f"{now()} [x] Received {method.routing_key}: {text} (задержка {delay} с)", flush=True)
    sleep(delay)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(f"{now()} [x] Done {method.routing_key}", flush=True)


channel.basic_consume(queue=QUEUE, on_message_callback=delayed_callback)
print(f"{now()} [*] {QUEUE} <- {', '.join(BINDINGS)}", flush=True)
try:
    channel.start_consuming()
except KeyboardInterrupt:
    connect.close()
