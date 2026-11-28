import unittest
from eagle_anlamsal_tur import anlamsal_tur


class AnlamsalGuvenlikTest(unittest.TestCase):

    def test_olumsuzluk(self):
        for metin in [
            "Plüton bir gezegen değildir.",
            "Mars bir yıldız değildir.",
            "Bu bir hayvan değildir."
        ]:
            self.assertEqual(anlamsal_tur(metin), "unknown")

    def test_dolayli_ifadeler(self):
        for metin in [
            "Bir fizikçi tarafından geliştirilmiştir.",
            "Gezegenleri inceleyen bir bilim dalıdır.",
            "Bir hayvanı temsil eden heykeldir.",
            "Bir ülkenin başkentidir."
        ]:
            self.assertEqual(anlamsal_tur(metin), "unknown")

    def test_belirsiz_ve_tarihsel(self):
        for metin in [
            "Eskiden gezegen olarak sınıflandırılmıştır.",
            "Gezegen olduğu iddia edilmektedir.",
            "Muhtemelen bir gezegendir.",
            "Bir yıldız olabilir."
        ]:
            self.assertEqual(anlamsal_tur(metin), "unknown")

    def test_gecerli_tanimlar(self):
        for metin, beklenen in [
            ("Güneş bir yıldızdır.", "star"),
            ("Venüs bir gezegendir.", "planet"),
            ("Ay bir doğal uydudur.", "natural_satellite"),
            ("Keman bir müzik aletidir.", "musical_instrument"),
            ("Python bir programlama dilidir.", "programming_language"),
            ("Bir cüce gezegendir.", "dwarf_planet"),
            ("Python bir yılan cinsidir.", "animal")
        ]:
            with self.subTest(metin=metin):
                self.assertEqual(anlamsal_tur(metin), beklenen)
