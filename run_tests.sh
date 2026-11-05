#!/usr/bin/env bash
# Локальный запуск тестов всех сервисов: unit, integration (нужен TEST_POSTGRES_URL),
# component (нужен поднятый стенд docker compose up -d).
set -e
port=8001
for s in clients appointments orders diagnostics repairs warehouse billing payments; do
  echo "== ${s}_service"
  (cd ${s}_service && SERVICE_URL=${SERVICE_URL_BASE:-http://localhost}:$port \
     CLIENTS_SERVICE_URL=${SERVICE_URL_BASE:-http://localhost}:8001 python -m pytest -q -p no:cacheprovider "$@")
  port=$((port + 1))
done
