"""
🦅 EAGLE MERKEZ MOTORU v1.0

Web = veri toplama katmanı.
Bu modül ham web sonuçlarını kullanıcı cevabı olarak göstermez.

Akış:
Soru
 -> mevcut motor sonucu
 -> web verisi
 -> aday cevap çıkarımı
 -> kaynak/tekrar kontrolü
 -> net cevap
 -> sonuç yoksa Gemini son çare sinyali

Mevcut eagle_api.py motorlarını değiştirmez.
"""

import re
from collections import Counter
from urllib.parse import urlparse


class EagleMerkezSonuc:
    def __init__(
        self,
        ok=False,
        cevap="",
        guven=0.0,
        kaynak_sayisi=0,
        gemini_gerekli=False,
        kaynak_goster=False,
        neden=""
    ):
        self.ok = bool(ok)
        self.cevap = str(cevap or "").strip()
        self.guven = float(guven or 0.0)
        self.kaynak_sayisi = int(kaynak_sayisi or 0)
        self.gemini_gerekli = bool(gemini_gerekli)
        self.kaynak_goster = bool(kaynak_goster)
        self.neden = str(neden or "")

    def as_dict(self):
        return {
            "ok": self.ok,
            "cevap": self.cevap,
            "guven": self.guven,
            "kaynak_sayisi": self.kaynak_sayisi,
            "gemini_gerekli": self.gemini_gerekli,
            "kaynak_goster": self.kaynak_goster,
            "neden": self.neden,
        }


