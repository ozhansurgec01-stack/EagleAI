from pathlib import Path
import re

def _metin_temizle(metin):
    if not metin:
        return ""
    cop_kelimeler = ["paylaş", "facebook", "twitter", "whatsapp", "tumblr", "reddit", "pinterest", "e-posta", "ilginizi çekebilecek", "diğer yazılar", "yorum yap", "abone ol"]
    satirlar = metin.split(chr(10))
    temiz_satirlar = [s for s in satirlar if not any(cop in s.lower() for cop in cop_kelimeler)]
    sonuc = " ".join(temiz_satirlar)
    return " ".join(sonuc.split())


import json

def _hafizadan_bilgi_cek(anahtar):
    """Kişisel hafıza (eagle_ai_memory.json) içindeki yalnızca 'kullanici' katmanını tarar."""
    try:
        p = Path("eagle_ai_memory.json")
        if p.exists():
            veriler = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(veriler, dict):
                kullanici_notlari = veriler.get("kullanici", [])
            elif isinstance(veriler, list):
                kullanici_notlari = veriler
            else:
                kullanici_notlari = []

            anahtar_kucuk = anahtar.casefold()
            stop = {"ne", "nedir", "kim", "kimdir", "hakkında", "bilgi", "ver", "adı", "adin"}
            kelimeler = [k for k in anahtar_kucuk.split() if k not in stop and len(k) > 1]
            if not kelimeler:
                kelimeler = [anahtar_kucuk]

            for item in kullanici_notlari:
                if isinstance(item, str):
                    item_kucuk = item.casefold()
                    if any(k in item_kucuk for k in kelimeler):
                        return item
    except Exception:
        pass
    return None

def _bilgi_bankasindan_cek(anahtar):
    """Teknik bilgi bankası (eagle_bilgi.json) içinde arama yapar."""
    try:
        p = Path("eagle_bilgi.json")
        if p.exists():
            veriler = json.loads(p.read_text(encoding="utf-8"))
            for kategori, alt_dict in veriler.items():
                if kategori.casefold() in anahtar.casefold():
                    if isinstance(alt_dict, dict) and "temel" in alt_dict:
                        return " ".join(alt_dict["temel"][:2])
    except Exception:
        pass
    return None

def _hafizaya_kaydet(yeni_bilgi):
    """Yeni öğrenilen bir bilgiyi kalıcı hafızaya mühürler."""
    try:
        p = Path("eagle_ai_memory.json")
        veriler = []
        if p.exists():
            veriler = json.loads(p.read_text(encoding="utf-8"))
        if yeni_bilgi not in veriler:
            veriler.append(yeni_bilgi)
            p.write_text(json.dumps(veriler, indent=2, ensure_ascii=False), encoding="utf-8")
            return True
    except Exception:
        pass
    return False


# -*- coding: utf-8 -*-

def _slash_komut_uygula(cevap, komut):
    """Slash komutlarını harici modele ihtiyaç duymadan yerel olarak uygular."""
    cevap = str(cevap or "").strip()
    komut = str(komut or "").strip().lower()

    if not cevap or not komut:
        return cevap

    # Motorun kendi etiketini dönüşümden önce kaldır.
    temiz = re.sub(r"^🦅\s*", "", cevap).strip()
    temiz = re.sub(r"^Bilgi bankama göre:\s*", "", temiz).strip()

    # Cümleleri ayır.
    cumleler = [
        x.strip()
        for x in re.split(r"(?<=[.!?])\s+", temiz)
        if x.strip()
    ]

    if komut == "brief":
        # İlk anlamlı cümle: mümkün olan en kısa yerel cevap.
        return f"🦅 {cumleler[0] if cumleler else temiz}"

    if komut == "summarize":
        # Bilgi bankasının temel maddelerinden kısa özet.
        secilen = cumleler[:2]
        return "🦅 " + " ".join(secilen)

    if komut == "stepbystep":
        if not cumleler:
            return f"🦅 1. {temiz}"

        adimlar = []
        for i, cumle in enumerate(cumleler, 1):
            adimlar.append(f"{i}. {cumle}")
        return "🦅 " + "\n".join(adimlar)

    if komut == "eli5":
        # Yerel sadeleştirme: gereksiz teknik parantezleri kaldır,
        # açıklamayı kısa cümlelere böl ve temel anlamı koru.
        basit = re.sub(r"\([^()]{1,120}\)", "", temiz)
        basit = re.sub(r"\s+", " ", basit).strip()
        return f"🦅 Basitçe: {basit}"

    if komut == "expert":
        # Yeni bilgi uydurmadan mevcut bilgiyi daha teknik ve düzenli sun.
        if len(cumleler) > 1:
            return "🦅 " + " ".join(cumleler)
        return f"🦅 Teknik açıklama: {temiz}"

    return cevap

