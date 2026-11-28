import requests
from eagle_gorsel_dogrulama import guvenilir_adres
from eagle_gorsel_kalite import uygun_mu, normla

API = "https://api.openverse.org/v1/images/"

LISANSLAR = {"cc0", "pdm", "by", "by-sa"}


def adaylari_ayikla(items, kavramlar, tur="place"):
    sonuc = []
    gorulen = set()

    kavramlar = [
        normla(k) for k in kavramlar if normla(k)
    ]

    if not kavramlar:
        return []

    for item in items:
        if not isinstance(item, dict):
            continue

        baslik = str(item.get("title") or "")
        url = str(item.get("url") or "")
        kaynak = str(item.get("foreign_landing_url") or "")
        lisans = str(item.get("license") or "").lower()
        yazar = str(item.get("creator") or "")

        if lisans not in LISANSLAR:
            continue

        if not kaynak.startswith("https://"):
            continue

        if lisans in {"by", "by-sa"} and not yazar:
            continue

        if not guvenilir_adres(url):
            continue

        if url in gorulen:
            continue

        if not uygun_mu(baslik, kaynak, tur):
            continue

        metin = " " + normla(baslik) + " "

        if not any(
            " " + k + " " in metin
            for k in kavramlar
        ):
            continue

        if any(
            " " + k + " " in metin
            for k in (
                "shirt", "t shirt", "tattoo",
                "costume", "toy", "merchandise"
            )
        ):
            continue

        if tur == "science":
            uzun_eslesme = any(
                len(k) >= 4 and " " + k + " " in metin
                for k in kavramlar
            )

            bilimsel_baglam = any(
                " " + k + " " in metin
                for k in (
                    "molecule", "molecular", "structure",
                    "diagram", "cycle", "synthesis",
                    "synthase", "model", "3d", "anion",
                    "microscopy", "micrograph",
                    "protein", "enzyme", "cell",
                    "adp", "datp", "dna", "rna",
                    "chemical", "biological",
                    "mekanizma", "molekul", "sema",
                    "hucre", "sentez", "yapi"
                )
            )

            if not uzun_eslesme and not bilimsel_baglam:
                continue

        try:
            w = int(item.get("width") or 0)
            h = int(item.get("height") or 0)
        except (ValueError, TypeError):
            continue

        if min(w, h) < 200:
            continue

        if max(w, h) / min(w, h) > 3:
            continue

        if url.split("?")[0].lower().endswith(
            (".svg", ".gif", ".pdf")
        ):
            continue

        gorulen.add(url)

        sonuc.append({
            "name": baslik,
            "url": url,
            "source": kaynak,
            "provider": "Openverse",
            "original_provider": item.get("source"),
            "creator": yazar,
            "license": lisans,
            "license_url": item.get("license_url"),
            "width": w,
            "height": h,
            "type": "image"
        })

    return sonuc


def ara(sorgu, kavramlar, tur="place"):
    try:
        r = requests.get(
            API,
            params={
                "q": sorgu,
                "page_size": 20,
                "license": "cc0,pdm,by,by-sa"
            },
            headers={
                "User-Agent": "EagleAI-Research/1.0"
            },
            timeout=(2, 4),
            allow_redirects=False
        )

        if r.status_code != 200:
            print("OPENVERSE HTTP:", r.status_code)
            return []

        return adaylari_ayikla(
            r.json().get("results", []),
            kavramlar,
            tur
        )

    except (requests.RequestException, ValueError):
        return []
