"""Bounded extract and optional offline translation; never invent facts."""
import re
import os
from threading import Lock

_language_lock = Lock()

def _detect_languages(text):
    from langdetect import detect_langs, DetectorFactory
    with _language_lock:
        DetectorFactory.seed = 0
        return detect_langs(text)


# Multilingual cues rank evidence, not its truth. Keep source order in output.
_METADATA = re.compile(r"this article was published|published in the daily newspaper|este art[ií]culo fue publicado|about the author|(?:magazine|revista|dergisi).{0,180}(?:published|publicad|yayımlanan|yazıyordu)|^html\b", re.I)
_OUTCOME = re.compile(r"no encontraron|sin encontrar|no ubicamos|no hab[ií]a|no se encontr|no hallaron|no evidence|found no|did not find|without finding|no remains|conclu|resultado|final report|informe final|keine|aucun|kalıntı|bulunamad|не обнаруж", re.I)
_ACTION = re.compile(r"investig|explor|comisi[oó]n|ge[oó]log|research|search|expedition|enqu[eê]te|untersuch|araştır|исслед|rumor|s[oö]ylenti", re.I)
_EVENT = re.compile(r"testig|testimon|witness|observ|vieron|escuch|explosi|explosion|tanık|görgü|patla|zeugen|t[eé]moin|свидетел", re.I)
_DATE = re.compile(r"\b(?:18|19|20)\d{2}\b|\b\d{1,2}:\d{2}\b")


# Strip flattened publisher headers only when a clear body delimiter exists.
_CAPTION = re.compile(r"(?:çekilmiş fotoğraf|fotoğrafı çekildi|photograph taken|photo taken|pictured here|^al[aı]na kurulan çadırlardan biri)", re.I)

_SITE_NOISE = re.compile(r"haberleri sayfasında|son dakika haberleri|haber başlıkları|web.de devam et|uygulamayı aç|köşe yazarlarına dikkat|sayfamızdan takip|toplam \d+ .{0,100}haberi|^peki,|^.{0,100}kimlerden oluşuyor\?|\b(?:duruşmasında|çarptıran|serisinin).{0,100}\d+\.$", re.I)

def clean_sentence(text):
    if '|' in text:
        parts = text.split('|')
        if re.search(r'\b\d{1,2}:\d{2}\b', '|'.join(parts[:-1])):
            text = parts[-1].strip()
    return text.strip()


# Conservative presentation categories: not semantic entailment.
_TR_OUTCOME = re.compile(r'bulunamad|bulamad|bulamadan|sonuçsuz|tespit edilemedi|kanıt yok|belirlenemedi|rastlanmad', re.I)
_TR_ACTION = re.compile(r'araştır|incele|komisyon|heyet|keşif|jeolog', re.I)
_TR_EVENT = re.compile(r'tanık|gördü|gözlem|patla|sarsıntı|meydana geldi|gerçekleşti', re.I)
_TR_RECOVERY = re.compile(r'(?:getirdi|getiren|ele geçir|çıkarıldı|bulundu|toplandı|çelikten yapıldığı|oval bir şekle sahip)', re.I)
_TR_OBJECT = re.compile(r'kalıntı|enkaz|parça|kutu|paket|cisim|nesne|çelikten yapıldığı|oval bir şekle sahip', re.I)
_TR_DATE = re.compile(r'\b\d{1,2}\s+(?:ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)\s+\d{4}\b', re.I)


def narrative_key(text):
    return re.sub(r'[^\w]+', ' ', text.casefold().replace('\u0307', '')).strip()


