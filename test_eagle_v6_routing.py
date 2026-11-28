import ast
import unittest
from pathlib import Path
from eagle_arastirma_niyeti import arastirma_karari
from eagle_arastirma_motoru_v5 import topic
from eagle_arastirma_motoru_v6 import quality

class V6Routing(unittest.TestCase):
    def test_promoted_intent_reaches_v6_gate(self):
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        gates = [n for n in ast.walk(tree) if isinstance(n, ast.If) and any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == 'research_answer' for x in ast.walk(ast.Module(body=n.body, type_ignores=[]))) and 'arastirma_konusu' in ast.unparse(n.test)]
        self.assertEqual(len(gates), 1)
        gate = gates[0].test
        class Motor:
            def genel_web_ulke_token_eslesiyor(self, a, b): return False
        for intent, arac in [('sohbet','eagle_sohbet'), ('guncel_bilgi','web_arastirma')]:
            for q in ["Plüton'u anlat", 'Venüs hakkında bilgi ver']:
                env = dict(karar=arastirma_karari(dict(intent=intent, arac=arac), True), arastirma_konusu=topic(q), anlati_istegi=False, mesaj=q, _eagle_guncel_olay_sorgusu=lambda q:False, merkez_motor=Motor())
                self.assertTrue(eval(compile(ast.Expression(gate), '<gate>', 'eval'), env))
    def test_unsupported_universal_and_broken_metadata(self):
        self.assertFalse(quality('Venüs, diğer tüm gezegenlerin aksi istikametinde döner.'))
        self.assertFalse(quality('Plüton (sembolleri: veya), bir cüce gezegendir.'))
        self.assertFalse(quality('Bu yüzden Venüs, Sabah Yıldızı olarak isimlendirilir.'))
        self.assertTrue(quality('Venüs, kendi ekseni etrafında ters yönde döner.'))
