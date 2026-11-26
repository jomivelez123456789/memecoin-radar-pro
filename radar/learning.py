"""Auditable feedback from actual paper outcomes, separate from service incidents."""
import html
import copy
from collections import Counter
from .model import number
from .telegram import stamp


def recover_entries(data, now):
    """Recover only uniquely matched original alerts, never infer missing evidence."""
    count = 0
    for p in data.get("paper", {}).get("trades", []):
        if p.get("entry_evidence"):
            continue
        matches = [h for h in data.get("history", []) if h.get("category", "").startswith("A")
                   and not h.get("dry_run") and h.get("key") == p["key"]
                   and abs(h.get("at", 0) - p["opened_at"]) < 0.001 and h.get("snapshot")]
        if len(matches) != 1:
            continue
        event = matches[0]
        p["entry_evidence"] = {"snapshot": copy.deepcopy(event["snapshot"]),
                               "analysis": copy.deepcopy(event.get("analysis", {})),
                               "recovered_from_original_alert_at": event["at"], "recovered_at": now}
        p["entry_pair"] = event["snapshot"].get("pair")
        count += 1
    return count


def metrics(data):
    closed = [p for p in data.get("paper", {}).get("trades", []) if p.get("closed_at") is not None]
    gains = sum(p["pnl"] for p in closed if p["pnl"] > 0)
    losses = -sum(p["pnl"] for p in closed if p["pnl"] < 0)
    gross = sum(p["budget"] * (p["exit_quote_eur"] / p["entry_quote_eur"] - 1) for p in closed)
    return {"closed": len(closed), "gains": gains, "losses": losses,
            "realized": gains - losses, "gross_without_costs": gross,
            "cost_drag": gross - gains + losses, "profit_factor": gains / losses if losses else None}


def incident(data, now, kind, host=None, status=None):
    log = data.setdefault("learning", {})
    log.setdefault("started_at", now)
    events = log.setdefault("incidents", [])
    item = {"at": now, "kind": kind}
    # Fixed categories and allowlisted provider only; never save exception bodies/URLs.
    from .http import Http
    if host in Http.HOSTS:
        item["host"] = host
    if isinstance(status, int) and 100 <= status <= 599:
        item["status"] = status
    events.append(item)
    del events[:-200]


def review(data, now):
    data.setdefault("learning", {}).setdefault("started_at", now)
    recover_entries(data, now)
    new = 0
    for p in data.get("paper", {}).get("trades", []):
        if p.get("closed_at") is None or p.get("review"):
            continue
        pnl = number(p.get("pnl"))
        if pnl is None:
            continue
        entry, exit_price, budget = (number(p.get(field)) for field in ("entry_quote_eur", "exit_quote_eur", "budget"))
        without_costs = number(budget * (exit_price / entry - 1)) if entry and exit_price and budget else None
        p["review"] = {"at": now, "outcome": "ganho" if pnl > 1e-8 else "perda" if pnl < -1e-8 else "empate",
                       "pnl_eur": pnl, "market_without_costs_eur": without_costs,
                       "cost_drag_eur": round(without_costs - pnl, 2) if without_costs is not None else None,
                       "monitoring_gap": bool(p.get("monitoring_gap")),
                       "entry_evidence_available": bool(p.get("entry_evidence")),
                       "cohort": p.get("research_version", "original")}
        new += 1
    if not new:
        return None
    return "🧠 <b>REVISÃO AUTOMÁTICA CONCLUÍDA</b>\n" + f"Analisei {new} nova(s) call(s) fictícia(s) encerrada(s), incluindo perdas e custos.\n" + view(data, now)


