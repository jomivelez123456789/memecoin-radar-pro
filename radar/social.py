"""Read only public server-rendered posts; no login, browser bypass or private API."""
import html
import json
import re
from datetime import datetime
from html.parser import HTMLParser
from .http import ApiError
from .telegram import stamp
from .model import number
from urllib.parse import urlsplit

PAGES = {"TikTok #memecoin": "https://www.tiktok.com/tag/memecoin",
         "TikTok Coin Bureau": "https://www.tiktok.com/@coinbureau",
         "Instagram Coin Bureau": "https://www.instagram.com/coinbureau/",
         "X Coin Bureau": "https://x.com/coinbureau",
         "Reddit r/CryptoCurrency": "https://www.reddit.com/r/CryptoCurrency/new/",
         "Reddit r/solana": "https://www.reddit.com/r/solana/new/"}
PREVIEWS = ("solana", "CryptoCurrency", "memecoins")


class PublicHTML(HTMLParser):
    def __init__(self):
        super().__init__(); self.posts = []; self.scripts = []; self.capture = False; self.parts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "shreddit-post":
            self.posts.append(a)
        if tag == "script" and (a.get("id") in ("__UNIVERSAL_DATA_FOR_REHYDRATION__", "SIGI_STATE")
                                or a.get("type") == "application/ld+json"):
            self.capture = True; self.parts = []

    def handle_data(self, text):
        if self.capture:
            self.parts.append(text)

    def handle_endtag(self, tag):
        if tag == "script" and self.capture:
            self.scripts.append("".join(self.parts)); self.capture = False


def parse(text, source, now):
    if len(text.encode()) > 2_000_000:
        raise ValueError("Página demasiado grande")
    parser = PublicHTML(); parser.feed(text); items = []
    if source.startswith("X "):
        items.extend(x_public_payloads(text, now))
    if source.startswith("Reddit"):
        community = source.split("r/", 1)[1]
        for p in parser.posts[:40]:
            path = p.get("permalink", "")
            title = p.get("post-title", "").strip()[:160]
            if not re.fullmatch(r"/r/" + re.escape(community) + r"/comments/[A-Za-z0-9]+/[A-Za-z0-9_%\-]*/?", path, re.I):
                continue
            try:
                date = datetime.fromisoformat(p.get("created-timestamp", "").replace("Z", "+00:00"))
                date = date.timestamp() if date.tzinfo else 0
            except (ValueError, OverflowError):
                continue
            if title and now - 48 * 3600 <= date <= now + 300:
                items.append({"source": source, "title": title, "url": "https://www.reddit.com" + path,
                              "published_at": date, "scope": "título público; comentários não lidos"})
    elif source.startswith("TikTok"):
        # Only actual public post structures qualify. HTTP 200/app configuration is not a feed.
        for script in parser.scripts:
            try:
                stack = [json.loads(script)]
            except ValueError:
                continue
            nodes = 0
            while stack and nodes < 10000:
                value = stack.pop(); nodes += 1
                if isinstance(value, list):
                    stack.extend(value[:1000]); continue
                if not isinstance(value, dict):
                    continue
                author = value.get("author", {})
                author = author.get("uniqueId", "") if isinstance(author, dict) else ""
                video, description = str(value.get("id", "")), value.get("desc")
                try:
                    date = float(value.get("createTime", 0))
                except (ValueError, TypeError, OverflowError):
                    date = 0
                if (re.fullmatch(r"[A-Za-z0-9._]{1,40}", author) and re.fullmatch(r"[0-9]{15,25}", video)
                        and isinstance(description, str) and description.strip() and now - 48 * 3600 <= date <= now + 300):
                    items.append({"source": source, "title": description.strip()[:160],
                                  "url": f"https://www.tiktok.com/@{author}/video/{video}",
                                  "published_at": date, "scope": "descrição pública; vídeo/áudio não vistos"})
                stack.extend(v for v in value.values() if isinstance(v, (dict, list)))
    elif source.startswith(("Instagram", "X ")):
        for script in parser.scripts:
            try:
                stack = [json.loads(script)]
            except ValueError:
                continue
            nodes = 0
            while stack and nodes < 2000:
                value = stack.pop(); nodes += 1
                if isinstance(value, list):
                    stack.extend(value[:100]); continue
                if not isinstance(value, dict):
                    continue
                stack.extend(v for v in value.values() if isinstance(v, (dict, list)))
                if value.get("@type") not in ("SocialMediaPosting", "BlogPosting", "Article"):
                    continue
                url = value.get("url", "")
                if not isinstance(url, str):
                    continue
                u = urlsplit(url)
                valid = (u.scheme == "https" and not u.query and not u.fragment and
                         ((source.startswith("X ") and u.netloc == "x.com" and re.fullmatch(r"/coinbureau/status/[0-9]+/?", u.path))
                          or (source.startswith("Instagram") and u.netloc == "www.instagram.com"
                              and re.fullmatch(r"/(p|reel)/[A-Za-z0-9_-]+/?", u.path)
                              and isinstance(value.get("author"), dict)
                              and value["author"].get("url", "").rstrip("/") == "https://www.instagram.com/coinbureau")))
                try:
                    date = datetime.fromisoformat(value.get("datePublished", "").replace("Z", "+00:00"))
                    date = date.timestamp() if date.tzinfo else 0
                except (ValueError, TypeError, AttributeError, OverflowError):
                    continue
                title = value.get("headline") or value.get("articleBody")
                if valid and isinstance(title, str) and title.strip() and now - 48*3600 <= date <= now + 300:
                    items.append({"source": source, "title": title.strip()[:160], "url": url,
                                  "published_at": date, "scope": "texto público estruturado; vídeo/áudio/comentários não lidos"})
    return list({i["url"]: i for i in items}.values())[:20]


