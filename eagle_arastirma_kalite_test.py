import unittest
from eagle_merkez_motoru import EagleMerkezMotoru as M

class QualityTests(unittest.TestCase):
    def test_reader_article_body_and_spanish_query(self):
        import ast, re, json
        from pathlib import Path
        from unittest.mock import Mock
        from bs4 import BeautifulSoup
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        names = {'web_sayfa_oku', '_eagle_cok_dilli_anlati_sorgulari'}
        body = 'Historical article with documented observations and context. ' * 12
        response = Mock(status_code=200, text='<script type="application/ld+json">' + json.dumps({'@type':'NewsArticle', 'articleBody':body}) + '</script><p>Short page</p>')
        scope = dict(re=re, json=json, BeautifulSoup=BeautifulSoup, requests=Mock(), web_kaynak_url=lambda u:u, _eagle_anlati_sorgusu_mu=lambda q:True)
        scope['requests'].get.return_value = response
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), 'reader', 'exec'), scope)
        self.assertEqual(scope['web_sayfa_oku']('https://example.org', metaveri_dahil=False), body.strip())
        self.assertIn('1978 Bolivia OVNI incidente', scope['_eagle_cok_dilli_anlati_sorgulari']('1978 Bolivya UFO olayını anlat'))

    @__import__("unittest.mock", fromlist=["patch"]).patch("eagle_anlati_sentez.translate_sources", return_value=[[]])
    def test_historical_external_evidence(self, translation):
        import ast
        from pathlib import Path
        from unittest.mock import Mock
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_eagle_tarihsel_web_kanit')
        scope = {'_eagle_cok_dilli_anlati_sorgulari': lambda q: ['1978 Bolivia UFO'],
                 '_web_sonucu_sorguyla_ilgili_mi': lambda q, a: 'UFO' in a['title']}
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {node.name, '_eagle_anlati_video_mu'}], type_ignores=[]), 'evidence', 'exec'), scope)
        run = scope[node.name]
        text = '1978 Bolivia UFO was described in a historical account, with the circumstances and reported observations recorded by the author. Another UFO account describes the reported observations without independently confirming the nature of the object. ' * 2
        a = {'title': 'UFO account', 'url': 'https://example.org/story', 'snippet': text}
        reader = Mock(return_value='')
        self.assertIsNone(run('1978 Bolivya UFO', [a], reader))
        reader.reset_mock()
        self.assertIsNone(run('1978 Bolivya UFO', [dict(a, url='https://m.youtube.com/watch?v=x')], reader))
        reader.assert_not_called()
        reader.return_value = text.replace('1978', '1979')
        self.assertIsNone(run('1978 Bolivya UFO', [a], reader))
        reader.return_value = text
        r = run('1978 Bolivya UFO', [a, dict(a, url='https://other.org/story')], reader)
        self.assertEqual(r['research_status'], 'unverified')
        self.assertFalse(r['ok'])
        self.assertFalse(r['event_verified'])
        self.assertEqual(len(r['research_sources']), 1)
        candidates = [dict(a, url=f'https://source{i}.org/story') for i in range(6)]
        reader.side_effect = lambda url, **kw: text if 'source5.' in url else 'short'
        r = run('1978 Bolivya UFO', candidates, reader)
        self.assertEqual(r['research_sources'][0]['url'], candidates[5]['url'])

    @__import__("unittest.mock", fromlist=["patch"]).patch("eagle_anlati_sentez.translate_sources", return_value=[[]])
    def test_historical_context_window(self, translation):
        import ast
        from pathlib import Path
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        names = {'_eagle_tarihsel_web_kanit', '_eagle_anlati_video_mu'}
        scope = {'_eagle_cok_dilli_anlati_sorgulari': lambda q: ['1978 Bolivia UFO'],
                 '_web_sonucu_sorguyla_ilgili_mi': lambda q, a: all(w in a['title'] for w in ('1978', 'Bolivia', 'UFO'))}
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), 'context', 'exec'), scope)
        run = scope['_eagle_tarihsel_web_kanit']
        a = {'title': '1978 Bolivia UFO', 'url': 'https://example.org/story'}
        text = ('The historical report dates the observation to May 1978. '
                'Witnesses in Bolivia described an unusual object in the sky. '
                'The UFO account records their statements without confirming the nature of the object. ')
        self.assertFalse(run('1978 Bolivya UFO', [a], lambda *args, **kw: text * 2)['ok'])
        self.assertIsNone(run('1978 Bolivya UFO', [a], lambda *args, **kw: text.replace('1978', '1979') * 2))
        self.assertIsNone(run('1978 Bolivya UFO', [a], lambda *args, **kw: text.replace('UFO', 'weather') * 2))

    @__import__("unittest.mock", fromlist=["patch"]).patch("eagle_anlati_sentez.translate_sources", return_value=[[]])
    def test_historical_spanish_article_anchors(self, translation):
        import ast
        from pathlib import Path
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        names = {'_eagle_tarihsel_web_kanit', '_eagle_anlati_video_mu'}
        scope = {'_eagle_cok_dilli_anlati_sorgulari': lambda q: ['1978 Bolivia OVNI incidente'],
                 '_web_sonucu_sorguyla_ilgili_mi': lambda q, a: True}
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), 'spanish', 'exec'), scope)
        run = scope['_eagle_tarihsel_web_kanit']
        a = {'title': 'Mecoya', 'url': 'https://example.org/story'}
        text = ('Un hecho que aún permanece en la memoria colectiva de quienes habitaban Tarija en 1978 nos trae al presente un extraño objeto en el cielo o una especie de llamarada que se creía había explosionado en la zona de Padcaya, pero cuando los expertos y la prensa llegaron al lugar no encontraron nada. El misterio hasta la fecha se mantiene. '
                + 'Los investigadores realizaron una expedición por las montañas y no encontraron restos del aparato. ' * 8
                + 'Sobrevolamos toda la parte boliviana. La prensa publicó titulares sobre el OVNI.')
        self.assertFalse(run('1978 Bolivya UFO olayını', [a], lambda *args, **kw: text)['ok'])
        result = run('1978 Bolivya UFO olayını', [a, dict(a, url="https://other.org/story")], lambda *args, **kw: text)
        self.assertIn("yeterli kaynak metni alınamadı", result["answer"])
        self.assertNotIn("Los investigadores realizaron una expedición", result["answer"])
        self.assertEqual(len(result["research_sources"]), 1)
        for bad in (text.replace('1978', '1979'), text.replace('boliviana', 'argentina'), text.replace('OVNI', 'clima'), text.replace('extraño objeto', 'avión comercial')):
            self.assertIsNone(run('1978 Bolivya UFO olayını', [a], lambda *args, **kw: bad))

    def test_search_acronyms_preserved(self):
        import ast, re
        from pathlib import Path
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_web_arama_sorgusunu_sadelestir')
        scope = {'re': re}
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'query', 'exec'), scope)
        run = scope[node.name]
        for word in ('UFO', 'NASA', 'NATO', 'TBMM'):
            self.assertIn(word, run('1978 Bolivya ' + word + ' olayını anlat'))
        self.assertEqual(run('NewYork'), 'New York')

    def test_historical_full_extract_fallback(self):
        import ast
        from pathlib import Path
        from unittest.mock import Mock
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        names = {'_eagle_tarihsel_wiki', '_eagle_tarihsel_paragraflar'}
        scope = {'requests': Mock(), '_wikimedia_user_agent': lambda: 'test',
                 '_web_sonucu_sorguyla_ilgili_mi': lambda q, r: 'Titanik' in r['title']}
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), 'history', 'exec'), scope)
        text = ('Titanik faciası hakkında tarihsel kaynak açıklaması 1912 yılında gerçekleşen olayın bağlamını ve sonuçlarını anlatmaktadır. ' * 4).strip()
        first = Mock(); first.json.return_value = {'query': {'pages': {'1': {'pageid': 1, 'title': 'Titanik', 'extract': 'Kısa.'}}}}
        full = Mock(); full.json.return_value = {'query': {'pages': {'1': {'pageid': 1, 'title': 'Titanik', 'extract': text}}}}
        scope['requests'].get.side_effect = [first, full]
        r = scope['_eagle_tarihsel_wiki']('Titanik faciasını')
        self.assertEqual(r['text'], text)
        self.assertEqual(scope['requests'].get.call_args.kwargs['params']['pageids'], 1)
        self.assertEqual(scope['_eagle_tarihsel_paragraflar']('Yarım cümle '*100), [])

    def test_encyclopedia_memory(self):
        import ast, os, tempfile
        from pathlib import Path
        from unittest.mock import patch
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_eagle_kaynakli_bilgi_hafizasi')
        scope = {}
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'memory', 'exec'), scope)
        run = scope[node.name]
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {'EAGLE_KNOWLEDGE_DB': str(Path(d)/'knowledge.db')}):
            record = {'title':'Tarih', 'text':'Tarihsel kaynak metni. '*40, 'url':'https://tr.wikipedia.org/wiki/Tarih', '_eagle_encyclopedia_extract':True}
            self.assertIsNone(run('Tarih', dict(record, _eagle_encyclopedia_extract=False)))
            self.assertEqual(run('Tarih', record), record)
            self.assertTrue(run('tarih')['_eagle_cached_source'])
            self.assertIsNone(run('başka konu'))
            run('Tarih', dict(record, text=record['text']+'Yeni sürüm.'))
            self.assertIsNone(run('Tarih'))

    def test_persistent_country_knowledge(self):
        import ast, os, re, tempfile
        from pathlib import Path
        from unittest.mock import Mock, patch
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_eagle_ulke_bilgi_hafizasi')
        scope = {'os': os, 're': re, 'merkez_motor': Mock()}
        scope['merkez_motor'].genel_web_ulke_token_eslesiyor.side_effect = lambda a,b: a.casefold()==b.casefold()
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'knowledge', 'exec'), scope)
        run = scope[node.name]
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {'EAGLE_KNOWLEDGE_DB': str(Path(d)/'knowledge.db')}):
            record = {'title':'Norveç','text':'Başkent: Oslo.', 'url':'https://www.wikidata.org/wiki/Q20','_eagle_country_structured':True}
            self.assertEqual(run('Norveç', record), record)
            self.assertIn('Hafıza kaydı:', run('norveç')['text'])
            self.assertIsNone(run('Kanada'))
            run('Kanada', dict(record, title='Kanada', url='https://example.org/Q20'))
            self.assertIsNone(run('Kanada'))
            rich = dict(record, text='Başkent: Oslo. Nüfus: 5.500.000 (2024).')
            run('Norveç', rich)
            self.assertEqual(run('Norveç', record), record)
            self.assertIn('Nüfus:', run('Norveç')['text'])

    def test_direct_publisher_feed(self):
        import ast, re
        from pathlib import Path
        from unittest.mock import Mock
        from datetime import datetime, timezone
        from email.utils import format_datetime
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        names = {'_eagle_yayinci_haberleri','_eagle_haber_basligi_uygun','_eagle_haber_makale_url'}
        scope = {'re':re,'requests':Mock(),'_wikimedia_user_agent':lambda:'test','_web_sonucu_sorguyla_ilgili_mi':lambda q,r:True}
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'feeds','exec'),scope)
        response = scope['requests'].get.return_value
        response.status_code = 200
        stamp = format_datetime(datetime.now(timezone.utc))
        response.content = f'<rss><channel><item><title>UFO iddiası</title><link>https://www.trthaber.com/haber/test.html</link><pubDate>{stamp}</pubDate></item><item><title>UFO</title><link>https://evil.org/test</link><pubDate>{stamp}</pubDate></item></channel></rss>'.encode()
        rows = scope['_eagle_yayinci_haberleri']('UFO')
        self.assertEqual(len(rows),1)
        self.assertEqual(scope['_eagle_haber_makale_url'](rows[0]),rows[0]['url'])

    def test_independent_research_cache(self):
        import ast, os, re, tempfile
        from pathlib import Path
        from unittest.mock import Mock, patch
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_eagle_bagimsiz_olay_arastirma')
        partial = {'answer': 'Kaynak iddiası', 'research_status': 'partial', 'research_sources': [{'url': 'https://example.org/news'}], 'event_verified': False, 'ok': False}
        summary = Mock(return_value=partial)
        grounded = Mock(return_value={'ok': True})
        scope = {'os': os, 're': re, '_eagle_olay_haber_ozeti': summary, '_eagle_haber_kaynaklari': Mock(return_value=[]), '_eagle_grounded_arastirma': grounded, '_eagle_gdelt_haberleri': Mock(return_value=[])}
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'independent', 'exec'), scope)
        run = scope[node.name]
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {'EAGLE_RESEARCH_CACHE': str(Path(d)/'cache.db'), 'EAGLE_GEMINI_RESEARCH_FALLBACK': '0'}):
            self.assertEqual(run('UFO', None), partial)
            self.assertTrue(run('ufo', None)['research_cached'])
            self.assertEqual(summary.call_count, 1)
            summary.return_value = {'research_status': 'unverified', 'research_sources': []}
            run('deprem', None)
            run('deprem', None)
            self.assertEqual(summary.call_count, 3)
            grounded.assert_not_called()
            with patch.dict(os.environ, {'EAGLE_GEMINI_RESEARCH_FALLBACK': '1'}):
                self.assertTrue(run('deprem', None)['ok'])
                grounded.assert_called_once()

    def test_gdelt_direct_discovery_and_gallery_categories(self):
        import ast, re
        from pathlib import Path
        from unittest.mock import Mock
        from datetime import datetime, timezone
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        names = {'_eagle_gdelt_haberleri', '_eagle_haber_basligi_uygun', '_eagle_haber_makale_url', '_eagle_ulke_gorsel_cesitlendir'}
        scope = {'re': re, 'requests': Mock(), '_web_sonucu_sorguyla_ilgili_mi': lambda q,r: True}
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), 'gdelt', 'exec'), scope)
        row = {'url': 'https://example.org/article', 'domain': 'example.org', 'title': 'UFO sighting', 'seendate': datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}
        response = scope['requests'].get.return_value
        response.status_code = 200
        response.json.return_value = {'articles': [row, dict(row, domain='evil.org'), dict(row, seendate='20000101T000000Z')]}
        rows = scope['_eagle_gdelt_haberleri']('En son UFO nerede görüldü?')
        self.assertEqual(len(rows), 1)
        self.assertNotIn('published', rows[0])
        self.assertEqual(scope['_eagle_haber_makale_url'](rows[0]), row['url'])
        response.status_code = 429
        self.assertEqual(scope['_eagle_gdelt_haberleri']('UFO'), [])
        gallery = scope['_eagle_ulke_gorsel_cesitlendir']([{'name':'Royal Palace','category':'diger'}, {'name':'Lake Bondhus','category':'diger'}], str.lower)
        self.assertEqual({x['category'] for x in gallery}, {'tarih','doga'})

    def test_current_event_news_dates(self):
        import ast, re
        from pathlib import Path
        from unittest.mock import Mock
        from datetime import datetime, timezone, timedelta
        from email.utils import format_datetime
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        names = {'_eagle_gundem_sorgusu', '_eagle_guncel_olay_sorgusu', '_eagle_haber_kaynaklari', '_eagle_haber_basligi_uygun', '_eagle_olay_haber_ozeti'}
        scope = {'re': re, 'requests': Mock(), '_wikimedia_user_agent': lambda: 'test', '_web_sonucu_sorguyla_ilgili_mi': lambda q, r: True}
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), 'news', 'exec'), scope)
        self.assertTrue(scope['_eagle_guncel_olay_sorgusu']('En son UFO nerede görüldü'))
        self.assertTrue(scope['_eagle_guncel_olay_sorgusu']('Bugün dünyada hangi olaylar yaşandı?'))
        for q in ('Bugün Türkiye gündeminde neler var?', 'Bugün dünya gündemi', 'Türkiye gündemi nedir?', 'Bugün Türkiye’de neler oldu?'):
            self.assertTrue(scope['_eagle_gundem_sorgusu'](q), q)
        for q in ('Bugün Türkiye maçı var mı?', 'Bugün Süper Lig maçları', 'Bugün hava nasıl?'):
            self.assertFalse(scope['_eagle_gundem_sorgusu'](q), q)
        self.assertFalse(scope['_eagle_guncel_olay_sorgusu']('Bugün hava nasıl?'))
        self.assertFalse(scope['_eagle_guncel_olay_sorgusu']('1000 pound kaç TL'))
        now = datetime.now(timezone.utc)
        def item(day):
            return f'<item><title>UFO haberi</title><link>https://news.google.com/rss/articles/test</link><source url="https://example.org">Test</source><pubDate>{format_datetime(day)}</pubDate></item>'
        scope['requests'].get.return_value.content = ('<rss><channel>'+item(now-timedelta(days=60))+item(now-timedelta(days=1))+'</channel></rss>').encode()
        rows = scope['_eagle_haber_kaynaklari']('En son UFO nerede görüldü')
        self.assertEqual(len(rows), 1)
        self.assertIn('olay tarihi değil', rows[0]['snippet'])
        self.assertFalse(scope['_eagle_haber_basligi_uygun']('UFO', 'Bursa UFO görünümlü mercek bulutları'))
        self.assertTrue(scope['_eagle_haber_basligi_uygun']('UFO', 'Gelibolu UFO iddiası'))
        result = scope['_eagle_olay_haber_ozeti']('UFO', rows, lambda *a, **k: '', lambda h: '')
        self.assertFalse(result['ok'])
        self.assertEqual(result['research_status'], 'unverified')
        self.assertEqual(result['research_sources'], [])
        self.assertIn('Tam metin doğrulanamadı', result['answer'])
        result = scope['_eagle_olay_haber_ozeti']('UFO', rows, lambda *a, **k: 'Gelibolu bölgesinde UFO görüldüğü iddiasının henüz bağımsız kaynaklar tarafından doğrulanmadığı açıklandı.', lambda h: 'https://example.org/article')
        self.assertIn('Kaynak metninden:', result['answer'])
        self.assertEqual(result['research_sources'][0]['url'], 'https://example.org/article')
        self.assertFalse(result['event_verified'])
        self.assertEqual(result['verification_status'], 'unverified_claim')
        old = dict(rows[0], title='1953 UFO sighting')
        result_old = scope['_eagle_olay_haber_ozeti']('UFO', [old], lambda *a, **k: 'unused', lambda h: 'https://example.org/article')
        self.assertEqual(result_old['research_sources'], [])
        self.assertFalse(result['ok'])

    def test_news_publisher_resolution(self):
        import ast, re
        from pathlib import Path
        from unittest.mock import Mock
        from bs4 import BeautifulSoup
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_eagle_haber_makale_url')
        requests = Mock()
        scope = {'re': re, 'requests': requests, 'BeautifulSoup': BeautifulSoup, '_wikimedia_user_agent': lambda: 'test'}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), 'resolver', 'exec'), scope)
        h = {'publisher': 'https://example.org', 'title': 'Gelibolu UFO iddiası - Test', 'url': 'https://news.google.com/rss/articles/test'}
        r = requests.get.return_value
        r.status_code = 200
        r.text = '<a class="result__a" href="https://evil.org/article">Gelibolu UFO iddiası</a><a class="result__a" href="https://example.org/article">Gelibolu UFO iddiası</a>'
        self.assertEqual(scope[fn.name](h), 'https://example.org/article')
        r.text = '<a class="result__a" href="https://example.org/other">Başka haber</a>'
        self.assertEqual(scope[fn.name](h), '')
        r.status_code = 302
        r.headers = {'Location': 'https://example.org/direct'}
        self.assertEqual(scope[fn.name](h), 'https://example.org/direct')

    def test_news_token_resolution(self):
        import ast, re, json
        from pathlib import Path
        from unittest.mock import Mock
        from bs4 import BeautifulSoup
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_eagle_haber_makale_url')
        requests = Mock()
        scope = {'re': re, 'requests': requests, 'BeautifulSoup': BeautifulSoup, '_wikimedia_user_agent': lambda: 'test'}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), 'resolver', 'exec'), scope)
        h = {'publisher': 'https://example.org', 'title': 'UFO iddiası', 'url': 'https://news.google.com/rss/articles/test'}
        requests.get.return_value = Mock(status_code=200, headers={}, text='<div data-n-a-sg="sig" data-n-a-ts="123"></div>')
        requests.post.return_value = Mock(status_code=200, text=json.dumps([["wrb.fr", "Fbv4je", json.dumps(["garturlres", "https://example.org/article"])]]))
        self.assertEqual(scope[fn.name](h), 'https://example.org/article')
        requests.post.return_value.text = json.dumps([["wrb.fr", "Fbv4je", json.dumps(["garturlres", "https://evil.org/article"])]] )
        self.assertEqual(scope[fn.name](h), '')

    def test_news_provider_failover(self):
        import ast, re, base64
        from pathlib import Path
        from unittest.mock import Mock
        from bs4 import BeautifulSoup
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_eagle_haber_makale_url')
        requests = Mock()
        scope = {'re': re, 'requests': requests, 'BeautifulSoup': BeautifulSoup, '_wikimedia_user_agent': lambda: 'test'}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), 'resolver', 'exec'), scope)
        h = {'publisher': 'https://example.org', 'title': 'Gelibolu UFO iddiası - Test', 'url': 'https://news.google.com/rss/articles/test'}
        redirect = Mock(status_code=302, headers={'Location': h['url']})
        blocked = Mock(status_code=202)
        token = base64.urlsafe_b64encode(b'https://example.org/article').decode().rstrip('=')
        bing = Mock(status_code=200, text=f'<li class="b_algo"><h2><a href="https://www.bing.com/ck/a?u=a1{token}">Gelibolu UFO iddiası</a></h2></li>')
        requests.get.side_effect = [redirect, bing]
        self.assertEqual(scope[fn.name](h), 'https://example.org/article')
        ddg = Mock(status_code=200, text='<a class="result__a" href="https://example.org/article">Gelibolu UFO iddiası</a>')
        requests.get.side_effect = [redirect, blocked, ddg]
        self.assertEqual(scope[fn.name](h), 'https://example.org/article')
        requests.get.side_effect = [redirect, blocked, blocked]
        self.assertEqual(scope[fn.name](h), '')
        engelli = set()
        requests.get.side_effect = [redirect, blocked, blocked, redirect]
        self.assertEqual(scope[fn.name](h, engelli), '')
        self.assertEqual(len(engelli), 2)
        self.assertEqual(scope[fn.name](h, engelli), '')

    def test_grounded_research(self):
        import ast
        from pathlib import Path
        from unittest.mock import Mock
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_eagle_grounded_arastirma')
        requests, os = Mock(), Mock()
        os.getenv.return_value = 'test'
        scope = {'requests': requests, 'os': os}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), 'grounding', 'exec'), scope)
        run = scope[fn.name]
        r = requests.post.return_value
        r.status_code = 200
        candidate = {'finishReason': 'STOP', 'groundingMetadata': {'webSearchQueries': ['UFO'], 'groundingChunks': [{'web': {'uri': 'https://example.org/news', 'title': 'Example'}}], 'groundingSupports': [{'segment': {'text': 'Bir gözlem iddiası bildirildi.'}, 'groundingChunkIndices': [0]}]}}
        r.json.return_value = {'candidates': [candidate]}
        result = run('UFO')
        self.assertTrue(result['ok'])
        self.assertFalse(result['event_verified'])
        self.assertIn('https://example.org/news', result['answer'])
        from datetime import date, timedelta
        today = date.today().isoformat()
        old = (date.today() - timedelta(days=60)).isoformat()
        supports = candidate['groundingMetadata']['groundingSupports']
        supports[:] = [{'segment': {'text': f'Olay: {today} | Yer: Bursa | Açıklama: UFO benzeri mercek bulutu görüldü.'}, 'groundingChunkIndices': [0]},
                       {'segment': {'text': f'Olay: {old} | Yer: Alaska | Açıklama: Bir gözlem iddiası bildirildi.'}, 'groundingChunkIndices': [0]}]
        self.assertIsNone(run('En son UFO nerede görüldü'))
        supports.append({'segment': {'text': f'Olay: {today} | Yer: Gelibolu | Açıklama: Bir gözlem iddiası bildirildi.'}, 'groundingChunkIndices': [0]})
        result = run('En son UFO nerede görüldü')
        self.assertIn('Gelibolu', result['answer'])
        self.assertNotIn('Bursa', result['answer'])
        self.assertNotIn('Alaska', result['answer'])
        self.assertEqual(result['verification_status'], 'unverified_claim')
        self.assertFalse(result['research_sources'][0]['independently_verified'])
        chunk = candidate['groundingMetadata']['groundingChunks'][0]['web']
        chunk.update(uri='https://vertexaisearch.cloud.google.com/grounding-api-redirect/test', title='medium.com')
        self.assertIsNone(run('En son UFO nerede görüldü'))
        chunk['title'] = 'faa.gov'
        result = run('En son UFO nerede görüldü')
        self.assertEqual(result['research_sources'][0]['source_type'], 'reported_official_domain')
        self.assertFalse(result['event_verified'])
        record = f'Olay: {today} | Yer: İzmir | Açıklama: Bir gözlem iddiası bildirildi.'
        first, second = record.split(' | Açıklama: ')
        second = '| Açıklama: ' + second
        start = len((first + ' ').encode('utf-8'))
        candidate['content'] = {'parts': [{'text': record}]}
        supports[:] = [{'segment': {'text': first, 'endIndex': len(first.encode('utf-8'))}, 'groundingChunkIndices': [0]},
                       {'segment': {'text': second, 'startIndex': start, 'endIndex': len(record.encode('utf-8'))}, 'groundingChunkIndices': [0]}]
        self.assertIn('İzmir', run('En son UFO nerede görüldü')['answer'])
        # Exact unique text can recover missing or inconsistent byte offsets.
        for support in supports:
            support['segment'].pop('endIndex', None)
        self.assertIn('İzmir', run('En son UFO nerede görüldü')['answer'])
        supports.pop()
        self.assertIsNone(run('En son UFO nerede görüldü'))
        formatted = f'- **Olay:** {today} | **Yer:** İzmir | **Açıklama:** Bir gözlem iddiası bildirildi.'
        candidate['content'] = {'parts': [{'text': formatted}]}
        supports[:] = [{'segment': {'text': formatted}, 'groundingChunkIndices': [0]}]
        self.assertIn('İzmir', run('En son UFO nerede görüldü')['answer'])
        combined = 'Araştırma sonucu:\n' + record
        candidate['content'] = {'parts': [{'text': combined}]}
        supports[:] = [{'segment': {'text': combined, 'endIndex': len(combined.encode('utf-8'))}, 'groundingChunkIndices': [0]}]
        self.assertIn('İzmir', run('En son UFO nerede görüldü')['answer'])
        prose = 'Gelibolu bölgesinde UFO görüntüleri paylaşıldığı iddia edildi.'
        candidate['content'] = {'parts': [{'text': prose}]}
        supports[:] = [{'segment': {'text': prose}, 'groundingChunkIndices': [0]}]
        result = run('En son UFO nerede görüldü')
        self.assertFalse(result['ok'])
        self.assertEqual(result['research_status'], 'partial')
        self.assertIn('Gelibolu', result['answer'])
        self.assertFalse(result['event_verified'])
        self.assertTrue(result['research_sources'])
        candidate['groundingMetadata']['groundingSupports'] = []
        self.assertIsNone(run('UFO'))
        r.status_code = 429
        self.assertIsNone(run('UFO'))
        calls = requests.post.call_count
        self.assertIsNone(run('UFO'))
        self.assertEqual(requests.post.call_count, calls)
        os.getenv.return_value = None
        self.assertIsNone(run('UFO'))

    def test_afad_direct_record(self):
        import ast
        from pathlib import Path
        from unittest.mock import Mock
        from datetime import datetime, timezone, timedelta
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_eagle_son_deprem')
        requests = Mock()
        scope = {'requests': requests}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), 'afad', 'exec'), scope)
        run = scope[fn.name]
        now = datetime.now(timezone(timedelta(hours=3)))
        row = {'date': (now-timedelta(minutes=2)).astimezone(timezone.utc).replace(tzinfo=None).isoformat(), 'location': 'Çorum', 'magnitude': 1.4, 'depth': 7}
        requests.get.return_value.status_code = 200
        requests.get.return_value.json.return_value = [dict(row, date=(now+timedelta(hours=1)).isoformat(), location='Gelecek'), row]
        result = run('En son deprem nerede oldu')
        self.assertIn('Çorum', result['answer'])
        self.assertNotIn('Gelecek', result['answer'])
        self.assertEqual(result['research_status'], 'official_record')
        self.assertIsNone(run('En son UFO nerede görüldü'))
        self.assertIsNone(run('Dünyada en son deprem nerede oldu'))
        requests.get.return_value.status_code = 429
        self.assertIsNone(run('En son deprem nerede oldu'))
        first, second = Mock(), Mock()
        first.status_code = 503
        second.status_code = 200
        second.json.return_value = {'features': [{'properties': {'type': 'earthquake', 'time': int((now-timedelta(minutes=1)).timestamp()*1000), 'mag': 2, 'place': 'Turkey'}, 'geometry': {'coordinates': [35, 39, 7]}}]}
        requests.get.side_effect = [first, second]
        result = run('En son deprem nerede oldu')
        self.assertEqual(result['research_sources'][0]['title'], 'USGS')
        self.assertIn('küçük depremlerin', result['answer'])

    def test_country_scope(self):
        for q in ('Avusturya', 'avusturya', 'Meksika hakkında bilgi verir misin', 'Norveç hakkında bilgi ver'):
            self.assertTrue(M.ulke_tanitim_konusu(q))
        self.assertFalse(M.ulke_tanitim_konusu('Avusturya faşizmi'))
        self.assertEqual(M.genel_web_cevabi('Avusturya', [{'title':'Avusturya faşizmi','snippet':'Avusturya faşizmi bir siyasi harekettir.'}]), ('', 0.0))
    def test_country_extract(self):
        text = 'Avusturya, Orta Avrupa’da bulunan bir ülkedir. Başkenti Viyana’dır. Ülkenin önemli bir bölümü Alp Dağları ile kaplıdır. Salzburg ve Graz önemli şehirleridir. Ülkenin resmî dili Almancadır.'
        self.assertEqual(M.genel_web_cevabi('Avusturya', [{'title':'Avusturya','text':text,'_eagle_country_extract':True}]), (text, .78))

    def test_country_full_pipeline_preserves_extract(self):
        text = "Avusturya Avusturya (Almanca:), Orta Avrupa'da bulunan bir ülkedir. Başkenti Viyana'dır. Ülkenin önemli bir bölümü Alp Dağları ile kaplıdır. Salzburg ve Graz önemli şehirleridir. Ülkenin resmî dili Almancadır."
        records = M.temizle_web_verisi([{'title':'Avusturya','text':text,'snippet':'Kısa özet','url':'https://tr.wikipedia.org/wiki/Avusturya','_eagle_country_extract':True}])
        self.assertEqual(records[0]['text'], text)
        self.assertTrue(records[0]['_eagle_country_extract'])
        answer, confidence = M.genel_web_cevabi('Avusturya', records)
        self.assertTrue(answer.startswith('Avusturya,'))
        self.assertNotIn('(Almanca:)', answer)
        self.assertIn('Viyana', answer)
        self.assertEqual(confidence, .78)

    def test_country_does_not_dump_unverified_history(self):
        text = "Norveç, Kuzey Avrupa'da bulunan bir ülkedir. Başkenti Oslo'dur. Ülkenin geniş kıyıları ve dağlık bölgeleri vardır. Nüfusu yaklaşık 5 milyon kişidir.\nVIII. Haakon, Norveç'in mevcut kralıdır."
        answer, confidence = M.genel_web_cevabi('Norveç', [{'title':'Norveç','text':text,'_eagle_country_extract':True}])
        self.assertIn('Oslo', answer)
        self.assertNotIn('Haakon', answer)
        self.assertLess(confidence, .9)

    def test_structured_country_pipeline(self):
        import ast, re
        from pathlib import Path
        from unittest.mock import Mock
        from urllib.parse import quote
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_eagle_yapilandirilmis_ulke')
        requests = Mock()
        def claim(v, qualifiers=None):
            return {'rank':'normal','mainsnak':{'datavalue':{'value':v}},'qualifiers':qualifiers or {}}
        record = {'id':'Q40','labels':{'tr':{'value':'Avusturya'}},'claims':{'P297':[claim('AT')],'P36':[claim({'id':'Q1741'})],'P1082':[claim({'amount':'+9000000','unit':'1'},{'P585':[{'datavalue':{'value':{'time':'+2025-01-01T00:00:00Z'}}}]} )]}}
        scope = {'requests': requests, 'merkez_motor': M, 're': re, '_wikimedia_user_agent':lambda:'test'}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), 'country', 'exec'), scope)
        get = scope[fn.name]
        requests.get.return_value.json.side_effect = [{'entities':{'Q40':record}}, {'entities':{'Q1741':{'labels':{'tr':{'value':'Viyana'}}}}}]
        result = get('avusturya')
        answer, confidence = M.genel_web_cevabi('Avusturya', M.temizle_web_verisi([result]))
        self.assertIn('Viyana', answer)
        self.assertIn('9.000.000 (2025)', answer)
        self.assertEqual(confidence, .78)
        # Gerçek Norveç hatası: etiket yok, aynı kimliğin Wikipedia başlığı var.
        norway = {'id':'Q20','labels':{'tr':{'value':'Norveç'}},'claims':{'P297':[claim('NO')],'P36':[claim({'id':'Q585'})]}}
        requests.get.return_value.json.side_effect = [{'entities':{'Q20':norway}}, {'entities':{'Q585':{'labels':{},'sitelinks':{'trwiki':{'title':'Oslo'}}}}}]
        self.assertIn('Başkent: Oslo', get('norveç')['text'])
        self.assertEqual(requests.get.call_args.kwargs['params']['props'], 'labels|sitelinks')
        requests.get.return_value.json.side_effect = [{'entities':{'Q20':norway}}, {'entities':{'Q585':{'labels':{},'sitelinks':{}}}}]
        self.assertIsNone(get('norveç'))
        requests.get.return_value.json.side_effect = None
        for payload in ({'success':False,'data':None,'errors':[{'message':'deprecated'}]}, [], {'entities':{'Q40':record}}):
            requests.get.return_value.json.return_value = payload
            self.assertIsNone(get('meksika'))

    def test_research_failure_and_heritage(self):
        import ast, re
        from pathlib import Path
        from unittest.mock import Mock
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        names = {'_eagle_arastirma_yetersiz', '_eagle_ulke_miras'}
        scope = {'re': re, 'requests': Mock(), '_wikimedia_user_agent': lambda: 'test'}
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), 'research', 'exec'), scope)
        self.assertTrue(scope['_eagle_arastirma_yetersiz']("En son UFO'nun nerede görüldüğüne dair bir bilgi bulunmamaktadır."))
        self.assertFalse(scope['_eagle_arastirma_yetersiz']('Norveç. Başkent: Oslo.'))
        record = {'url': 'https://www.wikidata.org/wiki/Q20', 'text': 'Norveç.', 'snippet': 'Norveç.'}
        scope['requests'].get.return_value.json.return_value = {'results': {'bindings': [{'placeLabel': {'value': 'Bryggen'}}, {'placeLabel': {'value': 'Q123'}}]}}
        self.assertIn('Bryggen', scope['_eagle_ulke_miras'](record)['text'])
        scope['requests'].get.side_effect = TimeoutError('test')
        self.assertIn('Önceden alınmış Wikidata kaydı', scope['_eagle_ulke_miras'](record)['text'])
        self.assertEqual(scope['_eagle_ulke_miras'](dict(record, url='https://www.wikidata.org/wiki/Q40')), dict(record, url='https://www.wikidata.org/wiki/Q40'))

    def test_country_gallery_diversity(self):
        import ast, re
        from pathlib import Path
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_eagle_ulke_gorsel_cesitlendir')
        scope = {'re': re}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), 'gallery', 'exec'), scope)
        names = ['Trail, Gesause National Park, Austria', 'Stream, Gesause National Park, Austria', 'Mexico City skyline', 'Mexico City street', 'Royal Palace Oslo', 'Lake Bondhus']
        result = scope[fn.name]([{'name': n} for n in names], lambda n: re.sub(r'[^a-z0-9]+', ' ', n.lower()).strip())
        self.assertEqual(len(result), 4)
        self.assertIn('Royal Palace Oslo', [r['name'] for r in result[:3]])

    def test_current_event_filter_not_exact_place_title(self):
        import ast, re
        from pathlib import Path
        from eagle_arastirma_niyeti import anlati_istegi_mi
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        names = {'_web_sonucu_sorguyla_ilgili_mi', '_gerekli_web_eslesme_sayisi'}
        scope = {'re': re, 'merkez_motor': M, '_eagle_anlati_sorgusu_mu': anlati_istegi_mi}
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), 'filter', 'exec'), scope)
        check = scope['_web_sonucu_sorguyla_ilgili_mi']
        self.assertTrue(check('En son UFO nerede görüldü', {'title':'Yeni UFO gözlemi bildirildi','snippet':'Bir UFO gözlemi rapor edildi.'}))
        self.assertFalse(check('En son UFO nerede görüldü', {'title':'Futbol sonuçları','snippet':'Maç sonuçları açıklandı.'}))
        self.assertFalse(check('Atlantis nerede', {'title':'Atlantis filmi','snippet':'Atlantis filmi'}))

if __name__ == '__main__': unittest.main()
