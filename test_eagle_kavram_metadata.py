import unittest
from eagle_merkez_motoru import EagleMerkezMotoru


class KavramMetadataTest(unittest.TestCase):

    def test_metadata_korunuyor(self):
        for tr, en in [
            ("Fil", "Elephant"),
            ("Keman", "Violin"),
            ("Plüton", "Pluto"),
            ("Ayçiçeği", "Sunflower"),
            ("Buhar makinesi", "Steam engine")
        ]:
            with self.subTest(konu=tr):
                kaynak = {
                    "title": tr,
                    "url": "https://tr.wikipedia.org/?curid=123",
                    "snippet": tr + " hakkında açıklama.",
                    "content_loaded": True,
                    "topic_aliases": [tr, en],
                    "english_title": en
                }

                temiz = EagleMerkezMotoru.temizle_web_verisi(
                    [kaynak]
                )

                self.assertEqual(
                    temiz[0]["english_title"], en
                )
                self.assertEqual(
                    temiz[0]["topic_aliases"], [tr, en]
                )
                self.assertTrue(
                    temiz[0]["content_loaded"]
                )

    def test_eski_kaynak_uyumlulugu(self):
        kaynak = {
            "title": "Test",
            "snippet": "Test açıklaması.",
            "url": "https://example.com"
        }

        temiz = EagleMerkezMotoru.temizle_web_verisi(
            [kaynak]
        )

        self.assertEqual(
            temiz[0]["english_title"], ""
        )


if __name__ == "__main__":
    unittest.main()
