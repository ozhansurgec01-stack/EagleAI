import unittest

from eagle_anlamsal_tur import (
    anlamsal_tur,
    tur_iliskisi
)


class AnlamsalTurTest(unittest.TestCase):

    def test_turler(self):
        ornekler = [
            ("Cüce gezegendir.", "dwarf_planet"),
            ("Doğal uydudur.", "natural_satellite"),
            ("Gezegendir.", "planet"),
            ("Roma tanrısıdır.", "deity"),
            ("Müzik aletidir.", "musical_instrument"),
            ("Yaylı çalgıdır.", "musical_instrument"),
            ("Fizikçidir.", "scientist"),
            ("Bilim insanıdır.", "scientist"),
            ("Memeli hayvandır.", "animal"),
            ("Satranç taşıdır.", "game_piece"),
            ("Programlama dilidir.", "programming_language"),
            ("Yılan cinsidir.", "animal"),
            ("Kimyasal elementtir.", "chemical_element"),
            ("Kimyasal bileşiktir.", "chemical_compound"),
            ("Bir ülkedir.", "country"),
            ("Büyük bir şehirdir.", "city"),
        ]

        for metin, beklenen in ornekler:
            with self.subTest(metin=metin):
                self.assertEqual(
                    anlamsal_tur(metin), beklenen
                )

    def test_belirsizlik(self):
        self.assertEqual(
            anlamsal_tur("Çok önemli bir varlıktır."),
            "unknown"
        )

    def test_birden_fazla_tur(self):
        self.assertEqual(
            anlamsal_tur("Gezegen ve doğal uydu."),
            "unknown"
        )

    def test_uyumlu(self):
        self.assertEqual(
            tur_iliskisi("scientist", "scientist"),
            "compatible"
        )

    def test_farkli_tur(self):
        self.assertEqual(
            tur_iliskisi("planet", "natural_satellite"),
            "different_type"
        )

    def test_bilinmeyen(self):
        self.assertEqual(
            tur_iliskisi("unknown", "animal"),
            "undetermined"
        )


if __name__ == "__main__":
    unittest.main()
