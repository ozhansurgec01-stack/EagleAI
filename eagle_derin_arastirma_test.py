import os
import tempfile
import unittest
from unittest.mock import patch
from eagle_derin_arastirma import research

class DeepTests(unittest.TestCase):
    def test_fallback_and_memory(self):
        calls=[]
        def discover(p,q):
            calls.append(p)
            return [{'url':'https://archive.org/details/mock-story','title':q}] if p=='archive' else []
        def validate(q, rows, reader):
            return {'ok':True,'research_sources':rows} if rows else None
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'EAGLE_KNOWLEDGE_DB':d+'/test.sqlite'}):
            self.assertTrue(research('topic',['topic en'],validate,None,discover)['ok'])
            self.assertIn('archive',calls)
            calls.clear()
            self.assertTrue(research('topic',['topic en'],validate,None,discover)['ok'])
            self.assertEqual(calls,[])
    def test_metadata_not_evidence(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'EAGLE_KNOWLEDGE_DB':d+'/test.sqlite'}):
            self.assertIsNone(research('topic',[],lambda *a:None,None,lambda *a:[{'url':'https://example.org/story','title':'topic'}]))

    def test_deep_metadata_does_not_block_reading(self):
        import ast
        from pathlib import Path
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        names = {'_eagle_tarihsel_web_kanit', '_eagle_anlati_video_mu'}
        scope = {'_eagle_cok_dilli_anlati_sorgulari': lambda q: ['1978 Bolivia OVNI incidente'],
                 '_web_sonucu_sorguyla_ilgili_mi': lambda q,a: all(w in a['title'] for w in ('1978','Bolivia','OVNI'))}
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'test','exec'),scope)
        run = scope['_eagle_tarihsel_web_kanit']
        a = {'title':'Regional archive','url':'https://example.org/story','_eagle_deep_candidate':True}
        body = ('En 1978 Bolivia registró un relato sobre un OVNI observado por varios habitantes de la región. '
                'El documento describe las declaraciones de los testigos sin confirmar el origen del objeto. ') * 3
        self.assertTrue(run('1978 Bolivya UFO',[a],lambda *args,**kw:body)['ok'])
        self.assertIsNone(run('1978 Bolivya UFO',[a],lambda *args,**kw:body.replace('1978','1979')))
        self.assertIsNone(run('1978 Bolivya UFO',[a],lambda *args,**kw:body.replace('OVNI','lluvia')))

    def test_rank_before_budget(self):
        from eagle_derin_arastirma import _rank
        q=['1978 Bolivia UFO','1978 Bolivia OVNI']
        good={'title':'Bolivia reports conflict on details of fallen object'}
        bad={'title':'Chromosome numbers in Bolivian grasses'}
        self.assertGreater(_rank(good,q),_rank(bad,q))
        self.assertGreater(_rank(good,q),_rank({'title':'CIA case log'},q))

    def test_archive_ocr(self):
        from eagle_derin_arastirma import archive_text
        from unittest.mock import MagicMock
        meta=MagicMock(status_code=200)
        meta.json.return_value={'files':[{'name':'doc_djvu.txt'}]}
        response=MagicMock(status_code=200)
        response.__enter__.return_value=response
        response.iter_content.return_value=[b'Historical document text.']
        with patch('eagle_derin_arastirma.requests.get',side_effect=[meta,response]) as get:
            self.assertEqual(archive_text('https://archive.org/details/doc'),'Historical document text.')
            self.assertEqual(get.call_args.args[0],'https://archive.org/download/doc/doc_djvu.txt')
        self.assertEqual(archive_text('https://example.org/details/doc'),'')

    def test_normal_web_memory_and_duplicate(self):
        import ast
        from pathlib import Path
        from eagle_derin_arastirma import _memory
        tree = ast.parse(Path(__file__).with_name('eagle_api.py').read_text())
        scope = {'_eagle_cok_dilli_anlati_sorgulari': lambda q: [], '_web_sonucu_sorguyla_ilgili_mi': lambda *a: True}
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'_eagle_tarihsel_web_kanit','_eagle_anlati_video_mu'}],type_ignores=[]),'test','exec'),scope)
        body = 'In 1978 the topic was investigated by several researchers who interviewed local witnesses. The researchers published a report describing the evidence and its limitations. ' + ' '.join(f'Investigation record {i} describes the observations of witnesses and the subsequent review of evidence.' for i in range(35))
        rows = [{'title':'Topic report','url':f'https://{host}.example.org/story'} for host in ('a','b')]
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'EAGLE_KNOWLEDGE_DB':d+'/test.sqlite','EAGLE_LOCAL_TRANSLATION':'0'}):
            result = scope['_eagle_tarihsel_web_kanit']('1978 topic',rows,lambda url,**kw:body + (' About the author. Extra biographical material.' if 'b.example' in url else ''))
            self.assertEqual(len(result['research_sources']),1)
            self.assertEqual(_memory('1978 topic'), [])
            from eagle_derin_arastirma import remember_sources
            remember_sources('1978 topic', result['research_sources'])
            self.assertEqual(_memory('1978 topic'), [])
            remember_sources('1978 topic', [{'url':'https://archive.org/details/mock-story','title':'Mock'}])
            self.assertEqual(_memory('1978 topic')[0]['url'], 'https://archive.org/details/mock-story')
            self.assertFalse(result['event_verified'])

    def test_discovery_keeps_candidates_and_decodes_bing(self):
        import base64
        from eagle_derin_arastirma import discovery_candidates
        url = 'https://archive.org/details/regional-report'
        token = base64.urlsafe_b64encode(url.encode()).decode().rstrip('=')
        rows = [{'title':'Regional report','url':'https://www.bing.com/ck/a?u=a1'+token},
                {'title':'Regional report','url':url},
                {'title':'Fixture','url':'https://example.org/story'},
                {'title':'Local','url':'https://127.0.0.1/story'}]
        out = discovery_candidates(rows,['1978 Bolivia UFO'])
        self.assertEqual(len(out),1)
        self.assertEqual(out[0]['url'],url)
        self.assertTrue(out[0]['_eagle_deep_candidate'])

    def test_independent_search_quality(self):
        from eagle_derin_arastirma import search_web
        rows = [{'title':'WiFi speed test','url':'https://news.example.edu/wifi'},
                {'title':'Mecoya: OVNI en Bolivia en 1978','url':'https://news.example.edu/report'}]
        with patch('eagle_derin_arastirma._search_rows',return_value=rows):
            out=search_web('1978 Bolivya UFO',['1978 Bolivia OVNI incidente'])
        self.assertEqual([r['url'] for r in out],['https://news.example.edu/report'])

    def test_rss_adapter(self):
        from eagle_derin_arastirma import _search_rows
        from unittest.mock import MagicMock
        r=MagicMock(status_code=200,url='https://www.bing.com/search')
        r.__enter__.return_value=r
        r.iter_content.return_value=[b'<rss><channel><item><title>Report</title><link>https://news.example.edu/report</link><description>Text</description></item></channel></rss>']
        with patch('eagle_derin_arastirma.requests.get',return_value=r) as get:
            self.assertEqual(_search_rows('bing-rss','1978 Bolivia OVNI','es-ES')[0]['title'],'Report')
            self.assertEqual(get.call_args.kwargs['params']['q'],'1978 Bolivia OVNI')
