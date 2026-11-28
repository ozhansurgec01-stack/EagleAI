"""Independent, bounded research provider; no generative API dependency."""
import re
import requests

def konu_ayir(soru):
    soru = str(soru or "").strip()

    kaliplar = (
        r"(.+?)\s+(?:hakk[ıi]nda|ile ilgili|konusunda)\s+bilgi(?:\s+.*)?",
        r"(.+?)\s+(?:nedir|kimdir|ne demek|ne anlama gelir)",
        r"(.+?)\s+nas[ıi]l\s+bir\s+(?:[\w]+\s*){1,3}",
        r"(.+?)\s+(?:hakk[ıi]nda|ile ilgili)\s+(?:anlat|açıkla|acikla)",
        r"(.+?)\s+(?:anlat|tanıt|tanit|açıkla|acikla)(?:\s+.*)?",
    )

    soru = soru.rstrip("?! .")

    for kalip in kaliplar:
        match = re.fullmatch(kalip, soru, re.I)
        if match:
            konu = match.group(1).strip()

            konu = re.sub(
                r"(lerini|larını)$",
                lambda m: "leri" if m.group(0).lower() == "lerini" else "ları",
                konu,
                flags=re.I
            )

            konu = re.sub(
                r"['’](?:y?[ıiuü]|n?[ıiuü]n)$",
                "",
                konu,
                flags=re.I
            )

            return konu

    return ""

def _ansiklopedi_tek_sorgu(soru, get=None):
    konu = konu_ayir(soru)
    if not konu:
        return []
    get = get or requests.get
    headers = {"User-Agent": "EagleAI/2.0 (https://github.com/ozhansurgec01-stack/EagleAI)", "Accept": "application/json"}
    def norm(value):
        return " ".join(str(value).casefold().split())
    try:
        response = get("https://tr.wikipedia.org/w/api.php", params={"action":"query","titles":konu,"redirects":1,"prop":"extracts|pageprops|langlinks","lllang":"en","lllimit":1,"exintro":1,"explaintext":1,"format":"json","formatversion":2}, headers=headers, timeout=(3,5))
        if response.status_code != 200:
            return []
        rows = []
        query = response.json().get("query", {})
        kabul_edilen = {norm(konu)}

        for _ in range(5):
            for yon in (
                query.get("normalized", [])
                + query.get("redirects", [])
            ):
                if norm(yon.get("from", "")) in kabul_edilen:
                    hedef = norm(yon.get("to", ""))
                    if hedef:
                        kabul_edilen.add(hedef)

        for page in query.get("pages", []):
            if page.get("missing") or "disambiguation" in page.get("pageprops",{}):
                continue
            title = page.get("title","")
            extract = page.get("extract","").strip()
            if norm(title) not in kabul_edilen or len(extract) < 100:
                continue
            ingilizce_ad = ""
            for dil in page.get("langlinks", []):
                if dil.get("lang") == "en":
                    ingilizce_ad = str(
                        dil.get("title") or dil.get("*") or ""
                    ).strip()
                    break

            pageid = int(page["pageid"])
            rows.append({"title":title,"url":f"https://tr.wikipedia.org/?curid={pageid}","snippet":extract[:6000],"content_loaded":True,"topic_aliases":list(dict.fromkeys(
                [konu, title] + (
                    [ingilizce_ad] if ingilizce_ad else []
                )
            )), "english_title":ingilizce_ad})
        return rows
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return []


