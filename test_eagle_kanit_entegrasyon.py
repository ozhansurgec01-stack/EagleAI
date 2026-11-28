import unittest

from eagle_arastirma_motoru_v6 import build_answer


def kaynak(konu, host, metin):
    return {
        "title": konu,
        "url": "https://" + host + "/bilgi",
        "snippet": metin,
        "content_loaded": True,
        "topic_aliases": [konu]
    }


class KanitEntegrasyonTest(unittest.TestCase):

    def test_celiskili_bilgi_engellenir(self):
        tanim = "Mars, Güneş Sistemi'nin dördüncü gezegenidir. "

        sonuc = build_answer("Mars hakkında bilgi", [
            kaynak(
                "Mars", "a.edu",
                tanim + "Mars'ın iki doğal uydusu bulunmaktadır."
            ),
            kaynak(
                "Mars", "b.org",
                tanim + "Mars'ın üç doğal uydusu bulunmaktadır."
            )
        ])

        self.assertTrue(sonuc["ok"])
        self.assertEqual(
            sonuc["research_status"],
            "unresolved_conflicts"
        )
        self.assertEqual(
            sonuc["research_conflicts"][0]["values"],
            [2, 3]
        )
        self.assertNotIn("iki doğal uydusu", sonuc["answer"])
        self.assertNotIn("üç doğal uydusu", sonuc["answer"])
        self.assertIn("dördüncü gezegenidir", sonuc["answer"])

    def test_uyumlu_bilgi_korunur(self):
        tanim = "Keman, yaylı bir müzik aletidir. "

        sonuc = build_answer("Keman nedir?", [
            kaynak(
                "Keman", "a.edu",
                tanim + "Kemanın dört teli vardır."
            ),
            kaynak(
                "Keman", "b.org",
                tanim + "Kemanın 4 teli vardır."
            )
        ])

        self.assertTrue(sonuc["ok"])
        self.assertEqual(sonuc["research_conflicts"], [])
        self.assertIn("dört teli", sonuc["answer"])

    def test_tek_kaynak_korunur(self):
        sonuc = build_answer("Keman nedir?", [
            kaynak(
                "Keman", "a.edu",
                "Keman, yaylı bir müzik aletidir. "
                "Kemanın dört teli vardır."
            )
        ])

        self.assertTrue(sonuc["ok"])
        self.assertEqual(sonuc["research_conflicts"], [])
        self.assertIn("dört teli", sonuc["answer"])


if __name__ == "__main__":
    unittest.main()
