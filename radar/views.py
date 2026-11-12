"""Mensagens de duas camadas: leitura simples primeiro; números nos detalhes."""
import hashlib
import html
import math
from .model import links
from .positions import estimate
from .telegram import stamp


def token_ref(key):
    return hashlib.sha256(key.encode()).hexdigest()[:12]


def money(value):
    if value is None:
        return "sem cotação"
    digits = 2 if abs(value) >= 1 else min(12, max(4, -int(math.floor(math.log10(abs(value)))) + 3)) if value else 2
    return f"{value:,.{digits}f}".replace(",", " ").replace(".", ",") + " USD"


def percent(value):
    return "sem dados" if value is None else f"{value:+.1f}%".replace(".", ",")


def units(value):
    return f"{value:,.8f}".rstrip("0").rstrip(".").replace(",", " ").replace(".", ",")


def token_buttons(s, register_buttons=True):
    direct = links(s["chain"], s["address"], s.get("pair"))
    ref = token_ref(s["key"])
    rows = [[{"text": "📈 Gráfico", "url": direct["chart"]},
             {"text": "👛 Abrir no Phantom", "url": direct["app"]}],
            [{"text": "📋 Copiar contrato", "copy_text": {"text": s["address"]}},
             {"text": "🔎 Explicar os dados", "callback_data": "detail:" + ref}]]
    if register_buttons:
        rows.append([{"text": "🧪 Simular", "callback_data": "sim:" + ref},
                     {"text": "📝 Já comprei", "callback_data": "buy:" + ref}])
        rows.append([{"text": "👀 Só acompanhar", "callback_data": "watch:" + ref},
                     {"text": "🧭 Guia rápido", "url": "https://github.com/jomivelez123456789/memecoin-radar-pro/blob/main/docs/UTILIZACAO_RAPIDA.md"}])
    return rows


def position_message(p, s, heading="💼 Resumo da tua posição", reason=None):
    if s is None:
        s = {}
    name = html.escape(s.get("name") or p["key"].split(":", 1)[0])
    if s.get("symbol"):
        name += " (" + html.escape(s["symbol"]) + ")"
    price = s.get("price")
    pnl = estimate(p, price) if price is not None and p["remaining"] > 0 else None
    change = (price / p["entry"] - 1) * 100 if price is not None else None
    mode = "🧪 SIMULAÇÃO — sem dinheiro real" if p["mode"] == "simulada" else "📝 REAL — compra registada por ti"
    status = "✅ Registo encerrado — saldo zero" if p["remaining"] == 0 else "📌 Registo aberto — continua acompanhado"
    result_label = "📈 Ganho estimado" if pnl is not None and pnl > 0 else "📉 Perda estimada" if pnl is not None and pnl < 0 else "⚖️ Sem variação estimada"
    result = (f"{result_label} na parte ainda aberta: <b>{money(abs(pnl))}</b>\n"
              "Conta teórica antes de taxas de saída e do desvio de execução; podes não conseguir vender por este preço.") if pnl is not None else (
              "🧮 Esta posição já está encerrada no registo." if p["remaining"] == 0 else "🧮 Falta uma cotação válida para estimar o resultado.")
    realized_label = "perda" if p["realized_pnl"] < 0 else "ganho" if p["realized_pnl"] > 0 else "sem ganho/perda"
    text = (f"<b>{heading}</b>\n{name} · {p['key'].split(':', 1)[0]}\n{mode}\n\n"
            + (f"💡 <b>O que aconteceu:</b> {html.escape(reason)}\n\n" if reason else "")
            + f"{status}\n📦 Quantidade por vender no registo: {units(p['remaining'])}\n"
            f"💰 Entrada que registaste: {money(p['entry'])}\n"
            f"📍 Cotação observada: {money(price)} ({percent(change)} face à entrada)\n"
            f"{result}\n📝 Nas vendas registadas: {realized_label} de {money(abs(p['realized_pnl']))}\n\n"
            f"🛑 O teu limite de perda: {money(p['stop'])}\n🎯 O teu objetivo: {money(p['take'])}\n"
            + (f"💧 Liquidez reportada: {money(s.get('liquidity'))} · volume 1h: {money(s.get('volume_h1'))}\n" if reason else "")
            + "⚠️ Risco elevado; contrato e possibilidade de vender não verificados. Sem garantia de lucro.\n"
            f"🕒 {stamp(s.get('observed_at'))}\n"
            "O radar não vendeu nada. /vender explica os passos; só registes uma venda real depois de confirmada na carteira.\n"
            f"🆔 <code>{p['id']}</code> · <code>{p['key']}</code>")
    buttons = [[{"text": "📝 Registar venda", "callback_data": "sell:" + p["id"]},
                {"text": "🎯 Alterar níveis", "callback_data": "levels:" + p["id"]}],
               [{"text": "💸 Como vender", "callback_data": "help:vender"}]] if p["remaining"] > 0 else []
    if s.get("key"):
        buttons += token_buttons(s, False)
    return {"text": text, "buttons": buttons, "expires_at": (s.get("observed_at") or 0) + 1800} if reason else {"text": text, "buttons": buttons}
