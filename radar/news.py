"""RSS públicos: títulos e links; ligação a token só com endereço e rede explícitos."""
import hashlib
import html
import re
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit
from xml.etree import ElementTree
from .http import ApiError
from .model import identity
from .telegram import stamp
from .views import token_buttons

FEEDS = {
    "CoinDesk": ("https://www.coindesk.com/arc/outboundfeeds/rss/", {"www.coindesk.com", "coindesk.com"}),
    "Cointelegraph": ("https://cointelegraph.com/rss", {"cointelegraph.com", "ct.com", "www.ct.com"}),
    "Decrypt": ("https://decrypt.co/feed", {"decrypt.co", "www.decrypt.co"}),
}
CHAIN_WORDS = {"solana": ("solana",), "ethereum": ("ethereum", "erc-20"),
               "base": ("on base", "base network", "base chain", "base blockchain", "rede base", "base l2")}


def parse_feed(text, source, allowed_hosts, now):
    if len(text.encode("utf-8")) > 1_000_000 or "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise ValueError("RSS não permitido ou demasiado grande")
    root = ElementTree.fromstring(text)
    output = []
    for item in root.findall("./channel/item")[:30]:
        url = (item.findtext("link") or "").strip()
        parsed_url = urlsplit(url)
        try:
            valid = (parsed_url.scheme == "https" and parsed_url.hostname in allowed_hosts
                     and parsed_url.port in (None, 443) and not parsed_url.username and not parsed_url.password)
        except ValueError:
            valid = False
        if not valid or len(url) > 2048:
            continue
        try:
            parsed_date = parsedate_to_datetime(item.findtext("pubDate") or "")
            if parsed_date.tzinfo is None:
                continue
            date = parsed_date.timestamp()
        except (ValueError, TypeError, OverflowError):
            continue
        if not now - 48 * 3600 <= date <= now + 300:
            continue
        title = re.sub(r"<[^>]+>", "", html.unescape(item.findtext("title") or "")).strip()[:160]
        if not title:
            continue
        context = title + " " + html.unescape(item.findtext("description") or "")[:20000]
        chains = [chain for chain, words in CHAIN_WORDS.items() if any(word in context.lower() for word in words)]
        mentions = []
        for address in re.findall(r"(?<![A-Za-z0-9])(?:0x[0-9a-fA-F]{40}|[1-9A-HJ-NP-Za-km-z]{32,44})(?![A-Za-z0-9])", context):
            for chain in chains:
                try:
                    mentions.append(identity(chain, address))
                except ValueError:
                    pass
        output.append({"id": hashlib.sha256((source + url).encode()).hexdigest()[:20],
                       "title": title, "url": url, "source": source, "published_at": date,
                       "mentions": list(dict.fromkeys(mentions))[:20]})
    return output


def refresh(data, http, now):
    news = data.setdefault("news", {"items": [], "sources": {}, "alerted": {}})
    if now - news.get("last_attempt", 0) < 1800:
        return
    items, success = [], False
    for source, (url, hosts) in FEEDS.items():
        try:
            received = parse_feed(http.text(url), source, hosts, now)
            items.extend(received)
            news["sources"][source] = "disponível"
            success = True
        except (ApiError, ValueError, UnicodeError, ElementTree.ParseError):
            news["sources"][source] = "indisponível nesta consulta"
            items.extend(item for item in news["items"] if item["source"] == source and now - item["published_at"] < 48 * 3600)
    news["last_attempt"] = now
    if success:
        news["last_success"] = now
    news["items"] = sorted({item["id"]: item for item in items}.values(), key=lambda i: i["published_at"], reverse=True)[:40]
    news["alerted"] = {key: at for key, at in news["alerted"].items() if now - at < 7 * 86400}


def correlate(data, snapshots, config, now, dry=False, limit=2):
    news = data.get("news", {})
    output = []
    for item in news.get("items", []):
        if now - item["published_at"] > 86400:
            continue
        for key in item["mentions"]:
            s = snapshots.get(key)
            if not s:
                continue
            from .engine import evaluate
            a = evaluate(s, config)
            if a["risk"] or a["missing"] or (a["relative_volume"] or 0) < config["min_relative_volume"] or (s.get("change_h1") or 0) < config["min_change_h1"]:
                continue
            notice_id = item["id"] + ":" + key
            if notice_id in news.get("alerted", {}):
                continue
            output.append({"text": "📰 <b>NOTÍCIA + ATIVIDADE — contexto para investigar</b>\n"
                f"🪙 {html.escape(s['name'])} · {s['chain']}\n"
                f"🗞️ {html.escape(item['source'])}: <a href=\"{html.escape(item['url'], quote=True)}\">{html.escape(item['title'])}</a>\n"
                f"🕒 Publicação indicada pela fonte: {stamp(item['published_at'])}\n"
                "🔗 O endereço completo e a rede aparecem na notícia, e o mercado mostra atividade crescente. "
                "Isto NÃO prova que a notícia seja verdadeira, favorável ou a causa da subida. Não valida ligação oficial a uma marca.\n"
                "🧭 Lê a fonte e verifica o contrato. Não é uma ordem de entrada nem altera o score de mercado.\n"
                f"📋 <code>{s['address']}</code>\n⚠️ Risco elevado e sem garantia de lucro.",
                "buttons": token_buttons(s), "expires_at": now + 1800,
                "news_id": item["id"], "key": key})
            if not dry:
                news.setdefault("alerted", {})[notice_id] = now
            if len(output) >= limit:
                return output
    return output


def news_view(data, now):
    news = data.get("news", {})
    sources = "\n".join(f"• {html.escape(name)}: {html.escape(status)}" for name, status in news.get("sources", {}).items()) or "A aguardar a primeira recolha."
    lines = ["📰 <b>O que o radar sabe das notícias</b>", sources,
             f"🕒 Última tentativa: {stamp(news.get('last_attempt'))}",
             "Leio RSS públicos destas fontes, no máximo a cada 30 minutos. Uma fonte pode falhar. Títulos são relatos da fonte, não factos verificados por mim."]
    for item in news.get("items", [])[:6]:
        if now - item["published_at"] <= 48 * 3600:
            lines.append(f"\n🗞️ {html.escape(item['source'])} · {stamp(item['published_at'])}\n"
                         f"<a href=\"{html.escape(item['url'], quote=True)}\">{html.escape(item['title'])}</a>")
    lines.append("\n🔗 Só associo uma notícia a uma moeda quando aparecem contrato completo e rede, juntamente com atividade de mercado. Nunca só pelo nome. "
                 "Não leio todas as notícias nem monitorizo X, TikTok, Instagram, Reddit, YouTube ou grupos Telegram. "
                 "Notícias não garantem lucro e não eliminam riscos do contrato.")
    return "\n".join(lines)
