from urllib.parse import urlsplit
import requests


def guvenilir_adres(url):
    try:
        u = urlsplit(url)
        host = (u.hostname or "").lower()

        if u.scheme != "https":
            return False

        if u.username or u.password:
            return False

        if u.port not in (None, 443):
            return False

        return (
            host in {
                "upload.wikimedia.org",
                "thumb.wikimedia.org",
                "live.staticflickr.com",
                "iiif.wellcomecollection.org"
            }
            or host.endswith(".mm.bing.net")
        )

    except (ValueError, TypeError):
        return False


def gorsel_formati(veri):
    if veri.startswith(b"\xff\xd8\xff"):
        return "jpeg"

    if veri.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"

    if veri[:4] == b"RIFF" and veri[8:12] == b"WEBP":
        return "webp"

    return None


def dogrula(url):
    if not guvenilir_adres(url):
        return False

    try:
        with requests.get(
            url,
            headers={
                "User-Agent": "EagleAI-Research/1.0"
            },
            timeout=(2, 3),
            stream=True,
            allow_redirects=False
        ) as r:

            if r.status_code != 200:
                return False

            veri = next(r.iter_content(64), b"")
            format_adi = gorsel_formati(veri)

            mime = r.headers.get(
                "Content-Type", ""
            ).split(";")[0].strip().lower()

            return bool(
                format_adi
                and mime == "image/" + format_adi
            )

    except requests.RequestException:
        return False
