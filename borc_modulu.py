import json
import re
from pathlib import Path

BORC_DOSYASI = Path("borc_verileri.json")

def borclari_yukle():
    try:
        if BORC_DOSYASI.exists():
            veri = json.loads(BORC_DOSYASI.read_text(encoding="utf-8"))
            if isinstance(veri, dict) and "borclar" in veri:
                return veri["borclar"]
    except Exception as e:
        print("⚠️ Borç verileri okunamadı:", e)
    return []

def borclari_kaydet(borclar):
    try:
        veri = {"borclar": borclar}
        BORC_DOSYASI.write_text(
            json.dumps(veri, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception as e:
        print("⚠️ Borç verileri kaydedilemedi:", e)

def fatura_adi_bul(mesaj):
    """Mesajdaki fatura adını sabit kayda bağlar."""
    m = str(mesaj or "").lower()

    cevir = str.maketrans({
        "ı": "i",
        "ş": "s",
        "ğ": "g",
        "ü": "u",
        "ö": "o",
        "ç": "c"
    })
    m = m.translate(cevir)

    eslesmeler = [
        ("d-smart", "D-Smart"),
        ("dsmart", "D-Smart"),
        ("d smart", "D-Smart"),
        ("elektrik", "Elektrik"),
        ("internet", "İnternet"),
        ("telefon", "Telefon"),
        ("su", "Su"),
    ]

    for aranan, kanonik in eslesmeler:
        if aranan in m:
            return kanonik

    return None


def borc_ekle(ad, kategori, toplam_borc, taksit_sayisi=1):
    borclar = borclari_yukle()
    yeni_id = str(len(borclar) + 1)
    
    yeni_borc = {
        "id": yeni_id,
        "ad": str(ad).strip(),
        "kategori": str(kategori).strip().capitalize(),
        "toplam_borc": float(toplam_borc),
        "odenen_tutar": 0.0,
        "kalan_borc": float(toplam_borc),
        "taksit_sayisi": int(taksit_sayisi) if taksit_sayisi > 0 else 1
    }
    
    borclar.append(yeni_borc)
    borclari_kaydet(borclar)
    return yeni_borc


def borc_guncelle(
    borc_id,
    ad=None,
    kategori=None,
    toplam_borc=None,
    taksit_sayisi=None,
    odenen_tutar=None
):
    borclar = borclari_yukle()

    for b in borclar:
        if str(b.get("id")) != str(borc_id):
            continue

        if ad is not None and str(ad).strip():
            b["ad"] = str(ad).strip()

        if kategori is not None and str(kategori).strip():
            b["kategori"] = str(kategori).strip().capitalize()

        if toplam_borc is not None:
            yeni_toplam = float(toplam_borc)
            if yeni_toplam <= 0:
                return False, None

            b["toplam_borc"] = yeni_toplam
            b["kalan_borc"] = max(
                0.0,
                yeni_toplam - float(b.get("odenen_tutar", 0.0))
            )

        if taksit_sayisi is not None:
            yeni_taksit = int(taksit_sayisi)
            if yeni_taksit < 1:
                yeni_taksit = 1
            b["taksit_sayisi"] = yeni_taksit

        if odenen_tutar is not None:
            yeni_odenen = float(odenen_tutar)
            if yeni_odenen < 0:
                return False, None
            b["odenen_tutar"] = yeni_odenen
            b["kalan_borc"] = max(
                0.0,
                float(b.get("toplam_borc", 0.0)) - yeni_odenen
            )

        borclari_kaydet(borclar)
        return True, b

    return False, None


def borc_sil(borc_id):
    borclar = borclari_yukle()

    for i, b in enumerate(borclar):
        if str(b.get("id")) == str(borc_id):
            silinen = borclar.pop(i)
            borclari_kaydet(borclar)
            return True, silinen

    return False, None


def odeme_yap(borc_adi_veya_id, odenen_tutar):
    borclar = borclari_yukle()
    odenen_tutar = float(odenen_tutar)
    
    bulundu = False
    guncel_borc = None
    
    for b in borclar:
        if (str(b["id"]) == str(borc_adi_veya_id) or 
            str(b["ad"]).lower() in str(borc_adi_veya_id).lower()):
            
            b["odenen_tutar"] += odenen_tutar
            b["kalan_borc"] = max(0.0, b["toplam_borc"] - b["odenen_tutar"])
            bulundu = True
            guncel_borc = b
            break
            
    if bulundu:
        borclari_kaydet(borclar)
        return True, guncel_borc
    return False, None

def taksit_hesapla(borc_adi_veya_id, taksit_sayisi=None):
    borclar = borclari_yukle()
    for b in borclar:
        if (str(b["id"]) == str(borc_adi_veya_id) or 
            str(b["ad"]).lower() in str(borc_adi_veya_id).lower()):
            
            sayi = int(taksit_sayisi) if taksit_sayisi else b["taksit_sayisi"]
            if sayi <= 0:
                sayi = 1
            
            aylik = b["kalan_borc"] / sayi
            return True, {"borc": b["ad"], "kalan": b["kalan_borc"], "taksit_sayisi": sayi, "aylik_taksit": aylik}
    return False, None

def genel_rapor():
    borclar = borclari_yukle()

    toplam_borc = 0.0
    toplam_odenen = 0.0
    toplam_kalan = 0.0

    for b in borclar:
        toplam = float(b.get("toplam_borc", 0.0))
        odenen = float(b.get("odenen_tutar", 0.0))
        kalan = max(0.0, toplam - odenen)

        b["toplam_borc"] = toplam
        b["odenen_tutar"] = odenen
        b["kalan_borc"] = kalan

        taksit = int(b.get("taksit_sayisi", 1) or 1)
        if taksit < 1:
            taksit = 1

        aylik_taksit = toplam / taksit

        if kalan > 0:
            kalan_taksit = int((kalan + aylik_taksit - 0.000001) // aylik_taksit)
            if kalan_taksit < 1:
                kalan_taksit = 1
        else:
            kalan_taksit = 0

        b["aylik_taksit"] = round(aylik_taksit, 2)
        b["kalan_taksit"] = kalan_taksit

        toplam_borc += toplam
        toplam_odenen += odenen
        toplam_kalan += kalan

    kategoriler = {}

    for b in borclar:
        kat = b.get("kategori", "Diğer")

        if kat not in kategoriler:
            kategoriler[kat] = {
                "toplam": 0.0,
                "kalan": 0.0
            }

        kategoriler[kat]["toplam"] += float(b.get("toplam_borc", 0.0))
        kategoriler[kat]["kalan"] += float(b.get("kalan_borc", 0.0))

    return {
        "toplam_borc": toplam_borc,
        "toplam_odenen": toplam_odenen,
        "toplam_kalan": toplam_kalan,
        "borclar": borclar,
        "kategoriler": kategoriler
    }


def para_degerini_oku(metin):
    s = str(metin).strip().replace(" ", "")

    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    
    return float(s)


def borc_mesaji_isle(mesaj):
    """Doğal Türkçe borç ve sabit fatura işlemlerini yönetir."""
    mesaj = str(mesaj or "").strip()
    m = mesaj.lower()

    # Türkçe karakterleri yalnızca eşleştirme için normalize et.
    norm = m.translate(str.maketrans({
        "ı": "i",
        "ş": "s",
        "ğ": "g",
        "ü": "u",
        "ö": "o",
        "ç": "c"
    }))

    # 1. Rapor
    rapor_ifadeleri = [
        "borclarimi goster",
        "kalan borc",
        "borc listesi",
        "borc ve taksit raporu",
        "borc raporu",
        "taksit raporu",
        "taksitlerimi goster",
    ]

    if any(x in norm for x in rapor_ifadeleri):
        rapor = genel_rapor()

        if not rapor["borclar"]:
            return "Henüz kayıtlı bir borcunuz bulunmuyor."

        def tl(sayi):
            return f"{sayi:,.0f}".replace(",", ".")

        yanit = "💳 BORÇ VE TAKSİT RAPORU\n\n"

        for b in rapor["borclar"]:
            yanit += (
                f"• {b['ad']}\n"
                f"  Kategori: {b['kategori']}\n"
                f"  Toplam: {tl(b.get('toplam_borc', 0))} TL\n"
                f"  Ödenen: {tl(b.get('odenen_tutar', 0))} TL\n"
                f"  Kalan: {tl(b.get('kalan_borc', 0))} TL\n"
            )

            if str(b.get("kategori", "")).strip().lower() != "fatura":
                yanit += f"  Taksit: {b.get('taksit_sayisi', 1)}\n"

            yanit += "\n"

        yanit += (
            f"💰 Genel Toplam: {tl(rapor['toplam_borc'])} TL\n"
            f"💵 Ödenen: {tl(rapor['toplam_odenen'])} TL\n"
            f"📌 Kalan: {tl(rapor['toplam_kalan'])} TL"
        )
        return yanit

    # 2. Toplam borç
    if any(x in norm for x in [
        "borclarimin toplami",
        "toplam borc ne kadar"
    ]):
        rapor = genel_rapor()
        return (
            f"Toplam kalan borcunuz: **{rapor['toplam_kalan']:,.2f} TL** "
            f"(Genel Borç: {rapor['toplam_borc']:,.2f} TL, "
            f"Ödenen: {rapor['toplam_odenen']:,.2f} TL)"
        )

    # 3. Sabit fatura adı
    fatura = fatura_adi_bul(mesaj)

    # 4. Fatura ödendi
    if "odendi" in norm and fatura:
        borclar = borclari_yukle()

        for b in borclar:
            if b.get("ad") == fatura:
                toplam = float(b.get("toplam_borc", 0) or 0)

                if toplam <= 0:
                    return f"ℹ️ **{fatura} faturası** için kayıtlı ödenecek tutar bulunmuyor."

                b["odenen_tutar"] = toplam
                b["kalan_borc"] = 0.0
                borclari_kaydet(borclar)

                return f"✅ **{fatura} faturası** ödendi. Kalan: **0 TL**."

        return f"**{fatura}** faturası kaydı bulunamadı."

    # 5. Fatura tutarı girme/güncelleme
    sayilar = re.findall(r'\d+(?:[.,]\d+)?', mesaj)

    if fatura and sayilar:
        tutar = para_degerini_oku(sayilar[-1])
        borclar = borclari_yukle()

        for b in borclar:
            if b.get("ad") == fatura:
                b["toplam_borc"] = tutar
                b["odenen_tutar"] = 0.0
                b["kalan_borc"] = tutar
                b["taksit_sayisi"] = 1
                borclari_kaydet(borclar)

                return (
                    f"✅ **{fatura} faturası** "
                    f"{tutar:,.2f} TL olarak güncellendi."
                )

        return f"**{fatura}** faturası kaydı bulunamadı."

    # 6. Taksit hesaplama
    if "taksit" in norm or "taksite bol" in norm:
        sayilar = re.findall(r'\d+', mesaj)

        if len(sayilar) >= 2:
            ilk = float(sayilar[0])
            ikinci = float(sayilar[1])

            if ilk > 12:
                tutar = ilk
                taksit = int(ikinci)
            else:
                taksit = int(ilk)
                tutar = ikinci

            if taksit <= 0:
                taksit = 1

            aylik = tutar / taksit

            return (
                f"🧮 **Taksit Hesaplama:**\n"
                f"• Toplam Tutar: {tutar:,.2f} TL\n"
                f"• Taksit Sayısı: {taksit}\n"
                f"• **Aylık Ödeme:** **{aylik:,.2f} TL**"
            )

    # 7. Normal borç ekleme
    if any(x in norm for x in ["ekle", "borcum var", "borc ekle"]):
        if sayilar:
            tutar = para_degerini_oku(sayilar[-1])

            kategori = "Diğer"

            for kat in ["Kredi", "Altın", "Kira"]:
                if kat.lower() in norm:
                    kategori = kat
                    break

            ad_temiz = norm
            for kelime in ["ekle", "borcum var", "borc", "tl"]:
                ad_temiz = ad_temiz.replace(kelime, "")

            ad = ad_temiz.strip().capitalize()

            if len(ad) < 3:
                ad = f"{kategori} Borcu"

            yeni = borc_ekle(ad, kategori, tutar, 1)

            return (
                f"✅ Yeni borç eklendi:\n"
                f"• **{yeni['ad']}** ({yeni['kategori']}) - "
                f"Tutar: {yeni['toplam_borc']:,.2f} TL"
            )

    return None

def akilli_borc_niyeti(mesaj):
    m = str(mesaj or "").lower()
    m = (
        m.replace("ı", "i")
         .replace("İ", "i")
         .replace("ş", "s")
         .replace("Ş", "s")
         .replace("ğ", "g")
         .replace("Ğ", "g")
         .replace("ü", "u")
         .replace("Ü", "u")
         .replace("ö", "o")
         .replace("Ö", "o")
         .replace("ç", "c")
         .replace("Ç", "c")
    )

    # 🗑️ Doğal dilde silme / artık ihtiyaç olmaması
    sil_ifadeleri = [
        "sil",
        "kaldir",
        "temizle",
        "gereksiz",
        "gerek yok",
        "gerek kalmadi",
        "lazim degil",
        "ihtiyacim yok",
        "artik istemiyorum",
        "artik kullanmiyorum",
        "kapatalim",
        "kapat bunu",
    ]

    # Silme niyeti için bağlamlı ifadeler.
    if any(x in m for x in sil_ifadeleri):
        return "sil"

    # 🧾 Borcun/taksidin bittiğini bildirme
    durum_ifadeleri = [
        "taksidi bitmis",
        "taksidini odedim",
        "son taksidi de odedim",
        "borcu bitti",
        "borcu bitmis",
        "artik borc degil",
        "odemesi bitti",
        "borc kapandi",
        "borc kapanmis",
    ]

    if any(x in m for x in durum_ifadeleri):
        return "durum"

    return None


def akilli_borc_historyden_bul(history):
    """Konuşma geçmişindeki son kullanıcı mesajından aktif borcu bulur."""
    borclar = borclari_yukle()

    for item in reversed(history or []):
        if not isinstance(item, dict):
            continue
        if item.get("role") != "user":
            continue

        metin = str(
            item.get("text", item.get("content", ""))
        ).lower()

        for b in borclar:
            ad = str(b.get("ad", "")).strip().lower()
            if ad and ad in metin:
                return b

    return None


def akilli_borc_bul(mesaj, aktif_borc_id=None, history=None):
    borclar = borclari_yukle()
    m = str(mesaj).lower()

    # Sabit faturaları doğal ifadeden kanonik kayda bağla.
    fatura = fatura_adi_bul(mesaj)
    if fatura:
        for b in borclar:
            if b.get("ad") == fatura:
                return b

    for b in borclar:
        ad = str(b.get("ad", "")).strip().lower()
        if ad and ad in m:
            return b

    if aktif_borc_id is not None:
        for b in borclar:
            if str(b.get("id")) == str(aktif_borc_id):
                return b

    return akilli_borc_historyden_bul(history)


    return None


def akilli_borc_isle(mesaj, aktif_borc_id=None, history=None):
    niyet = akilli_borc_niyeti(mesaj)

    # 🧠 Mesajda doğrudan bir borç adı varsa,
    # açık işlem söylenmese bile mevcut durumu getir.
    borc = akilli_borc_bul(mesaj, None, None)

    if not niyet and borc:
        niyet = "durum"

    if not niyet:
        return None, aktif_borc_id

    # Borç mesajda yoksa aktif/history bağlamını kullan.
    if borc is None:
        borc = akilli_borc_bul(mesaj, aktif_borc_id, history)

    if borc is None:
        borc = akilli_borc_bul(mesaj, aktif_borc_id, history)

    if not borc:
        return "Bu işlem için hangi borcu kastettiğini anlayamadım.", aktif_borc_id

    if niyet == "durum":
        aktif_borc_id = borc.get("id")
        kalan = float(borc.get("kalan_borc", 0) or 0)

        if str(borc.get("kategori", "")).strip().lower() == "fatura":
            if kalan <= 0:
                return f"{borc.get('ad')} faturası için kayıtlı tutar: 0 TL.", aktif_borc_id
            return f"{borc.get('ad')} faturası için kayıtlı tutar: {kalan:,.0f} TL.", aktif_borc_id

        if kalan <= 0:
            return f"Evet, {borc.get('ad')} taksidi bitmiş. Kalan borç: 0 TL.", aktif_borc_id

        return f"{borc.get('ad')} için borç henüz bitmemiş. Kalan borç: {kalan:,.0f} TL.", aktif_borc_id

    if niyet == "sil":
        silinen = borc.get("ad")
        basarili, _ = borc_sil(borc.get("id"))

        if basarili:
            return f"Tamam. {silinen} borcunu artık gerekmiyor diye kayıtlardan sildim.", None

        return "Borç silinirken bir sorun oluştu.", aktif_borc_id

    return None, aktif_borc_id
