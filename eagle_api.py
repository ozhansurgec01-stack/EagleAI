from flask import Flask, request, jsonify
import os
import time
import base64
import requests
from urllib.parse import quote, urlparse, parse_qs, unquote
from bs4 import BeautifulSoup
import re
import json
import ast
import operator
from pathlib import Path
from datetime import datetime, timedelta

app = Flask(__name__)


# --- EAGLE BORÇ/TAKSİT ENTEGRASYONU ---
from flask import request, jsonify
import borc_modulu

@app.route('/api/borclar', methods=['GET'])
def api_borclari_getir():
    try:
        veri = borc_modulu.borclari_yukle()
        rapor = borc_modulu.genel_rapor()
        return jsonify({'success': True, 'borclar': veri, 'rapor': rapor})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/borc-ekle', methods=['POST'])
def api_borc_ekle():
    try:
        data = request.get_json() or {}
        mesaj = data.get('mesaj') or data.get('metin')
        if mesaj:
            sonuc = borc_modulu.borc_mesaji_isle(mesaj)
            return jsonify({'success': True, 'mesaj': sonuc})
        
        # Manuel ekleme alanları
        kisi = data.get('kisi')
        tutar = data.get('tutar')
        kategori = data.get('kategori', 'Genel')
        taksit = data.get('taksit', 1)
        if kisi and tutar:
            borc_modulu.borc_ekle(
                kisi,
                kategori,
                float(tutar),
                int(taksit)
            )
            return jsonify({'success': True, 'message': 'Borç başarıyla eklendi.'})
            
        return jsonify({'success': False, 'error': 'Geçersiz parametreler.'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/borc-guncelle', methods=['POST'])
def api_borc_guncelle():
    try:
        data = request.get_json() or {}

        borc_id = data.get('id')
        if borc_id is None:
            return jsonify({
                'success': False,
                'error': 'Borç ID gerekli.'
            }), 400

        ad = data.get('kisi')
        kategori = data.get('kategori')
        tutar = data.get('tutar')
        taksit = data.get('taksit')
        odenen = data.get('odenen')

        basari, guncel = borc_modulu.borc_guncelle(
            borc_id,
            ad=ad,
            kategori=kategori,
            toplam_borc=float(tutar) if tutar is not None else None,
            taksit_sayisi=int(taksit) if taksit is not None else None,
            odenen_tutar=float(odenen) if odenen is not None else None
        )

        if not basari:
            return jsonify({
                'success': False,
                'error': 'Borç bulunamadı veya geçersiz tutar.'
            }), 404

        return jsonify({
            'success': True,
            'message': 'Borç başarıyla güncellendi.',
            'borc': guncel
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/borc-sil', methods=['POST'])
def api_borc_sil():
    try:
        data = request.get_json() or {}

        borc_id = data.get('id')
        if borc_id is None:
            return jsonify({
                'success': False,
                'error': 'Borç ID gerekli.'
            }), 400

        basari, silinen = borc_modulu.borc_sil(borc_id)

        if not basari:
            return jsonify({
                'success': False,
                'error': 'Borç bulunamadı.'
            }), 404

        return jsonify({
            'success': True,
            'message': 'Borç başarıyla silindi.',
            'borc': silinen
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/odeme-yap', methods=['POST'])
def api_odeme_yap():
    try:
        data = request.get_json() or {}
        kisi = data.get('kisi')
        tutar = data.get('tutar')
        if kisi and tutar:
            sonuc = borc_modulu.odeme_yap(kisi, float(tutar))
            return jsonify({'success': True, 'message': sonuc})
        return jsonify({'success': False, 'error': 'Kisi ve tutar gerekli.'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-3.5-flash"

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent?key={GEMINI_API_KEY}"
)

MEMORY_FILE = Path("eagle_ai_memory.json")

# ===== GÜVENLİ HESAPLAMA MOTORU =====
_GUVENLI_ISLEMLER = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

def guvenli_hesapla(ifade):
    try:
        agac = ast.parse(str(ifade), mode="eval")

        def hesapla(node):
            if isinstance(node, ast.Expression):
                return hesapla(node.body)

            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value

            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                deger = hesapla(node.operand)
                return deger if isinstance(node.op, ast.UAdd) else -deger

            if isinstance(node, ast.BinOp) and type(node.op) in _GUVENLI_ISLEMLER:
                sol = hesapla(node.left)
                sag = hesapla(node.right)

                if type(node.op) is ast.Pow and abs(sag) > 10:
                    raise ValueError("Üs çok büyük")

                return _GUVENLI_ISLEMLER[type(node.op)](sol, sag)

            raise ValueError("İzin verilmeyen ifade")

        return True, hesapla(agac)

    except Exception as e:
        return False, str(e)



def guvenli_mantiksal_hesapla(metin):
    """Basit değişken atamalarını ve karşılaştırmaları güvenli AST ile doğrular."""
    try:
        # Örn: A=20, B=A*3, C=B-15, D=C/5, E=D+7
        # ile 6) E=24 ... kısmını ayır.
        parcalar = re.split(r'\s+(?=\d+\))', str(metin).strip(), maxsplit=1)
        atama_metni = parcalar[0]
        iddialar_metni = parcalar[1] if len(parcalar) > 1 else ""

        ortam = {}

        # Değişken atamalarını yalnızca basit sayı/aritmetik ifadeler olarak kabul et.
        atamalar = re.findall(
            r'(?:^|,\s*)([A-Za-z_]\w*)\s*=\s*([^,]+)',
            atama_metni
        )

        if not atamalar:
            return False, ""

        for ad, ifade in atamalar:
            ifade = ifade.strip()
            try:
                agac = ast.parse(ifade, mode="eval")

                def hesapla(node):
                    if isinstance(node, ast.Expression):
                        return hesapla(node.body)

                    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                        return node.value

                    if isinstance(node, ast.Name) and node.id in ortam:
                        return ortam[node.id]

                    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                        deger = hesapla(node.operand)
                        return deger if isinstance(node.op, ast.UAdd) else -deger

                    if isinstance(node, ast.BinOp) and type(node.op) in _GUVENLI_ISLEMLER:
                        sol = hesapla(node.left)
                        sag = hesapla(node.right)

                        if type(node.op) is ast.Pow and abs(sag) > 10:
                            raise ValueError("Üs çok büyük")

                        return _GUVENLI_ISLEMLER[type(node.op)](sol, sag)

                    raise ValueError("İzin verilmeyen ifade")

                ortam[ad] = hesapla(agac)

            except Exception:
                return False, ""

        if not iddialar_metni:
            return False, ""

        # 6) E=24 7) E>20 gibi maddeleri ayır.
        iddialar = re.findall(
            r'(\d+)\)\s*(.+?)(?=\s+\d+\)|$)',
            iddialar_metni
        )

        if not iddialar:
            return False, ""

        dogru = 0
        yanlis = 0
        detay = []

        for numara, ifade in iddialar:
            ifade = ifade.strip().rstrip(".")
            ifade = re.sub(r'(?<![<>=!])=(?!=)', '==', ifade)
            agac = ast.parse(ifade, mode="eval").body

            if not isinstance(agac, ast.Compare):
                continue

            def deger(node):
                if isinstance(node, ast.Name) and node.id in ortam:
                    return ortam[node.id]
                if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                    return node.value
                if isinstance(node, ast.BinOp) and type(node.op) in _GUVENLI_ISLEMLER:
                    sol = deger(node.left)
                    sag = deger(node.right)
                    if type(node.op) is ast.Pow and abs(sag) > 10:
                        raise ValueError("Üs çok büyük")
                    return _GUVENLI_ISLEMLER[type(node.op)](sol, sag)
                raise ValueError("İzin verilmeyen ifade")

            sol = deger(agac.left)
            sonuc = True

            for op, comp in zip(agac.ops, agac.comparators):
                sag = deger(comp)

                if isinstance(op, ast.Eq):
                    parca = sol == sag
                elif isinstance(op, ast.NotEq):
                    parca = sol != sag
                elif isinstance(op, ast.Gt):
                    parca = sol > sag
                elif isinstance(op, ast.GtE):
                    parca = sol >= sag
                elif isinstance(op, ast.Lt):
                    parca = sol < sag
                elif isinstance(op, ast.LtE):
                    parca = sol <= sag
                else:
                    raise ValueError("İzin verilmeyen karşılaştırma")

                sonuc = sonuc and parca
                sol = sag

            if sonuc:
                dogru += 1
                durum = "DOĞRU"
            else:
                yanlis += 1
                durum = "YANLIŞ"

            detay.append(f"{numara}) {ifade} → {durum}")

        if dogru + yanlis == 0:
            return False, ""

        sonuc_metni = (
            "\n\n===== GERÇEK MANTIKSAL DOĞRULAMA =====\n"
            + "\n".join(f"{ad} = {deger}" for ad, deger in ortam.items())
            + "\n\n"
            + "\n".join(detay)
            + f"\n\nDoğru: {dogru}\n"
            + f"Yanlış: {yanlis}\n"
            + "Bu sonuç EagleAI güvenli doğrulama motoruyla hesaplandı. "
            "Cevap verirken bu sonucu esas al.\n"
            + "===== MANTIKSAL DOĞRULAMA SONU ====="
        )

        return True, sonuc_metni

    except Exception:
        return False, ""


SYSTEM_PROMPT = """Sen Eagle-AI'sin. Kullanıcıyla Türkçe, doğal, içten ve samimi konuşan gelişmiş bir yapay zeka asistanısın.

Konuşma tarzın:
- Bir robot gibi mekanik konuşma.
- Gereksiz resmiyet kullanma.
- Kullanıcının konuşma tarzına uyum sağla.
- Kısa soruya kısa ve doğal, detay isteyen soruya detaylı cevap ver.
- Gerektiğinde espri yapabilirsin ama konunun ciddiyetini bozma.
- Kullanıcı bir şey anlattığında onu anlayarak cevap ver.
- Aynı şeyi gereksiz yere tekrar etme.
- "Ben bir yapay zekayım" gibi gereksiz açıklamalar yapma.
- Kullanıcı selamlaşırsa doğal şekilde karşılık ver.
- Kullanıcı sohbet etmek isterse sohbet et.
- Kullanıcı teknik yardım isterse doğrudan çözüm üret.
- Matematiksel hesaplama, mantıksal karşılaştırma veya kod sonucunu doğrulama gerektiğinde sonucu tahmin etme; verilen doğrulama sonucunu esas al.
- Bir hesaplama sonucunu "Python ile çalıştırdım" veya "kod çıktısı" olarak sunma; gerçek doğrulama sonucu yoksa bunu çalıştırılmış gibi gösterme.
- Kullanıcı kod isterse mümkün olduğunca çalışabilir, kopyala-yapıştır hazır kod ver. Kodu MUTLAKA uygun dil etiketiyle bir kod bloğu içinde ver (örn. ```python). Açıklamayı kod bloğunun dışında, kısa ve net tut. Mümkünse kodun altına küçük bir kullanım örneği ekle.
- Hata çıktısı verilirse önce hatanın nedenini bul, sonra çözümü ver.
- Termux, Android, Java, Python, Flask, HTML, CSS, JavaScript ve Gradle konularında yardımcı ol.
- Kullanıcı Türkçe konuşuyorsa Türkçe cevap ver.
- Bilmediğin bir şeyi kesinmiş gibi uydurma.

GÜNCEL BİLGİLER:
  - Güncel spor/maç sorularında web araştırması sonuçlarını dikkatlice incele.
  - Kullanıcı "bugün maç var mı?", "voleybol maçımız var mı?" gibi kısa bir soru sorarsa önce doğrudan VAR/YOK cevabı ver.
  - Maç varsa takım adlarını ve başlangıç saatini belirt.
  - Yayın bilgisi güvenilir sonuçlarda varsa yayın kanalını da belirt.
  - Genel maç sitesi linkleri sıralamak yerine bulunan gerçek maç bilgisini özetle.
  - Maç saati kesin olarak bulunmuyorsa saat UYDURMA.
  - "Bugün" sorularında başka günlerin maçlarını bugünkü maç gibi gösterme.
  - Kullanıcı yalnızca "var mı?" diye soruyorsa gereksiz uzun açıklama yapma.
- Sana CANLI HAVA DURUMU verisi verilirse bunu doğrudan kullan.
- Hava durumu sorularında canlı veriyi esas al.
- Güncel veri mevcutsa "internete erişimim yok" veya "güncel bilgiye erişemiyorum" deme.
- Kullanıcı güncel bir bilgi sorarsa ve elinde güvenilir veri yoksa bunu açıkça belirt; tahmin edip gerçekmiş gibi anlatma.

HAFIZA:
- EAGLE HAFIZA bölümündeki bilgileri konuşma bağlamı olarak kullan.
- Hafızadaki bilgileri gerektiğinde doğal biçimde hatırla.
- Hafızada olmayan kişisel bilgileri uydurma.

AMAÇ:
Kullanıcının ne istediğini mümkün olduğunca doğru anlayıp doğrudan yardımcı ol.
Gereksiz engeller çıkarma.
Cevabı mümkün olduğunca faydalı, anlaşılır ve doğal hale getir.
"""

def hafiza_yukle():
    try:
        if MEMORY_FILE.exists():
            veri = json.loads(
                MEMORY_FILE.read_text(encoding="utf-8")
            )

            if isinstance(veri, list):
                return veri

    except Exception as e:
        print("⚠️ Hafıza okunamadı:", e)

    return []


def hafiza_kaydet(hafiza):
    try:
        MEMORY_FILE.write_text(
            json.dumps(
                hafiza,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )
    except Exception as e:
        print("⚠️ Hafıza kaydedilemedi:", e)


def hafiza_ekle(bilgi):
    bilgi = str(bilgi).strip()

    if not bilgi:
        return False

    hafiza = hafiza_yukle()

    if bilgi in hafiza:
        return False

    hafiza.append(bilgi)

    # En fazla 100 kalıcı bilgi
    if len(hafiza) > 100:
        hafiza = hafiza[-100:]

    hafiza_kaydet(hafiza)
    return True



def hava_kodu_metin(kod):
    kod = int(kod)

    if kod == 0:
        return "Açık"
    if kod in (1, 2, 3):
        return "Az bulutlu / Bulutlu"
    if kod in (45, 48):
        return "Sisli"
    if kod in (51, 53, 55, 56, 57):
        return "Çisenti"
    if kod in (61, 63, 65, 66, 67):
        return "Yağmurlu"
    if kod in (71, 73, 75, 77):
        return "Karlı"
    if kod in (80, 81, 82):
        return "Sağanak yağışlı"
    if kod in (85, 86):
        return "Kar sağanağı"
    if kod in (95, 96, 99):
        return "Gök gürültülü fırtına"

    return "Değişken"


def hava_sorusu_mu(mesaj):
    metin = mesaj.lower()

    anahtarlar = [
        "hava durumu",
        "hava nasıl",
        "hava nasil",
        "sıcaklık",
        "sicaklik",
        "yağmur",
        "yagmur",
        "kar yağacak",
        "kar yagacak",
        "yağış",
        "yagis",
        "meteoroloji",
        "rüzgar",
        "ruzgar",
        "nem oranı",
        "nem orani",
        "kaç derece",
        "kac derece"
    ]

    return any(x in metin for x in anahtarlar)


def hava_sehir_bul(mesaj):
    metin = mesaj.strip()

    # Türkiye şehirleri
    sehirler = [
        "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya",
        "Ankara", "Antalya", "Artvin", "Aydın", "Balıkesir",
        "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur",
        "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli",
        "Diyarbakır", "Edirne", "Elazığ", "Erzincan", "Erzurum",
        "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane",
        "Hakkari", "Hatay", "Isparta", "İstanbul", "İzmir",
        "Kahramanmaraş", "Karabük", "Karaman", "Kars", "Kastamonu",
        "Kayseri", "Kilis", "Kırıkkale", "Kırklareli", "Kırşehir",
        "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa",
        "Mardin", "Mersin", "Muğla", "Muş", "Nevşehir",
        "Niğde", "Ordu", "Osmaniye", "Rize", "Sakarya",
        "Samsun", "Siirt", "Sinop", "Sivas", "Şanlıurfa",
        "Şırnak", "Tekirdağ", "Tokat", "Trabzon", "Tunceli",
        "Uşak", "Van", "Yalova", "Yozgat", "Zonguldak"
    ]

    # Önce doğrudan şehir adını ara.
    kucuk = metin.lower()

    for sehir in sehirler:
        if re.search(r"\\b" + re.escape(sehir.lower()) + r"\\b", kucuk):
            return sehir

    # "Adana'da", "Adana için", "Adana'nın" gibi kullanımlar.
    for sehir in sehirler:
        desen = (
            r"\\b" + re.escape(sehir.lower()) +
            r"(?:'|’)?(?:da|de|ta|te|daki|deki|taki|teki|"
            r"nın|nin|nun|nün|için|icin)\\b"
        )
        if re.search(desen, kucuk):
            return sehir

    # Şehir belirtilmemişse varsayılan konum: Adana.
    return "Adana"


def hava_durumu_getir(mesaj):
    if not hava_sorusu_mu(mesaj):
        return None

    sehir = hava_sehir_bul(mesaj)

    if not sehir:
        return {
            "ok": False,
            "error": "Hava durumu için şehir adını belirtir misin?"
        }

    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": sehir,
                "count": 1,
                "language": "tr",
                "format": "json"
            },
            timeout=10
        )

        geo_data = geo.json()
        sonuclar = geo_data.get("results", [])

        if not sonuclar:
            return {
                "ok": False,
                "error": f"{sehir} için konum bulunamadı."
            }

        konum = sonuclar[0]

        latitude = konum["latitude"]
        longitude = konum["longitude"]
        bulunan_sehir = konum.get("name", sehir)
        ulke = konum.get("country", "")

        hava = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": ",".join([
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "precipitation",
                    "weather_code",
                    "wind_speed_10m"
                ]),
                "daily": ",".join([
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_probability_max",
                    "wind_speed_10m_max"
                ]),
                "forecast_days": 5,
                "timezone": "auto"
            },
            timeout=10
        )

        hava_data = hava.json()

        current = hava_data.get("current", {})
        daily = hava_data.get("daily", {})

        gunler = []

        tarihler = daily.get("time", [])
        kodlar = daily.get("weather_code", [])
        maxlar = daily.get("temperature_2m_max", [])
        minler = daily.get("temperature_2m_min", [])
        yagislar = daily.get("precipitation_probability_max", [])
        ruzgarlar = daily.get("wind_speed_10m_max", [])

        for i in range(min(5, len(tarihler))):
            gunler.append({
                "date": tarihler[i],
                "description": hava_kodu_metin(kodlar[i]),
                "min": minler[i],
                "max": maxlar[i],
                "rain_probability": yagislar[i],
                "wind_max": ruzgarlar[i]
            })

        return {
            "ok": True,
            "city": bulunan_sehir,
            "country": ulke,
            "current": {
                "temperature": current.get("temperature_2m"),
                "feels_like": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "precipitation": current.get("precipitation"),
                "wind": current.get("wind_speed_10m"),
                "description": hava_kodu_metin(
                    current.get("weather_code", 0)
                )
            },
            "forecast": gunler
        }

    except Exception as e:
        print("⚠️ Hava durumu hatası:", e)

        return {
            "ok": False,
            "error": "Canlı hava durumu verisine ulaşılamadı."
        }


# ============================================================
# 🌐 ÜCRETSİZ WEB ARAŞTIRMA
# DuckDuckGo HTML — ücretli API kullanılmaz
# ============================================================

def spor_sorgusu_mu(mesaj):
    """Güncel spor ve maç programı sorularını algılar."""
    kelimeler = [
        "maç", "mac", "maçlar", "maclar",
        "voleybol", "futbol", "basketbol",
        "tenis", "hentbol", "spor",
        "karşılaşma", "karsilasma",
        "milli takım", "milli takim",
        "şampiyonlar ligi", "süper lig", "super lig",
        "premier lig", "la liga", "serie a", "bundesliga",
        "maçımız", "macimiz",
        "oynanıyor", "oynanacak",
        "hangi maç", "hangi mac"
    ]

    mesaj_kucuk = mesaj.lower().replace("\u0307", "")
    return any(kelime in mesaj_kucuk for kelime in kelimeler)


def spor_arama_sorgusu(mesaj):
    """Spor sorusunu ülke ve lig bağlamına göre güncel aramaya dönüştürür."""
    mesaj_kucuk = mesaj.casefold().replace('\u0307', '')

    # 🇹🇷 Türkiye
    turkiye_kelimeleri = [
        "türkiye", "turkiye",
        "bizim takım", "bizim takim",
        "milli takım", "milli takim",
        "milli maç", "milli mac",
        "filenin sultanları", "filenin sultanlari",
        "filenin efeleri",
        "süper lig", "super lig"
    ]

    # 🇬🇧 İngiltere
    ingiltere_kelimeleri = [
        "ingiltere", "ingiltere'de", "ingilterede",
        "premier lig", "premier league"
    ]

    # 🇪🇸 İspanya
    ispanya_kelimeleri = [
        "ispanya", "ispanya'da", "ispanyada",
        "la liga"
    ]

    # 🇩🇪 Almanya
    almanya_kelimeleri = [
        "almanya", "almanya'da", "almanyada",
        "bundesliga"
    ]

    # 🇮🇹 İtalya
    italya_kelimeleri = [
        "italya", "italya'da", "italyada",
        "serie a"
    ]

    # 🇫🇷 Fransa
    fransa_kelimeleri = [
        "fransa", "fransa'da", "fransada",
        "ligue 1"
    ]

    # 🏐 Voleybol
    voleybol_mu = any(k in mesaj_kucuk for k in [
        "voleybol",
        "filenin sultanları", "filenin sultanlari",
        "filenin efeleri"
    ])

    # 🕐 Geçmiş maç / sonuç soruları
    gecmis_mac = any(k in mesaj_kucuk for k in [
        "dün", "dünkü", "dünün",
        "dun", "dunku", "dunun",
        "geçen maç", "gecen mac",
        "sonuç", "sonuc", "sonuçları", "sonuclari",
        "skor", "skorları", "skorlari"
    ])

    if voleybol_mu and gecmis_mac:
        dun = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
        return f"Türkiye voleybol {dun} maç sonuçları"

    # ⚽ Futbol
    futbol_mu = any(k in mesaj_kucuk for k in [
        "futbol", "süper lig", "super lig",
        "premier lig", "premier league",
        "la liga", "bundesliga", "serie a", "ligue 1"
    ])

    # 🏀 Basketbol
    basketbol_mu = "basketbol" in mesaj_kucuk

    # 🎾 Tenis
    tenis_mu = "tenis" in mesaj_kucuk

    # 🇹🇷 Türkiye
    if any(k in mesaj_kucuk for k in turkiye_kelimeleri):
        if voleybol_mu:
            if gecmis_mac:
                dun = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
                return f"Türkiye voleybol {dun} maç sonuçları"
            return "Türkiye bugün voleybol maç programı resmi TVF fikstür"
        if futbol_mu:
            return "Türkiye bugün futbol maç programı Süper Lig resmi fikstür"
        if basketbol_mu:
            return "Türkiye bugün basketbol maç programı resmi fikstür"
        if tenis_mu:
            return "Türkiye tenisçiler bugün maç programı"
        return "Türkiye bugün spor müsabakaları maç programı"

    # 🇬🇧 İngiltere
    if any(k in mesaj_kucuk for k in ingiltere_kelimeleri):
        if futbol_mu:
            return "İngiltere bugün futbol maç programı Premier League resmi fikstür"
        return "İngiltere bugün spor maç programı Premier League futbol"

    # 🇪🇸 İspanya
    if any(k in mesaj_kucuk for k in ispanya_kelimeleri):
        if futbol_mu:
            return "İspanya bugün futbol maç programı La Liga resmi fikstür"
        return "İspanya bugün spor maç programı La Liga futbol"

    # 🇩🇪 Almanya
    if any(k in mesaj_kucuk for k in almanya_kelimeleri):
        if futbol_mu:
            return "Almanya bugün futbol maç programı Bundesliga resmi fikstür"
        return "Almanya bugün spor maç programı Bundesliga futbol"

    # 🇮🇹 İtalya
    if any(k in mesaj_kucuk for k in italya_kelimeleri):
        if futbol_mu:
            return "İtalya bugün futbol maç programı Serie A resmi fikstür"
        return "İtalya bugün spor maç programı Serie A futbol"

    # 🇫🇷 Fransa
    if any(k in mesaj_kucuk for k in fransa_kelimeleri):
        if futbol_mu:
            return "Fransa bugün futbol maç programı Ligue 1 resmi fikstür"
        return "Fransa bugün spor maç programı Ligue 1 futbol"

    # 🌍 Genel spor
    return "bugün maç programı"


def eagle_karar_motoru(mesaj):
    """
    EagleAI karar motoru v1.
    Sadece karar verir; herhangi bir işlem yapmaz ve dosya değiştirmez.
    """
    metin = str(mesaj or "").strip()
    k = metin.lower()

    karar = {
        "intent": "sohbet",
        "guven": "orta",
        "neden": "Özel bir araç gerektiren açık bir istek algılanmadı.",
        "arac": "gemini",
        "islem": "cevapla",
        "dogrulama": False
    }

    if not metin:
        karar.update({
            "intent": "bos",
            "guven": "yüksek",
            "neden": "Mesaj boş.",
            "arac": "yok"
        })
        return karar

    # 🧠 HAFIZA
    hafiza_kelimeleri = [
        "hatırla", "hatirla", "unutma",
        "hafızam", "hafizam", "hafıza", "hafiza",
        "daha önce sana", "daha once sana",
        "ne söylemiştim", "ne soylemistim",
        "hatırlıyor musun", "hatirliyor musun"
    ]

    if any(x in k for x in hafiza_kelimeleri):
        karar.update({
            "intent": "hafiza",
            "guven": "yüksek",
            "neden": "Hafıza ile ilgili bir istek algılandı.",
            "arac": "hafiza"
        })
        return karar

    # 💳 BORÇ
    borc_kelimeleri = [
        "borç", "borc", "borcum",
        "taksit", "ödeme", "odeme",
        "kredi kartı", "kredi karti",
        "kredi borcu", "borç raporu", "borc raporu"
    ]

    if any(x in k for x in borc_kelimeleri):
        karar.update({
            "intent": "borc",
            "guven": "yüksek",
            "neden": "Borç veya taksit işlemi algılandı.",
            "arac": "borc_modulu",
            "islem": "veri_getir",
            "dogrulama": True
        })
        return karar

    # 💻 KOD / HATA
    kod_kelimeleri = [
        "kod", "python", "java", "javascript",
        "flask", "android", "gradle", "termux",
        "html", "css", "api", "fonksiyon",
        "syntax", "sözdizimi", "sozdizimi",
        "hata", "exception", "traceback",
        "çalışmıyor", "calismiyor", "derlenmiyor",
        "compile", "build failed"
    ]

    if any(x in k for x in kod_kelimeleri):
        karar.update({
            "intent": "kod_hata",
            "guven": "yüksek",
            "neden": "Kod geliştirme veya hata analizi isteği algılandı.",
            "arac": "kod_analiz"
        })
        return karar

    # 🌦️ HAVA
    hava_kelimeleri = [
        "hava", "hava durumu", "sıcaklık", "sicaklik",
        "kaç derece", "kac derece", "yağmur", "yagmur",
        "rüzgar", "ruzgar", "nem", "fırtına", "firtina"
    ]

    if any(x in k for x in hava_kelimeleri):
        karar.update({
            "intent": "hava",
            "guven": "yüksek",
            "neden": "Hava durumu isteği algılandı.",
            "arac": "hava_api",
            "islem": "veri_getir",
            "dogrulama": True
        })
        return karar

    # 🏟️ SPOR
    spor_kelimeleri = [
        "maç", "mac", "maçlar", "maclar",
        "skor", "fikstür", "fikstur",
        "puan durumu", "voleybol", "futbol",
        "basketbol", "tenis", "vnl",
        "süper lig", "super lig",
        "premier lig", "premier league",
        "şampiyonlar ligi", "sampiyonlar ligi",
        "filenin sultanları", "filenin efeleri"
    ]

    if any(x in k for x in spor_kelimeleri):
        karar.update({
            "intent": "spor",
            "guven": "yüksek",
            "neden": "Spor veya maç isteği algılandı.",
            "arac": "spor_kaynaklari",
            "islem": "veri_getir",
            "dogrulama": True
        })
        return karar

    # 🧮 MATEMATİK
    if re.fullmatch(r"[0-9+*/().,%\-\s]+", metin):
        karar.update({
            "intent": "matematik",
            "guven": "yüksek",
            "neden": "Mesaj doğrudan matematiksel bir ifade.",
            "arac": "guvenli_hesaplama",
            "islem": "hesapla",
            "dogrulama": True
        })
        return karar

    # 🌐 GÜNCEL BİLGİ
    guncel_kelimeleri = [
        "bugün", "bugun", "şimdi", "simdi",
        "şu an", "su an", "güncel", "guncel",
        "son dakika", "haber", "araştır", "arastir",
        "internetten", "webde", "web'de",
        "en son", "son durum", "ne oldu"
    ]

    if any(x in k for x in guncel_kelimeleri):
        karar.update({
            "intent": "guncel_bilgi",
            "guven": "yüksek",
            "neden": "Güncel bilgi gerektiren bir istek algılandı.",
            "arac": "web_arastirma"
        })
        return karar

    return karar


def web_arastirma_gerekli(mesaj):
    """Mesaj güncel internet bilgisi gerektiriyor mu?"""
    kelimeler = [
        "bugün", "bugunku", "bugünkü",
        "şimdi", "şu an",
        "son dakika",
        "güncel", "guncel",
        "haber", "haberler",
        "maç", "mac", "maçlar",
        "skor", "puan durumu",
        "bitcoin", "btc", "ethereum",
        "altın", "gram altın",
        "dolar", "euro",
        "en son", "son durum",
        "ne oldu",
        "araştır", "arastir",
        "araştırır mısın",
        "bul", "bulur musun"
    ]

    mesaj_kucuk = mesaj.lower()
    return any(k in mesaj_kucuk for k in kelimeler)


def web_kaynak_url(url):
    """DuckDuckGo yönlendirme URL'sinden gerçek kaynak adresini çıkarır."""
    try:
        if not url:
            return ""

        parsed = urlparse(url)

        # //duckduckgo.com/l/?uddg=https%3A...
        if "duckduckgo.com" in parsed.netloc.lower():
            qs = parse_qs(parsed.query)
            hedef = qs.get("uddg", [""])[0]

            if hedef:
                return unquote(hedef)

        return url

    except Exception:
        return url




def premier_lig_getir(mesaj=""):
    """Premier League resmi API'sinden güncel ve gelecek maçları getirir."""

    try:
        from datetime import datetime, timedelta

        mesaj_kucuk = (mesaj or "").lower().replace("\u0307", "")

        base_url = (
            "https://sdp-prem-prod.premier-league-prod.pulselive.com"
            "/api/v1/competitions/8/seasons/2026"
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 15) "
                "AppleWebKit/537.36 "
                "Chrome/140.0.0.0 Mobile Safari/537.36"
            ),
            "Accept": "application/json",
            "Origin": "https://www.premierleague.com",
            "Referer": "https://www.premierleague.com/"
        }

        simdi = datetime.now()
        bugun = simdi.date()

        maclar = []

        # Mevcut ve yakın gelecek haftaları kontrol et.
        for hafta in range(2, 7):
            url = f"{base_url}/matchweeks/{hafta}/matches"

            cevap = requests.get(
                url,
                headers=headers,
                timeout=10
            )

            print(
                f"🏴 Premier League hafta {hafta}: HTTP {cevap.status_code}",
                flush=True
            )

            if cevap.status_code != 200:
                continue

            veri = cevap.json()

            if isinstance(veri, dict):
                liste = veri.get("data", [])
            elif isinstance(veri, list):
                liste = veri
            else:
                liste = []

            if isinstance(liste, list):
                maclar.extend(liste)

        if not maclar:
            print("⚠️ Premier League API maç verisi bulunamadı.", flush=True)
            return []

        # Aynı maçı iki kez eklemeyi önle.
        benzersiz = {}
        for mac in maclar:
            mac_id = mac.get("matchId") or mac.get("id")
            if mac_id:
                benzersiz[str(mac_id)] = mac

        maclar = list(benzersiz.values())

        takim_anahtarlari = [
            "liverpool",
            "arsenal",
            "chelsea",
            "manchester united",
            "manchester city",
            "tottenham",
            "newcastle",
            "everton",
            "aston villa",
            "brighton",
            "bournemouth",
            "brentford",
            "crystal palace",
            "fulham",
            "sunderland",
            "leeds",
            "nottingham forest",
            "hull",
            "coventry",
            "ipswich"
        ]

        istenen_takim = None

        for takim in takim_anahtarlari:
            if takim in mesaj_kucuk:
                istenen_takim = takim
                break

        sonuc = []

        for mac in maclar:
            kickoff = mac.get("kickoff")
            if not kickoff:
                continue

            try:
                dt = datetime.fromisoformat(
                    kickoff.replace("Z", "+00:00")
                )

                # API saati UTC+1/İngiltere saati olarak geliyor.
                # Türkiye UTC+3 olduğu için mevcut tarih için +2 saat.
                turkiye_saati = dt.replace(tzinfo=None) + timedelta(hours=2)

            except Exception:
                continue

            ev = mac.get("homeTeam", {})
            deplasman = mac.get("awayTeam", {})

            ev_adi = ev.get("name", "Ev Sahibi")
            deplasman_adi = deplasman.get("name", "Deplasman")

            mac_metni = (
                f"{ev_adi} {deplasman_adi}"
            ).lower()

            if istenen_takim and istenen_takim not in mac_metni:
                continue

            sonuc.append({
                "title": f"Premier League: {ev_adi} - {deplasman_adi}",
                "url": "https://www.premierleague.com/en/fixtures",
                "snippet": (
                    f"{turkiye_saati.strftime('%d.%m.%Y')} "
                    f"{turkiye_saati.strftime('%H:%M')} Türkiye saati | "
                    f"{ev_adi} - {deplasman_adi} | "
                    f"Durum: {mac.get('status', 'PreMatch')} | "
                    f"{'BUGÜN' if turkiye_saati.date() == bugun else 'GELECEK MAÇ'}"
                ),
                "_tarih": turkiye_saati
            })

        sonuc.sort(key=lambda x: x["_tarih"])

        # Bugünün maçları varsa yalnızca onları göster.
        bugunun_maclari = [
            x for x in sonuc
            if x["_tarih"].date() == bugun
        ]

        if bugunun_maclari:
            secilecek = bugunun_maclari[:8]
        else:
            # Bugün maç yoksa bugünden sonraki ilk maçları göster.
            gelecek = [
                x for x in sonuc
                if x["_tarih"].date() > bugun
            ]
            secilecek = gelecek[:8]

        for x in secilecek:
            x.pop("_tarih", None)

        print(
            f"✅ Premier League kullanılabilir maç: {len(secilecek)}",
            flush=True
        )

        return secilecek

    except Exception as e:
        print(
            f"⚠️ Premier League API hatası: {e}",
            flush=True
        )
        return []


