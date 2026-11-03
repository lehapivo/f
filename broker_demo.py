import os
import sys
import time
import pika

# Variant 1. TASK=1 or 2; MODE=send or receive.
task = int(os.getenv('TASK', '1'))
mode = os.getenv('MODE', 'receive')
url = os.getenv('AMQP_URL', 'amqp://student:student@localhost:5672/')
c = pika.BlockingConnection(pika.URLParameters(url))
ch = c.channel()
name = f'ikbo-64-23_nikolaev_t{task}_v1'
if task == 1:
    # Only the receiver owns and declares the exclusive queue.
    if mode == 'receive':
        ch.queue_declare(queue=name, exclusive=True)
    exchange, key, persistent, symbol = '', name, False, '#'
else:
    exchange, key, persistent, symbol = name + '_exchange', '', True, '#'
    ch.exchange_declare(exchange=exchange, exchange_type='fanout', durable=True)
    ch.queue_declare(queue=name, durable=True)
    ch.queue_bind(queue=name, exchange=exchange)
if mode == 'send':
    message = ' '.join(sys.argv[1:]) or 'repair'
    ch.confirm_delivery()
    ch.basic_publish(exchange=exchange, routing_key=key, body=message.encode(),
        mandatory=True, properties=pika.BasicProperties(
            delivery_mode=2 if persistent else 1))
    print('SENT', message)
else:
    ch.basic_qos(prefetch_count=1)
    def handle(channel, method, props, body):
        text = body.decode()
        if task == 2:
            time.sleep(text.count(symbol))
        print('DONE', text, flush=True)
        channel.basic_ack(method.delivery_tag)
    ch.basic_consume(queue=name, on_message_callback=handle, auto_ack=False)
    ch.start_consuming()
c.close()
