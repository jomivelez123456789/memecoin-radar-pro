import html
from .model import identity
from .positions import register, close, estimate
from .telegram import fmt, stamp
from .education import page
from .views import position_message, token_buttons, money

HELP = page("ajuda")


def process(text, state, config, now):
    args = text.split()
    if not args:
        return HELP
    command = args.pop(0).split("@", 1)[0]
    data = state.data
    command = {"/ajuda": "/help", "/posicoes": "/positions", "/estado": "/health",
               "/acompanhar": "/watch"}.get(command, command)
    if command in ("/start", "/help"):
        return {"text": HELP, "buttons": [[{"text": "🛒 Aprender a comprar", "callback_data": "help:comprar"},
                     {"text": "💸 Aprender a vender", "callback_data": "help:vender"}],
                     [{"text": "🎯 Avisos de saída", "callback_data": "help:saidas"}]]}
    if command[1:] in ("comprar", "vender", "depositar", "retirar", "saidas"):
        return page(command[1:])
    if command == "/cancelar":
        data.pop("form", None)
        return "🛑 Formulário cancelado. Não mexi em posições nem carteiras."
    if command in ("/comprei", "/simular"):
        from .forms import choose, begin
        kind = "buy" if command == "/comprei" else "sim"
        if len(args) == 2:
            return begin(data, kind, now, key=identity(*args))
        return choose(data, kind)
    if command == "/noticias":
        from .news import news_view
        return news_view(data, now)
    if command == "/tecnico":
        return ("🔧 <b>Comandos completos, opcionais</b>\n"
                "/watch REDE CONTRATO\n/unwatch REDE CONTRATO\n"
                "/simulate REDE CONTRATO PREÇO QTD TAXA STOP OBJETIVO\n"
                "/register real REDE CONTRATO PREÇO QTD TAXA STOP OBJETIVO\n"
                "/close ID PREÇO QTD TAXA\n/detail REDE CONTRATO\n"
                "Valores em USD; ponto decimal nestes comandos. Para começar usa os botões e /ajuda.")
    if command in ("/watch", "/unwatch") and len(args) == 2:
        key = identity(*args)
        if command == "/watch":
            if key not in data["watched"]:
                if len(data["watched"]) >= 30:
                    raise ValueError("Limite de 30 tokens manuais")
                data["watched"].append(key)
        elif key in data["watched"]:
            data["watched"].remove(key)
        return "👀 Lista de observação atualizada. Posições abertas continuam acompanhadas até registares o encerramento. Observar não significa comprar."
    if command in ("/simulate", "/register"):
        mode = "simulada"
        if command == "/register":
            if not args or args.pop(0) != "real":
                raise ValueError("Usar /register real apenas para uma compra já executada manualmente")
            mode = "real"
        if len(args) != 7:
            return HELP
        p = register(data, mode, *args, now)
        return position_message(p, data["snapshots"].get(p["key"]), "✅ Posição registada — vou acompanhá-la")
    if command == "/close" and len(args) == 4:
        p, pnl = close(data, *args, now)
        message = position_message(p, data["snapshots"].get(p["key"]), "✅ Venda registada — sem executar transações")
        message["text"] += f"\n🧮 Resultado desta parcela: {money(pnl)}."
        return message
    if command == "/positions":
        opened = [p for p in data["positions"] if p["remaining"] > 0]
        closed = [p for p in data["positions"] if p["remaining"] == 0][-3:]
        cards = [position_message(p, data["snapshots"].get(p["key"])) for p in opened + closed]
        return [{"text": f"💼 <b>As tuas posições</b>\n{len(opened)} aberta(s), acompanhadas em simultâneo. "
                          f"Mostro também até 3 encerradas. {len(data['watched'])} moeda(s) só em observação.\n"
                          "Só estão aqui compras/simulações que registaste; não adivinho o que tens na carteira."}] + cards
    if command == "/detail" and len(args) == 2:
        from .engine import evaluate
        key = identity(*args)
        s = data["snapshots"].get(key)
        if not s:
            return "Sem observação. Usa /watch e aguarda a próxima execução."
        a = evaluate(s, config)
        checks = "\n".join(f"{'✅' if v else '⚪'} {k}: {'cumpre o filtro' if v else 'não cumpre ou faltam dados'}" for k, v in a["checks"].items())
        ratio = a["buy_ratio"] * 100 if a["buy_ratio"] is not None else None
        return {"text": (f"🔎 <b>Porque apareceu esta moeda?</b>\n<code>{key}</code>\n\n{html.escape(checks)}\n\n"
                f"🧮 Critérios cumpridos: {a['score']:g}/100 pontos. NÃO é uma probabilidade de lucro.\n"
                f"🛒 Compras: {fmt(ratio, '%')} das transações contadas; não mede dinheiro líquido a entrar.\n"
                f"🔄 Volume relativo: {fmt(a['relative_volume'])} vezes a média por hora das 23h anteriores. Pode haver atividade artificial.\n"
                f"💧 Liquidez reportada: {money(s['liquidity'])}; não garante que a tua venda execute.\n"
                f"🕒 Idade deste par: {fmt(s['pool_age_hours'])}h, não a idade do token. Consulta: {stamp(s['observed_at'])}\n"
                f"❔ Dados em falta: {html.escape(', '.join(a['missing']) or 'nenhum destes campos de mercado')}\n"
                "⚠️ Não verifico quem concentra os tokens, poderes de bloquear/criar tokens, liquidez bloqueada, "
                "contratos maliciosos ou se tu consegues vender. Não há auditoria de segurança. /noticias mostra a cobertura de notícias."),
                "buttons": token_buttons(s)}
    if command == "/health":
        health = data["health"]
        status = {"ok": "a funcionar", "degradado": "dados incompletos", "falha": "falha na última verificação"}
        return ("📡 <b>Estado do radar</b>\n"
                f"Estado: {status.get(health.get('status'), 'a aguardar primeira verificação')}\n"
                f"Última consulta: {stamp(health.get('last_attempt'))}\n"
                f"Última recolha com dados: {stamp(health.get('last_market_success'))}\n"
                f"Tokens observados: {health.get('observations', 0)} · sem dados: {health.get('missing', 0)}\n"
                f"Avisos/resumos nessa consulta: {health.get('signals', 0)}\n"
                "Verificações previstas de 5 em 5 minutos, sujeitas a atrasos. "
                "Este comando descreve a verificação anterior ao processamento da mensagem.")
    return HELP