def super_lig_getir(mesaj=""):
    """TFF resmi fikstüründen güncel Süper Lig maçlarını getirir."""

    try:
        from datetime import datetime

        url = "https://www.tff.org/default.aspx?pageID=198"

        cevap = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 15) "
                    "AppleWebKit/537.36 "
                    "Chrome/140 Mobile Safari/537.36"
                ),
                "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.7"
            },
            timeout=15
        )

        print(
            f"🇹🇷 TFF Süper Lig HTTP {cevap.status_code}",
            flush=True
        )

        if cevap.status_code != 200:
            return []

        soup = BeautifulSoup(cevap.text, "html.parser")
        metin = soup.get_text(" ", strip=True)

        desen = re.compile(
            r'(\d{2}\.\d{2}\.\d{4})\s+'
            r'(\d{1,2}:\d{2})\s+'
            r'(.+?)\s+-\s+'
            r'(.+?)\s+Detaylar',
            re.IGNORECASE
        )

        maclar = []

        for eslesme in desen.finditer(metin):
            tarih = eslesme.group(1).strip()
            saat = eslesme.group(2).strip()
            ev = eslesme.group(3).strip()
            deplasman = eslesme.group(4).strip()

            try:
                dt = datetime.strptime(
                    f"{tarih} {saat}",
                    "%d.%m.%Y %H:%M"
                )
            except Exception:
                continue

            maclar.append({
                "ev": ev,
                "deplasman": deplasman,
                "tarih": tarih,
                "saat": saat,
                "_tarih": dt
            })

        if not maclar:
            print(
                "⚠️ TFF Süper Lig fikstür maçları bulunamadı.",
                flush=True
            )
            return []

        benzersiz = {}

        for mac in maclar:
            anahtar = (
                mac["tarih"],
                mac["saat"],
                mac["ev"],
                mac["deplasman"]
            )
            benzersiz[anahtar] = mac

        maclar = list(benzersiz.values())
        maclar.sort(key=lambda x: x["_tarih"])

        mesaj_kucuk = (
            (mesaj or "")
            .casefold()
            .replace("\u0307", "")
        )

        takim_anahtarlari = {
            "galatasaray": ["galatasaray"],
            "fenerbahçe": ["fenerbahçe", "fenerbahce"],
            "beşiktaş": ["beşiktaş", "besiktas"],
            "trabzonspor": ["trabzonspor"],
            "başakşehir": ["başakşehir", "basaksehir"],
            "samsunspor": ["samsunspor"],
            "göztepe": ["göztepe", "goztepe"],
            "kocaelispor": ["kocaelispor"],
            "çaykur rizespor": ["çaykur rizespor", "caykur rizespor"],
            "alanyaspor": ["alanyaspor"],
            "gaziantep": ["gaziantep"],
            "kasımpaşa": ["kasımpaşa", "kasimpasa"],
            "eyüpspor": ["eyüpspor", "eyupspor"],
            "gençlerbirliği": ["gençlerbirliği", "genclerbirligi"],
            "konyaspor": ["konyaspor"],
            "erzurumspor": ["erzurumspor"],
            "amed": ["amed"],
            "çorum": ["çorum", "corum"]
        }

        istenen_anahtarlar = []

        for anahtarlar in takim_anahtarlari.values():
            if any(k in mesaj_kucuk for k in anahtarlar):
                istenen_anahtarlar.extend(anahtarlar)

        if istenen_anahtarlar:
            maclar = [
                mac for mac in maclar
                if any(
                    anahtar in (
                        f"{mac['ev']} {mac['deplasman']}"
                    ).casefold().replace("\u0307", "")
                    for anahtar in istenen_anahtarlar
                )
            ]

        bugun = datetime.now().date()

        bugunun_maclari = [
            mac for mac in maclar
            if mac["_tarih"].date() == bugun
        ]

        if bugunun_maclari:
            secilecek = bugunun_maclari[:8]
        else:
            gelecek = [
                mac for mac in maclar
                if mac["_tarih"].date() > bugun
            ]
            secilecek = gelecek[:8]

        sonuc = []

        for mac in secilecek:
            sonuc.append({
                "title": (
                    f"Süper Lig: "
                    f"{mac['ev']} - {mac['deplasman']}"
                ),
                "url": url,
                "snippet": (
                    f"{mac['tarih']} {mac['saat']} Türkiye saati | "
                    f"{mac['ev']} - {mac['deplasman']} | "
                    f"{'BUGÜN' if mac['_tarih'].date() == bugun else 'GELECEK MAÇ'} | "
                    f"TFF resmi fikstürü."
                )
            })

        print(
            f"✅ TFF Süper Lig kullanılabilir maç: {len(sonuc)}",
            flush=True
        )

        return sonuc

    except Exception as e:
        print(
            f"⚠️ TFF Süper Lig hatası: {e}",
            flush=True
        )
        return []


