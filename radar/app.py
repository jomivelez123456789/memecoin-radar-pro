import argparse
import html
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
from .views import position_message


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
    if config["max_tracked_tokens"] < 60 + config["discovery_limit"]:
        raise ValueError("A capacidade deve preservar 30 posições, 30 tokens manuais e a descoberta")
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


def scan(state, config, market, now, dry=False, news_http=None):
    data = state.data
    discovered, discovery_errors = market.discover(config["chains"], config["discovery_limit"])
    active = [p for p in data["positions"] if p["remaining"] > 0]
    recent = [key for key, stamp in data["signaled"].items() if now - stamp <= config["signal_watch_hours"] * 3600]
    # Positions and manual watchlist have priority over discovery; never infer ownership from alerts.
    owned_and_manual = list(dict.fromkeys([p["key"] for p in active] + data["watched"]))
    recent = sorted(recent, key=lambda key: data["signaled"][key], reverse=True)
    slots = max(0, config["max_tracked_tokens"] - len(owned_and_manual) - len(discovered))
    tracked = list(dict.fromkeys(owned_and_manual + [key for key in recent if key not in owned_and_manual][:slots]))
    keys = list(dict.fromkeys(tracked + discovered))[:config["max_tracked_tokens"]]
    snapshots, errors = market.fetch(keys, now)
    candidates = []
    for key, s in snapshots.items():
        positions = [p for p in active if p["key"] == key]
        a = evaluate(s, config, data["snapshots"].get(key), key in tracked, positions)
        if a["exit_events"]:
            for event in a["exit_events"]:
                p = next(p for p in positions if p["id"] == event["position_id"])
                version = str(p.get("levels_updated_at", p["opened_at"]))
                candidates.append((0, key, "B — ALERTA DE SAÍDA", [event["reason"]], s, a,
                    p, f"B:position:{p['id']}:{event['kind']}:{version}"))
        elif a["exits"]:
            candidates.append((1, key, "B — ALERTA DE SAÍDA", a["exits"], s, a, None, "B:" + key))
        elif a["risk"] and key in tracked:
            if positions:
                for p in positions:
                    candidates.append((2, key, "C — ALERTA DE RISCO", a["risk"], s, a, p, "C:position:" + p["id"]))
            else:
                candidates.append((2, key, "C — ALERTA DE RISCO", a["risk"], s, a, None, "C:" + key))
        elif a["entry"] and not positions:
            candidates.append((3, key, "A — POSSÍVEL ENTRADA", ["todos os filtros experimentais cumpridos"], s, a, None, "A:" + key))
        data["snapshots"][key] = s
    queued = 0
    notified_positions = set()
    for _, key, category, reasons, s, a, position, cooldown_key in sorted(candidates, key=lambda item: item[0]):
        if now - data["cooldowns"].get(cooldown_key, -1e20) < config["cooldown_hours"] * 3600:
            continue
        if queued >= config["max_alerts_per_run"]:
            break
        message = (position_message(position, s, "🟠 REVER SAÍDA — a tua posição" if category.startswith("B") else "🔴 ATENÇÃO — risco na tua posição", "; ".join(reasons))
                   if position else alert(s, a, category, reasons, config))
        if not dry:
            data["outbox"].append(message)
        data["history"].append({"at": now, "key": key, "category": category, "snapshot": s,
                                "analysis": a, "dry_run": dry,
                                "position_id": position["id"] if position else None,
                                "position_mode": position["mode"] if position else None})
        if not dry:
            data["cooldowns"][cooldown_key] = now
            if category.startswith("A"):
                data["signaled"][key] = now
            if position:
                position["last_update_at"] = now
                notified_positions.add(position["id"])
        queued += 1
    if news_http:
        from .news import refresh, correlate
        refresh(data, news_http, now)
        room = config["max_alerts_per_run"] - queued
        if room > 0:
            for notice in correlate(data, snapshots, config, now, dry, min(2, room)):
                if not dry:
                    data["outbox"].append(notice)
                data["history"].append({"at": now, "key": notice["key"], "category": "D — CONTEXTO DE NOTÍCIA",
                                        "news_id": notice["news_id"], "dry_run": dry})
                queued += 1
    for p in active:
        if queued >= config["max_alerts_per_run"]:
            break
        s = snapshots.get(p["key"])
        if (not s or p["id"] in notified_positions
                or now - p.get("last_update_at", p["opened_at"]) < config.get("position_update_hours", 6) * 3600):
            continue
        if not dry:
            data["outbox"].append(position_message(p, s, "💼 Como está a tua posição",
                "resumo periódico; ausência de novo aviso não prova que a moeda seja segura"))
            p["last_update_at"] = now
        queued += 1
    # Missing quotes never become zero prices or fabricated exits.
    monitored_missing = [key for key in tracked if key not in snapshots]
    if monitored_missing and not dry and now - data["health"].get("missing_notice_at", 0) >= 21600:
        missing_names = "\n".join("• " + html.escape(data["snapshots"].get(key, {}).get("name", key))
                                   for key in monitored_missing[:8])
        data["outbox"].append({"text": "🔴 NÃO CONSIGO AVALIAR ALGUMAS MOEDAS\n"
            f"{len(monitored_missing)} moeda(s) acompanhada(s) sem cotação válida:\n{missing_names}\n"
            "Não é possível avaliar saídas. Consulta /posicoes e verifica manualmente o gráfico. Falta de dados não significa preço zero nem segurança."})
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
        data["outbox"].append({"text": "📡 RADAR EM FUNCIONAMENTO\n"
            f"🔎 Consultei {len(snapshots)} moedas nesta verificação. "
            f"{'Há dados incompletos.' if data['health']['status'] != 'ok' else 'As fontes de mercado responderam.'}\n"
            "💼 Posições abertas continuam acompanhadas; um novo alerta não substitui as anteriores.\n"
            "⏳ Consultas previstas a cada 5 minutos, sujeitas a atrasos; não é vigilância em tempo real.\n"
            "🧭 /ajuda explica tudo. Se não receberes esta confirmação durante 26h, verifica GitHub Actions."})
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
                if state.data["health"].get("commands_version") != 2:
                    try:
                        telegram.call("setMyCommands", {"commands": [
                            {"command": name, "description": description} for name, description in [
                                ("ajuda", "Começar e perceber os alertas"), ("posicoes", "As moedas que registaste"),
                                ("comprar", "Aprender a comprar ou simular"), ("vender", "Aprender a vender"),
                                ("saidas", "Como funcionam os avisos de saída"), ("comprei", "Registar compra manual já feita"),
                                ("simular", "Registar uma compra fictícia"), ("depositar", "Compreender como entram fundos"),
                                ("retirar", "Compreender a saída para o banco"), ("noticias", "Notícias e cobertura disponível"),
                                ("estado", "Estado e hora da última verificação"), ("cancelar", "Cancelar formulário")]]})
                        state.data["health"]["commands_version"] = 2
                    except ApiError:
                        pass
            if telegram_test:
                telegram.call("getMe", {})
                telegram.send("Memecoin Radar Pro: ligação confirmada. Não executa transações. Usa /help.")
                return
            if telegram:
                flush(state, telegram)
                consume(telegram, state, config, time.time())
            result = scan(state, config, Market(http), time.time(), dry, http)
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
