"""Ensaio prospetivo em EUR; nunca envia ordens nem mistura posições manuais."""
import html
import uuid
import copy
import os
from .fx import valid as valid_fx
from .model import number, links
from .telegram import stamp

RULES = {"initial": 1000.0, "budget": 100.0, "max_open": 5,
         "fee": .01, "slippage": .01, "fixed_fee": .05,
         "stop": .10, "take": .20, "max_hold_hours": 48}


def eur(value):
    return "por apurar" if value is None else f"{value:,.2f}".replace(",", " ").replace(".", ",") + " €"


def pct(value):
    return "sem resultados" if value is None else f"{value:+.2f}%".replace(".", ",")


def opened(data):
    return [p for p in data.get("paper", {}).get("trades", []) if p.get("closed_at") is None]


def start(data, now, config=None):
    if "paper" not in data:
        data["paper"] = {"version": 1, "currency": "EUR", "running": True,
                         "started_at": now, "rules": dict(RULES), "cash": RULES["initial"],
                         "trades": [], "calls": 0, "skipped": 0, "skip_log": [],
                         "observations": 0, "last_scan": None, "last_summary": 0,
                         "signal_config_at_start": copy.deepcopy(config or {}),
                         "source_commit": os.environ.get("GITHUB_SHA", "local")}
    data["paper"]["running"] = True
    return report(data, now)


def quote(s, fx, now):
    price = number(s.get("price")) if s else None
    observed = number(s.get("observed_at")) if s else None
    liquidity = number(s.get("liquidity")) if s else None
    if (not valid_fx(fx, now) or price is None or price <= 0 or observed is None
            or not 0 <= now - observed <= 900 or liquidity is None or liquidity <= 0):
        return None
    converted = number(price / number(fx["usd_per_eur"]))
    return converted if converted is not None and converted > 0 else None


def proceeds(p, price, rules):
    # A paper sale assumes execution. It cannot prove on-chain sellability.
    value = number(p["quantity"] * price * (1 - rules["slippage"]) * (1 - rules["fee"]) - rules["fixed_fee"])
    return round(value, 2) if value is not None and value >= 0 else None


def statistics(data, now):
    book = data["paper"]; rules = book["rules"]; fx = data.get("fx", {})
    closed = [p for p in book["trades"] if p.get("closed_at") is not None]
    wins = sum(p["pnl"] > 1e-8 for p in closed)
    losses = sum(p["pnl"] < -1e-8 for p in closed)
    active = opened(data); marked = []; unresolved = 0
    for p in active:
        price = quote(data["snapshots"].get(p["key"]), fx, now)
        value = proceeds(p, price, rules) if price is not None else None
        if value is None:
            unresolved += 1
        else:
            marked.append(value)
    equity = None if unresolved else number(book["cash"] + sum(marked))
    if equity is None and active:
        unresolved = max(unresolved, 1)
    return {"closed": len(closed), "wins": wins, "losses": losses,
            "draws": len(closed) - wins - losses, "open": len(active), "unresolved": unresolved,
            "win_rate": 100 * wins / len(closed) if closed else None,
            "realized": sum(p["pnl"] for p in closed), "equity": equity,
            "pnl": equity - rules["initial"] if equity is not None else None,
            "return": 100 * (equity / rules["initial"] - 1) if equity is not None else None}