def format_narrative(sources, translated):
    """Organize attributed extracts without inventing links or resolving claims."""
    groups = {k: [] for k in ('Olayın başlangıcı ve gözlemler', 'Araştırma çalışmaları', 'Bulgular ve sonuçlar', 'Diğer aktarımlar')}
    seen = {}
    missing = []
    negative, recovery = set(), set()
    for i, source in enumerate(sources, 1):
        rows = translated[i-1] if i <= len(translated) else []
        if not rows:
            missing.append(f'[{i}] Türkçe çeviri alınamadı. Kaynak bağlantısından özgün metne ulaşılabilir.')
            continue
        for original, target in rows:
            target = target.strip()
            if target.endswith("?") or re.match(r"^[A-ZİŞĞÜÇÖ0-9 ]{18,} [A-ZİŞĞÜÇÖ][a-zçğıöşü]", target):
                continue
            if _SITE_NOISE.search(original) or _SITE_NOISE.search(target) or _METADATA.search(original) or _METADATA.search(target) or _CAPTION.search(original) or _CAPTION.search(target):
                continue
            key = narrative_key(target)
            if not key or re.search(r"\b\d+\.$", target) or (target.isupper() and len(target) > 15) or not re.search(r'[.!?][”"’)]*$', target):
                continue
            if key in seen:
                seen[key][1].add(i)
                continue
            # Only merge punctuation/spacing variants, never approximate claims.
            compact = key.replace(' ', '')
            equivalent = next((entry for old, entry in seen.items()
                               if len(compact) >= 30 and old.replace(' ', '') == compact), None)
            if equivalent is not None:
                equivalent[1].add(i)
                continue
            outcome = bool(_TR_OUTCOME.search(target))
            recovered = bool(_TR_RECOVERY.search(target) and _TR_OBJECT.search(target))
            if outcome:
                negative.add(i)
            if recovered and not outcome:
                recovery.add(i)
            group = ('Bulgular ve sonuçlar' if outcome or recovered or re.search(r'\b(?:mahkeme|hapis cezası|hüküm giy|beraat|tahliye)', target, re.I) else
                     'Araştırma çalışmaları' if _TR_ACTION.search(target) else
                     'Olayın başlangıcı ve gözlemler' if _TR_EVENT.search(target) or _TR_DATE.search(target) or re.search(r'\b(?:kaybol|gündemine geldi|başladı)', target, re.I) else 'Diğer aktarımlar')
            entry = [target, {i}]
            seen[key] = entry
            groups[group].append(entry)
        if not any(i in entry[1] for entry in seen.values()):
            missing.append(f'[{i}] Kullanılabilir tam cümle bulunamadı. Kaynak bağlantısından özgün metne ulaşılabilir.')
    paragraphs = []
    for heading, entries in groups.items():
        if not entries:
            continue
        if heading == 'Olayın başlangıcı ve gözlemler':
            def date_key(entry):
                years = re.findall(r'\b(?:18|19|20)\d{2}\b', entry[0])
                return int(years[0]) if years else 9999
            entries.sort(key=date_key)
        paragraphs.append(heading + ':\n' + ' '.join(
            ' '.join(f'[{i}]' for i in sorted(ids)) + ' ' + target for target, ids in entries))
    if any(a != b for a in negative for b in recovery):
        paragraphs.append('Kaynaklar arasındaki olası farklılık:\nBazı aktarımlarda sonuçsuz arama, diğerlerinde nesne veya malzeme bulunduğu, taşındığı ya da fiziksel özelliklerinin belirlendiği yönünde ifadeler var. Bunların aynı araştırmaya ilişkin olup olmadığı ve iddiaların doğruluğu belirlenmedi.')
    return ('Kaynaklardan düzenlenmiş seçili aktarımlar (otomatik çeviriler ve olay bağımsız doğrulanmadı; tam metin değildir):\n\n' + '\n\n'.join(paragraphs + missing))


