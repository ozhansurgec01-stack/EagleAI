import unittest
from unittest.mock import patch
import eagle_api as m


class GorselApiTest(unittest.TestCase):

    def setUp(self):
        self.client = m.app.test_client()
        self.images = [
            {"url": "https://example.org/test.jpg"}
        ]

    def test_endpoint(self):
        with patch.object(
            m,
            "_eagle_yer_gorsellerini_guvenli_getir",
            return_value=self.images
        ) as gallery:

            for q in [
                "Kanada hakkında bilgi",
                "Mitokondri nedir?",
                "ATP nedir?"
            ]:
                with self.subTest(q=q):
                    r = self.client.post(
                        "/api/gorseller",
                        json={"message": q}
                    )
                    self.assertEqual(r.status_code, 200)
                    self.assertEqual(
                        r.get_json()["images"], self.images
                    )

            self.assertEqual(gallery.call_count, 3)

    def test_finans(self):
        with patch.object(
            m,
            "_eagle_yer_gorsellerini_guvenli_getir"
        ) as gallery:
            r = self.client.post(
                "/api/gorseller",
                json={"message": "100 dolar kaç TL?"}
            )
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.get_json()["images"], [])
            gallery.assert_not_called()

    def test_gecersiz_istek(self):
        for payload in [
            {},
            {"message": ""},
            {"message": 123},
            {"message": "x" * 501},
            {"message": "ATP nedir?", "answer": []}
        ]:
            with self.subTest(payload=payload):
                r = self.client.post(
                    "/api/gorseller",
                    json=payload
                )
                self.assertEqual(r.status_code, 400)

    def sohbet_cevabi(self, ertelenmis):
        payload = {"message": "Mitokondri nedir?"}

        if ertelenmis:
            payload["defer_images"] = True

        with m.app.test_request_context(
            "/api/sohbet",
            method="POST",
            json=payload
        ):
            response = m.jsonify({
                "ok": True,
                "answer": "Mitokondri bir organeldir.",
                "web_search": True,
                "research_status": "unverified_source_extract"
            })
            return m.eagle_sohbet_hata_sozlesmesi(
                response
            ).get_json()

    def test_yeni_apk(self):
        with patch.object(
            m,
            "_eagle_yer_gorsellerini_guvenli_getir"
        ) as gallery:
            data = self.sohbet_cevabi(True)
            self.assertTrue(data["images_pending"])
            self.assertTrue(data["place_gallery"])
            self.assertEqual(
                data["media_images"]["images"], []
            )
            gallery.assert_not_called()

    def test_eski_apk(self):
        with patch.object(
            m,
            "_eagle_yer_gorsellerini_guvenli_getir",
            return_value=self.images
        ) as gallery:
            data = self.sohbet_cevabi(False)
            self.assertFalse(
                data.get("images_pending", False)
            )
            self.assertTrue(data["place_gallery"])
            self.assertEqual(
                data["media_images"]["images"],
                self.images
            )
            gallery.assert_called_once()


if __name__ == "__main__":
    unittest.main()