def view(data, now):
    from .paper import eur
    book = data.get("paper", {})
    closed = [p for p in book.get("trades", []) if p.get("closed_at") is not None]
    reviewed = [p for p in closed if p.get("review")]
    losses = [p for p in reviewed if p["review"]["outcome"] == "perda"]
    incidents = data.get("learning", {}).get("incidents", [])
    recent_incidents = [e for e in incidents if 0 <= now - e["at"] <= 86400]
    gaps = sum(p["review"]["monitoring_gap"] for p in reviewed)
    m = metrics(data)
    lines = ["🧠 <b>O QUE OS RESULTADOS NOS ENSINAM</b>",
             f"🕒 Consulta: {stamp(now)}",
             f"🧪 {len(closed)} calls fictícias fechadas · {len(reviewed)} revistas · {len(losses)} com perda.",
             "Uma perda não prova erro de entrada; um ganho também não valida uma estratégia.",
             f"🛠️ Falhas de execução/intervalos registados nas últimas 24h: {len(recent_incidents)} "
             "(histórico limitado aos 200 incidentes mais recentes; não equivale a perdas de trading)."]
    lines.append(f"Registo técnico iniciado em {stamp(data.get('learning', {}).get('started_at'))}; "
                 "não reconstrói todos os incidentes antigos. Zero registos não prova ausência de falhas.")
    if closed:
        lines.append(f"\n💸 Calls fechadas: {eur(m['realized'])} após custos assumidos. "
                     f"Cenário teórico sem custos: {eur(m['gross_without_costs'])}; diferença {eur(m['cost_drag'])}. "
                     "Isto não são comissões reais medidas; não retiro custos para apresentar lucro.")
        if m["profit_factor"] is not None:
            lines.append(f"⚖️ Ganhos/perdas em valor: {m['profit_factor']:.2f}. Abaixo de 1, as perdas superam os ganhos.")
    if not reviewed:
        lines.append("\n⏳ Ainda não há resultados fechados revistos. Não invento lições de trading nem taxas de sucesso. "
                     "As calls abertas só serão avaliadas depois de fecharem.")
    else:
        groups = Counter(p["review"]["cohort"] for p in reviewed)
        lines.append(f"\n📚 {len(groups)} versão(ões) de pesquisa registada(s); os resultados ficam separados por versão:")
        for cohort, count in groups.most_common(5):
            subset = [p for p in reviewed if p["review"]["cohort"] == cohort]
            wins = sum(p["review"]["outcome"] == "ganho" for p in subset)
            lines.append(f"• {html.escape(cohort)}: {count} fechadas, {wins} com ganho, resultado {eur(sum(p['pnl'] for p in subset))}.")
        lines.append(f"🕳️ {gaps} call(s) fechada(s) tiveram intervalo superior a 15 minutos entre cotações observadas. "
                     "Isto limita a avaliação das saídas; não prova que o atraso tenha causado a perda.")
        for p in reviewed[-3:]:
            r = p["review"]
            lines.append(f"\n• {html.escape(p['name'][:60])}: {eur(p['pnl'])}. "
                         f"Saída observada: {html.escape(p.get('reason', 'não registada')[:150])}.\n"
                         f"Diferença para um cenário teórico sem custos: {eur(r['cost_drag_eur'])}; "
                         + ("justificação da entrada guardada." if r["entry_evidence_available"] else "registo antigo sem justificação completa da entrada."))
        if len(reviewed) < 30:
            lines.append("\n🔬 Amostra pequena: menos de 30 calls fechadas. Não há evidência suficiente para escolher uma estratégia vencedora.")
    if recent_incidents:
        counts = Counter(e["kind"] for e in recent_incidents)
        lines.append("\n🔧 Incidentes observados: " + "; ".join(f"{html.escape(k)}: {v}" for k, v in counts.items()) + ".")
    lines.append("\n📋 A revisão é automática e descritiva: guarda a evidência de entrada e confronta-a com a saída. "
                 "Não treina uma IA nem altera filtros com base em poucos resultados. Qualquer experiência futura precisa de uma versão nova, "
                 "testada com dados posteriores; o histórico anterior fica preservado. /aprender · /resultados")
    return "\n".join(lines)
