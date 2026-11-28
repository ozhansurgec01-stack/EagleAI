import unittest
import time
import threading

from eagle_gorsel_motoru import GorselMotoru


def aday(no):
    return {
        "url": f"https://example.com/{no}.jpg",
        "name": f"Gorsel {no}"
    }


def secici(items, limit):
    return items[:limit]


class GorselMotoruTest(unittest.TestCase):

    def setUp(self):
        self.motor = GorselMotoru(kapasite=3)

    def tearDown(self):
        self.motor.kapat()

    def test_yavas_saglayici(self):

        def hizli(yayinla, kalan):
            yayinla(aday(1))

        def yavas(yayinla, kalan):
            time.sleep(0.8)
            yayinla(aday(2))

        r = self.motor.arastir(
            {"hizli": hizli, "yavas": yavas},
            secici,
            sure=0.2
        )

        self.assertEqual(len(r["images"]), 1)
        self.assertEqual(
            r["providers"]["yavas"],
            "zaman_asimi"
        )
        self.assertLess(r["elapsed"], 0.6)

    def test_saglayici_hatasi(self):

        def bozuk(yayinla, kalan):
            raise RuntimeError("Test hatasi")

        def saglam(yayinla, kalan):
            yayinla(aday(1))

        r = self.motor.arastir(
            {"bozuk": bozuk, "saglam": saglam},
            secici,
            sure=1
        )

        self.assertEqual(len(r["images"]), 1)
        self.assertEqual(
            r["providers"]["bozuk"],
            "hata"
        )

    def test_tekrar_engelleme(self):

        def bir(yayinla, kalan):
            yayinla(aday(1))

        def iki(yayinla, kalan):
            yayinla(aday(1))

        r = self.motor.arastir(
            {"bir": bir, "iki": iki},
            secici,
            sure=1
        )

        self.assertEqual(len(r["images"]), 1)

    def test_kaliteli_saglayici_beklenir(self):
        def hizli(yayinla, kalan):
            for i in range(4):
                x = aday(i)
                x["_score"] = 30
                yayinla(x)

        def kaliteli(yayinla, kalan):
            time.sleep(0.3)
            for i in range(4, 8):
                x = aday(i)
                x["_score"] = 100
                yayinla(x)

        def kaliteli_secici(items, limit):
            return sorted(
                items,
                key=lambda x: -x["_score"]
            )[:limit]

        r = self.motor.arastir(
            {"hizli": hizli, "kaliteli": kaliteli},
            kaliteli_secici,
            sure=2,
            limit=4
        )

        self.assertEqual(len(r["images"]), 4)
        self.assertTrue(all(
            x["_score"] == 100
            for x in r["images"]
        ))

    def test_gec_sonuc_reddedilir(self):

        bitti = threading.Event()
        kabul = []

        def yavas(yayinla, kalan):
            time.sleep(0.3)
            kabul.append(yayinla(aday(1)))
            bitti.set()

        r = self.motor.arastir(
            {"yavas": yavas},
            secici,
            sure=0.1
        )

        self.assertEqual(r["images"], [])
        self.assertTrue(bitti.wait(2))
        self.assertEqual(kabul, [False])
        self.assertEqual(r["images"], [])

    def test_kapasite_korumasi(self):

        motor = GorselMotoru(kapasite=1)
        basladi = threading.Event()
        serbest = threading.Event()

        def yavas(yayinla, kalan):
            basladi.set()
            serbest.wait(2)

        try:
            motor.arastir(
                {"bir": yavas},
                secici,
                sure=0.1
            )

            self.assertTrue(basladi.wait(1))

            r = motor.arastir(
                {"iki": yavas},
                secici,
                sure=0.1
            )

            self.assertEqual(
                r["providers"]["iki"],
                "yogun"
            )

        finally:
            serbest.set()
            motor.kapat()

    def test_paralel_calisma(self):

        bariyer = threading.Barrier(2)

        def bir(yayinla, kalan):
            bariyer.wait(timeout=1)
            yayinla(aday(1))

        def iki(yayinla, kalan):
            bariyer.wait(timeout=1)
            yayinla(aday(2))

        r = self.motor.arastir(
            {"bir": bir, "iki": iki},
            secici,
            sure=2
        )

        self.assertEqual(len(r["images"]), 2)


if __name__ == "__main__":
    unittest.main()
