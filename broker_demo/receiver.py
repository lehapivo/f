"""ПР5: потребитель читает очередь варианта, привязанную к обменнику.

Запуск: python receiver.py <вариант> <суффикс очереди> [<ключ привязки> ...]
"""
import sys
from datetime import datetime
from time import sleep

import pika

from variants import VARIANTS

v = VARIANTS[int(sys.argv[1])]
QUEUE = f"{v['queue_prefix']}_{sys.argv[2]}"
BINDINGS = sys.argv[3:] or [""]          # fanout не использует ключ

connect = pika.BlockingConnection(pika.ConnectionParameters(
    "localhost", 5672, credentials=pika.PlainCredentials("guest", "guest")))
channel = connect.channel()
channel.exchange_declare(exchange=v["exchange"], exchange_type=v["type"], durable=v["durable"])
# вариант 1, 3: авто-удаляемая очередь; вариант 2, 4: сохраняемая при перезапуске брокера
channel.queue_declare(queue=QUEUE, durable=v["durable"], auto_delete=v["auto_delete"])
for key in BINDINGS:
    channel.queue_bind(exchange=v["exchange"], queue=QUEUE, routing_key=key)
channel.basic_qos(prefetch_count=1)


def now() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def delayed_callback(ch, method, properties, body):
    text = body.decode()
    delay = v["delay"](text)
    print(f"{now()} [x] Received {method.routing_key or '-'}: {text} (задержка {delay} с)", flush=True)
    sleep(delay)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(f"{now()} [x] Done", flush=True)


channel.basic_consume(queue=QUEUE, on_message_callback=delayed_callback)
print(f"{now()} [*] {QUEUE} <- {v['exchange']} ({v['type']}): {', '.join(BINDINGS) or '-'}", flush=True)
try:
    channel.start_consuming()
except KeyboardInterrupt:
    connect.close()
