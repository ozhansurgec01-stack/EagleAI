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
    """Kullanıcının doğal Türkçe mesajını analiz eder ve ilgili borç işlemine yönlendirir."""
    mesaj_kucuk = mesaj.lower().replace("İ", "i").replace("I", "ı")
    
    # 1. Rapor / Listeleme / Toplam sorguları
    if any(k in mesaj_kucuk for k in ["borçlarımı göster", "borclarimi goster", "kalan borç", "kalan borc", "borç listesi", "borc listesi"]):
        rapor = genel_rapor()
        if not rapor["borclar"]:
            return "Henüz kayıtlı bir borcunuz bulunmuyor. 'Elektrik borcu ekle: 3000 TL' şeklinde ekleme yapabilirsiniz."
        
        def tl_format(sayi):
            return f"{sayi:,.0f}".replace(",", ".")

        yanit = "BORÇ VE TAKSİT RAPORU\\n\\n"

        for b in rapor["borclar"]:
            yanit += (
                f"• {b['ad']}\\n"
                f"  Kategori: {b['kategori']}\\n"
                f"  Aylık taksit: {tl_format(b.get('aylik_taksit', 0.0))} TL\\n"
                f"  Toplam borç: {tl_format(b['toplam_borc'])} TL\\n"
                f"  Ödenen: {tl_format(b['odenen_tutar'])} TL\\n"
                f"  Kalan: {tl_format(b['kalan_borc'])} TL\\n"
                f"  Taksit: {b['taksit_sayisi']}\\n"
                f"  Kalan taksit: {b.get('kalan_taksit', 0)}\\n\\n"
            )

        yanit += (
            f"💰 Genel Toplam: {tl_format(rapor['toplam_borc'])} TL\\n"
            f"💵 Ödenen: {tl_format(rapor['toplam_odenen'])} TL\\n"
            f"📌 Kalan: {tl_format(rapor['toplam_kalan'])} TL"
        )

        return yanit

    if any(k in mesaj_kucuk for k in ["borçlarımın toplamı", "borclarimin toplami", "toplam borç ne kadar", "toplam borc ne kadar"]):
        rapor = genel_rapor()
        return f"Toplam kalan borcunuz: **{rapor['toplam_kalan']:,.2f} TL** (Genel Borç: {rapor['toplam_borc']:,.2f} TL, Ödenen: {rapor['toplam_odenen']:,.2f} TL)"

    # 2. Ödeme yapma (Örn: "Elektrik borcuma 500 TL ödeme yaptım")
    if "ödeme" in mesaj_kucuk or "odedim" in mesaj_kucuk or "yatırdım" in mesaj_kucuk or "yatirdim" in mesaj_kucuk:
        # Sayı bul
        sayilar = re.findall(r'\d+(?:[.,]\d+)?', mesaj)
        if sayilar:
            tutar = para_degerini_oku(sayilar[-1])
            # Borç adını bulmaya çalış
            borclar = borclari_yukle()
            hedef_borc = None
            for b in borclar:
                if b["ad"].lower() in mesaj_kucuk or b["kategori"].lower() in mesaj_kucuk:
                    hedef_borc = b["ad"]
                    break
            
            if hedef_borc:
                basari, guncel = odeme_yap(hedef_borc, tutar)
                if basari:
                    return f"✅ **{guncel['ad']}** borcunuza {tutar:,.2f} TL ödeme eklendi. Güncel kalan borç: **{guncel['kalan_borc']:,.2f} TL**"
            
            # Eğer doğrudan isim eşleşmediyse ilk borca veya genel işleme yönlendir
            if borclar:
                basari, guncel = odeme_yap(borclar[0]["ad"], tutar)
                if basari:
                    return f"✅ **{guncel['ad']}** borcunuza {tutar:,.2f} TL ödeme eklendi. Güncel kalan borç: **{guncel['kalan_borc']:,.2f} TL**"
        
        return "Ödeme miktarını veya hangi borca ödeme yaptığınızı tam anlayamadım. Örn: 'Elektrik borcuma 500 TL ödeme yaptım'"

    # 3. Borç ekleme (Örn: "Elektrik borcu ekle: 3000 TL" veya "Kredi borcu 50000 TL")
    if "ekle" in mesaj_kucuk or "borcum var" in mesaj_kucuk or "borç ekle" in mesaj_kucuk:
        sayilar = re.findall(r'\d+(?:[.,]\d+)?', mesaj)
        if sayilar:
            tutar = para_degerini_oku(sayilar[-1])
            
            # Kategori tespiti
            kategori = "Diğer"
            for kat in ["Kredi", "Elektrik", "Su", "Altın", "Fatura", "Kira"]:
                if kat.lower() in mesaj_kucuk:
                    kategori = kat
                    break
            
            # Ad tespiti (basitçe mesajdan çıkarım)
            ad_temiz = mesaj_kucuk.replace("ekle", "").replace("borc", "").replace("borç", "").replace("tl", "").strip()
            ad = ad_temiz if len(ad_temiz) > 2 else f"{kategori} Borcu"
            ad = ad.capitalize()
            
            yeni = borc_ekle(ad, kategori, tutar, 1)
            return f"✅ Yeni borç eklendi:\n• **{yeni['ad']}** ({yeni['kategori']}) - Tutar: {yeni['toplam_borc']:,.2f} TL"

    # 4. Taksit hesaplama (Örn: "50000 TL borcu 10 taksite böl")
    if "taksit" in mesaj_kucuk or "taksite böl" in mesaj_kucuk:
        sayilar = re.findall(r'\d+', mesaj)
        if len(sayilar) >= 2:
            tutar = float(sayilar[0]) if float(sayilar[0]) > 12 else float(sayilar[1])
            taksit = int(sayilar[1]) if float(sayilar[0]) > 12 else int(sayilar[0])
            if taksit <= 0: taksit = 1
            aylik = tutar / taksit
            return f"🧮 **Taksit Hesaplama:**\n• Toplam Tutar: {tutar:,.2f} TL\n• Taksit Sayısı: {taksit}\n• **Aylık Ödeme:** **{aylik:,.2f} TL**"

    return None
