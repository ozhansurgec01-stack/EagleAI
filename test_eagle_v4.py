import unittest
from eagle_arastirma_v2 import kaynakli_tanim
class V4Tests(unittest.TestCase):
    def test_source_preference(self):
        def k(url, text): return dict(url=url, snippet=text, content_loaded=True)
        rows=[k('https://example.org/a','Mitoz, hücrelerin bölünmesiyle ilgili bir olaydır.'), k('https://example.edu.tr/a','Mitoz, ökaryot hücrelerde çekirdeğin bölünmesiyle gerçekleşen bir süreçtir.')]
        c,s=kaynakli_tanim('Mitoz nedir',rows)
        self.assertEqual(c,rows[1]['snippet']); self.assertEqual(s[0]['url'],rows[1]['url'])
    def test_reject(self):
        for text in ['DNA’nın başlıca rolü bilgiyi uzun süre saklamasıdır.', 'DNA birçok deney ve çalışmayla kanıtlanmıştır.']:
            self.assertEqual(kaynakli_tanim('DNA nedir',[dict(url='https://example.org',snippet=text,content_loaded=True)]),('',[]))
    def test_unread(self):
        self.assertEqual(kaynakli_tanim('DNA nedir',[dict(url='https://example.org',snippet='DNA, genetik bilgiyi taşıyan bir moleküldür.')]),('',[]))
