"""ПР5, вариант 1: поставщик публикует сообщение в topic-обменник.

Запуск: python sender.py <routing_key> "<тело сообщения>"
Ключ маршрутизации: <вид работ>.<узел>.<срочность>, например repair.brakes.urgent
"""
import sys

import pika

EXCHANGE = "ikbo-64-23_sedov_topic"

connect = pika.BlockingConnection(pika.ConnectionParameters(
    "localhost", 5672, credentials=pika.PlainCredentials("guest", "guest")))
channel = connect.channel()
channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic")

routing_key, body = sys.argv[1], sys.argv[2]
channel.basic_publish(exchange=EXCHANGE, routing_key=routing_key, body=body.encode())
print(f" [>] SENT {routing_key}: {body}", flush=True)
connect.close()
