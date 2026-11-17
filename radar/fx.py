"""BCE: câmbio diário de referência, apenas para contas fictícias em EUR."""
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from .http import ApiError
from .model import number

URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"


def valid(fx, now):
    rate = number(fx.get("usd_per_eur"))
    day = number(fx.get("date_at"))
    return rate is not None and rate > 0 and day is not None and 0 <= now - day <= 4 * 86400


def parse(text, now):
    if len(text) > 200000 or "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise ValueError("XML de câmbio inválido")
    root = ET.fromstring(text)
    dated = next((e for e in root.iter() if e.attrib.get("time")), None)
    if dated is None:
        raise ValueError("Data de câmbio ausente")
    day = datetime.strptime(dated.attrib["time"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    usd = next((e for e in dated.iter() if e.attrib.get("currency") == "USD"), None)
    fx = {"date": day.strftime("%Y-%m-%d"), "date_at": day.timestamp(),
          "usd_per_eur": number(usd.attrib.get("rate")) if usd is not None else None,
          "fetched_at": now, "source": URL}
    if not valid(fx, now):
        raise ValueError("Câmbio ausente, futuro ou desatualizado")
    return fx


def refresh(data, http, now):
    fx = data.setdefault("fx", {})
    interval = 21600 if fx.get("status") == "ok" else 900
    if now - fx.get("last_attempt", -1e20) < interval:
        return
    fx["last_attempt"] = now
    try:
        updated = parse(http.text(URL), now)
        data["fx"] = {**updated, "last_attempt": now, "status": "ok"}
    except (ApiError, ValueError, ET.ParseError, UnicodeError, StopIteration):
        fx["status"] = "indisponível; última referência, se ainda válida"
