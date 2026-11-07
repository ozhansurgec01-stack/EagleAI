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


def responses(altin_alis=6548, altin_satis=6651):
    now = datetime.now(ZoneInfo("Europe/Istanbul")).replace(microsecond=0) - timedelta(minutes=1)
    sanal = {"data": [{
        "id": 0, "updatedAt": now.isoformat(),
        "customerBuysAt": "6576.22", "customerSellsAt": "6597.09",
        "isVisible": True, "buyTradeStatus": True, "sellTradeStatus": True,
    }]}
    altin = [{
        "Kod": "GA", "Alis": str(altin_alis), "Satis": str(altin_satis),
        "GuncellenmeZamani": now.strftime("%d.%m.%Y %H:%M:%S"),
    }]
    return {SANAL_URL: FakeResponse(sanal), ALTIN_URL: FakeResponse(altin)}


class AltinEntegrasyonTests(unittest.TestCase):
    def test_iki_api_uyumlu(self):
        data = responses()
        with patch("requests.get", side_effect=lambda url, **kw: data[url]):
            cevap, guven = EagleMerkezMotoru().genel_altin_cevabi("Gram altın fiyatı", [])
        self.assertIn("Gram Altın", cevap)
        self.assertIn("6.562,11 TL", cevap)
        self.assertGreater(guven, 0)

    def test_yuzde_iki_fark_asilirsa_cevap_yok(self):
        data = responses(6800, 6900)
        with patch("requests.get", side_effect=lambda url, **kw: data[url]):
            cevap, guven = EagleMerkezMotoru().genel_altin_cevabi("Gram altın fiyatı", [])
        self.assertEqual(cevap, "")
        self.assertEqual(guven, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