def evidence_indices(rows, limit):
    eligible = [i for i,c in enumerate(rows) if 25 <= len(c) and len(c.encode('utf-8')) <= 500
                and not _SITE_NOISE.search(c) and not _METADATA.search(c) and not _CAPTION.search(c) and re.match(r'[“"¿¡(]*[A-ZÀ-ÖØ-ÞА-ЯЁİŞĞÜÇÖ]', c)
                and re.search(r'[.!?][”"’)]*$', c)]
    chosen = []
    # Reserve distinct slots for the event, date, investigation and outcome.
    for cue in (_EVENT, _DATE, _ACTION, _OUTCOME):
        candidates = [i for i in eligible if i not in chosen and cue.search(rows[i])]
        if candidates and len(chosen) < limit:
            chosen.append(max(candidates, key=lambda i: (bool(_OUTCOME.search(rows[i])) if cue is _OUTCOME else bool(re.search(r"\b\d{1,2}\s+(?:de\s+)?[A-Za-zÀ-ÿ]+\s+(?:de\s+)?\d{4}\b|\b\d{1,2}:\d{2}\b", rows[i])) if cue is _DATE else False, -i)))
    for i in sorted(eligible, key=lambda i: (-sum(bool(c.search(rows[i])) for c in (_OUTCOME,_ACTION,_EVENT,_DATE)), i)):
        if len(chosen) >= limit:
            break
        if i not in chosen:
            chosen.append(i)
    return sorted(chosen)


