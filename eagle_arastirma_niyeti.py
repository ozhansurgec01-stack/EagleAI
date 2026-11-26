"""Shared research/narrative intent rules; no network or model calls."""
import re


def anlati_istegi_mi(mesaj):
    m = str(mesaj or '').casefold().replace('\u0307', '')
    if re.search(r'\b(?:hikay\w*|hikâ[yv]\w*|öykü\w*|oyku\w*|efsane\w*|anekdot\w*|masal\w*|rivayet\w*)\b', m):
        return True
    olay = re.search(r'\b(?:olay\w*|vaka\w*|saldır\w*|saldir\w*|ufo\w*|kaçır\w*|kacir\w*|batış\w*|batis\w*|batma\w*|kaza\w*|felaket\w*|trajedi\w*|isyan\w*|devrim\w*|savaş\w*|savas\w*)\b', m)
    ayrinti = re.search(r'\b(?:anlat\w*|detay\w*|kronolojik|ayrınt\w*|ayrint\w*|başından sonuna|basindan sonuna)\b', m)
    yalın_olay = re.search(r'\b(?:olayı|olayi|vakası|vakasi)\s*[?!.]*$', m) and len(m.split()) <= 6
    return bool(olay and (ayrinti or yalın_olay))


def arastirma_karari(karar, gerekli):
    """Promote stale chat decisions, preserving all other decision fields."""
    sonuc = dict(karar or {})
    if gerekli and (sonuc.get('arac') in ('eagle_sohbet', 'genel_sohbet') or (not sonuc.get('arac') and sonuc.get('intent') in ('sohbet', 'basit_sohbet'))):
        sonuc.update(arac='web_arastirma', intent='web_arastirma')
    return sonuc
