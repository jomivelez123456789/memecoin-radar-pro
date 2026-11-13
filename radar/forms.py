"""Registo guiado por botões e uma resposta curta; nunca executa uma transação."""
import html
import re
import uuid
from .model import identity
from .positions import register, close, positive
from .views import token_ref, money, position_message, token_buttons, units
from .education import page


def find_token(data, ref):
    return next((s for key, s in data["snapshots"].items() if token_ref(key) == ref), None)


def choose(data, mode):
    snapshots = sorted(data["snapshots"].values(), key=lambda s: s["observed_at"], reverse=True)[:8]
    if not snapshots:
        return {"text": "🧭 Ainda não há moedas observadas. Aguarda uma verificação e usa o botão de um alerta.\nNão escolhas só pelo nome."}
    return {"text": "🧭 Escolhe a moeda que queres registar. Na etapa seguinte confirma o contrato completo.\n"
                    "🧪 Simular não usa dinheiro. 📝 Já comprei serve só para uma compra manual já confirmada.",
            "buttons": [[{"text": f"{s['symbol'][:16]} · {s['chain']} · {s['address'][:4]}…{s['address'][-4:]}",
                          "callback_data": mode + ":" + token_ref(s["key"])}] for s in snapshots]}


def begin(data, kind, now, key=None, position_id=None):
    form = {"kind": kind, "key": key, "position_id": position_id,
            "expires_at": now + 86400, "nonce": uuid.uuid4().hex[:10]}
    data["form"] = form
    if kind in ("sim", "buy"):
        chain, address = key.split(":", 1)
        mode = "🧪 SIMULAÇÃO — não há compra" if kind == "sim" else "📝 REGISTO REAL — apenas uma compra que já fizeste manualmente"
        text = (f"<b>{mode}</b>\nRede: {chain}\nContrato: <code>{address}</code>\n\n"
                "Confirma a identidade. Depois responde com UMA mensagem com estas 5 linhas, substituindo os valores por números:\n\n"
                "Preço: ...\nQuantidade: ...\nTaxa: ...\nLimite de perda: ...\nObjetivo: ...\n\n"
                "💵 USD significa dólares americanos, não euros. Usa essa mesma moeda de visualização na carteira, se disponível; não copies euros como se fossem dólares. "
                "Preço, taxa e níveis em USD. Quantidade é o número de unidades recebidas, não os euros gastos. "
                "Aceito vírgula decimal. Taxa pode ser 0. Limite deve ficar abaixo da entrada; objetivo acima.\n"
                "🎯 São níveis para avisos, não ordens. /saidas explica; /comprar ensina a simular primeiro.\n"
                "Só envia dados fictícios numa simulação, ou os dados reais da compra já confirmada num registo real. "
                "Não envies credenciais. Se ainda não sabes os valores, cancela e aprende primeiro.")
    else:
        p = next((p for p in data["positions"] if p["id"] == position_id and p["remaining"] > 0), None)
        if not p:
            data.pop("form", None)
            raise ValueError("Posição inexistente ou encerrada")
        if kind == "sell":
            text = (f"📝 <b>Registar venda {'SIMULADA' if p['mode']=='simulada' else 'REAL já executada'}</b>\n"
                    f"Posição <code>{p['id']}</code> · saldo registado {units(p['remaining'])} unidades\n\n"
                    "Responde numa mensagem com 3 linhas:\nPreço: ...\nQuantidade vendida: ...\nTaxa: ...\n\n"
                    "Preço executado e taxa em USD; aceita vírgula decimal e taxa 0. Podes registar uma parcela. "
                    "Isto NÃO vende na carteira. /vender explica o percurso. Numa posição simulada usa valores fictícios.")
        else:
            text = (f"🎯 <b>Alterar os teus níveis de aviso</b>\nPosição <code>{p['id']}</code>\n\n"
                    "Responde numa mensagem com 2 linhas:\nLimite de perda: ...\nObjetivo: ...\n\n"
                    "Ambos em USD por unidade; limite abaixo do objetivo. São preços que tu defines, sem uma sugestão pessoal do bot. "
                    "O limite de perda não é uma ordem e não impede perdas maiores. /saidas explica.")
    return {"text": text, "buttons": [[{"text": "🛑 Cancelar formulário", "callback_data": "cancel:" + form["nonce"]}]]}


