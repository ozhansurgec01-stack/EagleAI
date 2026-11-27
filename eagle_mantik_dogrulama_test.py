import ast
import operator
import re
import unittest
from pathlib import Path

ns = dict(ast=ast, operator=operator, re=re)
tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
for node in tree.body:
    if (isinstance(node, ast.FunctionDef) and node.name in ('guvenli_hesapla', 'guvenli_mantiksal_hesapla')) or (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '_GUVENLI_ISLEMLER' for t in node.targets)):
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'eagle_api.py', 'exec'), ns)

class MantikTest(unittest.TestCase):
    def check(self, query, correct, wrong):
        ok, answer = ns['guvenli_mantiksal_hesapla'](query)
        self.assertTrue(ok)
        self.assertIn(f'Doğru: {correct}\nYanlış: {wrong}\n', answer)
    def test_mixed(self):
        self.check('A=20, B=A*3 1) B=60 2) B=61', 1, 1)
    def test_false_first(self):
        self.check('A=2 1) A=3', 0, 1)
    def test_less_equal(self):
        self.check('A=2 1) A<=2 2) A<=1', 1, 1)
    def test_negative(self):
        self.check('A=-3 1) A=-3 2) A>-2', 1, 1)
    def test_chain(self):
        self.check('A=2 1) 1<A<=3 2) 3<A<4', 1, 1)
    def test_unsupported(self):
        self.assertFalse(ns['guvenli_mantiksal_hesapla']('A=2 1) A in 3')[0])
    def test_boolean(self):
        self.assertFalse(ns['guvenli_hesapla']('True+2')[0])
    def test_arithmetic(self):
        self.assertEqual(ns['guvenli_hesapla']('2+3*4'), (True, 14))
        self.assertFalse(ns['guvenli_hesapla']('1/0')[0])
    def test_nonfinite(self):
        for expr in ('1e999', '1e308*10', '(-1)**0.5'):
            self.assertFalse(ns['guvenli_hesapla'](expr)[0], expr)
    def test_resource_limits(self):
        for expr in ('(((10**10)**10)**10)**10', '+'.join(['1']*200), '1'*2050):
            self.assertFalse(ns['guvenli_hesapla'](expr)[0])
    def test_logic_nonfinite(self):
        self.assertFalse(ns['guvenli_mantiksal_hesapla']('A=1e999 1) A>2')[0])
        self.assertFalse(ns['guvenli_mantiksal_hesapla']('A=2 1) A<1e999')[0])
    def test_fraction_and_negative(self):
        self.assertEqual(ns['guvenli_hesapla']('(-3+1)/4'), (True, -0.5))
        self.check('A=2, B=A/4 1) B=0.5 2) B<0', 1, 1)
