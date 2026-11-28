import unittest
from eagle_arastirma_motoru_v6 import build_answer

class VerificationTest(unittest.TestCase):
    def test_copied_text_is_not_independent(self):
        text = 'Ekoloji canlıların çevreyle ilişkilerini inceleyen bilim dalıdır.'
        rows = [dict(title='Ekoloji', snippet=text, url=url, content_loaded=True) for url in ['https://example.edu/a','https://example.org/b']]
        r = build_answer('Ekoloji nedir?', rows)
        self.assertTrue(r['ok'])
        self.assertEqual(r['research_verification']['matching_text_count'], 1)
        self.assertEqual(r['research_verification']['independently_verified_count'], 0)
        self.assertEqual(r['research_evidence'][0]['verification_status'], 'matching_text_only')
    def test_single_source(self):
        r = build_answer('Ekoloji nedir?', [dict(title='Ekoloji', snippet='Ekoloji canlıların çevreyle ilişkilerini inceleyen bilim dalıdır.', url='https://example.edu/a', content_loaded=True)])
        self.assertEqual(r['research_evidence'][0]['verification_status'], 'single_source')
        self.assertEqual(r['research_verification']['matching_text_count'], 0)
