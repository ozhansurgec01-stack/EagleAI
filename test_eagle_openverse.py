import unittest
from eagle_openverse import adaylari_ayikla


class OpenverseTest(unittest.TestCase):

    def aday(self, baslik, **kwargs):
        item = {
            "title": baslik,
            "url": "https://live.staticflickr.com/a.jpg",
            "foreign_landing_url": "https://www.flickr.com/photos/test/1",
            "license": "by",
            "creator": "Test Author",
            "width": 800,
            "height": 600,
            "source": "flickr"
        }
        item.update(kwargs)
        return item

    def kontrol(self, baslik, **kwargs):
        return adaylari_ayikla(
            [self.aday(baslik, **kwargs)],
            ["ATP", "adenosine triphosphate"],
            "science"
        )

    def test_alakasiz_atp(self):
        self.assertFalse(self.kontrol(
            "atp in bici con regali per gli occhi"))

    def test_atp_cycle(self):
        self.assertTrue(self.kontrol("ADP ATP cycle"))

    def test_atp_structure(self):
        self.assertTrue(self.kontrol(
            "Structure of Adenosine Triphosphate"))

    def test_atp_datp(self):
        self.assertTrue(self.kontrol("ATP and dATP"))

    def test_lisans(self):
        self.assertFalse(self.kontrol(
            "ATP structure", license="by-nc"))

    def test_yazar(self):
        self.assertFalse(self.kontrol(
            "ATP structure", creator=""))

    def test_svg(self):
        self.assertFalse(self.kontrol(
            "ATP structure",
            url="https://upload.wikimedia.org/a.svg"))

    def test_sahte_host(self):
        self.assertFalse(self.kontrol(
            "ATP structure",
            url="https://live.staticflickr.com.fake.org/a.jpg"))

    def test_kucuk_gorsel(self):
        self.assertFalse(self.kontrol(
            "ATP structure", width=100))

    def test_urun(self):
        self.assertFalse(self.kontrol(
            "ATP structure shirt"))

    def test_mitokondri(self):
        self.assertTrue(adaylari_ayikla(
            [self.aday("Abnormal Mouse Mitochondria")],
            ["mitochondria", "mitochondrion"],
            "science"
        ))

    def test_kaynak_bilgileri(self):
        a = self.kontrol("ATP molecular structure")[0]
        self.assertEqual(a["creator"], "Test Author")
        self.assertEqual(a["license"], "by")
        self.assertEqual(a["provider"], "Openverse")
        self.assertTrue(a["source"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()
