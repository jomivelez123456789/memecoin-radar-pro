"""Regras experimentais; score ordinal, sem probabilidades ou promessa de lucro."""


def evaluate(s, config, previous=None, tracked=False, positions=()):
    missing = [name for name in ("price", "liquidity", "volume_h1", "volume_h24", "buys", "sells",
                                "change_h1", "pool_age_hours") if s.get(name) is None]
    total = (s.get("buys") or 0) + (s.get("sells") or 0)
    ratio = s["buys"] / total if total and s.get("buys") is not None else None
    # Compare the last hour to the previous 23 hours, not an overlapping 24h average.
    prior_volume = (s.get("volume_h24") or 0) - (s.get("volume_h1") or 0)
    relative = s["volume_h1"] / (prior_volume / 23) if (prior_volume > 0
        and s.get("volume_h1") is not None and (s.get("pool_age_hours") or 0) >= 24) else None
    if relative is None:
        missing.append("volume relativo (histórico insuficiente/inconsistente)")
    risk, exits = [], []
    if s.get("liquidity") is not None and s["liquidity"] < config["min_liquidity_usd"]:
        risk.append("liquidez abaixo do mínimo")
    if s.get("change_h1") is not None and s["change_h1"] <= config["exit_change_h1"]:
        risk.append("queda acentuada em 1h")
    if s.get("change_h1") is not None and s["change_h1"] > config["max_change_h1"]:
        risk.append("subida extrema; possível manipulação/FOMO")
    if previous and previous.get("pair") == s.get("pair") and previous.get("liquidity") and s.get("liquidity") is not None:
        if s["liquidity"] <= previous["liquidity"] * (1 - config["liquidity_drop_fraction"]):
            risk.append("queda de liquidez entre observações do mesmo par")
    if tracked and risk:
        exits.extend(reason for reason in risk if not reason.startswith("subida extrema"))
    for p in positions:
        price = s.get("price")
        if price is not None and (price <= p["stop"] or price >= p["take"]):
            exits.append(f"posição {p['id']} ({p['mode']}): nível de referência atingido")
    checks = {
        "liquidez": s.get("liquidity") is not None and s["liquidity"] >= config["min_liquidity_usd"],
        "volume": s.get("volume_h1") is not None and s["volume_h1"] >= config["min_volume_h1"],
        "idade do par": s.get("pool_age_hours") is not None and s["pool_age_hours"] >= config["min_age_hours"],
        "atividade": total >= config["min_transactions_h1"],
        "pressão compradora": ratio is not None and ratio >= config["min_buy_ratio"],
        "momentum": s.get("change_h1") is not None and config["min_change_h1"] <= s["change_h1"] <= config["max_change_h1"],
        "volume relativo": relative is not None and relative >= config["min_relative_volume"],
        "dados completos": not missing,
    }
    score = sum(12.5 for value in checks.values() if value)
    # All guards are mandatory even if the score threshold is lowered.
    entry = all(checks.values()) and score >= config["entry_score"] and not risk and not exits
    return {"entry": entry, "risk": risk, "exits": exits, "score": score,
            "buy_ratio": ratio, "relative_volume": relative, "missing": missing,
            "checks": checks, "risk_class": "MUITO ELEVADO" if risk or missing else "ELEVADO — contrato não auditado"}
