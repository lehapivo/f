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

## ПР5: все четыре варианта (`broker_demo/`)

| Вариант | Тип очереди | Обменник | Задержка |
|---|---|---|---|
| 1 | авто-удаляемая | `ikbo-64-23_sedov_v1_topic` (topic) | количество точек в теле |
| 2 | сохраняемая | `ikbo-64-23_sedov_v2_direct` (direct) | длина тела |
| 3 | авто-удаляемая | `ikbo-64-23_sedov_v3_fanout` (fanout) | случайное число 1–5 |
| 4 | сохраняемая | `ikbo-64-23_sedov_v4_direct` (direct) | число в теле |

```bash
python broker_demo/receiver.py 1 repairs "repair.#"     # <вариант> <суффикс очереди> [ключи]
python broker_demo/sender.py 1 repair.brakes.urgent "Замена колодок..."
python broker_demo/receiver.py 3 journal                # fanout: без ключа
python broker_demo/sender.py 3 "" "Ремонт завершен"
```
