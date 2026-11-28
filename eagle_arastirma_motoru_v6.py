"""Eagle Research V6 - deterministic evidence processing."""

import re
from urllib.parse import urlsplit
from eagle_arastirma_v2 import kavram_norm
from eagle_arastirma_motoru_v5 import topic, sentences, matches

NOISE = re.compile(
    r"goz korkutucu|bu yazimizda|bu makalede|"
    r"tiklayin|sepete ekle|son dakika|"
    r"hakkinda bilgi al|tum haklari saklidir|"
    r"reklam|abone olun|"
    r"\b(?:com|net|org) tr\b"
)

DEPENDENT = re.compile(
    r"^(?:cunku|ancak|fakat|dolayisiyla|"
    r"bunun sonucunda|bu nedenle|bu yuzden|"
    r"bu molekuller|bu durum|bu tanimlamaya gore|bu hizda|boylece|"
    r"sise acildiginda)\b"
)

FUNCTION = re.compile(
    r"\b(?:temel gorev|temel islev|baslica gorev|"
    r"enerji uret|atp|sentez|islev|"
    r"gorevi|gorevleri|rolu|islevi)"
)

MECHANISM = re.compile(
    r"\b(?:mekanizma|surec|donus|"
    r"gercekles|olus|tepkime|reaksiyon)"
)

EXAMPLE = re.compile(
    r"\b(?:ornegin|mesela|ornek olarak)\b"
)

DEFINITION = re.compile(
    r"\b(?:\w+(?:dir|dur|tir|tur)|"
    r"denir|adlandirilir|tanimlanir)$"
)

def source_info(url):
    try:
        p = urlsplit(str(url or ""))
        if p.scheme not in ("http", "https"):
            return "", 0
        host = (p.hostname or "").lower()
        if not host:
            return "", 0
        if host.endswith(
            (".edu.tr", ".gov.tr", ".edu", ".gov")
        ):
            return host, 4
        if host == "tr.wikipedia.org":
            return host, 2
        return host, 1
    except ValueError:
        return "", 0


def quality(text):
    if not isinstance(text, str):
        return False

    text = text.strip()

    # Yarım kalmış kişi baş harfleri ve Roma rakamları.
    if re.search(r"\s(?:[A-ZÇĞİÖŞÜ]|[IVXLCDM]{2,})\.$", text):
        return False

    # Boş dil ve metadata alanları.
    if re.search(r":\s*[;)]", text):
        return False

    # Remove malformed metadata before sentence selection, not factual prose.
    n = kavram_norm(text)

    if not n or NOISE.search(n):
        return False

    # Karsilastirma evrensel iddialari tek kaynakla guvenli degildir.
    if re.search(r"\b(?:diger tum|diger butun|tum diger|butun diger)\b", n):
        return False

    if DEPENDENT.search(n):
        return False

    if re.search(r"https?://|www\.|\.com\b", text):
        return False

    # Tamamlanmamis cumleleri ele.
    if not text.endswith("."):
        return False

    if "\ufffd" in text or "..." in text or "…" in text:
        return False

    # Bozuk parantez ve koseli parantez yapisi.
    eslesmeler = {")": "(", "]": "["}
    yigin = []

    for karakter in text:
        if karakter in "([":
            yigin.append(karakter)
        elif karakter in ")]":
            if not yigin or yigin.pop() != eslesmeler[karakter]:
                return False

    if yigin:
        return False

    # Cumleye karismis SEO ve makale basliklari.
    if re.search(
        r"\bhakkinda\s+(?:genel\s+)?bilgi\s*[:;]",
        text.lower().replace("ı", "i")
    ):
        return False

    if re.search(
        r"\b(?:hakkinda bilgi|hakkinda her sey|"
        r"merak edilenler|bilmeniz gerekenler)\b",
        n
    ) and re.search(r"[:;]", text):
        return False

    # Eksik sembol ve bozuk liste aktarimi.
    if re.search(
        r"[:;,]\s*(?:veya|yahut|ya da)\s*[,;)\]]",
        text,
        re.I
    ):
        return False

    return True



