import unittest
from eagle_gorsel_kalite import uygun_mu


class UlkeGorselKaliteTest(unittest.TestCase):

    def test_hdwallpapers(self):
        self.assertFalse(uygun_mu(
            "Banff National Park Canada Mountain Landscape",
            "https://www.hdwallpapers.in/test",
            "country"
        ))

    def test_10wallpaper(self):
        self.assertFalse(uygun_mu(
            "Canada Jasper National Park",
            "https://www.10wallpaper.com/test",
            "country"
        ))

    def test_liste_basligi(self):
        self.assertFalse(uygun_mu(
            "Canadian Architecture: 10 Iconic Buildings",
            "https://archeyes.com/test",
            "country"
        ))

    def test_reklam_basligi(self):
        self.assertFalse(uygun_mu(
            "Alberta Scenery That'll Have You Packing Your Bags",
            "https://readersdigest.ca/test",
            "country"
        ))

    def test_norvec_gecerli(self):
        self.assertTrue(uygun_mu(
            "Trollstigen - Rauma, Norway - Landscape photography",
            "https://www.flickr.com/photos/test",
            "country"
        ))

    def test_kanada_gecerli(self):
        self.assertTrue(uygun_mu(
            "Banff National Park Canada",
            "https://commons.wikimedia.org/test",
            "country"
        ))



    def galeri(self, isimler):
        from eagle_api import _eagle_ulke_gorsel_cesitlendir
        from eagle_gorsel_kalite import normla

        items = [
            {
                "name": x,
                "url": f"https://example.com/{i}.jpg"
            }
            for i, x in enumerate(isimler)
        ]

        return _eagle_ulke_gorsel_cesitlendir(
            items, normla
        )

    def test_farkli_parklar_korunur(self):
        isimler = [
            "North Mountain National Park",
            "South Mountain National Park",
            "Banff National Park",
            "Jasper National Park"
        ]

        sonuc = self.galeri(isimler)

        self.assertEqual(
            {x["name"] for x in sonuc},
            set(isimler)
        )

    def test_sehir_tekrari_engellenir(self):
        sonuc = self.galeri([
            "Toronto City Skyline",
            "Toronto City Street",
            "Quebec City Architecture"
        ])

        self.assertEqual(len(sonuc), 2)

    def test_cok_kelimeli_sehirler(self):
        sonuc = self.galeri([
            "New York City Skyline",
            "New York City Street",
            "York City Skyline",
            "Mexico City Architecture"
        ])

        self.assertEqual(
            {x["name"] for x in sonuc},
            {
                "New York City Skyline",
                "York City Skyline",
                "Mexico City Architecture"
            }
        )

if __name__ == "__main__":
    unittest.main()