def eagle_cevap_uret(mesaj, gecmis=None, hafiza=None, karar=None, baglam=None):
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
    baglam = str(baglam or '').strip()

    # 🦅 Slash komutu varsa komut önekini cevap motorundan ayır.
    # Komut yoksa mesaj aynen korunur.
    komut = str(karar.get("komut", "") or "").strip().lower()
    komut_metni = str(karar.get("komut_metni", "") or "").strip()

    if komut in {
        "brief",
        "expert",
        "eli5",
        "stepbystep",
        "summarize",
    }:
        mesaj = komut_metni

    if not mesaj:
        if komut:
            return f"🦅 /{komut} için bir mesaj yazmalısın."
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

    durum = _konusma_durumu_analiz_et(gecmis, mesaj)

    cevap = _yerel_cevap(
        mesaj=mesaj,
        son_kullanici=son_kullanici,
        son_eagle=son_eagle,
        hafiza=hafiza,
        karar=karar,
        baglam=baglam,
        durum=durum,
    )

    return _slash_komut_uygula(cevap, komut)



def _konusma_durumu_analiz_et(gecmis, mesaj):
    """
    Son konuşma akışından küçük bir durum özeti çıkarır.
    Cevap üretmez; yalnızca konuşmanın rolünü ve aktif bağlamını belirler.
    """
    gecmis = gecmis if isinstance(gecmis, list) else []
    mesaj = str(mesaj or "").strip()
    kucuk = mesaj.casefold()

    kullanici_mesajlari = []
    for item in gecmis:
        if not isinstance(item, dict):
            continue

        rol = str(item.get("role", "")).strip().lower()
        metin = str(item.get("text", item.get("content", ""))).strip()

        if rol == "user" and metin:
            kullanici_mesajlari.append(metin)

    onceki_kullanici = kullanici_mesajlari[-1] if kullanici_mesajlari else ""

    durum = {
        "rol": "normal",
        "onceki_kullanici": onceki_kullanici,
        "aktif_konu": "",
        "konu_degistir": False,
        "konu_kapat": False,
        "takip_sorusu": False,
    }

    konu_degistirme_ifadeleri = (
        "başka bir şey konuşalım",
        "baska bir sey konusalim",
        "başka şey konuşalım",
        "baska sey konusalim",
        "konuyu değiştirelim",
        "konuyu degistirelim",
        "konuyu değiştirebilir miyiz",
        "konuyu degistirebilir miyiz",
    )

    if any(ifade in kucuk for ifade in konu_degistirme_ifadeleri):
        durum["rol"] = "konu_degistir"
        durum["konu_degistir"] = True
        return durum

    konu_kapatma_ifadeleri = (
        "boşver",
        "bosver",
        "neyse",
        "önemi yok",
        "onemi yok",
        "geç boşver",
        "gec bosver",
    )

    if any(ifade in kucuk for ifade in konu_kapatma_ifadeleri):
        durum["rol"] = "konu_kapat"
        durum["konu_kapat"] = True
        return durum

    takip_ifadeleri = (
        "neden",
        "niye",
        "nasıl yani",
        "nasil yani",
        "peki",
        "sonra",
        "bunun nedeni ne",
        "sebebi ne",
    )

    takip_kucuk = kucuk.rstrip("?").strip()

    if onceki_kullanici and takip_kucuk in takip_ifadeleri:
        durum["rol"] = "takip_sorusu"
        durum["takip_sorusu"] = True

    sosyal_karsiliklar = (
        "ben de iyiyim",
        "ben de iyiyim.",
        "ben de iyiyim!",
        "ben de iyiyim teşekkürler",
        "ben de iyiyim tesekkurler",
        "iyiyim ben de",
        "sağ ol",
        "sag ol",
        "teşekkürler",
        "tesekkurler",
    )

    if kucuk in sosyal_karsiliklar:
        durum["rol"] = "sosyal_karsilik"

    if _duygu_var_mi(kucuk):
        durum["rol"] = "duygu"
        durum["aktif_konu"] = "duygu"

    if _gorus_istiyor_mu(kucuk):
        durum["rol"] = "gorus_isteme"

    return durum


