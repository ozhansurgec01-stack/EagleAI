import unittest
from eagle_api import _web_sonucu_sorguyla_ilgili_mi

class KisaTerimTest(unittest.TestCase):

    def test_eslesmeler(self):
        cases = [
            ("ATP", "ATP ve enerji", True),
            ("DNA", "DNA yapısı", True),
            ("RNA", "RNA çeşitleri", True),
            ("RAM", "RAM bellek", True),
            ("pH", "pH değeri", True),
            ("UFO", "UFO araştırmaları", True),
            ("ATP", "Atpaz araştırması", False),
            ("ATP", "Futbol haberleri", False),
            ("RAM", "Program geliştirme", False),
            ("RNA", "Turna balığı", False),
            ("ATP", "ATP'nin görevleri", True),
            ("ABD", "United States", True),
            ("ABD", "United Statesman", False),
            ("ABD", "USA", True),
            ("ABD", "United Kingdom", False),
            ("İngiltere", "United Kingdom", True),
            ("İngiltere", "England", True),
            ("İspanya", "Spain", True),
            ("İtalya", "Italy", True),
            ("İngiltere", "Spain", False),
            ("İstanbul", "İstanbul tarihi", True),
        ]

        for term, title, expected in cases:
            with self.subTest(term=term, title=title):
                result = _web_sonucu_sorguyla_ilgili_mi(
                    term + " nedir?",
                    {"title": title, "snippet": ""}
                )
                self.assertEqual(result, expected)

if __name__ == "__main__":
    unittest.main()
