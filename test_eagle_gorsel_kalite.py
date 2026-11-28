import unittest
from eagle_gorsel_kalite import (
    uygun_mu, bilim_turu, bilim_cesitlendir
)


class GorselKaliteTest(unittest.TestCase):

    def test_konut(self):
        self.assertFalse(uygun_mu(
            "Norveç Gölü'ne Bakan Konut tasarladı",
            "", "country"))

    def test_turistik_yer(self):
        self.assertTrue(uygun_mu(
            "Chateau Frontenac National Historic Site",
            "", "country"))

    def test_sinav_sorusu(self):
        self.assertFalse(uygun_mu(
            "Aşağıdaki şekilde mitokondri organeli",
            "", "science"))

    def test_kunduz(self):
        self.assertFalse(uygun_mu(
            "Mitokondri şeması",
            "https://kunduz.com/tr/soru-cozum/",
            "science"))

    def test_bilimsel_sema(self):
        self.assertTrue(uygun_mu(
            "Mitochondria structure diagram",
            "", "science"))

    def test_molekul(self):
        self.assertEqual(
            bilim_turu("ATP 3D balls"),
            "molekul_modeli")

    def test_mikroskop(self):
        self.assertEqual(
            bilim_turu("Mitochondria electron micrograph"),
            "mikroskop")

    def test_cesitlendirme(self):
        items = [
            {"name": "ATP 3D balls", "url": "a", "_score": 90},
            {"name": "ATP 3D spacefill", "url": "b", "_score": 85},
            {"name": "ATP anion 3D balls", "url": "c", "_score": 80},
            {"name": "ATP synthesis mechanism", "url": "d", "_score": 70},
            {"name": "ATP structure diagram", "url": "e", "_score": 60},
        ]
        self.assertEqual(
            [x["url"] for x in bilim_cesitlendir(items)],
            ["a", "d", "e", "b", "c"])


if __name__ == "__main__":
    unittest.main()
