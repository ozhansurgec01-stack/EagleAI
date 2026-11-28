import unittest
import requests

from eagle_saglayici_kontrol import (
    SaglayiciKontrol,
    hata_bekleme
)


class SaglayiciTest(unittest.TestCase):

    def setUp(self):
        self.now = 100
        self.motor = SaglayiciKontrol(
            clock=lambda: self.now
        )

    def test_403_bekleme(self):
        self.assertTrue(
            self.motor.baslat("mojeek")
        )
        self.motor.bitir("mojeek", 1800)

        self.assertFalse(
            self.motor.baslat("mojeek")
        )

        self.now += 1800

        self.assertTrue(
            self.motor.baslat("mojeek")
        )

    def test_paralel_istek(self):
        self.assertTrue(
            self.motor.baslat("google")
        )
        self.assertFalse(
            self.motor.baslat("google")
        )

        self.motor.bitir("google")

        self.assertTrue(
            self.motor.baslat("google")
        )

    def test_saglayici_bagimsizligi(self):
        self.motor.baslat("mojeek")
        self.motor.bitir("mojeek", 1800)

        self.assertTrue(
            self.motor.baslat("ddg-lite")
        )

    def test_http_hatalari(self):
        for status, expected in [
            (403, 1800),
            (429, 300),
            (500, 60),
            (503, 60),
            (404, 0),
        ]:
            with self.subTest(status=status):
                r = requests.Response()
                r.status_code = status

                exc = requests.HTTPError(
                    response=r
                )

                self.assertEqual(
                    hata_bekleme(exc), expected
                )

    def test_retry_after(self):
        r = requests.Response()
        r.status_code = 429
        r.headers["Retry-After"] = "120"

        self.assertEqual(
            hata_bekleme(
                requests.HTTPError(response=r)
            ),
            120
        )

    def test_timeout(self):
        self.assertEqual(
            hata_bekleme(requests.Timeout()),
            30
        )


if __name__ == "__main__":
    unittest.main()
