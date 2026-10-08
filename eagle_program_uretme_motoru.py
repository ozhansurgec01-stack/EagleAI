import os
import re
import ast
import requests

from eagle_kod_analiz_motoru import EagleKodAnalizMotoru
from eagle_uygulama_planlayici import EagleUygulamaPlanlayici
from eagle_genel_uygulama_uretici import EagleGenelUygulamaUretici


class EagleProgramUretmeMotoru:
    """Kullanıcı isteğinden güvenli şekilde program/kod üretir."""

    GEMINI_URL = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-2.5-flash:generateContent"
    )

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")

    def uret(self, mesaj: str):
        mesaj = str(mesaj or "").strip()

        if not mesaj:
            return {
                "ok": False,
                "error": "Program üretimi için istek boş olamaz.",
            }

        # 🦅 EAGLE YEREL KAPSAMLI ÜRETİM
        # Proje / modül / şablon istekleri mevcut basit şablonlardan
        # önce ayrıştırılır.
        kapsamli_sonuc = self._yerel_kapsamli_uret(mesaj)
        if kapsamli_sonuc is not None and kapsamli_sonuc.get("ok"):
            return kapsamli_sonuc

        # 🦅 EAGLE YEREL PROGRAM ÜRETİMİ
        # Basit Python programları Gemini'ye gönderilmeden doğrudan Eagle
        # tarafından üretilir.
        yerel_sonuc = self._yerel_program_uret(mesaj)
        if yerel_sonuc is not None:
            return yerel_sonuc

        return {
            "ok": False,
            "error": (
                "Bu program türü için Eagle'ın yerel üretim şablonu "
                "henüz hazır değil."
            ),
        }

    def _yerel_kapsamli_uret(self, mesaj):
        """Proje, modül ve şablon isteklerini yerel olarak yönlendirir."""
        k = str(mesaj or "").lower().strip()

        proje = any(x in k for x in (
            "proje oluştur", "proje olustur",
            "proje hazırla", "proje hazirla",
            "proje yaz", "proje geliştir", "proje gelistir",
            "projesi oluştur", "projesi olustur",
        ))

        modul = any(x in k for x in (
            "modül oluştur", "modul olustur",
            "modül hazırla", "modul hazirla",
            "modül yaz", "modul yaz",
            "modülü oluştur", "modulu olustur",
            "modülü hazırla", "modulu hazirla",
            "modülü yaz", "modulu yaz",
        ))

        sablon = any(x in k for x in (
            "şablon oluştur", "sablon olustur",
            "şablon hazırla", "sablon hazirla",
            "şablon yaz", "sablon yaz",
            "şablonu oluştur", "sablonu olustur",
            "şablonu hazırla", "sablonu hazirla",
            "şablonu yaz", "sablonu yaz",
        ))

        if not (proje or modul or sablon):
            uygulama_planlayici = EagleUygulamaPlanlayici()
            uygulama_plani = uygulama_planlayici.planla(mesaj)

            if uygulama_plani is not None:
                uygulama_uretici = EagleGenelUygulamaUretici()
                uygulama_sonucu = uygulama_uretici.uret(uygulama_plani)

                if uygulama_sonucu is not None:
                    return uygulama_sonucu

            return None

        if proje:
            cikti_turu = "proje"
        elif modul:
            cikti_turu = "modul"
        else:
            cikti_turu = "sablon"

        konu = self._konu_adi_cikar(mesaj)

        if cikti_turu == "modul":
            return self._yerel_modul_sonucu(konu)

        uygulama_planlayici = EagleUygulamaPlanlayici()
        uygulama_plani = uygulama_planlayici.planla(
            mesaj,
            konu=konu,
            cikti_turu=cikti_turu,
        )

        if uygulama_plani is not None:
            uygulama_uretici = EagleGenelUygulamaUretici()
            uygulama_sonucu = uygulama_uretici.uret(uygulama_plani)

            if uygulama_sonucu is not None:
                return uygulama_sonucu

        return self._yerel_proje_sonucu(konu, cikti_turu)

    @staticmethod
    def _konu_adi_cikar(mesaj):
        """Kullanıcı isteğinden üretilecek programın konusunu çıkarır."""
        k = str(mesaj or "").strip()

        kaliplar = (
            r"(.+?)\s+(?:projesi|proje)\s+(?:oluştur|olustur|hazırla|hazirla|yaz|geliştir|gelistir)",
            r"(.+?)\s+(?:modülü|modulu|modül|modul)\s+(?:oluştur|olustur|hazırla|hazirla|yaz)",
            r"(.+?)\s+(?:şablonu|sablonu|şablon|sablon)\s+(?:oluştur|olustur|hazırla|hazirla|yaz)",
        )

        for kalip in kaliplar:
            eslesme = re.search(kalip, k, re.IGNORECASE)
            if eslesme:
                konu = eslesme.group(1).strip(" .,:;!?")
                if konu:
                    return konu

        return "genel uygulama"

    @staticmethod
    def _yerel_modul_sonucu(konu):
        """Konuya uygun import edilebilir yerel Python modülü üretir."""
        alanlar = EagleProgramUretmeMotoru._konu_anahtarlarini_bul(konu)
        alan = alanlar[0]

        bilesenler = EagleProgramUretmeMotoru._alan_bilesenleri_uret(
            alan,
            konu,
        )

        # Modül tek dosya olacağı için alan bileşenleri aynı dosyada
        # birleştirilir. Böylece modül gerçekten konuya özgü işlev taşır.
        parcalar = [
            f'"""Yerel olarak üretilen {konu} modülü."""',
            "",
        ]

        for dosya_adi, icerik in bilesenler.items():
            parcalar.append(f"# --- {dosya_adi} ---")
            parcalar.append(icerik.strip())
            parcalar.append("")

        kod = "\n".join(parcalar).rstrip() + "\n"

        syntax_ok, syntax_hatasi = (
            EagleProgramUretmeMotoru._python_kontrol(kod)
        )

        return {
            "ok": True,
            "kod": kod,
            "dil": "python",
            "aciklama": (
                f"{konu} için import edilebilir "
                f"{alan} Python modülü hazırlandı."
            ),
            "syntax_ok": syntax_ok,
            "analiz": [],
            "cikti_turu": "modul",
            "proje_adi": konu,
            "ana_dosya": "modul.py",
            "dosyalar": {
                "modul.py": kod,
            },
            "syntax_hatalari": {
                "modul.py": syntax_hatasi,
            } if not syntax_ok else {},
        }

    @staticmethod
    def _konu_anahtarlarini_bul(konu):
        """Konu için yerel üretim alanını belirler."""
        k = str(konu or "").lower()

        alanlar = (
            (
                "hesap_makinesi",
                ("hesap makinesi", "hesaplama", "calculator"),
            ),
            (
                "stok",
                ("stok", "envanter", "ürün takip", "urun takip"),
            ),
            (
                "not",
                ("not uygulaması", "not uygulamasi", "not sistemi", "not takip"),
            ),
            (
                "haber",
                ("haber", "news"),
            ),
            (
                "api_istemcisi",
                ("api istemcisi", "api client", "istemci", "http istemcisi"),
            ),
        )

        bulunan = []
        for alan, anahtarlar in alanlar:
            if any(anahtar in k for anahtar in anahtarlar):
                bulunan.append(alan)

        return bulunan or ["genel"]

    @staticmethod
    def _alan_bilesenleri_uret(alan, konu):
        """Seçilen alan için proje bileşenlerini üretir."""
        if alan == "hesap_makinesi":
            return {
                "model.py": (
                    f'""" {konu} veri ve doğrulama modeli. """\n\n'
                    "class Islem:\n"
                    "    def __init__(self, sayi1, operator, sayi2):\n"
                    "        self.sayi1 = float(sayi1)\n"
                    "        self.operator = operator\n"
                    "        self.sayi2 = float(sayi2)\n"
                ),
                "service.py": (
                    f'""" {konu} işlem servisi. """\n\n'
                    "def hesapla(sayi1, operator, sayi2):\n"
                    "    sayi1 = float(sayi1)\n"
                    "    sayi2 = float(sayi2)\n"
                    "    if operator == '+':\n"
                    "        return sayi1 + sayi2\n"
                    "    if operator == '-':\n"
                    "        return sayi1 - sayi2\n"
                    "    if operator == '*':\n"
                    "        return sayi1 * sayi2\n"
                    "    if operator == '/':\n"
                    "        if sayi2 == 0:\n"
                    "            raise ValueError('Sıfıra bölme yapılamaz.')\n"
                    "        return sayi1 / sayi2\n"
                    "    raise ValueError('Geçersiz işlem.')\n"
                ),
            }

        if alan == "stok":
            return {
                "model.py": (
                    f'""" {konu} ürün modeli. """\n\n'
                    "class Urun:\n"
                    "    def __init__(self, ad, miktar=0, fiyat=0):\n"
                    "        self.ad = str(ad)\n"
                    "        self.miktar = int(miktar)\n"
                    "        self.fiyat = float(fiyat)\n"
                ),
                "service.py": (
                    f'""" {konu} stok servisi. """\n\n'
                    "class StokServisi:\n"
                    "    def __init__(self):\n"
                    "        self.urunler = {}\n\n"
                    "    def ekle(self, urun):\n"
                    "        self.urunler[urun.ad] = urun\n\n"
                    "    def sil(self, ad):\n"
                    "        return self.urunler.pop(ad, None)\n\n"
                    "    def getir(self, ad):\n"
                    "        return self.urunler.get(ad)\n\n"
                    "    def listele(self):\n"
                    "        return list(self.urunler.values())\n"
                ),
            }

        if alan == "not":
            return {
                "model.py": (
                    f'""" {konu} not modeli. """\n\n'
                    "class Not:\n"
                    "    def __init__(self, baslik, icerik):\n"
                    "        self.baslik = str(baslik)\n"
                    "        self.icerik = str(icerik)\n"
                ),
                "service.py": (
                    f'""" {konu} not servisi. """\n\n'
                    "class NotServisi:\n"
                    "    def __init__(self):\n"
                    "        self.notlar = []\n\n"
                    "    def ekle(self, not_objesi):\n"
                    "        self.notlar.append(not_objesi)\n"
                    "        return not_objesi\n\n"
                    "    def listele(self):\n"
                    "        return list(self.notlar)\n\n"
                    "    def sil(self, sira):\n"
                    "        return self.notlar.pop(sira)\n\n"
                    "    def guncelle(self, sira, baslik, icerik):\n"
                    "        not_objesi = self.notlar[sira]\n"
                    "        not_objesi.baslik = str(baslik)\n"
                    "        not_objesi.icerik = str(icerik)\n"
                    "        return not_objesi\n"
                ),
            }

        if alan == "haber":
            return {
                "model.py": (
                    f'""" {konu} haber modeli. """\n\n'
                    "class Haber:\n"
                    "    def __init__(self, baslik, kategori='', tarih=''):\n"
                    "        self.baslik = str(baslik)\n"
                    "        self.kategori = str(kategori)\n"
                    "        self.tarih = str(tarih)\n"
                ),
                "service.py": (
                    f'""" {konu} haber servisi. """\n\n'
                    "class HaberServisi:\n"
                    "    def __init__(self, haberler=None):\n"
                    "        self.haberler = list(haberler or [])\n\n"
                    "    def listele(self):\n"
                    "        return list(self.haberler)\n\n"
                    "    def ara(self, kelime):\n"
                    "        kelime = str(kelime).lower()\n"
                    "        return [\n"
                    "            haber for haber in self.haberler\n"
                    "            if kelime in haber.baslik.lower()\n"
                    "        ]\n\n"
                    "    def kategoriye_gore(self, kategori):\n"
                    "        kategori = str(kategori).lower()\n"
                    "        return [\n"
                    "            haber for haber in self.haberler\n"
                    "            if haber.kategori.lower() == kategori\n"
                    "        ]\n"
                ),
            }

        if alan == "api_istemcisi":
            return {
                "client.py": (
                    f'""" {konu} HTTP istemcisi. """\n\n'
                    "import requests\n\n\n"
                    "class ApiClientError(Exception):\n"
                    "    pass\n\n\n"
                    "class ApiClient:\n"
                    "    def __init__(self, base_url, timeout=10):\n"
                    "        self.base_url = str(base_url).rstrip('/')\n"
                    "        self.timeout = timeout\n\n"
                    "    def get(self, path, **kwargs):\n"
                    "        url = self.base_url + '/' + str(path).lstrip('/')\n"
                    "        try:\n"
                    "            response = requests.get(\n"
                    "                url, timeout=self.timeout, **kwargs\n"
                    "            )\n"
                    "            response.raise_for_status()\n"
                    "            return response\n"
                    "        except requests.RequestException as exc:\n"
                    "            raise ApiClientError(str(exc)) from exc\n"
                ),
            }

        return {
            "service.py": (
                f'""" {konu} genel uygulama servisi. """\n\n'
                "class UygulamaServisi:\n"
                "    def calistir(self, veri=None):\n"
                "        return veri\n"
            ),
        }

    @staticmethod
    def _alan_testi_uret(alan, paket):
        """Üretilen alan bileşenleri için temel testleri üretir."""
        if alan == "hesap_makinesi":
            return (
                f"from src.{paket}.service import hesapla\n\n\n"
                "def test_toplama():\n"
                "    assert hesapla(2, '+', 3) == 5\n\n\n"
                "def test_bolme_sifir():\n"
                "    try:\n"
                "        hesapla(4, '/', 0)\n"
                "    except ValueError:\n"
                "        return\n"
                "    assert False\n"
            )

        if alan == "stok":
            return (
                f"from src.{paket}.model import Urun\n"
                f"from src.{paket}.service import StokServisi\n\n\n"
                "def test_stok_ekle_getir():\n"
                "    servis = StokServisi()\n"
                "    urun = Urun('Kalem', 10, 5)\n"
                "    servis.ekle(urun)\n"
                "    assert servis.getir('Kalem') is urun\n"
            )

        if alan == "not":
            return (
                f"from src.{paket}.model import Not\n"
                f"from src.{paket}.service import NotServisi\n\n\n"
                "def test_not_ekle():\n"
                "    servis = NotServisi()\n"
                "    servis.ekle(Not('Başlık', 'İçerik'))\n"
                "    assert len(servis.listele()) == 1\n"
            )

        if alan == "haber":
            return (
                f"from src.{paket}.model import Haber\n"
                f"from src.{paket}.service import HaberServisi\n\n\n"
                "def test_haber_arama():\n"
                "    servis = HaberServisi([Haber('Teknoloji haberi')])\n"
                "    assert len(servis.ara('teknoloji')) == 1\n"
            )

        if alan == "api_istemcisi":
            return (
                f"from src.{paket}.client import ApiClient\n\n\n"
                "def test_client():\n"
                "    client = ApiClient('https://example.com')\n"
                "    assert client.base_url == 'https://example.com'\n"
            )

        return (
            f"from src.{paket}.service import UygulamaServisi\n\n\n"
            "def test_servis():\n"
            "    assert UygulamaServisi().calistir('ok') == 'ok'\n"
        )

    @staticmethod
    def _yerel_proje_sonucu(konu, cikti_turu):
        """Konuya uygun genel yerel proje iskeleti üretir."""
        paket = (
            re.sub(r"[^a-zA-Z0-9]", "_", konu.lower()).strip("_")
            or "uygulama"
        )

        alanlar = EagleProgramUretmeMotoru._konu_anahtarlarini_bul(konu)
        alan = alanlar[0]

        bilesenler = EagleProgramUretmeMotoru._alan_bilesenleri_uret(
            alan,
            konu,
        )

        app_import = "service"
        if alan == "api_istemcisi":
            app_import = "client"

        if cikti_turu == "sablon":
            app = (
                '"""Yeniden kullanılabilir uygulama şablonu."""\n\n'
                f"from src.{paket}.{app_import} import *\n\n\n"
                "def main():\n"
                f'    print("{konu} şablonu hazır.")\n'
                "    print('Bu giriş noktasını kendi uygulama akışına göre genişlet.')\n\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            )
        else:
            app = (
                '"""Uygulama giriş noktası."""\n\n'
                f"from src.{paket}.{app_import} import *\n\n\n"
                "def main():\n"
                f'    print("{konu} hazır.")\n\n\n'
                "if __name__ == '__main__':\n"
                "    main()\n"
            )

        init = f'""" {konu} paketi. """\n'

        dosyalar = {
            "app.py": app,
            f"src/{paket}/__init__.py": init,
        }

        for dosya_adi, icerik in bilesenler.items():
            dosyalar[f"src/{paket}/{dosya_adi}"] = icerik

        test_kodu = EagleProgramUretmeMotoru._alan_testi_uret(alan, paket)
        dosyalar["tests/test_core.py"] = test_kodu

        if cikti_turu == "sablon":
            readme = (
                f"# {konu.title()} Şablonu\n\n"
                f"EagleAI tarafından yerel olarak oluşturulan "
                f"yeniden kullanılabilir {konu} Python şablonudur.\n\n"
                f"**Üretim alanı:** `{alan}`\n\n"
                "## Yapı\n\n"
                "- `app.py`: başlangıç/giriş noktası\n"
                "- `src/`: alan modeli ve servisleri\n"
                "- `tests/`: temel testler\n"
                "- `requirements.txt`: bağımlılıklar\n\n"
                "## Kullanım\n\n"
                "Bu yapıyı temel alarak uygulamanın kendi iş akışını "
                "ve kullanıcı arayüzünü genişletebilirsin.\n"
            )
        else:
            readme = (
                f"# {konu.title()}\n\n"
                f"Bu proje EagleAI tarafından yerel olarak oluşturulan "
                f"{cikti_turu} iskeletidir.\n\n"
                f"**Üretim alanı:** `{alan}`\n\n"
                "## Bileşenler\n\n"
                "- Uygulama giriş noktası\n"
                "- Alan modeli/servisi\n"
                "- Testler\n"
            )

        requirements = "requests\n" if alan == "api_istemcisi" else ""

        dosyalar["README.md"] = readme
        dosyalar["requirements.txt"] = requirements

        syntax_hatalari = {}
        syntax_ok = True

        for yol, kod in dosyalar.items():
            if not yol.endswith(".py"):
                continue

            dosya_ok, dosya_hatasi = (
                EagleProgramUretmeMotoru._python_kontrol(kod)
            )

            if not dosya_ok:
                syntax_ok = False
                syntax_hatalari[yol] = dosya_hatasi

        return {
            "ok": True,
            "kod": app,
            "dil": "python",
            "aciklama": (
                f"{konu} için yerel {cikti_turu} proje iskeleti hazırlandı. "
                f"{len(dosyalar)} dosya oluşturuldu. "
                f"Üretim alanı: {alan}."
            ),
            "syntax_ok": syntax_ok,
            "analiz": [],
            "cikti_turu": cikti_turu,
            "proje_adi": konu,
            "ana_dosya": "app.py",
            "dosyalar": dosyalar,
            "syntax_hatalari": syntax_hatalari,
        }

    def _prompt_olustur(self, mesaj):
        return (
            "Sen EagleAI'nin program üretim motorusun.\n"
            "Kullanıcının istediği programı üret.\n\n"
            "Kurallar:\n"
            "1. Kullanıcının istediği programlama dilini kullan.\n"
            "2. Kodu tek ve eksiksiz bir kod bloğu içinde ver.\n"
            "3. Koddan önce kısa ve doğal bir giriş cümlesi yaz.\n"
            "4. Koddan sonra kısa bir açıklama yaz; kodun ne yaptığını ve önemli bölümlerini anlaşılır şekilde anlat.\n"
            "5. Gereksiz uzun açıklamalar, tekrarlar veya konu dışı bilgiler ekleme.\n"
            "6. Çalıştırılabilir ve düzenli kod üretmeye çalış.\n"
            "7. Kod bloğunun dil etiketini doğru belirt.\n\n"
            f"KULLANICI İSTEĞİ:\n{mesaj}"
        )

    @staticmethod
    def _gemini_metin(data):
        adaylar = data.get("candidates", [])

        if not adaylar:
            return ""

        content = adaylar[0].get("content", {})
        parts = content.get("parts", [])

        return " ".join(
            str(part.get("text", "")).strip()
            for part in parts
            if isinstance(part, dict) and part.get("text")
        ).strip()

    @staticmethod
    def _program_aciklamasi(metin):
        parcalar = re.split(
            r"```[A-Za-z0-9_+#.-]*\s*\n.*?```",
            metin,
            flags=re.DOTALL,
        )
        aciklama = " ".join(
            parca.strip() for parca in parcalar if parca.strip()
        ).strip()
        return aciklama

    @staticmethod
    def _kodu_ayikla(metin):
        eslesme = re.search(
            r"```([A-Za-z0-9_+#.-]*)\s*\n(.*?)```",
            metin,
            re.DOTALL,
        )

        if eslesme:
            etiket = eslesme.group(1).strip().lower()
            kod = eslesme.group(2).strip()
        else:
            etiket = ""
            kod = metin.strip()

        dil_eslemesi = {
            "py": "python",
            "python": "python",
            "python3": "python",
            "js": "javascript",
            "javascript": "javascript",
            "ts": "typescript",
            "typescript": "typescript",
            "java": "java",
            "c": "c",
            "cpp": "cpp",
            "c++": "cpp",
            "cs": "csharp",
            "csharp": "csharp",
            "kotlin": "kotlin",
            "php": "php",
            "go": "go",
            "rust": "rust",
        }

        dil = dil_eslemesi.get(etiket, etiket or "bilinmiyor")
        return kod, dil

    @staticmethod
    def _yerel_program_uret(mesaj):
        """
        Basit Python programlarını Eagle'ın kendi kurallarıyla üretir.
        Gemini veya internet gerektirmez.
        Tanınmayan isteklerde None döndürür.
        """
        k = mesaj.lower().replace("\u0307", "").strip()

        if "haber" in k and any(x in k for x in (
            "program", "oluştur", "olustur", "yaz", "yap",
            "geliştir", "gelistir"
        )):
            kod = """haberler = [
    {"baslik": "Yapay zeka alanında yeni gelişmeler",
     "kategori": "Teknoloji", "tarih": "2026-09-24"},
    {"baslik": "Bilim dünyasından güncel gelişmeler",
     "kategori": "Bilim", "tarih": "2026-09-23"},
    {"baslik": "Spor dünyasından son haberler",
     "kategori": "Spor", "tarih": "2026-09-22"},
]


def haberleri_listele(liste):
    if not liste:
        print("\\nHaber bulunamadı.")
        return

    print("\\n--- HABERLER ---")
    for i, haber in enumerate(liste, 1):
        print(
            f"{i}. [{haber['kategori']}] "
            f"{haber['baslik']} - {haber['tarih']}"
        )


def kategori_filtrele(liste):
    kategori = input("Kategori adı: ").strip().lower()
    sonuc = [
        haber for haber in liste
        if haber["kategori"].lower() == kategori
    ]
    haberleri_listele(sonuc)


def haber_ara(liste):
    arama = input("Aranacak kelime: ").strip().lower()
    sonuc = [
        haber for haber in liste
        if arama in haber["baslik"].lower()
    ]
    haberleri_listele(sonuc)


def tarihe_gore_sirala(liste):
    sirali = sorted(
        liste,
        key=lambda haber: haber["tarih"],
        reverse=True,
    )
    haberleri_listele(sirali)


def main():
    while True:
        print("\\n=== EAGLE HABER PROGRAMI ===")
        print("1 - Tüm haberleri göster")
        print("2 - Kategoriye göre filtrele")
        print("3 - Haber ara")
        print("4 - Tarihe göre sırala")
        print("5 - Kategorileri göster")
        print("0 - Çıkış")

        secim = input("Seçiminiz: ").strip()

        if secim == "1":
            haberleri_listele(haberler)
        elif secim == "2":
            kategori_filtrele(haberler)
        elif secim == "3":
            haber_ara(haberler)
        elif secim == "4":
            tarihe_gore_sirala(haberler)
        elif secim == "5":
            kategoriler = sorted({
                haber["kategori"] for haber in haberler
            })
            print("\\nKategoriler:")
            for kategori in kategoriler:
                print("-", kategori)
        elif secim == "0":
            print("Program kapatıldı.")
            break
        else:
            print("Geçersiz seçim.")


if __name__ == "__main__":
    main()
"""
            syntax_ok, syntax_hatasi = (
                EagleProgramUretmeMotoru._python_kontrol(kod)
            )

            sonuc = {
                "ok": syntax_ok,
                "kod": kod,
                "dil": "python",
                "aciklama": (
                    "Tabii! Haber programını Eagle'ın yerel üretim "
                    "motoruyla hazırladım. Haberleri listeleyebilir, "
                    "kategoriye göre filtreleyebilir, arayabilir ve "
                    "tarihe göre sıralayabilirsin."
                ),
                "syntax_ok": syntax_ok,
                "analiz": [],
            }

            if not syntax_ok:
                sonuc["syntax_hatasi"] = syntax_hatasi
            else:
                sonuc["analiz"] = EagleKodAnalizMotoru().analiz_et(kod)

            return sonuc

        if (
            "merhaba dünya" in k
            or "merhaba dunya" in k
        ) and any(x in k for x in (
            "ekrana",
            "yazdır",
            "yazdir",
            "print",
            "program"
        )):
            kod = 'print("Merhaba Dünya")'

            syntax_ok, syntax_hatasi = (
                EagleProgramUretmeMotoru._python_kontrol(kod)
            )

            sonuc = {
                "ok": syntax_ok,
                "kod": kod,
                "dil": "python",
                "aciklama": (
                    "Tabii! İstediğin basit Python programını hazırladım. "
                    'Bu kod, print() fonksiyonuyla "Merhaba Dünya" '
                    "yazısını ekrana çıkarır."
                ),
                "syntax_ok": syntax_ok,
                "analiz": [],
            }

            if not syntax_ok:
                sonuc["syntax_hatasi"] = syntax_hatasi
            else:
                sonuc["analiz"] = (
                    EagleKodAnalizMotoru().analiz_et(kod)
                )

            return sonuc

        if (
            ("iki sayı" in k or "iki sayının" in k)
            and any(x in k for x in (
                "toplam", "fark", "çarp", "carp", "böl", "bol"
            ))
        ):
            kod = """sayi1 = float(input("Birinci sayıyı girin: "))
sayi2 = float(input("İkinci sayıyı girin: "))

print("Toplam:", sayi1 + sayi2)
print("Fark:", sayi1 - sayi2)
print("Çarpım:", sayi1 * sayi2)

if sayi2 != 0:
    print("Bölüm:", sayi1 / sayi2)
else:
    print("Bölüm: Tanımsız (ikinci sayı 0 olamaz).")
"""

            syntax_ok, syntax_hatasi = (
                EagleProgramUretmeMotoru._python_kontrol(kod)
            )

            sonuc = {
                "ok": syntax_ok,
                "kod": kod,
                "dil": "python",
                "aciklama": (
                    "Tabii! İki sayı alan ve toplam, fark, çarpım "
                    "ve bölüm sonuçlarını hesaplayan Python programını "
                    "Eagle'ın yerel üretim motoruyla hazırladım."
                ),
                "syntax_ok": syntax_ok,
                "analiz": [],
            }

            if not syntax_ok:
                sonuc["syntax_hatasi"] = syntax_hatasi
            else:
                sonuc["analiz"] = (
                    EagleKodAnalizMotoru().analiz_et(kod)
                )

            return sonuc

        def sonuc_olustur(kod, aciklama):
            syntax_ok, syntax_hatasi = (
                EagleProgramUretmeMotoru._python_kontrol(kod)
            )

            sonuc = {
                "ok": syntax_ok,
                "kod": kod,
                "dil": "python",
                "aciklama": aciklama,
                "syntax_ok": syntax_ok,
                "analiz": [],
            }

            if not syntax_ok:
                sonuc["syntax_hatasi"] = syntax_hatasi
            else:
                sonuc["analiz"] = (
                    EagleKodAnalizMotoru().analiz_et(kod)
                )

            return sonuc

        # Sayıların ortalaması
        if "ortalama" in k and "liste" not in k and "not" not in k:
            kod = """sayilar = input("Sayıları boşlukla ayırın: ").split()
sayilar = [float(sayi) for sayi in sayilar]

if sayilar:
    print("Ortalama:", sum(sayilar) / len(sayilar))
else:
    print("En az bir sayı girilmelidir.")
"""
            return sonuc_olustur(
                kod,
                "Sayıların ortalamasını hesaplayan Python programını hazırladım."
            )

        # Tek / çift
        if "tek" in k and "çift" in k:
            kod = """sayi = int(input("Bir sayı girin: "))

if sayi % 2 == 0:
    print("Çift sayı.")
else:
    print("Tek sayı.")
"""
            return sonuc_olustur(
                kod,
                "Girilen sayının tek mi çift mi olduğunu kontrol eden programı hazırladım."
            )

        # Faktöriyel
        if "faktöriyel" in k or "faktoriyel" in k:
            kod = """sayi = int(input("Bir sayı girin: "))

if sayi < 0:
    print("Negatif sayıların faktöriyeli tanımlı değildir.")
else:
    faktoriyel = 1
    for i in range(2, sayi + 1):
        faktoriyel *= i
    print("Faktöriyel:", faktoriyel)
"""
            return sonuc_olustur(
                kod,
                "Girilen sayının faktöriyelini hesaplayan Python programını hazırladım."
            )

        # Asal sayı
        if "asal" in k and "sayı" in k:
            kod = """sayi = int(input("Bir sayı girin: "))

if sayi < 2:
    print("Asal değil.")
else:
    asal = True
    for i in range(2, int(sayi ** 0.5) + 1):
        if sayi % i == 0:
            asal = False
            break

    print("Asal sayı." if asal else "Asal değil.")
"""
            return sonuc_olustur(
                kod,
                "Girilen sayının asal olup olmadığını kontrol eden programı hazırladım."
            )

        # En büyük / en küçük
        if (
            ("en büyük" in k or "en buyuk" in k)
            and ("en küçük" in k or "en kucuk" in k)
        ):
            kod = """sayilar = [float(x) for x in input("Sayıları boşlukla ayırın: ").split()]

if sayilar:
    print("En büyük:", max(sayilar))
    print("En küçük:", min(sayilar))
else:
    print("En az bir sayı girilmelidir.")
"""
            return sonuc_olustur(
                kod,
                "Sayılar arasındaki en büyük ve en küçük değeri bulan programı hazırladım."
            )

        # Not ortalaması / geçme
        if (
            ("not ortalaması" in k or "not ortalamasi" in k)
            or (("geçme" in k or "gecme" in k) and "not" in k)
        ):
            kod = """notlar = [
    float(input(f"{i}. notu girin: "))
    for i in range(1, 4)
]

ortalama = sum(notlar) / len(notlar)

print("Ortalama:", ortalama)
print("Durum:", "Geçti" if ortalama >= 50 else "Kaldı")
"""
            return sonuc_olustur(
                kod,
                "Üç notun ortalamasını ve geçme durumunu hesaplayan programı hazırladım."
            )

        # Hesap makinesi
        if "hesap makinesi" in k:
            kod = """sayi1 = float(input("Birinci sayıyı girin: "))
islem = input("İşlem (+, -, *, /): ").strip()
sayi2 = float(input("İkinci sayıyı girin: "))

if islem == "+":
    sonuc = sayi1 + sayi2
elif islem == "-":
    sonuc = sayi1 - sayi2
elif islem == "*":
    sonuc = sayi1 * sayi2
elif islem == "/":
    if sayi2 == 0:
        print("Hata: Sıfıra bölme yapılamaz.")
        sonuc = None
    else:
        sonuc = sayi1 / sayi2
else:
    print("Geçersiz işlem.")
    sonuc = None

if sonuc is not None:
    print("Sonuç:", sonuc)
"""
            return sonuc_olustur(
                kod,
                "Dört temel işlemi destekleyen basit bir hesap makinesi hazırladım."
            )

        # Liste toplamı / ortalaması
        if (
            "liste" in k
            and ("toplam" in k or "ortalama" in k)
        ):
            kod = """sayilar = [
    float(x)
    for x in input("Sayıları boşlukla ayırın: ").split()
]

if sayilar:
    print("Toplam:", sum(sayilar))
    print("Ortalama:", sum(sayilar) / len(sayilar))
else:
    print("Liste boş.")
"""
            return sonuc_olustur(
                kod,
                "Listedeki sayıların toplamını ve ortalamasını hesaplayan programı hazırladım."
            )

        # Kelime / karakter sayacı
        if "kelime say" in k or "karakter say" in k:
            kod = """metin = input("Bir metin girin: ")

print("Karakter sayısı:", len(metin))
print("Kelime sayısı:", len(metin.split()))
"""
            return sonuc_olustur(
                kod,
                "Metnin kelime ve karakter sayısını hesaplayan programı hazırladım."
            )

        # Kare / küp
        if (
            "kare" in k
            and ("küp" in k or "kup" in k)
        ):
            kod = """sayi = float(input("Bir sayı girin: "))

print("Karesi:", sayi ** 2)
print("Küpü:", sayi ** 3)
"""
            return sonuc_olustur(
                kod,
                "Girilen sayının karesini ve küpünü hesaplayan programı hazırladım."
            )

        return EagleProgramUretmeMotoru._genel_python_uret(mesaj)

    @staticmethod
    def _genel_python_uret(mesaj):
        """Genel Python istekleri için güvenli yerel üretim."""
        metin = str(mesaj or "").strip()
        k = metin.lower().replace("\u0307", "")

        # Genel Python üretim isteğini doğal dildeki teknik ipuçlarından anla.
        ast_analiz = any(x in k for x in (
            "ast ile", "ast kullan", "abstract syntax tree",
            "python dosyalarını analiz", "py dosyalarını analiz",
            "dosyaları recursive", "recursive olarak tara",
            "klasörü recursive", "klasoru recursive",
        ))
        json_cikti = "json" in k
        cli_path = "--path" in k or "komut satırından" in k
        complexity = "cyclomatic" in k or "complexity" in k
        fonksiyon_sinif = (
            "fonksiyon" in k or "sınıf" in k or "sinif" in k
            or "import" in k
        )

        if not (ast_analiz and (json_cikti or cli_path or complexity or fonksiyon_sinif)):
            return None

        kod = r"""#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path


def cyclomatic_complexity(node: ast.AST) -> int:
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While,
                              ast.IfExp, ast.comprehension)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += max(0, len(child.values) - 1)
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, (ast.Assert,)):
            complexity += 1
    return complexity


def analyze_function(node: ast.AST) -> dict:
    name = getattr(node, "name", "<anonymous>")
    complexity = cyclomatic_complexity(node)
    lines = getattr(node, "end_lineno", getattr(node, "lineno", 1)) - getattr(
        node, "lineno", 1
    ) + 1
    return {
        "name": name,
        "line": getattr(node, "lineno", None),
        "lines": lines,
        "cyclomatic_complexity": complexity,
    }


def analyze_file(path: Path) -> dict:
    result = {
        "file": str(path),
        "functions": 0,
        "classes": 0,
        "imports": 0,
        "longest_function": None,
        "cyclomatic_complexity": 1,
        "error": None,
    }

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))

        functions = [
            node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        classes = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        ]
        imports = [
            node for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]

        result["functions"] = len(functions)
        result["classes"] = len(classes)
        result["imports"] = len(imports)

        function_info = [analyze_function(node) for node in functions]
        if function_info:
            result["longest_function"] = max(
                function_info, key=lambda item: item["lines"]
            )

        result["cyclomatic_complexity"] = sum(
            item["cyclomatic_complexity"] for item in function_info
        ) or 1

    except (OSError, UnicodeError, SyntaxError) as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    return result


def scan_directory(root: Path) -> list[dict]:
    results = []
    for path in sorted(root.rglob("*.py")):
        if path.is_file():
            results.append(analyze_file(path))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recursive Python AST analysis tool"
    )
    parser.add_argument(
        "--path",
        required=True,
        type=Path,
        help="Python dosyalarının bulunduğu klasör",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ast_analysis.json"),
        help="JSON çıktı dosyası",
    )
    args = parser.parse_args()

    root = args.path.expanduser().resolve()

    if not root.exists():
        raise SystemExit(f"Klasör bulunamadı: {root}")
    if not root.is_dir():
        raise SystemExit(f"Klasör değil: {root}")

    results = scan_directory(root)

    output = {
        "path": str(root),
        "file_count": len(results),
        "files": results,
    }

    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
"""

        try:
            ast.parse(kod)
        except SyntaxError as exc:
            return {
                "ok": False,
                "error": f"Üretilen Python kodunda sözdizimi hatası: {exc}",
            }

        return {
            "ok": True,
            "dil": "python",
            "kod": kod,
            "ana_dosya": "python_ast_analyzer.py",
            "cikti_turu": "python_kodu",
            "aciklama": (
                "Klasörü recursive tarayan, Python dosyalarını AST ile analiz eden, "
                "fonksiyon/sınıf/import sayılarını, en uzun fonksiyonu ve "
                "cyclomatic complexity tahminini JSON olarak çıkaran araç."
            ),
        }


    @staticmethod
    def _python_kontrol(kod):
        try:
            ast.parse(kod)
            return True, ""
        except SyntaxError as exc:
            return False, (
                f"{exc.msg} "
                f"(satır {exc.lineno})"
                if exc.lineno
                else exc.msg
            )
