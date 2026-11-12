import html
from .model import identity
from .positions import register, close, estimate
from .telegram import fmt, stamp

HELP = """<b>Radar — comandos privados</b>
/watch REDE CONTRATO — acompanhar
/unwatch REDE CONTRATO — remover acompanhamento manual
/simulate REDE CONTRATO PREÇO QTD TAXA STOP OBJETIVO
/register real REDE CONTRATO PREÇO QTD TAXA STOP OBJETIVO
/close ID PREÇO QTD TAXA — registar venda manual/simulada
/positions — posições e resultados estimados
/detail REDE CONTRATO — última análise
/health — estado da última verificação
Valores em USD, ponto decimal. Preços de referência, sem ordens.
<a href="https://github.com/jomivelez123456789/memecoin-radar-pro/blob/main/docs/FORMACAO.md">Guia de formação e exercícios</a>
Não enviar frases de recuperação, chaves ou palavras-passe.
Comandos são processados na próxima execução, não em tempo real."""


def process(text, state, config, now):
    args = text.split()
    if not args:
        return HELP
    command = args.pop(0).split("@", 1)[0]
    data = state.data
    if command in ("/start", "/help"):
        return HELP
    if command in ("/watch", "/unwatch") and len(args) == 2:
        key = identity(*args)
        if command == "/watch":
            if key not in data["watched"]:
                if len(data["watched"]) >= 30:
                    raise ValueError("Limite de 30 tokens manuais")
                data["watched"].append(key)
        elif key in data["watched"]:
            data["watched"].remove(key)
        return "Lista manual atualizada. Posições abertas e sinais recentes continuam acompanhados."
    if command in ("/simulate", "/register"):
        mode = "simulada"
        if command == "/register":
            if not args or args.pop(0) != "real":
                raise ValueError("Usar /register real apenas para uma compra já executada manualmente")
            mode = "real"
        if len(args) != 7:
            return HELP
        p = register(data, mode, *args, now)
        return f"Posição {p['mode']} registada: <code>{p['id']}</code>. Nenhuma transação executada."
    if command == "/close" and len(args) == 4:
        p, pnl = close(data, *args, now)
        return f"Venda registada ({p['mode']}). Resultado desta parcela: ${fmt(pnl)}; saldo: {fmt(p['remaining'])}."
    if command == "/positions":
        lines = ["<b>Posições registadas — USD</b>"]
        for p in data["positions"][-30:]:
            snapshot = data["snapshots"].get(p["key"], {})
            price = snapshot.get("price")
            pnl = estimate(p, price) if price is not None and p["remaining"] else None
            lines.append(f"<code>{p['id']}</code> {p['mode']} · {p['key']}\n"
                         f"Saldo {fmt(p['remaining'])} · preço ref. ${fmt(price)} · "
                         f"P/L aberto ${fmt(pnl)} · realizado ${fmt(p['realized_pnl'])}\n"
                         f"Última consulta: {stamp(snapshot.get('observed_at'))}\n"
                         f"Entrada ${fmt(p['entry'])} · taxa entrada ${fmt(p['entry_fee'])} · "
                         f"stop ${fmt(p['stop'])} · objetivo ${fmt(p['take'])}")
        lines.append("Estimativa aberta sem taxa de saída/slippage; preço pode estar desatualizado e não ser executável.")
        return "\n".join(lines)
    if command == "/detail" and len(args) == 2:
        from .engine import evaluate
        key = identity(*args)
        s = data["snapshots"].get(key)
        if not s:
            return "Sem observação. Usa /watch e aguarda a próxima execução."
        a = evaluate(s, config)
        checks = "; ".join(f"{k}: {'sim' if v else 'não'}" for k, v in a["checks"].items())
        return (f"<b>Análise de referência</b>\n<code>{key}</code>\n{html.escape(checks)}\n"
                f"Score {a['score']:g}/100 · compras/vendas 1h: {fmt(s['buys'])}/{fmt(s['sells'])}\n"
                f"Variação 24h {fmt(s['change_h24'], '%')} · idade do par {fmt(s['pool_age_hours'])}h\n"
                f"Última consulta: {stamp(s['observed_at'])}\n"
                f"Ausências: {html.escape(', '.join(a['missing']) or 'campos de mercado completos')}\n"
                "Idade do par não é idade do token. Não há auditoria: holders, baleias, LP, "
                "mint/freeze, honeypots e restrições de venda desconhecidos. Score não é probabilidade de lucro.")
    if command == "/health":
        health = data["health"]
        status = {"ok": "a funcionar", "degradado": "dados incompletos", "falha": "falha na última verificação"}
        return ("<b>Estado do radar</b>\n"
                f"Estado: {status.get(health.get('status'), 'a aguardar primeira verificação')}\n"
                f"Última consulta: {stamp(health.get('last_attempt'))}\n"
                f"Última recolha com dados: {stamp(health.get('last_market_success'))}\n"
                f"Tokens observados: {health.get('observations', 0)} · sem dados: {health.get('missing', 0)}\n"
                f"Sinais nessa consulta: {health.get('signals', 0)}\n"
                "Verificações previstas de 15 em 15 minutos, sujeitas a atrasos. "
                "Este comando descreve a verificação anterior ao processamento da mensagem.")
    return HELP


def consume(telegram, state, config, now):
    for update in telegram.updates(state.data["offset"]):
        update_id = update.get("update_id", -1)
        if update_id < state.data["offset"]:
            continue
        message = update.get("message", {})
        if telegram.authorized(message) and now - message.get("date", 0) <= 86400:
            text = message.get("text", "")
            if text.startswith("/") and len(text) <= 1000:
                try:
                    reply = process(text, state, config, now)
                except (ValueError, TypeError):
                    reply = "Comando inválido. Confirma rede, contrato e valores; usa /help."
                # Save effect and reply together before acknowledging the Telegram update.
                for start in range(0, len(reply), 3500):
                    # Long position lists are sent as plain escaped text, no partial HTML tags.
                    if len(reply) > 3500:
                        import re
                        clean = html.unescape(re.sub(r"</?[^>]+>", "", reply))
                        reply_chunks = [html.escape(clean[i:i + 3000]) for i in range(0, len(clean), 3000)]
                        state.data["outbox"].extend({"text": chunk} for chunk in reply_chunks)
                        break
                    state.data["outbox"].append({"text": reply})
        state.data["offset"] = update_id + 1
        state.save()
