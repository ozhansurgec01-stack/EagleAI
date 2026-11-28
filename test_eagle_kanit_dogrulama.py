import unittest
from eagle_kanit_dogrulama import sayisal_imza, celiskileri_bul


def aday(metin, host):
    return {
        "text": metin,
        "host": host,
        "url": "https://" + host + "/bilgi"
    }


class KanitDogrulamaTest(unittest.TestCase):

    def test_celiski(self):
        sonuc = celiskileri_bul([
            aday("Mars'ın iki doğal uydusu vardır.", "a.org"),
            aday("Mars'ın üç doğal uydusu vardır.", "b.org")
        ])
        self.assertEqual(len(sonuc), 1)
        self.assertEqual(sonuc[0]["values"], [2, 3])
        self.assertFalse(sonuc[0]["resolved"])

    def test_uyumlu(self):
        self.assertEqual(celiskileri_bul([
            aday("Kemanın dört teli vardır.", "a.org"),
            aday("Kemanın 4 teli vardır.", "b.org")
        ]), [])

    def test_farkli_ozellikler(self):
        self.assertEqual(celiskileri_bul([
            aday("Aracın dört tekerleği vardır.", "a.org"),
            aday("Aracın iki kapısı vardır.", "b.org")
        ]), [])

    def test_farkli_konular(self):
        self.assertEqual(celiskileri_bul([
            aday("Kemanın dört teli vardır.", "a.org"),
            aday("Gitarın altı teli vardır.", "b.org")
        ]), [])

    def test_ayni_host(self):
        self.assertEqual(celiskileri_bul([
            aday("Kemanın dört teli vardır.", "a.org"),
            aday("Kemanın beş teli vardır.", "a.org")
        ]), [])

    def test_karmasik_sayilar(self):
        for metin in [
            "Uzunluğu 3,5 metredir.",
            "Nüfusu yaklaşık 5 milyondur.",
            "Uzunluğu 2-4 metredir.",
            "En az 3 metre uzunluğundadır."
        ]:
            with self.subTest(metin=metin):
                self.assertIsNone(sayisal_imza(metin))

    def test_genel_kullanim(self):
        for konu, ozellik in [
            ("Gitarın", "teli"),
            ("Aracın", "kapısı"),
            ("Binanın", "katı"),
            ("Robotun", "motoru")
        ]:
            sonuc = celiskileri_bul([
                aday(f"{konu} 4 {ozellik} vardır.", "a.org"),
                aday(f"{konu} 6 {ozellik} vardır.", "b.org")
            ])
            self.assertEqual(len(sonuc), 1)


if __name__ == "__main__":
    unittest.main()
