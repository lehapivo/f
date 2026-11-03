import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4
from domain import connect, create_order, consume, finish_repair


def data():
    return dict(client_id=str(uuid4()), vehicle_id=str(uuid4()), complaint='Шум')


def envelope(kind, **values):
    return dict(event_id=str(uuid4()), schema_version=1,
                event_type=kind, data=values)


class UnitTests(unittest.TestCase):
    def test_empty_complaint(self):
        db = Mock()
        d = data(); d['complaint'] = ' '
        with self.assertRaises(ValueError):
            create_order(db, d)
        db.execute.assert_not_called()

    def test_invalid_uuid(self):
        db = Mock(); d = data(); d['client_id'] = 'invalid'
        with self.assertRaises(ValueError):
            create_order(db, d)
        db.execute.assert_not_called()

    def test_unknown_schema(self):
        db = Mock()
        with self.assertRaises(ValueError):
            consume(db, {'schema_version': 2}, 'repairs')
        db.execute.assert_not_called()


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.orders = connect(str(Path(self.temp.name) / 'orders.db'))
        self.repairs = connect(str(Path(self.temp.name) / 'repairs.db'))

    def tearDown(self):
        self.orders.close(); self.repairs.close(); self.temp.cleanup()

    def test_order_and_outbox(self):
        order = create_order(self.orders, data())
        e = json.loads(self.orders.execute('SELECT body FROM outbox').fetchone()[0])
        self.assertEqual(e['data']['order_id'], order['id'])
        self.assertEqual(order['status'], 'created')

    def test_duplicate_event(self):
        e = envelope('order.created', order_id=str(uuid4()))
        consume(self.repairs, e, 'repairs'); consume(self.repairs, e, 'repairs')
        self.assertEqual(self.repairs.execute('SELECT COUNT(*) FROM repairs').fetchone()[0], 1)
        self.assertEqual(self.repairs.execute('SELECT COUNT(*) FROM inbox').fetchone()[0], 1)

    def test_full_business_cycle(self):
        order = create_order(self.orders, data())
        e = json.loads(self.orders.execute('SELECT body FROM outbox').fetchone()[0])
        consume(self.repairs, e, 'repairs')
        rid = self.repairs.execute('SELECT id FROM repairs').fetchone()[0]
        finish_repair(self.repairs, rid)
        e = json.loads(self.repairs.execute('SELECT body FROM outbox').fetchone()[0])
        consume(self.orders, e, 'orders')
        self.assertEqual(self.orders.execute('SELECT status FROM orders').fetchone()[0], 'ready')

    def test_repeated_completion(self):
        consume(self.repairs, envelope('order.created', order_id=str(uuid4())), 'repairs')
        rid = self.repairs.execute('SELECT id FROM repairs').fetchone()[0]
        finish_repair(self.repairs, rid)
        with self.assertRaises(RuntimeError):
            finish_repair(self.repairs, rid)
        self.assertEqual(self.repairs.execute('SELECT COUNT(*) FROM outbox').fetchone()[0], 1)

    def test_missing_repair(self):
        with self.assertRaises(KeyError):
            finish_repair(self.repairs, str(uuid4()))

    def test_unknown_order_rolls_back(self):
        with self.assertRaises(ValueError):
            consume(self.orders, envelope('repair.completed', order_id=str(uuid4())), 'orders')
        self.assertEqual(self.orders.execute('SELECT COUNT(*) FROM inbox').fetchone()[0], 0)

    def test_persistence(self):
        order = create_order(self.orders, data())
        other = connect(str(Path(self.temp.name) / 'orders.db'))
        self.assertEqual(other.execute('SELECT id FROM orders').fetchone()[0], order['id'])
        other.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
