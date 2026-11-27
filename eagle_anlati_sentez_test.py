import unittest
from unittest.mock import patch
from eagle_anlati_sentez import narrative_extract, translate_local

class NarrativeTests(unittest.TestCase):
    def test_end_preserved(self):
        rows = ['A historical report from 1978 establishes the topic.'] + [f'Investigation detail {i}: witnesses described the incident and investigators recorded their accounts.' for i in range(45)] + ['The investigation concluded without finding physical remains.', 'Tienes acceso libre a 200 notas al mes.', 'Unrelated advertisement must not be returned.']
        out = ' '.join(narrative_extract(rows, 0, 1))
        self.assertIn(rows[0], out)
        self.assertIn(rows[-3], out)
        self.assertNotIn(rows[-1], out)
        self.assertLessEqual(len(out), 3500)
    def test_disabled_translation(self):
        with patch.dict('os.environ', {'EAGLE_LOCAL_TRANSLATION':'0'}):
            self.assertEqual(translate_local('Texto original'), ('Texto original', False))

    def test_loopback_translation(self):
        import sys
        import json
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        original = 'El informe fue publicado en 1978.'
        detector = SimpleNamespace(detect_langs=lambda t: [SimpleNamespace(lang='es', prob=.99)], DetectorFactory=SimpleNamespace(seed=None))
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({'ok':True,'source_language':'es','originals':[original],'translations':['Rapor 1978 yılında yayımlandı.'],'translation_status':'machine_translation_unverified'}).encode()
        with patch.dict('os.environ', {'EAGLE_LOCAL_TRANSLATION':'1'}), patch.dict(sys.modules, {'langdetect':detector}), patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value = response
            self.assertEqual(translate_local(original), ('Rapor 1978 yılında yayımlandı.', True))
            self.assertEqual(opener.return_value.open.call_args.args[0].full_url, 'http://127.0.0.1:8765/translate')
            opener.return_value.open.side_effect = TimeoutError
            self.assertEqual(translate_local(original), (original, False))
            opener.return_value.open.side_effect = None
            response.__enter__.return_value.read.return_value = json.dumps({'ok':True,'source_language':'es','originals':[original],'translations':['Rapor 1979 yılında yayımlandı.'],'translation_status':'machine_translation_unverified'}).encode()
            self.assertEqual(translate_local(original), (original, False))

    def test_middle_preserved(self):
        rows = [f'Investigation detail {i}: witnesses described the incident and investigators recorded their accounts.' for i in range(60)]
        out = narrative_extract(rows, 0, 1)
        self.assertIn(rows[30], out)
        self.assertIn(rows[-1], out)
        self.assertIn('[…]', out)
        self.assertLessEqual(len(' '.join(out)), 3500)

    def test_partial_source_translation(self):
        from eagle_anlati_sentez import translate_sources
        text = 'The first witness described an unusual object. The investigators searched the surrounding region. The final report did not establish its origin.'
        with patch.dict('os.environ', {'EAGLE_ONLINE_TRANSLATION':'0'}), patch('eagle_anlati_sentez.translate_local', side_effect=[('İlk tanık nesneyi anlattı.', True), ('', False), ('Son rapor kökenini belirlemedi.', True)]) as tr:
            rows = translate_sources([{'text': text}])
            self.assertEqual(len(rows[0]), 2)
            self.assertEqual(len({c.kwargs['deadline'] for c in tr.call_args_list}), 1)

    def test_zero_budget(self):
        from eagle_anlati_sentez import translate_sources
        with patch.dict('os.environ', {'EAGLE_ONLINE_TRANSLATION':'0'}), patch('eagle_anlati_sentez.translate_local') as tr:
            self.assertEqual(translate_sources([{'text': 'A sufficiently long sentence for translation.'}], budget=0), [[]])
            tr.assert_not_called()

    def test_online_cache_and_validation(self):
        import tempfile, sys, json
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        from eagle_anlati_sentez import translate_online
        original = 'El informe fue publicado en 1978.'
        target = 'Rapor 1978 yılında yayımlandı.'
        detector = SimpleNamespace(detect_langs=lambda t: [SimpleNamespace(lang='es' if t.startswith('El') else 'tr', prob=.99)], DetectorFactory=SimpleNamespace(seed=None))
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({'responseStatus':200,'responseData':{'translatedText':target}}).encode()
        with tempfile.TemporaryDirectory() as d, patch.dict('os.environ', {'EAGLE_TRANSLATION_DB':d+'/test.db'}), patch.dict(sys.modules, {'langdetect':detector}), patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value = response
            self.assertEqual(translate_online(original), (target, True))
            self.assertEqual(translate_online(original), (target, True))
            self.assertEqual(opener.return_value.open.call_count, 1)
            self.assertEqual(translate_online(original+'x'*500), (original+'x'*500, False))
            self.assertEqual(translate_online(original.replace('1978','1979')), (original.replace('1978','1979'), False))
            response.__enter__.return_value.read.return_value = json.dumps({'responseStatus':429,'quotaFinished':True}).encode()
            self.assertEqual(translate_online(original+' A'), (original+' A', False))
            count = opener.return_value.open.call_count
            self.assertEqual(translate_online(original+' B'), (original+' B', False))
            self.assertEqual(opener.return_value.open.call_count,count)

    def test_online_parallel_partial(self):
        from eagle_anlati_sentez import translate_sources
        text = 'The first witness described an unusual object. The investigators searched the surrounding region. The final report did not establish its origin.'
        with patch.dict('os.environ', {'EAGLE_ONLINE_TRANSLATION':'1'}), patch('eagle_anlati_sentez._detect_languages', return_value=[__import__('types').SimpleNamespace(lang='en', prob=.99)]), patch('eagle_anlati_sentez.translate_online', side_effect=lambda t,d,lang: (t+' translated', not t.startswith('The investigators'))):
            rows = translate_sources([{'text':text}])
            self.assertEqual(len(rows[0]),2)
            self.assertTrue(rows[0][0][0].startswith('The first'))

    def test_news_tail_removed(self):
        rows = ['The witnesses described an unusual object in 1978.', 'html La temperatura subirá con fuerza en Tucumán.', 'Unrelated political news.']
        self.assertEqual(narrative_extract(rows, 0, 1), rows[:1])

    def test_language_detection_serialized(self):
        import sys, time
        from types import SimpleNamespace
        from concurrent.futures import ThreadPoolExecutor
        from eagle_anlati_sentez import _detect_languages
        active = []
        def detect(text):
            self.assertFalse(active)
            active.append(text)
            time.sleep(.01)
            active.pop()
            return text
        detector = SimpleNamespace(detect_langs=detect, DetectorFactory=SimpleNamespace(seed=None))
        with patch.dict(sys.modules, {'langdetect':detector}), ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(list(pool.map(_detect_languages, ['a','b','c','d'])), ['a','b','c','d'])

    def test_evidence_selection_real_excerpt(self):
        from eagle_anlati_sentez import evidence_indices
        rows = [
            'This article was published in the daily newspaper Nice-Matin, France, on May 17, 1978.',
            'crashed so that one finally knows what these odd objects are?',
            'Los tarijeños vieron un objeto largo que botaba fuego y creyeron que había explotado en terrenos cercanos a la frontera con Argentina.',
            'Corría el 6 de mayo de 1978, eran las 17:00 horas.',
            'Rápidamente se formó una comisión de exploración, y quien la encabezó fue el geólogo Daniel Centeno.',
            'Entramos una primera vez y una segunda vez, pero no ubicamos nada.',
            'Luego del evento comenzó el rumor de que la NASA había enviado un equipo para hacer una expedición en Tarija.',
        ]
        self.assertEqual(evidence_indices(rows, 6), [2,3,4,5,6])

    def test_online_selection_byte_budget(self):
        from eagle_anlati_sentez import translate_sources
        from types import SimpleNamespace
        texts = [{'text': ' '.join('The witnesses described an unusual object in the region and investigators searched for evidence number %d. ' % j for j in range(12))} for i in range(3)]
        with patch.dict('os.environ', {'EAGLE_ONLINE_TRANSLATION':'1'}), patch('eagle_anlati_sentez._detect_languages', return_value=[SimpleNamespace(lang='en',prob=.99)]), patch('eagle_anlati_sentez.translate_online', side_effect=lambda t,d,l:(t,True)) as tr:
            result = translate_sources(texts)
            self.assertTrue(all(result))
            self.assertGreater(tr.call_count, 9)
            self.assertLessEqual(sum(len(c.args[0].encode()) for c in tr.call_args_list),2400)


