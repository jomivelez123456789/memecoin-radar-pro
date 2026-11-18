"""Bounded public research and transparent rejection reports; never changes entry rules."""
import html
import math
from datetime import datetime
from xml.etree import ElementTree as ET
from collections import Counter
from .http import ApiError
from .model import links
from .telegram import stamp

VERSION = "public-research-v2"
CHANNELS = {
    "Coin Bureau": "UCqK_GSMbpiV8spgD3ZGloSw",
    "Benjamin Cowen": "UCRvqjQPSeaWn-uEx-w0XOIg",
}
ATOM = "{http://www.w3.org/2005/Atom}"
YT = "{http://www.youtube.com/xml/schemas/2015}"
FILTER_HELP = {"liquidez": "liquidez: pouco dinheiro disponível para trocas",
               "volume": "volume: poucas trocas em valor", "idade do par": "par demasiado recente",
               "atividade": "poucas compras e vendas", "pressão compradora": "proporção de compras insuficiente",
               "momentum": "subida fora do intervalo definido", "volume relativo": "atividade sem aceleração suficiente ou sem histórico",
               "dados completos": "faltam dados ou histórico fiável"}


def youtube_items(text, channel, channel_id, now):
    if len(text.encode()) > 1_000_000 or "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise ValueError("Feed não permitido")
    root = ET.fromstring(text)
    # YouTube's Atom feed currently omits the UC prefix in yt:channelId.
    if root.findtext(YT + "channelId") not in (channel_id, channel_id.removeprefix("UC")):
        raise ValueError("Identidade do canal não confirmada")
    output = []
    for entry in root.findall(ATOM + "entry")[:15]:
        video = entry.findtext(YT + "videoId") or ""
        if len(video) != 11 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in video):
            continue
        try:
            date = datetime.fromisoformat(entry.findtext(ATOM + "published").replace("Z", "+00:00"))
            if date.tzinfo is None:
                continue
            date = date.timestamp()
        except (ValueError, TypeError, AttributeError, OverflowError):
            continue
        if not now - 7 * 86400 <= date <= now + 300:
            continue
        title = (entry.findtext(ATOM + "title") or "").strip()[:160]
        if title:
            output.append({"source": channel, "title": title, "published_at": date,
                           "url": "https://www.youtube.com/watch?v=" + video})
    return output


def refresh(data, http, now):
    research = data.setdefault("research", {})
    if now - research.get("last_attempt", 0) < 1800:
        return
    sources, videos, benchmarks = {}, [], {}
    for channel, channel_id in CHANNELS.items():
        try:
            videos.extend(youtube_items(http.text("https://www.youtube.com/feeds/videos.xml?channel_id=" + channel_id),
                                        channel, channel_id, now))
            sources[channel] = "disponível (títulos públicos)"
        except (ApiError, ValueError, UnicodeError, ET.ParseError):
            sources[channel] = "indisponível nesta consulta"
    for symbol in ("BTC", "ETH", "SOL"):
        try:
            stats = http.json(f"https://api.exchange.coinbase.com/products/{symbol}-USD/stats")
            opening, last = float(stats["open"]), float(stats["last"])
            change = (last / opening - 1) * 100 if opening > 0 and last > 0 else float("nan")
            if not math.isfinite(change):
                raise ValueError("Cotação inválida")
            benchmarks[symbol] = round(change, 2)
            sources["Coinbase " + symbol] = "disponível"
        except (ApiError, ValueError, TypeError, KeyError, OverflowError):
            sources["Coinbase " + symbol] = "indisponível nesta consulta"
    # Failed fetches are explicit; do not silently label cached quotes as fresh.
    research.update(last_attempt=now, sources=sources, videos=sorted(videos, key=lambda v: v["published_at"], reverse=True)[:10],
                    benchmarks=benchmarks)


def observe(data, snapshots, analyses, calls, coverage, config, now):
    research = data.setdefault("research", {})
    if research.get("version") != VERSION:
        research["version"] = VERSION
        if data.get("paper"):
            data["paper"].setdefault("research_changes", []).append({"at": now, "version": VERSION,
                "chains": config["chains"], "discovery_limit": config["discovery_limit"],
                "note": "Universo de descoberta ampliado; regras de entrada e saldo preservados."})
    window = research.setdefault("window", {"since": now, "scans": 0, "observations": 0,
                                           "unique": {}, "blocked": {}, "qualified": 0, "calls": 0})
    window["scans"] += 1
    window["observations"] += len(snapshots)
    window["calls"] += len(calls)
    blockers = Counter(window["blocked"])
    for key, a in analyses.items():
        window["unique"][key] = now
        blockers.update(name for name, ok in a["checks"].items() if not ok)
        window["qualified"] += bool(a["entry"])
    # Bound state size even if reporting is interrupted for days.
    window["unique"] = dict(sorted(window["unique"].items(), key=lambda pair: pair[1], reverse=True)[:2000])
    window["blocked"] = dict(blockers)
    ranked = sorted(analyses, key=lambda key: (analyses[key]["score"], not analyses[key]["risk"]), reverse=True)
    research.update(last_scan=now, coverage=coverage, chains=config["chains"],
                    sample=[{"key": key, "name": snapshots[key]["name"], "checks": analyses[key]["checks"],
                             "risk": analyses[key]["risk"], "entry": analyses[key]["entry"]} for key in ranked[:3]])


