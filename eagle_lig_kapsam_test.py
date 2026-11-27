import ast
import unittest
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch, Mock

ns = {}
tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in ('eagle_lig_fikstur_kapsami', 'eagle_lig_fikstur_cevabi'):
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'eagle_api.py', 'exec'), ns)

class LigTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 27, 8, tzinfo=ZoneInfo('Europe/Istanbul'))
    def scope(self, q):
        return ns['eagle_lig_fikstur_kapsami'](q, self.now)
    def test_default(self):
        a = self.scope('Şampiyonlar Ligi maçları')
        self.assertEqual(a[1], 'uefa.champions')
        self.assertEqual((a[3]-a[2]).days, 13)
    def test_week(self):
        a = self.scope('Gelecek hafta Avrupa Ligi maçları')
        self.assertEqual((str(a[2]), str(a[3])), ('2026-11-30', '2026-12-06'))
    def test_yesterday(self):
        a = self.scope('Dün Bundesliga maç sonuçları')
        self.assertEqual(str(a[2]), '2026-11-26')
        self.assertTrue(a[4])
    def test_team(self):
        self.assertIsNone(self.scope('Galatasaray Şampiyonlar Ligi maçları'))
    def test_leagues(self):
        for q, code in [('Konferans Ligi','uefa.europa.conf'), ('Premier Lig','eng.1'), ('La Liga','esp.1'), ('Serie A','ita.1'), ('Ligue 1','fra.1')]:
            self.assertEqual(self.scope(q+' maçları')[1], code)
    @patch('requests.get')
    def test_empty(self, get):
        get.return_value.json.return_value = {'events': []}
        ok, answer = ns['eagle_lig_fikstur_cevabi'](self.scope('Şampiyonlar Ligi maçları'), self.now)
        self.assertFalse(ok)
        self.assertIn('Şampiyonlar Ligi', answer)
        self.assertEqual(get.call_count, 1)
        self.assertIn('uefa.champions', get.call_args.args[0])
    @patch('requests.get', side_effect=TimeoutError)
    def test_timeout(self, get):
        ok, answer = ns['eagle_lig_fikstur_cevabi'](self.scope('Şampiyonlar Ligi maçları'), self.now)
        self.assertFalse(ok)
        self.assertIn('ulaşılamadı', answer)
    @patch('requests.get')
    def test_fallback_exact_league(self, get):
        event = {'startTimestamp': int(datetime(2026,11,28,15,tzinfo=ZoneInfo('Europe/Istanbul')).timestamp()), 'tournament': {'uniqueTournament': {'id':17}}, 'status': {'type':'notstarted'}, 'homeTeam': {'name':'A'}, 'awayTeam': {'name':'B'}}
        wrong = dict(event, tournament={'uniqueTournament': {'id':52}}, homeTeam={'name':'Wrong'})
        def response(url, **kwargs):
            if 'espn.com' in url:
                raise TimeoutError()
            r = Mock(); r.json.return_value = {'events':[event,wrong]}; return r
        get.side_effect = response
        ok, answer = ns['eagle_lig_fikstur_cevabi'](self.scope('Yarın Premier League maçları'), self.now)
        self.assertTrue(ok)
        self.assertIn('SofaScore', answer)
        self.assertIn('A - B', answer)
        self.assertNotIn('Wrong', answer)
    @patch('requests.get')
    def test_local_date(self, get):
        event = {'date':'2026-11-27T22:00:00Z','status':{'type':{'state':'pre'}},'competitions':[{'competitors':[{'homeAway':'home','team':{'displayName':'A'}},{'homeAway':'away','team':{'displayName':'B'}}]}]}
        get.return_value.json.return_value = {'events':[event]}
        ok, answer = ns['eagle_lig_fikstur_cevabi'](self.scope('Yarın Şampiyonlar Ligi maçları'), self.now)
        self.assertTrue(ok)
        self.assertIn('28.11.2026 01:00', answer)
        ok, _ = ns['eagle_lig_fikstur_cevabi'](self.scope('Bugün Şampiyonlar Ligi maçları'), self.now)
        self.assertFalse(ok)

if __name__ == '__main__':
    unittest.main()