def x_public_payloads(text, now):
    """Decode JSON string literals included in public HTML; never evaluate scripts."""
    output = []
    for token in re.finditer(r'"(?:\\.|[^"\\])*"', text):
        raw = token.group()
        if len(raw) > 1_500_000 or "created_at_ms" not in raw or "full_text" not in raw:
            continue
        try:
            value = json.loads(raw)
            if not isinstance(value, str):
                continue
            stack = [json.loads(value)]
        except (ValueError, RecursionError):
            continue
        nodes = 0
        while stack and nodes < 10000:
            item = stack.pop(); nodes += 1
            if isinstance(item, list):
                stack.extend(item[:1000]); continue
            if not isinstance(item, dict):
                continue
            stack.extend(v for v in item.values() if isinstance(v, (dict, list)))
            detail = item.get("details")
            if not isinstance(detail, dict):
                continue
            author = item
            for part in ("core", "user_results", "result", "core"):
                author = author.get(part, {}) if isinstance(author, dict) else {}
            if not isinstance(author, dict) or author.get("screen_name", "").lower() != "coinbureau":
                continue
            post_id = item.get("rest_id", "")
            date = number(detail.get("created_at_ms"))
            title = detail.get("full_text")
            if (not isinstance(post_id, str) or not re.fullmatch(r"[0-9]{15,25}", post_id)
                    or date is None or not now - 48*3600 <= date/1000 <= now + 300
                    or not isinstance(title, str) or not title.strip()):
                continue
            output.append({"source": "X Coin Bureau", "title": title.strip()[:160],
                           "published_at": date/1000, "url": "https://x.com/coinbureau/status/" + post_id,
                           "scope": "texto público do perfil; comentários, áudio e vídeo não lidos"})
    return list({i["url"]: i for i in output}.values())[:20]


def reddit_preview(payload, community, now):
    if (not isinstance(payload, dict) or not isinstance(payload.get("subreddit"), str)
            or payload["subreddit"].lower() != ("r/" + community).lower()):
        raise ValueError("Comunidade não confirmada")
    try:
        updated = datetime.fromisoformat(payload["updated"].replace("Z", "+00:00"))
        if updated.tzinfo is None:
            raise ValueError("Data sem fuso horário")
        updated = updated.timestamp()
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        raise ValueError("Data do fornecedor inválida") from None
    if not now - 86400 <= updated <= now + 300:
        raise ValueError("Amostra do fornecedor desatualizada")
    posts = payload.get("newest_posts")
    if not isinstance(posts, list):
        raise ValueError("Amostra sem lista de publicações")
    items = []
    for post in posts[:10]:
        if not isinstance(post, dict):
            continue
        url, date = post.get("url", ""), number(post.get("created_utc"))
        if not isinstance(url, str):
            continue
        u = urlsplit(url)
        path = r"/r/" + re.escape(community) + r"/comments/[A-Za-z0-9]+/[A-Za-z0-9_%\-]*/?"
        if (u.scheme != "https" or u.netloc != "www.reddit.com" or not re.fullmatch(path, u.path, re.I)
                or u.query or u.fragment or date is None or not now - 48*3600 <= date <= now + 300):
            continue
        title = post.get("title")
        if not isinstance(title, str) or not title.strip():
            continue
        items.append({"source": f"Reddit r/{community} via Redlisten", "title": title.strip()[:160],
                      "url": url, "published_at": date, "provider_updated_at": updated,
                      "provider_url": "https://redlisten.com/r/" + community,
                      "scope": "título de amostra pública de terceiros; comentários não lidos"})
    return items, updated


