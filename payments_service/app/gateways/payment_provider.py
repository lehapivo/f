"""Внешняя платежная система (учебная заглушка)."""
from uuid import uuid4


class PaymentProvider:
    LIMIT = 1_000_000

    def charge(self, amount: int, method: str) -> tuple[bool, str]:
        if method == "card" and amount > self.LIMIT:
            return False, "limit_exceeded"
        return True, f"PS-{uuid4().hex[:10].upper()}"
