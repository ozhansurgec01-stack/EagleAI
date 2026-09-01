from flask import Flask, request, jsonify
import os
import base64
import requests
from urllib.parse import quote, urlparse, parse_qs, unquote
from bs4 import BeautifulSoup
import re
import json
from pathlib import Path

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-3.5-flash-lite"

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent?key={GEMINI_API_KEY}"
)

MEMORY_FILE = Path("eagle_ai_memory.json")

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
        "tenis", "hentbol",
        "milli takım", "milli takim",
        "şampiyonlar ligi", "süper lig", "super lig",
        "premier lig", "la liga", "serie a", "bundesliga",
        "maçımız", "macimiz",
        "oynanıyor", "oynanacak",
        "hangi maç", "hangi mac"
    ]

    mesaj_kucuk = mesaj.lower()
    return any(kelime in mesaj_kucuk for kelime in kelimeler)


def spor_arama_sorgusu(mesaj):
    """Spor sorusunu güncel ve resmi kaynak öncelikli aramaya dönüştürür."""
    mesaj_kucuk = mesaj.lower()

    # Voleybol sorularında resmi TVF kaynaklarını özellikle hedefle.
    if any(k in mesaj_kucuk for k in [
        "voleybol",
        "filenin sultanları",
        "filenin efeleri"
    ]):
        return (
            mesaj.strip()
            + " bugün maç programı maç saati "
            + "site:tvf.org.tr OR site:fikstur.tvf.org.tr"
        )

    return (
        mesaj.strip()
        + " bugün maç programı maç saati sonuçları "
        + "Türkiye"
    )


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

            if cevap.status_code == 200:
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

def web_sonuclari_metni(sonuclar):
    """Web sonuçlarını Gemini'ye aktarılacak metne çevirir."""
    if not sonuclar:
        return ""

    satirlar = [
        "",
        "===== ÜCRETSİZ WEB ARAŞTIRMASI =====",
        "Aşağıdaki bilgiler internet aramasından alınmıştır.",
        "Kaynakları dikkate al ve desteklenmeyen bilgi uydurma.",
        ""
    ]

    for i, sonuc in enumerate(sonuclar, 1):
        satirlar.append(
            f"[KAYNAK {i}]\n"
            f"Başlık: {sonuc['title']}\n"
            f"Adres: {sonuc['url']}\n"
            f"Özet: {sonuc['snippet']}\n"
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

    if not GEMINI_API_KEY:
        return jsonify({
            "ok": False,
            "error": "GEMINI_API_KEY bulunamadı."
        }), 500

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

    hava_verisi = hava_durumu_getir(mesaj)

    # 🌐 Güncel bilgi gerekiyorsa ücretsiz web araştırması yap
    web_verisi = []

    if web_arastirma_gerekli(mesaj):
        if spor_sorgusu_mu(mesaj):
            arama_sorgusu = spor_arama_sorgusu(mesaj)
            web_verisi = web_arastir(arama_sorgusu, limit=8)
        else:
            web_verisi = web_arastir(mesaj)

    web_metni = web_sonuclari_metni(web_verisi)

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

    sistem = (
        SYSTEM_PROMPT
        + "\n\n===== EAGLE HAFIZA =====\n"
        + kalici_hafiza
        + "\n===== HAFIZA SONU ====="
        + hava_metni
        + web_metni
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

    try:

        # Gemini isteği
        # 🌐 Güncel internet araştırması için Google Search
        response = requests.post(
            GEMINI_URL,
            json={
                "contents": contents
            },
            timeout=60
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

    except requests.exceptions.Timeout:

        return jsonify({
            "ok": False,
            "error":
            "Gemini bağlantısı zaman aşımına uğradı."
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
