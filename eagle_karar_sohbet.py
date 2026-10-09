"""EagleAI için basit sohbet ve hafıza karar kuralları."""


def erken_sohbet_karari(metin, karar):
    """Eşleşen erken sohbet/hafıza kararını döndürür; eşleşme yoksa None."""
    k = metin.lower()

    basit_sohbet_kelimeleri = [
        "merhaba", "selam", "selamlar", "günaydın", "gunaydin",
        "iyi akşamlar", "iyi aksamlar", "iyi geceler",
        "nasılsın", "nasilsin", "teşekkür ederim", "tesekkur ederim",
        "sağ ol", "sag ol", "kimsin", "sen kimsin",
        "senin adın ne", "senin adin ne", "ne yapabiliyorsun",
        "ne yapabilirsin"
    ]

    if (
        any(x in k for x in basit_sohbet_kelimeleri)
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
