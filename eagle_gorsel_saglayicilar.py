from eagle_gorsel_hiz_siniri import kontrollu_get
from eagle_openverse_arastirma import (
    arastir, kavram_coz
)
from eagle_gorsel_kabul import openverse_puanla


def openverse_saglayici(
    konu,
    tur,
    ingilizce_ad="",
    etiketler=()
):
    kavramlar = kavram_coz(
        konu, ingilizce_ad, etiketler
    )

    def calistir(yayinla, kalan):
        if kalan() <= 0:
            return

        adaylar = arastir(
            konu,
            tur,
            ingilizce_ad,
            etiketler
        )

        for aday in adaylar:
            if kalan() <= 0:
                break

            puan = openverse_puanla(
                aday, kavramlar, tur
            )

            if puan < 10:
                continue

            sonuc = dict(aday)
            sonuc["_score"] = puan + 20

            yayinla(sonuc)

    return calistir


def wikimedia_saglayici(
    konu,
    tur,
    ingilizce_ad="",
    etiketler=()
):
    import requests
    import re

    from eagle_gorsel_kalite import (
        normla, uygun_mu
    )
    from eagle_gorsel_dogrulama import dogrula

    kavramlar = kavram_coz(
        konu, ingilizce_ad, etiketler
    )

    ad = kavramlar[0] if kavramlar else konu

    terimler = {
        "science": (
            "diagram", "microscopy", "structure"
        ),
        "country": (
            "landmark", "national park", "city"
        ),
        "astronomy": (
            "NASA", "telescope"
        ),
        "landmark": (
            "exterior", "photograph"
        ),
        "nature": (
            "landscape", "photograph"
        ),
        "water": (
            "ocean", "photograph"
        ),
        "city": (
            "skyline", "architecture"
        )
    }.get(tur, ("photograph",))

    def calistir(yayinla, kalan):
        for terim in terimler:
            if kalan() < 1:
                break

            r = kontrollu_get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "search",
                    "gsrsearch": f"{ad} {terim}",
                    "gsrnamespace": 6,
                    "gsrlimit": 12,
                    "prop": "imageinfo",
                    "iiprop": "url|mime|size|extmetadata",
                    "iiurlwidth": 800,
                    "format": "json"
                },
                headers={
                    "User-Agent": "EagleAI-Research/1.0"
                },
                timeout=min(3, kalan()),
                allow_redirects=False
            )

            if r.status_code == 429:
                print("WIKIMEDIA: 429", flush=True)
                return

            r.raise_for_status()

            pages = r.json().get(
                "query", {}
            ).get("pages", {})

            for page in pages.values():
                if kalan() < 1:
                    return

                info = (
                    page.get("imageinfo") or [{}]
                )[0]

                title = page.get(
                    "title", ""
                ).removeprefix("File:")

                url = info.get("thumburl") or info.get("url")
                source = info.get("descriptionurl", "")

                if not url or not source:
                    continue

                if not uygun_mu(title, source, tur):
                    continue

                metin = normla(title)

                if not any(
                    f" {normla(k)} " in f" {metin} "
                    for k in kavramlar
                    if len(normla(k)) >= 3
                ):
                    continue

                w = info.get("width") or 0
                h = info.get("height") or 0

                if min(w, h) < 200:
                    continue

                if max(w, h) / min(w, h) > 3:
                    continue

                if not dogrula(url):
                    continue

                meta = info.get("extmetadata") or {}

                def alan(key):
                    value = meta.get(
                        key, {}
                    ).get("value", "")
                    return re.sub(
                        r"<[^>]+>", "", str(value)
                    ).strip()

                lisans = alan("LicenseShortName")
                yazar = alan("Artist")

                if not lisans or not yazar:
                    continue

                yayinla({
                    "url": url,
                    "name": title,
                    "source": source,
                    "provider": "Wikimedia Commons",
                    "type": "image",
                    "license": lisans,
                    "license_url": alan("LicenseUrl"),
                    "creator": yazar,
                    "width": w,
                    "height": h,
                    "_score": 75
                })

    return calistir
