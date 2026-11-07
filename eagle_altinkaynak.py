"""Altınkaynak Gold JSON verisini güvenli biçimde ayrıştırır."""
from datetime import datetime, timedelta
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ISTANBUL = ZoneInfo("Europe/Istanbul")
API_URL = "https://static.altinkaynak.com/public/Gold"
HOST = "static.altinkaynak.com"

# Şimdilik yalnızca iki kaynak arasında fiyatı doğrulanmış ürün.
PRODUCTS = {"GA": "Gram Altın"}


def _fiyat(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        text = str(value).strip().replace(" ", "")
        if not text:
            return None
        if "," in text and "." in text:
            if text.rfind(",") > text.rfind("."):
                text = text.replace(".", "").replace(",", ".")
            else:
                text = text.replace(",", "")
        elif "," in text:
            text = text.replace(",", ".")
        elif text.count(".") > 1:
            text = text.replace(".", "")
        elif len(text.split(".")[-1]) == 3 and text.split(".")[0].isdigit():
            text = text.replace(".", "")
        result = float(text)
        return result if 500 <= result <= 100000 else None
    except (TypeError, ValueError, OverflowError):
        return None


def _zaman(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.strptime(value.strip(), "%d.%m.%Y %H:%M:%S")
        return parsed.replace(tzinfo=ISTANBUL)
    except (TypeError, ValueError, OverflowError):
        return None


def parse_payload(payload, url=API_URL, now=None):
    """Altınkaynak JSON dizisini ortak altın kayıt biçimine dönüştürür."""
    try:
        parsed_url = urlparse(url)
        if (
            parsed_url.scheme != "https"
            or (parsed_url.hostname or "").lower().rstrip(".") != HOST
            or parsed_url.path.rstrip("/") != "/public/Gold"
        ):
            return []

        if not isinstance(payload, list):
            return []

        if now is None:
            now = datetime.now(ISTANBUL)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=ISTANBUL)
        else:
            now = now.astimezone(ISTANBUL)

        records = {}
        for item in payload:
            if not isinstance(item, dict):
                continue

            code = str(item.get("Kod", "")).strip().upper()
            product = PRODUCTS.get(code)
            if not product:
                continue

            updated = _zaman(item.get("GuncellenmeZamani"))
            if updated is None:
                continue

            age = now - updated
            if age < timedelta(seconds=-30) or age > timedelta(minutes=5):
                continue

            buy = _fiyat(item.get("Alis"))
            sell = _fiyat(item.get("Satis"))
            if buy is None or sell is None:
                continue

            record = {
                "urun": product,
                "alis": buy,
                "satis": sell,
                "url": API_URL,
                "host": HOST,
                "tarih": updated.date().isoformat(),
                "tarih_kapsami": "urun",
                "ham": item,
            }
            previous = records.get(code)
            if previous is None or updated > previous[0]:
                records[code] = (updated, record)

        return [records[code][1] for code in PRODUCTS if code in records]
    except Exception:
        return []