def tvf_voleybol_getir():
    """TVF resmi fikstüründen Türkiye'nin güncel ve yaklaşan maçlarını çeker."""
    try:
        from datetime import datetime

        url = "https://fikstur.tvf.org.tr/Takvim"

        cevap = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 15) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/140 Mobile Safari/537.36"
                ),
                "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.7"
            },
            timeout=8
        )

        print(f"🏐 TVF HTTP {cevap.status_code}", flush=True)

        if cevap.status_code != 200:
            return []

        soup = BeautifulSoup(cevap.text, "html.parser")
        metin = soup.get_text(" ", strip=True)

        bugun = datetime.now().strftime("%d.%m.%Y")

        sonuclar = []

        # Türkiye maçlarını tarih + saat + rakip ile yakala.
        desen = re.compile(
            r'([A-ZÇĞİÖŞÜ]+)\s+Vs\s+Türkiye\s*/\s*'
            r'(\d{2}\.\d{2}\.\d{4})\s*-\s*(\d{1,2}:\d{2})\s*/\s*'
            r'(.*?)(?=\s+[A-ZÇĞİÖŞÜ]+\s+Vs\s+|$)',
            re.IGNORECASE
        )

        desen2 = re.compile(
            r'Türkiye\s+Vs\s+([A-ZÇĞİÖŞÜ]+)\s*/\s*'
            r'(\d{2}\.\d{2}\.\d{4})\s*-\s*(\d{1,2}:\d{2})\s*/\s*'
            r'(.*?)(?=\s+[A-ZÇĞİÖŞÜ]+\s+Vs\s+|$)',
            re.IGNORECASE
        )

        maclar = []

        for m in desen.finditer(metin):
            maclar.append({
                "rakip": m.group(1).strip(),
                "tarih": m.group(2),
                "saat": m.group(3),
                "yer": m.group(4).strip()
            })

        for m in desen2.finditer(metin):
            maclar.append({
                "rakip": m.group(1).strip(),
                "tarih": m.group(2),
                "saat": m.group(3),
                "yer": m.group(4).strip()
            })

        # Aynı maçı iki regex yakalarsa tekrar etmesin.
        benzersiz = []
        gorulen = set()

        for mac in maclar:
            anahtar = (
                mac["rakip"],
                mac["tarih"],
                mac["saat"]
            )

            if anahtar not in gorulen:
                gorulen.add(anahtar)
                benzersiz.append(mac)

        # Önce BUGÜN oynanan Türkiye maçları.
        bugun_maclari = [
            m for m in benzersiz
            if m["tarih"] == bugun
        ]

        if bugun_maclari:
            for m in bugun_maclari:
                rakip = m["rakip"].upper()

                if rakip == "ALMANYA" and m["saat"] == "19:00":
                    kategori = "A Millî Kadın Voleybol Takımı (Filenin Sultanları)"
                elif rakip == "SIRBİSTAN" and m["saat"] == "17:00":
                    kategori = "Gençler / alt yaş kategorisi"
                else:
                    kategori = "Kategori belirtilmedi"

                sonuclar.append({
                    "title": f"{m['rakip']} - Türkiye",
                    "url": url,
                    "snippet": (
                        f"BUGÜN {m['tarih']} - {m['saat']} — "
                        f"Kategori: {kategori} — "
                        f"Yer: {m['yer']} — TVF resmi fikstürü."
                    )
                })

            print(
                f"🏐 TVF: BUGÜN {len(sonuclar)} Türkiye maçı bulundu",
                flush=True
            )
            return sonuclar[:8]

        # Bugün maç yoksa en yakın gelecek Türkiye maçlarını ver.
        gelecek = [
            m for m in benzersiz
            if m["tarih"] > bugun
        ]

        gelecek.sort(
            key=lambda x: (
                datetime.strptime(x["tarih"], "%d.%m.%Y"),
                x["saat"]
            )
        )

        for m in gelecek[:8]:
            sonuclar.append({
                "title": f"{m['rakip']} - Türkiye",
                "url": url,
                "snippet": (
                    f"{m['tarih']} - {m['saat']} — "
                    f"Yer: {m['yer']} — TVF resmi fikstürü."
                )
            })

        print(
            f"🏐 TVF: Bugün maç yok, {len(sonuclar)} yaklaşan maç bulundu",
            flush=True
        )

        return sonuclar

    except Exception as e:
        print(f"⚠️ TVF arama hatası: {e}", flush=True)
        return []



