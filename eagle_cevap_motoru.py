
import json
from pathlib import Path

import json
import re

def _hafizadan_bilgi_cek(anahtar):
    """Kullanici hafizasi ve Eagle ogrenme alaninda esnek arama yapar."""
    try:
        p = Path("eagle_ai_memory.json")
        if not p.exists():
            return None

        veriler = json.loads(p.read_text(encoding="utf-8"))
        sorgu = str(anahtar or "").casefold()

        kelimeler = [
            k for k in re.findall(r"\w+", sorgu)
            if len(k) > 2 and k not in {
                "nedir", "ne", "hakkında", "bilgi", "ver", "kimdir", "adı"
            }
        ]

        if isinstance(veriler, list):
            kullanici = veriler
            ogrenme = []
        elif isinstance(veriler, dict):
            kullanici = veriler.get("kullanici", [])
            ogrenme = veriler.get("eagle_ogrenme", [])
        else:
            return None

        for item in kullanici:
            metin = str(item).casefold()
            if any(k in metin for k in kelimeler):
                return item

        for item in ogrenme:
            if not isinstance(item, dict):
                continue

            konu = str(item.get("konu", "")).casefold()
            bilgi = str(item.get("bilgi", "")).strip()

            if any(k in konu or k in bilgi.casefold() for k in kelimeler):
                return bilgi

    except Exception:
        pass

    return None

def _sohbet_hafizasindan_cek(anahtar):
    """Geçmişte kaydedilmiş başarılı soru-cevap örneklerinde arama yapar."""
    try:
        p = Path("eagle_ai_memory.json")
        if not p.exists():
            return None

        veriler = json.loads(p.read_text(encoding="utf-8"))

        if not isinstance(veriler, dict):
            return None

        sohbet = veriler.get("sohbet", [])
        sorgu = str(anahtar or "").casefold()

        kelimeler = [
            k for k in re.findall(r"\w+", sorgu)
            if len(k) > 2 and k not in {
                "nedir", "ne", "hakkında", "bilgi", "ver", "kimdir"
            }
        ]

        for kayit in reversed(sohbet):
            if not isinstance(kayit, dict):
                continue

            soru = str(kayit.get("soru", "")).casefold()
            cevap = str(kayit.get("cevap", "")).strip()

            eslesen = sum(1 for k in kelimeler if k in soru)

            if kelimeler and eslesen >= max(1, len(kelimeler) // 2):
                return cevap

    except Exception:
        pass

    return None


def _bilgi_bankasindan_cek(anahtar):
    """Bilgi bankasında anahtar ve içerik üzerinden esnek arama yapar."""
    try:
        p = Path("eagle_bilgi.json")
        if not p.exists():
            return None

        veriler = json.loads(p.read_text(encoding="utf-8"))
        sorgu = str(anahtar or "").casefold()
        kelimeler = [
            k for k in re.findall(r"\w+", sorgu)
            if len(k) > 2 and k not in {
                "nedir", "ne", "hakkında", "bilgi", "ver", "kimdir"
            }
        ]

        if not isinstance(veriler, dict):
            return None

        for kategori, veri in veriler.items():
            kat = str(kategori).casefold()

            if (
                kat in sorgu
                or any(k == kat or k in kat or kat in k for k in kelimeler)
            ):
                if isinstance(veri, dict):
                    if isinstance(veri.get("temel"), list):
                        return " ".join(str(x) for x in veri["temel"][:2])
                    if veri.get("aciklama"):
                        return str(veri["aciklama"])
                return str(veri)

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
        baglam=baglam,
    )


def _yerel_cevap(mesaj, son_kullanici="", son_eagle="", hafiza=None, karar=None, baglam=""):
    """
    Genel yerel cevap çekirdeği.

    Konuşma devamlılığını önceki kullanıcı mesajı ve kişisel hafızayla
    birlikte değerlendirir.
    """

    metin = str(mesaj or "").strip()
    kucuk = metin.casefold()

    if not metin:
        return "🦅 Buradayım."

    # API bağlam çözücüsünün oluşturduğu devam mesajını ayır.
    if "kullanıcının devam mesajı:" in kucuk:
        metin = metin.split("Kullanıcının devam mesajı:", 1)[1].strip()
        kucuk = metin.casefold()

    # Görüş isteyen mesajlar.
    if "?" in metin and _gorus_istiyor_mu(kucuk):
        return _gorus_uret(metin, son_kullanici)

    # Duygu belirten mesajlar.
    if _duygu_var_mi(kucuk):
        return _duygu_uret(metin, son_eagle)

    # Kullanıcı önceki ifadesini düzeltiyorsa.
    if _duzeltme_mesaji_mi(kucuk):
        duzeltilmis_soru = _duzeltme_sorusunu_ayikla(metin)
        if duzeltilmis_soru != metin:
            return _soru_uret(duzeltilmis_soru, son_kullanici)

    # Önceki konuşmanın devamı.
    if _devam_mesaji_mi(kucuk) and son_kullanici:
        return _devam_uret(metin, son_kullanici, son_eagle, hafiza)

    # Kişisel hafıza.
    hafiza_sonuc = _hafizadan_bilgi_cek(kucuk)
    if hafiza_sonuc:
        return f"🦅 Hafızamda bununla ilgili şu bilgiyi buldum: {hafiza_sonuc}"

    # Geçmiş başarılı sohbetler.
    sohbet_sonuc = _sohbet_hafizasindan_cek(kucuk)
    if sohbet_sonuc:
        return f"🦅 Daha önceki sohbet hafızamdan bulduğum cevap: {sohbet_sonuc}"

    # Bilgi bankası.
    bilgi_sonuc = _bilgi_bankasindan_cek(kucuk)
    if bilgi_sonuc:
        return f"🦅 Bilgi bankama göre: {bilgi_sonuc}"

    # Normal soru.
    if _soru_gibi_mi(kucuk):
        return _soru_uret(metin, son_kullanici)

    # Hafıza uygunsa konuşmaya bağla.
    if hafiza and _hafiza_uygun_mu(kucuk):
        bilgi = str(hafiza[-1]).strip()
        if bilgi:
            return f"🦅 Bunu konuşurken aklımda tuttuğum bilgi de şu: {bilgi}"

    # Selamlaşma / doğal sohbet.
    if _selam_mi(kucuk):
        return "🦅 Buradayım. Nasıl gidiyor?"

    # Son çare: mesajı aynen tekrar eden kalıbı kullanma.
    return _devam_uret(metin, son_kullanici, son_eagle, hafiza)



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

    return metin.endswith(("mi?", "mı?", "mu?", "mü?"))


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


def _devam_uret(mesaj, onceki_kullanici, son_eagle, hafiza=None):
    if _gorus_istiyor_mu(mesaj.casefold()):
        return _gorus_uret(mesaj, onceki_kullanici)

    hafiza_bilgisi = _hafizadan_bilgi_cek(
        f"{onceki_kullanici} {mesaj}"
    )

    if hafiza_bilgisi:
        return (
            f"🦅 Hafızamdaki bilgiye göre: {hafiza_bilgisi} "
            f"“{mesaj}” dediğine göre, bu konunun üzerinden devam edebiliriz."
        )

    return _soru_uret(mesaj, onceki_kullanici)


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

    if onceki_kullanici:
        return (
            "🦅 Tabii. Bunu konuştuğumuz konuyla birlikte değerlendirebiliriz. "
            "Önceki söylediklerini de dikkate alıyorum."
        )

    return "🦅 Tabii, konuşalım. Ne düşündüğünü biraz daha anlatabilirsin."
