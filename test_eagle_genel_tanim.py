import unittest
from eagle_merkez_motoru import EagleMerkezMotoru


class GenelTanimTests(unittest.TestCase):

    def test_turkce_tanimlar(self):
        testler = [
            ("Difüzyon", "Difüzyon (Geçişme veya yayılma olarak da bilinir.), maddelerin çok yoğun ortamdan az yoğun ortama doğru kendiliğinden yayılmasıdır."),
            ("Yoğuşma", "Yoğuşma, gaz halindeki bir maddenin sıvı hale dönüşmesidir."),
            ("Erozyon", "Erozyon, toprağın su ve rüzgar etkisiyle aşınması ve taşınmasıdır."),
            ("Kristalleşme", "Kristalleşme, atomların düzenli bir yapı içerisinde bir araya gelmesidir."),
            ("Buharlaşma", "Buharlaşma, sıvı haldeki maddenin gaz haline geçmesidir.")
        ]

        for konu, metin in testler:
            with self.subTest(konu=konu):
                cevap, guven = EagleMerkezMotoru.genel_web_cevabi(
                    konu + " nedir",
                    [{
                        "title": konu,
                        "url": "https://example.org/test",
                        "snippet": metin
                    }]
                )

                self.assertTrue(cevap)
                self.assertGreaterEqual(guven, 0.75)

    def test_birlesik_ve_alternatif_tanimlar(self):
        cases = [
            ("Kara delik", "Kara delik", "Kara delik, ışığın bile kaçamayacağı kadar güçlü kütleçekimine sahip bir uzay-zaman bölgesidir."),
            ("Kuantum fiziği", "Kuantum mekaniği", "Kuantum mekaniği veya kuantum fiziği, atomların ve atom altı parçacıkların davranışlarını inceleyen bir fizik dalıdır."),
            ("Yer çekimi", "Yerçekimi", "Yerçekimi, cisimlerin Dünya’ya doğru ivmelenmesine neden olan fiziksel bir etkidir."),
            ("Ekoloji", "Ekoloji", "Ekoloji, canlıların birbirleriyle ve çevreleriyle ilişkilerini inceleyen bilim dalıdır."),
            ("Atmosfer", "Atmosfer", "Atmosfer, bir gök cismini çevreleyen gaz tabakasıdır."),
        ]
        for konu, baslik, metin in cases:
            with self.subTest(konu=konu):
                cevap, _ = EagleMerkezMotoru.genel_web_cevabi(konu + " nedir", [{
                    "title": baslik, "snippet": metin, "content_loaded": True,
                    "topic_aliases": [konu, baslik],
                    "url": "https://tr.wikipedia.org/"
                }])
                self.assertEqual(cevap, metin)


if __name__ == "__main__":
    unittest.main()
