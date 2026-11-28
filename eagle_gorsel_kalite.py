import re
import unicodedata
from urllib.parse import urlsplit


def normla(metin):
    metin = unicodedata.normalize(
        "NFKD", str(metin or "").casefold()
    )
    metin = "".join(
        c for c in metin
        if not unicodedata.combining(c)
    ).replace("ı", "i")
    return re.sub(r"[^a-z0-9]+", " ", metin).strip()


def uygun_mu(baslik, kaynak="", tur="place"):

    kategori = str(tur or "").lower()
    kelimeler = set(normla(baslik).split())

    kategori_engelleri = {
        "person": (
            "statue sculpture bust monument "
            "spacecraft rocket satellite rollout "
            "raumfrachter vessel ship "
            "quote quotation coin banknote "
            "stamp figurine toy replica "
            "heykel bust anit alinti"
        ),
        "animal": (
            "toy figurine plush costume "
            "statue sculpture tattoo "
            "mascot oyuncak heykel"
        ),
        "plant": (
            "artificial plastic toy "
            "costume tattoo figurine "
            "yapay oyuncak"
        )
    }

    engeller = set(
        kategori_engelleri.get(
            kategori, ""
        ).split()
    )

    if kelimeler & engeller:
        return False

    metin = normla(baslik)
    host = (urlsplit(kaynak).hostname or "").lower()

    if not metin:
        return False

    if re.search(
        r"\b(?:stock photo|stock image|stock illustration|ai generated|"
        r"image generator|wallpaper|"
        r"royalty free|sponsored)\b", metin
    ):
        return False

    if tur == "science":
        if host == "kunduz.com" or host.endswith(".kunduz.com"):
            return False

        if re.search(
            r"\b(?:asagidaki|yukaridaki|"
            r"soru cozumu|test sorusu|"
            r"question paper|exam question|"
            r"multiple choice|quiz)\b", metin
        ):
            return False

    if tur == "country":
        engelli = {
            "hdwallpapers.in",
            "10wallpaper.com"
        }
        if any(
            host == d or host.endswith("." + d)
            for d in engelli
        ):
            return False

        if re.search(
            r"\b(?:wallpaper|wallpapers|"
            r"photo preview|iconic buildings|"
            r"packing your bags|top \d+|"
            r"best places)\b", metin
        ):
            return False

        if re.search(
            r"\b(?:konut|villa|apartment|"
            r"residential project|private residence|"
            r"real estate|satilik|kiralik|"
            r"housing project|interior design)\b",
            metin
        ):
            return False

    return True


def bilim_turu(baslik):
    metin = normla(baslik)

    if re.search(
        r"\b(?:microscopy|micrograph|"
        r"microscope|mikroskop|tem|sem)\b", metin
    ):
        return "mikroskop"

    if re.search(
        r"\b(?:3d|spacefill|balls|"
        r"ball and stick|molecular model)\b", metin
    ):
        return "molekul_modeli"

    if re.search(
        r"\b(?:cycle|pathway|mechanism|"
        r"dongu|mekanizma|synthesis|sentez)\b",
        metin
    ):
        return "mekanizma"

    if re.search(
        r"\b(?:diagram|schematic|sema|"
        r"semasi|sematik|illustration|"
        r"structure|yapi|formula)\b", metin
    ):
        return "sema"

    return "diger"


def bilim_cesitlendir(items):
    items = bilim_dil_tekrarlarini_ayikla(items)
    sonuc = []
    alternatifler = []
    turler = set()
    adresler = set()
    basliklar = set()

    sirali = sorted(
        items,
        key=lambda x: x.get("_score", 0),
        reverse=True
    )

    for item in sirali:
        adres = item.get("url", "")
        baslik = normla(item.get("name", ""))

        if not adres or adres in adresler:
            continue

        if not baslik or baslik in basliklar:
            continue

        if not uygun_mu(
            item.get("name", ""),
            item.get("source", ""),
            "science"
        ):
            continue

        adresler.add(adres)
        basliklar.add(baslik)

        tur = bilim_turu(item.get("name", ""))

        if tur in turler:
            alternatifler.append(dict(item))
            continue

        turler.add(tur)
        sonuc.append(dict(item))

    return sonuc + alternatifler


