"""Eagle anlamsal varlik turu katmani."""

import re
from eagle_arastirma_v2 import kavram_norm


TURLER = {
    "dwarf_planet": ("cuce gezegen",),
    "natural_satellite": ("dogal uydu",),
    "planet": ("gezegen",),
    "star": ("yildiz",),
    "deity": ("tanri", "tanrica", "tanrisi"),
    "musical_instrument": (
        "muzik aleti", "muzik alet",
        "yayli calgi", "calgi", "enstruman"
    ),
    "scientist": (
        "bilim insani", "fizikci",
        "matematikci", "kimyaci", "biyolog"
    ),
    "animal": (
        "hayvan", "memeli", "yilan",
        "surungen", "kus", "balik", "bocek"
    ),
    "plant": ("bitki",),
    "game_piece": ("satranc tasi", "oyun tasi"),
    "programming_language": ("programlama dili",),
    "chemical_element": ("kimyasal element",),
    "chemical_compound": ("kimyasal bilesik",),
    "country": ("ulke", "egemen devlet"),
    "city": ("sehir", "kent"),
}

EKLER = (
    r"(?:dir|dur|tir|tur|"
    r"idir|udur|sidir|sudur|"
    r"idirler|dirler|durler)?"
)


def anlamsal_tur(tanim):
    n = kavram_norm(tanim)

    # Olumsuz, tarihsel ve kesin olmayan ifadeler.
    if re.search(
        r"\b(?:degil\w*|eskiden|onceden|"
        r"iddia\w*|varsay\w*|sanil\w*|"
        r"olabilir|muhtemelen|tarafindan|"
        r"olarak|oldugu|benzer)\b",
        n
    ):
        return "unknown"

    # Birlesik tur ifadelerinde kesin karar verme.
    if re.search(r"\b(?:ve|veya|yahut|ya da)\b", n):
        return "unknown"

    bulunan = set()

    for tur, ifadeler in TURLER.items():
        for ifade in ifadeler:
            desen = (
                r"(?<!\w)" + re.escape(ifade)
                + EKLER + r"(?!\w)"
            )

            if re.search(desen + r"$", n):
                bulunan.add(tur)
                break

    if re.search(
        r"\b(?:yilan|kus|balik|bocek|"
        r"memeli|surungen|hayvan)"
        r"\s+(?:cinsidir|turudur|ailesindendir)$",
        n
    ):
        bulunan.add("animal")

    # Daha ozel astronomi turunu koru.
    if "dwarf_planet" in bulunan:
        bulunan.discard("planet")

    # Birden fazla tur varsa tahmin yapma.
    if len(bulunan) != 1:
        return "unknown"

    return next(iter(bulunan))


def tur_iliskisi(a, b):
    if "unknown" in (a, b):
        return "undetermined"

    if a == b:
        return "compatible"

    # Farkli turler tek basina celiski kaniti degildir.
    return "different_type"
