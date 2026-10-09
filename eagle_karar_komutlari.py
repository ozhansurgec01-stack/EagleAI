"""EagleAI karar motoru için slash komutu ayrıştırıcısı."""

import re


def slash_komutunu_coz(metin):
    """Desteklenen slash komutunu ve devamındaki mesajı ayrıştırır."""
    slash_komutlari = {
        "brief": "brief",
        "expert": "expert",
        "eli5": "eli5",
        "stepbystep": "stepbystep",
        "summarize": "summarize",
    }

    eslesme = re.match(
        r"^/(brief|expert|eli5|stepbystep|summarize)(?:\s+(.*))?$",
        metin,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not eslesme:
        return None

    komut = eslesme.group(1).lower()
    komut_metni = (eslesme.group(2) or "").strip()

    return {
        "komut": slash_komutlari[komut],
        "komut_metni": komut_metni,
    }
