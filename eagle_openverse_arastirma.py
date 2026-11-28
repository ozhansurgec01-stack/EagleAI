from concurrent.futures import ThreadPoolExecutor
from eagle_openverse import ara
from eagle_gorsel_dogrulama import dogrula
from eagle_gorsel_kalite import normla

# Canli testlerde kullanilan baslangic kavramlari.
KAVRAMLAR = {
    "mitokondri": ("mitochondria", "mitochondrion"),
    "atp": ("adenosine triphosphate", "ATP"),
    "norvec": ("Norway",),
    "kanada": ("Canada",),
}


def kavram_coz(konu, ingilizce_ad="", etiketler=()):
    adaylar = [
        ingilizce_ad,
        *KAVRAMLAR.get(normla(konu), ()),
        konu,
        *etiketler
    ]

    sonuc = []
    gorulen = set()

    for aday in adaylar:
        aday = str(aday or "").strip()
        anahtar = normla(aday)

        if anahtar and anahtar not in gorulen:
            gorulen.add(anahtar)
            sonuc.append(aday)

    return sonuc


def arastir(konu, tur, ingilizce_ad="", etiketler=()):
    kavramlar = kavram_coz(
        konu, ingilizce_ad, etiketler
    )

    if not kavramlar:
        return []

    ana = kavramlar[0]

    if tur == "country":
        sorgu = f"{ana} landmarks landscape"
    elif tur == "science":
        sorgu = ana
    else:
        sorgu = ana

    adaylar = ara(sorgu, kavramlar, tur)[:8]

    if not adaylar:
        return []

    with ThreadPoolExecutor(max_workers=4) as pool:
        durumlar = list(pool.map(
            dogrula,
            [a["url"] for a in adaylar]
        ))

    return [
        dict(a)
        for a, ok in zip(adaylar, durumlar)
        if ok
    ]
