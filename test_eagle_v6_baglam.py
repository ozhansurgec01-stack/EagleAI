import unittest
from eagle_arastirma_motoru_v6 import build_answer


def cevap(konu, metin):
    sonuc = build_answer(
        konu + " nedir?",
        [{
            "title": konu,
            "url": "https://tr.wikipedia.org/wiki/" + konu,
            "content_loaded": True,
            "topic_aliases": [konu],
            "snippet": metin
        }]
    )
    return sonuc.get("answer", "")


class BaglamTest(unittest.TestCase):

    def test_gezegen_gecisi(self):
        r = cevap(
            "Venüs",
            "Venüs bir gezegendir. "
            "Mars gezegeni iki doğal uyduya sahiptir. "
            "Yüzeyi demir oksit içerir."
        )
        self.assertIn("Venüs bir gezegendir.", r)
        self.assertNotIn("doğal uyduya", r)
        self.assertNotIn("demir oksit", r)

    def test_ulke_gecisi(self):
        r = cevap(
            "Kanada",
            "Kanada bir ülkedir. "
            "Fransa ülkesi Avrupa kıtasında bulunur. "
            "Başkenti Paris şehridir."
        )
        self.assertIn("Kanada bir ülkedir.", r)
        self.assertNotIn("Avrupa", r)
        self.assertNotIn("Paris", r)

    def test_gecerli_baglam(self):
        r = cevap(
            "Mitokondri",
            "Mitokondri bir organeldir. "
            "İç zarı kıvrımlı bir yapıya sahiptir. "
            "Kendi DNA molekülünü içerir."
        )
        self.assertIn("kıvrımlı", r)
        self.assertIn("DNA", r)

    def test_bilimsel_baglam(self):
        r = cevap(
            "Plüton",
            "Plüton bir cüce gezegendir. "
            "Yüzeyi büyük ölçüde buzla kaplıdır. "
            "Atmosferi oldukça incedir."
        )
        self.assertIn("buzla", r)
        self.assertIn("incedir", r)

    def test_ortuk_ozne(self):
        r = cevap(
            "Fotosentez",
            "Fotosentez, ışık enerjisini kimyasal "
            "enerjiye dönüştüren bir süreçtir. "
            "Temel girdileri su ve karbondioksittir. "
            "Bitkilerde kloroplast içerisinde gerçekleşir."
        )
        self.assertIn("karbondioksit", r)
        self.assertIn("kloroplast", r)




class BaglamSureklilikTest(unittest.TestCase):

    def test_kisa_varlik_gecisi(self):
        r = cevap(
            "Venüs",
            "Venüs bir gezegendir. "
            "Mars kızıldır. "
            "Yüzeyi demir oksit içerir."
        )
        self.assertIn("Venüs bir gezegendir.", r)
        self.assertNotIn("demir oksit", r)

    def test_tursuz_varlik_gecisi(self):
        r = cevap(
            "Venüs",
            "Venüs bir gezegendir. "
            "Mars iki uyduya sahiptir. "
            "Yüzeyi demir oksit içerir."
        )
        self.assertIn("Venüs bir gezegendir.", r)
        self.assertNotIn("demir oksit", r)

    def test_kisa_ulke_gecisi(self):
        r = cevap(
            "Kanada",
            "Kanada bir ülkedir. "
            "Fransa büyüktür. "
            "Başkenti Paris şehridir."
        )
        self.assertIn("Kanada bir ülkedir.", r)
        self.assertNotIn("Paris", r)

if __name__ == "__main__":
    unittest.main()