def report(data, now):
    if "paper" not in data:
        return "🧪 O teste automático ainda não começou. /teste_iniciar cria 1 000 € fictícios; não deposita nem compra nada."
    book = data["paper"]; r = book["rules"]; s = statistics(data, now); fx = data.get("fx", {})
    accuracy = "sem calls fechadas" if s["win_rate"] is None else f"{s['win_rate']:.1f}%".replace(".", ",")
    cash_only = s["pnl"] if s["pnl"] is not None else None
    result = "ganho" if cash_only is not None and cash_only > 0 else "perda" if cash_only is not None and cash_only < 0 else "resultado"
    details = []
    for p in opened(data):
        price = quote(data["snapshots"].get(p["key"]), fx, now)
        value = proceeds(p, price, r) if price is not None else None
        pnl = value - p["budget"] if value is not None else None
        details.append(f"• {html.escape(p['name'][:64])}: {eur(pnl)} estimados")
    recent = [p for p in book["trades"] if p.get("closed_at") is not None][-3:]
    details += [f"• Encerrada: {html.escape(p['name'][:64])}: {eur(p['pnl'])} ({pct(100*p['pnl']/p['budget'])})" for p in recent]
    detail_text = "\n" + "\n".join(details) + "\n" if details else ""
    return ("🧪 <b>TESTE AUTOMÁTICO — SALDO FICTÍCIO EM EUROS</b>\n"
            f"🕒 Início: {stamp(book['started_at'])}\n"
            f"💶 Saldo inicial: {eur(r['initial'])}\n💵 Disponível: {eur(book['cash'])}\n"
            f"💼 Saldo total estimado, incluindo abertas: <b>{eur(s['equity'])}</b>\n"
            f"📊 {result.capitalize()} total estimado: {eur(s['pnl'])} ({pct(s['return'])})\n"
            f"🏁 Resultado só das calls fechadas: {eur(s['realized'])}\n\n"
            f"🎯 <b>Taxa de acerto: {accuracy}</b>\n"
            f"✅ {s['wins']} com lucro · ❌ {s['losses']} com perda · ➖ {s['draws']} empatadas\n"
            f"⏳ {s['open']} abertas · ❔ {s['unresolved']} sem avaliação atual\n"
            f"📬 Calls A desde o início: {book['calls']} · não simuladas por limites/dados: {book['skipped']}\n"
            f"🔎 Observações de mercado: {book['observations']} · última avaliação: {stamp(book.get('last_scan'))}\n\n"
            f"{detail_text}"
            + (f"🔎 Cobertura da pesquisa ampliada em {stamp(book['research_changes'][-1]['at'])}; saldo e histórico preservados.\n" if book.get("research_changes") else "") +
            "💡 1 acerto em 1 call fechada = 100% de acerto; não é duplicar o saldo. "
            "Abertas não contam como vitórias. Sem calls, não há prova de rentabilidade.\n"
            f"🧮 Regras fixas: até {eur(r['budget'])}/call, máximo {r['max_open']} abertas; "
            f"limite de cotação −{r['stop']*100:g}% / objetivo de cotação +{r['take']*100:g}% em EUR, saída por risco ou após {r['max_hold_hours']}h. "
            "São movimentos da cotação antes dos custos, não limites garantidos do ganho/perda líquido.\n"
            f"Custos fictícios em CADA lado: {r['fee']*100:g}% + {eur(r['fixed_fee'])}; "
            f"desvio desfavorável de {r['slippage']*100:g}%. Não são tarifas reais verificadas.\n"
            f"💱 BCE: {html.escape(fx.get('date', 'indisponível'))}; referência diária, não taxa de execução bancária.\n"
            "⚠️ Cotações não garantem compra/venda. Intervalos e falta de liquidez podem impedir executar. "
            "Resultados teóricos, sem carteira nem garantia de lucro.\n"
            f"{'▶️ Novas simulações ativas.' if book['running'] else '⏸️ Sem novas entradas; abertas continuam acompanhadas.'} "
            "/resultados · /teste_parar")