def narrative_extract(sentences, start, anchor_count):
    selected = []
    for c in sentences[start:start+60]:
        if re.search(r'cookie|çerez|subscribe|suscripci[oó]n|iniciar sesi[oó]n|abone olun|privacy policy|captcha|tienes acceso libre|related articles|egresad[oa] de ciencias de la comunicaci[oó]n|se desempeña como periodista|about the author', c, re.I):
            break
        if re.search(r'\bhtml\s+La temperatura|\b(?:noticias relacionadas|últimas noticias|más noticias|también te puede interesar|related news|read more)\b', c, re.I):
            break
        if not 15 <= len(c) <= 900:
            continue
        if c not in selected:
            selected.append(c)
    # Reserve space for beginning, middle and conclusion, in original order.
    if len(' '.join(selected)) <= 3500:
        return selected
    n = len(selected)
    chosen = set(range(min(anchor_count, n)))
    def add(indices, budget):
        used = 0
        for i in indices:
            if i in chosen:
                continue
            cost = len(selected[i]) + 1
            if used + cost > budget or sum(len(selected[j])+6 for j in chosen)+cost+6 > 3450:
                continue
            chosen.add(i)
            used += cost
    add(evidence_indices(selected, 6), 1450)
    add(range(n-1, -1, -1), 950)
    add(range(n//2, n), 950)
    add(range(n), 1100)
    out = []
    previous = -1
    for i in sorted(chosen):
        if i > previous+1:
            out.append('[…]')
        out.append(selected[i])
        previous = i
    return out


def translate_local(text, deadline=None):
    """Opt-in loopback NLLB service; fail closed to the original text."""
    if os.getenv('EAGLE_LOCAL_TRANSLATION') != '1':
        return text, False
    try:
        import json
        import urllib.request
        from langdetect import detect_langs, DetectorFactory
        DetectorFactory.seed = 0
        languages = detect_langs(text)
        if not languages or languages[0].prob < .90:
            return text, False
        code = languages[0].lang
        if code not in {'en', 'es', 'de', 'fr', 'ru'}:
            return text, False
        chunks = re.split(r'(?<=[.!?])\s+|\s*(?=\[…\])|(?<=\[…\])\s*', text)
        chunks = [c.strip() for c in chunks if c.strip()]
        originals = [c for c in chunks if c != '[…]']
        if not originals or len(originals) > 40 or any(len(c) > 900 for c in originals):
            return text, False
        # Do not follow redirects or use environment HTTP proxies.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        import time
        deadline = deadline if deadline is not None else time.monotonic() + 30
        translated = []
        for i in range(0, len(originals), 3):
            batch = originals[i:i+3]
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("translation budget exhausted")
            req = urllib.request.Request('http://127.0.0.1:8765/translate',
                data=json.dumps({'lang': code, 'texts': batch}).encode(),
                headers={'Content-Type': 'application/json'})
            with opener.open(req, timeout=min(remaining, 25)) as response:
                raw = response.read(65537)
            if len(raw) > 65536:
                return text, False
            data = json.loads(raw)
            out = data.get('translations')
            if (data.get('ok') is not True or data.get('source_language') != code
                    or data.get('originals') != batch
                    or data.get('translation_status') != 'machine_translation_unverified'
                    or not isinstance(out, list) or len(out) != len(batch)
                    or any(not isinstance(t, str) or not t.strip() for t in out)):
                return text, False
            # Reject obvious changes to numeric facts, not a semantic guarantee.
            if any(sorted(re.findall(r'\d+', a)) != sorted(re.findall(r'\d+', b))
                   for a, b in zip(batch, out)):
                print("ANLATI CEVIRI RED: sayisal uyumsuzluk", flush=True)
                return text, False
            translated.extend(out)
        it = iter(translated)
        return ' '.join(c if c == '[…]' else next(it) for c in chunks), True
    except Exception as exc:
        print(f'ANLATI CEVIRI YOK: {type(exc).__name__}', flush=True)
    return text, False


def translate_online(text, deadline=None, source_lang=None):
    """Public-source excerpts only; conservative local daily quota and cache."""
    import json
    import sqlite3
    import time
    import urllib.request
    import urllib.parse
    from contextlib import closing
    try:
        lang = source_lang
        if lang is None:
            langs = _detect_languages(text)
            lang = langs[0].lang if langs and langs[0].prob >= .90 else None
        if lang not in {'en','es','de','fr','ru'}:
            return text, False
        cost = len(text.encode('utf-8'))
        if not 0 < cost <= 500:
            return text, False
        deadline = deadline if deadline is not None else time.monotonic()+8
        path = os.getenv('EAGLE_TRANSLATION_DB', os.path.expanduser('~/.eagleai/translation.sqlite3'))
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        day = time.strftime('%Y-%m-%d', time.gmtime())
        with closing(sqlite3.connect(path, timeout=1)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS translations (lang TEXT, source TEXT, target TEXT, PRIMARY KEY(lang,source))')
            db.execute('CREATE TABLE IF NOT EXISTS quota (day TEXT PRIMARY KEY, used INTEGER)')
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT target FROM translations WHERE lang=? AND source=?',(lang,text)).fetchone()
            if row:
                return row[0], True
            row = db.execute('SELECT used FROM quota WHERE day=?',(day,)).fetchone()
            used = row[0] if row else 0
            if used+cost > 5000 or time.monotonic() >= deadline:
                return text, False
            db.execute('INSERT OR REPLACE INTO quota VALUES (?,?)',(day,used+cost))
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):
                return None
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        url = 'https://api.mymemory.translated.net/get?' + urllib.parse.urlencode({'q':text,'langpair':lang+'|tr'})
        remaining = deadline-time.monotonic()
        if remaining <= 0:
            return text, False
        with opener.open(url, timeout=min(remaining, 5)) as response:
            raw = response.read(65537)
        if len(raw)>65536:
            return text, False
        data = json.loads(raw)
        if data.get('quotaFinished') is True or str(data.get('responseStatus')) == '429':
            with closing(sqlite3.connect(path, timeout=1)) as db, db:
                db.execute('INSERT OR REPLACE INTO quota VALUES (?,?)',(day,5000))
            return text, False
        if str(data.get('responseStatus')) != '200' or data.get('responseDetails'):
            return text, False
        out = data.get('responseData',{}).get('translatedText')
        if not isinstance(out,str) or not out.strip() or out.strip()==text.strip():
            return text, False
        import html
        out = html.unescape(out).strip()
        if sorted(re.findall(r'\d+',text)) != sorted(re.findall(r'\d+',out)):
            return text, False
        if not .25 <= len(out)/len(text) <= 4 or re.search(r'MYMEMORY WARNING|QUOTA EXCEEDED|INVALID LANGUAGE',out,re.I):
            return text, False
        target = _detect_languages(out)
        if not target or target[0].lang != 'tr' or target[0].prob < .80:
            return text, False
        with closing(sqlite3.connect(path, timeout=1)) as db, db:
            db.execute('INSERT OR REPLACE INTO translations VALUES (?,?,?)',(lang,text,out))
        return out, True
    except Exception as exc:
        print(f'ANLATI ONLINE CEVIRI YOK: {type(exc).__name__}',flush=True)
        return text, False

def translate_sources(sources, budget=45):
    """Translate short, distributed excerpts; preserve each successful sentence."""
    import time
    deadline = time.monotonic() + budget
    selections = []
    online = os.getenv('EAGLE_ONLINE_TRANSLATION', '1') == '1'
    for source in sources:
        sentences = [clean_sentence(x) for x in re.split(r'(?<=[.!?])\s+|\s*\[…\]\s*', source['text']) if 25 <= len(clean_sentence(x)) <= (500 if online else 400)]
        indices = evidence_indices(sentences, 6) if online else (sorted(set([0, len(sentences)//2, len(sentences)-1])) if sentences else [])
        selections.append([sentences[i] for i in indices])
    results = [[] for _ in sources]
    langs = []
    for i, source in enumerate(sources):
        try:
            detected = _detect_languages(source['text'][:3500])
            lang = detected[0].lang if detected and detected[0].prob >= .90 else None
        except Exception:
            lang = None
        # If optional language detection is absent or uncertain, recognize only
        # strongly Turkish prose; a Turkish URL alone is not evidence of language.
        if lang is None:
            words = re.findall(r"[^\W\d_]+", source['text'].casefold(), re.UNICODE)
            markers = {'bir','ve','ile','olarak','için','sonra','önce','ancak','tarafından','olan','bu','olduğu','göre'}
            if len(set(words) & markers) >= 4 and sum(bool(re.search(r'[çğıöşü]', w)) for w in words) >= 5:
                lang = 'tr'
        langs.append(lang)
        if lang == 'tr':
            results[i] = [(c, c) for c in selections[i]]
            selections[i] = []
    if os.getenv('EAGLE_ONLINE_TRANSLATION', '1') == '1':
        from concurrent.futures import ThreadPoolExecutor, wait
        deadline = min(deadline, time.monotonic()+8)
        jobs = [(i, sentences[j]) for j in range(6) for i, sentences in enumerate(selections) if j < len(sentences) and langs[i] in {'en','es','de','fr','ru'}]
        bounded = []
        used = 0
        for i, original in jobs:
            cost = len(original.encode('utf-8'))
            if used + cost <= 2400:
                bounded.append((i, original))
                used += cost
        jobs = bounded
        if not jobs or time.monotonic() >= deadline:
            return results
        jobs = [(i, original) for i, original in jobs if langs[i] in {'en','es','de','fr','ru'}]
        if not jobs:
            return results
        pool = ThreadPoolExecutor(max_workers=4)
        futures = [pool.submit(translate_online, original, deadline, langs[i]) for i, original in jobs]
        try:
            done, _ = wait(futures, timeout=max(0,deadline-time.monotonic()))
            for (i, original), future in zip(jobs, futures):
                if future in done:
                    try:
                        translated, ok = future.result()
                    except Exception:
                        continue  # A failed provider must not discard other sources.
                    if ok:
                        results[i].append((original, translated))
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
        return results
    for j in range(3):
        for i, sentences in enumerate(selections):
            if j >= len(sentences) or time.monotonic() >= deadline:
                continue
            original = sentences[j]
            translated, ok = translate_local(original, deadline=deadline)
            if ok:
                results[i].append((original, translated))
    return results
