"""HTTP restrito a fornecedores conhecidos. Nunca incluir URLs em erros."""
import json
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit


class ApiError(RuntimeError):
    pass


class Http:
    HOSTS = {"api.dexscreener.com": 0.3, "api.geckoterminal.com": 2.1,
             "api.telegram.org": 1.1, "api.github.com": 0.3,
             "www.coindesk.com": 1.0, "cointelegraph.com": 1.0, "decrypt.co": 1.0}

    def __init__(self):
        self.last = {}

    def json(self, url, payload=None, headers=None, method=None, retry=True, raw=False):
        host = urlsplit(url).hostname
        if urlsplit(url).scheme != "https" or host not in self.HOSTS:
            raise ApiError("Destino HTTP não autorizado")
        for attempt in range(3 if retry else 1):
            time.sleep(max(0, self.HOSTS[host] - (time.monotonic() - self.last.get(host, 0))))
            self.last[host] = time.monotonic()
            request = urllib.request.Request(url,
                data=json.dumps(payload, allow_nan=False).encode() if payload is not None else None,
                headers={"User-Agent": "MemecoinRadar/1.0", "Content-Type": "application/json",
                         **(headers or {})}, method=method)
            try:
                # API redirects are rejected: a redirect must never leak credentials.
                opener = urllib.request.build_opener(NoRedirect())
                with opener.open(request, timeout=15) as response:
                    body = response.read(8_000_001)
                    if len(body) > 8_000_000:
                        raise ApiError("Resposta demasiado grande")
                    return body if raw else json.loads(body)
            except urllib.error.HTTPError as error:
                if retry and (error.code == 429 or error.code >= 500) and attempt < 2:
                    try:
                        delay = min(30, max(2, float(error.headers.get("Retry-After", 2 ** (attempt + 1)))))
                    except (TypeError, ValueError):
                        delay = 4
                    error.close()
                    time.sleep(delay)
                    continue
                error.close()
                raise ApiError(f"{host}: HTTP {error.code}") from None
            except (urllib.error.URLError, TimeoutError, OSError, ValueError):
                if retry and attempt < 2:
                    time.sleep(2 ** (attempt + 1))
                    continue
                raise ApiError(f"{host}: indisponível ou resposta inválida") from None

    def text(self, url):
        return self.json(url, headers={"Accept": "application/rss+xml, application/xml"},
                         retry=False, raw=True).decode("utf-8")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None
