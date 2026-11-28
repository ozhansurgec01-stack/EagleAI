import unittest
from unittest.mock import patch, MagicMock

from eagle_gorsel_dogrulama import (
    guvenilir_adres,
    gorsel_formati,
    dogrula
)


class GorselDogrulamaTest(unittest.TestCase):

    def test_flickr(self):
        self.assertTrue(guvenilir_adres(
            "https://live.staticflickr.com/test.jpg"))

    def test_sahte_host(self):
        self.assertFalse(guvenilir_adres(
            "https://live.staticflickr.com.example.org/a.jpg"))

    def test_localhost(self):
        self.assertFalse(guvenilir_adres(
            "https://127.0.0.1/test.jpg"))

    def test_http(self):
        self.assertFalse(guvenilir_adres(
            "http://live.staticflickr.com/test.jpg"))

    def test_jpeg(self):
        self.assertEqual(
            gorsel_formati(b"\xff\xd8\xffabc"), "jpeg")

    def test_png(self):
        self.assertEqual(
            gorsel_formati(b"\x89PNG\r\n\x1a\n"), "png")

    def test_webp(self):
        self.assertEqual(
            gorsel_formati(b"RIFF1234WEBP"), "webp")

    def test_html(self):
        self.assertIsNone(
            gorsel_formati(b"<html>Error</html>"))

    @patch("eagle_gorsel_dogrulama.requests.get")
    def test_http_durumlari(self, get):
        r = MagicMock()
        get.return_value.__enter__.return_value = r

        r.headers = {"Content-Type": "image/jpeg"}
        r.iter_content.return_value = iter(
            [b"\xff\xd8\xffabc"]
        )

        url = "https://live.staticflickr.com/test.jpg"

        r.status_code = 429
        self.assertFalse(dogrula(url))

        r.status_code = 424
        self.assertFalse(dogrula(url))

        r.status_code = 200
        self.assertTrue(dogrula(url))


if __name__ == "__main__":
    unittest.main()