def _yerel_cevap(mesaj, son_kullanici="", son_eagle="", hafiza=None, karar=None, baglam="", durum=None):
    kucuk = mesaj.strip().lower()


    # Konuşma durumu, hafıza ve bilgi bankasından önce değerlendirilir.
    # Sosyal karşılıklar ve takip soruları bilgi aramasına düşmemeli.
    durum = durum if isinstance(durum, dict) else {}
    rol = durum.get("rol", "normal")

    if rol == "sosyal_karsilik":
        return "🦅 Güzel, sevindim. O zaman bugün ne yapmak istediğine bakalım. 😊"

    if rol == "konu_degistir":
        return "🦅 Tabii, o konuyu bırakalım. Başka bir şey konuşabiliriz."

    if rol == "konu_kapat":
        return "🦅 Tamam, boşverelim. İstersen başka bir şeyden devam ederiz."

    if rol == "takip_sorusu" and son_kullanici:
        return _devam_uret(mesaj.strip(), son_kullanici, son_eagle)

    if rol == "gorus_isteme":
        return _gorus_uret(mesaj.strip(), "")
    # === HAFIZA -> BİLGİ BANKASI SIRALAMASI ===
    # 1. Adım: Kişisel Hafıza (eagle_ai_memory.json -> kullanıcı notları)
    hafiza_bulunan = _hafizadan_bilgi_cek(kucuk)
    if hafiza_bulunan:
        return f"🦅 Hafızamda bununla ilgili şu bilgiyi buldum: {hafiza_bulunan}"

    # 2. Adım: Teknik Bilgi Bankası (eagle_bilgi.json)
    bilgi_bulunan = _bilgi_bankasindan_cek(kucuk)
    if bilgi_bulunan:
        return f"🦅 Bilgi bankama göre: {bilgi_bulunan}"
    # ================================================
    """
    Genel ve küçük bir yerel cevap çekirdeği.

    Amaç kullanıcı mesajını tekrar etmek yerine,
    konuşmanın akışına uygun kısa bir karşılık vermektir.
    """

    metin = mesaj.strip()
    kucuk = metin.casefold()

    # Ayrı taşınan konuşma bağlamı varsa, cevap üretiminde
    # en yakın kullanıcı mesajından daha güçlü bağlam olarak kullan.
    baglam_metin = str(baglam or "").strip()
    if baglam_metin:
        son_kullanici = baglam_metin

    # Konuşma durumu önceki bağlamın nasıl kullanılacağını belirler.
    durum = durum if isinstance(durum, dict) else {}
    rol = durum.get("rol", "normal")

    if rol == "konu_degistir":
        return "🦅 Tabii, o konuyu bırakalım. Başka bir şey konuşabiliriz."

    if rol == "konu_kapat":
        return "🦅 Tamam, boşverelim. İstersen başka bir şeyden devam ederiz."

    if rol == "takip_sorusu" and son_kullanici:
        return _devam_uret(metin, son_kullanici, son_eagle)

    if rol == "gorus_isteme":
        return _gorus_uret(metin, "")

    # Görüş isteyen mesajlar.
    if "?" in mesaj and _gorus_istiyor_mu(kucuk):
        return _gorus_uret(metin, son_kullanici)

    # Duygu belirten mesajlar.
    if _duygu_var_mi(kucuk):
        return _duygu_uret(metin, son_eagle)

    # Kullanıcı önceki ifadeyi düzeltiyorsa, gerçek soruyu ayıkla.
    if _duzeltme_mesaji_mi(kucuk):
        duzeltilmis_soru = _duzeltme_sorusunu_ayikla(metin)
        if duzeltilmis_soru != metin:
            return _soru_uret(duzeltilmis_soru, son_kullanici)

    # Önceki konuşmanın devamı.
    if _devam_mesaji_mi(kucuk) and son_kullanici:
        return _devam_uret(metin, son_kullanici, son_eagle)

    # Önce kişisel hafızada veya bilgi bankasında bu anahtar kelimeyi arayalım
    hafiza_sonuc = _hafizadan_bilgi_cek(kucuk)
    if hafiza_sonuc:
        return f"🦅 Hafızamda bununla ilgili şu bilgiyi buldum: {hafiza_sonuc}"

    bilgi_sonuc = _bilgi_bankasindan_cek(kucuk)
    if bilgi_sonuc:
        return f"🦅 Bilgi bankama göre: {bilgi_sonuc}"

    # Normal soru.
    if _soru_gibi_mi(kucuk):
        return _soru_uret(metin, son_kullanici)

    # Hafıza varsa ama cevabı gereksiz yere hafızaya bağlama.
    if hafiza and _hafiza_uygun_mu(kucuk):
        bilgi = str(hafiza[-1]).strip()
        if bilgi:
            return f"🦅 Bunu konuşurken aklımda tuttuğum bilgi de şu: {bilgi}"

    # Basit selamlaşma / doğal sohbet.
    if _selam_mi(kucuk):
        return "🦅 Buradayım. Nasıl gidiyor?"

