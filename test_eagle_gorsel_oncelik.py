import unittest
import threading

from eagle_gorsel_motoru import GorselMotoru


class GorselOncelikTest(unittest.TestCase):

    def test_yuksek_puanli_tekrar_korunur(self):
        motor = GorselMotoru(kapasite=2)
        hazir = threading.Event()

        def hizli(yayinla, kalan):
            yayinla({
                "url": "https://example.com/test.jpg",
                "_score": 30
            })
            hazir.set()

        def kaliteli(yayinla, kalan):
            if hazir.wait(timeout=1):
                yayinla({
                    "url": "https://example.com/test.jpg",
                    "_score": 100
                })

        try:
            sonuc = motor.arastir(
                {
                    "hizli": hizli,
                    "kaliteli": kaliteli
                },
                lambda items, limit: sorted(
                    items,
                    key=lambda x: -x.get("_score", 0)
                )[:limit],
                sure=2,
                limit=4
            )

            self.assertEqual(len(sonuc["images"]), 1)
            self.assertEqual(
                sonuc["images"][0]["_score"], 100
            )

            print("OK: En kaliteli aday korundu.")

        finally:
            motor.kapat()


if __name__ == "__main__":
    unittest.main()
