from eagle_cevap_motoru import eagle_cevap_uret

# -*- coding: utf-8 -*-

def _son_mesajlar(gecmis, limit=6):
    sonuc = []

    for item in reversed(gecmis):
        if not isinstance(item, dict):
            continue

        rol = str(item.get("role", "")).strip().lower()
        metin = str(item.get("text", item.get("content", ""))).strip()

        if rol not in ("user", "assistant") or not metin:
            continue

        sonuc.append({
            "role": rol,
            "text": metin
        })

        if len(sonuc) >= limit:
            break

    return list(reversed(sonuc))


def _konusma_ozeti(gecmis):
    mesajlar = _son_mesajlar(gecmis)

    if not mesajlar:
        return ""

    return "\n".join(
        f"{item['role']}: {item['text']}"
        for item in mesajlar
    )


def _hafiza_bilgisi(hafiza):
    if isinstance(hafiza, list):
        return "\n".join(
            str(x).strip()
            for x in hafiza
            if str(x).strip()
        )

    return str(hafiza or "").strip()


def genel_sohbet(mesaj, gecmis=None, hafiza=None, karar=None, baglam=None):
    """
    EagleAI doğal konuşma motoru.

    Genel sohbet için Gemini veya başka bir harici model kullanmaz.
    Eagle'ın mevcut konuşma geçmişini, hafızasını ve kararını
    tek bir bağlam altında değerlendirir.
    """

    metin = str(mesaj or "").strip()

    if not metin:
        return "🦅 Buradayım."

    gecmis = gecmis if isinstance(gecmis, list) else []
    karar = karar if isinstance(karar, dict) else {}

    cevap_baglam = {
        "mesaj": metin,
        "konusma": _konusma_ozeti(gecmis),
        "hafiza": _hafiza_bilgisi(hafiza),
        "karar": karar,
        "baglam": baglam or "",
    }

    # Eagle'ın doğal konuşma bağlamı.
    #
    # Bu katman cevapları soru kalıplarına göre seçmez.
    # Üst cevap motorunun kullanacağı yapı burada hazırlanır.
    return eagle_cevap_uret(
        cevap_baglam["mesaj"],
        gecmis=gecmis,
        hafiza=hafiza,
        karar=karar,
        baglam=cevap_baglam["baglam"]
    )


if __name__ == "__main__":
    gecmis = [
        {"role": "user", "text": "Bugün biraz yoruldum."},
        {"role": "assistant", "text": "Yoğun bir gün olmuş gibi."},
    ]

    print(genel_sohbet(
        "Şimdi biraz dinlenmek istiyorum.",
        gecmis=gecmis,
        hafiza=["Kullanıcı EagleAI projesi üzerinde çalışıyor."],
        karar={"intent": "sohbet", "arac": "eagle_sohbet"}
    ))