# Sabit bir kalıp yerine, cümlenin akışına göre doğal bir reaksiyon verelim
    if len(metin) > 30:
        return "🦅 Bu konuyu detaylıca ele alabiliriz, gerçekten derin ve önemli detaylar barındırıyor."
    return f"🦅 {mesaj} üzerine odaklanalım, devam edelim."


def _soru_gibi_mi(metin):
    soru_kokleri = (
        "nasılsın",
        "nasilsin",
        "iyi misin",
        "iyi mi",
        "ne düşünüyorsun",
        "ne dusunuyorsun",
        "ne yapıyorsun",
        "ne yapiyorsun",
        "nasıl gidiyor",
        "nasil gidiyor",
        "günün nasıl geçti",
        "gunun nasil gecti",
        "bugün neler yaptın",
        "bugun neler yaptin",
        "bugün ne yaptın",
        "bugun ne yaptin",
        "neler yaptın",
        "neler yaptin",
    )
    if any(kok in metin for kok in soru_kokleri):
        return True

    # Türkçede soru işareti yazılmasa da soru yapısını yakala.
    if metin.endswith((" mi", " mı", " mu", " mü")):
        return True

    # Genel bilgi talepleri soru işareti taşımayabilir.
    # Cümlenin bilgi isteme yapısını kontrol et.
    if (
        "hakkında bilgi" in metin
        or "bilgi verir misin" in metin
        or "bilgi verir mısın" in metin
        or metin.endswith(" nedir")
        or metin.endswith(" nedir?")
    ):
        return True

    # Doğrudan soru yapıları; geniş kelime listesi yerine cümle yapısına bak.
    soru_yapilari = (
        "ne yaparsın",
        "ne yapardın",
        "ne yapabilirsin",
        "ne düşünürsün",
        "ne düşünürdün",
        "ne dersin",
        "ne olur",
        "neden",
        "niye",
        "nasıl",
        "hangi",
        "kim",
        "nerede",
        "ne zaman",
        "kaç",
    )

    return any(yapi in metin for yapi in soru_yapilari)


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


def _duzeltme_mesaji_mi(metin):
    if not metin:
        return False

    if metin.startswith((
        "değil",
        "degil",
        "yok",
        "hayır",
        "hayir",
        "onu demiyorum",
        "onu sormuyorum",
        "öyle değil",
        "oyle degil",
    )):
        return True

    return " değil " in f" {metin} " or " degil " in f" {metin} "


def _duzeltme_sorusunu_ayikla(metin):
    if not metin:
        return metin

    kucuk = metin.casefold().strip()

    ayiraclar = (
        " soruyorum",
        " soruyorum.",
        " soruyorum!",
        " soruyorum?",
        " diye soruyorum",
    )

    for ayirac in ayiraclar:
        if ayirac in kucuk:
            parca = kucuk.split(ayirac, 1)[0].strip()
            if " değil " in f" {parca} ":
                return parca.rsplit(" değil ", 1)[1].strip()
            if " degil " in f" {parca} ":
                return parca.rsplit(" degil ", 1)[1].strip()

    if kucuk.startswith(("onu demiyorum", "onu sormuyorum")):
        for ayirac in (",", ":", ";"):
            if ayirac in kucuk:
                return kucuk.split(ayirac, 1)[1].strip()

    return metin


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

    return (
        "🦅 Bence bugün biraz keyfine göre ilerleyelim. "
        "İstersen sohbet edebilir, bir şeyler izleyebilir, dışarı çıkabilir "
        "ya da aklına gelen başka bir şeyi birlikte değerlendirebiliriz."
    )


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

    onceki = str(onceki_kullanici or "").casefold()

    if any(
        ifade in onceki
        for ifade in (
            "canım sıkkın",
            "canim sikkin",
            "moralim bozuk",
            "üzgünüm",
            "uzgunum",
            "sıkıldım",
            "sikildim",
            "gerildim",
            "endişeliyim",
            "endiseleniyorum",
        )
    ):
        return (
            "🦅 Bazen insanın neden böyle hissettiğini hemen açıklaması kolay olmuyor. "
            "İstersen seni sıkan şeyi biraz açabiliriz; istemiyorsan da konuyu değiştirebiliriz."
        )

    return (
        "🦅 Evet, önceki konunun devamındayız. "
        "İstersen biraz daha açalım; neyi merak ettiğini birlikte netleştirebiliriz."
    )


