import ast
import re
import unittest
import tempfile
import os
from pathlib import Path
import sympy as sp
from eagle_kod_calistirici import guvenlik_hook

node = next(n for n in ast.parse(Path(__file__).with_name('eagle_api.py').read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'sembolik_denklem_coz')
ns = dict(ast=ast, re=re, sp=sp)
exec(compile(ast.Module(body=[node], type_ignores=[]), 'equation', 'exec'), ns)
solve = ns['sembolik_denklem_coz']

class EquationTest(unittest.TestCase):
    def test_linear(self): self.assertEqual(solve('2x+3=7')['cozumler'], [2])
    def test_quadratic(self): self.assertEqual(solve('x^2=9')['cozumler'], [-3,3])
    def test_fraction(self): self.assertEqual(solve('x/2=3')['cozumler'], [6])
    def test_invalid(self):
        for s in ('x**999999=1', 'x.__class__=1', 'x/0=1', 'x/(x-1)=2', 'x+y=2', 'x=2', 'x^4*x^4=1'):
            self.assertIsNone(solve(s), s)
    def test_no_solution(self): self.assertEqual(solve('x+1=x+2')['cozumler'], [])
    def test_runtime_flags(self):
        import sys
        with tempfile.TemporaryDirectory() as d:
            hook = guvenlik_hook(Path(d))
            path = str(Path(sys.prefix)/'example')
            hook('open', (path, None, os.O_RDONLY))
            with self.assertRaises(PermissionError): hook('open', (path, None, os.O_WRONLY))
    def test_link_destination(self):
        with tempfile.TemporaryDirectory() as d:
            hook = guvenlik_hook(Path(d))
            for event in ('os.link','os.symlink'):
                with self.assertRaises(PermissionError): hook(event, (str(Path(d)/'file'), '/outside/file'))
