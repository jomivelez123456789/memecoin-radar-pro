import html
import os
from datetime import datetime, timezone
from .http import ApiError
from .model import links


def fmt(value, suffix=""):
    return "indisponível" if value is None else f"{value:,.8g}{suffix}"


def alert(s, analysis, category, reasons, config):
    link = links(s["chain"], s["address"], s.get("pair"))
    stamp = datetime.fromtimestamp(s["observed_at"], timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    text = (f"<b>{category}</b>\n{html.escape(s['name'])} ({html.escape(s['symbol'])}) · {s['chain']}\n"
            f"<code>{s['address']}</code>\n"
            f"Preço observado: ${fmt(s['price'])} · 1h: {fmt(s['change_h1'], '%')}\n"
            f"Volume 1h: ${fmt(s['volume_h1'])} · Liquidez: ${fmt(s['liquidity'])}\n"
            f"Score: {analysis['score']:g}/100 · Compras: {fmt(analysis['buy_ratio'] * 100 if analysis['buy_ratio'] is not None else None, '%')}\n"
            f"RVOL: {fmt(analysis['relative_volume'])} · Risco: {analysis['risk_class']}\n"
            f"Motivo: {html.escape('; '.join(reasons))}\n"
            f"Invalidação: liquidez &lt; ${config['min_liquidity_usd']:g}, momentum fora de "
            f"{config['min_change_h1']:g}–{config['max_change_h1']:g}%/1h ou dados incompletos.\n"
            f"{stamp} · consulta à API; última negociação não confirmada.\n"
            "Sem garantia de rentabilidade. Contrato, holders, mint/freeze e venda não verificados.\n"
            f"Detalhes: <code>/detail {s['chain']} {s['address']}</code>")
    buttons = [[{"text": "Ver gráfico", "url": link["chart"]},
                {"text": "Abrir token no Phantom", "url": link["app"]}],
               [{"text": "Copiar contrato", "copy_text": {"text": s["address"]}}]]
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
                                       "allowed_updates": ["message"]})

    def authorized(self, message):
        return (str(message.get("chat", {}).get("id")) == self.chat
                and str(message.get("from", {}).get("id")) == self.user
                and message.get("chat", {}).get("type") == "private")
