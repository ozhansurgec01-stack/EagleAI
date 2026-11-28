import unittest
from eagle_arastirma_v2 import ansiklopedi_kaynaklari

class Response:
    status_code = 200

    def __init__(self, page):
        self.page = page

    def json(self):
        return {"query": {"pages": [self.page]}}


class KavramProfiliTest(unittest.TestCase):

    def test_otomatik_dil_eslesmesi(self):
        for tr, en in [
            ("Fil", "Elephant"),
            ("Ayçiçeği", "Sunflower"),
            ("Buhar makinesi", "Steam engine"),
            ("Plüton", "Pluto"),
            ("Keman", "Violin"),
            ("Atatürk", "Mustafa Kemal Atatürk")
        ]:
            with self.subTest(konu=tr):
                page = {
                    "title": tr,
                    "pageid": 123,
                    "extract": (tr + " hakkında açıklama. ") * 10,
                    "langlinks": [
                        {"lang": "en", "title": en}
                    ]
                }

                rows = ansiklopedi_kaynaklari(
                    tr + " nedir",
                    get=lambda *a, **k: Response(page)
                )

                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["english_title"], en)
                self.assertIn(en, rows[0]["topic_aliases"])

    def test_belirsiz_kavram(self):
        page = {
            "title": "Fil",
            "pageid": 123,
            "extract": "Belirsiz kavram. " * 10,
            "pageprops": {"disambiguation": ""},
            "langlinks": [
                {"lang": "en", "title": "Wrong entity"}
            ]
        }

        rows = ansiklopedi_kaynaklari(
            "Fil nedir",
            get=lambda *a, **k: Response(page)
        )

        self.assertEqual(rows, [])

    def test_dil_baglantisi_yok(self):
        page = {
            "title": "Keman",
            "pageid": 123,
            "extract": "Keman bir müzik aletidir. " * 10
        }

        rows = ansiklopedi_kaynaklari(
            "Keman nedir",
            get=lambda *a, **k: Response(page)
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["english_title"], "")


if __name__ == "__main__":
    unittest.main()
