import unittest
from eagle_gorsel_kabul import openverse_puanla


class GorselKabulTest(unittest.TestCase):

    def aday(self, baslik, **ek):
        sonuc = {
            "name": baslik,
            "provider": "Openverse",
            "url": "https://live.staticflickr.com/1/a.jpg",
            "source": "https://www.flickr.com/photos/test/1",
            "license": "by",
            "creator": "Test creator",
            "width": 800,
            "height": 600
        }
        sonuc.update(ek)
        return sonuc

    def test_bilimsel_adaylar(self):
        testler = [
            ("Abnormal Mouse Mitochondria",
             ["mitochondria"]),

            ("Cells with nuclei in blue, mitochondria in green",
             ["mitochondria"]),

            ("ATP and dATP", ["ATP"]),

            ("ADP ATP cycle", ["ATP"]),

            ("Adenosine-triphosphate-anion-3D-balls.png",
             ["adenosine triphosphate"])
        ]

        for baslik, kavramlar in testler:
            with self.subTest(baslik=baslik):
                self.assertGreaterEqual(
                    openverse_puanla(
                        self.aday(baslik),
                        kavramlar, "science"
                    ), 10
                )

    def test_ulke_adaylari(self):
        testler = [
            ("Trollstigen - Rauma, Norway - Landscape photography",
             ["Norway"]),

            ("View from Trolltunga - Norway, Ringedalsvatnet",
             ["Norway"]),

            ("Night photos of Vancouver, Canada",
             ["Canada"])
        ]

        for baslik, kavramlar in testler:
            with self.subTest(baslik=baslik):
                self.assertGreaterEqual(
                    openverse_puanla(
                        self.aday(baslik),
                        kavramlar, "country"
                    ), 10
                )

    def test_ilgisiz_adaylar(self):
        for baslik in [
            "This is a horrible metaphor. The mitochondria?",
            "Mitochondria shirt",
            "Mitochondria",
            "ATP bicycle"
        ]:
            with self.subTest(baslik=baslik):
                self.assertLess(
                    openverse_puanla(
                        self.aday(baslik),
                        ["mitochondria", "ATP"],
                        "science"
                    ), 10
                )

    def test_yanlis_konu(self):
        self.assertLess(openverse_puanla(
            self.aday("Night photos of Vancouver, Canada"),
            ["Norway"], "country"
        ), 10)

    def test_lisans(self):
        self.assertLess(openverse_puanla(
            self.aday("ADP ATP cycle", license="unknown"),
            ["ATP"], "science"
        ), 10)

    def test_yazar(self):
        self.assertLess(openverse_puanla(
            self.aday("ADP ATP cycle", creator=""),
            ["ATP"], "science"
        ), 10)

    def test_guvensiz_adres(self):
        self.assertLess(openverse_puanla(
            self.aday(
                "ADP ATP cycle",
                url="https://example.org/a.jpg"
            ),
            ["ATP"], "science"
        ), 10)

    def test_boyut(self):
        self.assertLess(openverse_puanla(
            self.aday("ADP ATP cycle", width=50),
            ["ATP"], "science"
        ), 10)



    def test_evrensel_kabul(self):
        ornekler = [
            ("astronomy", "Venus", "Venus planet NASA photograph"),
            ("animal", "African elephant", "African elephant wildlife photograph"),
            ("plant", "Sunflower", "Sunflower botanical photograph"),
            ("person", "Albert Einstein", "Albert Einstein portrait"),
            ("technology", "Steam engine", "Steam engine photograph"),
            ("city", "Paris", "Paris city skyline"),
            ("landmark", "Eiffel Tower", "Eiffel Tower photograph"),
            ("water", "Atlantic Ocean", "Atlantic Ocean waves"),
            ("event", "Apollo 11", "Apollo 11 historical photograph"),
            ("unknown", "Violin", "Violin musical instrument"),
        ]

        for tur, konu, baslik in ornekler:
            with self.subTest(tur=tur):
                self.assertGreaterEqual(
                    openverse_puanla(
                        self.aday(baslik), [konu], tur
                    ), 10
                )

    def test_evrensel_yanlis_konu(self):
        self.assertLess(
            openverse_puanla(
                self.aday("Mars planet NASA photograph"),
                ["Venus"], "astronomy"
            ), 10
        )

    def test_evrensel_reklam(self):
        for baslik in [
            "Violin tattoo",
            "Violin shirt",
            "Violin toy",
            "Violin advertisement"
        ]:
            with self.subTest(baslik=baslik):
                self.assertLess(
                    openverse_puanla(
                        self.aday(baslik),
                        ["Violin"], "unknown"
                    ), 10
                )

    def test_evrensel_guvenlik(self):
        for ek in [
            {"license": "unknown"},
            {"creator": ""},
            {"width": 50},
            {"url": "https://example.org/a.jpg"}
        ]:
            with self.subTest(ek=ek):
                self.assertLess(
                    openverse_puanla(
                        self.aday(
                            "Venus NASA photograph", **ek
                        ),
                        ["Venus"], "astronomy"
                    ), 10
                )

    def test_person_namesake(self):
        for title in ["Ariane 5 / ATV-4 Albert Einstein", "Albert Einstein - Beach view 3", "Ferb Fletcher vs. Albert Einstein", "Albert Einstein - Start 3"]:
            self.assertLess(openverse_puanla(self.aday(title), ["Albert Einstein"], "person"), 10)
        self.assertGreaterEqual(openverse_puanla(self.aday("The face of Albert Einstein"), ["Albert Einstein"], "person"), 10)

if __name__ == "__main__":
    unittest.main()
