# -*- coding: utf-8 -*-

def eagle_cevap_uret(mesaj, gecmis=None, hafiza=None, karar=None):
    """
    EagleAI yerel doğal cevap motoru.

    Harici bir metin modeli kullanmaz.
    Mesajı; konuşma geçmişi, hafıza ve karar motorunun
    verdiği bağlamla birlikte değerlendirir.
    """

    mesaj = str(mesaj or "").strip()
    gecmis = gecmis if isinstance(gecmis, list) else []
    hafiza = hafiza if isinstance(hafiza, list) else []
    karar = karar if isinstance(karar, dict) else {}

    if not mesaj:
        return "🦅 Buradayım."

    if karar.get("arac") and karar.get("arac") != "eagle_sohbet":
        return mesaj

    son_kullanici = ""
    son_eagle = ""

    for item in reversed(gecmis):
        if not isinstance(item, dict):
            continue

        rol = str(item.get("role", "")).strip().lower()
        metin = str(item.get("text", item.get("content", ""))).strip()

        if not metin:
            continue

        if rol == "user" and not son_kullanici:
            son_kullanici = metin
        elif rol == "assistant" and not son_eagle:
            son_eagle = metin

        if son_kullanici and son_eagle:
            break

    return _yerel_cevap(
        mesaj=mesaj,
        son_kullanici=son_kullanici,
        son_eagle=son_eagle,
        hafiza=hafiza,
        karar=karar,
    )


def _yerel_cevap(mesaj, son_kullanici="", son_eagle="", hafiza=None, karar=None):
    """
    Genel ve küçük bir yerel cevap çekirdeği.

    Amaç kullanıcı mesajını tekrar etmek yerine,
    konuşmanın akışına uygun kısa bir karşılık vermektir.
    """

    metin = mesaj.strip()
    kucuk = metin.casefold()

    # Görüş isteyen mesajlar.
    if "?" in metin and _gorus_istiyor_mu(kucuk):
        return _gorus_uret(metin, son_kullanici)

    # Duygu belirten mesajlar.
    if _duygu_var_mi(kucuk):
        return _duygu_uret(metin, son_eagle)

    # Önceki konuşmanın devamı.
    if _devam_mesaji_mi(kucuk) and son_kullanici:
        return _devam_uret(metin, son_kullanici, son_eagle)

    # Normal soru.
    if "?" in metin:
        return _soru_uret(metin, son_kullanici)

    # Hafıza varsa ama cevabı gereksiz yere hafızaya bağlama.
    if hafiza and _hafiza_uygun_mu(kucuk):
        bilgi = str(hafiza[-1]).strip()
        if bilgi:
            return f"🦅 Bunu konuşurken aklımda tuttuğum bilgi de şu: {bilgi}"

    # Basit selamlaşma / doğal sohbet.
    if _selam_mi(kucuk):
        return "🦅 Buradayım. Nasıl gidiyor?"

    return f"🦅 Anladım. {metin}"


def _gorus_istiyor_mu(metin):
    return any(
        ifade in metin
        for ifade in (
            "sence",
            "ne düşünüyorsun",
            "ne dusunuyorsun",
            "ne düşün",
            "ne dusun",
            "sen ne dersin",
            "fikrin ne",
            "fikrin",
        )
    )


def _duygu_var_mi(metin):
    """
    Tek tek cevap üretmek yerine temel duygu yönünü yakalar.
    Bu liste cevap değil, yalnızca konuşma bağlamını anlamak içindir.
    """
    return any(
        ifade in metin
        for ifade in (
            "yoruldum",
            "çok yoruldum",
            "uzgunum",
            "üzgünüm",
            "sıkıldım",
            "sikildim",
            "moralim bozuk",
            "canım sıkkın",
            "canim sikkin",
            "mutluyum",
            "sinirliyim",
            "gerildim",
            "endişeliyim",
            "endiseleniyorum",
        )
    )


def _devam_mesaji_mi(metin):
    if not metin:
        return False

    baslangiclar = (
        "peki",
        "buna",
        "bunu",
        "bunun",
        "şuna",
        "şunu",
        "şunun",
        "ona",
        "onu",
        "onun",
        "bir de",
        "sonra",
        "devam",
    )

    return metin.startswith(baslangiclar)


def _selam_mi(metin):
    return metin in {
        "merhaba",
        "selam",
        "selaam",
        "günaydın",
        "gunaydin",
        "iyi akşamlar",
        "iyi aksamlar",
        "iyi geceler",
    }


def _hafiza_uygun_mu(metin):
    return any(
        ifade in metin
        for ifade in (
            "hatırlıyor musun",
            "hatirliyor musun",
            "daha önce",
            "daha once",
            "hafızanda",
            "hafizanda",
        )
    )


def _gorus_uret(mesaj, onceki_kullanici):
    if onceki_kullanici:
        onceki = onceki_kullanici.casefold()

        if any(
            ifade in onceki
            for ifade in (
                "yoruldum",
                "sıkıldım",
                "sikildim",
                "moralim bozuk",
                "gerildim",
                "endişeliyim",
                "endiseleniyorum",
            )
        ):
            return (
                "🦅 Bence önce biraz nefes almak ve kendine zaman ayırmak iyi olabilir. "
                "Yoğun geçen bir günün ardından her şeyi hemen çözmeye çalışmak gerekmiyor."
            )

        return (
            "🦅 Bence bunu konuştuğumuz konu üzerinden değerlendirmek daha doğru. "
            "Benim açımdan önemli olan, önceki söylediklerini de gözden kaçırmamak."
        )

    return "🦅 Bence biraz daha bağlam olursa düşüncemi daha net ortaya koyabilirim."


def _duygu_uret(mesaj, son_eagle):
    metin = mesaj.casefold()

    if "yoruldum" in metin:
        return (
            "🦅 Anladım. Yoğun geçmiş gibi görünüyor. "
            "Biraz dinlenmek ve kafanı toparlamak iyi gelebilir."
        )

    if any(x in metin for x in ("üzgün", "uzgun", "moralim bozuk", "canım sıkkın", "canim sikkin")):
        return (
            "🦅 Anladım. Böyle hissettiğinde bunu içinde tutmak zorunda değilsin. "
            "İstersen ne olduğunu konuşabiliriz."
        )

    if any(x in metin for x in ("sıkıldım", "sikildim")):
        return (
            "🦅 Anladım. Biraz sıkılmış gibisin. "
            "İstersen konuyu değiştirip daha keyifli bir şey konuşabiliriz."
        )

    if any(x in metin for x in ("endişeliyim", "endiseleniyorum", "gerildim")):
        return (
            "🦅 Anladım. Önce biraz sakinleşip neyin seni gerdiğine bakmak iyi olabilir."
        )

    return "🦅 Anladım. İstersen bunu biraz daha konuşabiliriz."


def _devam_uret(mesaj, onceki_kullanici, son_eagle):
    if _gorus_istiyor_mu(mesaj.casefold()):
        return _gorus_uret(mesaj, onceki_kullanici)

    return (
        "🦅 Anladım, önceki konunun devamındayız. "
        "Söylediklerini birlikte değerlendirerek ilerleyebiliriz."
    )


def _soru_uret(mesaj, onceki_kullanici):
    if onceki_kullanici:
        return (
            "🦅 Tabii. Bunu konuştuğumuz konuyla birlikte değerlendirebiliriz. "
            "Önceki söylediklerini de dikkate alıyorum."
        )

    return "🦅 Tabii, konuşalım. Ne düşündüğünü biraz daha anlatabilirsin."
