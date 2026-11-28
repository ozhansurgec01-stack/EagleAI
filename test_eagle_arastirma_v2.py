import unittest
from eagle_arastirma_v2 import konu_ayir, ansiklopedi_kaynaklari

class Response:
    status_code = 200
    def json(self):
        return {"query":{"pages":[{"title":"Venüs","pageid":123,"extract":"Venüs bir gezegendir. " * 10}]}}

class ResearchTests(unittest.TestCase):
    def test_variants(self):
        self.assertEqual(konu_ayir("Venüs hakkında bilgi verirmisin"), "Venüs")
        self.assertEqual(konu_ayir("Plüton ile ilgili bilgi verir misin?"), "Plüton")
        self.assertEqual(konu_ayir("Fotosentez nedir?"), "Fotosentez")
        self.assertEqual(konu_ayir("100 dolar kaç TL"), "")
    def test_exact(self):
        self.assertEqual(len(ansiklopedi_kaynaklari("Venüs nedir", get=lambda *a, **k: Response())), 1)
        self.assertEqual(ansiklopedi_kaynaklari("Plüton nedir", get=lambda *a, **k: Response()), [])
    def test_rate_limit(self):
        response = Response()
        response.status_code = 429
        self.assertEqual(ansiklopedi_kaynaklari("Venüs nedir", get=lambda *a, **k: response), [])

if __name__ == "__main__":
    unittest.main()
