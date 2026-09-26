import os
import re
import ast
import requests

from eagle_kod_analiz_motoru import EagleKodAnalizMotoru


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
        k = mesaj.lower().strip()

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
            "print"
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
            "iki sayı" in k
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

        return None

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
