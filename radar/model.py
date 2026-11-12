import math
import re
from urllib.parse import quote

CHAINS = {"solana", "base", "ethereum"}
CAIP = {"solana": "solana:4sGjMW1sUnHzSxGspuhpqLDx6wiyjNtZ/spl:",
        "base": "eip155:8453/erc20:", "ethereum": "eip155:1/erc20:"}


def identity(chain, address):
    if chain not in CHAINS or not isinstance(address, str):
        raise ValueError("Rede ou contrato inválido")
    if chain == "solana":
        alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        if not re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", address):
            raise ValueError("Endereço Solana inválido")
        value = 0
        for char in address:
            value = value * 58 + alphabet.index(char)
        length = (value.bit_length() + 7) // 8 + len(address) - len(address.lstrip("1"))
        if length != 32:
            raise ValueError("Endereço Solana deve representar 32 bytes")
    elif not re.fullmatch(r"0x[0-9a-fA-F]{40}", address):
        raise ValueError("Endereço EVM inválido")
    else:
        address = address.lower()
    return f"{chain}:{address}"


def number(value):
    if isinstance(value, bool):
        return None
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (ValueError, TypeError, OverflowError):
        return None


def links(chain, address, pair=None):
    key = identity(chain, address)
    address = key.split(":", 1)[1]
    chart = f"https://dexscreener.com/{chain}/{quote(pair or address, safe='')}"
    return {"chart": chart, "app": "https://phantom.com/ul/v1/fungible?token=" +
            quote(CAIP[chain] + address, safe=""), "contract": address}


def normalize(pair, chain, address, now):
    key = identity(chain, address)
    if pair.get("chainId") != chain:
        return None
    try:
        if identity(chain, pair.get("baseToken", {}).get("address")) != key:
            return None
    except ValueError:
        return None
    token = pair.get("baseToken", {})
    volume = pair.get("volume") or {}
    changes = pair.get("priceChange") or {}
    tx = (pair.get("txns") or {}).get("h1") or {}
    created = number(pair.get("pairCreatedAt"))
    age = (now - created / 1000) / 3600 if created else None
    result = {"key": key, "chain": chain, "address": key.split(":", 1)[1],
              "name": str(token.get("name", "?"))[:60], "symbol": str(token.get("symbol", "?"))[:20],
              "price": number(pair.get("priceUsd")), "liquidity": number((pair.get("liquidity") or {}).get("usd")),
              "volume_h1": number(volume.get("h1")), "volume_h24": number(volume.get("h24")),
              "change_h1": number(changes.get("h1")), "change_h24": number(changes.get("h24")),
              "buys": number(tx.get("buys")), "sells": number(tx.get("sells")),
              "pool_age_hours": age if age is not None and age >= 0 else None,
              "observed_at": now, "pair": pair.get("pairAddress"), "source": "DexScreener"}
    for name in ("price", "liquidity", "volume_h1", "volume_h24", "buys", "sells"):
        if result[name] is not None and result[name] < 0:
            result[name] = None
    if result["price"] == 0:
        result["price"] = None
    # Historical candles and timestamp of last trade are not supplied by this endpoint.
    return result
