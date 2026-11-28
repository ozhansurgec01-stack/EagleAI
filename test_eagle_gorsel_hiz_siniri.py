import unittest
from unittest.mock import patch, Mock
import requests
import eagle_gorsel_hiz_siniri as motor


class HizSiniriTest(unittest.TestCase):

    def setUp(self):
        motor._BEKLEME.clear()

    def tearDown(self):
        motor._BEKLEME.clear()

    def test_tekrar_engellenir(self):
        yanit = Mock()
        yanit.status_code = 429
        yanit.headers = {"Retry-After": "60"}

        with patch.object(
            motor.requests, "get",
            return_value=yanit
        ) as get:
            for _ in range(2):
                with self.assertRaises(requests.HTTPError):
                    motor.kontrollu_get(
                        "https://commons.wikimedia.org/w/api.php"
                    )

            self.assertEqual(get.call_count, 1)

    def test_host_izolasyonu(self):
        hata = Mock()
        hata.status_code = 429
        hata.headers = {"Retry-After": "60"}

        basarili = Mock()
        basarili.status_code = 200

        with patch.object(
            motor.requests, "get",
            side_effect=[hata, basarili]
        ) as get:
            with self.assertRaises(requests.HTTPError):
                motor.kontrollu_get(
                    "https://commons.wikimedia.org/w/api.php"
                )

            sonuc = motor.kontrollu_get(
                "https://www.wikidata.org/w/api.php"
            )

            self.assertEqual(sonuc.status_code, 200)
            self.assertEqual(get.call_count, 2)


if __name__ == "__main__":
    unittest.main()
