"""EAGLE ANA KOORDİNATÖRÜ
Uzmanları seçer, bağımlı görevleri sıralar, çıktıları aktarır ve denetler.
Mevcut uzman motorlarını callback üzerinden kullanır.
"""
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
import re


@dataclass
class EagleKoordinatorSonuc:
    ok: bool = False
    cevap: str = ""
    plan: Optional[Dict[str, Any]] = None
    gorev_sayisi: int = 0
    tamamlanan_gorev: int = 0
    denetim: Optional[Dict[str, Any]] = None
    neden: str = ""

    def as_dict(self):
        return asdict(self)


class EagleAnaKoordinator:
    SURUM = "3.0"

    def __init__(self, akil_motoru=None, uzman_calistir=None,
                 uzman_motorlari=None):
        self.akil_motoru = akil_motoru
        self.uzman_calistir = uzman_calistir
        self.uzman_motorlari = dict(uzman_motorlari or {})

    @staticmethod
    def _temizle(metin):
        return re.sub(r"\s+", " ", str(metin or "")).strip()

    @staticmethod
    def _program_ve_denetim_mi(mesaj):
        m = str(mesaj or "").replace("İ", "i").lower()
        # "Kod yazmadan", "kodsuz" gibi olumsuz ifadeler program isteği değildir.
        olumsuz = any(x in m for x in (
            "kod yazmadan", "kod yazmasan", "kod yazmayarak", "kod yazmaksızın",
            "kod yazmak istemiyorum", "kodsuz", "kod olmadan", "kod vermeden",
            "kod istemiyorum", "program yazmadan", "program yazmasan"
        ))
        program = not olumsuz and any(x in m for x in (
            "program yaz", "kod yaz", "uygulama geliştir",
            "uygulama oluştur", "program oluştur", "yazılım geliştir",
            "python ile", "python program"
        ))
        denetim = any(x in m for x in (
            "analiz et", "analizini yap", "hatalarını bul",
            "hataları bul", "hata kontrol", "güvenlik kontrol",
            "güvenliğini kontrol", "güvenlik açık", "denetle",
            "test et", "kontrol et"
        ))
        return program and denetim

    @classmethod
    def uzmanlari_sec(cls, mesaj, karar=None):
        karar = dict(karar or {})
        arac = str(karar.get("arac") or "").strip().lower()
        intent = str(karar.get("intent") or "").strip().lower()

        # Karar motoru görevi açıkça finansal analiz olarak sınıflandırdıysa
        # anahtar kelime tahmini yerine bu görev türü izlenir.
        if str(karar.get("islem") or "").strip().lower() == "finansal_analiz":
            return ["merkez_bilgi"]

        if cls._program_ve_denetim_mi(mesaj):
            return ["program_uretme", "kod_analiz", "kod_guvenlik"]

        if arac in ("eagle_sohbet", "genel_sohbet") or intent in (
            "sohbet", "basit_sohbet"
        ):
            return ["genel_sohbet"]

        if arac in ("kod_analiz", "kod_guvenlik") or intent == "kod_hata":
            return ["kod_analiz", "kod_guvenlik"]

        if arac in ("program_uretme", "program_yazma") or intent in (
            "program_yazma", "kod_yazma"
        ):
            return ["program_uretme"]

        if arac in ("web_arastirma", "web", "merkez_bilgi") or intent in (
            "guncel_bilgi", "web_arastirma"
        ):
            return ["merkez_bilgi"]

        return ["merkez_bilgi"]

    @classmethod
    def gorevlere_ayir(cls, mesaj):
        metin = cls._temizle(mesaj)
        return [metin] if metin else []

    def planla(self, mesaj, gecmis=None, karar=None):
        metin = self._temizle(mesaj)
        karar_verildi = karar is not None
        karar = dict(karar or {})
        akil_plani = None

        if not karar_verildi and self.akil_motoru is not None:
            try:
                akil_plani = self.akil_motoru.planla(metin, gecmis)
                if isinstance(akil_plani, dict):
                    karar = akil_plani.get("karar", {}) or {}
            except Exception as exc:
                akil_plani = {"hata": str(exc)}

        uzmanlar = self.uzmanlari_sec(metin, karar)
        gorevler = []

        for i, uzman in enumerate(uzmanlar):
            bagimliliklar = [1] if i > 0 and uzmanlar[0] == "program_uretme" else []
            gorevler.append({
                "id": i + 1,
                "mesaj": metin,
                "uzman": uzman,
                "bagimliliklar": bagimliliklar,
                "durum": "bekliyor",
            })

        return {
            "koordinator": "EAGLE ANA KOORDİNATÖRÜ",
            "surum": self.SURUM,
            "mesaj": metin,
            "karar": karar,
            "akil_plani": akil_plani,
            "uzmanlar": uzmanlar,
            "gorevler": gorevler,
            "asama": "plan_hazir",
        }

    @staticmethod
    def _sonucu_duzenle(ham_sonuc):
        if hasattr(ham_sonuc, "as_dict"):
            ham_sonuc = ham_sonuc.as_dict()

        if isinstance(ham_sonuc, dict):
            cevap = str(
                ham_sonuc.get("cevap")
                or ham_sonuc.get("answer")
                or ham_sonuc.get("yanit")
                or ""
            ).strip()

            if not cevap and ham_sonuc.get("kod"):
                cevap = (
                    "Program üretildi.\n\n```python\n"
                    + str(ham_sonuc["kod"]) + "\n```"
                )

            if not cevap and ham_sonuc.get("dosyalar"):
                cevap = "Üretilen dosyalar:\n" + "\n".join(
                    "- " + str(x) for x in ham_sonuc["dosyalar"]
                )

            if not cevap and "guvenli" in ham_sonuc:
                cevap = (
                    "Güvenlik kontrolü: "
                    + ("Güvenli." if ham_sonuc.get("guvenli")
                       else "Risk bulundu.")
                )

            bulgular = ham_sonuc.get("bulgular") or []
            if bulgular:
                cevap += "\n" + "\n".join("- " + str(x) for x in bulgular)

            if not cevap and ham_sonuc.get("hata"):
                cevap = str(ham_sonuc["hata"])

            basarili = ham_sonuc.get("ok", bool(cevap))
            return {
                "ok": bool(basarili and cevap),
                "cevap": cevap,
                "ham_sonuc": ham_sonuc,
            }

        if isinstance(ham_sonuc, (list, tuple)):
            cevap = "\n".join("- " + str(x) for x in ham_sonuc).strip()
            return {"ok": bool(cevap), "cevap": cevap,
                    "ham_sonuc": ham_sonuc}

        cevap = str(ham_sonuc or "").strip()
        return {"ok": bool(cevap), "cevap": cevap, "ham_sonuc": None}

    @staticmethod
    def _kod_cikar(sonuc):
        ham = sonuc.get("ham_sonuc")
        if isinstance(ham, dict):
            for anahtar in ("kod", "code", "source", "python_kodu"):
                deger = ham.get(anahtar)
                if isinstance(deger, str) and deger.strip():
                    return deger.strip()

        cevap = str(sonuc.get("cevap") or "")
        eslesen = re.search(
            r"```(?:python|py)?\s*(.*?)```", cevap, re.S | re.I
        )
        return eslesen.group(1).strip() if eslesen else ""

    @staticmethod
    def cevap_denetle(gorevler, sonuclar):
        sonuc_haritasi = {
            s.get("gorev_id"): s for s in sonuclar
            if s.get("gorev_id") is not None
        }
        tamamlanan = sum(
            1 for gorev in gorevler
            if sonuc_haritasi.get(gorev["id"], {}).get("ok")
        )
        toplam = len(gorevler)
        return {
            "gorev_toplam": toplam,
            "gorev_tamamlanan": tamamlanan,
            "gorev_eksik": max(0, toplam - tamamlanan),
            "kapsam_tamam": toplam > 0 and tamamlanan == toplam,
            "kaynak_dogrulamasi_yapildi": False,
            "uzman_hatalari": [
                {
                    "gorev_id": s.get("gorev_id"),
                    "uzman": s.get("uzman"),
                    "hata": s.get("hata") or s.get("cevap", ""),
                }
                for s in sonuclar if not s.get("ok")
            ],
            "not": (
                "Görevlerin tamamlanması denetlendi; harici kaynak "
                "doğruluğu tek başına kanıtlanmadı."
            ),
        }

    def calistir(self, mesaj, gecmis=None, uzman_calistir=None, karar=None):
        plan = self.planla(mesaj, gecmis, karar=karar)
        gorevler = plan["gorevler"]
        varsayilan = uzman_calistir or self.uzman_calistir
        sonuclar = []
        calisan_uzmanlar = []
        onceki_sonuclar = []
        uretilen_kod = ""

        for gorev in gorevler:
            uzman_adi = gorev["uzman"]
            eksik_bagimlilik = [
                bag_id for bag_id in gorev["bagimliliklar"]
                if not any(
                    s.get("gorev_id") == bag_id and s.get("ok")
                    for s in sonuclar
                )
            ]

            if gorev["bagimliliklar"] and not uretilen_kod:
                eksik_bagimlilik = list(gorev["bagimliliklar"])

            if eksik_bagimlilik:
                sonuc = {
                    "ok": False,
                    "cevap": "",
                    "hata": "Bağımlı görev başarısız veya gerekli kod çıktısı yok; bu aşama çalıştırılmadı.",
                    "uzman": uzman_adi,
                    "gorev_id": gorev["id"],
                    "durum": "engellendi",
                }
                sonuclar.append(sonuc)
                gorev["durum"] = "engellendi"
                continue

            uzman = self.uzman_motorlari.get(uzman_adi)
            if not callable(uzman):
                if uzman_adi == "merkez_bilgi" and callable(varsayilan):
                    uzman = varsayilan
                else:
                    sonuc = {
                        "ok": False,
                        "cevap": "",
                        "hata": f"{uzman_adi} uzmanı bağlı değil.",
                        "uzman": uzman_adi,
                        "gorev_id": gorev["id"],
                        "durum": "basarisiz",
                    }
                    sonuclar.append(sonuc)
                    gorev["durum"] = "basarisiz"
                    continue

            gorev_mesaji = gorev["mesaj"]
            if gorev["bagimliliklar"] and uretilen_kod:
                gorev_mesaji += (
                    "\n\nÖNCEKİ UZMANIN ÜRETTİĞİ KOD. "
                    "Bu kod üzerinde istenen incelemeyi yap:\n"
                    "```python\n" + uretilen_kod + "\n```"
                )

            gorev_karari = dict(plan["karar"])
            gorev_karari["_koordinator_onceki_sonuclar"] = list(
                onceki_sonuclar
            )
            if uretilen_kod:
                gorev_karari["_koordinator_uretilen_kod"] = uretilen_kod

            try:
                ham = uzman(gorev_mesaji, gorev_karari, gecmis)
                sonuc = self._sonucu_duzenle(ham)
                sonuc["uzman"] = uzman_adi
                sonuc["gorev_id"] = gorev["id"]
                sonuc["durum"] = (
                    "tamamlandi" if sonuc["ok"] else "basarisiz"
                )
                sonuclar.append(sonuc)
                gorev["durum"] = sonuc["durum"]

                if sonuc["ok"]:
                    calisan_uzmanlar.append(uzman_adi)
                    onceki_sonuclar.append({
                        "gorev_id": gorev["id"],
                        "uzman": uzman_adi,
                        "cevap": sonuc["cevap"],
                    })
                    if uzman_adi == "program_uretme":
                        uretilen_kod = self._kod_cikar(sonuc)
            except Exception as exc:
                sonuclar.append({
                    "ok": False,
                    "cevap": "",
                    "hata": str(exc),
                    "uzman": uzman_adi,
                    "gorev_id": gorev["id"],
                    "durum": "basarisiz",
                })
                gorev["durum"] = "basarisiz"

        denetim = self.cevap_denetle(gorevler, sonuclar)
        cevaplar = [
            s["cevap"] for s in sonuclar
            if s.get("ok") and s.get("cevap")
        ]
        cevap = "\n\n".join(dict.fromkeys(cevaplar))
        basarili = bool(cevap) and denetim["kapsam_tamam"]

        plan["calisan_uzmanlar"] = list(dict.fromkeys(calisan_uzmanlar))
        plan["sonuclar"] = sonuclar
        plan["asama"] = "sonuc_denetlendi"

        return EagleKoordinatorSonuc(
            ok=basarili,
            cevap=cevap,
            plan=plan,
            gorev_sayisi=len(gorevler),
            tamamlanan_gorev=denetim["gorev_tamamlanan"],
            denetim=denetim,
            neden=(
                "Seçilen görevlerin tamamı başarıyla tamamlandı."
                if basarili else
                "Görev zincirinde başarısız veya eksik aşama var."
            ),
        ).as_dict()


def eagle_ana_koordinatorunu_kur(
    akil_motoru=None,
    uzman_calistir=None,
    uzman_motorlari=None,
):
    return EagleAnaKoordinator(
        akil_motoru=akil_motoru,
        uzman_calistir=uzman_calistir,
        uzman_motorlari=uzman_motorlari,
    )
