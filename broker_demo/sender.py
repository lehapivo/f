"""ПР5: поставщик публикует сообщение в обменник варианта.

Запуск: python sender.py <вариант> <ключ маршрутизации> "<тело сообщения>"
"""
import sys

import pika

from variants import VARIANTS

v = VARIANTS[int(sys.argv[1])]
routing_key, body = sys.argv[2], sys.argv[3]

connect = pika.BlockingConnection(pika.ConnectionParameters(
    "localhost", 5672, credentials=pika.PlainCredentials("guest", "guest")))
channel = connect.channel()
channel.exchange_declare(exchange=v["exchange"], exchange_type=v["type"], durable=v["durable"])
# для сохраняемых очередей сообщение тоже должно быть сохраняемым
properties = pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent) if v["durable"] else None
channel.basic_publish(exchange=v["exchange"], routing_key=routing_key, body=body.encode(), properties=properties)
print(f" [>] SENT {routing_key or '(без ключа)'}: {body}", flush=True)
connect.close()
