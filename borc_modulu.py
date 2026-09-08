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
        ("elektrige", "Elektrik"),
        ("internet", "İnternet"),
        ("telefon", "Telefon"),
        ("su", "Su"),
    ]

    for aranan, kanonik in eslesmeler:
        if aranan in m:
            return kanonik

    return None


def borc_ekle(ad, kategori, toplam_borc):
    borclar = borclari_yukle()
    yeni_id = str(len(borclar) + 1)
    
    yeni_borc = {
        "id": yeni_id,
        "ad": str(ad).strip(),
        "kategori": str(kategori).strip().capitalize(),
        "toplam_borc": float(toplam_borc),
        "odenen_tutar": 0.0,
        "kalan_borc": float(toplam_borc)
    }
    
    borclar.append(yeni_borc)
    borclari_kaydet(borclar)
    return yeni_borc


def borc_guncelle(
    borc_id,
    ad=None,
    kategori=None,
    toplam_borc=None,
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

def borc_ozeti():
    """Borçların toplam, ödenen ve kalan tutarlarını hesaplar."""
    borclar = borclari_yukle()

    toplam_borc = 0.0
    toplam_odenen = 0.0
    toplam_kalan = 0.0

    for b in borclar:
        toplam = float(b.get("toplam_borc", 0.0) or 0.0)
        odenen = float(b.get("odenen_tutar", 0.0) or 0.0)
        kalan = max(0.0, toplam - odenen)

        b["toplam_borc"] = toplam
        b["odenen_tutar"] = odenen
        b["kalan_borc"] = kalan

        toplam_borc += toplam
        toplam_odenen += odenen
        toplam_kalan += kalan

    borclari_kaydet(borclar)

    return {
        "toplam_borc": toplam_borc,
        "toplam_odenen": toplam_odenen,
        "toplam_kalan": toplam_kalan,
        "borclar": borclar
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
    """Doğal Türkçe borç ve fatura işlemlerini yönetir."""
    mesaj = str(mesaj or "").strip()
    m = mesaj.lower()

    norm = m.translate(str.maketrans({
        "ı": "i",
        "ş": "s",
        "ğ": "g",
        "ü": "u",
        "ö": "o",
        "ç": "c"
    }))

    # Borçları sade şekilde göster
    if any(x in norm for x in [
        "borclarimi goster",
        "kalan borc",
        "borc listesi",
        "borclarim"
    ]):
        borclar = borclari_yukle()

        if not borclar:
            return "Henüz kayıtlı bir borcunuz bulunmuyor."

        def tl(sayi):
            return f"{float(sayi):,.0f}".replace(",", ".")

        satirlar = ["💳 BORÇLARIM", ""]

        for b in borclar:
            satirlar.append(
                f"• {b.get('ad', 'Bilinmeyen')}\n"
                f"  Toplam Borç: {tl(b.get('toplam_borc', 0))} TL\n"
                f"  Ödenen: {tl(b.get('odenen_tutar', 0))} TL\n"
                f"  Kalan: {tl(b.get('kalan_borc', 0))} TL"
            )

        return "\n\n".join(satirlar)

    # Toplam kalan borç
    if any(x in norm for x in [
        "borclarimin toplami",
        "toplam borc ne kadar"
    ]):
        borclar = borclari_yukle()
        toplam_kalan = sum(
            max(
                0.0,
                float(b.get("toplam_borc", 0) or 0)
                - float(b.get("odenen_tutar", 0) or 0)
            )
            for b in borclar
        )
        return f"Toplam kalan borcunuz: **{toplam_kalan:,.2f} TL**"

    # Fatura adı
    fatura = fatura_adi_bul(mesaj)

    # Sayısal tutar
    sayilar = re.findall(r'\d+(?:[.,]\d+)?', mesaj)

    # Ödeme ifadeleri: "ödedim", "ödeme yaptım", "yatırdım" vb.
    odeme_ifadeleri = [
        "odedim",
        "odendi",
        "odeme yaptim",
        "odeme yapildi",
        "yatirdim",
        "yatirildi",
        "para verdim",
        "parasini verdim"
    ]

    if fatura and any(x in norm for x in odeme_ifadeleri):
        borclar = borclari_yukle()

        for b in borclar:
            if b.get("ad") != fatura:
                continue

            kalan = max(
                0.0,
                float(b.get("toplam_borc", 0) or 0)
                - float(b.get("odenen_tutar", 0) or 0)
            )

            if kalan <= 0:
                return f"ℹ️ **{fatura}** için kalan borç bulunmuyor."

            if sayilar:
                tutar = para_degerini_oku(sayilar[-1])
                if tutar <= 0:
                    return "Ödeme tutarı 0'dan büyük olmalı."

                gercek_odeme = min(tutar, kalan)
                b["odenen_tutar"] = float(b.get("odenen_tutar", 0) or 0) + gercek_odeme
                b["kalan_borc"] = max(
                    0.0,
                    float(b.get("toplam_borc", 0) or 0) - b["odenen_tutar"]
                )
                borclari_kaydet(borclar)

                return (
                    f"✅ **{fatura}** için {gercek_odeme:,.2f} TL ödeme işlendi.\n"
                    f"Ödenen: **{b['odenen_tutar']:,.2f} TL**\n"
                    f"Kalan: **{b['kalan_borc']:,.2f} TL**"
                )

            # Tutar belirtilmediyse kalan borcun tamamını öde
            b["odenen_tutar"] = float(b.get("toplam_borc", 0) or 0)
            b["kalan_borc"] = 0.0
            borclari_kaydet(borclar)

            return f"✅ **{fatura}** faturası ödendi. Kalan: **0 TL**."

        return f"**{fatura}** faturası kaydı bulunamadı."

    # Fatura tutarı girme/güncelleme
    if fatura and sayilar:
        tutar = para_degerini_oku(sayilar[-1])

        if tutar <= 0:
            return "Fatura tutarı 0'dan büyük olmalı."

        borclar = borclari_yukle()

        for b in borclar:
            if b.get("ad") == fatura:
                b["toplam_borc"] = tutar
                b["odenen_tutar"] = 0.0
                b["kalan_borc"] = tutar
                borclari_kaydet(borclar)

                return (
                    f"✅ **{fatura} faturası** "
                    f"{tutar:,.2f} TL olarak güncellendi."
                )

        return f"**{fatura}** faturası kaydı bulunamadı."

    # Normal borç ekleme
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

            yeni = borc_ekle(ad, kategori, tutar)

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

    # 💰 Ödeme niyeti
    odeme_ifadeleri = [
        "odedim",
        "odendi",
        "odeme yaptim",
        "odeme yapildi",
        "yatirdim",
        "yatirildi",
        "para verdim",
        "parasini verdim",
    ]

    if any(x in m for x in odeme_ifadeleri):
        return "odeme"

    # 🧾 Borcun kapandığını bildirme
    durum_ifadeleri = [
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
            return f"Evet, {borc.get('ad')} borcu bitmiş. Kalan borç: 0 TL.", aktif_borc_id

        return f"{borc.get('ad')} için borç henüz bitmemiş. Kalan borç: {kalan:,.0f} TL.", aktif_borc_id

    if niyet == "sil":
        silinen = borc.get("ad")
        basarili, _ = borc_sil(borc.get("id"))

        if basarili:
            return f"Tamam. {silinen} borcunu artık gerekmiyor diye kayıtlardan sildim.", None

        return "Borç silinirken bir sorun oluştu.", aktif_borc_id

    return None, aktif_borc_id