def bilim_dil_tekrarlarini_ayikla(items):
    import re

    gruplar = {}

    for item in items:
        baslik = str(item.get("name", ""))
        eslesme = re.fullmatch(
            r"(.+?)[ _.-]([a-z]{2,3})\.(svg|png|jpg|jpeg)",
            baslik,
            flags=re.IGNORECASE
        )

        if eslesme:
            ana, dil, uzanti = eslesme.groups()
            dil = dil.lower()

            if dil in {
                "tr", "en", "de", "fr", "es",
                "it", "pt", "ru", "ar", "zh",
                "ja", "ko", "as", "ca", "cs",
                "et", "pl", "nl", "uk", "sv",
                "fi", "da", "no", "hu", "el"
            }:
                anahtar = ("dil", normla(ana))
                oncelik = (
                    2 if dil == "tr"
                    else 1 if dil == "en"
                    else 0
                )
            else:
                anahtar = ("normal", normla(baslik))
                oncelik = 0
        else:
            anahtar = ("normal", normla(baslik))
            oncelik = 0

        puan = (
            oncelik,
            item.get("_score", 0)
        )

        eski = gruplar.get(anahtar)

        if eski is None or puan > eski[0]:
            gruplar[anahtar] = (puan, item)

    return [
        item for _, item in gruplar.values()
    ]


def gorsel_kalite_puani(baslik, tur):
    """Kategoriye gore ana konu ve yardimci sahne puani."""
    metin = normla(baslik)
    kelimeler = set(metin.split())

    kurallar = {
        "person": (
            "portrait headshot face photograph portre",
            "rollout launch spacecraft rocket ship vessel "
            "raumfrachter beach quote quotation statue"
        ),
        "astronomy": (
            "surface hemispheric globe planet "
            "atmosphere terrain yuzey",
            "transit viewing visibility observation "
            "event launch spacecraft flyby"
        ),
        "object": (
            "closeup detail structure instrument "
            "detay yapi",
            "teacher player lesson concert tutorial "
            "student egitmen ogretmen ders"
        ),
        "animal": (
            "wildlife habitat herd portrait "
            "species dogal",
            "toy statue mascot costume"
        ),
        "plant": (
            "flower botanical leaf blossom "
            "species cicek yaprak",
            "artificial plastic decoration"
        ),
        "technology": (
            "mechanism structure engine machine "
            "diagram cutaway",
            "advertisement sale shop tutorial"
        )
    }

    olumlu, olumsuz = kurallar.get(tur, ("", ""))

    puan = min(
        len(kelimeler & set(olumlu.split())), 3
    ) * 12

    puan -= min(
        len(kelimeler & set(olumsuz.split())), 3
    ) * 18

    return puan


def gorsel_aile_anahtari(baslik):
    """Ayni gorselin duzenlenmis surumlerini gruplar."""
    metin = normla(baslik)

    ekler = {
        "cropped", "crop", "cleaned", "restored",
        "retouched", "edited", "colorized",
        "colourized", "enhanced", "resized",
        "jpg", "jpeg", "png", "webp", "tiff"
    }

    return " ".join(
        k for k in metin.split()
        if k not in ekler
    )


def genel_gorsel_cesitlendir(items, tur):
    """Kalite siralamasi ve gorsel ailesi tekrar kontrolu."""
    sirali = sorted(
        items,
        key=lambda x: (
            x.get("_score", 0)
            + gorsel_kalite_puani(
                x.get("name", ""), tur
            )
        ),
        reverse=True
    )

    sonuc = []
    gorulen = set()

    for item in sirali:
        anahtar = gorsel_aile_anahtari(
            item.get("name", "")
        )

        if not anahtar or anahtar in gorulen:
            continue

        gorulen.add(anahtar)
        sonuc.append(item)

    return sonuc
