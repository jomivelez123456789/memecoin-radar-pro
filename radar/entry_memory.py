"""Prospective hypothesis: persistence and bounded feedback; not a proven strategy."""
VERSION = "public-research-v3-confirmed"


def check(data, snapshot, analysis, now):
    memory = data.setdefault("entry_memory", {})
    key = snapshot["key"]
    previous = memory.get(key)
    reasons = []
    if not analysis["entry"]:
        memory.pop(key, None)
        return []
    if (not previous or not 180 <= now - previous["at"] <= 600
            or previous.get("pair") != snapshot.get("pair")):
        reasons.append("aguardar confirmação noutra consulta do mesmo par (3–10 minutos)")
    recent_losses = [p for p in data.get("paper", {}).get("trades", []) if p["key"] == key
                     and p.get("closed_at") is not None and 0 <= now - p["closed_at"] <= 72 * 3600
                     and p.get("pnl", 0) < 0]
    if len(recent_losses) >= 2:
        reasons.append("duas perdas fictícias neste contrato em 72h; novas calls suspensas até sair dessa janela")
    # An early duplicate invocation does not postpone the first eligible confirmation.
    if not previous or now - previous["at"] >= 180:
        memory[key] = {"at": now, "pair": snapshot.get("pair")}
    for old_key in list(memory):
        if now - memory[old_key]["at"] > 600:
            memory.pop(old_key)
    return reasons