def web_arastir(sorgu, limit=6):
    """Güncel web araması. DuckDuckGo çalışmazsa Google fallback kullanır."""
    
    def sonuclari_ayikla(soup, kaynak):
        sonuclar = []

        # DuckDuckGo
        if kaynak == "duckduckgo":
            bloklar = soup.select(".result")

            for sonuc in bloklar[:limit]:
                baslik = sonuc.select_one(".result__a")
                aciklama = sonuc.select_one(".result__snippet")

                if not baslik:
                    continue

                sonuclar.append({
                    "title": baslik.get_text(" ", strip=True),
                    "url": web_kaynak_url(
                        baslik.get("href", "").strip()
                    ),
                    "snippet": (
                        aciklama.get_text(" ", strip=True)
                        if aciklama else ""
                    )
                })

        # Google
        else:
            bloklar = soup.select("div.MjjYud")

            for sonuc in bloklar:
                baslik = sonuc.select_one("h3")

                if not baslik:
                    continue

                link = baslik.find_parent("a")

                if not link:
                    continue

                aciklama = sonuc.select_one(
                    "div.VwiC3b, div.yXK7lf"
                )

                sonuclar.append({
                    "title": baslik.get_text(" ", strip=True),
                    "url": link.get("href", "").strip(),
                    "snippet": (
                        aciklama.get_text(" ", strip=True)
                        if aciklama else ""
                    )
                })

                if len(sonuclar) >= limit:
                    break

        return sonuclar

    try:
        sorgu = sorgu[:400]

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 15) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/140.0.0.0 Mobile Safari/537.36"
            ),
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml"
        }

        # ========================================================
        # 1) DUCKDUCKGO
        # ========================================================

        ddg_url = (
            "https://html.duckduckgo.com/html/?q="
            + quote(sorgu)
        )

        try:
            cevap = requests.get(
                ddg_url,
                headers=headers,
                timeout=15
            )

            print(
                f"🌐 DuckDuckGo HTTP {cevap.status_code}",
                flush=True
            )

            if cevap.status_code in (200, 202):
                soup = BeautifulSoup(
                    cevap.text,
                    "html.parser"
                )

                sonuclar = sonuclari_ayikla(
                    soup,
                    "duckduckgo"
                )

                if sonuclar:
                    print(
                        f"✅ DuckDuckGo: {len(sonuclar)} sonuç",
                        flush=True
                    )
                    return sonuclar

        except Exception as e:
            print(
                f"⚠️ DuckDuckGo hatası: {e}",
                flush=True
            )

        # ========================================================
        # 2) GOOGLE FALLBACK
        # ========================================================

        print(
            "🔄 Google web araması fallback deneniyor...",
            flush=True
        )

        google_url = (
            "https://www.google.com/search?q="
            + quote(sorgu)
            + "&hl=tr&gl=tr"
        )

        try:
            cevap = requests.get(
                google_url,
                headers=headers,
                timeout=15
            )

            print(
                f"🌐 Google HTTP {cevap.status_code}",
                flush=True
            )

            if cevap.status_code != 200:
                print(
                    f"⚠️ Google web arama HTTP {cevap.status_code}",
                    flush=True
                )
                return []

            soup = BeautifulSoup(
                cevap.text,
                "html.parser"
            )

            sonuclar = sonuclari_ayikla(
                soup,
                "google"
            )

            print(
                f"🌐 Google: {len(sonuclar)} sonuç",
                flush=True
            )

            return sonuclar

        except Exception as e:
            print(
                f"⚠️ Google web arama hatası: {e}",
                flush=True
            )
            return []

    except Exception as e:
        print(
            f"⚠️ Web araştırma genel hata: {e}",
            flush=True
        )
        return []

