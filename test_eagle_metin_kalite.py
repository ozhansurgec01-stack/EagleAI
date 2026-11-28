import unittest

from eagle_arastirma_motoru_v6 import quality


class MetinKaliteTest(unittest.TestCase):

    def test_gecerli_bilgiler(self):
        metinler = [
            "Venüs, Güneş Sistemi'nin ikinci gezegenidir.",
            "Plüton, Kuiper Kuşağı'nda bulunan bir cüce gezegendir.",
            "Mitokondri, hücrede enerji üretiminde görev alan bir organeldir.",
            "Keman, yaylı çalgılar ailesinin bir üyesidir.",
            "Su (H2O), hidrojen ve oksijenden oluşur.",
            "Mars'ın iki doğal uydusu vardır: Phobos ve Deimos.",
            "ATP (adenozin trifosfat), hücrelerde enerji aktarımında görev alır.",
        ]

        for metin in metinler:
            with self.subTest(metin=metin):
                self.assertTrue(quality(metin))

    def test_seo_basliklari(self):
        metinler = [
            "Venüs Gezegeni Hakkında Bilgi; Genel ve Fiziksel Özellikleri, Tarihçesi Güneş Sistemi'nde yer alır.",
            "Kanada Hakkında Bilgi: Genel Özellikleri ve Tarihçesi Kanada bir ülkedir.",
            "Keman Hakkında Her Şey: Keman yaylı bir çalgıdır.",
            "Mars hakkında bilmeniz gerekenler: Mars bir gezegendir.",
        ]

        for metin in metinler:
            with self.subTest(metin=metin):
                self.assertFalse(quality(metin))

    def test_bozuk_metinler(self):
        metinler = [
            "Plüton, sembolleri: veya ), Kuiper Kuşağı'nda bulunur.",
            "Venüs, Güneş Sistemi'nin ikinci gezegenidir (",
            "Su (H2O, hidrojen ve oksijenden oluşur.",
            "Mars [gezegen), Güneş Sistemi'nde bulunur.",
            "Keman, yaylı bir müzik aletidir...",
            "Mitokondri, hücrede enerji",
        ]

        for metin in metinler:
            with self.subTest(metin=metin):
                self.assertFalse(quality(metin))

    def test_reklam_ve_gereksiz_metinler(self):
        metinler = [
            "Bu yazımızda Venüs hakkında merak edilenleri anlatıyoruz.",
            "Venüs hakkında detaylı bilgi almak için tıklayın.",
            "Tüm hakları saklıdır.",
        ]

        for metin in metinler:
            with self.subTest(metin=metin):
                self.assertFalse(quality(metin))


if __name__ == "__main__":
    unittest.main()
