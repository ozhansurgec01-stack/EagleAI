import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from eagle_altinkaynak import parse_payload, _fiyat

IST = ZoneInfo("Europe/Istanbul")
NOW = datetime(2026, 11, 8, 0, 20, tzinfo=IST)


def item(code="GA", **changes):
    value = {
        "Kod": code,
        "Aciklama": "Gram Altın",
        "Alis": "6.548",
        "Satis": "6.651",
        "GuncellenmeZamani": "08.11.2026 00:17:26",
        "IsMobile": True,
    }
    value.update(changes)
    return value


class AltinkaynakTests(unittest.TestCase):
    def test_gram_altin_eslesmesi(self):
        result = parse_payload([item()], now=NOW)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["urun"], "Gram Altın")
        self.assertEqual(result[0]["alis"], 6548)
        self.assertEqual(result[0]["satis"], 6651)
        self.assertEqual(result[0]["tarih"], "2026-11-08")
        self.assertEqual(result[0]["tarih_kapsami"], "urun")
        self.assertEqual(result[0]["host"], "static.altinkaynak.com")

    def test_dogrulanmamis_urun_kodlari_dislanir(self):
        payload = [item(code) for code in ("C", "PC", "Y", "T", "PA", "XX")]
        self.assertEqual(parse_payload(payload, now=NOW), [])

    def test_eski_ve_gelecek_veri_dislanir(self):
        eski = item(GuncellenmeZamani="08.11.2026 00:14:59")
        gelecek = item(GuncellenmeZamani="08.11.2026 00:21:00")
        self.assertEqual(parse_payload([eski], now=NOW), [])
        self.assertEqual(parse_payload([gelecek], now=NOW), [])

    def test_gecersiz_fiyat_ve_tarih_dislanir(self):
        for changes in (
            {"Alis": "0"},
            {"Satis": "hatalı"},
            {"GuncellenmeZamani": "geçersiz"},
        ):
            self.assertEqual(
                parse_payload([item(**changes)], now=NOW), []
            )

    def test_yetkisiz_url_ve_payload_dislanir(self):
        self.assertEqual(
            parse_payload([item()], url="https://ornek.com/public/Gold", now=NOW),
            [],
        )
        self.assertEqual(
            parse_payload([item()], url="http://static.altinkaynak.com/public/Gold", now=NOW),
            [],
        )
        self.assertEqual(parse_payload({"data": [item()]}, now=NOW), [])

    def test_fiyat_formatlari(self):
        self.assertEqual(_fiyat("6.548"), 6548)
        self.assertEqual(_fiyat("6.548,25"), 6548.25)
        self.assertEqual(_fiyat("6548.25"), 6548.25)
        self.assertIsNone(_fiyat(True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