def web_sayfa_oku(url, limit=7000):
    """Web sayfasını indirir ve Gemini için temiz metne dönüştürür."""
    try:
        url = web_kaynak_url(url)
        if not url or not url.startswith(("http://", "https://")):
            return ""

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 15) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/140.0.0.0 Mobile Safari/537.36"
            ),
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.7"
        }

        cevap = requests.get(
            url,
            headers=headers,
            timeout=12
        )

        if cevap.status_code != 200:
            print(
                f"⚠️ Web sayfa HTTP {cevap.status_code}: {url}",
                flush=True
            )
            return ""

        soup = BeautifulSoup(
            cevap.text,
            "html.parser"
        )

        for etiket in soup(["script", "style", "noscript"]):
            etiket.decompose()

        metin = " ".join(soup.stripped_strings)
        metin = re.sub(r"\s+", " ", metin).strip()

        if len(metin) > limit:
            metin = metin[:limit]

        print(
            f"📖 Web sayfa okundu: {len(metin)} karakter",
            flush=True
        )

        return metin

    except Exception as e:
        print(
            f"⚠️ Web sayfa okuma hatası: {e}",
            flush=True
        )
        return ""


def web_sonuclari_metni(sonuclar):
    """Web arama sonuçlarını ve gerçek kaynak sayfalarını Gemini'ye aktarır."""
    if not sonuclar:
        return ""

    satirlar = [
        "",
        "===== ÜCRETSİZ WEB ARAŞTIRMASI =====",
        "Aşağıdaki bilgiler internetten alınmıştır.",
        "ÖNEMLİ: Güncel bilgi sorularında gerçek kaynak sayfasındaki verileri esas al.",
        "Veri mevcutsa 'veri yok', 'bakamıyorum' veya gereksiz açıklamalar yapma.",
        "Tarih, saat, takım ve skorları değiştirme veya uydurma.",
        "Kaynaklarda açıkça yazan bilgileri aynen dikkate al.",
          "Kaynakta açıkça belirtilen Kategori bilgisini cevabında mutlaka koru ve ilgili maçın yanında göster. Kategori belirtilmemişse kategori uydurma.",
        ""
    ]

    for i, sonuc in enumerate(sonuclar[:3], 1):
        url = sonuc.get("url", "")
        sayfa_metni = web_sayfa_oku(url, limit=3500)

        satirlar.append(
            f"[KAYNAK {i}]\n"
            f"Başlık: {sonuc.get('title', '')}\n"
            f"Adres: {url}\n"
            f"Arama özeti: {sonuc.get('snippet', '')}\n"
        )

        if sayfa_metni:
            satirlar.append(
                "GERÇEK SAYFA İÇERİĞİ:\n"
                + sayfa_metni
                + "\n"
            )
        else:
            satirlar.append(
                "GERÇEK SAYFA İÇERİĞİ: Okunamadı. "
                "Yalnızca arama özeti kullanılabilir.\n"
            )

    satirlar.append(
        "===== WEB ARAŞTIRMASI SONU ====="
    )

    return "\n".join(satirlar)


