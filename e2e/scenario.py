"""Сквозной сценарий автосервиса через все 8 микросервисов.

Запуск: python e2e/scenario.py  (стенд поднят командой docker compose up -d)
"""
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import requests

HOST = os.getenv("STAND_HOST", "http://localhost")
URL = {name: f"{HOST}:{port}/api" for name, port in [
    ("clients", 8001), ("appointments", 8002), ("orders", 8003), ("diagnostics", 8004),
    ("repairs", 8005), ("warehouse", 8006), ("billing", 8007), ("payments", 8008)]}
T0 = time.monotonic()


def log(step: str, text: str) -> None:
    print(f"[{time.monotonic() - T0:6.2f} s] {step:<13} {text}", flush=True)


def call(method: str, service: str, path: str, expect: int, **kw):
    response = requests.request(method, URL[service] + path, timeout=10, **kw)
    if response.status_code != expect:
        print(f"FAIL {method} {service}{path}: {response.status_code} {response.text}")
        sys.exit(1)
    return response.json()


def wait_for(description: str, probe, timeout: float = 20.0):
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        value = probe()
        if value:
            log("  async", f"{description} ({time.monotonic() - start:.2f} s)")
            return value
        time.sleep(0.2)
    print(f"FAIL timeout: {description}")
    sys.exit(1)