def values(text, count, fee_index=None):
    parts = [p.strip() for p in re.split(r"[;\n]", text.strip()) if p.strip()]
    if len(parts) == 1 and ":" not in text:
        parts = text.split()
    if len(parts) != count:
        raise ValueError("Número de linhas incorreto")
    output = []
    for index, part in enumerate(parts):
        part = part.split(":", 1)[-1].strip()
        part = re.sub(r"\s*(?:USD|\$)$", "", part, flags=re.I).replace(" ", "").replace(",", ".")
        if not re.fullmatch(r"[+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", part):
            raise ValueError("Número inválido")
        output.append(positive(part, index == fee_index))
    return output


def reply(data, text, now):
    form = data.get("form")
    if not form:
        return None
    if now > form["expires_at"]:
        data.pop("form", None)
        return {"text": "⌛ O formulário expirou. Usa novamente o botão da moeda ou /ajuda."}
    kind = form["kind"]
    try:
        if kind in ("sim", "buy"):
            entry, quantity, fee, stop, take = values(text, 5, 2)
            chain, address = form["key"].split(":", 1)
            p = register(data, "simulada" if kind == "sim" else "real", chain, address,
                         entry, quantity, fee, stop, take, now)
            message = position_message(p, data["snapshots"].get(p["key"]), "✅ Posição registada — vou acompanhá-la")
        elif kind == "sell":
            price, quantity, fee = values(text, 3, 2)
            p, pnl = close(data, form["position_id"], price, quantity, fee, now)
            message = position_message(p, data["snapshots"].get(p["key"]), "✅ Venda registada — nenhuma transação executada")
            message["text"] += f"\n🧮 Resultado desta parcela: {money(pnl)}."
        else:
            stop, take = values(text, 2)
            if stop >= take:
                raise ValueError("Limite acima do objetivo")
            p = next(p for p in data["positions"] if p["id"] == form["position_id"] and p["remaining"] > 0)
            p["stop"], p["take"] = stop, take
            p["levels_updated_at"] = now
            message = position_message(p, data["snapshots"].get(p["key"]), "🎯 Níveis de aviso atualizados")
    except (ValueError, TypeError, StopIteration):
        return {"text": "✏️ Não consegui validar esses valores. Mantive o formulário e não alterei posições. "
                        "Confirma o número de linhas, usa apenas números e vírgula/ponto decimal. "
                        "Na entrada: limite < preço < objetivo. Na venda: quantidade não pode exceder o saldo. "
                        "Se precisares de aprender primeiro, usa /cancelar e /ajuda."}
    data.pop("form", None)
    return message


def callback(payload, state, config, now):
    data = state.data
    action, _, ref = payload.partition(":")
    if action == "help":
        return {"text": page(ref)}
    if action == "cancel":
        if data.get("form", {}).get("nonce") == ref:
            data.pop("form", None)
            return {"text": "🛑 Formulário cancelado. Não alterei posições nem carteiras."}
        return {"text": "⌛ Esse formulário já não é o atual. Se estiveres a preencher outro, continua ou usa /cancelar."}
    if action in ("sell", "levels"):
        return begin(data, action, now, position_id=ref)
    s = find_token(data, ref)
    if s is None:
        return {"text": "⌛ Este botão pertence a uma observação antiga ou indisponível. Usa /posicoes ou aguarda um novo alerta. Não escolhas outra moeda pelo nome."}
    if action in ("sim", "buy"):
        return begin(data, action, now, key=s["key"])
    if action == "watch":
        if s["key"] not in data["watched"]:
            if len(data["watched"]) >= 30:
                raise ValueError("Lista manual cheia")
            data["watched"].append(s["key"])
        return {"text": "👀 Vou acompanhar esta moeda. Isto NÃO significa que compraste. "
                        "Se entrares manualmente, regista com «📝 Já comprei» para teres os teus níveis de saída.",
                "buttons": token_buttons(s)}
    if action == "detail":
        from .commands import process
        return process(f"/detail {s['chain']} {s['address']}", state, config, now)
    return {"text": "🧭 Botão não reconhecido. Usa /ajuda."}
