import unittest
from eagle_arastirma_motoru_v6 import build_answer


class V6Tests(unittest.TestCase):

    def row(self, title, text, url=None):
        return {
            "title": title,
            "snippet": text,
            "url": url or "https://example.edu/a",
            "content_loaded": True
        }

    def test_function_priority(self):
        row = self.row(
            "Mitokondri",
            "Mitokondri, hücre organellerinden biridir. "
            "Mitokondri hücrede ATP üretimini sağlar. "
            "Mitokondri çift zarlı bir yapıya sahiptir."
        )
        result = build_answer(
            "Mitokondri nedir?", [row]
        )
        self.assertTrue(result["ok"])
        self.assertIn("ATP", result["answer"])
        self.assertEqual(
            result["research_evidence"][1]["category"],
            "function"
        )

    def test_subjective_noise(self):
        row = self.row(
            "Kuantum fiziği",
            "Kuantum fiziği temel bir fizik dalıdır. "
            "Kuantum fiziği göz korkutucu bir sahadır."
        )
        result = build_answer(
            "Kuantum fiziği nedir?", [row]
        )
        self.assertTrue(result["ok"])
        self.assertNotIn(
            "göz korkutucu", result["answer"]
        )

    def test_dependent_sentence(self):
        row = self.row(
            "Fotosentez",
            "Fotosentez biyokimyasal bir süreçtir. "
            "Çünkü fotosentez yapan canlılar vardır."
        )
        result = build_answer(
            "Fotosentez nedir?", [row]
        )
        self.assertTrue(result["ok"])
        self.assertNotIn("Çünkü", result["answer"])

    def test_unread_source(self):
        row = self.row(
            "Ekoloji",
            "Ekoloji canlıları inceleyen bilim dalıdır."
        )
        row["content_loaded"] = False
        self.assertFalse(
            build_answer("Ekoloji nedir?", [row])["ok"]
        )

    def test_unrelated_source(self):
        row = self.row(
            "Delik",
            "Delik bir yüzeyde bulunan açıklıktır."
        )
        self.assertFalse(
            build_answer("Kara delik nedir?", [row])["ok"]
        )

    def test_matching_sources(self):
        text = (
            "Ekoloji canlıların çevreyle ilişkilerini "
            "inceleyen bilim dalıdır."
        )
        result = build_answer(
            "Ekoloji nedir?",
            [
                self.row("Ekoloji", text),
                self.row(
                    "Ekoloji", text,
                    "https://example.org/b"
                )
            ]
        )
        self.assertTrue(result["ok"])
        evidence = result["research_evidence"][0]
        self.assertTrue(evidence["matching_text_sources"])
        self.assertFalse(evidence["independently_verified"])

    def test_general_information(self):
        row = self.row(
            "Atlas Okyanusu",
            "Atlas Okyanusu dünyanın ikinci büyük "
            "okyanusudur."
        )
        result = build_answer(
            "Atlas Okyanusu hakkında bilgi ver", [row]
        )
        self.assertTrue(result["ok"])


    def test_definition_priority(self):
        cases = {
            "ATP": "ATP, hücrelerde enerji aktarımında kullanılan bir moleküldür.",
            "Ribozom": "Ribozom, protein sentezinin gerçekleştiği hücresel bir yapıdır."
        }
        for name, text in cases.items():
            with self.subTest(name=name):
                r = build_answer(
                    name + " nedir?",
                    [self.row(name, text)]
                )
                self.assertTrue(r["ok"])
                self.assertEqual(
                    r["research_evidence"][0]["category"],
                    "definition"
                )

    def test_property_preserved(self):
        row = self.row(
            "Mitokondri",
            "Mitokondri, hücre organellerinden biridir. "
            "Mitokondri hücrede ATP üretimini sağlar. "
            "Mitokondri çift zarlı bir yapıya sahiptir."
        )
        r = build_answer("Mitokondri nedir?", [row])
        self.assertTrue(r["ok"])
        self.assertIn("ATP", r["answer"])
        self.assertIn("çift zarlı", r["answer"])


if __name__ == "__main__":
    unittest.main()