def classify(text, names):
    n = kavram_norm(text)

    starts = any(
        n.startswith(a + " ")
        for a in names if a
    )

    if EXAMPLE.search(n):
        return "example"

    explicit_function = re.search(
        r"\b(?:temel gorev|temel islev|"
        r"baslica gorev|gorevi|gorevleri|"
        r"islevi|rolu)\b", n
    )

    property_end = re.search(
        r"\b(?:sahiptir|icerir|bulunur|"
        r"olusur|sahip)\b$", n
    )

    if explicit_function:
        return "function"

    if property_end:
        return "property"

    # Ozellik ve eylem bildiren cumleler.
    if re.search(
        r"\b(?:vardir|yoktur|bulunmaktadir|"
        r"sahiptir|icermektedir|"
        r"\w+mistir|\w+mustur|"
        r"\w+maktadir|\w+mektedir)\b$",
        n
    ):
        return "property"

    # Ilgi ekiyle baslayan ozellik ifadeleri.
    if any(
        re.match(
            r"^" + re.escape(a)
            + r"\s+(?:in|un|nin|nun)\s+",
            n
        )
        for a in names if a
    ):
        return "property"

    if starts and DEFINITION.search(n):
        return "definition"

    # Ansiklopedik biyografi tanimlari.
    if (
        starts
        and re.search(
            r"\(\s*\d{1,2}\s+\w+\s+\d{4}",
            text
        )
        and re.search(
            r"\b(?:fizikci|kimyager|matematikci|"
            r"bilim adami|bilim insani|"
            r"yazar|sair|sanatci|oyuncu|"
            r"muzisyen|filozof|muhendis|"
            r"politikaci|tarihci|akademisyen|"
            r"hekim|besteci|ressam|sporcu)$",
            n
        )
    ):
        return "definition"

    if FUNCTION.search(n):
        return "function"

    if MECHANISM.search(n):
        return "mechanism"

    return "property"


def similarity(a, b):
    x = set(kavram_norm(a).split())
    y = set(kavram_norm(b).split())
    return len(x & y) / max(1, len(x | y))




def redundant_fact(a, b):
    # A dated biography already contains its birth year. Do not repeat
    # a bare birth statement, but preserve new birthplace details.
    def birth_year(text):
        n = kavram_norm(text)
        m = re.search(r"\b(\d{4})\b", n)
        if m and (re.search(r"\b(?:dogdu|dogmustur|dunyaya gelmistir|dunyaya geldi)\b", n)
                  or re.search(r"\(\s*\d{1,2}\s+\w+\s+\d{4}", text)):
            return m.group(1)
        return None
    if birth_year(a) and birth_year(a) == birth_year(b):
        x, y = kavram_norm(a), kavram_norm(b)
        # Only suppress a birth statement if its location is already present.
        for short, long in ((x, y), (y, x)):
            m = re.search(r"\b\d{4}\s+(?:senesinde |yilinda )?(\w+)\s+(?:da|de)\s+(?:dunyaya gelmistir|dunyaya geldi|dogdu|dogmustur)$", short)
            if m and re.search(r"\b" + re.escape(m.group(1)) + r"\b", long):
                return True
    return False


def v6_sentences(text, names):
    text = re.sub(
        r'\[\d+\]', '', str(text or '')
    )[:6000]

    for c in re.split(
        r'(?<=[.!?])\s+|\n+', text
    ):
        c = ' '.join(c.split())
        c = re.sub(r'\s*\([^()]*;\s*sembolleri\s*:\s*(?:veya|yahut|ya da)\s*\)', '', c, flags=re.I)

        if not c:
            continue

        if len(c) >= 20:
            accepted = list(sentences(c))

            if accepted:
                yield from accepted
            else:
                yield ""

            continue

        if (
            c[0].isupper()
            and quality(c)
            and matches(kavram_norm(c), names)
            and classify(c, names) == "definition"
        ):
            yield c
        else:
            yield ""


def information_score(text):
    n = kavram_norm(text)
    score = 0

    patterns = (
        (5, r"\b(?:temel gorev\w*|temel islev\w*|"
            r"baslica gorev\w*|gorevi|islevi)\b"),

        (4, r"\b(?:uretir|ureten|sentezler|"
            r"donusturur|donusturen|saglar|"
            r"calisma prensibi)\b"),

        (3, r"\b(?:baskenti|nufusu|yuzolcumu|"
            r"resmi dili|para birimi|"
            r"kesfedildi|icat edildi)\b"),

        (2, r"\b(?:olusur|icerir|sahiptir|"
            r"gerceklesir|bulunur)\b"),

        (-3, r"\b(?:adini almistir|"
             r"sembolu|sozcuklerinden|"
             r"etimolojik)\b"),
    )

    for weight, pattern in patterns:
        if re.search(pattern, n):
            score += weight

    return score