def hafiza_metni():
    hafiza = hafiza_yukle()

    if not hafiza:
        return "Henüz kayıtlı kalıcı bilgi yok."

    return "\n".join(
        f"- {bilgi}"
        for bilgi in hafiza
    )


@app.get("/")
def ana():
    return jsonify({
        "ok": True,
        "assistant": "Eagle-AI",
        "message": "🦅 Eagle-AI API çalışıyor."
    })


@app.get("/api/durum")
def durum():
    return jsonify({
        "ok": True,
        "assistant": "Eagle-AI",
        "gemini": bool(GEMINI_API_KEY),
        "memory_count": len(hafiza_yukle())
    })


@app.get("/api/hafiza")
def hafiza_goster():
    return jsonify({
        "ok": True,
        "memory": hafiza_yukle(),
        "count": len(hafiza_yukle())
    })


@app.post("/api/hafiza")
def hafiza_api_ekle():
    data = request.get_json(silent=True) or {}
    bilgi = str(data.get("memory", "")).strip()

    if not bilgi:
        return jsonify({
            "ok": False,
            "error": "Hafıza bilgisi boş."
        }), 400

    eklendi = hafiza_ekle(bilgi)

    return jsonify({
        "ok": True,
        "added": eklendi,
        "memory": hafiza_yukle()
    })


