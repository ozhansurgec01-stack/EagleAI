import unittest
from eagle_arastirma_motoru_v5 import build_answer
class Tests(unittest.TestCase):
    def row(self,title,text,url='https://example.edu/a',**kw):
        return dict(title=title,snippet=text,url=url,content_loaded=True,**kw)
    def test_authority(self):
        a=self.row('Mitoz','Mitoz, hücre çekirdeğinin bölünmesiyle ilgili bir süreçtir.')
        b=self.row('Mitoz','Mitoz, hücre döngüsünün çok kısa bir parçasıdır.', 'https://example.com/a')
        self.assertIn(a['snippet'],build_answer('Mitoz nedir',[b,a])['answer'])
    def test_side(self):
        self.assertFalse(build_answer('DNA nedir',[self.row('DNA',"DNA'nın başlıca rolü bilgiyi uzun süre saklamasıdır.")])['ok'])
    def test_alias(self):
        a=self.row('Kuantum mekaniği','Kuantum mekaniği, fiziksel sistemleri inceleyen bir fizik dalıdır.','https://tr.wikipedia.org/?curid=1',topic_aliases=['Kuantum fiziği','Kuantum mekaniği'])
        self.assertTrue(build_answer('Kuantum fiziği nedir',[a])['ok'])
    def test_unread(self):
        a=self.row('Ekoloji','Ekoloji, canlıların çevreyle ilişkilerini inceleyen bilim dalıdır.'); a['content_loaded']=False
        self.assertFalse(build_answer('Ekoloji nedir',[a])['ok'])
    def test_unrelated(self):
        self.assertFalse(build_answer('Kara delik nedir',[self.row('Delik','Delik, herhangi bir yüzeyde bulunan açıklıktır.')])['ok'])
