#!/usr/bin/env bash
# End-to-end check of the running Compose stack: order -> repair -> complete -> ready.
set -euo pipefail
ORDERS=${ORDERS:-http://localhost:8001}
REPAIRS=${REPAIRS:-http://localhost:8002}
json() { python3 -c "import json,sys; d=json.load(sys.stdin); print($1)"; }
wait_for() { for _ in $(seq 1 60); do curl -sf "$1" >/dev/null && return 0; sleep 1; done; echo "timeout: $1"; exit 1; }

wait_for "$ORDERS/health"; wait_for "$REPAIRS/health"
ORDER=$(curl -sf -X POST "$ORDERS/api/orders" -H 'Content-Type: application/json' \
  -d '{"client_id":"11111111-1111-4111-8111-111111111111","vehicle_id":"22222222-2222-4222-8222-222222222222","complaint":"Noise when braking"}')
OID=$(echo "$ORDER" | json "d['id']"); echo "order created: $OID"

RID=""
for _ in $(seq 1 60); do
  RID=$(curl -sf "$REPAIRS/api/repairs?limit=100" | json "next((r['id'] for r in d if r['order_id']=='$OID'), '')")
  [ -n "$RID" ] && break; sleep 1
done
[ -n "$RID" ] || { echo "FAIL: repair was not created by order.created"; exit 1; }
echo "repair created: $RID"

curl -sf -X POST "$REPAIRS/api/repairs/$RID/complete" | json "d['status']" | grep -qx completed
echo "repair completed"

for _ in $(seq 1 60); do
  STATUS=$(curl -sf "$ORDERS/api/orders/$OID" | json "d['status']")
  [ "$STATUS" = ready ] && break; sleep 1
done
[ "$STATUS" = ready ] || { echo "FAIL: order status is $STATUS"; exit 1; }
echo "order status: ready"

CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$REPAIRS/api/repairs/$RID/complete")
[ "$CODE" = 409 ] || { echo "FAIL: repeated completion returned $CODE"; exit 1; }
echo "repeated completion: 409"
echo "E2E OK"
