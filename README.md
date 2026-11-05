# Автосервис — микросервисная система (ПР5–8, ИКБО-64-23)

Восемь микросервисов на Python 3.12 (FastAPI, Pydantic, SQLAlchemy), PostgreSQL 16 и RabbitMQ 3.13.
Сервисы выделены из ограниченных контекстов Event Storming (ПР1–4).

| Сервис | Порт | Контекст | Синхронный вызов |
|---|---|---|---|
| clients_service | 8001 | Клиенты и автомобили | — |
| appointments_service | 8002 | Запись на обслуживание | clients: проверка автомобиля |
| orders_service | 8003 | Заказ-наряды | clients: проверка автомобиля и пробега |
| diagnostics_service | 8004 | Диагностика | warehouse: цена и наличие запчастей |
| repairs_service | 8005 | Ремонт | — |
| warehouse_service | 8006 | Склад и заказ запчастей | — |
| billing_service | 8007 | Счета | — |
| payments_service | 8008 | Платежи | billing: сумма и статус счета |

Асинхронные события публикуются в topic-обменник `autoservice`, у каждого сервиса своя долговечная
очередь `autoservice.<сервис>`.

## Запуск

```bash
docker compose up --build -d --wait   # PostgreSQL, RabbitMQ и 8 сервисов
python e2e/scenario.py                # сквозной сценарий от записи до выдачи автомобиля
```

Документация API: `http://localhost:800N/docs`. Панель RabbitMQ: `http://localhost:15672` (guest/guest).

## Тесты

```bash
./run_tests.sh tests/unit
TEST_POSTGRES_URL=postgresql://autoservice:autoservice@localhost:5432/autoservice_test ./run_tests.sh tests/integration
./run_tests.sh tests/component        # при запущенном стенде
```

## ПР5, вариант 1 (`broker_demo/`)

Авто-удаляемые очереди `ikbo-64-23_sedov_*`, обменник `ikbo-64-23_sedov_topic` (topic),
задержка обработки равна числу точек в теле сообщения.

```bash
python broker_demo/receiver.py repairs "repair.#"
python broker_demo/sender.py repair.brakes.urgent "Замена колодок..."
```
