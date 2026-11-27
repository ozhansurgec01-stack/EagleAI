"""Independent, bounded research provider; no generative API dependency."""
import re
import requests

def konu_ayir(soru):
    match = re.fullmatch(r"\s*(.+?)\s+(?:(?:hakk[ıi]nda|ile ilgili)\s+bilgi(?:\s+ver(?:ir)?\s*(?:m[ıi]s[ıi]n(?:[ıi]z)?)?)?|nedir|kimdir)\s*[?! .]*", str(soru), re.I)
    return match.group(1).strip() if match else ""

def ansiklopedi_kaynaklari(soru, get=None):
    konu = konu_ayir(soru)
    if not konu:
        return []
    get = get or requests.get
    headers = {"User-Agent": "EagleAI/2.0 (https://github.com/ozhansurgec01-stack/EagleAI)", "Accept": "application/json"}
    def norm(value):
        return " ".join(str(value).casefold().split())
    try:
        response = get("https://tr.wikipedia.org/w/api.php", params={"action":"query","titles":konu,"redirects":1,"prop":"extracts|pageprops","exintro":1,"explaintext":1,"format":"json","formatversion":2}, headers=headers, timeout=(3,5))
        if response.status_code != 200:
            return []
        rows = []
        for page in response.json().get("query",{}).get("pages",[]):
            if page.get("missing") or "disambiguation" in page.get("pageprops",{}):
                continue
            title = page.get("title","")
            extract = page.get("extract","").strip()
            if norm(title) != norm(konu) or len(extract) < 100:
                continue
            pageid = int(page["pageid"])
            rows.append({"title":title,"url":f"https://tr.wikipedia.org/?curid={pageid}","snippet":extract[:6000]})
        return rows
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return []