def view(data, now):
    r = data.get("research", {})
    window = r.get("window") or r.get("last_window") or {}
    if not window.get("scans"):
        window = r.get("last_window", {})
    lines = ["🔎 <b>RESUMO DA PESQUISA — mesmo sem call</b>",
             f"🕒 Período observado desde {stamp(window.get('since'))}; última consulta {stamp(r.get('last_scan'))}.",
             f"🌐 Redes: {', '.join(r.get('chains', [])) or 'a aguardar'}.",
             f"📊 {window.get('scans', 0)} consultas · {window.get('observations', 0)} observações "
             f"(incluem repetições) · {len(window.get('unique', {}))} contratos distintos (limite de contagem: 2 000).",
             f"🎯 Calls de entrada emitidas: {window.get('calls', 0)}. "
             "Sem call não há compra no teste; não significa que não existam oportunidades fora da amostra."]
    if window.get("blocked"):
        lines.append("\n🛑 <b>Porque fiquei de fora</b> (uma observação pode falhar vários filtros):")
        lines.extend(f"• {html.escape(FILTER_HELP.get(name, name))}: {count} falhas" for name, count in Counter(window["blocked"]).most_common(4))
    if r.get("last_scan") and now - r["last_scan"] <= 900:
        lines.append("\n👀 <b>Exemplos da última amostra — não são recomendações</b>")
        for item in r.get("sample", []):
            chain, address = item["key"].split(":", 1)
            failed = [name for name, ok in item["checks"].items() if not ok]
            reason = "; ".join(item["risk"] or [FILTER_HELP.get(name, name) for name in failed]) or "filtros cumpridos; consultar alerta e possível intervalo entre avisos"
            lines.append(f"• <a href=\"{html.escape(links(chain, address)['chart'], quote=True)}\">{html.escape(item['name'])}</a> "
                         f"({chain}): {sum(item['checks'].values())}/8 filtros. {html.escape(reason)}.")
    else:
        lines.append("⚠️ Amostra antiga ou ainda indisponível; não apresento moedas como atuais.")
    if r.get("last_attempt") and now - r["last_attempt"] <= 3600:
        if r.get("benchmarks"):
            lines.append("\n🌍 Mercado geral na Coinbase, variação de 24h: " + " · ".join(f"{s} {v:+.1f}%" for s, v in r["benchmarks"].items()) + ". Contexto; não prevê memecoins.")
        for video in r.get("videos", [])[:2]:
            lines.append(f"\n📺 {html.escape(video['source'])} · {stamp(video['published_at'])}\n"
                         f"<a href=\"{html.escape(video['url'], quote=True)}\">{html.escape(video['title'])}</a>")
    news = data.get("news", {})
    for item in news.get("items", [])[:1]:
        if now - item["published_at"] <= 48 * 3600:
            lines.append(f"\n📰 {html.escape(item['source'])}: <a href=\"{html.escape(item['url'], quote=True)}\">{html.escape(item['title'])}</a>")
    unavailable = [name for name, status in {**r.get("coverage", {}), **r.get("sources", {}), **news.get("sources", {})}.items() if "indisponível" in status]
    if unavailable:
        lines.append("\n⚠️ Fontes sem acesso nesta recolha: " + html.escape(", ".join(unavailable)))
    lines.append("\n📚 YouTube: apenas títulos e links de 2 canais; não vejo vídeos, transcrições ou comentários. "
                 "Notícias e opiniões dão contexto, não aumentam o score nem provam lucro. "
                 "TikTok, Instagram, X e grupos não estão monitorizados. Não cubro toda a internet nem todos os mercados. "
                 "🧪 /resultados · 📰 /noticias · 🔎 /pesquisa. Resumo previsto de 3 em 3 horas, sujeito a atrasos.")
    return "\n".join(lines)


def periodic(data, now):
    r = data.get("research", {})
    if not r.get("window", {}).get("scans") or now - r.get("last_report", 0) < 10800:
        return None
    message = view(data, now)
    r["last_report"] = now
    r["last_window"] = r.pop("window")
    return {"text": message, "expires_at": now + 3600}