def main() -> None:
    suffix = uuid4().hex[:6].upper()
    # склад: две позиции, вторая отсутствует
    for sku, name, price, qty in [(f"BP-{suffix}", "Колодки тормозные передние", 3500, 10),
                                  (f"BD-{suffix}", "Диск тормозной", 6200, 0)]:
        call("POST", "warehouse", "/parts", 201, json={"sku": sku, "name": name, "price": price, "quantity": qty})
    log("warehouse", f"добавлены запчасти BP-{suffix} (10 шт.) и BD-{suffix} (0 шт.)")

    client = call("POST", "clients", "/clients", 201, json={"full_name": "Седов Александр", "phone": "+79161112233"})
    car = call("POST", "clients", f"/clients/{client['id']}/vehicles", 201, json={
        "vin": f"XTA21700{suffix}001"[:17], "plate": "А123ВС777", "brand": "Lada", "model": "Vesta",
        "year": 2021, "mileage": 42000})
    log("clients", f"клиент {client['id'][:8]}…, автомобиль {car['brand']} {car['model']} {car['plate']}")

    when = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=9, minute=int(suffix, 16) % 60,
                                                                     second=0, microsecond=0)
    appointment = call("POST", "appointments", "/appointments", 201, json={
        "client_id": client["id"], "vehicle_id": car["id"], "scheduled_at": when.isoformat(),
        "reason": "Скрип при торможении"})
    call("POST", "appointments", f"/appointments/{appointment['id']}:confirm", 200)
    log("appointments", f"запись на {when:%d.%m %H:%M} создана (проверка автомобиля в clients) и подтверждена")

    order = call("POST", "orders", "/orders", 201, json={
        "client_id": client["id"], "vehicle_id": car["id"], "appointment_id": appointment["id"],
        "complaint": "Скрип при торможении", "mileage": 42350})
    log("orders", f"заказ-наряд {order['id'][:8]}… создан, status={order['status']}")
    wait_for("appointments: запись -> arrived", lambda: call(
        "GET", "appointments", f"/appointments/{appointment['id']}", 200)["status"] == "arrived")
    diagnostic = wait_for("diagnostics: открыта диагностика по order.created", lambda: (call(
        "GET", "diagnostics", "/diagnostics", 200, params={"order_id": order["id"]}) or [None])[0])

    result = call("POST", "diagnostics", f"/diagnostics/{diagnostic['id']}:complete", 200, json={
        "faults": ["Износ передних колодок", "Износ тормозного диска"],
        "works": [{"code": "W-101", "name": "Замена тормозных колодок", "price": 2500},
                  {"code": "W-102", "name": "Замена тормозного диска", "price": 1800}],
        "parts": [{"sku": f"BP-{suffix}", "qty": 1}, {"sku": f"BD-{suffix}", "qty": 1}]})
    log("diagnostics", "диагностика завершена, цены из warehouse: "
        + ", ".join(f"{p['sku']}={p['price']} (в наличии: {p['in_stock']})" for p in result["parts"]))
    order = wait_for("orders: status=diagnosed по diagnostics.completed", lambda: (lambda o: o if o["status"] == "diagnosed" else None)(
        call("GET", "orders", f"/orders/{order['id']}", 200)))
    log("orders", f"предварительная стоимость {order['estimate']} руб.")

    order = call("POST", "orders", f"/orders/{order['id']}:approve", 200)
    log("orders", f"работы согласованы с клиентом, status={order['status']}")
    repair = wait_for("repairs: ремонт запланирован по order.approved", lambda: (call(
        "GET", "repairs", "/repairs", 200, params={"order_id": order["id"]}) or [None])[0])
    wait_for("repairs: parts_status=shortage по parts.shortage", lambda: call(
        "GET", "repairs", f"/repairs/{repair['id']}", 200)["parts_status"] == "shortage")
    response = requests.post(f"{URL['repairs']}/repairs/{repair['id']}:start", json={"mechanic": "Петров И."})
    log("repairs", f"попытка начать ремонт без запчастей: {response.status_code} {response.json()['error']}")

    purchase = next(p for p in call("GET", "warehouse", "/purchase-orders", 200, params={"status": "ordered", "count": 100})
                    if p["order_id"] == order["id"])
    call("POST", "warehouse", f"/purchase-orders/{purchase['id']}:receive", 200)
    log("warehouse", f"поставка {purchase['sku']} x{purchase['qty']} получена")
    wait_for("repairs: parts_status=reserved по parts.reserved", lambda: call(
        "GET", "repairs", f"/repairs/{repair['id']}", 200)["parts_status"] == "reserved")

    call("POST", "repairs", f"/repairs/{repair['id']}:start", 200, json={"mechanic": "Петров И."})
    call("POST", "repairs", f"/repairs/{repair['id']}:complete", 200, json={"note": "Колодки и диск заменены"})
    log("repairs", "ремонт начат и завершен механиком")
    response = requests.post(f"{URL['repairs']}/repairs/{repair['id']}:complete")
    log("repairs", f"повторное завершение: {response.status_code} {response.json()['error']}")
    wait_for("orders: status=ready по repair.completed", lambda: call(
        "GET", "orders", f"/orders/{order['id']}", 200)["status"] == "ready")
    invoice = wait_for("billing: счет сформирован по order.completed", lambda: (call(
        "GET", "billing", "/invoices", 200, params={"order_id": order["id"]}) or [None])[0])
    log("billing", f"счет {invoice['id'][:8]}… на {invoice['total']} руб., позиций: {len(invoice['lines'])}")
    wait_for("orders: invoice_id сохранен по invoice.issued", lambda: call(
        "GET", "orders", f"/orders/{order['id']}", 200)["invoice_id"] == invoice["id"])
    stock = call("GET", "warehouse", f"/parts/BP-{suffix}", 200)
    log("warehouse", f"после repair.completed: BP-{suffix} остаток {stock['quantity']}, резерв {stock['reserved']}")

    response = requests.post(f"{URL['payments']}/payments", json={"invoice_id": invoice["id"], "amount": 100, "method": "card"})
    log("payments", f"оплата неверной суммы: {response.status_code} {response.json()['error']}")
    payment = call("POST", "payments", "/payments", 201, json={
        "invoice_id": invoice["id"], "amount": invoice["total"], "method": "card"})
    log("payments", f"оплата {payment['amount']} руб. (сумма проверена в billing): {payment['status']}, {payment['external_id']}")
    wait_for("billing: счет оплачен по payment.succeeded", lambda: call(
        "GET", "billing", f"/invoices/{invoice['id']}", 200)["status"] == "paid")
    wait_for("orders: status=paid по invoice.paid", lambda: call(
        "GET", "orders", f"/orders/{order['id']}", 200)["status"] == "paid")

    order = call("POST", "orders", f"/orders/{order['id']}:close", 200, json={"mileage": 42360})
    log("orders", f"автомобиль выдан клиенту, status={order['status']}")
    wait_for("clients: пробег 42360 по order.closed", lambda: call(
        "GET", "clients", f"/vehicles/{car['id']}", 200)["mileage"] == 42360)
    log("result", "СЦЕНАРИЙ ВЫПОЛНЕН")


if __name__ == "__main__":
    main()
