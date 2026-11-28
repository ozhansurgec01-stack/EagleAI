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


class AnlamsalEntegrasyonTest(unittest.TestCase):

    def test_farkli_astronomi_turleri(self):
        sonuc = build_answer("Plüton nedir?", [
            kaynak("Plüton", "a.edu",
                   "Plüton bir cüce gezegendir."),
            kaynak("Plüton", "b.org",
                   "Plüton bir doğal uydudur.")
        ])
        self.assertFalse(sonuc["ok"])
        self.assertEqual(
            sonuc["research_status"],
            "entity_type_uncertain"
        )
        self.assertEqual(
            set(sonuc["research_entity_types"]),
            {"dwarf_planet", "natural_satellite"}
        )

    def test_ayni_isimli_kavramlar(self):
        sonuc = build_answer("Python nedir?", [
            kaynak("Python", "a.edu",
                   "Python bir programlama dilidir."),
            kaynak("Python", "b.org",
                   "Python bir yılan cinsidir.")
        ])
        self.assertFalse(sonuc["ok"])
        self.assertEqual(
            sonuc["research_status"],
            "entity_type_uncertain"
        )

    def test_uyumlu_tanimlar(self):
        sonuc = build_answer("Keman nedir?", [
            kaynak("Keman", "a.edu",
                   "Keman bir müzik aletidir."),
            kaynak("Keman", "b.org",
                   "Keman yaylı bir çalgıdır.")
        ])
        self.assertTrue(sonuc["ok"])

    def test_tek_tur(self):
        sonuc = build_answer("Venüs nedir?", [
            kaynak("Venüs", "a.edu",
                   "Venüs bir gezegendir.")
        ])
        self.assertTrue(sonuc["ok"])

    def test_bilinmeyen_tur_engellenmez(self):
        sonuc = build_answer("Mitokondri nedir?", [
            kaynak("Mitokondri", "a.edu",
                   "Mitokondri hücresel bir organeldir.")
        ])
        self.assertTrue(sonuc["ok"])
