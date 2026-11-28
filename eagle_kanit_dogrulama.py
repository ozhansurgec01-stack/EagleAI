"""Eagle merkezi kanit karsilastirma katmani."""

import re
from collections import defaultdict
from eagle_arastirma_v2 import kavram_norm


SAYILAR = {
    "sifir": "0",
    "bir": "1",
    "iki": "2",
    "uc": "3",
    "dort": "4",
    "bes": "5",
    "alti": "6",
    "yedi": "7",
    "sekiz": "8",
    "dokuz": "9",
    "on": "10",
}

SAYI_DESENI = re.compile(
    r"\b(?:\d+|" + "|".join(SAYILAR) + r")\b"
)


def sayisal_imza(metin):
    # Ondalik, aralik ve karmasik sayilari simdilik atla.
    if re.search(r"\d[.,/-]\d", metin):
        return None

    n = kavram_norm(metin)

    if re.search(
        r"\b(?:yaklasik|ortalama|en az|en fazla|"
        r"civarinda|milyon|milyar|bin|yuz|"
        r"eskiden|guncel|arasinda)\b",
        n
    ):
        return None

    eslesmeler = list(SAYI_DESENI.finditer(n))

    if len(eslesmeler) != 1:
        return None

    m = eslesmeler[0]
    deger = SAYILAR.get(m.group(), m.group())

    imza = n[:m.start()] + "<sayi>" + n[m.end():]

    return imza, int(deger)


def celiskileri_bul(adaylar):
    gruplar = defaultdict(list)

    for aday in adaylar:
        imza = sayisal_imza(aday.get("text", ""))

        if imza is None:
            continue

        anahtar, deger = imza
        gruplar[anahtar].append((deger, aday))

    sonuc = []

    for anahtar, grup in gruplar.items():
        degerler = {deger for deger, _ in grup}
        hostlar = {
            aday.get("host")
            for _, aday in grup
            if aday.get("host")
        }

        if len(degerler) < 2 or len(hostlar) < 2:
            continue

        sonuc.append({
            "type": "numeric_disagreement",
            "signature": anahtar,
            "values": sorted(degerler),
            "evidence": [
                {
                    "value": deger,
                    "text": aday["text"],
                    "source": aday["url"]
                }
                for deger, aday in grup
            ],
            "resolved": False
        })

    return sonuc
