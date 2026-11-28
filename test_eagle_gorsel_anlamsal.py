import unittest
from eagle_gorsel_kalite import uygun_mu


class AnlamsalKaliteTest(unittest.TestCase):

    def test_kategori_kalitesi(self):
        ornekler = [
            ("person", "Albert Einstein age 3", True),
            ("person", "Albert Einstein portrait", True),
            ("person", "Albert Einstein with his wife", True),
            ("person", "Albert Einstein quote at library", False),
            ("person", "3D-scanned statue of Albert Einstein", False),
            ("person", "Albert Einstein spacecraft", False),
            ("person", "Nikola Tesla portrait", True),
            ("person", "Nikola Tesla commemorative coin", False),
            ("person", "Isaac Newton statue", False),
            ("person", "Marie Curie laboratory photograph", True),
            ("animal", "African elephant wildlife", True),
            ("animal", "Elephant plastic toy", False),
            ("plant", "Sunflower botanical photograph", True),
            ("technology", "Steam engine structure", True),
            ("landmark", "Statue of Liberty", True),
            ("astronomy", "Venus spacecraft image", True),
            ("plant", "Artificial sunflower", False),
            ("animal", "Lion plush toy", False),
        ]

        for tur, baslik, beklenen in ornekler:
            with self.subTest(tur=tur, baslik=baslik):
                self.assertEqual(
                    bool(uygun_mu(
                        baslik,
                        "https://commons.wikimedia.org/",
                        tur
                    )),
                    beklenen
                )


if __name__ == "__main__":
    unittest.main()