class NarrativeFormattingTests(__import__('unittest').TestCase):
    def test_incomplete_translation_not_presented_as_fact(self):
        from eagle_anlati_sentez import format_narrative
        out = format_narrative([{'text':'a'}, {'text':'b'}], [[('a','Ancak araştırmanın sonucunda')], [('b','Kalıntı bulunamadı.')]])
        self.assertNotIn('Ancak araştırmanın sonucunda', out)
        self.assertIn('[1] Kullanılabilir tam cümle bulunamadı.', out)
        self.assertIn('[2] Kalıntı bulunamadı.', out)

    def test_flat_header(self):
        from eagle_anlati_sentez import clean_sentence
        self.assertEqual(clean_sentence('Title | Title 31 Marzo 2019, 13:07 | Un hecho ocurrió en 1978.'), 'Un hecho ocurrió en 1978.')
        self.assertEqual(clean_sentence('Corría el 6 de mayo de 1978, eran las 17:00 horas.'), 'Corría el 6 de mayo de 1978, eran las 17:00 horas.')

    def test_attribution_and_exact_duplicate(self):
        from eagle_anlati_sentez import format_narrative
        out = format_narrative([{'text':'a'},{'text':'b'},{'text':'original'}], [[('a','Tanıklar ışık gördü.')],[('b','Tanıklar ışık gördü.'),('c','Kalıntı bulunamadı.')],[]])
        self.assertEqual(out.count('Tanıklar ışık gördü.'),1)
        self.assertIn('[1] [2] Tanıklar ışık gördü.',out)
        self.assertIn('[3] Türkçe çeviri alınamadı.',out)
        self.assertIn('bağımsız doğrulanmadı',out)

    def test_possible_disagreement_and_attribution(self):
        from eagle_anlati_sentez import format_narrative
        out = format_narrative([{'text':'a'},{'text':'b'}], [[('a','Araştırmacılar hiçbir kalıntı bulamadı.')],[('b','Bilim heyeti birkaç kutu getirdi.'),('c','Olay 6 Mayıs 1978 tarihinde meydana geldi.')]])
        self.assertIn('olası farklılık', out)
        self.assertIn('[1] Araştırmacılar hiçbir kalıntı bulamadı.', out)
        self.assertIn('[2] Bilim heyeti birkaç kutu getirdi.', out)
        self.assertLess(out.index('6 Mayıs'),out.index('kalıntı'))
        self.assertNotIn('[…]',out)

    def test_no_conflict_from_same_source(self):
        from eagle_anlati_sentez import format_narrative
        out = format_narrative([{'text':'a'}], [[('a','Araştırmacılar kalıntı bulamadı.'),('b','Heyet kutu getirdi.')]])
        self.assertNotIn('olası farklılık',out)


