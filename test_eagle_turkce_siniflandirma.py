import unittest

from eagle_konu_siniflandirma import (
    siniflandir,
    tur_sozcugu_var
)


class TurkceSiniflandirmaTest(unittest.TestCase):

    def test_canli_hatalar(self):
        for konu, tanim, beklenen in [
            ("Aslan", "Buyuk bir kedidir.", "animal"),
            ("Ayçiçeği", "Bir tarım bitkisidir.", "plant"),
            ("Buhar makinesi", "Yanmalı motordur.", "technology"),
            ("Keman", "Yaylı çalgılar ailesinin üyesidir.", "object"),
            ("Venüs", "İkinci sıradaki gezegendir.", "astronomy")
        ]:
            with self.subTest(konu=konu):
                self.assertEqual(
                    siniflandir(konu, aciklama=tanim),
                    beklenen
                )

    def test_farkli_konular(self):
        for konu, tanim, beklenen in [
            ("Leopar", "Yırtıcı bir kedidir.", "animal"),
            ("Lale", "Süs bitkisidir.", "plant"),
            ("Piyano", "Tuşlu bir çalgıdır.", "object"),
            ("Neptün", "Bir gezegendir.", "astronomy"),
            ("Dizel", "İçten yanmalı bir motordur.", "technology"),
            ("Ribozom", "Hücre organellerinden biridir.", "science")
        ]:
            with self.subTest(konu=konu):
                self.assertEqual(
                    siniflandir(konu, aciklama=tanim),
                    beklenen
                )

    def test_yanlis_kok_eslesmesi(self):
        for metin, kok in [
            ("motorlu", "motor"),
            ("gezegenimsi", "gezegen"),
            ("bitkisel", "bitki"),
            ("kedigiller", "kedi"),
            ("kalem", "kale")
        ]:
            with self.subTest(metin=metin):
                self.assertFalse(
                    tur_sozcugu_var(metin, [kok])
                )


if __name__ == "__main__":
    unittest.main()