class EagleMerkezMotoru:
    SURUM = "1.0"

    # Kullanıcı açıkça kaynak/arama sonucu isterse
    # merkezi motor ham kaynak görünümüne izin verir.
    KAYNAK_ISTEKLERI = (
        "haberleri göster",
        "haberleri gösterir misin",
        "kaynakları göster",
        "kaynaklari göster",
        "kaynakları ver",
        "kaynaklari ver",
        "arama sonuçlarını göster",
        "arama sonuclarini göster",
        "arama sonuçları",
        "arama sonuclari",
        "web sonuçlarını göster",
        "web sonuclarini göster",
        "linkleri göster",
        "linkleri ver",
        "siteleri göster",
        "hangi kaynaklar",
    )

    # Bunlar mevcut cevabın kullanıcıya doğrudan verilmesini
    # engelleyen açık web-listesi ifadeleridir.
    HAM_WEB_BASLIKLARI = (
        "eagle web",
        "web arama sonuçları",
        "web arama sonuclari",
        "arama sonuçları",
        "arama sonuclari",
    )

    # Güncel değer sorularını genel olarak tanımaya yardımcı olur.
    DEGER_TERIMLERI = (
        "fiyat",
        "fiyatı",
        "fiyati",
        "kur",
        "kuru",
        "kaç tl",
        "kaç lira",
        "değeri",
        "degeri",
        "oran",
        "skor",
        "sonuç",
        "sonuc",
        "kaç kaç",
        "ne oldu",
    )

    def __init__(self):
        pass

    @staticmethod
    def normalize(text):
        text = str(text or "").strip().lower()
        text = (
            text.replace("İ", "i")
            .replace("I", "ı")
        )
        return re.sub(r"\s+", " ", text)

    @classmethod
    def kaynak_isteniyor_mu(cls, mesaj):
        metin = cls.normalize(mesaj)
        return any(
            ifade in metin
            for ifade in cls.KAYNAK_ISTEKLERI
        )

    @classmethod
    def deger_sorusu_mu(cls, mesaj):
        metin = cls.normalize(mesaj)
        return any(
            ifade in metin
            for ifade in cls.DEGER_TERIMLERI
        )

    @staticmethod
    def domain(url):
        try:
            return urlparse(str(url or "")).netloc.lower()
        except Exception:
            return ""

    @classmethod
    def temizle_web_verisi(cls, web_verisi):
        """
        Web motorundan gelen kayıtları standartlaştırır.
        Geçersiz/boş kayıtları atar.
        """
        temiz = []

        if not isinstance(web_verisi, (list, tuple)):
            return temiz

        for sonuc in web_verisi:
            if not isinstance(sonuc, dict):
                continue

            baslik = str(
                sonuc.get("title", "")
            ).strip()

            ozet = str(
                sonuc.get("snippet", "")
            ).strip()

            url = str(
                sonuc.get("url", "")
            ).strip()

            metin = " ".join(
                x for x in (baslik, ozet)
                if x
            ).strip()

            if not metin:
                continue

            temiz.append({
                "title": baslik,
                "snippet": ozet,
                "url": url,
                "domain": cls.domain(url),
                "text": metin,
            })

        return temiz

    @staticmethod
    def sayisal_adaylar(metin):
        """
        Metindeki sayısal ifadeleri çıkarır.
        Para/kur/skor/fiyat gibi sonuçlarda yardımcı katmandır.
        """
        if not metin:
            return []

        desenler = (
            r"\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,4})?\b",
            r"\b\d{1,3}\s*[-:]\s*\d{1,3}\b",
            r"\b\d+(?:[.,]\d+)?\s*(?:TL|₺|USD|EUR|GBP|dolar|euro|sterlin)\b",
        )

        bulunan = []

        for desen in desenler:
            bulunan.extend(
                re.findall(
                    desen,
                    metin,
                    flags=re.IGNORECASE
                )
            )

        return [
            x.strip()
            for x in bulunan
            if x.strip()
        ]

    @classmethod
    def ortak_sayisal_bilgiler(cls, veriler):
        """
        Aynı sayısal bilginin KAÇ FARKLI KAYNAKTA
        görüldüğünü ölçer.

        Aynı kaynak içinde tekrar eden sayı yalnızca
        bir kaynak olarak sayılır.

        Sayının birimli/birimsiz yazımları aynı değerse
        tek aday kabul edilir.
        """
        def deger_normalize(deger):
            deger = cls.normalize(deger)

            # Para birimi eklerini karşılaştırmadan önce ayır.
            deger = re.sub(
                r"\s*(tl|₺|usd|eur|gbp|dolar|euro|sterlin)\s*$",
                "",
                deger,
                flags=re.IGNORECASE
            ).strip()

            return deger

        kaynak_degerleri = []

        for veri in veriler or []:
            if not isinstance(veri, dict):
                continue

            metin = str(veri.get("text", "") or "")

            if not metin:
                metin = " ".join(
                    str(veri.get(alan, "") or "")
                    for alan in ("title", "snippet")
                ).strip()

            if not metin:
                continue

            adaylar = cls.sayisal_adaylar(metin)

            benzersiz = {
                deger_normalize(x)
                for x in adaylar
                if str(x).strip()
            }

            if benzersiz:
                kaynak_degerleri.append(benzersiz)

        if not kaynak_degerleri:
            return []

        tum_degerler = set().union(*kaynak_degerleri)

        sonuc = []

        for deger in tum_degerler:
            tekrar = sum(
                1
                for kaynak in kaynak_degerleri
                if deger in kaynak
            )

            sonuc.append({
                "deger": deger,
                "tekrar": tekrar,
            })

        return sorted(
            sonuc,
            key=lambda x: (-x["tekrar"], x["deger"])
        )

    @classmethod
    def metin_tekrar_skoru(cls, veriler):
        """
        Kaynakların aynı bilgiye işaret edip etmediğini
        kaba ama genel bir şekilde ölçer.

        Burada site/ekip/şehir hardcode edilmez.
        """
        if len(veriler) < 2:
            return 0.0

        kelime_kumeleri = []

        for veri in veriler:
            metin = cls.normalize(
                veri.get("text", "")
            )

            kelimeler = {
                kelime
                for kelime in re.findall(
                    r"[a-z0-9çğıöşü]+",
                    metin
                )
                if len(kelime) >= 4
            }

            kelime_kumeleri.append(kelimeler)

        eslesmeler = 0
        toplam = 0

        for i in range(len(kelime_kumeleri)):
            for j in range(i + 1, len(kelime_kumeleri)):
                toplam += 1

                ortak = (
                    kelime_kumeleri[i]
                    & kelime_kumeleri[j]
                )

                if len(ortak) >= 3:
                    eslesmeler += 1

        if toplam == 0:
            return 0.0

        return eslesmeler / toplam

    @classmethod
    def _sayisal_ifadeleri_bul(cls, metin):
        """
        Metindeki sayıların konumlarını ve değerlerini bulur.
        Sayıyı çevresindeki kelimelerle birlikte korur.
        """
        if not metin:
            return []

        sonuc = []

        desen = re.compile(
            r"(?<![\w])"
            r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,4})?"
            r"|\d{1,3}\s*[-:]\s*\d{1,3})"
            r"(?![\w])",
            flags=re.IGNORECASE
        )

        for eslesme in desen.finditer(metin):
            deger = eslesme.group(1).strip()

            sol = max(0, eslesme.start() - 90)
            sag = min(len(metin), eslesme.end() + 90)

            baglam = metin[sol:sag].strip()

            sonuc.append({
                "deger": deger,
                "baglam": baglam,
                "start": eslesme.start(),
                "end": eslesme.end(),
            })

        return sonuc

    @classmethod
    def _takim_skoru_cikar(cls, mesaj, veriler):
        """
        Skorları web kaynaklarından çıkarır.
        Takım veya lig isimleri hardcode edilmez.
        Skorun hemen çevresindeki kelimeler kullanılır.
        Aynı sonuç en az iki kaynakta görülürse doğrulanır.
        """
        import re
        from collections import defaultdict

        skor_deseni = re.compile(
            r"(\d{1,2})\s*[-–—]\s*(\d{1,2})"
        )

        duraklar = {
            "maç", "mac", "sonucu", "sonuc", "skoru",
            "score", "match", "result"
        }

        adaylar = []

        for kaynak_no, veri in enumerate(veriler or []):
            if not isinstance(veri, dict):
                continue

            # Her alanı ayrı ayrı değerlendir.
            alanlar = [
                str(veri.get("title", "")),
                str(veri.get("snippet", "")),
                str(veri.get("text", "")),
            ]

            for metin in alanlar:
                if not metin.strip():
                    continue

                for eslesme in skor_deseni.finditer(metin):
                    sol = metin[:eslesme.start()].strip()
                    sag = metin[eslesme.end():].strip()

                    sol_kelime = sol.split()
                    sag_kelime = sag.split()

                    if not sol_kelime or not sag_kelime:
                        continue

                    # Skorun hemen solundaki anlamlı kelime.
                    home = sol_kelime[-1].strip(
                        ".,:;|()[]{}<>-–—"
                    )

                    # Skorun hemen sağındaki anlamlı kelime.
                    away = sag_kelime[0].strip(
                        ".,:;|()[]{}<>-–—"
                    )

                    if not home or not away:
                        continue

                    # Genel sonuç kelimelerini takım adı kabul etme.
                    if cls.normalize(home) in duraklar:
                        continue

                    if cls.normalize(away) in duraklar:
                        continue

                    if not re.search(
                        r"[A-Za-zÇĞİÖŞÜçğıöşü]",
                        home
                    ):
                        continue

                    if not re.search(
                        r"[A-Za-zÇĞİÖŞÜçğıöşü]",
                        away
                    ):
                        continue

                    adaylar.append({
                        "home": home,
                        "away": away,
                        "a": eslesme.group(1),
                        "b": eslesme.group(2),
                        "kaynak": kaynak_no,
                    })

        if not adaylar:
            return None, 0.0

        # Aynı kaynakta tekrar eden aynı sonucu tek say.
        gruplar = defaultdict(set)

        for aday in adaylar:
            anahtar = (
                cls.normalize(aday["home"]),
                cls.normalize(aday["away"]),
                aday["a"],
                aday["b"],
            )
            gruplar[anahtar].add(aday["kaynak"])

        # En fazla bağımsız kaynakta doğrulanan sonucu seç.
        en_iyi = max(
            gruplar.items(),
            key=lambda x: len(x[1])
        )

        anahtar, kaynaklar = en_iyi

        if len(kaynaklar) < 2:
            return None, 0.0

        home_norm, away_norm, skor_a, skor_b = anahtar

        for aday in adaylar:
            if (
                cls.normalize(aday["home"]) == home_norm
                and cls.normalize(aday["away"]) == away_norm
                and aday["a"] == skor_a
                and aday["b"] == skor_b
            ):
                return (
                    f"{aday['home']} {skor_a} - "
                    f"{skor_b} {aday['away']}",
                    0.90
                )

        return None, 0.0

    @classmethod
    def net_sayisal_cevap(cls, mesaj, veriler):
        """
        Web verisinden kullanıcının gerçekten sorduğu sayısal
        değeri çıkarır.

        Öncelik:
        1. Skor/maç sonucu
        2. Kullanıcının istediği birime doğrudan bağlı sayı
        3. Ondalıklı/değer niteliğindeki sayı
        4. Birden fazla kaynakta doğrulanan sayı

        Genel amaçlıdır; takım, lig, para birimi veya site
        adına özel hardcode içermez.
        """
        if not veriler:
            return None, 0.0

        # -------------------------------------------------
        # 1) Spor skorları önce korunur.
        # -------------------------------------------------
        skor_cevap, skor_guven = cls._takim_skoru_cikar(
            mesaj,
            veriler
        )

        if skor_cevap:
            return skor_cevap, skor_guven

        # -------------------------------------------------
        # 2) Kullanıcının istediği birimi belirle.
        # -------------------------------------------------
        mesaj_norm = cls.normalize(mesaj)

          # -------------------------------------------------
        # 2.1) Kur sorularında doğrudan "1 PARA = DEĞER TL"
        # kalıbını yakala.
        # Örn: 1 EUR = 56,1200 TL
        # Baz değer yerine kur karşılığını döndür.
        # Para birimi hardcode edilmez.
        # -------------------------------------------------
        kur_sorusu = bool(
            re.search(
                r"\bkur\b|\bkuru\b|\bkaç tl\b|"
                r"\bkac tl\b|\bkaç lira\b|\bkac lira\b",
                mesaj_norm,
                flags=re.IGNORECASE
            )
        )

        if kur_sorusu:
            kur_kalibi = re.compile(
                r"\b1\s*([A-Z]{3})\s*=\s*"
                r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,4})?"
                r"|\d+(?:[.,]\d+)?)"
                r"\s*(TL|₺|TRY)\b",
                flags=re.IGNORECASE
            )

            for veri in veriler:
                if not isinstance(veri, dict):
                    continue

                metin = " ".join(
                    str(veri.get(alan, "") or "")
                    for alan in ("title", "snippet", "text")
                ).strip()

                eslesme = kur_kalibi.search(metin)

                if eslesme:
                    return (
                        f"{eslesme.group(2)} {eslesme.group(3)}",
                        0.82
                    )


        hedef_birimler = []

        if re.search(
            r"tl|₺|kaç lira|kac lira",
            mesaj_norm,
            flags=re.IGNORECASE
        ):
            hedef_birimler.extend([
                "tl", "₺", "try"
            ])

        if re.search(
            r"usd|dolar",
            mesaj_norm,
            flags=re.IGNORECASE
        ):
            hedef_birimler.extend([
                "usd", "dolar"
            ])

        if re.search(
            r"eur|euro",
            mesaj_norm,
            flags=re.IGNORECASE
        ):
            hedef_birimler.extend([
                "eur", "euro"
            ])

        if re.search(
            r"gbp|sterlin",
            mesaj_norm,
            flags=re.IGNORECASE
        ):
            hedef_birimler.extend([
                "gbp", "sterlin"
            ])

        birim_regex = (
            r"TL|₺|USD|EUR|GBP|TRY|dolar|euro|sterlin|"
            r"altın|gram|kg|%|yüzde"
        )

        sayi_regex = re.compile(
            r"(?<![\w])"
            r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,4})?"
            r"|\d+(?:[.,]\d+)?)"
            r"(?![\w])"
        )

        adaylar = []

        # -------------------------------------------------
        # 3) Her web kaynağındaki sayıları bağlamıyla çıkar.
        # -------------------------------------------------
        for kaynak_no, veri in enumerate(veriler):
            if not isinstance(veri, dict):
                continue

            metin = " ".join(
                str(veri.get(alan, "") or "")
                for alan in (
                    "title",
                    "snippet",
                    "text"
                )
            ).strip()

            if not metin:
                continue

            for eslesme in sayi_regex.finditer(metin):
                deger = eslesme.group(1).strip()

                sol = max(
                    0,
                    eslesme.start() - 100
                )
                sag = min(
                    len(metin),
                    eslesme.end() + 100
                )

                baglam = metin[sol:sag]

                # Sayının hemen sonrasındaki birim.
                sonrasi = metin[
                    eslesme.end():
                    min(len(metin), eslesme.end() + 30)
                ]

                birim_sonrasi = re.match(
                    rf"\s*({birim_regex})\b",
                    sonrasi,
                    flags=re.IGNORECASE
                )

                # Sayının hemen öncesindeki birim.
                oncesi = metin[
                    max(0, eslesme.start() - 30):
                    eslesme.start()
                ]

                birim_oncesi = re.search(
                    rf"({birim_regex})\s*$",
                    oncesi,
                    flags=re.IGNORECASE
                )

                birim = ""

                if birim_sonrasi:
                    birim = birim_sonrasi.group(1)
                elif birim_oncesi:
                    birim = birim_oncesi.group(1)

                yakin_birim = bool(birim)

                adaylar.append({
                    "deger": deger,
                    "kaynak": kaynak_no,
                    "baglam": baglam,
                    "birim": birim,
                    "yakin_birim": yakin_birim,
                    "ondalik": bool(
                        re.search(
                            r"[.,]\d+",
                            deger
                        )
                    ),
                })

        if not adaylar:
            return None, 0.0

        # -------------------------------------------------
        # 4) Aynı değeri kaynaklar arasında grupla.
        # -------------------------------------------------
        gruplar = {}

        for aday in adaylar:
            anahtar = cls.normalize(
                aday["deger"]
            )

            gruplar.setdefault(
                anahtar,
                []
            ).append(aday)

        # -------------------------------------------------
        # 5) Aday puanlama.
        # -------------------------------------------------
        def birim_eslesiyor_mu(birim):
            if not birim or not hedef_birimler:
                return False

            birim_norm = cls.normalize(
                birim
            )

            return any(
                birim_norm == cls.normalize(hedef)
                for hedef in hedef_birimler
            )

        sirali = []

        for deger, grup in gruplar.items():
            kaynak_sayisi = len({
                x["kaynak"]
                for x in grup
            })

            hedef_birim_puani = 0
            yakin_birim_puani = 0
            ondalik_puani = 0
            kur_karsilik_puani = 0

            # Kur/değer sorularında eşitlik ifadesinin
            # karşılığındaki sayıyı önceliklendir.
            kur_sorusu = bool(
                re.search(
                    r"\bkur\b|\bkuru\b|\bkaç tl\b|"
                    r"\bkac tl\b|\bkaç lira\b|\bkac lira\b",
                    mesaj_norm,
                    flags=re.IGNORECASE
                )
            )

            for aday in grup:
                if aday["yakin_birim"]:
                    yakin_birim_puani = max(
                        yakin_birim_puani,
                        2
                    )

                if birim_eslesiyor_mu(
                    aday["birim"]
                ):
                    hedef_birim_puani = max(
                        hedef_birim_puani,
                        10
                    )

                if aday["ondalik"]:
                    ondalik_puani = max(
                        ondalik_puani,
                        1
                    )

                if kur_sorusu and aday["birim"]:
                    baglam_norm = cls.normalize(
                        aday["baglam"]
                    )

                    deger_norm = cls.normalize(
                        aday["deger"]
                    )

                    # "1 USD = 48,4947 TL" gibi ifadelerde
                    # eşitliğin sağındaki/karşılığındaki değeri yakala.
                    if re.search(
                        r"=.{0,80}" + re.escape(deger_norm),
                        baglam_norm,
                        flags=re.IGNORECASE
                    ):
                        kur_karsilik_puani = max(
                            kur_karsilik_puani,
                            20
                        )

            puan = (
                kur_karsilik_puani,
                hedef_birim_puani,
                yakin_birim_puani,
                ondalik_puani,
                kaynak_sayisi,
            )

            sirali.append(
                (puan, deger, grup)
            )

        sirali.sort(
            key=lambda x: x[0],
            reverse=True
        )

        # -------------------------------------------------
        # 6) En güçlü gerçek değeri seç.
        # -------------------------------------------------
        for puan, deger, grup in sirali:
            hedef_birimli = [
                x for x in grup
                if birim_eslesiyor_mu(
                    x["birim"]
                )
            ]

            yakin_birimli = [
                x for x in grup
                if x["yakin_birim"]
            ]

            # Kur sorularında eşitliğin karşılığındaki
            # gerçek değeri, baz birimden önce seç.
            if kur_sorusu and puan[0] >= 20:
                secilen = (
                    hedef_birimli[0]
                    if hedef_birimli
                    else yakin_birimli[0]
                )

            # Kullanıcı belirli bir birim istediyse
            # başka birimin sayısını seçme.
            elif hedef_birimler:
                if not hedef_birimli:
                    continue

                secilen = hedef_birimli[0]
            else:
                if not yakin_birimli:
                    continue

                secilen = yakin_birimli[0]

            kaynak_sayisi = len({
                x["kaynak"]
                for x in grup
            })

            if kaynak_sayisi >= 3:
                guven = 0.90
            elif kaynak_sayisi >= 2:
                guven = 0.82
            else:
                guven = 0.76

            sonuc_degeri = secilen["deger"]
            sonuc_birimi = secilen["birim"]

            if sonuc_birimi:
                return (
                    f"{sonuc_degeri} {sonuc_birimi}",
                    guven
                )

            return (
                sonuc_degeri,
                guven
            )

        # -------------------------------------------------
        # 7) Son güvenli fallback:
        # Birden fazla kaynakta ortak sayı.
        # -------------------------------------------------
        ortak = cls.ortak_sayisal_bilgiler(
            veriler
        )

        for aday in ortak:
            if aday["tekrar"] >= 3:
                return aday["deger"], 0.90

            if aday["tekrar"] >= 2:
                return aday["deger"], 0.78

        return None, 0.0

    @classmethod
    def kaynak_ozeti(cls, veriler):
        """
        Kaynak sayısını ve farklı domainleri hesaplar.
        """
        domainler = {
            veri.get("domain", "")
            for veri in veriler
            if veri.get("domain")
        }

        return {
            "kaynak_sayisi": len(veriler),
            "farkli_domain_sayisi": len(domainler),
        }

    def calistir(
        self,
        mesaj,
        karar=None,
        web_verisi=None,
        mevcut_cevap="",
        sayfa_okuyucu=None,
        web_arayici=None,
    ):
        """
        Merkezi koordinasyon noktası.

        mevcut_cevap doluysa ve zaten çalışan özel bir
        motor tarafından üretilmişse onu bozmaz.

        Web verisi varsa:
          - kaynak isteği varsa kaynak görünümüne izin verir
          - değilse gerçek cevap çıkarmayı dener
          - çıkaramazsa Gemini son çare sinyali üretir
        """
        karar = karar or {}
        mevcut_cevap = str(
            mevcut_cevap or ""
        ).strip()

        veriler = self.temizle_web_verisi(
            web_verisi
        )

        kaynak_ozet = self.kaynak_ozeti(
            veriler
        )

        # 1. Mevcut çalışan özel motor sonucu
        # merkezi motor tarafından değiştirilmez.
        if mevcut_cevap:
            return EagleMerkezSonuc(
                ok=True,
                cevap=mevcut_cevap,
                guven=1.0,
                kaynak_sayisi=(
                    kaynak_ozet["kaynak_sayisi"]
                ),
                gemini_gerekli=False,
                kaynak_goster=False,
                neden="Mevcut özel motor sonucu korundu."
            )

        # 2. Kullanıcı özellikle kaynak istiyorsa
        # üst katman eski kaynak gösterimini kullanabilir.
        if self.kaynak_isteniyor_mu(mesaj):
            return EagleMerkezSonuc(
                ok=False,
                cevap="",
                guven=1.0,
                kaynak_sayisi=(
                    kaynak_ozet["kaynak_sayisi"]
                ),
                gemini_gerekli=False,
                kaynak_goster=True,
                neden="Kullanıcı kaynakları açıkça istedi."
            )

        # 3. Web sonucu yoksa Gemini'ye doğrudan atlama.
        # Önce diğer mevcut motorların sonucu beklenir.
        if not veriler:
            return EagleMerkezSonuc(
                ok=False,
                cevap="",
                guven=0.0,
                kaynak_sayisi=0,
                gemini_gerekli=False,
                kaynak_goster=False,
                neden="Kullanılabilir web verisi yok."
            )

        # 4. Kısa sayısal/güncel cevap adayı.
        if self.deger_sorusu_mu(mesaj):
            cevap, guven = self.net_sayisal_cevap(
                mesaj,
                veriler
            )

            if cevap and guven >= 0.75:
                return EagleMerkezSonuc(
                    ok=True,
                    cevap=cevap,
                    guven=guven,
                    kaynak_sayisi=(
                        kaynak_ozet["kaynak_sayisi"]
                    ),
                    gemini_gerekli=False,
                    kaynak_goster=False,
                    neden=(
                        "Birden fazla web sonucunda "
                        "tekrarlanan sayısal bilgi bulundu."
                    )
                )

            # Snippetlerde gerçek değer yoksa mevcut web sayfa
            # okuyucusunu kullan. Web katmanı burada değiştirilmez.
            if sayfa_okuyucu:
                okunmus_veriler = []

                for veri in veriler[:4]:
                    url = str(
                        veri.get("url", "")
                    ).strip()

                    if not url:
                        continue

                    try:
                        sayfa_metni = sayfa_okuyucu(url)

                        if sayfa_metni:
                            yeni_veri = dict(veri)
                            yeni_veri["text"] = " ".join(
                                x for x in (
                                    veri.get("title", ""),
                                    veri.get("snippet", ""),
                                    sayfa_metni
                                )
                                if x
                            ).strip()

                            okunmus_veriler.append(
                                yeni_veri
                            )
                    except Exception as sayfa_hatasi:
                        print(
                            "⚠️ Merkezi motor sayfa okuma hatası:",
                            sayfa_hatasi
                        )

                if okunmus_veriler:
                    sayfa_kaynak_ozeti = self.kaynak_ozeti(
                        okunmus_veriler
                    )

                    cevap, guven = self.net_sayisal_cevap(
                        mesaj,
                        okunmus_veriler
                    )

                    if cevap and guven >= 0.75:
                        return EagleMerkezSonuc(
                            ok=True,
                            cevap=cevap,
                            guven=guven,
                            kaynak_sayisi=(
                                sayfa_kaynak_ozeti[
                                    "kaynak_sayisi"
                                ]
                            ),
                            gemini_gerekli=False,
                            kaynak_goster=False,
                            neden=(
                                "Arama özetlerinde değer bulunamadı; "
                                "ilgili web sayfaları okunarak cevap "
                                "çıkarıldı."
                            )
                        )

                    # Sayfa içerikleri artık sonraki metin analizinde
                    # de kullanılabilir.
                    veriler = okunmus_veriler
                    kaynak_ozet = sayfa_kaynak_ozeti

        # 5. Metinler birbirine yeterince yakınsa
        # henüz doğal dil sentezi yapmadan mevcut
        # kaynaklardan güvenli aday üretmeye çalışır.
        tekrar_skoru = self.metin_tekrar_skoru(
            veriler
        )

        if tekrar_skoru >= 0.60:
            en_iyi = veriler[0].get("snippet") or \
                veriler[0].get("title")

            if en_iyi:
                return EagleMerkezSonuc(
                    ok=True,
                    cevap=en_iyi.strip(),
                    guven=0.68,
                    kaynak_sayisi=(
                        kaynak_ozet["kaynak_sayisi"]
                    ),
                    gemini_gerekli=False,
                    kaynak_goster=False,
                    neden=(
                        "Birden fazla kaynak benzer "
                        "bilgi verdi; kısa aday çıkarıldı."
                    )
                )

        # 6. Hiçbir güvenli çıkarım yok.
        # Gemini burada devreye GİRECEK değil;
        # yalnızca üst katmana son çare sinyali verilecek.
        return EagleMerkezSonuc(
            ok=False,
            cevap="",
            guven=0.0,
            kaynak_sayisi=(
                kaynak_ozet["kaynak_sayisi"]
            ),
            gemini_gerekli=True,
            kaynak_goster=False,
            neden=(
                "Web verisi var ancak merkezi motor "
                "güvenli net cevap çıkaramadı. "
                "Gemini son çare olarak değerlendirilebilir."
            )
        )


def eagle_merkez_motorunu_kur():
    return EagleMerkezMotoru()
