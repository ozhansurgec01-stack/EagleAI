"""Conservative extractive research, with explicit provenance; no LLM."""
import re
from urllib.parse import urlsplit
from eagle_arastirma_v2 import kavram_norm, konu_ayir


def topic(question):
    return konu_ayir(question) or (re.fullmatch(r'\s*(.+?)\s+(?:ne demek|ne anlama gelir)\s*[?!. ]*', question, re.I).group(1) if re.fullmatch(r'\s*(.+?)\s+(?:ne demek|ne anlama gelir)\s*[?!. ]*', question, re.I) else '')


def sentences(text):
    text = re.sub(r'\[\d+\]', '', str(text or ''))[:6000]
    for c in re.split(r'(?<=[.!?])\s+|\n+', text):
        c = ' '.join(c.split())
        if 20 <= len(c) <= 500 and c.endswith('.') and c[0].isupper() and not re.search(r'[?…]|\.\.\.|\ufffd', c):
            yield c


def matches(n, names):
    for a in names:
        if not a:
            continue

        if re.search(
            r"(?<!\w)" + re.escape(a) + r"(?!\w)",
            n
        ):
            return True

        if len(a) >= 4:
            ekler = (
                r"(?:in|un|nin|nun|"
                r"inin|unun|"
                r"lari|leri|larin|lerin)"
            )

            if re.search(
                r"(?<!\w)" + re.escape(a)
                + ekler + r"(?!\w)",
                n
            ):
                return True

    return False


def build_answer(question, rows):
    name = topic(question)
    names = {kavram_norm(name)} - {''}
    candidates = []
    for row in rows or []:
        if not isinstance(row, dict) or row.get('content_loaded') is not True:
            continue
        url = str(row.get('url') or '')
        try:
            parsed = urlsplit(url)
            host = parsed.hostname or ''
        except ValueError:
            continue
        if parsed.scheme not in ('http','https') or not host:
            continue
        if host == 'tr.wikipedia.org' and any(kavram_norm(a).replace(' ','') == kavram_norm(name).replace(' ','') for a in row.get('topic_aliases',[]) if isinstance(a,str)):
            names.update(kavram_norm(a) for a in row['topic_aliases'] if isinstance(a,str))
        candidates.append((row,host,url))
    definitions, details = [], []
    for row,host,url in candidates:
        authority = 4 if host.endswith(('.edu.tr','.gov.tr','.edu','.gov')) else 2 if host == 'tr.wikipedia.org' else 0
        title = kavram_norm(row.get('title',''))
        if not matches(title,names):
            continue
        for i,c in enumerate(sentences(row.get('snippet'))):
            n = kavram_norm(c)
            if not matches(n,names) or re.search(r'\b(?:nedir|nelerdir|tiklayin|sepete ekle|bu yazimizda|bu makalede)\b',n):
                continue
            start = any(n.startswith(a+' ') for a in names if a)
            predicate = bool(re.search(r'\b(?:\w+(?:dir|dur|tir|tur)|denir|adlandirilir|tanimlanir)$',n))
            side = bool(re.search(r'\b(?:baslica rolu|temel gorevi|en onemli ozelligi|bir parcasidir)\b|\b\w+(?:mistir|mustur|maktadir|mektedir)$',n))
            item = (authority*10 + max(0,5-i),c,url,host)
            if start and predicate and not side:
                definitions.append(item)
            elif not side:
                details.append(item)
    if not definitions:
        return {'ok':False,'answer':'Bu konu için güvenilir bir tanım çıkaramadım.','research_sources':[],'research_status':'insufficient'}
    definitions.sort(reverse=True)
    chosen = [definitions[0]]
    for item in sorted(details,reverse=True):
        words=set(kavram_norm(item[1]).split())
        if any(len(words & set(kavram_norm(x[1]).split()))/max(1,len(words | set(kavram_norm(x[1]).split()))) > .45 for x in chosen):
            continue
        chosen.append(item)
        if len(chosen)==3: break
    sources=list(dict.fromkeys(x[2] for x in chosen))
    return {'ok':True,'answer':'\n\n'.join(x[1]+' ['+str(sources.index(x[2])+1)+']' for x in chosen)+'\n\nKaynaklar (bağımsız doğrulama yapılmadı):\n'+'\n'.join(f'{i+1}. {u}' for i,u in enumerate(sources)), 'research_sources':[{'id':i+1,'url':u,'independently_verified':False} for i,u in enumerate(sources)],'research_status':'unverified_source_extract'}