class NarrativeRegressionTests(__import__('unittest').TestCase):
    def test_publication_not_event(self):
        from eagle_anlati_sentez import evidence_indices
        rows = ['The mystery magazine NOSTRA #323 for July 1, 1978, published in France, told about this: LA PAZ.', 'Corría el 6 de mayo de 1978, eran las 17:00 horas.', 'Los testigos vieron una luz en el cielo en 1978.']
        self.assertEqual(evidence_indices(rows, 2), [1, 2])

    def test_physical_description_disagreement(self):
        from eagle_anlati_sentez import format_narrative
        out = format_narrative([{'text':'a'}, {'text':'b'}], [[('a','Zaten çelikten yapıldığı ve oval bir şekle sahip olduğu bilinmektedir.')], [('b','Araştırmacılar hiçbir şey bulamadı.')]])
        self.assertIn('olası farklılık', out)

    def test_turkish_bypasses_translation(self):
        from eagle_anlati_sentez import translate_sources
        from types import SimpleNamespace
        text = 'Araştırmacılar olayın nedenini belirlemek için bölgeyi inceledi.'
        with patch.dict('os.environ', {'EAGLE_ONLINE_TRANSLATION':'1'}), patch('eagle_anlati_sentez._detect_languages', return_value=[SimpleNamespace(lang='tr',prob=.99)]), patch('eagle_anlati_sentez.translate_online') as tr:
            self.assertEqual(translate_sources([{'text':text}]), [[(text,text)]])
            tr.assert_not_called()

    def test_caption_and_bounded_fallback(self):
        from eagle_anlati_sentez import format_narrative
        out = format_narrative([{'text':'a'},{'text':'original '*500}], [[('a','Ormanın 1938 yılında çekilmiş fotoğraf.')],[]])
        self.assertNotIn('1938',out)
        self.assertLess(len(out),700)
