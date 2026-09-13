"""
🦅 EAGLE AKIL MOTORU v1.1
Merkezi orkestrasyon + konuşma bağlamı.

Amaç:
- Mevcut karar motorunu kullanmak
- Önceki konuşmadan aktif konuyu taşımak
- Devam sorularını önceki konuyla ilişkilendirmek
- Kalıcı hafıza ile geçici konuşma bağlamını ayırmak
- Doğrulanmamış bilgiyi otomatik öğrenmemek
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


@dataclass
class EagleAkilKarari:
    intent: str = "sohbet"

    def get(self, anahtar, varsayilan=None):
        """Eski sözlük tabanlı EagleAI koduyla geriye dönük uyumluluk."""
        eslesme = {
            "intent": self.intent,
            "arac": self.arac,
            "islem": self.islem,
            "guven": self.guven,
            "neden": self.neden,
            "dogrulama": self.dogrulama_gerekli,
            "dogrulama_gerekli": self.dogrulama_gerekli,
            "ogrenme_adayi": self.ogrenme_adayi,
            "baglamdan": self.baglam_kullanildi,
            "history_devam": self.baglam_kullanildi,
        }
        return eslesme.get(anahtar, varsayilan)
    arac: str = "eagle_sohbet"
    islem: str = "cevapla"
    guven: str = "orta"
    neden: str = ""
    dogrulama_gerekli: bool = False
    ogrenme_adayi: bool = False
    baglam_kullanildi: bool = False


class EagleAkilMotoru:

    SURUM = "1.1"

    DEVAM_IFADELERI = (
        "bunu",
        "buna",
        "şunu",
        "şuna",
        "onun",
        "onda",
        "ondan",
        "peki",
        "peki ya",
        "devam et",
        "devamını",
        "daha açık",
        "daha fazla",
        "biraz daha",
        "anlatır mısın",
        "açıklar mısın",
        "ne demek",
        "neden",
        "nasıl yani",
        "sonra ne oldu",
        "ne zaman",
        "kaç tane",
        "hangisi"
    )

    def __init__(self, karar_motoru=None, hafiza_yukle=None):
        self.karar_motoru = karar_motoru
        self.hafiza_yukle = hafiza_yukle

        # Geçici konuşma durumu.
        # Kalıcı hafızanın yerine geçmez.
        self.son_konu = ""
        self.son_intent = ""
        self.son_arac = ""
        self.son_mesaj = ""

    @staticmethod
    def normalize(mesaj: Any) -> str:
        return str(mesaj or "").strip()

    @classmethod
    def devam_sorusu_mu(cls, mesaj: str) -> bool:
        metin = cls.normalize(mesaj).lower()

        if not metin:
            return False

        return any(
            ifade in metin
            for ifade in cls.DEVAM_IFADELERI
        )

    def _baglam_uygula(
        self,
        mesaj: str,
        karar: EagleAkilKarari
    ) -> EagleAkilKarari:

        if not self.son_mesaj:
            return karar

        # Açık bir devam ifadesi varsa veya hem mevcut hem önceki
        # karar genel sohbet akışındaysa bağlamı koru.
        # Bağımsız bilgi/araç soruları eski sohbet tarafından ezilmez.
        ayni_sohbet_akisi = (
            karar.arac == "eagle_sohbet"
            and self.son_arac == "eagle_sohbet"
        )

        if not self.devam_sorusu_mu(mesaj) and not ayni_sohbet_akisi:
            return karar

        # Önceki istek belirgin bir araç/konu taşıyorsa
        # devam mesajını o bağlama bağla.
        if self.son_intent and self.son_arac:
            karar.intent = self.son_intent
            karar.arac = self.son_arac
            karar.baglam_kullanildi = True
            karar.neden = (
                "Konuşma bağlamı önceki sohbet akışıyla "
                "ilişkilendirildi."
            )

        return karar

    def anla(self, mesaj: Any, gecmis=None) -> EagleAkilKarari:
        metin = self.normalize(mesaj)

        if not metin:
            return EagleAkilKarari(
                intent="bos",
                arac="yok",
                islem="bekle",
                guven="yüksek",
                neden="Boş mesaj."
            )

        if callable(self.karar_motoru):
            try:
                ham_karar = self.karar_motoru(
                    metin,
                    gecmis
                )

                if isinstance(ham_karar, dict):
                    karar = EagleAkilKarari(
                        intent=ham_karar.get(
                            "intent",
                            "sohbet"
                        ),
                        arac=ham_karar.get(
                            "arac",
                            "eagle_sohbet"
                        ),
                        islem=ham_karar.get(
                            "islem",
                            "cevapla"
                        ),
                        guven=ham_karar.get(
                            "guven",
                            "orta"
                        ),
                        neden=ham_karar.get(
                            "neden",
                            ""
                        ),
                        dogrulama_gerekli=bool(
                            ham_karar.get(
                                "dogrulama",
                                False
                            )
                        ),
                        ogrenme_adayi=False,
                        baglam_kullanildi=bool(
                            ham_karar.get(
                                "baglamdan",
                                False
                            )
                            or ham_karar.get(
                                "history_devam",
                                False
                            )
                        )
                    )

                    karar = self._baglam_uygula(
                        metin,
                        karar
                    )

                    self._durumu_guncelle(
                        metin,
                        karar
                    )

                    return karar

            except Exception as exc:
                return EagleAkilKarari(
                    intent="sohbet",
                    arac="eagle_sohbet",
                    guven="düşük",
                    neden=(
                        "Karar motoru güvenli geri dönüş yaptı: "
                        f"{exc}"
                    )
                )

        karar = EagleAkilKarari(
            intent="sohbet",
            arac="eagle_sohbet",
            guven="orta",
            neden="Varsayılan doğal sohbet yolu."
        )

        karar = self._baglam_uygula(
            metin,
            karar
        )

        self._durumu_guncelle(
            metin,
            karar
        )

        return karar

    def _durumu_guncelle(
        self,
        mesaj: str,
        karar: EagleAkilKarari
    ):
        """
        Sadece aktif konuşmanın çalışma durumunu tutar.
        Kalıcı hafızaya otomatik yazmaz.
        """

        self.son_mesaj = mesaj
        self.son_intent = karar.intent
        self.son_arac = karar.arac

        if karar.intent not in (
            "sohbet",
            "basit_sohbet",
            "bos"
        ):
            self.son_konu = karar.intent

    def planla(
        self,
        mesaj: Any,
        gecmis=None
    ) -> Dict[str, Any]:

        karar = self.anla(
            mesaj,
            gecmis
        )

        return {
            "motor": "EAGLE AKIL MOTORU",
            "surum": self.SURUM,
            "mesaj": self.normalize(mesaj),
            "karar": asdict(karar),
            "baglam": {
                "son_konu": self.son_konu,
                "son_intent": self.son_intent,
                "son_arac": self.son_arac,
                "son_mesaj": self.son_mesaj
            },
            "asama": "arac_secimi"
        }

    def dogrula_adayi(
        self,
        kaynak: Optional[str],
        sonuc: Any
    ) -> Dict[str, Any]:

        var = bool(sonuc)

        return {
            "kaynak_var": bool(kaynak),
            "sonuc_var": var,
            "ogrenmeye_hazir": bool(
                kaynak and var
            )
        }

    def ogrenme_kontrolu(
        self,
        kaynak: Optional[str],
        sonuc: Any,
        dogrulandi: bool = False
    ) -> Dict[str, Any]:

        uygun = bool(
            kaynak
            and sonuc
            and dogrulandi
        )

        return {
            "aday": uygun,
            "kaynak": kaynak or "",
            "neden": (
                "Kaynak ve doğrulanmış sonuç mevcut."
                if uygun
                else
                "Bilgi doğrulanmadan kalıcı öğrenme "
                "yapılmayacak."
            )
        }


def eagle_akil_motorunu_kur(
    karar_motoru=None,
    hafiza_yukle=None
):
    return EagleAkilMotoru(
        karar_motoru=karar_motoru,
        hafiza_yukle=hafiza_yukle
    )