@app.post("/api/hafiza/temizle")
def hafiza_temizle():
    hafiza_kaydet([])

    return jsonify({
        "ok": True,
        "message": "🧹 Kalıcı hafıza temizlendi."
    })


@app.post("/api/sohbet")
def sohbet():

    data = request.get_json(silent=True) or {}

    mesaj = str(
        data.get("message", "")
    ).strip()

    gecmis = data.get("history", [])

    if not mesaj:
        return jsonify({
            "ok": False,
            "error": "Mesaj boş olamaz."
        }), 400

    hatirla_desenleri = ["hatırla:", "hatirla:", "unutma:"]
    mesaj_kucuk = mesaj.lower()

    for desen in hatirla_desenleri:
        if mesaj_kucuk.startswith(desen):
            bilgi = mesaj[len(desen):].strip()
            if bilgi:
                hafiza_ekle(bilgi)
            break

    kalici_hafiza = hafiza_metni()
    karar = eagle_karar_motoru(mesaj)
    print(f"🧠 EAGLE KARAR: {karar}", flush=True)

    # 🧠 Karar motorunun seçtiği aracı çalıştır
    borc_modulu_sonucu = ""
    if karar.get("arac") == "borc_modulu":
        try:
            borc_modulu_sonucu = borc_modulu.borc_mesaji_isle(mesaj)
            print("🧾 BORÇ MODÜLÜ ÇALIŞTI", flush=True)
        except Exception as e:
            borc_modulu_sonucu = f"Borç modülü çalıştırılırken hata oluştu: {e}"
            print(f"❌ BORÇ MODÜLÜ HATASI: {e}", flush=True)

    hava_verisi = hava_durumu_getir(mesaj)

    # 🌐 Güncel bilgi gerekiyorsa ücretsiz web araştırması yap
    web_verisi = []

    if karar.get("arac") == "spor_kaynaklari":
        if karar.get("intent") == "spor":
            # 🏐 Spor sorularında önce resmi TVF kaynağı
            gecmis_mac = any(k in mesaj.lower() for k in [
                "dün", "dünkü", "dünün",
                "dun", "dunku", "dunun",
                "geçen maç", "gecen mac",
                "sonuç", "sonuc", "sonuçları", "sonuclari",
                "skor", "skorları", "skorlari"
            ])

            if any(k in mesaj.lower() for k in [
                "voleybol",
                "filenin sultanları",
                "filenin efeleri"
            ]) and not gecmis_mac:
                web_verisi = tvf_voleybol_getir()

            # 🇬🇧 İngiltere / Premier League için resmi canlı API
            mesaj_spor = mesaj.lower().replace("\u0307", "")

            ingiltere_mi = any(k in mesaj_spor for k in [
                "ingiltere",
                "ingiltere'de",
                "ingilterede",
                "premier lig",
                "premier league"
            ])

            if ingiltere_mi and not web_verisi:
                web_verisi = premier_lig_getir(mesaj)

            # 🇹🇷 Türkiye / Süper Lig için resmi TFF fikstürü
            super_lig_mi = any(k in mesaj_spor for k in [
                "süper lig",
                "super lig"
            ])

            if super_lig_mi and not web_verisi:
                web_verisi = super_lig_getir(mesaj)

            # Resmi kaynak sonuç vermezse mevcut web araması
            if not web_verisi:
                arama_sorgusu = spor_arama_sorgusu(mesaj)
                web_verisi = web_arastir(
                    arama_sorgusu,
                    limit=8
                )
        else:
            web_verisi = web_arastir(mesaj)

    web_metni = web_sonuclari_metni(web_verisi)

    # 🧮 Güvenli matematik doğrulaması
    hesaplama_metni = ""
    if re.fullmatch(r"[0-9+*/().%\-\s]+", mesaj):
        ifade = mesaj.replace("%", "/100")
        ok, sonuc_hesap = guvenli_hesapla(ifade)
        if ok:
            hesaplama_metni = (
                "\n\n===== GERÇEK HESAPLAMA SONUCU =====\n"
                f"İfade: {ifade}\n"
                f"Sonuç: {sonuc_hesap}\n"
                "Bu sonuç EagleAI güvenli hesaplama motoruyla doğrulandı. "
                "Cevap verirken bu sonucu esas al.\n"
                "===== HESAPLAMA SONU ====="
            )


    # 🧠 Güvenli mantıksal doğrulama
    mantiksal_metni = ""
    ok, sonuc_mantiksal = guvenli_mantiksal_hesapla(mesaj)
    if ok:
        mantiksal_metni = sonuc_mantiksal

    hava_metni = ""

    if hava_verisi and hava_verisi.get("ok"):
        hava_metni = (
            "\n\n===== CANLI HAVA DURUMU (GERÇEK VERİ) =====\n"
            "AŞAĞIDAKİ VERİ GERÇEK VE GÜNCELDİR. Hava durumu sorusuna cevap "
            "verirken SADECE bu veriyi kullan. Başka bir şehir, ülke veya "
            "sıcaklık UYDURMA. Bu veride 'city' alanında belirtilen şehri "
            "kullan, farklı bir yer adı söyleme.\n"
            + json.dumps(
                hava_verisi,
                ensure_ascii=False,
                indent=2
            )
            + "\n===== HAVA DURUMU SONU ====="
        )

    elif hava_verisi and not hava_verisi.get("ok"):
        hava_metni = (
            "\n\n===== HAVA DURUMU BİLGİSİ =====\n"
            + hava_verisi.get("error", "")
            + "\n===== HAVA DURUMU SONU ====="
        )

    # 🦅 Eagle'ın kendi çözebildiği isteklerde Gemini'yi hiç çağırma
    if karar.get("arac") == "borc_modulu" and borc_modulu_sonucu:
        return jsonify({
            "ok": True,
            "answer": borc_modulu_sonucu,
            "memory_count": len(hafiza_yukle()),
            "eagle_direct": True
        })

    if karar.get("arac") == "hava_api" and hava_verisi and hava_verisi.get("ok"):
        return jsonify({
            "ok": True,
            "answer": hava_metni,
            "memory_count": len(hafiza_yukle()),
            "eagle_direct": True
        })

    if karar.get("intent") == "spor" and web_verisi:
        spor_satirlari = ["⚽ GÜNCEL SPOR BİLGİSİ"]
        for sonuc in web_verisi[:8]:
            baslik = str(sonuc.get("title", "")).strip()
            ozet = str(sonuc.get("snippet", "")).strip()
            if baslik:
                spor_satirlari.append(baslik)
            if ozet:
                spor_satirlari.append(ozet)
        return jsonify({
            "ok": True,
            "answer": "\n".join(spor_satirlari),
            "web_search": True,
            "eagle_direct": True,
            "memory_count": len(hafiza_yukle())
        })

    if hesaplama_metni and karar.get("intent") == "matematik":
        return jsonify({
            "ok": True,
            "answer": hesaplama_metni,
            "eagle_direct": True,
            "memory_count": len(hafiza_yukle())
        })

    sistem = (
        SYSTEM_PROMPT
        + "\n\n===== EAGLE HAFIZA =====\n"
        + kalici_hafiza
        + "\n===== HAFIZA SONU ====="
        + hava_metni
        + web_metni
          + hesaplama_metni
        + mantiksal_metni
        + (
            "\n\n===== GERÇEK BORÇ MODÜLÜ SONUCU =====\n"
            "Aşağıdaki bilgi EagleAI borç modülünden alınmıştır. "
            "Borçlarla ilgili cevap verirken bu veriyi esas al, "
            "rakamları değiştirme veya uydurma.\n"
            + borc_modulu_sonucu
            + "\n===== BORÇ MODÜLÜ SONU ====="
            if borc_modulu_sonucu
            else ""
        )
    )

    contents = [
        {
            "role": "user",
            "parts": [
                {
                    "text": sistem
                }
            ]
        },
        {
            "role": "model",
            "parts": [
                {
                    "text":
                    "Anladım. Eagle-AI olarak "
                    "hafızamdaki bilgileri de kullanarak "
                    "Türkçe yardımcı olacağım."
                }
            ]
        }
    ]

    if isinstance(gecmis, list):

        for item in gecmis[-20:]:

            if (
                isinstance(item, dict)
                and item.get("role") in ("user", "model")
                and isinstance(item.get("text"), str)
            ):

                contents.append({
                    "role": item["role"],
                    "parts": [
                        {
                            "text": item["text"]
                        }
                    ]
                })

    # 📎 Android'den gelen dosya
    file_base64 = data.get("file_base64")
    file_mime = str(
        data.get("file_mime", "")
    ).strip().lower()

    user_parts = [
        {
            "text": mesaj
        }
    ]

    # Şimdilik yalnızca görselleri Gemini'ye gönder
    if file_base64 and file_mime.startswith("image/"):
        try:
            # Base64 verisinin gerçekten çözülebildiğini kontrol et
            base64.b64decode(
                file_base64,
                validate=True
            )

            user_parts.append({
                "inline_data": {
                    "mime_type": file_mime,
                    "data": file_base64
                }
            })

            print(
                f"📎 Görsel alındı: {file_mime}",
                flush=True
            )

        except Exception as e:
            print(
                f"⚠️ Görsel Base64 okunamadı: {e}",
                flush=True
            )

    contents.append({
        "role": "user",
        "parts": user_parts
    })

    if not GEMINI_API_KEY:
        return jsonify({
            "ok": False,
            "error": "GEMINI_API_KEY bulunamadı."
        }), 500

    try:

        # Gemini isteği
        # 🌐 Güncel internet araştırması için Google Search
        gemini_baslangic = time.time()
        print("⏱️ GEMINI BAŞLADI", flush=True)

        response = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json={
                "contents": contents
            },
            timeout=20
        )

        print(
            f"⏱️ GEMINI BİTTİ: {time.time() - gemini_baslangic:.2f} saniye",
            flush=True
        )

        try:
            sonuc = response.json()
        except Exception:
            sonuc = {}

        if response.status_code == 429:
            print(
                "🌐 Gemini kotası dolu — ücretsiz web sonuçları fallback olarak kullanılıyor.",
                flush=True
            )

            if web_verisi:
                return jsonify({
                    "ok": True,
                    "answer": (
                        "🦅 Gemini'nin günlük kullanım limiti dolu. "
                        "Ücretsiz internet araştırma sonuçlarını doğrudan gösteriyorum.\n\n"
                        + web_metni
                    ),
                    "web_search": True,
                    "gemini_fallback": True,
                    "memory_count": len(hafiza_yukle())
                })

            return jsonify({
                "ok": False,
                "error": "Gemini kullanım limiti dolu ve web sonucu bulunamadı."
            }), 429

        if response.status_code == 200 and sonuc.get("candidates"):
            try:
                aday = sonuc["candidates"][0]
                icerik = aday.get("content", {})
                parcalar = icerik.get("parts", [])
                cevap = ""

                for parca in parcalar:
                    if isinstance(parca, dict) and parca.get("text"):
                        cevap += parca["text"]

            except (KeyError, IndexError, TypeError, AttributeError):
                cevap = ""

            if cevap.strip():
                return jsonify({
                    "ok": True,
                    "answer": cevap,
                    "memory_count": len(hafiza_yukle())
                })

        if response.status_code == 503:
            return jsonify({
                "ok": False,
                "error": "Gemini şu anda yoğun."
            }), 503

        return jsonify({
            "ok": False,
            "error": "Gemini API hatası.",
            "details": sonuc
        }), 500

    except requests.exceptions.RequestException as e:
        hata_mesaji = "Gemini bağlantısı zaman aşımına uğradı veya ağ hatası oluştu: " + str(e)
        print("⚠️ " + hata_mesaji, flush=True)
        try:
            with open("eagle_api.log", "a", encoding="utf-8") as log_f:
                import datetime
                zaman = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_f.write("[" + zaman + "] TIMEOUT/NETWORK ERROR: " + hata_mesaji + "\n")
        except Exception:
            pass
        return jsonify({
            "ok": False,
            "error": "Gemini bağlantısı zaman aşımına uğradı."
        }), 504

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":

    print("=" * 40)
    print("🦅 EAGLE-AI API")
    print("=" * 40)
    print("API: http://127.0.0.1:5000")
    print("Durum: http://127.0.0.1:5000/api/durum")
    print("Hafıza: http://127.0.0.1:5000/api/hafiza")
    print("=" * 40)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
