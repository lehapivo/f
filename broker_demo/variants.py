"""ПР5: параметры четырех вариантов из таблицы 1 методических указаний."""
import random
import re

GROUP = "ikbo-64-23_sedov"            # <группа>_<фамилия>


def dots(body: str) -> int:           # вариант 1: количество точек в теле
    return body.count(".")


def length(body: str) -> int:         # вариант 2: длина тела (символов)
    return len(body)


def random_delay(body: str) -> int:   # вариант 3: случайное число в диапазоне [1, 5]
    return random.randint(1, 5)


def number(body: str) -> int:         # вариант 4: число, переданное в теле
    match = re.search(r"\d+", body)
    return int(match.group()) if match else 0


VARIANTS = {
    1: {"type": "topic", "durable": False, "auto_delete": True, "delay": dots},
    2: {"type": "direct", "durable": True, "auto_delete": False, "delay": length},
    3: {"type": "fanout", "durable": False, "auto_delete": True, "delay": random_delay},
    4: {"type": "direct", "durable": True, "auto_delete": False, "delay": number},
}
for n, v in VARIANTS.items():
    v["exchange"] = f"{GROUP}_v{n}_{v['type']}"
    v["queue_prefix"] = f"{GROUP}_v{n}"
