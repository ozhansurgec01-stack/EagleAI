import unittest
from eagle_arastirma_niyeti import anlati_istegi_mi, arastirma_karari
from eagle_ana_koordinator import EagleAnaKoordinator
from eagle_merkez_motoru import EagleMerkezMotoru

class ResearchTests(unittest.TestCase):
    def test_narrative(self):
        for q in ['Bolivya UFO olayı', "Bolivya’da görülen UFO’yu anlatır mısın bana", 'Titanik batışını başından sonuna anlat', 'Franz Kafka başka ilginç bir olayı anlat', 'Kafka hikâyesi']:
            with self.subTest(q=q):
                self.assertTrue(anlati_istegi_mi(q))
                self.assertEqual(EagleMerkezMotoru.genel_web_cevabi(q, []), ('', 0.0))
    def test_chat(self):
        for q in ['Merhaba', 'Bugün nasılsın', 'Bugün çok yoruldum', 'En son UFO nerede görüldü']:
            self.assertFalse(anlati_istegi_mi(q))
    def test_coordinator(self):
        calls = []
        def chat(*args):
            calls.append('chat'); return {'ok': True, 'cevap': 'chat'}
        def research(*args):
            calls.append('research'); return {'ok': True, 'cevap': 'research'}
        c = EagleAnaKoordinator(uzman_motorlari={'genel_sohbet': chat})
        old = {'arac': 'eagle_sohbet', 'intent': 'basit_sohbet', 'komut': 'kisa'}
        new = arastirma_karari(old, True)
        self.assertEqual(new['komut'], 'kisa')
        self.assertEqual(old['arac'], 'eagle_sohbet')
        self.assertEqual(c.calistir('Bolivya UFO olayı', karar=new, uzman_calistir=research)['cevap'], 'research')
        self.assertEqual(c.calistir('Merhaba', karar=arastirma_karari(old, False), uzman_calistir=research)['cevap'], 'chat')
        self.assertEqual(calls, ['research', 'chat'])
    def test_specialist(self):
        old = {'arac': 'guvenli_hesaplama', 'intent': 'matematik'}
        self.assertEqual(arastirma_karari(old, True), old)

if __name__ == '__main__': unittest.main()
