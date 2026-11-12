import uuid
from .model import identity, number


def positive(value, zero=False):
    result = number(value)
    if result is None or (result < 0 if zero else result <= 0):
        raise ValueError("Usar números finitos positivos; ponto decimal, sem símbolo monetário")
    return result


def register(data, mode, chain, address, entry, quantity, fee, stop, take, now):
    key = identity(chain, address)
    entry, quantity, fee = positive(entry), positive(quantity), positive(fee, True)
    stop, take = positive(stop), positive(take)
    if mode not in ("simulada", "real") or not stop < entry < take:
        raise ValueError("É necessário stop < entrada < objetivo; tipo simulada ou real")
    if len([p for p in data["positions"] if p["remaining"] > 0]) >= 30:
        raise ValueError("Limite de 30 posições abertas")
    position = {"id": uuid.uuid4().hex[:10], "key": key, "mode": mode, "entry": entry,
                "quantity": quantity, "remaining": quantity, "investment": entry * quantity,
                "entry_fee": fee, "stop": stop, "take": take, "opened_at": now,
                "realized_pnl": 0, "sales": []}
    if not all(number(position[n]) is not None for n in ("investment",)):
        raise ValueError("Montante demasiado grande")
    data["positions"].append(position)
    return position


def close(data, position_id, price, quantity, fee, now):
    p = next((p for p in data["positions"] if p["id"] == position_id), None)
    if p is None:
        raise ValueError("Posição não encontrada")
    price, quantity, fee = positive(price), positive(quantity), positive(fee, True)
    if quantity > p["remaining"]:
        raise ValueError("Quantidade superior ao saldo registado")
    pnl = (price - p["entry"]) * quantity - p["entry_fee"] * quantity / p["quantity"] - fee
    if number(pnl) is None or number(p["realized_pnl"] + pnl) is None:
        raise ValueError("Resultado inválido")
    p["remaining"] = max(0, p["remaining"] - quantity)
    p["realized_pnl"] += pnl
    p["sales"].append({"price": price, "quantity": quantity, "fee": fee, "at": now, "pnl": pnl})
    return p, pnl


def estimate(p, price):
    return (price - p["entry"]) * p["remaining"] - p["entry_fee"] * p["remaining"] / p["quantity"]
