import argparse
import json
import math
import time
from pathlib import Path
from .commands import consume
from .engine import evaluate
from .http import Http, ApiError
from .market import Market
from .state import State
from .telegram import Telegram, alert


def load_config(path="config.json"):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if not set(config["chains"]) <= {"solana", "base", "ethereum"}:
        raise ValueError("Redes inválidas")
    for key, value in config.items():
        if key != "chains" and (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or (value < 0 and key not in ("exit_change_h1", "min_change_h1"))):
            raise ValueError("Configuração numérica inválida")
    if not 1 <= config["max_alerts_per_run"] <= 20 or not 1 <= config["discovery_limit"] <= 30:
        raise ValueError("Limites de alertas/descoberta inválidos")
    return config


def flush(state, telegram):
    while state.data["outbox"]:
        item = state.data["outbox"][0]
        if item.get("expires_at", float("inf")) < time.time():
            # Never deliver a delayed market signal as though it were current.
            state.data["outbox"].pop(0)
            state.save()
            continue
        telegram.send(item["text"], item.get("buttons"))
        state.data["outbox"].pop(0)
        state.save()


def scan(state, config, market, now, dry=False):
    data = state.data
    discovered, discovery_errors = market.discover(config["chains"], config["discovery_limit"])
    active = [p for p in data["positions"] if p["remaining"] > 0]
    recent = [key for key, stamp in data["signaled"].items() if now - stamp <= config["signal_watch_hours"] * 3600]
    # Positions and manual watchlist have priority over discovery; never infer ownership from alerts.
    tracked = list(dict.fromkeys([p["key"] for p in active] + data["watched"] + recent))
    keys = list(dict.fromkeys(tracked + discovered))[:config["max_tracked_tokens"]]
    snapshots, errors = market.fetch(keys, now)
    candidates = []
    for key, s in snapshots.items():
        positions = [p for p in active if p["key"] == key]
        a = evaluate(s, config, data["snapshots"].get(key), key in tracked, positions)
        if a["exits"]:
            candidates.append((0, key, "B — ALERTA DE SAÍDA", a["exits"], s, a))
        elif a["risk"] and key in tracked:
            candidates.append((1, key, "C — ALERTA DE RISCO", a["risk"], s, a))
        elif a["entry"]:
            candidates.append((2, key, "A — POSSÍVEL ENTRADA", ["todos os filtros experimentais cumpridos"], s, a))
        data["snapshots"][key] = s
    queued = 0
    for _, key, category, reasons, s, a in sorted(candidates, key=lambda item: item[0]):
        cooldown_key = category[0] + ":" + key
        if now - data["cooldowns"].get(cooldown_key, -1e20) < config["cooldown_hours"] * 3600:
            continue
        if queued >= config["max_alerts_per_run"]:
            break
        message = alert(s, a, category, reasons, config)
        if not dry:
            data["outbox"].append(message)
        data["history"].append({"at": now, "key": key, "category": category, "snapshot": s,
                                "analysis": a, "dry_run": dry})
        if not dry:
            data["cooldowns"][cooldown_key] = now
            if category.startswith("A"):
                data["signaled"][key] = now
        queued += 1
    # Missing quotes never become zero prices or fabricated exits.
    monitored_missing = [key for key in tracked if key not in snapshots]
    if monitored_missing and not dry and now - data["health"].get("missing_notice_at", 0) >= 21600:
        data["outbox"].append({"text": "C — ALERTA DE RISCO / DADOS AUSENTES\n"
            f"{len(monitored_missing)} token(s) acompanhado(s) sem cotação válida. "
            "Não é possível avaliar saídas. Consulta /positions e verifica manualmente o gráfico."})
        data["health"]["missing_notice_at"] = now
    data["history"] = data["history"][-5000:]
    data["signaled"] = {key: at for key, at in data["signaled"].items()
                         if now - at <= config["signal_watch_hours"] * 3600}
    data["cooldowns"] = {key: at for key, at in data["cooldowns"].items()
                          if now - at <= max(config["cooldown_hours"] * 3600, 86400)}
    data["snapshots"] = {key: s for key, s in data["snapshots"].items()
                          if key in tracked or key in keys}
    data["health"].update({"last_attempt": now, "observations": len(snapshots), "missing": len(errors),
                            "discovery_errors": discovery_errors, "signals": queued,
                            "status": "degradado" if errors or discovery_errors else "ok"})
    if snapshots:
        data["health"]["last_market_success"] = now
    if not snapshots:
        state.save()
        raise ApiError("Nenhuma observação válida; execução degradada")
    if not dry and now - data["health"].get("heartbeat_at", 0) >= 86400:
        data["outbox"].append({"text": "Radar ativo — verificação periódica concluída. "
            f"Observações: {len(snapshots)}. Estado: {data['health']['status']}. "
            "Se não receberes esta confirmação durante 26h, verifica GitHub Actions. Usa /health."})
        data["health"]["heartbeat_at"] = now
    state.save()
    return {"observations": len(snapshots), "missing": len(errors), "signals": queued,
            "discovery_errors": discovery_errors}


def run(path="data/state.json", dry=False, telegram_test=False):
    state, config, http = State(path), load_config(), Http()
    telegram = None
    with state.lock():
        try:
            if not dry:
                telegram = Telegram(http)
            if telegram_test:
                telegram.call("getMe", {})
                telegram.send("Memecoin Radar Pro: ligação confirmada. Não executa transações. Usa /help.")
                return
            if telegram:
                flush(state, telegram)
                consume(telegram, state, config, time.time())
            result = scan(state, config, Market(http), time.time(), dry)
            if telegram:
                flush(state, telegram)
            print(json.dumps(result, ensure_ascii=False))
        except Exception:
            state.data["health"].update({"last_failure": time.time(), "status": "falha"})
            state.save()
            if telegram:
                try:
                    telegram.send("Radar: a verificação falhou. Consulta GitHub Actions. "
                                  "Os alertas podem estar atrasados; não dependas deles para uma saída.")
                except Exception:
                    pass
            raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Dados reais sem Telegram; estado separado")
    parser.add_argument("--telegram-test", action="store_true")
    parser.add_argument("--state")
    args = parser.parse_args()
    try:
        run(args.state or ("data/dry-run.json" if args.dry_run else "data/state.json"),
            args.dry_run, args.telegram_test)
    except Exception as error:
        # No exception body: libraries can include credential-bearing URLs.
        print(f"Falha controlada ({type(error).__name__}). Verifica configuração/conectividade; segredos omitidos.")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
