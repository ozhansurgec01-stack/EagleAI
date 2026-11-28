import re
from urllib.parse import urlsplit

from eagle_gorsel_kalite import normla, uygun_mu
from eagle_gorsel_dogrulama import guvenilir_adres


def openverse_puanla(aday, kavramlar, tur):
    if not isinstance(aday, dict):
        return -100

    if aday.get("provider") != "Openverse":
        return -100

    baslik = str(aday.get("name") or "")
    kaynak = str(aday.get("source") or "")
    url = str(aday.get("url") or "")
    lisans = aday.get("license")
    yazar = str(aday.get("creator") or "").strip()

    if not guvenilir_adres(url):
        return -100

    if not kaynak.startswith("https://"):
        return -100

    if lisans not in {"cc0", "pdm", "by", "by-sa"}:
        return -100

    if lisans in {"by", "by-sa"} and not yazar:
        return -100

    if not uygun_mu(baslik, kaynak, tur):
        return -100

    try:
        w = int(aday.get("width") or 0)
        h = int(aday.get("height") or 0)

        if min(w, h) < 200:
            return -100

        if max(w, h) / min(w, h) > 3:
            return -100

    except (TypeError, ValueError):
        return -100

    metin = normla(baslik)
    kelimeler = set(metin.split())

    adlar = [
        normla(k) for k in kavramlar
        if len(normla(k)) >= 3
    ]

    eslesen = [
        k for k in adlar
        if f" {k} " in f" {metin} "
    ]

    if not eslesen:
        return -100

    if "?" in baslik:
        return -100

    if re.search(
        r"\b(?:metaphor|meme|joke|cartoon|"
        r"shirt|tattoo|costume|toy|merchandise|"
        r"wallpaper|advertisement|stock)\b",
        metin
    ):
        return -100

    puan = 45

    if tur == "science":
        baglam = {
            "cell", "cells", "nuclei",
            "cytoskeleton", "mouse",
            "molecule", "molecular",
            "structure", "diagram",
            "microscopy", "micrograph",
            "microscope", "cycle",
            "adp", "datp", "protein",
            "enzyme", "anion", "3d",
            "balls", "spacefill",
            "synthesis", "model"
        }

        bilimsel = kelimeler & baglam

        if not bilimsel:
            return -100

        puan += min(len(bilimsel), 5) * 6

    elif tur == "person":
        # A name match alone does not establish a portrait.
        if re.search(r"\b(?:ariane|atv|launch|start|beach|versus|vs|transit)\b", metin):
            return -100
        portrait = kelimeler & {"portrait", "photograph", "photo", "face", "portre", "fotograf"}
        if not portrait and metin not in adlar:
            return -100
        puan += 15 if portrait else 0

    elif tur == "country":
        sahne = {
            "photo", "photos", "photography",
            "landscape", "scenery", "view",
            "panorama", "mountain", "lake",
            "fjord", "forest", "waterfall",
            "city", "skyline", "street",
            "architecture", "castle",
            "cathedral", "palace",
            "park", "bridge", "coast"
        }

        if not kelimeler & sahne:
            return -100

        if re.search(
            r"\b(?:guide|tour package|"
            r"book now|travel agency)\b",
            metin
        ):
            return -100

        puan += 15

    else:
        baglamlar = {
            "astronomy": "planet nasa telescope orbit space surface galaxy satellite",
            "animal": "animal wildlife species mammal bird reptile habitat",
            "plant": "plant botanical flower leaf species garden",
            "person": "portrait photograph photo",
            "technology": "machine engine device mechanism structure model",
            "city": "city skyline street architecture building",
            "landmark": "monument exterior architecture photograph",
            "nature": "landscape mountain forest lake waterfall",
            "water": "ocean sea waves coast water marine",
            "event": "historical archive photograph mission"
        }

        genel_baglam = set(
            "photo photograph photography image illustration "
            "portrait structure diagram model archive".split()
        )

        kategori_baglam = set(
            baglamlar.get(tur, "").split()
        )

        puan += min(
            len(kelimeler & kategori_baglam), 5
        ) * 6

        puan += min(
            len(kelimeler & genel_baglam), 3
        ) * 3

    return puan
