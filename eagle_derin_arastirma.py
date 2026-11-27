"""Keyless discovery. Search metadata is never treated as evidence."""
import re
import sqlite3
import os
import time
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
import requests


def _url(url):
    try:
        u = urlsplit(str(url))
        return u.scheme == 'https' and bool(u.hostname) and not u.username and not u.password and u.port in (None, 443)
    except ValueError:
        return False


def _discover(provider, query):
    headers = {'User-Agent': 'EagleAI/1.0 research', 'Accept': 'application/json'}
    if provider == 'archive':
        # Search indexed item metadata, not full-text claims.
        terms = ' AND '.join('"' + w + '"' for w in re.findall(r'[^\W_]+', query)[:8])
        r = requests.get('https://archive.org/advancedsearch.php', params={'q': terms, 'fl[]': ['identifier','title','description'], 'rows': 8, 'output': 'json'}, headers=headers, timeout=(3, 5))
        r.raise_for_status()
        return [{'title': str(x.get('title','')), 'snippet': str(x.get('description',''))[:1500], 'url': 'https://archive.org/details/'+x['identifier']} for x in r.json().get('response',{}).get('docs',[]) if re.fullmatch(r'[A-Za-z0-9_.-]+', str(x.get('identifier','')))]
    if provider == 'openalex':
        r = requests.get('https://api.openalex.org/works', params={'search':query,'per-page':8}, headers=headers, timeout=(3,5))
        r.raise_for_status()
        out = []
        for x in r.json().get('results',[]):
            loc = x.get('best_oa_location') or x.get('primary_location') or {}
            out.append({'title': x.get('display_name') or '', 'snippet': '', 'url': loc.get('landing_page_url') or x.get('doi') or ''})
        return out
    lang = provider.split(':',1)[1]
    if lang not in ('en','es','de','tr'):
        return []
    r = requests.get('https://'+lang+'.wikipedia.org/w/api.php', params={'action':'query','list':'search','srsearch':query,'srlimit':8,'format':'json'}, headers=headers, timeout=(3,5))
    r.raise_for_status()
    return [{'title':x.get('title',''), 'snippet':re.sub('<[^>]+>','',x.get('snippet','')), 'url':'https://'+lang+'.wikipedia.org/?curid='+str(x['pageid'])} for x in r.json().get('query',{}).get('search',[]) if isinstance(x.get('pageid'),int)]


def _fixture_url(url):
    host = (urlsplit(url).hostname or '').lower().rstrip('.')
    return any(host == d or host.endswith('.' + d) for d in ('example.org', 'example.com', 'example.net', 'test', 'invalid', 'localhost'))


