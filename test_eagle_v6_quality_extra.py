import unittest
from eagle_arastirma_motoru_v6 import redundant_fact, research_answer

class ExtraQuality(unittest.TestCase):
    def test_birth_repeat(self):
        a = 'Albert Einstein (14 Mart 1879 - 18 Nisan 1955), Almanya doğumlu teorik fizikçi ve bilim adamı.'
        self.assertTrue(redundant_fact(a, 'Albert Einstein, 1879 senesinde Almanya’da dünyaya gelmiştir.'))
        self.assertFalse(redundant_fact(a, 'Albert Einstein, 1879 yılında Ulm’da doğdu.'))
    def test_generator_failure(self):
        def broken(q):
            raise TimeoutError()
            yield None
        row = dict(title='Mitokondri', snippet='Mitokondri bir organeldir.', url='https://example.org/a', content_loaded=True)
        result, _ = research_answer('Mitokondri nedir?', [row], broken)
        self.assertTrue(result['ok'])