def _soru_uret(mesaj, onceki_kullanici):
    metin = mesaj.casefold().strip()

    soru_metin = metin

    if " " in soru_metin:
        ilk, kalan = soru_metin.split(" ", 1)
        if ilk not in (
            "nasılsın",
            "nasilsin",
            "iyi",
            "bugün",
            "bugun",
            "neler",
            "günün",
            "gunun",
            "ne",
        ):
            soru_metin = kalan.strip()

    hal_hatir = any(
        ifade in soru_metin
        for ifade in (
            "nasılsın",
            "nasilsin",
            "iyi misin",
            "nasıl gidiyor",
            "nasil gidiyor",
        )
    )

    su_an = any(
        ifade in soru_metin
        for ifade in (
            "ne yapıyorsun",
            "ne yapiyorsun",
        )
    )

    bugun = any(
        ifade in soru_metin
        for ifade in (
            "bugün neler yaptın",
            "bugun neler yaptin",
            "bugün ne yaptın",
            "bugun ne yaptin",
            "neler yaptın",
            "neler yaptin",
            "günün nasıl geçti",
            "gunun nasil gecti",
        )
    )

    if hal_hatir and (su_an or bugun):
        return (
            "🦅 İyiyim Özhan, buradayım. 😊 "
            "Bugün de seninle konuşuyor, sorularını yanıtlıyor ve yardımcı olmaya çalışıyorum. "
            "Senin günün nasıl geçti?"
        )

    if hal_hatir:
        return (
            "🦅 İyiyim Özhan, buradayım. "
            "Seninle konuşmaya ve yardımcı olmaya hazırım. 😊"
        )

    if bugun:
        return (
            "🦅 Bugün seninle konuşuyor, sorularını yanıtlıyor ve yardımcı olmaya çalışıyorum. "
            "Benim açımdan günün en güzel kısmı seninle sohbet etmek. 😊"
        )

    if su_an:
        return (
            "🦅 Şu an seninle konuşuyorum. "
            "Sorularını yanıtlıyor ve sana yardımcı olmaya çalışıyorum. 😊"
        )

    # Tanınan özel soru kalıpları dışında da soruyu anlamsız
    # bir "ne düşündüğünü anlat" cevabına düşürme.
    if _soru_gibi_mi(metin):
        if any(x in soru_metin for x in (
            "ne yaparsın",
            "ne yapardın",
            "ne yapabilirsin",
        )):
            return (
                "🦅 Böyle bir durumda önce biraz kafa dağıtmayı seçerdim. "
                "Müzik dinlemek, bir şeyler öğrenmek ya da seninle sohbet etmek güzel olurdu."
            )

        if any(x in soru_metin for x in (
            "planın var mı",
            "planin var mi",
        )):
            return (
                "🦅 Benim insanlardaki gibi önceden belirlenmiş kişisel planlarım yok. "
                "Ama burada seninle konuşmaya ve ne yapmak istediğine göre ilerlemeye hazırım."
            )

        if onceki_kullanici:
            return (
                "🦅 Güzel soru. Bunu önceki konuşmamızdan bağımsız olarak doğrudan cevaplayabilirim. "
                "Sorunun neyi merak ettiğini dikkate alarak ilerleyelim."
            )

        return (
            "🦅 Güzel soru. Bunu doğrudan cevaplayabilirim; "
            "sorunun neyi merak ettiğine göre düşünelim."
        )

    if onceki_kullanici:
        return (
            "🦅 Tabii. Bunu konuştuğumuz konuyla birlikte değerlendirebiliriz. "
            "Önceki söylediklerini de dikkate alıyorum."
        )

    return "🦅 Tabii, konuşalım."
