import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from eagle_sanalkuyumculuk import parse_payload, _fiyat


IST = ZoneInfo("Europe/Istanbul")
NOW = datetime(2026, 11, 7, 23, 45, tzinfo=IST)


def item(product_id, **changes):
    value = {
        "id": product_id,
        "updatedAt": "2026-11-07T23:44:00",
        "customerBuysAt": "6.576,22",
        "customerSellsAt": "6.597,09",
        "isVisible": True,
        "buyTradeStatus": True,
        "sellTradeStatus": True,
    }
    value.update(changes)
    return value


class SanalKuyumculukTests(unittest.TestCase):
    def test_bes_urun_eslesmesi(self):
        payload = {"data": [item(i) for i in (0, 35, 37, 39, 49)]}
        result = parse_payload(payload, now=NOW)
        self.assertEqual(
            [x["urun"] for x in result],
            ["Gram Altın", "Çeyrek Altın", "Yarım Altın",
             "Tam Altın", "Ata Altın"],
        )
        self.assertEqual(result[0]["alis"], 6576.22)
        self.assertEqual(result[0]["satis"], 6597.09)
        self.assertEqual(result[0]["tarih"], "2026-11-07")
        self.assertEqual(result[0]["tarih_kapsami"], "urun")

    def test_eski_varyantlar_ve_bilinmeyen_id_dislanir(self):
        payload = {"data": [item(i) for i in (1, 36, 38, 40, 50, 999)]}
        self.assertEqual(parse_payload(payload, now=NOW), [])

    def test_eski_veri_dislanir(self):
        payload = {"data": [item(0, updatedAt="2026-11-07T23:39:00")]}
        self.assertEqual(parse_payload(payload, now=NOW), [])

    def test_gelecek_zaman_toleransi(self):
        gecmis = {"data": [item(0, updatedAt="2026-11-07T23:45:20")]}
        gelecek = {"data": [item(0, updatedAt="2026-11-07T23:46:00")]}
        self.assertEqual(len(parse_payload(gecmis, now=NOW)), 1)
        self.assertEqual(parse_payload(gelecek, now=NOW), [])

    def test_pasif_urun_dislanir(self):
        for field in ("isVisible", "buyTradeStatus", "sellTradeStatus"):
            payload = {"data": [item(0, **{field: "false"})]}
            self.assertEqual(parse_payload(payload, now=NOW), [])

    def test_gecersiz_fiyat_ve_tarih_dislanir(self):
        for changes in (
            {"customerBuysAt": "0"},
            {"customerSellsAt": "abc"},
            {"updatedAt": "gecersiz"},
        ):
            self.assertEqual(
                parse_payload({"data": [item(0, **changes)]}, now=NOW), []
            )

    def test_yetkisiz_url_ve_hatalı_payload(self):
        payload = {"data": [item(1)]}
        self.assertEqual(
            parse_payload(payload, url="https://ornek.com/altin-api.php", now=NOW), []
        )
        self.assertEqual(
            parse_payload(payload, url="http://sanalkuyumculuk.com/altin-api.php", now=NOW), []
        )
        self.assertEqual(parse_payload([], now=NOW), [])
        self.assertEqual(parse_payload({"data": "hatalı"}, now=NOW), [])

    def test_fiyat_formatlari(self):
        self.assertEqual(_fiyat("6.576,22"), 6576.22)
        self.assertEqual(_fiyat("6576.22"), 6576.22)
        self.assertEqual(_fiyat("6,576.22"), 6576.22)
        self.assertIsNone(_fiyat(True))
        self.assertIsNone(_fiyat("0"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
