import time
import threading
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

import requests

_KILIT = threading.Lock()
_BEKLEME = {}


def kontrollu_get(url, **kwargs):
    host = urlsplit(url).hostname or ""

    with _KILIT:
        if time.monotonic() < _BEKLEME.get(host, 0):
            raise requests.HTTPError(
                f"429: {host} ortak bekleme suresinde"
            )

    yanit = requests.get(url, **kwargs)

    if yanit.status_code == 429:
        retry = yanit.headers.get("Retry-After", "60")

        try:
            sure = float(retry)
        except (ValueError, TypeError):
            try:
                sure = (
                    parsedate_to_datetime(retry).timestamp()
                    - time.time()
                )
            except (ValueError, TypeError, OverflowError):
                sure = 60

        with _KILIT:
            _BEKLEME[host] = max(
                _BEKLEME.get(host, 0),
                time.monotonic() + max(1, sure)
            )

        raise requests.HTTPError(
            f"429: {host} gecici bekleme",
            response=yanit
        )

    return yanit