def refresh(data, http, now):
    social = data.setdefault("social", {})
    if now - social.get("last_attempt", 0) < 3600:
        return
    sources, items = dict(social.get("sources", {})), []
    for source, url in PAGES.items():
        if not source.startswith("X ") and now - social.get("direct_attempt", 0) < 21600:
            items.extend(i for i in social.get("items", []) if i["source"] == source and now - i["published_at"] <= 48*3600)
            continue
        try:
            body = http.json(url, headers={"Accept": "text/html"}, retry=False, raw=True)
            received = parse(body.decode("utf-8"), source, now)
            items.extend(received)
            sources[source] = (f"{len(received)} publicações públicas recentes lidas" if received else
                               "sem publicações recentes legíveis; acompanhamento NÃO confirmado")
        except ApiError as error:
            sources[source] = f"indisponível (HTTP {error.status})" if error.status else "indisponível (rede/resposta)"
        except (ValueError, UnicodeError):
            sources[source] = "indisponível (página não validada)"
    if now - social.get("direct_attempt", 0) >= 21600:
        social["direct_attempt"] = now
    for community in PREVIEWS:
        source = f"Reddit r/{community} via Redlisten"
        try:
            received, updated = reddit_preview(http.json("https://redlisten.com/r/" + community.lower() + "?format=json", retry=False), community, now)
            items.extend(received)
            sources[source] = f"{len(received)} títulos recentes da amostra; fornecedor atualizado em {stamp(updated)}"
        except ApiError as error:
            sources[source] = f"indisponível (HTTP {error.status})" if error.status else "indisponível (rede/resposta)"
        except ValueError:
            sources[source] = "indisponível (amostra inválida ou fornecedor desatualizado)"
    social.update(last_attempt=now, sources=sources,
                  items=sorted(items, key=lambda i: i["published_at"], reverse=True)[:30])


def view(data, now):
    social = data.get("social", {})
    lines = ["📱 <b>PESQUISA SOCIAL — acesso real</b>", f"🕒 Última tentativa: {stamp(social.get('last_attempt'))}.",
             "X e amostras públicas Redlisten: consulta a cada 1h, sem conta/chave/pagamento. Outras páginas diretas: tentativa a cada 6h. Não é acesso completo ou em tempo real."]
    lines.extend(f"• {html.escape(source)}: {html.escape(status)}" for source, status in social.get("sources", {}).items())
    if not social.get("sources"):
        lines.append("A aguardar a primeira tentativa; acesso ainda não confirmado.")
    if social.get("last_attempt") and now - social["last_attempt"] <= 21600 + 900:
        for item in social.get("items", [])[:4]:
            if 0 <= now - item["published_at"] <= 48 * 3600:
                lines.append(f"\n<a href=\"{html.escape(item['url'], quote=True)}\">{html.escape(item['title'])}</a>\n"
                             f"{html.escape(item['source'])} · {stamp(item['published_at'])} · {html.escape(item['scope'])}.")
                if item.get("provider_updated_at"):
                    lines.append(f"Fornecedor: {stamp(item['provider_updated_at'])}; <a href=\"{html.escape(item['provider_url'], quote=True)}\">amostra Redlisten</a>.")
    else:
        lines.append("⚠️ Não há uma recolha recente confirmada.")
    lines.append("\nSe a página exigir entrada, apresentar proteção ou não entregar publicações legíveis, fico sem dados. "
                 "Não contorno bloqueios. O RSS do Reddit terminou em 13/11/2026; não é usado. "
                 "Sem dados não há leitura de sentimento nem sinal social. Não vejo vídeos, áudio, comentários ou toda a internet. "
                 "Os posts são contexto não verificado: não alteram os filtros de entrada. /sociais · /pesquisa")
    return "\n".join(lines)
