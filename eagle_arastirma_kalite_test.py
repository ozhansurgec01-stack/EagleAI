import unittest
from eagle_merkez_motoru import EagleMerkezMotoru as M

class QualityTests(unittest.TestCase):
    def test_current_event_news_dates(self):
        import ast, re
        from pathlib import Path
        from unittest.mock import Mock
        from datetime import datetime, timezone, timedelta
        from email.utils import format_datetime
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        names = {'_eagle_guncel_olay_sorgusu', '_eagle_haber_kaynaklari', '_eagle_haber_basligi_uygun', '_eagle_olay_haber_ozeti'}
        scope = {'re': re, 'requests': Mock(), '_wikimedia_user_agent': lambda: 'test', '_web_sonucu_sorguyla_ilgili_mi': lambda q, r: True}
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), 'news', 'exec'), scope)
        self.assertTrue(scope['_eagle_guncel_olay_sorgusu']('En son UFO nerede görüldü'))
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
        self.assertEqual(result['research_status'], 'partial')
        self.assertIn('Tam metin doğrulanamadı', result['answer'])
        result = scope['_eagle_olay_haber_ozeti']('UFO', rows, lambda *a, **k: 'Gelibolu bölgesinde UFO görüldüğü iddiasının henüz bağımsız kaynaklar tarafından doğrulanmadığı açıklandı.', lambda h: 'https://example.org/article')
        self.assertIn('Kaynak metninden:', result['answer'])
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
        self.assertEqual(scope['_eagle_ulke_miras'](record), record)

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
