import ast
import operator
import re
import unittest
from pathlib import Path
from unittest.mock import patch
import sympy as sp
from eagle_merkez_motoru import EagleMerkezMotoru
from eagle_bilim_hesap import bilim_hesapla

source = Path(__file__).with_name('eagle_api.py').read_text()
tree = ast.parse(source)
ns = dict(ast=ast, operator=operator, re=re, sp=sp)
for node in tree.body:
    if (isinstance(node, ast.FunctionDef) and node.name in ('guvenli_hesapla','sembolik_denklem_coz','eagle_yerel_matematik','_eagle_gundem_sorgusu','eagle_yerel_kavram')) or (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '_GUVENLI_ISLEMLER' for t in node.targets)):
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'api', 'exec'), ns)

class LocalTest(unittest.TestCase):
    def test_math(self):
        for q, expected in [('2 + 3 * 4 kaç eder?', '14'), ('2x + 3 = 7 denklemini çöz','x = 2'), ('x^2 = 9 denklemini çöz','x = -3, x = 3'), ('-5 < -2 doğru mu?', 'Doğru')]:
            self.assertIn(expected, ns['eagle_yerel_matematik'](q))
    def test_science(self):
        for q, expected in [('1500 metre kaç kilometredir?', '1,5 km'), ('Kenarları 5 ve 8 metre olan dikdörtgenin alanı','40 m²'), ('Kütlesi 10 kg ivmesi 3 m/s² olan cismin kuvveti','30 N')]:
            self.assertIn(expected, bilim_hesapla(q))
    def test_news(self):
        for q in ['Türkiye gündeminde bugün neler var?', 'Dünyada bugün neler oluyor?']:
            self.assertTrue(ns['_eagle_gundem_sorgusu'](q))
        self.assertFalse(ns['_eagle_gundem_sorgusu']('Türkiye bugün maçları'))
    def test_country(self):
        self.assertEqual(EagleMerkezMotoru.ulke_tanitim_konusu('Kanada hakkında detaylı bilgi ver'), 'kanada')
    def test_concepts(self):
        f = ns["eagle_yerel_kavram"]
        self.assertIn("Tuple değiştirilemez", f("Python'da liste ve tuple arasındaki fark nedir?"))
        self.assertIn("olay ufku", f("Kara delikler nasıl oluşur?"))
        self.assertIsNone(f("Kara delikler hakkında güncel haberler"))
        self.assertIsNone(f("Python liste ve tuple farkı için program yaz"))
    def test_unrelated(self):
        for q in ['1500 metre atletizm', 'Python x=2', '2026 haberleri']:
            self.assertIsNone(ns['eagle_yerel_matematik'](q))

class ApiTest(unittest.TestCase):
    def test_actual_route(self):
        try:
            from eagle_api import app
        except ModuleNotFoundError as e:
            if e.name == 'flask': self.skipTest('Flask unavailable')
            raise
        with app.test_client() as c, patch('eagle_api.web_arastir', side_effect=AssertionError('Unexpected web search')):
            for q, expected in [('2 + 3 * 4 kaç eder?', '14'), ('2x + 3 = 7 denklemini çöz','x = 2'), ('x^2 = 9 denklemini çöz','x = -3'), ('-5 < -2 doğru mu?', 'Doğru'), ('1500 metre kaç kilometredir?', '1,5 km'), ('Kenarları 5 ve 8 metre olan dikdörtgenin alanı','40 m²'), ('Kütlesi 10 kg ivmesi 3 m/s² olan cismin kuvveti','30 N')]:
                r = c.post('/api/sohbet', json={'message':q})
                self.assertEqual(r.status_code, 200, q)
                self.assertIn(expected, r.get_json()['answer'], q)
                self.assertFalse(r.get_json()['web_search'], q)

class ContextTest(unittest.TestCase):
    def test_followup_skips_acknowledgement(self):
        from eagle_api import eagle_genel_baglam_coz as resolve
        history = [{'role':'user','content':'Kanada hakkında bilgi ver'}, {'role':'assistant','content':'Kanada bir ülkedir.'}, {'role':'user','content':'Tamam'}]
        self.assertIn('Kanada hakkında bilgi ver', resolve('Peki bunun başkenti?', history))
        self.assertEqual(resolve('Python liste nedir?', history), 'Python liste nedir?')
    def test_no_assistant_as_user_context(self):
        from eagle_api import eagle_genel_baglam_coz as resolve
        self.assertEqual(resolve('Peki bunun nedeni?', [{'role':'assistant','content':'Bir konu'}]), 'Peki bunun nedeni?')
