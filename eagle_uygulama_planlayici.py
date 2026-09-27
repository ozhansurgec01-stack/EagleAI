import re


class EagleUygulamaPlanlayici:
    """Kullanıcı isteğini genel bir uygulama bileşen planına dönüştürür."""

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
            "hava",
            "finans",
            "borsa",
            "döviz",
            "doviz",
            "kur",
            "fiyat",
            "spor",
            "skor",
            "maç",
            "mac",
            "harita",
            "trafik",
            "sosyal medya",
            "sosyal akış",
            "sosyal akis",
        )

        if any(x in k for x in veri_dogasi_alanlari) or any(
            x in konu.lower() for x in veri_dogasi_alanlari
        ):
            dis_kaynak = True

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
        }
