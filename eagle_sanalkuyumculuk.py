"""Sanal Kuyumculuk API verisini güvenli biçimde ayrıştırır."""

from datetime import datetime, timedelta
from urllib.parse import urlparse
from zoneinfo import ZoneInfo


ISTANBUL = ZoneInfo("Europe/Istanbul")
API_URL = "https://www.sanalkuyumculuk.com/altin-api.php"
HOST = "sanalkuyumculuk.com"

# Yalnızca yeni tip ürünler; eski/yeni varyantları karıştırma.
PRODUCTS = {
    0: "Gram Altın",
    35: "Çeyrek Altın",
    37: "Yarım Altın",
    39: "Tam Altın",
    49: "Ata Altın",
}


def _aktif_mi(value):
    if value is True or value == 1:
        return True
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1")
    return False


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
            # 6.576 biçimindeki binlik ayırıcı.
            text = text.replace(".", "")
        result = float(text)
        if not 500 <= result <= 100000:
            return None
        return result
    except (TypeError, ValueError, OverflowError):
        return None


def _zaman(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ISTANBUL)
        return parsed.astimezone(ISTANBUL)
    except (TypeError, ValueError, OverflowError):
        return None


def parse_payload(payload, url=API_URL, now=None):
    """API JSON nesnesini altin_tablo_oku kayıt biçiminde döndürür."""
    try:
        parsed_url = urlparse(url)
        if (
            parsed_url.scheme != "https"
            or (parsed_url.hostname or "").lower().rstrip(".") not in
            (HOST, "www." + HOST)
            or parsed_url.path.rstrip("/") != "/altin-api.php"
        ):
            return []

        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            return []

        if now is None:
            now = datetime.now(ISTANBUL)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=ISTANBUL)
        else:
            now = now.astimezone(ISTANBUL)

        records = {}

        for item in payload["data"]:
            if not isinstance(item, dict):
                continue

            try:
                product_id = int(item.get("id"))
            except (TypeError, ValueError):
                continue

            product_name = PRODUCTS.get(product_id)
            if not product_name:
                continue

            if not all(_aktif_mi(item.get(key)) for key in (
                "isVisible", "buyTradeStatus", "sellTradeStatus"
            )):
                continue

            updated = _zaman(item.get("updatedAt"))
            if updated is None:
                continue

            age = now - updated
            if age < timedelta(seconds=-30) or age > timedelta(minutes=5):
                continue

            buy = _fiyat(item.get("customerBuysAt"))
            sell = _fiyat(item.get("customerSellsAt"))
            if buy is None or sell is None:
                continue

            record = {
                "urun": product_name,
                "alis": buy,
                "satis": sell,
                "url": API_URL,
                "host": HOST,
                "tarih": updated.date().isoformat(),
                "tarih_kapsami": "urun",
                "ham": item,
            }

            previous = records.get(product_id)
            if previous is None or updated > previous[0]:
                records[product_id] = (updated, record)

        return [
            records[product_id][1]
            for product_id in PRODUCTS
            if product_id in records
        ]
    except Exception:
        return []
