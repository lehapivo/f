# Автосервис: заказ-наряды и ремонт (практические работы №5–8)

Два микросервиса (orders, repairs) на Python + SQLite, обмен событиями через RabbitMQ (outbox/inbox).

```bash
docker compose up --build -d          # RabbitMQ, 2 HTTP-сервиса, 2 worker
./e2e_test.sh                         # сквозной сценарий заказ → ремонт → ready
python -m unittest -v                 # 3 unit + 7 интеграционных тестов
TASK=1 MODE=receive python broker_demo.py   # задание RabbitMQ, вариант 1
```
