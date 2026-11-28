import re
from eagle_gorsel_kalite import normla


ULKELER = set("""
kanada avusturya norvec isvec finlandiya
almanya fransa italya ispanya portekiz
yunanistan japonya cin abd amerika
ingiltere isvicre hollanda belcika
brezilya arjantin avustralya meksika
hindistan rusya ukrayna iran irak
turkiye misir danimarka izlanda
polonya romanya bulgaristan
""".split())

BILIM_KOKLERI = set("""
hucre molekul enzim organel organizma
protein atom elektron proton notron
biyoloji kimya fizik biyokimya
mikroskop kromozom bakteri virus
genetik ribozom mitokondri
fotosentez metabolizma
""".split())

EKLER = (
    r"(?:ler|lar)?"
    r"(?:imiz|umuz|iniz|unuz|si|su|i|u)?"
    r"(?:nin|nun|in|un|de|da|te|ta|"
    r"den|dan|ten|tan|ye|ya|e|a)?"
    r"(?:dir|dur|tir|tur)?"
)

BILIM_KALIBI = re.compile(
    r"\b(?:"
    + "|".join(sorted(BILIM_KOKLERI))
    + r")" + EKLER + r"\b"
)

BILIM_EN = set("""
biological chemical physical biochemical
molecule molecules cell cells enzyme enzymes
microscope microscopy organism organisms
physiological protein proteins organelle
organelles chromosome chromosomes
mitochondria mitochondrion ribosome
photosynthesis metabolism
""".split())


def tur_sozcugu_var(metin, kokler):
    """Tam kelime veya kontrollu Turkce ek eslesmesi."""
    metin = normla(metin)

    ekler = (
        r"(?:lar|ler)?"
        r"(?:si|su|i|u|imiz|umuz|iniz|unuz)?"
        r"(?:nin|nun|in|un|de|da|den|dan|"
        r"te|ta|ten|tan|ye|ya|e|a)?"
        r"(?:dir|dur|tir|tur)?"
    )

    kelimeler = set(metin.split())

    for kok in kokler:
        if kok in kelimeler:
            return True

        if len(kok) >= 3:
            if re.search(
                r"\b" + re.escape(kok)
                + ekler + r"\b",
                metin
            ):
                return True

    return False


def bilimsel_mi(metin):
    metin = normla(metin)

    return bool(
        BILIM_KALIBI.search(metin)
        or set(metin.split()) & BILIM_EN
    )


def siniflandir(
    konu,
    cevap="",
    aciklama="",
    etiketler=(),
    tarihsel=False,
    ulke_eslesmesi=False
):
    k = normla(konu)
    ks = set(k.split())

    varlik = normla(
        " ".join(map(str, etiketler))
        + " " + str(aciklama or "")
    )

    vs = set(varlik.split())
    cs = set(normla(cevap).split())

    if tarihsel:
        return "event"

    # Sehir devletleri cografi sehirlerden once gelir.
    if any(x in varlik for x in (
        "sovereign city state",
        "independent city state",
        "sovereign state",
        "egemen sehir devleti"
    )):
        return "country"

    # Varlik aciklamasina dayali genel tur tanima.
    # Konu isimleri degil, tur bilgileri kullanilir.
    tanim = normla(aciklama or "")
    tanim_kelimeleri = set(tanim.split())

    tur_kurallari = {
        "person": (
            "physicist scientist mathematician "
            "politician statesman actor actress "
            "musician composer writer author "
            "athlete footballer officer inventor "
            "historian philosopher engineer "
            "bilim insani fizikci yazar sanatci "
            "siyasetci sporcu asker besteci"
        ),
        "plant": (
            "plant botanical flowering flora "
            "bitki botanik cicek"
        ),
        "animal": (
            "animal mammal bird reptile amphibian "
            "fish insect feline feline cat canine "
            "hayvan memeli kus surungen bocek kedi kopek"
        ),
        "technology": (
            "engine machine device computer "
            "processor turbine technology "
            "motor makine cihaz teknoloji"
        ),
        "object": (
            "instrument furniture tool utensil "
            "musical enstruman mobilya alet esya calgi"
        ),
        "landmark": (
            "tower monument temple castle "
            "cathedral palace statue "
            "kule anit tapinak saray"
        )
    }

    # Aciklama icindeki tur sozcuklerini kullan.
    for aday_tur, kelimeler in tur_kurallari.items():
        if tur_sozcugu_var(tanim, kelimeler.split()):
            return aday_tur

    kurallar = {
        "water": """
            okyanus okyanusu deniz denizi ocean sea
        """,
        "landmark": """
            piramit piramitleri pyramid pyramids
            tapinak temple castle kale
            monument anit heykel
        """,
        "nature": """
            dag daglari mountain gol golu lake
            nehir river ada island orman forest
            selale waterfall volkan volcano
        """,
        "city": """
            sehir sehri sehirleri kent kenti kentleri city town baskent baskenti capital
        """
    }

    for tur, kelimeler in kurallar.items():
        if ks & set(kelimeler.split()):
            return tur

    if ulke_eslesmesi or k in ULKELER:
        return "country"

    if vs & {
        "country", "ulke", "devlet",
        "republic", "kingdom"
    } or "sovereign state" in varlik:
        return "country"

    for tur, kelimeler in kurallar.items():
        if vs & set(kelimeler.split()):
            return tur

    if "body of water" in varlik:
        return "water"

    if any(x in varlik for x in (
        "historic site", "tarihi eser"
    )):
        return "landmark"

    if any(x in varlik for x in (
        "national park", "natural feature"
    )):
        return "nature"

    astronomi = set("""
        planet gezegen asteroid asteroit
        comet kuyrukluyildiz star yildiz
        satellite uydu galaxy galaksi
    """.split())

    if tur_sozcugu_var(k + " " + varlik, astronomi):
        return "astronomy"

    if bilimsel_mi(k + " " + varlik):
        return "science"

    if cs & astronomi:
        return "astronomy"

    if bilimsel_mi(cevap):
        return "science"

    return "unknown"
