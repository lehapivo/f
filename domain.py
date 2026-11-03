import json
import sqlite3
from uuid import uuid4
from datetime import datetime, timezone


def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript('''
    CREATE TABLE IF NOT EXISTS orders (
      id TEXT PRIMARY KEY, client_id TEXT NOT NULL,
      vehicle_id TEXT NOT NULL, complaint TEXT NOT NULL,
      status TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS repairs (
      id TEXT PRIMARY KEY, order_id TEXT UNIQUE NOT NULL,
      status TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS inbox (id TEXT PRIMARY KEY);
    CREATE TABLE IF NOT EXISTS outbox (
      id TEXT PRIMARY KEY, routing TEXT NOT NULL,
      body TEXT NOT NULL, sent INTEGER DEFAULT 0);
    ''')
    return db


def event(db, kind, data):
    e = dict(event_id=str(uuid4()), event_type=kind,
             schema_version=1,
             occurred_at=datetime.now(timezone.utc).isoformat(),
             data=data)
    db.execute('INSERT INTO outbox(id,routing,body) VALUES(?,?,?)',
               (e['event_id'], kind, json.dumps(e)))


def create_order(db, data):
    for key in ('client_id', 'vehicle_id', 'complaint'):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(key)
    from uuid import UUID
    UUID(data['client_id']); UUID(data['vehicle_id'])
    row = dict(id=str(uuid4()), client_id=data['client_id'],
               vehicle_id=data['vehicle_id'],
               complaint=data['complaint'], status='created')
    with db:
        db.execute('INSERT INTO orders VALUES(:id,:client_id,'
                   ':vehicle_id,:complaint,:status)', row)
        event(db, 'order.created', {'order_id': row['id']})
    return row


def consume(db, e, role):
    if e.get('schema_version') != 1:
        raise ValueError('schema_version')
    with db:
        if db.execute('SELECT 1 FROM inbox WHERE id=?',
                      (e['event_id'],)).fetchone():
            return
        if role == 'repairs' and e['event_type'] == 'order.created':
            db.execute('INSERT OR IGNORE INTO repairs VALUES(?,?,?)',
                       (str(uuid4()), e['data']['order_id'], 'created'))
        elif role == 'orders' and e['event_type'] == 'repair.completed':
            cur = db.execute("UPDATE orders SET status='ready' WHERE id=?",
                             (e['data']['order_id'],))
            if cur.rowcount != 1:
                raise ValueError('unknown_order')
        else:
            raise ValueError('event_type')
        db.execute('INSERT INTO inbox VALUES(?)', (e['event_id'],))


def finish_repair(db, repair_id):
    with db:
        row = db.execute('SELECT * FROM repairs WHERE id=?',
                         (repair_id,)).fetchone()
        if row is None:
            raise KeyError(repair_id)
        if row['status'] != 'created':
            raise RuntimeError('already_completed')
        db.execute("UPDATE repairs SET status='completed' WHERE id=?",
                   (repair_id,))
        event(db, 'repair.completed', {'order_id': row['order_id'],
                                      'repair_id': repair_id})
    return dict(db.execute('SELECT * FROM repairs WHERE id=?',
                           (repair_id,)).fetchone())
