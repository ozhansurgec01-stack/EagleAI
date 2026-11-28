import unittest
from eagle_arastirma_motoru_v6 import build_answer

class SourcePolicyTests(unittest.TestCase):
    def row(self, url, text, title='Venüs'):
        return dict(url=url, title=title, snippet=text, content_loaded=True)

    def test_untrusted_details_excluded(self):
        r = build_answer('Venüs nedir?', [self.row('https://tr.wikipedia.org/a', 'Venüs bir gezegendir.'), self.row('https://example.com/a', 'Venüs kendine ait fizistrospedi parçalama ve trospinakolitan perazmına sahiptir.')])
        self.assertTrue(r['ok'])
        self.assertNotIn('fizistrospedi', r['answer'])

    def test_malformed_metadata_and_context(self):
        r = build_answer("Plüton'u anlat", [self.row('https://tr.wikipedia.org/a', 'Plüton (küçük gezegen tanımı: 134340 Pluto; sembolleri: veya), Kuiper Kuşağı içinde bulunan bir cüce gezegendir. Bu tanımlamaya göre Plüton yanlış bir sınıfa dahil edilmiştir.', 'Plüton')])
        self.assertTrue(r['ok'])
        self.assertIn('cüce gezegendir', r['answer'])
        self.assertNotIn('sembolleri', r['answer'])
        self.assertNotIn('yanlış bir sınıfa', r['answer'])

    def test_unknown_source_only_definition(self):
        r = build_answer('Venüs nedir?', [self.row('https://example.com/a', 'Venüs bir gezegendir. Venüs çok sayıda özelliğe sahiptir.')])
        self.assertTrue(r['ok'])
        self.assertEqual(len(r['research_evidence']), 1)
