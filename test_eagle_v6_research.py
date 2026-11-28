import unittest
from eagle_arastirma_motoru_v6 import research_answer


def source(url, text, loaded=True):
    return {
        "title": "Mitokondri",
        "url": url,
        "snippet": text,
        "content_loaded": loaded
    }


class ResearchTests(unittest.TestCase):

    def test_extra_search(self):
        calls = []

        def searcher(q):
            calls.append(q)
            return [
                source(
                    "https://example.edu/biology",
                    "Mitokondri hücrede enerji üretir."
                )
            ]

        result, rows = research_answer(
            "Mitokondri nedir?",
            [
                source(
                    "https://tr.wikipedia.org/wiki/Mitokondri",
                    "Mitokondri bir organeldir."
                )
            ],
            searcher
        )

        self.assertTrue(result["ok"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(rows), 2)
        self.assertTrue(result["research_extra_search"])
        self.assertIn("enerji", result["answer"])

    def test_unread_source(self):
        result, rows = research_answer(
            "Mitokondri nedir?",
            [],
            lambda q: [
                source(
                    "https://example.org/test",
                    "Mitokondri bir organeldir.",
                    False
                )
            ]
        )

        self.assertFalse(result["ok"])

    def test_provider_failure(self):
        def searcher(q):
            raise TimeoutError()

        result, rows = research_answer(
            "Mitokondri nedir?",
            [
                source(
                    "https://example.org/biology",
                    "Mitokondri bir organeldir."
                )
            ],
            searcher
        )

        self.assertTrue(result["ok"])

    def test_duplicate_source(self):
        row = source(
            "https://example.org/biology",
            "Mitokondri bir organeldir."
        )

        result, rows = research_answer(
            "Mitokondri nedir?",
            [row],
            lambda q: [row, row]
        )

        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