def kaynak_metni_kaliteli_mi(baslik, metin):
    import re
    import unicodedata

    metin = str(metin or "").strip()

    if len(metin) < 100:
        return False

    if metin.count("\ufffd") > 2:
        return False

    if re.search(r"[ÃÂ][\x80-\xbf]|Ä[±°]|Å[Ÿž]", metin):
        return False

    kontrol = metin[:3000]

    bozuk = sum(
        unicodedata.category(c).startswith("C")
        and c not in "\n\r\t"
        for c in kontrol
    )

    if bozuk > len(kontrol) * 0.01:
        return False

    if sum(c.isalpha() for c in kontrol) < len(kontrol) * 0.45:
        return False

    icerik = (str(baslik) + " " + kontrol)
    icerik = icerik.replace("İ", "i").replace("I", "ı")
    icerik = unicodedata.normalize("NFC", icerik.casefold())
    icerik = icerik.replace("\u0307", "")

    ticari = (
        r"sepete ekle",
        r"hemen satın al",
        r"alışveriş sepeti",
        r"ücretsiz kargo",
        r"taksit imkanı",
        r"taksit imkânı",
        r"havale.{0,5}eft",
        r"indirim fırsatı",
        r"sipariş ver",
    )

    if sum(bool(re.search(x, icerik)) for x in ticari) >= 2:
        return False

    return True


def kavram_norm(metin):
    import unicodedata
    metin = unicodedata.normalize('NFKD', str(metin or '').casefold())
    return ' '.join(re.findall(r'[a-z0-9]+', ''.join(c for c in metin if not unicodedata.combining(c)).replace('ı','i')))


def gorsel_kavram_eslesiyor(baslik, adlar):
    """Bir adın tamamı eşleşmeli; farklı adların parçaları birleştirilmez."""
    b = ' ' + kavram_norm(baslik) + ' '
    for ad in adlar:
        a = kavram_norm(ad)
        if len(a) >= 3 and re.search(r'(?<![a-z0-9])' + re.escape(a) + r'(?:s|es)?(?![a-z0-9])', b):
            return True
    return False


def ansiklopedi_tanimi(soru, kaynaklar):
    """Doğrulanmış başlık yönlendirmesinin girişinden sınırlı alıntı.
    Kaynak eşleşmesi, olgusal doğrulama anlamına gelmez.
    """
    konu = konu_ayir(soru)
    if not konu or not re.search(r'\bnedir\s*[?!. ]*$', soru, re.I):
        return ''
    for k in kaynaklar or []:
        if not isinstance(k, dict) or not k.get('content_loaded'):
            continue
        from urllib.parse import urlsplit
        if urlsplit(k.get('url','')).hostname != 'tr.wikipedia.org':
            continue
        adlar = k.get('topic_aliases') or []
        if not any(kavram_norm(a).replace(' ','') == kavram_norm(konu).replace(' ','') for a in adlar):
            continue
        metin = re.sub(r'\s+', ' ', str(k.get('snippet',''))).strip()
        metin = re.sub(r'\[\d+\]', '', metin)
        # Parantez içindeki nokta ve ondalık sayılar cümle sonu değildir.
        derinlik = 0
        for i, c in enumerate(metin[:550]):
            if c == '(': derinlik += 1
            elif c == ')': derinlik = max(0, derinlik-1)
            elif c == '.' and not derinlik and (i+1 == len(metin) or metin[i+1].isspace()):
                cumle = metin[:i+1].strip()
                n = kavram_norm(cumle)
                if not 35 <= len(cumle) <= 500: break
                if not any(n.startswith(kavram_norm(a)+' ') or n.replace(' ','').startswith(kavram_norm(a).replace(' ','')) for a in adlar if a): break
                if re.search(r'\b(?:[a-z]{3,}(?:dir|dur|tir|tur)|denir|adlandirilir|tanimlanir)$', n):
                    if not re.search(r'\b\w+(?:mistir|mustur|mistir|ilmistir|lanmistir|maktadir|mektedir)$', n):
                        return cumle
                break
    return ''


