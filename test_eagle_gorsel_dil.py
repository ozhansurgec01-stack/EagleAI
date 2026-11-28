import unittest
from eagle_gorsel_kalite import (
    bilim_dil_tekrarlarini_ayikla
)


class GorselDilTest(unittest.TestCase):

    def aday(self, ad, puan=75):
        return {
            "name": ad,
            "url": "https://example.org/" + ad,
            "_score": puan
        }

    def test_turkce_onceligi(self):
        items = [
            self.aday("Animal mitochondrion diagram as.svg"),
            self.aday("Animal mitochondrion diagram ca.svg"),
            self.aday("Animal mitochondrion diagram en.svg"),
            self.aday("Animal mitochondrion diagram tr.svg"),
            self.aday("Mitochondria electron microscopy.jpg")
        ]

        sonuc = bilim_dil_tekrarlarini_ayikla(items)

        self.assertEqual(len(sonuc), 2)

        self.assertEqual(
            sonuc[0]["name"],
            "Animal mitochondrion diagram tr.svg"
        )

    def test_ingilizce_yedek(self):
        items = [
            self.aday("Cell diagram de.svg"),
            self.aday("Cell diagram en.svg"),
            self.aday("Cell diagram fr.svg")
        ]

        sonuc = bilim_dil_tekrarlarini_ayikla(items)

        self.assertEqual(len(sonuc), 1)
        self.assertEqual(
            sonuc[0]["name"],
            "Cell diagram en.svg"
        )

    def test_farkli_sema_korunur(self):
        items = [
            self.aday("Cell structure en.svg"),
            self.aday("Cell membrane en.svg")
        ]

        self.assertEqual(
            len(bilim_dil_tekrarlarini_ayikla(items)),
            2
        )


if __name__ == "__main__":
    unittest.main()
