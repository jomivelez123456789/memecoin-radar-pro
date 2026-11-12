import html
import os
from datetime import datetime, timezone
from .http import ApiError
from .model import links


def fmt(value, suffix=""):
    return "indisponível" if value is None else f"{value:,.8g}{suffix}"


def stamp(value):
    return datetime.fromtimestamp(value, timezone.utc).strftime("%d/%m/%Y %H:%M UTC") if value else "sem observação"


def alert(s, analysis, category, reasons, config):
    from .views import money, percent, token_buttons
    link = links(s["chain"], s["address"], s.get("pair"))
    observed = stamp(s["observed_at"])
    if category.startswith("A"):
        invalidation = (f"liquidez &lt; ${config['min_liquidity_usd']:g}, momentum fora de "
                        f"{config['min_change_h1']:g}–{config['max_change_h1']:g}%/1h ou dados incompletos.")
    elif category.startswith("B"):
        invalidation = "reavaliar se o preço voltar entre os níveis definidos e a liquidez recuperar; confirmar dados atuais."
    else:
        invalidation = "reavaliar com dados completos e atividade normalizada; riscos contratuais continuam desconhecidos."
    if category.startswith("A"):
        heading = "🟡 POSSÍVEL ENTRADA — para analisares"
        explanation = "Há mais atividade e pressão compradora, com os filtros de mercado cumpridos. Isto não prova que a moeda seja segura nem que vá subir."
        action = "Começa por «🧪 Simular». Se comprares manualmente, regista em «📝 Já comprei»; só assim fica como uma posição tua."
    elif category.startswith("B"):
        heading = "🟠 MOEDA EM OBSERVAÇÃO — condições pioraram"
        explanation = "; ".join(reasons)
        action = "Não há uma compra tua registada neste aviso. É só observação, não um pedido para vender algo que não tens. Se compraste manualmente, regista-a; /posicoes mostra apenas o que registaste."
    else:
        heading = "🔴 ATENÇÃO — risco observado"
        explanation = "; ".join(reasons)
        action = "Evita decidir à pressa. Confirma os dados e lê as limitações antes de assinar qualquer transação."
    text = (f"<b>{heading}</b>\n🪙 {html.escape(s['name'])} ({html.escape(s['symbol'])}) · {s['chain']}\n\n"
            f"💡 <b>Em palavras simples:</b> {html.escape(explanation)}\n"
            f"📍 Preço observado: <b>{money(s['price'])}</b>\n"
            f"📊 Na última hora: {percent(s['change_h1'])}\n"
            f"💧 Liquidez: {money(s['liquidity'])} — recursos reportados para trocas, sem garantia de venda.\n"
            f"🔄 Volume 1h: {money(s['volume_h1'])} — valor negociado, não lucro.\n\n"
            f"🧭 <b>O que fazer:</b> {action}\n"
            f"❗ Risco {analysis['risk_class'].lower()}. Contrato, holders, mint/freeze e possibilidade de vender não verificados.\n"
            f"↩️ Quando reavaliar: {invalidation}\n"
            f"🕒 {observed} · hora da consulta; última negociação não confirmada.\n"
            "Sem garantia de rentabilidade.\n"
            f"📋 Rede: {s['chain']} · contrato completo:\n<code>{s['address']}</code>")
    buttons = token_buttons(s)
    return {"text": text, "buttons": buttons, "expires_at": s["observed_at"] + 1800}


class Telegram:
    def __init__(self, http):
        self.http = http
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat = os.environ.get("TELEGRAM_CHAT_ID", "")
        self.user = os.environ.get("TELEGRAM_USER_ID", self.chat)
        if not self.token or not self.chat or not self.user:
            raise ValueError("Configurar os segredos Telegram antes de enviar")

    def call(self, method, payload, retry=True):
        result = self.http.json(f"https://api.telegram.org/bot{self.token}/{method}", payload, retry=retry)
        if not result.get("ok"):
            raise ApiError("Telegram recusou o pedido")
        return result["result"]

    def send(self, text, buttons=None):
        payload = {"chat_id": self.chat, "text": text, "parse_mode": "HTML",
                   "link_preview_options": {"is_disabled": True}}
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": buttons}
        # Retrying sendMessage after a timeout can duplicate a delivered message.
        return self.call("sendMessage", payload, retry=False)

    def updates(self, offset):
        return self.call("getUpdates", {"offset": offset, "limit": 100, "timeout": 0,
                                       "allowed_updates": ["message", "callback_query"]})

    def answer(self, callback_id):
        return self.call("answerCallbackQuery", {"callback_query_id": callback_id,
                        "text": "Pedido processado pelo radar.", "show_alert": False}, retry=False)

    def authorized(self, message):
        return (str(message.get("chat", {}).get("id")) == self.chat
                and str(message.get("from", {}).get("id")) == self.user
                and message.get("chat", {}).get("type") == "private")