def kaynakli_tanim(soru, kaynaklar):
    """Conservative extractive answer; provenance is not factual verification."""
    from urllib.parse import urlsplit
    konu = konu_ayir(soru)
    if not konu or not re.search(r'\bnedir\s*[?!. ]*$', soru, re.I):
        return '', []
    adaylar = []
    for k in kaynaklar or []:
        if not isinstance(k, dict) or not k.get('content_loaded'):
            continue
        url = str(k.get('url') or '')
        try:
            host = urlsplit(url).hostname or ''
        except ValueError:
            continue
        if not host or not url.startswith(('https://','http://')):
            continue
        adlar = [konu]
        if host == 'tr.wikipedia.org':
            adlar += k.get('topic_aliases') or []
        metin = re.sub(r'\[\d+\]', '', str(k.get('snippet') or ''))
        for c in re.split(r'(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ])', metin[:6000]):
            c = ' '.join(c.split())
            n = kavram_norm(c)
            if not 35 <= len(c) <= 500 or not c.endswith('.'):
                continue
            if not any(n.startswith(kavram_norm(a)+' ') for a in adlar if a):
                continue
            if not re.search(r'\b(?:\w+(?:dir|dur|tir|tur)|denir|adlandirilir|tanimlanir)$', n):
                continue
            if re.search(r'\b\w+(?:mistir|mustur|maktadir|mektedir)$', n) or re.search(r'\b(?:baslica rolu|temel gorevi|en onemli ozelligi)\b', n):
                continue
            if re.search(r'\b(?:nedir|nelerdir|tiklayin|sepete ekle)\b', n):
                continue
            puan = 3 if host.endswith(('.edu.tr','.gov.tr','.edu','.gov')) else 2 if host == 'tr.wikipedia.org' else 1
            adaylar.append((puan, c, url, host))
            break
    adaylar.sort(key=lambda a: -a[0])
    if not adaylar:
        return '', []
    _, c, url, host = adaylar[0]
    return c, [{'url':url, 'title':host}]


def kavram_profili(konu, kaynaklar):
    """Mevcut arastirma kaynaklarindan kavram profili cikarir."""
    from urllib.parse import urlsplit
    from eagle_konu_siniflandirma import siniflandir

    hedef = kavram_norm(konu)

    if not hedef:
        return {}

    for k in kaynaklar or []:
        if not isinstance(k, dict):
            continue

        if k.get("content_loaded") is not True:
            continue

        url = urlsplit(str(k.get("url") or ""))

        if url.scheme != "https":
            continue

        if url.hostname != "tr.wikipedia.org":
            continue

        adlar = k.get("topic_aliases") or []

        if not isinstance(adlar, list):
            continue

        if not any(
            kavram_norm(a) == hedef
            for a in adlar
        ):
            continue

        metin = str(k.get("snippet") or "").strip()

        if not kaynak_metni_kaliteli_mi(
            k.get("title", ""), metin
        ):
            continue

        ingilizce = str(
            k.get("english_title") or ""
        ).strip()

        tanim = re.split(
            r"(?<=[.!?])\s+", metin, maxsplit=1
        )[0][:500]

        tur = siniflandir(
            konu=konu,
            aciklama=tanim,
            etiketler=adlar
        )

        return {
            "konu": konu,
            "ingilizce_ad": ingilizce,
            "etiketler": adlar,
            "aciklama": tanim,
            "tur": tur,
            "kaynak": k["url"]
        }

    return {}


def ansiklopedi_kaynaklari(soru, get=None):
    rows = _ansiklopedi_tek_sorgu(soru, get=get)

    if rows:
        return rows

    konu = konu_ayir(soru)

    if not konu:
        return []

    if not re.search(
        r"\b(?:anlat|tanıt|tanit|açıkla|acikla)\b",
        str(soru),
        re.I
    ):
        return []

    adaylar = []

    for ek in (
        "yı", "yi", "yu", "yü",
        "nı", "ni", "nu", "nü",
        "ı", "i", "u", "ü"
    ):
        if konu.lower().endswith(ek):
            aday = konu[:-len(ek)].strip()

            if len(aday) >= 3 and aday not in adaylar:
                adaylar.append(aday)

    for aday in adaylar:
        rows = _ansiklopedi_tek_sorgu(
            aday + " nedir?",
            get=get
        )

        if rows:
            for row in rows:
                aliases = row.setdefault(
                    "topic_aliases", []
                )
                if konu not in aliases:
                    aliases.append(konu)

            return rows

    return []
