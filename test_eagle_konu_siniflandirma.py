import unittest
from eagle_konu_siniflandirma import siniflandir


class KonuSiniflandirmaTest(unittest.TestCase):

    def test_genel_kategoriler(self):
        ornekler = [
            ("Venüs", "planet", "astronomy"),
            ("Plüton", "dwarf planet", "astronomy"),
            ("Fil", "species of mammal", "animal"),
            ("Aslan", "species of large cat", "animal"),
            ("Ayçiçeği", "flowering plant", "plant"),
            ("Albert Einstein", "theoretical physicist", "person"),
            ("Atatürk", "military officer and statesman", "person"),
            ("Buhar makinesi", "heat engine", "technology"),
            ("Keman", "musical instrument", "object"),
            ("Eyfel Kulesi", "tower in Paris", "landmark"),
            ("Kanada", "country in North America", "country"),
            ("Madagaskar", "island country", "country"),
            ("Singapur", "sovereign city-state", "country"),
            ("Paris", "capital city of France", "city"),
            ("Atlas Okyanusu", "ocean", "water"),
            ("Mitokondri", "cell organelle", "science"),
            ("ATP", "chemical molecule", "science"),
            ("Bilinmeyen kavram", "", "unknown"),
        ]

        for konu, aciklama, beklenen in ornekler:
            with self.subTest(konu=konu):
                self.assertEqual(
                    siniflandir(konu, aciklama=aciklama),
                    beklenen
                )

    def test_yeni_konular(self):
        ornekler = [
            ("Jaguar", "species of mammal", "animal"),
            ("Orkide", "flowering plant", "plant"),
            ("Nikola Tesla", "inventor and engineer", "person"),
            ("Mikroislemci", "computer processor", "technology"),
            ("Gitar", "musical instrument", "object"),
            ("Galata Kulesi", "historic tower", "landmark"),
            ("Monako", "sovereign city-state", "country"),
        ]

        for konu, aciklama, beklenen in ornekler:
            with self.subTest(konu=konu):
                self.assertEqual(
                    siniflandir(konu, aciklama=aciklama),
                    beklenen
                )

    def test_tarihsel_oncelik(self):
        self.assertEqual(
            siniflandir("Tarihsel olay", tarihsel=True),
            "event"
        )

    def test_bilinmeyen_konu(self):
        self.assertEqual(
            siniflandir("XYZ123"),
            "unknown"
        )


if __name__ == "__main__":
    unittest.main()
