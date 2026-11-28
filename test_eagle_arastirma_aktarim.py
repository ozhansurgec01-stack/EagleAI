import unittest
from eagle_arastirma_v2 import ansiklopedi_tanimi, gorsel_kavram_eslesiyor
from eagle_merkez_motoru import EagleMerkezMotoru

class AktarimTests(unittest.TestCase):
    def test_metadata_and_definition(self):
        for soru, baslik, metin in [
            ('Kuantum fiziği', 'Kuantum mekaniği', 'Kuantum mekaniği veya kuantum fiziği, atom altı parçacıkları inceleyen temel bir fizik dalıdır.'),
            ('Yer çekimi', 'Yerçekimi', 'Yerçekimi (g ile gösterilir), nesnelere aktarılan net ivmedir.'),
            ('Kara delik', 'Kara delik', 'Kara delik, ışığın kaçamadığı bir uzay-zaman bölgesidir.')]:
            with self.subTest(soru=soru):
                kaynak = {'title':baslik,'url':'https://tr.wikipedia.org/?curid=1','snippet':metin+' Bu konu çok ilginçtir.', 'content_loaded':True,'topic_aliases':[soru,baslik]}
                temiz = EagleMerkezMotoru.temizle_web_verisi([kaynak])
                self.assertTrue(temiz[0]['content_loaded'])
                self.assertEqual(temiz[0]['topic_aliases'], [soru,baslik])
                self.assertEqual(ansiklopedi_tanimi(soru+' nedir', temiz),metin)
                self.assertEqual(ansiklopedi_tanimi('Ekoloji nedir', temiz),'')
    def test_gorsel(self):
        self.assertTrue(gorsel_kavram_eslesiyor('Black hole - Messier 87.jpg',['Kara delik','Black hole']))
        self.assertFalse(gorsel_kavram_eslesiyor('Animals water hole.jpg',['Kara delik','Black hole']))
        self.assertFalse(gorsel_kavram_eslesiyor('Quantum computer.jpg',['Quantum mechanics','Kuantum fiziği']))
    def test_yan_bilgi(self):
        k={'url':'https://tr.wikipedia.org/?curid=1','topic_aliases':['Kuantum fiziği'],'content_loaded':True,'snippet':'Kuantum fiziği birçok deney ve çalışmayla ölçülmüş ve kanıtlanmıştır.'}
        self.assertEqual(ansiklopedi_tanimi('Kuantum fiziği nedir',[k]),'')

if __name__ == '__main__': unittest.main()