def step(data, snapshots, analyses, calls, now):
    book = data.get("paper")
    if not book:
        return []
    r = book["rules"]; fx = data.get("fx", {}); events = []
    book["observations"] += len(snapshots); book["last_scan"] = now
    # Close only at the NEXT available observed quote, never at an invented stop fill.
    for p in opened(data):
        s = snapshots.get(p["key"]); price = quote(s, fx, now)
        if price is None:
            continue
        if now - p.get("last_observed_at", p["opened_at"]) > 900:
            p["monitoring_gap"] = True
        if s.get("pair") and p.get("entry_pair") and s["pair"] != p["entry_pair"]:
            p["pair_changed"] = True
        p["last_observed_at"] = now
        risks = [x for x in analyses.get(p["key"], {}).get("risk", []) if not x.startswith("subida extrema")]
        reason = ("limite de perda ultrapassado" if price <= p["stop"] else
                  "objetivo atingido" if price >= p["take"] else
                  "risco de mercado: " + "; ".join(risks) if risks else
                  "prazo máximo de observação" if now - p["opened_at"] >= r["max_hold_hours"] * 3600 else None)
        if reason:
            net = proceeds(p, price, r)
            if net is None or number(book["cash"] + net) is None:
                continue
            book["cash"] += net
            p.update({"closed_at": now, "exit_quote_eur": price, "exit_fx": dict(fx),
                      "proceeds": net, "pnl": round(net - p["budget"], 2), "reason": reason,
                      "exit_evidence": {"pair": s.get("pair"), "observed_at": s.get("observed_at"),
                                        "risk": list(risks)}})
            outcome = "✅ GANHO FICTÍCIO" if p["pnl"] > 1e-8 else "❌ PERDA FICTÍCIA" if p["pnl"] < -1e-8 else "➖ EMPATE FICTÍCIO"
            events.append({"text": f"🧪 <b>{outcome} — CALL ENCERRADA</b>\n🪙 {html.escape(p['name'])}\n"
                           f"💡 {html.escape(reason)}\nResultado após custos assumidos: <b>{eur(p['pnl'])}</b> "
                           f"({pct(100*p['pnl']/p['budget'])} desta call).\n"
                           + ("⚠️ Houve intervalo sem cotação; usei o preço observado no regresso, não o limite ideal.\n" if p.get("monitoring_gap") else "")
                           + "Não foi feita uma transação. /resultados mostra todas as contas.",
                           "buttons": [[{"text": "📈 Gráfico desta call", "url": p["chart"]}]]})
    for key in calls:
        book["calls"] += 1
        s = snapshots[key]; price = quote(s, fx, now)
        active = opened(data)
        fill = number(price * (1 + r["slippage"])) if price is not None else None
        quantity = number((r["budget"] - r["fixed_fee"]) / (1 + r["fee"]) / fill) if fill else None
        reason = ("teste pausado" if not book["running"] else "já existe call aberta nesta moeda" if any(p["key"] == key for p in active)
                  else "limite de posições abertas" if len(active) >= r["max_open"] else "saldo fictício insuficiente" if book["cash"] + 1e-8 < r["budget"]
                  else "câmbio/cotação/liquidez indisponível" if price is None or not quantity or number(price * (1+r["take"])) is None else None)
        if reason:
            book["skipped"] += 1
            book["skip_log"].append({"key": key, "at": now, "reason": reason})
            book["skip_log"] = book["skip_log"][-1000:]
            continue
        p = {"id": uuid.uuid4().hex[:10], "key": key, "name": s["name"], "opened_at": now,
             "research_version": data.get("research", {}).get("version", "original"),
             "entry_pair": s.get("pair"),
             "entry_evidence": {"analysis": copy.deepcopy(analyses.get(key, {})),
                                "snapshot": copy.deepcopy(s),
                                "source_commit": os.environ.get("GITHUB_SHA", "local")},
             "entry_quote_eur": price, "entry_fill_eur": fill, "entry_fx": dict(fx),
             "budget": r["budget"], "quantity": quantity, "stop": price * (1-r["stop"]),
             "take": price * (1+r["take"]), "closed_at": None, "last_observed_at": now,
             "chart": links(s["chain"], s["address"], s.get("pair"))["chart"]}
        book["cash"] -= r["budget"]; book["trades"].append(p)
        events.append({"text": "🧪 <b>ENTRADA FICTÍCIA — TESTE AUTOMÁTICO</b>\n"
                       f"🪙 {html.escape(p['name'])}\nEsta call A passou os filtros e entrou no ensaio.\n"
                       f"💶 Montante: {eur(p['budget'])}, incluindo custos de entrada assumidos.\n"
                       "Vou acompanhar a saída automaticamente neste teste. Não comprei nada numa carteira.\n"
                       f"🆔 <code>{p['id']}</code> · /resultados", "expires_at": now + 1800,
                       "buttons": [[{"text": "📈 Gráfico desta call", "url": p["chart"]}]]})
    if events or now - book.get("last_summary", 0) >= 21600:
        events.append({"text": report(data, now)})
        book["last_summary"] = now
    return events
