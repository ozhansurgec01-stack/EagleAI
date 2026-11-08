import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from eagle_merkez_motoru import EagleMerkezMotoru
from eagle_sanalkuyumculuk import API_URL as SANAL_URL
from eagle_altinkaynak import API_URL as ALTIN_URL


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


def responses(altin_alis=6548, altin_satis=6651, ceyrek_alis=10569):
    now = (
        datetime.now(ZoneInfo("Europe/Istanbul"))
        .replace(microsecond=0) - timedelta(minutes=1)
    )

    sanal = {"data": [
        {
            "id": 0, "updatedAt": now.isoformat(),
            "customerBuysAt": "6576.22", "customerSellsAt": "6597.09",
            "isVisible": True, "buyTradeStatus": True, "sellTradeStatus": True,
        },
        {
            "id": 35, "updatedAt": now.isoformat(),
            "customerBuysAt": "10576", "customerSellsAt": "10897",
            "isVisible": True, "buyTradeStatus": True, "sellTradeStatus": True,
        },
        {
            "id": 37, "updatedAt": now.isoformat(),
            "customerBuysAt": "21048", "customerSellsAt": "21909",
            "isVisible": True, "buyTradeStatus": True, "sellTradeStatus": True,
        },
    ]}

    zaman = now.strftime("%d.%m.%Y %H:%M:%S")
    altin = [
        {
            "Kod": "GA", "Alis": str(altin_alis), "Satis": str(altin_satis),
            "GuncellenmeZamani": zaman,
        },
        {
            "Kod": "C", "Alis": str(ceyrek_alis), "Satis": "10893",
            "GuncellenmeZamani": zaman,
        },
        {
            "Kod": "Y", "Alis": "21048", "Satis": "21909",
            "GuncellenmeZamani": zaman,
        },
    ]
    return {
        SANAL_URL: FakeResponse(sanal),
        ALTIN_URL: FakeResponse(altin),
    }


class AltinEntegrasyonTests(unittest.TestCase):
    def test_gram_altin_iki_api_ile_dogrulanir(self):
        data = responses()
        with patch("requests.get", side_effect=lambda url, **kw: data[url]):
            cevap, guven = EagleMerkezMotoru().genel_altin_cevabi(
                "Gram altın fiyatı", []
            )
        self.assertIn("Gram Altın", cevap)
        self.assertIn("6.562,11 TL", cevap)
        self.assertGreater(guven, 0)

    def test_genel_sorguda_gram_ceyrek_yarim_gosterilir(self):
        data = responses()
        with patch("requests.get", side_effect=lambda url, **kw: data[url]):
            cevap, guven = EagleMerkezMotoru().genel_altin_cevabi(
                "Güncel altın fiyatları", []
            )
        self.assertIn("Gram Altın", cevap)
        self.assertIn("Çeyrek Altın", cevap)
        self.assertIn("Yarım Altın", cevap)
        self.assertGreater(guven, 0)

    def test_ceyrek_uyusmazligi_gram_ve_yarimi_engellemez(self):
        data = responses(ceyrek_alis=12000)
        with patch("requests.get", side_effect=lambda url, **kw: data[url]):
            cevap, guven = EagleMerkezMotoru().genel_altin_cevabi(
                "Güncel altın fiyatları", []
            )
        self.assertIn("Gram Altın", cevap)
        self.assertNotIn("Çeyrek Altın", cevap)
        self.assertIn("Yarım Altın", cevap)
        self.assertGreater(guven, 0)

    def test_yuzde_iki_fark_asilirsa_html_gram_fallback_yok(self):
        data = responses(6800, 6900)
        html_verileri = [
            {"url": "https://altin-a.example/fiyat", "text": "Gram Altın alış 6500 TL satış 6550 TL"},
            {"url": "https://altin-b.example/fiyat", "text": "Gram Altın alış 6500 TL satış 6550 TL"},
        ]
        with patch("requests.get", side_effect=lambda url, **kw: data[url]):
            cevap, guven = EagleMerkezMotoru().genel_altin_cevabi(
                "Gram altın fiyatı", html_verileri
            )
        self.assertEqual(cevap, "")
        self.assertEqual(guven, 0.0)

    def test_api_hatasinda_html_gram_fallback_yok(self):
        html_verileri = [
            {"url": "https://altin-a.example/fiyat", "text": "Gram Altın alış 6500 TL satış 6550 TL"},
            {"url": "https://altin-b.example/fiyat", "text": "Gram Altın alış 6500 TL satış 6550 TL"},
        ]
        with patch("requests.get", side_effect=RuntimeError("API erişilemiyor")):
            cevap, guven = EagleMerkezMotoru().genel_altin_cevabi(
                "Gram altın fiyatı", html_verileri
            )
        self.assertEqual(cevap, "")
        self.assertEqual(guven, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