def build_answer(question, rows):
    name = topic(question)
    names = {kavram_norm(name)} - {""}

    empty = {
        "ok": False,
        "answer": (
            "Bu konu için yeterli kaynak "
            "temelli açıklama çıkaramadım."
        ),
        "research_sources": [],
        "research_status": "insufficient"
    }

    if not names:
        return empty

    sources = []

    for row in rows or []:
        if not isinstance(row, dict):
            continue
        if row.get("content_loaded") is not True:
            continue

        url = str(row.get("url") or "")
        host, authority = source_info(url)

        if not host:
            continue

        aliases = {
            kavram_norm(a)
            for a in row.get("topic_aliases", [])
            if isinstance(a, str)
        } - {""}

        if host == "tr.wikipedia.org" and names & aliases:
            names.update(aliases)

        sources.append((row, url, host, authority))

    candidates = []

    for source_index, item in enumerate(sources):
        row, url, host, authority = item

        if not matches(
            kavram_norm(row.get("title", "")), names
        ):
            continue

        context_budget = 0

        for position, text in enumerate(
            v6_sentences(row.get("snippet"), names)
        ):
            if not quality(text):
                context_budget = 0
                continue

            normalized = kavram_norm(text)
            direct = matches(normalized, names)

            if direct:
                category = classify(text, names)
                context_budget = (
                    3 if category == "definition" else 0
                )
            else:
                contextual = bool(
                    re.match(
                        r"^(?:kendi\s|"
                        r"(?:\w+\s){0,2}\w{3,}(?:i|u)\s)",
                        normalized
                    )
                    or (
                        re.match(
                            r"^\w{3,}(?:de|da|te|ta)\s",
                            normalized
                        )
                        and re.search(
                            r"\b(?:gerceklesir|olusur|"
                            r"meydana gelir|uretilir)\b$",
                            normalized
                        )
                    )
                )

                explicit_entity = bool(
                    re.search(
                        r"\b[A-ZÇĞİÖŞÜ][\w]+['’]",
                        text
                    )
                    or re.match(
                        r"^\w+\s+(?:gezegeni|yildizi|ulkesi|"
                        r"sehri|devleti|nehri|dagi|golu|"
                        r"okyanusu|denizi)\b",
                        normalized
                    )
                )

                if (
                    context_budget <= 0
                    or not contextual
                    or explicit_entity
                ):
                    context_budget = 0
                    continue

                context_budget -= 1
                category = "property"

            candidates.append({
                "text": text,
                "url": url,
                "host": host,
                "authority": authority,
                "source_index": source_index,
                "position": position,
                "category": category
            })

    # Ortak anlamsal kavram ayrimi.
    from eagle_anlamsal_tur import anlamsal_tur

    tur_gruplari = {}

    for aday in candidates:
        if aday["category"] != "definition":
            continue

        tur = anlamsal_tur(aday["text"])

        if tur == "unknown":
            continue

        tur_gruplari.setdefault(tur, []).append(aday)

    if len(tur_gruplari) > 1:
        tur_kanitlari = [
            {
                "type": tur,
                "text": aday["text"],
                "source": aday["url"]
            }
            for tur, grup in tur_gruplari.items()
            for aday in grup
        ]

        return {
            **empty,
            "research_engine": "v6",
            "research_status": "entity_type_uncertain",
            "research_entity_types": sorted(tur_gruplari),
            "research_entity_evidence": tur_kanitlari,
            "answer": (
                "Kaynaklarda bu kavram icin farkli "
                "varlik turleri bulundu. Bilgileri "
                "yanlis bicimde birlestirmemek icin "
                "kesin bir aciklama sunamiyorum."
            )
        }

    # Merkezi kanit dogrulama.
    from eagle_kanit_dogrulama import celiskileri_bul

    celiskiler = celiskileri_bul(candidates)

    engellenen = {
        (e["text"], e["source"])
        for c in celiskiler
        for e in c["evidence"]
    }

    candidates = [
        c for c in candidates
        if (c["text"], c["url"]) not in engellenen
    ]

    # Prefer established sources; do not fill an answer with unsupported
    # details from arbitrary sites. Keep all candidates for conflict detection.
    trusted = [c for c in candidates if c["authority"] >= 2]
    eligible = trusted if trusted else candidates

    definitions = [
        c for c in eligible
        if c["category"] == "definition"
    ]

    if not definitions and celiskiler:
        return {
            **empty,
            "research_engine": "v6",
            "research_status": "unresolved_conflicts",
            "research_conflicts": celiskiler,
            "answer": (
                "Kaynaklarda uyusmayan bilgiler bulundu. "
                "Guvenilir bir tanim olusturulamadi."
            )
        }

    if not definitions:
        return empty

    def rank(c):
        return (
            -c["authority"],
            -information_score(c["text"]),
            c["position"],
            c["source_index"]
        )

    chosen = [min(definitions, key=rank)]
    # Without an established source, return only a provisional definition.
    if not trusted:
        eligible = []

    for category in (
        "function",
        "mechanism",
        "property",
        "example"
    ):
        group = sorted(
            (
                c for c in eligible
                if c["category"] == category
            ),
            key=rank
        )

        for c in group:
            if any(
                similarity(c["text"], x["text"]) > .45
                or redundant_fact(c["text"], x["text"])
                for x in chosen
            ):
                continue

            chosen.append(c)

            if category != "property":
                break

            if sum(
                x["category"] == "property"
                for x in chosen
            ) >= 3:
                break

    urls = list(dict.fromkeys(
        c["url"] for c in chosen
    ))

    evidence = []

    # Identical text on another host is not independent verification.

    for c in chosen:
        supporting_urls = list(dict.fromkeys(
            other["url"]
            for other in candidates
            if other["host"] != c["host"]
            and kavram_norm(other["text"])
            == kavram_norm(c["text"])
        ))

        evidence.append({
            "category": c["category"],
            "text": c["text"],
            "source": c["url"],
            "matching_text_sources": supporting_urls,
            "verification_status": (
                "matching_text_only" if supporting_urls else "single_source"
            ),
            "independently_verified": False
        })

    answer = "\n\n".join(
        c["text"] + " [" +
        str(urls.index(c["url"]) + 1) + "]"
        for c in chosen
    )

    answer += (
        "\n\nKaynaklar "
        "(bağımsız doğrulama yapılmadı):\n"
    )

    answer += "\n".join(
        f"{i}. {url}"
        for i, url in enumerate(urls, 1)
    )

    sonuc = {
        "ok": True,
        "answer": answer,
        "research_engine": "v6",
        "research_status": "unverified_source_extract",
        "research_sources": [
            {
                "id": i,
                "url": url,
                "independently_verified": False
            }
            for i, url in enumerate(urls, 1)
        ],
        "research_evidence": evidence
    }

    sonuc["research_verification"] = {
        "claim_count": len(evidence),
        "matching_text_count": sum(bool(e["matching_text_sources"]) for e in evidence),
        "independently_verified_count": 0,
        "status": "not_independently_verified"
    }
    sonuc["research_conflicts"] = celiskiler

    if celiskiler:
        sonuc["research_status"] = "unresolved_conflicts"
        sonuc["answer"] += (
            "\n\nNot: Kaynaklarda birbiriyle uyusmayan "
            "sayisal bilgiler bulundu. Bu bilgiler "
            "kesin bilgi olarak sunulmadi."
        )

    return sonuc


def research_answer(question, rows, searcher):
    initial = list(rows or [])
    first = build_answer(question, initial)

    if first.get("research_status") in {
        "entity_type_uncertain",
        "unresolved_conflicts"
    }:
        return first, initial

    hosts = {
        source_info(e.get("source", ""))[0]
        for e in first.get("research_evidence", [])
    } - {""}

    if (
        first.get("ok")
        and len(hosts) >= 2
        and len(first.get("research_evidence", [])) >= 4
    ):
        return first, initial

    name = topic(question)

    if not name:
        return first, initial

    try:
        extra = list(searcher(name + " hakkında bilgi bilimsel kurumsal kaynak") or [])
    except Exception:
        return first, initial

    combined = []
    seen = set()

    for row in initial + list(extra):
        if not isinstance(row, dict):
            continue

        if row.get("content_loaded") is not True:
            continue

        url = str(row.get("url") or "")

        if not url or url in seen:
            continue

        seen.add(url)
        combined.append(row)

    if not combined:
        return first, initial

    result = build_answer(question, combined)

    result["research_extra_search"] = True
    result["research_candidate_count"] = len(combined)

    return result, combined
