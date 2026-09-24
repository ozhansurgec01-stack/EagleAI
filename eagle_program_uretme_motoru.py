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

        if not self.gemini_key:
            return {
                "ok": False,
                "error": "GEMINI_API_KEY bulunamadı.",
            }

        prompt = self._prompt_olustur(mesaj)

        try:
            response = requests.post(
                self.GEMINI_URL,
                params={"key": self.gemini_key},
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ]
                },
                timeout=30,
            )
        except Exception as exc:
            return {
                "ok": False,
                "error": f"Program üretim bağlantı hatası: {exc}",
            }

        if not response.ok:
            return {
                "ok": False,
                "error": (
                    f"Program üretim servisi HTTP {response.status_code} "
                    "döndürdü."
                ),
            }

        try:
            data = response.json()
        except Exception:
            return {
                "ok": False,
                "error": "Program üretim servisi geçersiz JSON döndürdü.",
            }

        metin = self._gemini_metin(data)

        if not metin:
            return {
                "ok": False,
                "error": "Program üretim servisi boş cevap döndürdü.",
            }

        kod, dil = self._kodu_ayikla(metin)

        aciklama = self._program_aciklamasi(metin)

        if not kod:
            return {
                "ok": False,
                "error": "Üretilen cevapta kod bulunamadı.",
                "ham_cevap": metin,
            }

        sonuc = {
            "ok": True,
            "kod": kod,
            "dil": dil,
            "aciklama": aciklama,
            "syntax_ok": None,
            "analiz": [],
        }

        if dil == "python":
            syntax_ok, syntax_hatasi = self._python_kontrol(kod)
            sonuc["syntax_ok"] = syntax_ok

            if not syntax_ok:
                sonuc["syntax_hatasi"] = syntax_hatasi

            analiz = EagleKodAnalizMotoru().analiz_et(kod)
            sonuc["analiz"] = analiz

        return sonuc

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
