"""EagleAI için basit sohbet ve hafıza karar kuralları."""
import re

BASIT_SOHBET_KELIMELERI = [
    "merhaba", "selam", "selamlar", "günaydın", "gunaydin",
    "iyi akşamlar", "iyi aksamlar", "iyi geceler",
    "nasılsın", "nasilsin", "teşekkür ederim", "tesekkur ederim",
    "sağ ol", "sag ol", "kimsin", "sen kimsin",
    "senin adın ne", "senin adin ne", "ne yapabiliyorsun",
    "ne yapabilirsin"
]

_SELAM_ONAY = {
    "merhaba", "selam", "selamlar", "günaydın", "gunaydin",
    "tamam", "tamamdır", "tamamdir", "evet", "hayır", "hayir",
    "ok", "okey", "peki", "olur", "sağ ol", "sag ol",
    "teşekkürler", "tesekkurler", "teşekkür ederim", "tesekkur ederim",
    "eagle", "eagleai",
}

_SORU_FIIL = {
    "mı", "mi", "mu", "mü", "musun", "misin", "musunuz", "misiniz",
    "nedir", "kimdir", "kim", "ne", "nasıl", "nasil", "neden", "niye",
    "yap", "anlat", "ver", "söyle", "soyle", "bul", "yaz",
    "hesapla", "göster", "goster",
}


def _kucult(metin):
    return str(metin or "").replace("İ", "i").replace("I", "ı").lower()


def yazim_normalle(metin):
    k = _kucult(metin).strip(" ?!.,;:")
    k = re.sub(r"\bver(?:ir)?\s*m[iı]s[iı]n\b", "verir misin", k)
    return re.sub(r"\s+", " ", k)


def konu_adi_mi(metin):
    """1-4 kelimelik, her kelimesi büyük harfle başlayan yalın ad."""
    parca = str(metin or "").strip(" ?!.,;:").split()
    if not 1 <= len(parca) <= 4:
        return False
    if yazim_normalle(metin) in _SELAM_ONAY:
        return False
    if any(_kucult(p) in _SORU_FIIL for p in parca):
        return False
    return all(p[:1].isupper() for p in parca)


def _basit_sohbet_mi(k):
    kalan = k
    bulundu = False
    for x in sorted(BASIT_SOHBET_KELIMELERI, key=len, reverse=True):
        kalip = r"(?<!\w)" + re.escape(x) + r"(?!\w)"
        if re.search(kalip, kalan):
            bulundu = True
            kalan = re.sub(kalip, " ", kalan)
    # Selamın yanında asıl bir konu varsa bu basit sohbet değildir.
    return bulundu and len(kalan.split()) <= 2


def erken_sohbet_karari(metin, karar):
    """Eşleşen erken sohbet/hafıza kararını döndürür; eşleşme yoksa None."""
    k = _kucult(metin)

    if (
        _basit_sohbet_mi(k)
        and not (
            "program" in k
            and (
                "yap" in k
                or "yaz" in k
                or "oluştur" in k
                or "olustur" in k
                or "geliştir" in k
                or "gelistir" in k
            )
        )
    ):
        karar.update({
            "intent": "basit_sohbet",
            "guven": "yüksek",
            "neden": "Basit sohbet isteği algılandı.",
            "arac": "eagle_sohbet",
            "islem": "dogrudan_cevap",
            "dogrulama": True
        })
        return karar

    hafiza_kelimeleri = [
        "hatırla", "hatirla", "unutma",
        "hafızam", "hafizam", "hafıza", "hafiza",
        "daha önce sana", "daha once sana",
        "ne söylemiştim", "ne soylemistim",
        "hatırlıyor musun", "hatirliyor musun"
    ]

    if any(x in k for x in hafiza_kelimeleri):
        karar.update({
            "intent": "hafiza",
            "guven": "yüksek",
            "neden": "Hafıza ile ilgili bir istek algılandı.",
            "arac": "hafiza"
        })
        return karar

    return None