def enqueue(state, reply):
    if reply is None:
        return
    if isinstance(reply, list):
        for item in reply:
            enqueue(state, item)
        return
    item = {"text": reply} if isinstance(reply, str) else reply
    if len(item["text"]) > 3500:
        import re
        clean = html.unescape(re.sub(r"</?[^>]+>", "", item["text"]))
        state.data["outbox"].extend({"text": html.escape(clean[i:i + 2800])} for i in range(0, len(clean), 2800))
    else:
        state.data["outbox"].append(item)


def consume(telegram, state, config, now):
    for update in telegram.updates(state.data["offset"]):
        update_id = update.get("update_id", -1)
        if update_id < state.data["offset"]:
            continue
        query = update.get("callback_query")
        if query:
            message = {**query.get("message", {}), "from": query.get("from", {})}
            if telegram.authorized(message):
                from .forms import callback
                try:
                    reply = callback(query.get("data", ""), state, config, now)
                except (ValueError, TypeError):
                    reply = "✏️ Não consegui validar esse pedido. Usa /ajuda; nenhuma transação foi executada."
                enqueue(state, reply)
                # Telegram can reject acknowledgements after a delayed scheduled run.
                try:
                    if hasattr(telegram, "answer"):
                        telegram.answer(query["id"])
                except Exception:
                    pass
        message = update.get("message", {})
        if not query and telegram.authorized(message) and now - message.get("date", 0) <= 86400:
            text = message.get("text", "")
            if len(text) <= 1000:
                try:
                    if text.startswith("/"):
                        reply = process(text, state, config, now)
                    else:
                        from .forms import reply as form_reply
                        reply = form_reply(state.data, text, now)
                except (ValueError, TypeError):
                    reply = "✏️ Não consegui validar. Confirma rede, contrato e valores; /ajuda explica os botões."
                # Save effect and reply together before acknowledging the Telegram update.
                enqueue(state, reply)
        state.data["offset"] = update_id + 1
        state.save()