def _memory(key, sources=None):
    try:
        path = os.environ.get('EAGLE_KNOWLEDGE_DB', os.path.expanduser('~/.eagleai/knowledge.sqlite3'))
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with closing(sqlite3.connect(path, timeout=2)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS deep_source_urls (topic TEXT, url TEXT, title TEXT, saved REAL, PRIMARY KEY(topic,url))')
            if sources is not None:
                db.executemany('INSERT OR REPLACE INTO deep_source_urls VALUES (?,?,?,?)', [(key,s['url'],s.get('title',''),time.time()) for s in sources if _url(s.get('url')) and not _fixture_url(s['url'])])
                return []
            return [{'url':u,'title':t,'snippet':''} for u,t in db.execute('SELECT url,title FROM deep_source_urls WHERE topic=? AND saved>? ORDER BY saved DESC',(key,time.time()-30*86400)) if _url(u) and not _fixture_url(u)][:6]
    except (OSError, sqlite3.Error):
        return []


def remember_sources(topic, sources):
    """Store URLs of accepted extracts, not verified facts."""
    return _memory(" ".join(topic.casefold().split()), sources)


def _terms(text):
    import unicodedata
    text = ''.join(c for c in unicodedata.normalize('NFKD', str(text).casefold()) if not unicodedata.combining(c)).replace('ı','i')
    return set(re.findall(r'[^\W_]+', text))


def _rank(candidate, queries):
    title = _terms(candidate.get('title',''))
    body = _terms(candidate.get('snippet',''))
    stop = {'olay','olayini','olayi','incident','incidente','vorfall','anlat','historical','report','faciasi','disaster','accident','kazasi'}
    groups = [_terms(q)-stop for q in queries]
    aliases = {'ufo','ovni','ufos','ovnis','ufologie','ufology','satellite','satelite','object','objeto'}
    def score(group):
        core = {w for w in group if not w.isdigit()}
        def hits(words):
            return sum(w in words or (w in aliases and bool(words & aliases)) for w in core)
        return 8*hits(title)+2*hits(body)+3*len((group-core)&(title|body))
    return max(map(score,groups),default=0)


def discovery_candidates(rows, queries, limit=12):
    """Rank discovery metadata, never use it as factual evidence."""
    import base64
    from urllib.parse import parse_qs
    from ipaddress import ip_address
    from collections import Counter
    unique = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        url = str(row.get('url') or '')
        try:
            u = urlsplit(url)
            if u.hostname in ('www.bing.com', 'bing.com') and u.path == '/ck/a':
                token = parse_qs(u.query).get('u', [''])[0]
                if not token.startswith('a1'):
                    continue
                token = token[2:]
                url = base64.urlsafe_b64decode(token + '=' * (-len(token) % 4)).decode()
            if not _url(url) or _fixture_url(url):
                continue
            host = urlsplit(url).hostname
            if '.' not in host or host.endswith(('.local', '.internal')):
                continue
            try:
                ip_address(host)
                continue  # No literal IP targets in search discovery.
            except ValueError:
                pass
        except (ValueError, UnicodeError):
            continue
        candidate = dict(row, url=url, _eagle_deep_candidate=True)
        if url not in unique or _rank(candidate, queries) > _rank(unique[url], queries):
            unique[url] = candidate
    ranked = sorted(unique.values(), key=lambda a: _rank(a, queries), reverse=True)
    counts = Counter()
    out = []
    for a in ranked:
        host = urlsplit(a['url']).hostname.removeprefix('www.')
        if counts[host] >= 2:
            continue
        counts[host] += 1
        out.append(a)
        if len(out) >= limit:
            break
    return out


def archive_text(url, limit=12000, timeout=5):
    """Read public OCR text from the fixed Archive API, not item HTML."""
    from urllib.parse import quote
    u = urlsplit(url)
    m = re.fullmatch(r'/details/([A-Za-z0-9_.-]+)',u.path)
    if u.hostname != 'archive.org' or not m or not _url(url):
        return ''
    ident = m.group(1)
    try:
        r = requests.get('https://archive.org/metadata/'+ident, timeout=(3,timeout), allow_redirects=False)
        if r.status_code != 200:
            return ''
        files = r.json().get('files',[])
        for f in files:
            name = str(f.get('name',''))
            if not name.endswith('_djvu.txt') or '/' in name or '\\' in name:
                continue
            with requests.get('https://archive.org/download/'+ident+'/'+quote(name,safe=''), timeout=(3,timeout), stream=True, allow_redirects=False) as response:
                if response.status_code != 200:
                    continue
                data = bytearray()
                for chunk in response.iter_content(8192):
                    data.extend(chunk)
                    if len(data)>=min(limit*4,48000):
                        break
                return bytes(data).decode('utf-8','replace')[:limit]
    except (requests.RequestException, ValueError, TypeError):
        pass
    return ''


def research(topic, variants, validate, reader, discover=_discover):
    """Two bounded discovery rounds; existing evidence validator remains authoritative."""
    key = ' '.join(topic.casefold().split())
    cached = _memory(key)
    seen = set()
    def check(candidates):
        fresh = []
        for a in candidates:
            url = a.get('url','')
            if not _url(url) or url in seen:
                continue
            seen.add(url)
            print("DERIN ADAY:", str(a.get("title", ""))[:180], url, flush=True)
            fresh.append(dict(a, _eagle_deep_candidate=True))
        fresh.sort(key=lambda a: _rank(a, [topic]+list(variants)), reverse=True)
        result = validate(topic, fresh[:12], reader) if fresh else None
        if result and result.get('ok'):
            _memory(key, result.get('research_sources',[]))
        return result
    result = check(cached)
    if result:
        return result
    queries = list(dict.fromkeys([topic]+list(variants)))[:4]
    short_queries = [re.sub(r"\b(?:olay\w*|incident|incidente|vorfall|anlat|facias[ıi]|disaster|accident)\b", " ", q, flags=re.I).strip() for q in queries]
    def run(job):
        provider, q = job
        try:
            rows = discover(provider,q)
            print('DERIN ARASTIRMA:',provider,q,len(rows),flush=True)
            return rows
        except Exception as exc:
            print('DERIN ARASTIRMA:',provider,type(exc).__name__,flush=True)
            return []
    for jobs in ([('wiki:'+('tr' if i==0 else 'es' if re.search(r'\b(?:OVNI|incidente)\b',q,re.I) else 'de' if 'Vorfall' in q else 'en'),q) for i,q in enumerate(queries)], [('archive',q) for q in short_queries[1:3] or short_queries]+[('openalex',q) for q in short_queries[1:3] or short_queries]):
        with ThreadPoolExecutor(max_workers=4) as pool:
            groups = list(pool.map(run,jobs))
        # Round-robin avoids one provider consuming the candidate budget.
        candidates = [g[i] for i in range(max(map(len,groups),default=0)) for g in groups if i<len(g)]
        result = check(candidates)
        if result:
            return result
    return None

def _search_rows(provider, query, locale):
    """Independent search adapters; no generic web parser or query suffixes."""
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin, parse_qs
    import xml.etree.ElementTree as ET
    endpoints = {
        'bing-rss': ('https://www.bing.com/search', {'q':query,'format':'rss','mkt':locale}),
        'ddg-lite': ('https://lite.duckduckgo.com/lite/', {'q':query,'kl':locale.lower()}),
        'google': ('https://www.google.com/search', {'q':query,'hl':locale[:2],'num':10}),
        'mojeek': ('https://www.mojeek.com/search', {'q':query}),
    }
    url, params = endpoints[provider]
    with requests.get(url, params=params, headers={'User-Agent':'Mozilla/5.0','Accept-Language':locale}, timeout=(3,6), stream=True) as r:
        print('ANLATI SAGLAYICI:', provider, r.status_code, r.url, flush=True)
        r.raise_for_status()
        if r.status_code != 200:
            return []
        data = bytearray()
        for chunk in r.iter_content(16384):
            data.extend(chunk)
            if len(data)>2_000_000:
                return []
    if provider == 'bing-rss':
        return [{'title':x.findtext('title',''), 'url':x.findtext('link',''), 'snippet':x.findtext('description','')} for x in ET.fromstring(data).findall('.//item')][:12]
    soup = BeautifulSoup(bytes(data),'html.parser')
    rows = []
    for node in soup.select({'ddg-lite':'a.result-link','google':'h3','mojeek':'h2'}[provider])[:15]:
        a = node if node.name=='a' else node.find_parent('a',href=True) or node.find('a',href=True)
        if not a:
            continue
        target = urljoin(url,a.get('href',''))
        u = urlsplit(target)
        if u.hostname in ('www.google.com','google.com','duckduckgo.com','lite.duckduckgo.com'):
            p = parse_qs(u.query)
            target = (p.get('uddg') or p.get('q') or p.get('url') or [''])[0]
        rows.append({'title':node.get_text(' ',strip=True),'url':target,'snippet':''})
    return rows


def _metadata_relevant(row, queries):
    # Require topical anchors, not merely a matching date. Weak metadata is
    # allowed only when it contains at least one actual topic anchor.
    words = _terms(' '.join(str(row.get(k,'')) for k in ('title','snippet','url')))
    stop = {'olay','olayi','olayini','incident','incidente','vorfall','anlat','historical','report','faciasi','disaster','accident','kazasi','haber','arsiv'}
    aliases = {'ufo','ovni','ufos','ovnis','ufology','ufologie','uap'}
    for q in queries:
        core = {w for w in _terms(q)-stop if not w.isdigit()}
        hits = {w for w in core if w in words or (w in aliases and words & aliases) or any(w+s in words for s in ('n','na','no','an','ian'))}
        if core and len(hits)>=min(2,len(core)):
            return True
        if hits and len(core)<=3 and any(w.isdigit() and w in words for w in _terms(q)):
            return True
    return False


def search_web(topic, variants, limit=12):
    queries = list(dict.fromkeys([topic]+list(variants)))[:4]
    jobs = []
    for q in queries:
        short = ' '.join(re.sub(r'\b(?:olay\w*|incident|incidente|vorfall|anlat|facias[ıi]|disaster|accident)\b',' ',q,flags=re.I).split())
        locale = 'es-ES' if re.search(r'\bOVNI\b',q,re.I) else 'de-DE' if 'Vorfall' in q else 'tr-TR' if q==topic else 'en-US'
        jobs.extend((p,short,locale) for p in ('bing-rss','ddg-lite','google','mojeek'))
    jobs = list(dict.fromkeys(jobs))
    def run(job):
        try:
            rows = _search_rows(*job)
            good = [r for r in rows if _metadata_relevant(r,queries)]
            print('ANLATI SAGLAYICI KALITE:',job[0],len(good),'/',len(rows),flush=True)
            return good
        except Exception as exc:
            print('ANLATI SAGLAYICI HATA:',job[0],type(exc).__name__,flush=True)
            return []
    with ThreadPoolExecutor(max_workers=8) as pool:
        groups = list(pool.map(run,jobs))
    return discovery_candidates([r for g in groups for r in g],queries,limit)
