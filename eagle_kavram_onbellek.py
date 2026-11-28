import time
import threading
from copy import deepcopy
from collections import OrderedDict

from eagle_arastirma_v2 import kavram_norm

_KILIT = threading.Lock()
_CACHE = OrderedDict()

TTL = 300
KAPASITE = 256


def kaynaklari_sakla(soru, kaynaklar):
    if not isinstance(kaynaklar, list):
        return False

    anahtar = kavram_norm(soru)

    if not anahtar:
        return False

    from urllib.parse import urlsplit

    temiz = []

    for k in kaynaklar:
        if not isinstance(k, dict):
            continue

        url = urlsplit(str(k.get("url") or ""))

        if url.scheme != "https":
            continue

        if url.hostname != "tr.wikipedia.org":
            continue

        if k.get("content_loaded") is not True:
            continue

        temiz.append(deepcopy(k))

        if len(temiz) >= 5:
            break

    if not temiz:
        return False

    with _KILIT:
        _CACHE[anahtar] = (
            time.monotonic(), temiz
        )

        _CACHE.move_to_end(anahtar)

        while len(_CACHE) > KAPASITE:
            _CACHE.popitem(last=False)

    return True


def kaynaklari_al(soru):
    anahtar = kavram_norm(soru)

    with _KILIT:
        kayit = _CACHE.get(anahtar)

        if kayit is None:
            return []

        tarih, kaynaklar = kayit

        if time.monotonic() - tarih >= TTL:
            _CACHE.pop(anahtar, None)
            return []

        _CACHE.move_to_end(anahtar)

        return deepcopy(kaynaklar)
