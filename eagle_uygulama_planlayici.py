import re


class EagleUygulamaPlanlayici:
    """Kullanıcı isteğini genel bir uygulama bileşen planına dönüştürür."""

    @staticmethod
    def _gereksinimleri_cikar(mesaj, konu):
        """
        Kullanıcı isteğinden güvenli ve deterministik gereksinim özeti çıkarır.

        Bilinmeyen alanlarda uydurma domain bilgisi üretmez; genel CRUD
        fallback'ı için yalnızca güvenli varsayılanları kullanır.
        """
        metin = f"{mesaj} {konu}".lower()

        varlik_eslesmeleri = (
            ("müşteri", "musteri"),
            ("musteri", "musteri"),
            ("randevu", "randevu"),
            ("kitap", "kitap"),
            ("üye", "uye"),
            ("uye", "uye"),
            ("evcil hayvan", "evcil_hayvan"),
            ("hayvan", "hayvan"),
            ("görev", "gorev"),
            ("gorev", "gorev"),
            ("stok", "stok"),
            ("ürün", "urun"),
            ("urun", "urun"),
            ("not", "not"),
            ("haber", "haber"),
            ("haberler", "haber"),
        )

        varliklar = []
        for ifade, varlik in varlik_eslesmeleri:
            if ifade in metin and varlik not in varliklar:
                varliklar.append(varlik)

        if "evcil_hayvan" in varliklar and "hayvan" in varliklar:
            varliklar.remove("hayvan")

        if not varliklar:
            varliklar = ["kayit"]

        alanlar = {
            "kayit": ["id", "veri"],
        }

        if "musteri" in varliklar:
            alanlar["musteri"] = ["id", "ad", "telefon", "email"]
        if "randevu" in varliklar:
            alanlar["randevu"] = ["id", "baslik", "tarih", "durum"]
        if "kitap" in varliklar:
            alanlar["kitap"] = ["id", "baslik", "yazar", "durum"]
        if "uye" in varliklar:
            alanlar["uye"] = ["id", "ad", "telefon", "durum"]
        if "evcil_hayvan" in varliklar:
            alanlar["evcil_hayvan"] = ["id", "ad", "tur", "notlar"]
        if "hayvan" in varliklar:
            alanlar["hayvan"] = ["id", "ad", "tur", "notlar"]
        if "gorev" in varliklar:
            alanlar["gorev"] = ["id", "baslik", "aciklama", "durum"]
        if "stok" in varliklar:
            alanlar["stok"] = ["id", "urun", "miktar"]
        if "urun" in varliklar:
            alanlar["urun"] = ["id", "ad", "miktar"]
        if "not" in varliklar:
            alanlar["not"] = ["id", "baslik", "icerik"]
        if "haber" in varliklar:
            alanlar["haber"] = ["id", "baslik", "icerik", "kategori"]

        islem_sozcukleri = (
            ("ekle", "ekle"),
            ("oluştur", "olustur"),
            ("olustur", "olustur"),
            ("kaydet", "kaydet"),
            ("listele", "listele"),
            ("görüntüle", "goruntule"),
            ("goruntule", "goruntule"),
            ("detay", "detay"),
            ("ara", "ara"),
            ("filtrele", "filtrele"),
            ("güncelle", "guncelle"),
            ("guncelle", "guncelle"),
            ("düzenle", "duzenle"),
            ("duzenle", "duzenle"),
            ("sil", "sil"),
            ("takip", "takip"),
            ("yönet", "yonet"),
            ("yonet", "yonet"),
        )

        islemeler = []
        for ifade, islem in islem_sozcukleri:
            if ifade in metin and islem not in islemeler:
                islemeler.append(islem)

        if not islemeler:
            islemeler = ["ekle", "listele", "detay", "guncelle", "sil"]

        ekranlar = []
        if any(
            x in metin
            for x in ("arayüz", "arayuz", "web", "ekran", "sayfa", "mobil", "uygulama")
        ):
            ekranlar.extend(["liste", "ekle", "detay"])

        if not ekranlar:
            ekranlar = ["liste", "ekle", "detay"]

        iliskiler = []

        if "randevu" in varliklar and "musteri" in varliklar:
            iliskiler.append("randevu -> musteri")
        if "stok" in varliklar and "urun" in varliklar:
            iliskiler.append("stok -> urun")
        if "uye" in varliklar and "randevu" in varliklar:
            iliskiler.append("randevu -> uye")

        return {
            "varliklar": varliklar,
            "alanlar": alanlar,
            "islemler": islemeler,
            "ekranlar": ekranlar,
            "iliskiler": iliskiler,
        }

    def planla(self, mesaj, konu=None, cikti_turu="proje"):
        mesaj = str(mesaj or "").strip()
        konu = str(konu or mesaj).strip()

        k = mesaj.lower()

        tam_uygulama = any(x in k for x in (
            "uygulaması",
            "uygulamasi",
            "uygulama",
            "sistem",
            "platform",
            "yönetim sistemi",
            "yonetim sistemi",
            "takip sistemi",
            "otomasyon",
            "web uygulaması",
            "web uygulamasi",
            "çalışan uygulama",
            "calisan uygulama",
        ))

        veri_tabanli = any(x in k for x in (
            "veritabanı",
            "veritabani",
            "database",
            "db",
            "kayıt",
            "kayit",
            "kaydet",
            "listele",
            "takip",
            "yönetim",
            "yonetim",
        ))

        api_istegi = any(x in k for x in (
            "api",
            "rest",
            "rest api",
            "backend",
            "endpoint",
            "servis",
        ))

        arayuz_istegi = any(x in k for x in (
            "arayüz",
            "arayuz",
            "ui",
            "frontend",
            "web",
            "ekran",
            "sayfa",
            "mobil",
        ))

        dis_kaynak = any(x in k for x in (
            "internetten",
            "internet üzerinden",
            "internet uzerinden",
            "internet verisi",
            "gerçek veri",
            "gercek veri",
            "canlı veri",
            "canli veri",
            "dış kaynaktan",
            "dis kaynaktan",
            "veri kaynağı",
            "veri kaynagi",
            "veri akışı",
            "veri akisi",
            "rss",
            "harici api",
            "external api",
        ))

        # Bazı uygulama türleri doğası gereği harici veri kaynağı
        # gerektirir. Bu alanlar tek tek uygulama üreticisi olarak
        # değil, genel gereksinim olarak değerlendirilir.
        veri_dogasi_alanlari = (
            "haber",
            "news",
            "hava durumu",
            "hava tahmini",
            "finans verisi",
            "borsa verisi",
            "döviz kuru",
            "doviz kuru",
            "canlı kur",
            "canli kur",
            "ürün fiyatı",
            "urun fiyati",
            "canlı fiyat",
            "canli fiyat",
            "spor skoru",
            "maç skoru",
            "mac skoru",
            "harita verisi",
            "trafik verisi",
            "sosyal medya akışı",
            "sosyal medya akisi",
        )

        if any(x in k for x in veri_dogasi_alanlari) or any(
            x in konu.lower() for x in veri_dogasi_alanlari
        ):
            dis_kaynak = True

        gereksinimler = self._gereksinimleri_cikar(mesaj, konu)

        if tam_uygulama:
            veri_tabanli = True
            api_istegi = True
            arayuz_istegi = True

        if not any((tam_uygulama, veri_tabanli, api_istegi, arayuz_istegi, dis_kaynak)):
            return None

        bilesenler = [
            "model",
            "service",
        ]

        if veri_tabanli:
            bilesenler.append("database")

        if dis_kaynak:
            bilesenler.append("source")

        if api_istegi:
            bilesenler.append("api")

        if arayuz_istegi:
            bilesenler.extend(("ui", "detail"))

        bilesenler.append("tests")

        return {
            "konu": konu,
            "cikti_turu": cikti_turu,
            "profil": "tam_uygulama" if tam_uygulama else "uygulama",
            "bilesenler": bilesenler,
            "veri_tabanli": veri_tabanli,
            "api": api_istegi,
            "arayuz": arayuz_istegi,
            "detay_ekrani": arayuz_istegi,
            "dis_kaynak": dis_kaynak,
            "gereksinimler": gereksinimler,
            "varliklar": gereksinimler["varliklar"],
            "alanlar": gereksinimler["alanlar"],
            "islemler": gereksinimler["islemler"],
            "ekranlar": gereksinimler["ekranlar"],
            "iliskiler": gereksinimler["iliskiler"],
            "harici_kaynak_gerekli": dis_kaynak,
        }
