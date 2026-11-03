import json
import os
import time
import pika
from domain import connect, consume

role = os.environ['ROLE']
while True:
    db = None
    try:
        db = connect(os.environ['DB'])
        connection = pika.BlockingConnection(
            pika.URLParameters(os.environ['AMQP_URL']))
        ch = connection.channel()
        ch.exchange_declare(exchange='autoservice', exchange_type='topic',
                            durable=True)
        queue = f'ikbo-64-23_nikolaev_{role}'
        ch.queue_declare(queue=queue, durable=True)
        key = 'order.created' if role == 'repairs' else 'repair.completed'
        ch.queue_bind(exchange='autoservice', queue=queue, routing_key=key)
        ch.confirm_delivery()
        while True:
            rows = db.execute('SELECT * FROM outbox WHERE sent=0').fetchall()
            for r in rows:
                ch.basic_publish(exchange='autoservice',
                    routing_key=r['routing'], body=r['body'], mandatory=True,
                    properties=pika.BasicProperties(delivery_mode=2,
                        content_type='application/json', message_id=r['id']))
                with db:
                    db.execute('UPDATE outbox SET sent=1 WHERE id=?', (r['id'],))
            method, properties, body = ch.basic_get(queue, auto_ack=False)
            if method:
                consume(db, json.loads(body), role)
                ch.basic_ack(method.delivery_tag)
            else:
                connection.process_data_events(time_limit=0.2)
    except Exception as e:
        print(type(e).__name__, str(e), flush=True)
        try:
            connection.close()
        except Exception:
            pass
        time.sleep(2)
    finally:
        if db is not None:
            db.close()
