import ast, json, tempfile, unittest
from pathlib import Path

class MemoryTests(unittest.TestCase):
    def test_formats(self):
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        names = {'hafiza_yukle', 'hafiza_kaydet', 'hafiza_ekle', 'sohbet_hafizaya_ekle'}
        code = compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), 'memory', 'exec')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'memory.json'
            env = {'MEMORY_FILE':path,'json':json}
            exec(code,env)
            for initial in (None, [], ['eski'], {'kullanici':None,'sohbet':None}):
                if path.exists(): path.unlink()
                if initial is not None: path.write_text(json.dumps(initial))
                self.assertTrue(env['sohbet_hafizaya_ekle']('soru','cevap'))
                self.assertTrue(env['hafiza_ekle']('yeni'))
                self.assertFalse(env['hafiza_ekle']('yeni'))
                data=env['hafiza_yukle']()
                self.assertIn('yeni',data['kullanici'])
                self.assertEqual(len(data['sohbet']),1)
                if initial == ['eski']: self.assertIn('eski',data['kullanici'])
if __name__ == '__main__': unittest.main()
