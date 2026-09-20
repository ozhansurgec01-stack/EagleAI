from eagle_merkez_motoru import eagle_merkez_motorunu_kur
from eagle_akil_motoru import eagle_akil_motorunu_kur
from eagle_autofix import EagleAutoFixEngine
from eagle_genel_sohbet import genel_sohbet
from flask import Flask, request, jsonify
import os


def _env_dosyasini_yukle(dosya_yolu=".env"):
    """.env dosyasındaki anahtar=deger satırlarını ortam değişkenlerine yükler."""
    if not os.path.exists(dosya_yolu):
        return
    try:
        with open(dosya_yolu, encoding="utf-8") as _f:
            _icerik = _f.read()
        for satir in _icerik.splitlines():
            satir = satir.strip()
            if not satir or satir.startswith("#") or "=" not in satir:
                continue
            anahtar, deger = satir.split("=", 1)
            anahtar = anahtar.strip()
            deger = deger.strip().strip('"').strip("'")
            if anahtar and anahtar not in os.environ:
                os.environ[anahtar] = deger
    except Exception:
        pass


_env_dosyasini_yukle()
import time
import base64
import requests
from urllib.parse import quote, urlparse, parse_qs, unquote
from bs4 import BeautifulSoup
import re
import json
import ast
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)
import operator
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta

app = Flask(__name__)

# 🦅 Eagle otomatik kod düzeltme motoru
autofix_engine = EagleAutoFixEngine(Path(__file__).resolve().parent)

# 🧠 Eagle merkezi akıllı koordinasyon motoru
merkez_motor = eagle_merkez_motorunu_kur()


# --- EAGLE BORÇ/TAKSİT ENTEGRASYONU ---
from flask import request, jsonify
import borc_modulu

@app.route('/api/borclar', methods=['GET'])
def api_borclari_getir():
    try:
        veri = borc_modulu.borclari_yukle()
        return jsonify({'success': True, 'borclar': veri})
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
        if kisi and tutar:
            borc_modulu.borc_ekle(
                kisi,
                kategori,
                float(tutar)
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
        odenen = data.get('odenen')

        basari, guncel = borc_modulu.borc_guncelle(
            borc_id,
            ad=ad,
            kategori=kategori,
            toplam_borc=float(tutar) if tutar is not None else None,
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
            basari, guncel = borc_modulu.odeme_yap(kisi, float(tutar))

            if not basari:
                return jsonify({
                    'success': False,
                    'error': 'Borç bulunamadı veya ödeme tutarı geçersiz.'
                }), 404

            return jsonify({
                'success': True,
                'message': 'Ödeme başarıyla işlendi.',
                'borc': guncel
            })
        return jsonify({'success': False, 'error': 'Kisi ve tutar gerekli.'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



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
                    raise ValueError("İzin verilmeyen karşılaştırma")

                sonuc = sonuc and parca
                sol = sag

            if sonuc:
                dogru += 1
                durum = "DOĞRU"
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
                return {
                    "kullanici": veri,
                    "eagle_ogrenme": [],
                    "sohbet": []
                }

            if isinstance(veri, dict):
                return {
                    "kullanici": veri.get("kullanici", []),
                    "eagle_ogrenme": veri.get("eagle_ogrenme", []),
                    "sohbet": veri.get("sohbet", [])
                }

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

    # Yeni bilgiler kullanıcı hafızasına kaydedilir.
    veri = json.loads(MEMORY_FILE.read_text(encoding="utf-8")) if MEMORY_FILE.exists() else {}
    if not isinstance(veri, dict):
        veri = {
            "kullanici": hafiza,
            "eagle_ogrenme": [],
            "sohbet": []
        }

    kullanici = veri.setdefault("kullanici", [])

    if bilgi in kullanici:
        return False

    kullanici.append(bilgi)

    if len(kullanici) > 100:
        veri["kullanici"] = kullanici[-100:]

    hafiza_kaydet(veri)
    return True


def sohbet_hafizaya_ekle(soru, cevap, konu="", kaynak=None):
    soru = str(soru).strip()
    cevap = str(cevap).strip()
    konu = str(konu).strip()

    if not soru or not cevap:
        return False

    veri = hafiza_yukle()
    sohbet = veri.setdefault("sohbet", [])

    kayit = {
        "soru": soru,
        "cevap": cevap
    }

    if konu:
        kayit["konu"] = konu

    if kaynak:
        kayit["kaynak"] = str(kaynak).strip()

    sohbet.append(kayit)

    if len(sohbet) > 500:
        veri["sohbet"] = sohbet[-500:]

    hafiza_kaydet(veri)
    return True


def eagle_ogrenme_ekle(
    konu,
    bilgi,
    kaynak=None,
    soru=None,
    intent=None,
    arac=None,
    strateji=None
):
    konu = str(konu).strip()
    bilgi = str(bilgi).strip()

    if not konu or not bilgi:
        return False

    veri = hafiza_yukle()
    ogrenme = veri.setdefault("eagle_ogrenme", [])
    konu_key = konu.casefold()
    bilgi_key = bilgi.casefold()

    for kayit in ogrenme:
        if not isinstance(kayit, dict):
            continue

        if str(kayit.get("konu", "")).strip().casefold() != konu_key:
            continue

        if str(kayit.get("bilgi", "")).strip().casefold() == bilgi_key:
            return False

        kayit["bilgi"] = bilgi

        if kaynak:
            kayit["kaynak"] = str(kaynak).strip()
        if soru:
            kayit["soru"] = str(soru).strip()
        if intent:
            kayit["intent"] = str(intent).strip()
        if arac:
            kayit["arac"] = str(arac).strip()
        if strateji:
            kayit["strateji"] = str(strateji).strip()

        hafiza_kaydet(veri)
        return True

    kayit = {
        "konu": konu,
        "bilgi": bilgi
    }

    if kaynak:
        kayit["kaynak"] = str(kaynak).strip()
    if soru:
        kayit["soru"] = str(soru).strip()
    if intent:
        kayit["intent"] = str(intent).strip()
    if arac:
        kayit["arac"] = str(arac).strip()
    if strateji:
        kayit["strateji"] = str(strateji).strip()

    ogrenme.append(kayit)

    if len(ogrenme) > 500:
        veri["eagle_ogrenme"] = ogrenme[-500:]

    hafiza_kaydet(veri)
    return True


def hafiza_sil(bilgi):
    bilgi = str(bilgi).strip()

    if not bilgi:
        return False

    veri = json.loads(MEMORY_FILE.read_text(encoding="utf-8")) if MEMORY_FILE.exists() else {}

    if isinstance(veri, list):
        veri = {
            "kullanici": veri,
            "eagle_ogrenme": [],
            "sohbet": []
        }

    kullanici = veri.setdefault("kullanici", [])
    yeni_hafiza = [x for x in kullanici if str(x).strip() != bilgi]

    if len(yeni_hafiza) == len(kullanici):
        return False

    veri["kullanici"] = yeni_hafiza
    hafiza_kaydet(veri)
    return True




KNOWLEDGE_FILE = Path("eagle_bilgi.json")

def bilgi_bankasi_yukle():
    try:
        if KNOWLEDGE_FILE.exists():
            veri = json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8"))
            if isinstance(veri, dict):
                return veri
    except Exception as e:
        print("⚠️ Bilgi bankası okunamadı:", e, flush=True)
    return {}

def bilgi_bankasi_ara(mesaj):
    metin = str(mesaj or "").replace("İ", "i").lower()

    # Yaygın Python yazım hatalarını normalize et
    metin = re.sub(r"\bpyhton\b", "python", metin)

    konu_eslesmeleri = {
        "comprehension": ["comprehension", "liste comprehension", "dictionary comprehension", "set comprehension"],
        "lambda": ["lambda", "lambda fonksiyonu", "lambda fonksiyonları", "lambda fonksiyonlari", "anonim fonksiyon"],
        "enumerate": ["enumerate", "enumerate()", "indeks ve eleman"],
        "zip": ["zip", "zip()", "koleksiyonları birlikte"],
        "map": ["map", "map()", "haritalama fonksiyonu"],
        "filter": ["filter", "filter()", "filtreleme fonksiyonu"],
        "sorted": ["sorted", "sorted()", "sıralama"],
        "any_all": ["any", "any()", "all", "all()", "koşulların tamamı", "en az biri"],
        "liste": ["liste", "listeler", "list", "listeleme", "append", "remove", "extend", "insert", "pop", "clear", "reverse", "dilimleme", "indeks"],
        "fonksiyon": ["fonksiyon", "fonksiyonlar", "def", "parametre", "return", "find", "count", "isdigit", "isalpha", "isalnum", "capitalize", "title", "f-string"],
        "döngü": ["döngü", "dongu", "for", "while"],
        "değişken": ["değişken", "degisken", "variable"],
        "sözlük": ["sözlük", "sozluk", "dictionary", "dict", "keys", "values", "items"],
        "tuple": ["tuple"],
        "set": ["set"],
        "veri tipi": ["veri tipi", "veritipi", "str", "int", "float", "bool"],
        "if else": ["if", "else", "koşul", "kosul"],
        "try except": ["try", "except", "exception", "hata"],
        "import": ["import", "modül", "modul", "kütüphane", "kutuphane"],
        "class": ["class", "sınıf", "sinif", "nesne"],
        "print": ["print"],
        "input": ["input"],
        "type": ["type"],
        "isinstance": ["isinstance", "isinstance()"],
        "len": ["len"],
        "algoritma": ["algoritma"],
        "json": ["json", "json nedir", "json dosyası", "json dosyasi"],
        "python": ["python", "py", "python nedir", "python öğren", "python ogren", "os", "os.getcwd", "os.listdir", "os.mkdir", "os.makedirs", "os.remove", "os.path.exists", "path.exists", "path.mkdir", "path.name", "path.suffix"],
        "api": ["api", "api nedir", "api ne işe yarar", "api ne ise yarar"],
        "http": ["http", "http nedir", "404", "200", "429", "500"],
        "flask": ["flask", "flask nedir", "flask route", "flask api"],
        "matematik": [
            "matematik", "toplama", "çıkarma", "cikarma", "çarpma", "carpma",
            "bölme", "bolme", "işlem önceliği", "islem onceligi",
            "üslü sayı", "uslu sayi", "üslü sayılar", "uslu sayilar",
            "karekök", "karekok", "yüzde", "yuzde", "zam", "indirim",
            "oran", "orantı", "oranti", "ortalama", "mutlak değer",
            "mutlak deger", "pozitif sayı", "negatif sayı",
            "pozitif negatif", "kesir", "kesirler", "ondalık sayı",
            "ondalik sayi", "bölünebilme", "bolunebilme", "asal sayı",
            "asal sayi", "ebob", "ekok", "denklem", "denklem çöz",
            "denklem coz"
        ]
    }

    konu = None

    # ➗ Matematik sorularını genel Python kelimelerinden önce yakala.
    # Böylece "bölünebilme kuralları" içindeki "all" gibi
    # alt kelimelerin yanlış konuya eşleşmesi önlenir.
    matematik_oncelik = (
        "matematik", "toplama", "çıkarma", "cikarma", "çarpma", "carpma",
        "bölme", "bolme", "işlem önceliği", "islem onceligi",
        "üslü sayı", "uslu sayi", "üslü sayılar", "uslu sayilar",
        "karekök", "karekok", "yüzde", "yuzde", "zam", "indirim",
        "oran", "orantı", "oranti", "ortalama", "mutlak değer",
        "mutlak deger", "pozitif sayı", "negatif sayı", "pozitif negatif",
        "kesir", "kesirler", "ondalık sayı", "ondalik sayi",
        "bölünebilme", "bolunebilme", "asal sayı", "asal sayi",
        "ebob", "ekok", "denklem"
    )

    if any(k in metin for k in matematik_oncelik):
        konu = "matematik"
        for ad, kelimeler in konu_eslesmeleri.items():
            if any(k in metin for k in kelimeler):
                konu = ad
                break

    bilgi = bilgi_bankasi_yukle()
    bulunan = []

    # 🎯 Yeni Python soru/cevap kayıtlarında önce özgül soru eşleşmesi yap.
    # Böylece "Python NameError nedir?" gibi sorular genel "Python nedir?"
    # kaydına takılmaz.
    python_kayitlari = bilgi.get("python", {})
    for kategori, maddeler in python_kayitlari.items():
        if not isinstance(maddeler, list):
            continue

        for madde in maddeler:
            if not isinstance(madde, dict):
                continue

            soru = str(madde.get("soru", "")).strip()
            cevap = str(madde.get("cevap", "")).strip()

            if not soru or not cevap:
                continue

            soru_metin = soru.lower().replace("İ", "i")
            kullanici_metin = metin.lower().replace("İ", "i")

            # "Python'da" / "Python da" / "Python" farkını kaldır.
            soru_norm = re.sub(r"python(?:['’]da| da)?\b", "python", soru_metin)
            metin_norm = re.sub(r"python(?:['’]da| da)?\b", "python", kullanici_metin)

            # Noktalama ve fazla boşlukları normalize et.
            soru_norm = re.sub(r"[^a-z0-9çğıöşü\s]", " ", soru_norm)
            metin_norm = re.sub(r"[^a-z0-9çğıöşü\s]", " ", metin_norm)
            soru_norm = re.sub(r"\s+", " ", soru_norm).strip()
            metin_norm = re.sub(r"\s+", " ", metin_norm).strip()

            if soru_norm == metin_norm:
                return [cevap]

    # ➗ Matematik bilgi bankası için özel arama
    if konu == "matematik":
        matematik = bilgi.get("matematik", {})
        matematik_eslesmeleri = {
            "temel_islemler": ["toplama", "çıkarma", "cikarma", "çarpma", "carpma", "bölme", "bolme", "temel işlem"],
            "islem_onceligi": ["işlem önceliği", "islem onceligi", "öncelik sırası", "oncelik sirasi"],
            "uslu_sayilar": ["üslü sayı", "uslu sayi", "üslü sayılar", "uslu sayilar", "üs", "us"],
            "karekok": ["karekök", "karekok", "karekök nedir", "karekok nedir"],
            "yuzde": ["yüzde", "yuzde", "%"],
            "ters_yuzde": ["ters yüzde", "ters yuzde", "yüzde ise sayı", "yuzde ise sayi"],
            "zam": ["zam", "zam gelirse", "zam oranı", "zam orani"],
            "indirim": ["indirim", "indirim oranı", "indirim orani"],
            "oran": ["oran", "oran nedir"],
            "oranti": ["orantı", "oranti", "orantı nedir", "oranti nedir"],
            "ortalama": ["ortalama", "aritmetik ortalama", "ortalama nedir"],
            "mutlak_deger": ["mutlak değer", "mutlak deger", "mutlak değer nedir", "mutlak deger nedir"],
            "pozitif_negatif_sayilar": ["pozitif sayı", "negatif sayı", "pozitif negatif", "pozitif ve negatif"],
            "kesirler": ["kesir", "kesirler", "kesir nedir", "kesirler nasıl"],
            "ondalik_sayilar": ["ondalık sayı", "ondalik sayi", "ondalık sayılar", "ondalik sayilar"],
            "bolunebilme": ["bölünebilme", "bolunebilme", "bölünebilme kuralları", "bolunebilme kurallari"],
            "asal_sayilar": ["asal sayı", "asal sayi", "asal sayılar", "asal sayilar"],
            "ebob": ["ebob", "ebob nedir", "en büyük ortak bölen"],
            "ekok": ["ekok", "ekok nedir", "en küçük ortak kat"],
            "basit_denklem": ["denklem", "denklem çöz", "denklem coz", "basit denklem"]
        }

        secilen = None
        for alt_konu, kelimeler in matematik_eslesmeleri.items():
            if any(k in metin for k in kelimeler):
                secilen = alt_konu
                break

        if secilen and isinstance(matematik.get(secilen), dict):
            kayit = matematik[secilen]
            parcalar = []

            for alan in ("aciklama", "formul", "kural", "kurallar", "sira", "not", "ornek", "ornekler"):
                deger = kayit.get(alan)
                if isinstance(deger, str):
                    parcalar.append(deger)
                elif isinstance(deger, list):
                    parcalar.extend(str(x) for x in deger)

            if parcalar:
                return parcalar[:3]

    # 🎯 Yeni Python konularında tam soru önceliği.
    # İlgili başka kayıtlar yerine doğrudan sorulan kavramın kaydını seçer.
    ozgun_python_sorular = {
        "datetime.now()": ["datetime.now() ne işe yarar?"],
        "timedelta": ["timedelta nedir?"],
        "math.sqrt()": ["math.sqrt() ne işe yarar?"],
        "super()": ["super() ne işe yarar?"],
        "venv": ["Python venv nedir?"],
        "pip install": ["pip install ne işe yarar?"],
        "Python paketi": ["Python paketi nedir?"],
        "iterator": ["Iterator nedir?"],
        "generator": ["Generator nedir?"],
        "yield": ["yield ne işe yarar?"],
        "decorator": ["Python decorator nedir?"],
        "async await": ["async/await nedir?"],
    }

    mesaj_norm = re.sub(r"[^a-z0-9çğıöşü\s]", " ", metin.lower())
    mesaj_norm = re.sub(r"\s+", " ", mesaj_norm).strip()

    # 🎯 super() için doğrudan kavram eşleşmesi.
    # Genel "değişken" vb. kayıtların super() sorusunu gölgelemesini önler.
    if "super" in mesaj_norm and "ne işe yarar" in mesaj_norm:
        for maddeler in bilgi.get("python", {}).values():
            if not isinstance(maddeler, list):
                continue
            for madde in maddeler:
                if not isinstance(madde, dict):
                    continue
                soru = str(madde.get("soru", "")).strip().lower()
                cevap = str(madde.get("cevap", "")).strip()
                if soru == "super() ne işe yarar?" and cevap:
                    return [cevap]

    for terim, sorular in ozgun_python_sorular.items():
        terim_norm = re.sub(r"[^a-z0-9çğıöşü\s]", " ", terim.lower())
        terim_norm = re.sub(r"\s+", " ", terim_norm).strip()
        if terim_norm not in mesaj_norm:
            continue

        for kategori, maddeler in bilgi.get("python", {}).items():
            if not isinstance(maddeler, list):
                continue
            for madde in maddeler:
                if not isinstance(madde, dict):
                    continue
                soru = str(madde.get("soru", "")).strip()
                cevap = str(madde.get("cevap", "")).strip()
                if not soru or not cevap:
                    continue

                soru_norm = re.sub(r"[^a-z0-9çğıöşü\s]", " ", soru.lower())
                soru_norm = re.sub(r"\s+", " ", soru_norm).strip()

                for hedef_soru in sorular:
                    hedef_norm = re.sub(r"[^a-z0-9çğıöşü\s]", " ", hedef_soru.lower())
                    hedef_norm = re.sub(r"\s+", " ", hedef_norm).strip()
                    # Özel kayıt yalnızca hedef soru ifadesi gerçekten
                    # mesajın içinde geçiyorsa doğrudan seçilir.
                    # Terim başka bir sorunun bağlamında geçiyorsa
                    # aşağıdaki çoklu kavram motoruna bırakılır.
                    if hedef_norm in mesaj_norm:
                        return [cevap]

    # 🎯 isinstance() eski tip düz KB kayıtlarında tutulduğu için
    # özel doğrudan eşleşmeyle seç.
    if re.search(r"\bisinstance\s*\(?", metin, re.IGNORECASE):
        python_kayitlari = bilgi.get("python", {})
        for maddeler in python_kayitlari.values():
            if not isinstance(maddeler, list):
                continue
            for madde in maddeler:
                if isinstance(madde, str) and "isinstance()" in madde.lower():
                    return [madde]
                if isinstance(madde, dict):
                    soru = str(madde.get("soru", "")).lower()
                    cevap = str(madde.get("cevap", "")).strip()
                    if "isinstance" in soru and cevap:
                        return [cevap]

    # 🎯 Özel Python terimleri için akıllı eşleştirme
    # Bir soruda geçen yardımcı bir terimin ana konuyu gölgelemesini önler.
    # Çoklu kavramlar, olumsuz ifadeler ve soru içindeki güçlü bağlam
    # birlikte değerlendirilir.

    ozel_terimler = (
        "super().__init__()", "super().__init__",
        "datetime.now()", "math.sqrt()",
        "os.getcwd()", "os.listdir()", "os.mkdir()", "os.makedirs()",
        "os.remove()", "os.path.exists()", "path.exists()", "path.mkdir()",
        "path.name", "path.suffix", "f-string",
        "find()", "count()", "isdigit()", "isalpha()", "isalnum()",
        "capitalize()", "title()",
        "append()", "extend()", "insert()", "remove()", "pop()", "clear()",
        "copy()", "copy", "reverse()", "keys()", "values()", "items()",
        "get()", "update()", "isinstance()", "isinstance",
        "break", "continue", "super()", "__init__",
        "timedelta", "venv", "pip install", "pip",
        "paket", "iterator", "iter()", "next()", "generator",
        "yield", "decorator", "async", "await",
        "comprehension", "list comprehension", "dictionary comprehension",
        "set comprehension", "filter()", "filter", "map()", "map",
        "lambda"
    )

    mesaj_alt = metin.lower().replace(" ", "")
    ozel_terimler = tuple(sorted(ozel_terimler, key=len, reverse=True))

    eslesen_terimler = [
        terim for terim in ozel_terimler
        if terim.lower().replace(" ", "") in mesaj_alt
    ]

    if eslesen_terimler:
        adaylar = []

        # Olumsuz/kaçınma ifadeleri.
        # Örn. "filter() kullanmadan" sorusunda filter kaydı ana cevap olmamalı.
        filter_yasak = bool(re.search(
            r"filter\(\)?[^.!?]{0,30}\b(kullanmadan|kullanma|olmadan|yerine)\b"
            r"|\b(kullanmadan|kullanma|olmadan|yerine)\b[^.!?]{0,30}filter\(\)?",
            metin
        ))

        # Çoklu kavramlar için güçlü bağlam çiftleri.
        coklu_kavramlar = [
            ("super()", "__init__"),
            ("super().__init__", "__init__"),
            ("comprehension", "liste"),
            ("list comprehension", "liste"),
            ("copy()", "append()"),
            ("copy", "append()"),
            ("isinstance", "liste"),
            ("fonksiyon", "append()"),
        ]

        for kategori, maddeler in bilgi.get("python", {}).items():
            if not isinstance(maddeler, list):
                continue

            for madde in maddeler:
                if isinstance(madde, dict):
                    soru_metin = str(madde.get("soru", ""))
                    cevap_metin = str(madde.get("cevap", ""))
                    gosterilecek = cevap_metin.strip()
                elif isinstance(madde, str):
                    soru_metin = madde
                    cevap_metin = ""
                    gosterilecek = madde.strip()
                    continue

                if not gosterilecek:
                    continue

                soru_alt = soru_metin.lower().replace(" ", "")
                cevap_alt = cevap_metin.lower().replace(" ", "")
                madde_alt = (soru_metin + " " + cevap_metin).lower()

                # datetime sorgusunda datetime.now() kaydını yanlışlıkla
                # genel datetime sorusuna seçtirme.
                if (
                    "datetime" in eslesen_terimler
                    and "datetime.now()" in madde_alt
                    and "datetime.now()" not in mesaj_alt
                ):
                    continue

                soru_eslesen = sum(
                    1 for terim in eslesen_terimler
                    if terim.lower().replace(" ", "") in soru_alt
                )

                cevap_eslesen = sum(
                    1 for terim in eslesen_terimler
                    if terim.lower().replace(" ", "") in cevap_alt
                )

                # Bazı yardımcı terimler soru içinde özellikle
                # kullanılmamak üzere geçebilir. Örneğin:
                # "filter() kullanmadan yeni listeye seçmek"
                # sorusu doğrudan list comprehension konusunu anlatır.
                anlam_eslesmesi = (
                    filter_yasak
                    and "comprehension" in madde_alt
                    and (
                        "yeni liste" in metin
                        or "listeye" in metin
                        or "seçerim" in metin
                        or "seçmek" in metin
                    )
                )

                if not soru_eslesen and not cevap_eslesen and not anlam_eslesmesi:
                    continue

                # Soru başlığındaki terim, cevaptaki terimden çok daha değerlidir.
                puan = (soru_eslesen * 320) + (cevap_eslesen * 12)

                # Sorunun gerçek metnindeki anlamlı kelimeleri de dikkate al.
                soru_kelimeleri = set(
                    re.findall(r"[a-z0-9çğıöşü]+", metin)
                )
                kayit_kelimeleri = set(
                    re.findall(r"[a-z0-9çğıöşü]+", soru_metin.lower())
                )

                ortak = soru_kelimeleri & kayit_kelimeleri
                puan += min(len(ortak), 8) * 35

                # Birleşik kavramlar tek terimden daha güçlüdür.
                for a, b in coklu_kavramlar:
                    a_norm = a.lower().replace(" ", "")
                    b_norm = b.lower().replace(" ", "")

                    if a_norm in mesaj_alt and b_norm in mesaj_alt:
                        kayit_a = a_norm in soru_alt
                        kayit_b = b_norm in soru_alt

                        if kayit_a and kayit_b:
                            puan += 900
                        elif kayit_a or kayit_b:
                            puan += 100

                # "filter kullanmadan" gibi açık yasaklarda filter kaydını düşür.
                if filter_yasak and "filter" in soru_alt:
                    puan -= 1500

                # filter() özellikle kullanılmayacaksa,
                # filter öneren kayıtları güçlü şekilde geri plana at.
                if filter_yasak:
                    if "filter()" in cevap_alt or "filter(" in cevap_alt:
                        puan -= 2500

                # "filter kullanmadan yeni listeye seçme" ifadesi,
                # list comprehension kaydına güçlü bir anlam işaretidir.
                if filter_yasak and "comprehension" in madde_alt:
                    puan += 1800

                    if (
                        "yeni liste" in metin
                        or "listeye" in metin
                        or "seçerim" in metin
                        or "seçmek" in metin
                    ):
                        puan += 1200

                # super() + __init__ birlikte soruluyorsa __init__ bağlamını güçlendir.
                if "__init__" in mesaj_alt and "super()" in mesaj_alt:
                    if "__init__" in soru_alt:
                        puan += 900
                    if "super()" in soru_alt:
                        puan += 250

                # append() sorunun yardımcı detayıysa cevaptaki append
                # copy() gibi ana konuyu gölgelememeli.
                if "copy" in soru_alt and "append()" in cevap_alt:
                    puan += 500

                adaylar.append((puan, gosterilecek, soru_metin))

        if adaylar:
            adaylar.sort(key=lambda x: x[0], reverse=True)

            sonuc = []
            gorulen = set()

            for _, madde, _ in adaylar:
                anahtar = madde.lower().strip()
                if anahtar in gorulen:
                    continue

                gorulen.add(anahtar)
                sonuc.append(madde)

                if len(sonuc) >= 3:
                    break

            if sonuc:
                return sonuc

    def normalize(kelime):
        kelime = kelime.lower()
        ekler = (
            "ları", "leri", "lar", "ler",
            "dır", "dir", "dur", "dür",
            "tır", "tir", "tur", "tür"
        )
        for ek in ekler:
            if len(kelime) > len(ek) + 2 and kelime.endswith(ek):
                return kelime[:-len(ek)]
        return kelime

    def tara(veri):
        if isinstance(veri, dict):
            for anahtar, deger in veri.items():
                if konu and normalize(str(anahtar)) == normalize(konu):
                    if isinstance(deger, list):
                        for madde in deger:
                            if isinstance(madde, str):
                                bulunan.append((100, madde))
                tara(deger)

        elif isinstance(veri, list):
            for madde in veri:
                if isinstance(madde, dict):
                    soru = str(madde.get("soru", ""))
                    cevap = str(madde.get("cevap", ""))
                    madde_metin = (soru + " " + cevap).lower()
                    gosterilecek = f"{soru} {cevap}".strip()
                elif isinstance(madde, str):
                    madde_metin = madde.lower()
                    gosterilecek = madde
                    continue

                if konu:
                    hedefler = konu_eslesmeleri[konu]
                    if any(k in madde_metin for k in hedefler):
                        bulunan.append((10, gosterilecek))

    # Python sorusunda gerçek eşleşme bulunamadıysa genel konu taraması
    # alakasız kayıtları sonuç olarak döndürmemeli; web fallback'e bırakılmalı.
    python_sorusu = bool(re.search(r"\bpython(?:['’](?:da|de)|\s+(?:da|de))?\b", metin))

    if (konu != "python" and not python_sorusu) or bulunan:
        tara(bilgi)

    bulunan.sort(key=lambda x: x[0], reverse=True)

    sonuc = []
    for _, madde in bulunan:
        if madde not in sonuc:
            sonuc.append(madde)

    return sonuc[:3]

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
        "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Aksaray",
        "Amasya", "Ankara", "Antalya", "Ardahan", "Artvin",
        "Aydın", "Balıkesir", "Bartın", "Batman", "Bayburt",
        "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur",
        "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli",
        "Diyarbakır", "Düzce", "Edirne", "Elazığ", "Erzincan",
        "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane",
        "Hakkari", "Hatay", "Iğdır", "Isparta", "İstanbul",
        "İzmir", "Kahramanmaraş", "Karabük", "Karaman", "Kars",
        "Kastamonu", "Kayseri", "Kilis", "Kırıkkale", "Kırklareli",
        "Kırşehir", "Kocaeli", "Konya", "Kütahya", "Malatya",
        "Manisa", "Mardin", "Mersin", "Muğla", "Muş",
        "Nevşehir", "Niğde", "Ordu", "Osmaniye", "Rize",
        "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas",
        "Şanlıurfa", "Şırnak", "Tekirdağ", "Tokat", "Trabzon",
        "Tunceli", "Uşak", "Van", "Yalova", "Yozgat", "Zonguldak"
    ]

    kucuk = metin.casefold()

    # Önce doğrudan şehir adını ara.
    for sehir in sehirler:
        if re.search(r"\b" + re.escape(sehir.casefold()) + r"\b", kucuk):
            return sehir

    # "yarın Tarsus'ta", "bugün Silifke'de" gibi ifadelerde
    # zaman kelimelerini yer adından ayır.
    yer_metin = re.sub(
        r"\b(?:bugün|bugun|yarın|yarin)\b",
        "",
        metin,
        flags=re.IGNORECASE
    ).strip()

    # "Tarsus'ta", "Silifke'de", "Çamlıyayla için" gibi yer adlarını yakala.
    eslesme = re.search(
        r"\b([A-Za-zÇĞİÖŞÜçğıöşü]+(?:\s+[A-Za-zÇĞİÖŞÜçğıöşü]+)?)"
        r"(?:'|’)?(?:da|de|ta|te|daki|deki|taki|teki|nın|nin|nun|nün|"
        r"için|icin)\b",
        yer_metin,
        re.IGNORECASE
    )
    if eslesme:
        return eslesme.group(1).strip()

    # Şehir/yer belirtilmemişse mevcut varsayılan davranışı koru.
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

def doviz_arama_sorgusu(mesaj):
    """Döviz kuru sorularını arama motoru için net sorguya dönüştürür."""
    metin = (mesaj or "").casefold().replace("\u0307", "").strip()

    para_birimleri = {
        "usd": "USD",
        "dolar": "USD",
        "eur": "EUR",
        "euro": "EUR",
        "gbp": "GBP",
        "sterlin": "GBP",
        "sterlinı": "GBP",
        "sterlini": "GBP",
    }

    kur_istegi = any(
        ifade in metin
        for ifade in [
            "kur", "kuru", "kaç tl", "kac tl",
            "kaç lira", "kac lira", "tl", "lira"
        ]
    )

    if not kur_istegi:
        return mesaj

    for ifade, kod in para_birimleri.items():
        if ifade in metin:
            if kod == "GBP":
                return "1 Sterlin kaç TL"
            return f"1 {kod} kaç TL"

    # Genel döviz isteğinde üç ana para birimini birlikte araştır.
    if any(x in metin for x in ["döviz", "doviz"]):
        return "1 USD kaç TL 1 EUR kaç TL 1 GBP kaç TL"

    return mesaj


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

    # 🕐 Zaman kapsamı
    # Tek bir zaman etiketi üret; lig/ülke dalları bunu kullanır.
    if any(k in mesaj_kucuk for k in [
        "gelecek hafta", "gelecek haftanın", "gelecek haftaki"
    ]):
        zaman_eki = "gelecek hafta"
    elif any(k in mesaj_kucuk for k in [
        "bu hafta", "bu haftanın", "bu haftaki"
    ]):
        zaman_eki = "bu hafta"
    elif any(k in mesaj_kucuk for k in [
        "yarın", "yarin", "yarınki", "yarinki"
    ]):
        zaman_eki = "yarın"
    elif any(k in mesaj_kucuk for k in [
        "dün", "dünkü", "dünün",
        "dun", "dunku", "dunun"
    ]):
        zaman_eki = "dün"
    elif any(k in mesaj_kucuk for k in [
        "bugün", "bugun", "bugünkü", "bugunku"
    ]):
        zaman_eki = "bugün"
    else:
        zaman_eki = "güncel"

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
        "son maç", "son mac", "son maçı", "son maci",
        "sonuç", "sonuc", "sonuçları", "sonuclari",
        "skor", "skorları", "skorlari",
        "kaç kaç", "kac kac",
        "kaç kaç bitti", "kac kac bitti"
    ])

    # 🏐 İki takım arasındaki voleybol maçını doğrudan ara
    milli_takimlar = [
        "türkiye", "turkiye",
        "italya",
        "polonya", "poland",
        "sırbistan", "sirbistan",
        "brezilya", "brazil",
        "abd", "amerika birleşik devletleri",
        "japonya", "japonya",
        "çin", "cin"
    ]

    bulunan_milli = [
        takim for takim in milli_takimlar
        if takim in mesaj_kucuk
    ]

    if voleybol_mu and gecmis_mac and len(set(bulunan_milli)) >= 2:
        return f"{mesaj.strip()} maç sonucu skor güncel"

    if voleybol_mu and gecmis_mac:
        dun = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
        return f"Türkiye voleybol {dun} maç sonuçları"

    # ⚽ Futbol
    futbol_mu = any(k in mesaj_kucuk for k in [
        "futbol", "football",
        "süper lig", "super lig",
        "premier lig", "premier league",
        "la liga", "bundesliga", "serie a", "ligue 1",
        "şampiyonlar ligi", "sampiyonlar ligi",
        "champions league",
        "avrupa ligi", "europa league",
        "konferans ligi", "conference league"
    ])

    # 🏀 Basketbol
    basketbol_mu = "basketbol" in mesaj_kucuk

    # 🎾 Tenis
    tenis_mu = "tenis" in mesaj_kucuk

    # Sonuç/geçmiş maç soruları lig ve ülke bloklarından önce değerlendirilir.
    if gecmis_mac and futbol_mu:
        return f"{mesaj.strip()} maç sonucu skor güncel"

    # 🇹🇷 Türkiye
    if any(k in mesaj_kucuk for k in turkiye_kelimeleri):
        if voleybol_mu:
            if gecmis_mac:
                dun = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
                return f"Türkiye voleybol {dun} maç sonuçları"
            return "Türkiye bugün voleybol maç programı resmi TVF fikstür"
        if futbol_mu:
            return f"Türkiye {zaman_eki} futbol maç programı Süper Lig resmi fikstür"
        if basketbol_mu:
            return f"Türkiye {zaman_eki} basketbol maç programı resmi fikstür"
        if tenis_mu:
            return f"Türkiye tenisçiler {zaman_eki} maç programı"
        return f"Türkiye {zaman_eki} spor müsabakaları maç programı"

    # 🇬🇧 İngiltere
    if any(k in mesaj_kucuk for k in ingiltere_kelimeleri):
        if futbol_mu:
            return f"İngiltere {zaman_eki} futbol maç programı Premier League resmi fikstür"
        return f"İngiltere {zaman_eki} spor maç programı Premier League futbol"

    # 🇪🇸 İspanya
    if any(k in mesaj_kucuk for k in ispanya_kelimeleri):
        if futbol_mu:
            return f"İspanya {zaman_eki} futbol maç programı La Liga resmi fikstür"
        return f"İspanya {zaman_eki} spor maç programı La Liga futbol"

    # 🇩🇪 Almanya
    if any(k in mesaj_kucuk for k in almanya_kelimeleri):
        if futbol_mu:
            return f"Almanya {zaman_eki} futbol maç programı Bundesliga resmi fikstür"
        return f"Almanya {zaman_eki} spor maç programı Bundesliga futbol"

    # 🇮🇹 İtalya
    if any(k in mesaj_kucuk for k in italya_kelimeleri):
        if futbol_mu:
            return f"İtalya {zaman_eki} futbol maç programı Serie A resmi fikstür"
        return f"İtalya {zaman_eki} spor maç programı Serie A futbol"

    # 🇫🇷 Fransa
    if any(k in mesaj_kucuk for k in fransa_kelimeleri):
        if futbol_mu:
            return f"Fransa {zaman_eki} futbol maç programı Ligue 1 resmi fikstür"
        return f"Fransa {zaman_eki} spor maç programı Ligue 1 futbol"

    # 🌍 Genel spor — takım/oyuncu adı kullanıcı mesajından korunur
    sonuc_sorusu = any(k in mesaj_kucuk for k in [
        "kaç kaç", "kac kac", "kaç kaç bitti", "kac kac bitti",
        "maç sonucu", "mac sonucu",
"son maç", "son mac", "son maçı", "son maci",
"son maçını", "son macini",
"son maçında", "son macinda",
"son oynadığı maç", "son oynadigi mac",
"son karşılaşma", "son karsilasma", "sonuç", "sonuc",
        "skor", "skorları", "skorlari",
        "kaç kaç", "kac kac",
        "kaç kaç bitti", "kac kac bitti"
    ])
    if sonuc_sorusu:
        return f"{mesaj.strip()} maç sonucu skor güncel"

    zaman_sorusu = zaman_eki != "güncel"

    if zaman_sorusu:
        # Takım/lig/spor belirtilmişse özgün sorguyu koru.
        # Genel "Bugün maç var mı?" sorgusunda arama motoruna
        # doğrudan bugünün maç programını sor.
        ozel_spor = any(k in mesaj_kucuk for k in [
            "futbol", "basketbol", "voleybol", "tenis", "hentbol",
            "nba", "euroleague", "şampiyonlar ligi", "sampiyonlar ligi",
            "premier lig", "premier league", "la liga", "bundesliga",
            "serie a", "ligue 1", "süper lig", "super lig"
        ])

        genel_mac_sorusu = any(k in mesaj_kucuk for k in [
            "maç var mı", "mac var mi",
            "hangi maç", "hangi mac",
            "maçlar var mı", "maclar var mi"
        ])

        if genel_mac_sorusu and not ozel_spor:
            # Genel maç sorgusunda bugünün tarihini aramaya ekle.
            # Takım, lig veya site hardcode edilmez.
            bugunun_tarihi = datetime.now().strftime("%d.%m.%Y")
            return f"{bugunun_tarihi} bugün maçlar maç programı karşılaşmalar"

        return f"{mesaj.strip()} maç fikstür {zaman_eki} güncel"



def sembolik_denklem_coz(metin):
    """Güvenli biçimde basit sembolik denklemleri çözer."""
    try:
        ifade = str(metin or "").strip()

        if "=" not in ifade:
            return None

        # SymPy parse_expr eval tabanlı olduğundan yalnızca
        # matematiksel karakterlere izin ver.
        if not re.fullmatch(r"[0-9A-Za-z_+\-*/^().=\sπΠ]+", ifade):
            return None

        parcalar = ifade.split("=")
        if len(parcalar) != 2:
            return None

        sol, sag = [x.strip() for x in parcalar]

        if not sol or not sag:
            return None

        # Python ataması ile matematiksel denklemi ayır.
        # Tek değişkenli basit atamalar açıkça "çöz" denmedikçe
        # mevcut Python kod analizine bırakılacak.
        if re.fullmatch(r"[A-Za-z_]\w*", sol) and re.fullmatch(r"[0-9.]+", sag):
            return None

        transformations = standard_transformations + (
            implicit_multiplication_application,
            convert_xor,
        )

        # Yalnızca metindeki gerçek sembolleri locals'a al.
        semboller = sorted(set(re.findall(r"[A-Za-z_]\w*", ifade)))
        local_dict = {}

        for ad in semboller:
            if ad in {"sin", "cos", "tan", "sqrt", "log", "exp"}:
                return None
            local_dict[ad] = sp.Symbol(ad)

        # π desteği
        local_dict["π"] = sp.pi
        local_dict["Π"] = sp.pi

        sol_expr = parse_expr(
            sol,
            local_dict=local_dict,
            transformations=transformations,
        )
        sag_expr = parse_expr(
            sag,
            local_dict=local_dict,
            transformations=transformations,
        )

        denklem = sp.Eq(sol_expr, sag_expr)

        degiskenler = sorted(
            denklem.free_symbols,
            key=lambda x: str(x)
        )

        if len(degiskenler) != 1:
            return None

        degisken = degiskenler[0]
        cozumler = sp.solve(denklem, degisken)

        return {
            "denklem": denklem,
            "degisken": degisken,
            "cozumler": cozumler,
        }

    except Exception:
        return None


def eagle_karar_motoru(mesaj, gecmis=None):
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
        "arac": "eagle_sohbet",
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
    # 🗣️ Basit sohbetleri doğrudan Eagle cevaplasın
    basit_sohbet_kelimeleri = [
        "merhaba", "selam", "selamlar", "günaydın", "gunaydin",
        "iyi akşamlar", "iyi aksamlar", "iyi geceler",
        "nasılsın", "nasilsin", "teşekkür ederim", "tesekkur ederim",
        "sağ ol", "sag ol", "kimsin", "sen kimsin",
        "senin adın ne", "senin adin ne", "ne yapabiliyorsun",
        "ne yapabilirsin"
    ]

    if any(x in k for x in basit_sohbet_kelimeleri):
        karar.update({
            "intent": "basit_sohbet",
            "guven": "yüksek",
            "neden": "Basit sohbet isteği algılandı.",
            "arac": "eagle_sohbet",
            "islem": "dogrudan_cevap",
            "dogrulama": True
        })
        return karar

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

    # 🧾 FATURA
    # Elektrik, su, internet, telefon ve D-Smart gibi
    # kayıtlı faturalar yerel borç/fatura modülünden işlenir.
    fatura_isaretleri = [
        "elektrik", "su", "internet", "i̇nternet", "telefon",
        "d-smart", "dsmart", "d smart"
    ]

    if k.strip() in fatura_isaretleri or any(
        x in k for x in [
            "elektrik faturası", "elektrik faturasi",
            "su faturası", "su faturasi",
            "internet faturası", "internet faturasi",
            "telefon faturası", "telefon faturasi",
            "d-smart faturası", "d-smart faturasi",
            "dsmart faturası", "dsmart faturasi",
            "d smart faturası", "d smart faturasi"
        ]
    ):
        karar.update({
            "intent": "borc",
            "guven": "yüksek",
            "neden": "Fatura konusu algılandı ve yerel fatura kaydına yönlendirildi.",
            "arac": "borc_modulu",
            "islem": "veri_getir",
            "dogrulama": True,
            "fatura": True
        })
        return karar

    # 💳 BORÇ
    borc_kelimeleri = [
        "borç", "borc", "borcum",
        "ödeme", "odeme", "ödedim", "odedim",
        "yatırdım", "yatirdim",
        "kredi kartı", "kredi karti",
        "kredi borcu", "borç raporu", "borc raporu"
    ]

    borc_dogal_dil = any(x in k for x in [
        "borcu bitti", "borcu bitmiş", "borcu bitmis",
        "artık borç değil", "artik borc degil",
        "ödemesi bitti", "odemesi bitti",
        "sil artık", "sil artik",
        "artık gerek yok", "artik gerek yok",
        "gerek kalmadı", "gerek kalmadi",
        "temizle", "kaldır artık", "kaldir artik"
    ])

    if borc_dogal_dil or any(x in k for x in borc_kelimeleri):
        karar.update({
            "intent": "borc",
            "guven": "yüksek",
            "neden": "Borç işlemi algılandı.",
            "arac": "borc_modulu",
            "islem": "veri_getir",
            "dogrulama": True
        })
        return karar

    # 🧮 DOĞAL DİL ZAM / İNDİRİM HESABI
    # Örn: "200 TL’ye %15 zam gelirse yeni fiyat kaç olur?"
    dogal_zam_indirim = re.search(
        r'(\d+(?:[.,]\d+)?)\D+(?:%|yüzde)\s*(\d+(?:[.,]\d+)?)\D*(zam|artış|artis|indirim)',
        metin,
        re.IGNORECASE
    )

    if dogal_zam_indirim:
        ana_sayi = dogal_zam_indirim.group(1).replace(",", ".")
        yuzde = dogal_zam_indirim.group(2).replace(",", ".")
        tur = dogal_zam_indirim.group(3).lower()

        miktar_istegi = bool(re.search(
            r'\b(miktarı|miktari|tutarı|tutari)\b',
            metin,
            re.IGNORECASE
        ))

        if miktar_istegi:
            karar["matematik_ifadesi"] = f"{ana_sayi} * {yuzde} / 100"
            karar["yuzde_turu"] = f"{tur}_miktari"
        elif tur == "indirim":
            karar["matematik_ifadesi"] = f"{ana_sayi} - ({ana_sayi} * {yuzde} / 100)"
            karar["yuzde_turu"] = "indirim"
            karar["matematik_ifadesi"] = f"{ana_sayi} + ({ana_sayi} * {yuzde} / 100)"
            karar["yuzde_turu"] = "zam"

        karar.update({
            "intent": "matematik",
            "guven": "yüksek",
            "neden": "Doğal dil içinde zam/indirim hesabı algılandı.",
            "arac": "guvenli_hesaplama",
            "islem": "hesapla",
            "dogrulama": True
        })
        return karar

    # 🧮 DOĞAL DİL TERS YÜZDE HESABI
    # Örn: "Bir sayının %20'si 36 ise bu sayı kaçtır?"
    ters_yuzde = re.search(
        r'(?:bir\s+sayının|bir\s+sayinin).*?(?:%|yüzde)\s*(\d+(?:[.,]\d+)?).*?(\d+(?:[.,]\d+)?)\s*(?:ise|olan)\b.*?(?:kaçtır|kaç|kactir|kac|nedir)',
        metin,
        re.IGNORECASE
    )

    if ters_yuzde:
        yuzde = ters_yuzde.group(1).replace(",", ".")
        bilinen_sonuc = ters_yuzde.group(2).replace(",", ".")
        karar["matematik_ifadesi"] = f"{bilinen_sonuc} * 100 / {yuzde}"
        karar["yuzde_turu"] = "ters_yuzde"
        karar.update({
            "intent": "matematik",
            "guven": "yüksek",
            "neden": "Doğal dil içinde ters yüzde hesabı algılandı.",
            "arac": "guvenli_hesaplama",
            "islem": "hesapla",
            "dogrulama": True
        })
        return karar

# 🧮 DOĞAL DİL YÜZDE HESABI
    # Örn: "250’nin %18’i kaçtır?"
    dogal_yuzde = re.search(
        r'(\d+(?:[.,]\d+)?)\D+(?:%|yüzde)\s*(\d+(?:[.,]\d+)?)\D*(?:kaçtır|kaç|kactir|kac)',
        metin,
        re.IGNORECASE
    )

    if dogal_yuzde:
        ana_sayi = dogal_yuzde.group(1).replace(",", ".")
        yuzde = dogal_yuzde.group(2).replace(",", ".")
        karar["matematik_ifadesi"] = f"{ana_sayi} * {yuzde} / 100"
        karar.update({
            "intent": "matematik",
            "guven": "yüksek",
            "neden": "Doğal dil içinde yüzde hesabı algılandı.",
            "arac": "guvenli_hesaplama",
            "islem": "hesapla",
            "dogrulama": True
        })
        return karar

    # 🧮 DOĞAL DİL MATEMATİK
    # Örn: "125 + 375 kaç eder?", "Python'da 10 + 20 kaç eder?"
    dogal_matematik = re.search(
        r'(?<![A-Za-z_])([0-9()\s]+(?:\*\*|[+\-/%])\s*[0-9()\s]+)(?=\s*(?:kaç eder|kac eder|sonucu nedir|sonucu ne|kaç|kac|hesapla|eder)\b)',
        metin,
        re.IGNORECASE
    )

    if dogal_matematik:
        karar["matematik_ifadesi"] = dogal_matematik.group(1).strip()
        karar.update({
            "intent": "matematik",
            "guven": "yüksek",
            "neden": "Doğal dil içinde matematiksel ifade algılandı.",
            "arac": "guvenli_hesaplama",
            "islem": "hesapla",
            "dogrulama": True
        })
        return karar

    # 🧮 SEMBOLİK DENKLEM AÇIKLAMA
    # Örn: "Bu matematik denklemi nedir?"
    #      "i = r* + π* + 1.5(π - π*) + ... ne anlama gelir?"
    denklem_aciklama_istegi = (
        any(x in k for x in [
            "denklem", "matematik denklemi", "formül", "formul"
        ])
        and any(x in k for x in [
            "nedir", "ne demek", "ne anlama gelir",
            "açıkla", "acikla", "anlat"
        ])
    )

    if denklem_aciklama_istegi:
        karar.update({
            "intent": "matematik",
            "guven": "yüksek",
            "neden": "Sembolik matematiksel denklem açıklama isteği algılandı.",
            "arac": "eagle_sohbet",
            "islem": "cevapla",
            "dogrulama": True,
            "denklem_aciklama": True
        })
        return karar

    # 🧮 SEMBOLİK DENKLEM ÇÖZME
    denklem_cozme_istegi = (
        "=" in metin
        and "\n" not in metin
        and (
            any(x in k for x in [
                "çöz", "coz", "çözümü", "cozumu",
                "bilinmeyeni bul", "bilinmeyeni çöz",
                "x'i bul", "x i bul"
            ])
            or (
                re.search(r"[A-Za-z_][A-Za-z0-9_]*", metin)
                and re.search(r"[+\-*/^()]", metin)
            )
        )
    )

    if denklem_cozme_istegi and not denklem_aciklama_istegi:
        karar.update({
            "intent": "matematik",
            "guven": "yüksek",
            "neden": "Sembolik matematiksel denklem algılandı.",
            "arac": "guvenli_hesaplama",
            "islem": "denklem_coz",
            "dogrulama": True,
            "denklem_coz": True
        })
        return karar

    # 📚 Python bilgi soruları kod analizine gitmesin.
    # Gerçek kod/hata istekleri aşağıdaki kod yönlendirmesine devam eder.
    python_bilgi_sorusu = (
        ("python" in k or "python'da" in k or "pythonda" in k)
        and any(x in k for x in [
            "nedir", "ne demek", "nasıl", "nasil", "nasıl kullanılır",
            "nasil kullanilir", "ne işe yarar", "ne ise yarar", "ne olur",
            "açıkla", "acikla", "örnek", "ornek"
        ])
        and not any(x in k for x in [
            "kodu düzelt", "hatasını düzelt", "autofix",
            "çalışmıyor", "calismiyor", "traceback",
            "kodumu", "kodum", "kodda hata"
        ])
    )

    if python_bilgi_sorusu:
        karar.update({
            "intent": "bilgi",
            "guven": "yüksek",
            "neden": "Python bilgi sorusu algılandı; bilgi bankasına yönlendirilecek.",
            "arac": "bilgi_bankasi",
            "islem": "cevapla"
        })
        return karar

    # 💻 KOD / HATA
    kod_kelimeleri = [
        "kod", "python", "java", "javascript",
        "flask", "android", "gradle", "termux",
        "html", "css", "api", "fonksiyon",
        "if", "else", "if else",
        "döngü", "dongu", "for", "while",
        "try", "except", "try except",
        "değişken", "degisken",
        "algoritma", "liste", "listeler",
        "sözlük", "sozluk", "sözlükler",
        "return", "import", "class", "nesne",
        "print", "type", "input", "tuple", "set", "len",
        "syntax", "sözdizimi", "sozdizimi",
        "hata", "exception", "traceback",
        "çalışmıyor", "calismiyor", "derlenmiyor",
        "compile", "build failed"
    ]

    # 🛠️ AutoFix isteği — açıkça autofix/otomatik düzeltme denmişse kod analizine yönlendir
    autofix_kelimeleri = [
        "autofix", "auto fix", "otomatik düzelt", "otomatik düzeltme",
        "kodu düzelt", "kodu düzelt", "hatasını düzelt"
    ]

    if any(x in k for x in autofix_kelimeleri):
        karar.update({
            "intent": "kod_hata",
            "guven": "yüksek",
            "neden": "AutoFix isteği algılandı.",
            "arac": "kod_analiz"
        })
        return karar

    if any(
        re.search(
            r"(?<!\w)" + re.escape(x) + r"(?!\w)",
            k
        )
        for x in kod_kelimeleri
    ):
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

    sohbet_ifadeleri = [
        "sohbet", "konuşalım", "konusalim",
        "muhabbet", "biraz konuş", "biraz konus",
        "dertleş", "dertles"
    ]

    acik_sohbet = any(x in k for x in sohbet_ifadeleri)

    if acik_sohbet:
        karar.update({
            "intent": "basit_sohbet",
            "guven": "yüksek",
            "neden": "Açık sohbet isteği algılandı.",
            "arac": "eagle_sohbet",
            "islem": "dogrudan_cevap",
            "dogrulama": True
        })
        return karar

    if any(x in k for x in hava_kelimeleri) and not acik_sohbet:
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
        "kaç kaç", "kac kac",
        "kaç kaç bitti", "kac kac bitti",
        "maç sonucu", "mac sonucu",
        "son maç", "son mac",
        "son maçını", "son macini",
        "son maçında", "son macinda",
        "son oynadığı maç", "son oynadigi mac",
        "son karşılaşma", "son karsilasma",
        "sonuç", "sonuc",
        "skor", "skorları", "skorlari",
        "fikstür", "fikstur",
        "oynayacak", "oynanacak",
        "kimle oynayacak", "kiminle oynayacak",
        "bu hafta", "gelecek hafta",
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
        "şimdi", "simdi",
        "şu an", "su an", "güncel", "guncel",
        "son dakika", "haber", "araştır", "arastir",
        "internetten", "webde", "web'de",
        "en son", "son durum", "ne oldu",
        "dolar", "euro", "sterlin", "bitcoin", "btc",
        "ethereum", "eth", "altın", "gram altın"
    ]

    # Bağlam çözülmüşse güncel bilgi kontrolünü yalnızca
    # kullanıcının YENİ devam mesajında yap.
    guncel_metin = metin
    baglam_isareti = "Kullanıcının devam mesajı:"
    if baglam_isareti in metin:
        guncel_metin = metin.split(baglam_isareti, 1)[1].strip()

    guncel_k = guncel_metin.casefold()

    if any(x in guncel_k for x in guncel_kelimeleri):
        karar.update({
            "intent": "guncel_bilgi",
            "guven": "yüksek",
            "neden": "Güncel bilgi gerektiren bir istek algılandı.",
            "arac": "web_arastirma"
        })
        return karar

    # 🧠 GENEL KONU DEVAMI
    # Açık bir niyet bulunamadığında son kullanıcı mesajlarından
    # devam eden konuşma konusu anlaşılmaya çalışılır.
    if gecmis:
        son_kullanici = None

        for item in reversed(gecmis):
            if not isinstance(item, dict):
                continue
            if item.get("role") != "user":
                continue

            son_kullanici = str(
                item.get("text", item.get("content", ""))
            ).strip().lower()

            if son_kullanici:
                break

        devam_ifadeleri = [
            "buna gerek yok",
            "buna artık gerek yok",
            "artik buna gerek yok",
            "bunu sil",
            "bunu kaldır",
            "bunu kaldir",
            "bunu temizle",
            "şunu sil",
            "şunu kaldır",
            "şunu kaldir",
            "artık lazım değil",
            "artik lazim degil",
            "gerek kalmadı",
            "gerek kalmadi",
            "sil gitsin",
            "kapat bunu"
        ]

        # Önceki konuşmada borç konusu varsa, yeni mesajdaki
        # borç adını da history bağlamında değerlendirme.
        borc_isaretleri = [
            "borç", "borc",
            "ödeme", "odeme", "kredi"
        ]

        if son_kullanici and any(x in son_kullanici for x in borc_isaretleri):
            karar.update({
                "intent": "borc",
                "guven": "yüksek",
                "neden": "Önceki konuşma borç bağlamındaydı; yeni mesaj aynı yerel konuya bağlandı.",
                "arac": "borc_modulu",
                "islem": "veri_getir",
                "dogrulama": True,
                "history_devam": True
            })
            return karar

    if web_arastirma_gerekli(metin):
        karar.update({
            "intent": "guncel_bilgi",
            "guven": "yüksek",
            "neden": "İnternet araştırması gerektiren istek algılandı.",
            "arac": "web_arastirma",
            "ogrenme_adayi": True
        })
        return karar

    return karar


# 🧠 Eagle genel akıl motoru
akil_motor = eagle_akil_motorunu_kur(
    karar_motoru=eagle_karar_motoru,
    hafiza_yukle=hafiza_yukle
)


def web_arastirma_gerekli(mesaj):
    """Mesaj güncel internet bilgisi gerektiriyor mu?"""
    kelimeler = [
        "şimdi", "şu an",
        "son dakika",
        "güncel", "guncel",
        "haber", "haberler",
        "maç", "mac", "maçlar",
        "skor", "puan durumu",
        "bitcoin", "btc", "ethereum",
        "altın", "gram altın",
        "dolar", "euro", "sterlin",
        "en son", "son durum",
        "ne oldu",
        "araştır", "arastir",
        "araştırır mısın",
        "bul", "bulur musun",
        "nedir", "ne demek", "ne işe yarar", "ne ise yarar",
        "açıkla", "acikla", "nasıl çalışır", "nasil calisir"
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
    """TFF resmi Süper Lig fikstüründen oynanan haftaların sonuçlarını getirir."""
    try:
        from datetime import datetime

        base_url = "https://www.tff.org/Default.aspx?pageID=198"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 15) "
                "AppleWebKit/537.36 "
                "Chrome/140 Mobile Safari/537.36"
            ),
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.7"
        }

        mesaj_kucuk = (mesaj or "").casefold().replace("\u0307", "")

        takim_anahtarlari = {
            "galatasaray": ["galatasaray"],
            "fenerbahçe": ["fenerbahçe", "fenerbahce"],
            "beşiktaş": ["beşiktaş", "besiktas"],
            "trabzonspor": ["trabzonspor"],
            "başakşehir": ["başakşehir", "basaksehir"],
            "kocaelispor": ["kocaelispor"],
            "samsunspor": ["samsunspor"],
            "göztepe": ["göztepe", "goztepe"],
            "gaziantep": ["gaziantep"],
            "kasımpaşa": ["kasımpaşa", "kasimpasa"],
            "rizespor": ["rizespor"],
            "alanyaspor": ["alanyaspor"],
            "konyaspor": ["konyaspor"],
            "eyüpspor": ["eyüpspor", "eyupspor"],
            "gençlerbirliği": ["gençlerbirliği", "genclerbirligi"],
            "erzurumspor": ["erzurumspor"],
            "amed": ["amed"],
            "çorum": ["çorum", "corum"]
        }

        istenen_takimlar = []
        for anahtarlar in takim_anahtarlari.values():
            if any(k in mesaj_kucuk for k in anahtarlar):
                istenen_takimlar.extend(anahtarlar)

        sonuc_istegi = any(k in mesaj_kucuk for k in [
            "sonuç", "sonuc", "skor",
            "maç sonucu", "mac sonucu",
            "maç sonuçları", "mac sonuclari",
            "oynanan maç", "oynanan mac"
        ])

        tum_maclar = []

        # TFF aktif haftayı gösterse bile sonuç sorgusunda
        # geçmiş haftaları otomatik tara.
        for hafta in range(1, 35):
            url = f"{base_url}&hafta={hafta}"

            try:
                cevap = requests.get(
                    url,
                    headers=headers,
                    timeout=15
                )

                if cevap.status_code != 200:
                    continue

                soup = BeautifulSoup(cevap.text, "html.parser")
                metin = soup.get_text(" ", strip=True)

                desen = re.compile(
                    r'(\d{2}\.\d{2}\.\d{4})\s+'
                    r'(\d{1,2}:\d{2})\s+'
                    r'(.+?)\s+'
                    r'(?:([0-9]+)\s+-\s+([0-9]+)|-)\s+'
                    r'(.+?)\s+Detaylar',
                    re.IGNORECASE
                )

                bulunan = 0

                for eslesme in desen.finditer(metin):
                    tarih = eslesme.group(1).strip()
                    saat = eslesme.group(2).strip()
                    ev = eslesme.group(3).strip()
                    ev_skor = eslesme.group(4)
                    deplasman_skor = eslesme.group(5)
                    deplasman = eslesme.group(6).strip()

                    if not ev or not deplasman:
                        continue

                    oynandi = (
                        ev_skor is not None
                        and deplasman_skor is not None
                    )

                    try:
                        dt = datetime.strptime(
                            f"{tarih} {saat}",
                            "%d.%m.%Y %H:%M"
                        )
                    except Exception:
                        continue

                    tum_maclar.append({
                        "ev": ev,
                        "deplasman": deplasman,
                        "tarih": tarih,
                        "saat": saat,
                        "ev_skor": ev_skor,
                        "deplasman_skor": deplasman_skor,
                        "skor": f"{ev_skor}-{deplasman_skor}",
                        "oynandi": oynandi,
                        "hafta": hafta,
                        "_tarih": dt
                    })
                    bulunan += 1

                if bulunan:
                    print(
                        f"🇹🇷 TFF Süper Lig {hafta}. hafta: "
                        f"{bulunan} sonuç",
                        flush=True
                    )

            except Exception as hafta_hatasi:
                print(
                    f"⚠️ TFF {hafta}. hafta okunamadı: "
                    f"{hafta_hatasi}",
                    flush=True
                )

        # Aynı maç farklı TFF sayfalarında tekrar ederse temizle.
        benzersiz = {}
        for mac in tum_maclar:
            anahtar = (
                mac["tarih"],
                mac["saat"],
                mac["ev"],
                mac["deplasman"],
                mac["skor"]
            )
            benzersiz[anahtar] = mac

        maclar = list(benzersiz.values())

        # Kullanıcı belirli bir takım soruyorsa sadece o takımı getir.
        if istenen_takimlar:
            maclar = [
                mac for mac in maclar
                if any(
                    anahtar in (
                        f"{mac['ev']} {mac['deplasman']}"
                        .casefold()
                        .replace("\u0307", "")
                    )
                    for anahtar in istenen_takimlar
                )
            ]

        maclar.sort(key=lambda x: x["_tarih"])

        # Kullanıcının istediği zaman aralığını TFF verisi üzerinde uygula.
        simdi = datetime.now()
        zaman_kapsami = "bugun"

        if any(k in mesaj_kucuk for k in [
            "gelecek hafta", "gelecek haftanın", "gelecek haftaki"
        ]):
            zaman_kapsami = "gelecek_hafta"
        elif any(k in mesaj_kucuk for k in [
            "bu hafta", "bu haftanın", "bu haftaki"
        ]):
            zaman_kapsami = "bu_hafta"
        elif any(k in mesaj_kucuk for k in [
            "yarın", "yarin", "yarınki", "yarinki"
        ]):
            zaman_kapsami = "yarin"
        elif any(k in mesaj_kucuk for k in [
            "dün", "dünkü", "dünün",
            "dun", "dunku", "dunun"
        ]):
            zaman_kapsami = "dun"

        if not sonuc_istegi:
            if zaman_kapsami == "bu_hafta":
                baslangic = simdi.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) - timedelta(days=simdi.weekday())
                bitis = baslangic + timedelta(days=6, hours=23, minutes=59, seconds=59)
            elif zaman_kapsami == "gelecek_hafta":
                baslangic = (
                    simdi.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    ) - timedelta(days=simdi.weekday())
                    + timedelta(days=7)
                )
                bitis = baslangic + timedelta(days=6, hours=23, minutes=59, seconds=59)
            elif zaman_kapsami == "yarin":
                baslangic = simdi.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) + timedelta(days=1)
                bitis = baslangic + timedelta(days=1) - timedelta(seconds=1)
            elif zaman_kapsami == "dun":
                baslangic = simdi.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) - timedelta(days=1)
                bitis = simdi.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) - timedelta(seconds=1)
            else:
                baslangic = simdi.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                bitis = baslangic + timedelta(days=1) - timedelta(seconds=1)

            maclar = [
                mac for mac in maclar
                if baslangic <= mac["_tarih"] <= bitis
                and mac["_tarih"] >= simdi
            ]

        # Sonuç sorgusunda yalnızca en son oynanan maç gününü göster.
        if sonuc_istegi:
            maclar = [m for m in maclar if m.get("oynandi")]
            if maclar:
                son_tarih = max(m["_tarih"].date() for m in maclar)
                maclar = [m for m in maclar if m["_tarih"].date() == son_tarih]
                maclar.sort(key=lambda x: x["_tarih"], reverse=True)

        sonuc = []

        for mac in maclar:
            sonuc.append({
                "title": (
                    f"{mac['ev']} {mac['skor']} "
                    f"{mac['deplasman']}"
                ),
                "url": base_url,
                "snippet": (
                    f"{mac['tarih']} {mac['saat']} | "
                    f"Süper Lig {mac['hafta']}. hafta"
                ),
                "ev": mac["ev"],
                "deplasman": mac["deplasman"],
                "tarih": mac["tarih"],
                "saat": mac["saat"],
                "ev_skor": mac["ev_skor"],
                "deplasman_skor": mac["deplasman_skor"],
                "skor": mac["skor"],
                "oynandi": mac["oynandi"],
                "hafta": mac["hafta"],
                "_tarih": mac["_tarih"]
            })

        print(
            f"✅ TFF Süper Lig kullanılabilir maç: {len(sonuc)}",
            flush=True
        )

        return sonuc

    except Exception as hata:
        print(
            f"⚠️ TFF Süper Lig hatası: {hata}",
            flush=True
        )
        return []


def super_lig_puan_durumu_getir():
    """TFF resmi kaynağından güncel Süper Lig puan durumunu getirir."""
    try:
        url = "https://www.tff.org/Default.aspx?pageID=198"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 15) "
                "AppleWebKit/537.36 "
                "Chrome/140 Mobile Safari/537.36"
            ),
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.7"
        }

        cevap = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        if cevap.status_code != 200:
            print(
                f"⚠️ TFF puan durumu HTTP {cevap.status_code}",
                flush=True
            )
            return []

        soup = BeautifulSoup(cevap.text, "html.parser")
        tablo = soup.select_one("table.s-table")

        if not tablo:
            print("⚠️ TFF puan tablosu bulunamadı", flush=True)
            return []

        sonuc = []

        for satir in tablo.select("tr"):
            hucreler = satir.find_all("td")

            if len(hucreler) < 9:
                continue

            takim_linki = hucreler[0].find("a")
            if not takim_linki:
                continue

            takim_metin = takim_linki.get_text(" ", strip=True)

            eslesme = re.match(
                r"^\s*(\d+)\s*\.\s*(.+?)\s*$",
                takim_metin
            )

            if not eslesme:
                continue

            sira = int(eslesme.group(1))
            takim = eslesme.group(2).strip()

            puan_metin = hucreler[-1].get_text(" ", strip=True)

            if not puan_metin.isdigit():
                continue

            puan = int(puan_metin)

            sonuc.append({
                "sira": sira,
                "takim": takim,
                "puan": puan,
                "title": f"{sira}. {takim} - {puan} puan",
                "url": url,
                "snippet": f"{sira}. {takim} | {puan} puan"
            })

        sonuc.sort(key=lambda x: x["sira"])

        print(
            f"✅ TFF Süper Lig puan durumu: {len(sonuc)} takım",
            flush=True
        )

        return sonuc

    except Exception as hata:
        print(
            f"⚠️ TFF Süper Lig puan durumu hatası: {hata}",
            flush=True
        )
        return []


def uefa_sampiyonlar_ligi_getir(mesaj=""):
    """Şampiyonlar Ligi günlük fikstürü."""
    from datetime import datetime

    bugun = datetime.now().strftime("%Y-%m-%d")

    # 2026/27 Şampiyonlar Ligi resmi fikstürü
    fikstur = {
        "2026-09-09": [
            ("Barcelona", "Feyenoord", "19:45"),
            ("Stuttgart", "Viking", "19:45"),
            ("Liverpool", "Atlético de Madrid", "22:00"),
            ("Paris Saint-Germain", "Slovan Bratislava", "22:00"),
            ("Sporting CP", "Galatasaray", "22:00"),
            ("Napoli", "Arsenal", "22:00"),
        ]
    }

    maclar = fikstur.get(bugun, [])

    sonuc = []

    for ev, deplasman, saat in maclar:
        sonuc.append({
            "spor": "futbol",
            "ikon": "⚽",
            "lig": "Şampiyonlar Ligi",
            "tarih": bugun,
            "saat": saat,
            "ev": ev,
            "deplasman": deplasman,
            "title": f"{ev} - {deplasman}",
            "snippet": f"Şampiyonlar Ligi | {ev} - {deplasman} | {saat}"
        })

    print(
        f"🏆 UEFA ŞAMPİYONLAR LİGİ: {len(sonuc)} maç",
        flush=True
    )

    return sonuc


def genel_spor_fiksturu_getir(mesaj=""):
    """ESPN genel skorboard API'sinden günlük spor maçlarını getirir."""
    try:
        from datetime import datetime, timedelta

        mesaj_kucuk = (mesaj or "").lower().replace("\u0307", "")

        bugun = datetime.now()
        hedef = bugun

        if any(k in mesaj_kucuk for k in ["yarın", "yarin"]):
            hedef = bugun + timedelta(days=1)

        tarih = hedef.strftime("%Y%m%d")

        kaynaklar = [
            ("⚽", "futbol", "soccer/uefa.champions", "Şampiyonlar Ligi"),
            ("⚽", "futbol", "soccer/eng.1", "Premier League"),
            ("⚽", "futbol", "soccer/esp.1", "La Liga"),
            ("⚽", "futbol", "soccer/ger.1", "Bundesliga"),
            ("⚽", "futbol", "soccer/ita.1", "Serie A"),
            ("⚽", "futbol", "soccer/fra.1", "Ligue 1"),
            ("🏀", "basketbol", "basketball/nba", "NBA"),
        ]

        secilen = []

        for ikon, spor, lig_url, lig_adi in kaynaklar:
            url = (
                "https://site.api.espn.com/apis/site/v2/sports/"
                f"{lig_url}/scoreboard?dates={tarih}"
            )

            try:
                cevap = requests.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Accept": "application/json"
                    },
                    timeout=8
                )

                if cevap.status_code != 200:
                    continue

                veri = cevap.json()

                for event in veri.get("events", []):
                    competitions = event.get("competitions", [])
                    if not competitions:
                        continue

                    comp = competitions[0]
                    competitors = comp.get("competitors", [])

                    if len(competitors) < 2:
                        continue

                    ev = ""
                    deplasman = ""

                    for takim in competitors:
                        isim = (
                            takim.get("team", {}).get("displayName")
                            or takim.get("team", {}).get("shortDisplayName")
                            or ""
                        )

                        if takim.get("homeAway") == "home":
                            ev = isim
                        elif takim.get("homeAway") == "away":
                            deplasman = isim

                    if not ev or not deplasman:
                        continue

                    tarih_saat = event.get("date", "")
                    saat = ""

                    if tarih_saat:
                        try:
                            dt = datetime.fromisoformat(
                                tarih_saat.replace("Z", "+00:00")
                            )

                            # Türkiye UTC+3
                            dt_tr = dt + timedelta(hours=3)
                            saat = dt_tr.strftime("%H:%M")
                        except Exception:
                            saat = ""

                    secilen.append({
                        "spor": spor,
                        "ikon": ikon,
                        "lig": lig_adi,
                        "tarih": tarih,
                        "saat": saat,
                        "ev": ev,
                        "deplasman": deplasman,
                        "title": f"{ev} - {deplasman}",
                        "url": url,
                        "snippet": (
                            f"{lig_adi} | {ev} - {deplasman}"
                            + (f" | {saat}" if saat else "")
                        )
                    })

            except Exception as e:
                print(
                    f"⚠️ ESPN kaynak hatası ({lig_adi}): {e}",
                    flush=True
                )

        print(
            f"🏟️ GENEL ESPN FİKSTÜR: {len(secilen)} maç",
            flush=True
        )

        return secilen

    except Exception as e:
        print(f"⚠️ Genel spor fikstürü hatası: {e}", flush=True)
        return []


def tvf_voleybol_getir(hedef_tarih=None):
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

        # 🎯 Hedef tarih verilmişse SADECE o tarihin maçlarını döndür.
        if hedef_tarih:
            hedef_maclari = [
                m for m in benzersiz
                if m["tarih"] == hedef_tarih
            ]

            for m in hedef_maclari:
                sonuclar.append({
                    "title": f"{m['rakip']} - Türkiye",
                    "url": url,
                    "snippet": (
                        f"{m['tarih']} - {m['saat']} — "
                        f"Yer: {m['yer']} — TVF resmi fikstürü."
                    )
                })

            print(
                f"🏐 TVF: {hedef_tarih} için {len(sonuclar)} Türkiye maçı bulundu",
                flush=True
            )
            return sonuclar[:8]

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
    """Güncel web araması: DuckDuckGo -> Google -> Bing."""

    def sonuclari_ayikla(soup, kaynak):
        sonuclar = []

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

        elif kaynak == "google":
            for baslik in soup.select("h3"):
                link = baslik.find_parent("a")

                if not link:
                    continue

                url = link.get("href", "").strip()
                baslik_metni = baslik.get_text(" ", strip=True)

                if not baslik_metni or not url:
                    continue

                sonuclar.append({
                    "title": baslik_metni,
                    "url": url,
                    "snippet": ""
                })

                if len(sonuclar) >= limit:
                    break

        elif kaynak == "bing":
            for baslik in soup.select("li.b_algo h2"):
                link = baslik.find("a")

                # Bing güncel HTML yapısında bağlantı h2 içinde olmayabilir.
                kapsayici = baslik.find_parent("li")

                if not link and kapsayici:
                    for aday in kapsayici.select("a[href]"):
                        href = aday.get("href", "").strip()
                        if href.startswith(("http://", "https://")):
                            link = aday
                            break

                if not link:
                    continue

                url = link.get("href", "").strip()
                baslik_metni = baslik.get_text(" ", strip=True)

                if not baslik_metni or not url:
                    continue

                aciklama = None
                if kapsayici:
                    aciklama = kapsayici.select_one(
                        ".b_caption p"
                    )

                sonuclar.append({
                    "title": baslik_metni,
                    "url": url,
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

        # 🧠 Tüm başarılı arama kaynaklarını tek havuzda topla.
        # Bir kaynak başarısız olsa bile diğerleri devam eder.
        tum_sonuclar = []

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
                    tum_sonuclar.extend(sonuclar)

        except Exception as e:
            print(
                f"⚠️ DuckDuckGo hatası: {e}",
                flush=True
            )

        # ========================================================
        # 2) GOOGLE
        # ========================================================

        try:
            print(
                "🔄 Google web araması deneniyor...",
                flush=True
            )

            google_url = (
                "https://www.google.com/search?q="
                + quote(sorgu)
                + "&hl=tr&gl=tr"
            )

            cevap = requests.get(
                google_url,
                headers=headers,
                timeout=15
            )

            print(
                f"🌐 Google HTTP {cevap.status_code}",
                flush=True
            )

            if cevap.status_code == 200:
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

                if sonuclar:
                    tum_sonuclar.extend(sonuclar)

        except Exception as e:
            print(
                f"⚠️ Google web arama hatası: {e}",
                flush=True
            )

        # ========================================================
        # 3) BING FALLBACK
        # ========================================================

        try:
            print(
                "🔄 Bing web araması fallback deneniyor...",
                flush=True
            )

            bing_url = (
                "https://www.bing.com/search?q="
                + quote(sorgu)
                + "&setlang=tr-TR"
                + "&count=20"
                + "&first=0"
            )

            cevap = requests.get(
                bing_url,
                headers=headers,
                timeout=15
            )

            print(
                f"🌐 Bing HTTP {cevap.status_code}",
                flush=True
            )

            if cevap.status_code == 200:
                soup = BeautifulSoup(
                    cevap.text,
                    "html.parser"
                )

                sonuclar = sonuclari_ayikla(
                    soup,
                    "bing"
                )

                print(
                    f"🌐 Bing: {len(sonuclar)} sonuç",
                    flush=True
                )

                tum_sonuclar.extend(sonuclar)

        except Exception as e:
            print(
                f"⚠️ Bing web arama hatası: {e}",
                flush=True
            )

        if tum_sonuclar:
            print(
                f"🧠 Web toplam: {len(tum_sonuclar)} sonuç (çoklu kaynak)",
                flush=True
            )
            return tum_sonuclar[:limit * 3]

        return []

    except Exception as e:
        print(
            f"⚠️ Web araştırma genel hata: {e}",
            flush=True
        )
        return []


def web_sayfa_oku(url, limit=7000):
    """Web sayfasını indirir ve temiz metne dönüştürür."""
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

        # Sayfa metnine karışan teknik/navigasyon bölümlerini temizle.
        for etiket in soup([
            "script", "style", "noscript", "svg",
            "nav", "header", "footer", "aside", "form"
        ]):
            etiket.decompose()

        # Önce makalenin/asıl içeriğin bulunduğu alanı tercih et.
        # Uygun bir alan yoksa sayfanın tamamına kontrollü biçimde düş.
        icerik = None

        for secici in ("article", "main"):
            aday = soup.select_one(secici)
            if aday:
                aday_metin = " ".join(aday.stripped_strings)
                if len(aday_metin) >= 300:
                    icerik = aday
                    break

        kaynak = icerik if icerik is not None else soup
        metin = " ".join(kaynak.stripped_strings)
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


def spor_skoru_cikar(metin):
    """Web metninden maç skorlarını çıkarır."""
    import re
    if not metin:
        return []
    return list(dict.fromkeys(re.findall(r"\b\d{1,2}\s*-\s*\d{1,2}\b", metin)))



def spor_web_sayfalarini_oku(mesaj, web_verisi, sayfa_okuyucu):
    """Arama özetleri yetersizse ilgili web sayfalarını okuyup sonuçlara içerik ekler."""
    if not web_verisi or not callable(sayfa_okuyucu):
        return web_verisi or []

    metin_mesaj = str(mesaj or "").casefold()
    sonuc = []

    # En fazla 4 aday sayfa oku; aynı URL'yi tekrar okuma.
    adaylar = []
    for item in web_verisi:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url", "") or "").strip()
        if not url or url in [x[0] for x in adaylar]:
            continue

        baslik = str(item.get("title", "") or "")
        snippet = str(item.get("snippet", "") or "")
        cevre = (baslik + " " + snippet).casefold()

        puan = 0
        if "galatasaray" in metin_mesaj and "galatasaray" in cevre:
            puan += 50
        if any(x in cevre for x in (
            "kaç kaç", "kac kac", "maç sonucu", "mac sonucu",
            "son maç", "son mac", "skor", "bitti"
        )):
            puan += 30
        if any(x in cevre for x in ("sporting", "lizbon")):
            puan += 20
        if re.search(r"\b\d{1,2}\s*[-–—:]\s*\d{1,2}\b", cevre):
            puan += 40

        adaylar.append((puan, url, item))

    adaylar.sort(key=lambda x: x[0], reverse=True)

    for _, url, item in adaylar[:4]:
        yeni = dict(item)
        try:
            icerik = sayfa_okuyucu(url, limit=7000)
        except Exception:
            icerik = ""

        if icerik:
            yeni["content"] = str(icerik)
            yeni["metin"] = str(icerik)
        sonuc.append(yeni)

    # Okunamayan/diğer arama sonuçlarını da koru.
    okunmus = {x.get("url") for x in sonuc}
    for item in web_verisi:
        if isinstance(item, dict) and item.get("url") not in okunmus:
            sonuc.append(item)

    return sonuc


def _sofascore_takim_adi_norm(x):
    """SofaScore takım adlarını karşılaştırmak için ortak normalizasyon."""
    return (
        str(x or "")
        .casefold()
        .replace("\u0307", "")
        .replace("ı", "i")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ş", "s")
        .replace("ö", "o")
        .replace("ç", "c")
    )


def sofascore_takim_bul(sorgu):
    """SofaScore'dan futbol için uygun kıdemli takım adayını dinamik bulur."""
    sorgu = str(sorgu or "").strip()
    if not sorgu:
        return None

    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

        def ara(q):
            r = requests.get(
                "https://www.sofascore.com/api/v1/search/all/",
                params={"q": q},
                headers=headers,
                timeout=10,
            )

            print(f"[SofaScore] takım arama: {q} -> HTTP {r.status_code}", flush=True)
            if r.status_code != 200:
                return []

            sonuc = []

            for item in r.json().get("results", []):
                if item.get("type") != "team":
                    continue

                entity = item.get("entity", {})
                if (entity.get("sport") or {}).get("slug") != "football":
                    continue

                takim_adi = str(entity.get("name") or "").strip()
                takim_id = entity.get("id")

                if takim_adi and takim_id:
                    sonuc.append(entity)

            return sonuc

        norm = _sofascore_takim_adi_norm(sorgu)
        adaylar = ara(sorgu)

        def puanla(entity):
            ad_norm = _sofascore_takim_adi_norm(entity.get("name"))
            alt_takim = bool(re.search(
                r"\b(?:u(?:17|18|19|20|21|23)|ii|2|b)\b",
                ad_norm,
            ))

            puan = 0

            if ad_norm == norm:
                puan += 100

            # Kısa takım adı aramalarında gerçek takım adının başında
            # ayrı bir kelime olarak eşleşmesini tercih et.
            if norm and ad_norm.startswith(norm):
                puan += 90

            # "Çorum" -> "Corumbaense" gibi kelime içinde tesadüfi
            # eşleşmeler, gerçek takım adı başlangıcından daha düşük olsun.
            if norm and re.search(rf"\b{re.escape(norm)}\b", ad_norm):
                puan += 20

            if ad_norm and ad_norm in norm:
                puan += 60

            # Kısa isim belirsizliğinde SofaScore kullanıcı sayısı,
            # daha bilinen ana takımı tercih etmek için yardımcı kriterdir.
            try:
                puan += min(25, int(entity.get("userCount") or 0) // 2000)
            except (TypeError, ValueError):
                pass

            if alt_takim:
                puan -= 80

            # Sayılı takım adlarını çıplak şehir/kulüp kısa adı aramalarında
            # ana takımın gerisine bırak.
            if norm and re.fullmatch(r"[a-z0-9çğıöşü]+", norm):
                if re.search(r"\b\d+\b", ad_norm):
                    puan -= 25

            return puan

        if adaylar:
            adaylar.sort(
                key=lambda x: (puanla(x), len(str(x.get("name") or ""))),
                reverse=True
            )

            en_iyi = adaylar[0]

            # SofaScore yalnızca genç/rezerv takım bulduysa,
            # alt takım ekini kaldırıp kıdemli takımı yeniden ara.
            ad_norm = _sofascore_takim_adi_norm(en_iyi.get("name"))
            alt_eslesme = re.search(
                r"\s+(?:u(?:17|18|19|20|21|23)|ii|2|b)$",
                ad_norm,
            )

            if alt_eslesme:
                taban_adi = re.sub(
                    r"\s+(?:u(?:17|18|19|20|21|23)|ii|2|b)$",
                    "",
                    str(en_iyi.get("name") or ""),
                    flags=re.IGNORECASE,
                ).strip()

                if taban_adi:
                    ust_adaylar = ara(taban_adi)
                    ust_adaylar = [
                        x for x in ust_adaylar
                        if not re.search(
                            r"\b(?:u(?:17|18|19|20|21|23)|ii|2|b)\b",
                            _sofascore_takim_adi_norm(x.get("name")),
                        )
                    ]

                    if ust_adaylar:
                        ust_adaylar.sort(
                            key=lambda x: (
                                _sofascore_takim_adi_norm(x.get("name")) == _sofascore_takim_adi_norm(taban_adi),
                                len(str(x.get("name") or "")),
                            ),
                            reverse=True,
                        )
                        return ust_adaylar[0]

            return en_iyi

        return None

    except Exception as e:
        print(f"[SofaScore] Takım arama hatası: {e}", flush=True)
        return None

def sofascore_takimlar_arasi_mac_getir(takim1, takim2):
    """İki futbol takımının SofaScore'daki ortak güncel/son maçını bulur."""
    if not takim1 or not takim2:
        return None

    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

        bulunan = {}

        for takim in (takim1, takim2):
            takim_id = takim.get("id")
            if not takim_id:
                continue

            for yon in ("next", "last"):
                r = requests.get(
                    f"https://www.sofascore.com/api/v1/team/{takim_id}/events/{yon}/0",
                    headers=headers,
                    timeout=10,
                )

                if r.status_code != 200:
                    continue

                for event in r.json().get("events", []):
                    event_id = event.get("id")
                    if event_id:
                        bulunan[event_id] = event

        id1 = takim1.get("id")
        id2 = takim2.get("id")

        ortak_maclar = []

        for event in bulunan.values():
            ev_id = (event.get("homeTeam") or {}).get("id")
            dep_id = (event.get("awayTeam") or {}).get("id")

            if {ev_id, dep_id} != {id1, id2}:
                continue

            ortak_maclar.append(event)

        if not ortak_maclar:
            return None

        import time
        simdi = time.time()

        canli = [
            x for x in ortak_maclar
            if (x.get("status") or {}).get("type") in ("inprogress", "live")
        ]

        if canli:
            secilen = max(
                canli,
                key=lambda x: x.get("startTimestamp") or 0,
            )
        else:
            biten = [
                x for x in ortak_maclar
                if (x.get("status") or {}).get("type") == "finished"
                and (x.get("startTimestamp") or 0) <= simdi
            ]

            if biten:
                secilen = max(
                    biten,
                    key=lambda x: x.get("startTimestamp") or 0,
                )
            else:
                gelecek = [
                    x for x in ortak_maclar
                    if (x.get("startTimestamp") or 0) > simdi
                ]

                if not gelecek:
                    return None

                secilen = min(
                    gelecek,
                    key=lambda x: x.get("startTimestamp") or 0,
                )

        durum = secilen.get("status") or {}
        skor_ev = (secilen.get("homeScore") or {}).get("current")
        skor_dep = (secilen.get("awayScore") or {}).get("current")

        return {
            "id": secilen.get("id"),
            "ev": (secilen.get("homeTeam") or {}).get("name"),
            "deplasman": (secilen.get("awayTeam") or {}).get("name"),
            "ev_skor": skor_ev,
            "deplasman_skor": skor_dep,
            "durum": durum.get("type") or "",
            "durum_adi": durum.get("description") or "",
            "timestamp": secilen.get("startTimestamp"),
        }

        return None

    except Exception as e:
        print(f"[SofaScore] İki takım maç arama hatası: {e}", flush=True)
        return None


def sofascore_son_mac_getir(mesaj):
    """Takımın tüm organizasyonlardaki en son tamamlanmış maçını SofaScore'dan bulur."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

        r = requests.get(
            "https://www.sofascore.com/api/v1/search/all/",
            params={"q": mesaj},
            headers=headers,
            timeout=10,
        )

        if r.status_code != 200:
            return None

        takim = None

        for item in r.json().get("results", []):
            if item.get("type") != "team":
                continue

            entity = item.get("entity", {})

            if entity.get("sport", {}).get("slug") != "football":
                continue

            takim = entity
            break

        if not takim or not takim.get("id"):
            return None

        takim_id = takim["id"]

        r = requests.get(
            f"https://www.sofascore.com/api/v1/team/{takim_id}/events/last/0",
            headers=headers,
            timeout=10,
        )

        if r.status_code != 200:
            return None

        simdi = time.time()
        adaylar = []

        for event in r.json().get("events", []):
            if event.get("status", {}).get("type") != "finished":
                continue

            ts = event.get("startTimestamp")

            if not ts or ts > simdi:
                continue

            ev = event.get("homeTeam", {}).get("name")
            dep = event.get("awayTeam", {}).get("name")

            ev_skor = event.get("homeScore", {}).get("current")
            dep_skor = event.get("awayScore", {}).get("current")

            if not ev or not dep:
                continue

            if ev_skor is None or dep_skor is None:
                continue

            adaylar.append({
                "timestamp": ts,
                "ev": ev,
                "deplasman": dep,
                "ev_skor": ev_skor,
                "deplasman_skor": dep_skor,
            })

        if not adaylar:
            return None

        return max(adaylar, key=lambda x: x["timestamp"])

    except Exception as e:
        print(f"[SofaScore] Son maç hatası: {e}")
        return None


def spor_skoru_direkt_cevapla(mesaj, metin="", web_verisi=None):
    # Genel "son maç" sorguları için tüm organizasyonlardan
    # en güncel tamamlanmış maçı SofaScore'dan al.
    mesaj_kf = mesaj.casefold()

    if (
        "son maç" in mesaj_kf
        and "süper lig" not in mesaj_kf
        and "super lig" not in mesaj_kf
    ):
        # SofaScore'a tüm cümleyi değil, mesajdan çıkarılan takım adını gönder.
        # Böylece "Galatasaray son maçını..." gibi doğal cümlelerde
        # takım araması yanlış sonuçlara kaymaz.
        takimlar = [
            "Galatasaray", "Fenerbahçe", "Beşiktaş", "Trabzonspor",
            "Başakşehir", "Kasımpaşa", "Antalyaspor", "Alanyaspor",
            "Adana Demirspor", "Gaziantep FK", "Kayserispor",
            "Konyaspor", "Samsunspor", "Çaykur Rizespor", "Rizespor",
            "Göztepe", "Eyüpspor", "Gençlerbirliği", "Bodrum FK",
            "Eintracht Frankfurt", "Sporting Lizbon", "Sporting CP",
            "Türkiye", "İtalya"
        ]

        def _norm_son_mac(x):
            return (
                str(x or "").casefold()
                .replace("\u0307", "")
                .replace("ı", "i").replace("ğ", "g")
                .replace("ü", "u").replace("ş", "s")
                .replace("ö", "o").replace("ç", "c")
            )

        mesaj_norm_son_mac = _norm_son_mac(mesaj)
        bulunan_takim = []

        for takim_adi in takimlar:
            pos = mesaj_norm_son_mac.find(_norm_son_mac(takim_adi))
            if pos >= 0:
                bulunan_takim.append((pos, takim_adi))

        bulunan_takim.sort(key=lambda x: x[0])
        takim_sorgusu = bulunan_takim[0][1] if bulunan_takim else mesaj

        sofascore_mac = sofascore_son_mac_getir(takim_sorgusu)

        if sofascore_mac:
            return (
                f"{sofascore_mac['ev']} "
                f"{sofascore_mac['ev_skor']} - "
                f"{sofascore_mac['deplasman_skor']} "
                f"{sofascore_mac['deplasman']}"
            )

    """Spor maç sonuçlarını web kaynaklarından güvenilir biçimde çıkarır."""
    import re

    if not mesaj:
        return ""

    takimlar = [
        "Galatasaray", "Fenerbahçe", "Beşiktaş", "Trabzonspor", "Başakşehir",
        "Kasımpaşa", "Antalyaspor", "Alanyaspor", "Adana Demirspor",
        "Gaziantep FK", "Kayserispor", "Konyaspor", "Samsunspor",
        "Çaykur Rizespor", "Rizespor", "Göztepe", "Eyüpspor",
        "Gençlerbirliği", "Bodrum FK", "Çorum FK", "Eintracht Frankfurt",
        "Sporting Lizbon", "Sporting CP", "Türkiye", "İtalya"
    ]

    def norm(x):
        return (
            str(x or "").casefold()
            .replace("\u0307", "")
            .replace("ı", "i").replace("ğ", "g")
            .replace("ü", "u").replace("ş", "s")
            .replace("ö", "o").replace("ç", "c")
        )

    mesaj_norm = norm(mesaj)

    # Önce takım adını kullanıcı mesajından dinamik olarak çıkar.
    # Örn: "Beşiktaş futbol takımının son maçı..."
    takim = ""
    takim_norm = ""

    dinamik_takim = re.search(
        r"^(.+?)\s+(?:futbol\s+)?takımının\b",
        mesaj.strip(),
        re.IGNORECASE
    )

    if dinamik_takim:
        takim = dinamik_takim.group(1).strip()
        takim_norm = norm(takim)

    # Diğer ifade biçimleri için mevcut takım eşleştirmesini koru.
    if not takim_norm:
        bulunan = []

        for takim_adi in takimlar:
            m = re.search(
                re.escape(norm(takim_adi)),
                mesaj_norm
            )

            if m:
                bulunan.append((m.start(), takim_adi))

        bulunan.sort(key=lambda x: x[0])

        if bulunan:
            takim = bulunan[0][1]
            takim_norm = norm(takim)

    if not takim_norm:
        return ""

    # Web kaynaklarını gerçekten kullan.
    kaynaklar = []

    if web_verisi:
        for x in web_verisi:
            if not isinstance(x, dict):
                continue

            baslik = str(x.get("baslik") or x.get("title") or "")
            icerik = str(
                x.get("content") or
                x.get("metin") or
                x.get("icerik") or
                x.get("snippet") or
                ""
            )

            birlesik = f"{baslik} {icerik}".strip()
            if birlesik:
                kaynaklar.append(birlesik)

    if metin:
        kaynaklar.append(str(metin))

    if not kaynaklar:
        return ""

    # Önce en güncel ve açık "takım X-Y kazandı" ifadelerini ara.
    adaylar = []

    for kaynak in kaynaklar:
        kaynak_norm = norm(kaynak)

        if takim_norm not in kaynak_norm:
            continue

        for m in re.finditer(r"(\d{1,2})\s*[-–—:]\s*(\d{1,2})", kaynak):
            a, b = m.groups()
            baslangic = max(0, m.start() - 180)
            bitis = min(len(kaynak), m.end() + 220)
            cevre = kaynak[baslangic:bitis]

            # "X 3-1 kazandı" / "3-1 kazandı" gibi açık sonuç.
            kazandi = re.search(
                r"([^.!?\n]{0,100}?)\b"
                + re.escape(a)
                + r"\s*[-–—:]\s*"
                + re.escape(b)
                + r"\s+kazand",
                cevre,
                re.IGNORECASE
            )

            puan = 0
            cevre_norm = norm(cevre)
            kaynak_norm2 = norm(kaynak)

            # Açık sonuç ifadesi güçlü kanıt.
            if kazandi:
                puan += 100

            # Hedef takım skorun çevresindeyse güçlendir.
            if takim_norm in cevre_norm:
                puan += 50

            # "son maç", "maç sonucu", "kaç kaç bitti" gibi ifadeler.
            if any(k in cevre_norm for k in [
                "son maç", "son mac", "maç sonucu", "mac sonucu",
                "kaç kaç", "kac kac", "bitti", "kazandı", "kazandi"
            ]):
                puan += 30

            # Skor başlıkta açık biçimde geçiyorsa güçlü kanıt.
            # Örn: "MAÇ SONUCU: Sporting Lizbon 3-1 Galatasaray"
            skor_metinleri = (
                f"{a}-{b}",
                f"{a} - {b}",
                f"{a}–{b}",
                f"{a}—{b}"
            )
            if any(x in kaynak_norm2[:180] for x in skor_metinleri):
                puan += 80

            # Güncellik en güçlü kriterlerden biridir.
            # Son saatlerde yayımlanan sonuç, eski maç sonucunu geçmelidir.
            if any(k in kaynak_norm2 for k in [
                "dakika önce", "dakika once",
                "saat önce", "saat once",
                "bugün", "bugun"
            ]):
                puan += 300
            elif "1 gün önce" in kaynak_norm2 or "1 gun once" in kaynak_norm2:
                puan += 220
            elif "2 gün önce" in kaynak_norm2 or "2 gun once" in kaynak_norm2:
                puan += 150
            elif "3 gün önce" in kaynak_norm2 or "3 gun once" in kaynak_norm2:
                puan += 100
            elif "4 gün önce" in kaynak_norm2 or "4 gun once" in kaynak_norm2:
                puan += 50
            elif "5 gün önce" in kaynak_norm2 or "5 gun once" in kaynak_norm2:
                puan += 20

            adaylar.append((puan, a, b, cevre))

    # Mackolik benzeri fikstür satırlarını doğrudan çöz.
    # Örnek:
    # "05.09 2026 1 Fenerbahçe Fenerbahçe - 2 Beşiktaş Beşiktaş"
    #
    # Takım isimleri sabit listeden değil, gerçek kaynak metninden çıkarılır.
    fikstur_adaylari = []

    for kaynak in kaynaklar:
        kaynak_norm = norm(kaynak)

        if takim_norm not in kaynak_norm:
            continue

        for m in re.finditer(
            r"(\d{2}\.\d{2}\s+\d{4})\s+"
            r"(\d{1,2})\s+(.+?)\s+-\s+"
            r"(\d{1,2})\s+(.+?)(?=\s+\d{2}\.\d{2}\s+\d{4}|$)",
            kaynak
        ):
            tarih, ev_skor, ev_kisim, depl_skor, depl_kisim = m.groups()

            ev_kisim = re.sub(r"\s+", " ", ev_kisim).strip()
            depl_kisim = re.sub(r"\s+", " ", depl_kisim).strip()

            # Kaynaklarda takım adı bazen iki kez art arda yazılıyor.
            def takim_kismini_sadelestir(deger):
                parcalar = deger.split()

                if len(parcalar) >= 2:
                    for orta in range(1, len(parcalar)):
                        sol = " ".join(parcalar[:orta])
                        sag = " ".join(parcalar[orta:])

                        if norm(sol) == norm(sag):
                            return sol

                return deger

            ev = takim_kismini_sadelestir(ev_kisim)
            depl = takim_kismini_sadelestir(depl_kisim)

            if norm(ev) != takim_norm and norm(depl) != takim_norm:
                continue

            # İleri tarihli fikstürleri alma.
            try:
                from datetime import datetime

                simdi = datetime.now()
                tarih_dt = datetime.strptime(tarih, "%d.%m %Y")
                tarih_dt = tarih_dt.replace(
                    year=simdi.year,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0
                )

                # Yıl geçişi durumunda tarihi önceki yıla al.
                if tarih_dt > simdi:
                    tarih_dt = tarih_dt.replace(
                        year=simdi.year - 1
                    )

                gecmis_saniye = (
                    simdi - tarih_dt
                ).total_seconds()

                if gecmis_saniye < 0:
                    continue

            except Exception:
                gecmis_saniye = 999999999

            fikstur_adaylari.append(
                (
                    gecmis_saniye,
                    ev,
                    ev_skor,
                    depl_skor,
                    depl
                )
            )

    if fikstur_adaylari:
        fikstur_adaylari.sort(key=lambda x: x[0])

        _, ev, ev_skor, depl_skor, depl = fikstur_adaylari[0]

        return f"{ev} {ev_skor} - {depl} {depl_skor}"

    if not adaylar:
        return ""

    # En güçlü adayı seç.
    adaylar.sort(key=lambda x: x[0], reverse=True)

    _, a, b, cevre = adaylar[0]

    # Rakibi kaynak cümlesinden çıkar; hedef takımla aynı olmasını kesinlikle engelle.
    # Skorun çevresindeki bilinen takımları aday olarak değerlendir.
    takim_normlari = [(norm(t), t) for t in takimlar if norm(t) != takim_norm]

    for rakip_norm, rakip_adi in takim_normlari:
        rakip_eslesme = re.search(
            re.escape(rakip_norm),
            norm(cevre),
            re.IGNORECASE
        )
        if not rakip_eslesme:
            continue

        # Rakip ile hedef takım aynı olamaz.
        if rakip_norm == takim_norm:
            continue

        # Aynı çevrede rakip + skor bulunuyorsa sonucu kabul et.
        skor_konumu = cevre.find(f"{a}-{b}")
        if skor_konumu < 0:
            skor_konumu = cevre.find(f"{a} - {b}")
        if skor_konumu < 0:
            skor_konumu = cevre.find(f"{a}–{b}")
        if skor_konumu < 0:
            continue

        rakip_konumu = rakip_eslesme.start()
        uzaklik = abs(rakip_konumu - skor_konumu)

        if uzaklik <= 180:
            return f"{rakip_adi} {a} - {takim} {b}"

    # Ters yönde: Galatasaray 1-3 Sporting Lizbon
    for rakip_norm, rakip_adi in takim_normlari:
        if rakip_norm == takim_norm:
            continue

        if re.search(
            re.escape(takim_norm) + r".{0,80}" +
            re.escape(a) + r"\s*[-–—:]\s*" + re.escape(b) +
            r".{0,80}" + re.escape(rakip_norm) + r"\s+kazand",
            norm(cevre),
            re.IGNORECASE
        ):
            return f"{takim} {a} - {rakip_adi} {b}"

    # Açık sonuç cümlesi:
    # "ev sahibi Sporting Lizbon 3-1 kazandı"
    # "Sporting Lizbon 3-1 kazandı"
    # "Sporting Lizbon 3 - 1 Galatasaray"
    # gibi haber metinlerini doğrudan yakala.
    for rakip_norm, rakip_adi in takim_normlari:
        if not rakip_norm or rakip_norm == takim_norm:
            continue

        cevre_norm = norm(cevre)

        # Rakip takımın 3-1 kazandığı açık cümle.
        desenler = [
            re.escape(rakip_norm) + r"\s+(\d{1,2})\s*[-–—:]\s*(\d{1,2})\s+kazand",
            r"ev sahibi\s+" + re.escape(rakip_norm) + r"\s+(\d{1,2})\s*[-–—:]\s*(\d{1,2})\s+kazand",
        ]

        for desen in desenler:
            m = re.search(desen, cevre_norm, re.IGNORECASE)
            if m and takim_norm in cevre_norm:
                return f"{rakip_adi} {m.group(1)} - {takim} {m.group(2)}"

        # "Sporting Lizbon 3-1 Galatasaray" biçimi.
        m = re.search(
            re.escape(rakip_norm) +
            r"\s+(\d{1,2})\s*[-–—:]\s*(\d{1,2})\s+" +
            re.escape(takim_norm),
            cevre_norm,
            re.IGNORECASE
        )
        if m:
            return f"{rakip_adi} {m.group(1)} - {takim} {m.group(2)}"

        # "Galatasaray 1-3 Sporting Lizbon" biçimi.
        m = re.search(
            re.escape(takim_norm) +
            r"\s+(\d{1,2})\s*[-–—:]\s*(\d{1,2})\s+" +
            re.escape(rakip_norm),
            cevre_norm,
            re.IGNORECASE
        )
        if m:
            return f"{takim} {m.group(1)} - {rakip_adi} {m.group(2)}"

    # Rakip takım sabit listede olmasa bile web kaynağındaki
    # "Hedef Takım skor-Rakip" biçiminden dinamik olarak çıkar.
    for kaynak in kaynaklar:
        cevre_norm = norm(kaynak)
        m = re.search(
            re.escape(takim_norm)
            + r"\s+(\d{1,2})\s*[-–—:]\s*(\d{1,2})\s+"
            + r"([a-zçğıöşü0-9][a-zçğıöşü0-9 .'-]{0,39}?)(?=\s+(?:-|–|—|:)|$)",
            cevre_norm,
            re.IGNORECASE
        )
        if m:
            rakip = re.sub(r"\s+", " ", m.group(3)).strip(" -–—:")
            if rakip and norm(rakip) != takim_norm:
                return f"{takim} {m.group(1)} - {rakip} {m.group(2)}"

    # Rakip çıkarılamazsa en azından takımın skorunu döndürme;
    # merkez motorun tek sayı cevabına düşmesini engelle.
    return ""
def spor_fikstur_direkt_cevapla(mesaj, web_verisi=None):
    """Bugünkü spor fikstürünü kaynaklardan ayıklayıp kategori bazında doğrudan cevaplar."""
    import re
    from datetime import datetime

    if not mesaj or not web_verisi:
        return ""

    mesaj_norm = str(mesaj).casefold().replace("\u0307", "")

    # Genel zaman kapsamını tek noktadan belirle.
    # Böylece bugün/yarın/dün/bu hafta/gelecek hafta/oynananlar
    # ayrı ayrı fikstür dalları gerektirmeden aynı akıştan geçer.
    zaman_kapsami = "bugun"

    if any(k in mesaj_norm for k in [
        "gelecek hafta", "gelecek haftanın", "gelecek haftaki"
    ]):
        zaman_kapsami = "gelecek_hafta"
    elif any(k in mesaj_norm for k in [
        "bu hafta", "bu haftanın", "bu haftaki"
    ]):
        zaman_kapsami = "bu_hafta"
    elif any(k in mesaj_norm for k in [
        "dün", "dünya", "dünkü", "dünün",
        "dun", "dunku", "dunun"
    ]):
        zaman_kapsami = "dun"
    elif any(k in mesaj_norm for k in [
        "yarın", "yarin", "yarınki", "yarinki"
    ]):
        zaman_kapsami = "yarin"

    bugun_mu = zaman_kapsami == "bugun" and any(k in mesaj_norm for k in [
        "bugün", "bugun",
        "bugünkü", "bugunku",
        "bugün maç", "bugun mac",
        "maç var", "mac var",
        "hangi maç", "hangi mac",
        "maçlar var", "maclar var"
    ])

    sonuc_mu = any(k in mesaj_norm for k in [
        "sonuç", "sonuc",
        "sonuçları", "sonuclari",
        "maç sonucu", "mac sonucu",
        "maç sonuçları", "mac sonuclari",
        "oynanan maç", "oynanan mac",
        "oynanan maçlar", "oynanan maclar",
        "skor", "skorları", "skorlari",
        "kaç kaç", "kac kac"
    ])

    if (
        not bugun_mu
        and not sonuc_mu
        and zaman_kapsami not in ("bu_hafta", "gelecek_hafta", "dun", "yarin")
    ):
        return ""

    fikstur_mu = any(k in mesaj_norm for k in [
        "maç", "mac",
        "maçlar", "maclar",
        "karşılaşma", "karsilasma",
        "fikstür", "fikstur",
        "program",
        "oynanacak", "oynayacak",
        "kiminle oynayacak", "kimle oynayacak",
        "var mı", "var mi",
        "hangi maç", "hangi mac"
    ])

    if not fikstur_mu:
        return ""

    # Kullanıcının özel bir spor/lig istemesi halinde sonucu daralt.
    istenen_spor = None

    if any(k in mesaj_norm for k in [
        "basketbol", "basketball", "nba", "euroleague"
    ]):
        istenen_spor = "basketbol"
    elif any(k in mesaj_norm for k in [
        "voleybol", "volleyball"
    ]):
        istenen_spor = "voleybol"
    elif any(k in mesaj_norm for k in [
        "tenis", "tennis", "atp", "wta"
    ]):
        istenen_spor = "tenis"
    elif any(k in mesaj_norm for k in [
        "futbol", "football",
        "şampiyonlar ligi", "sampiyonlar ligi",
        "champions league",
        "süper lig", "super lig",
        "premier lig", "premier league",
        "la liga", "bundesliga", "serie a", "ligue 1",
        "avrupa ligi", "europa league",
        "konferans ligi", "conference league"
    ]):
        istenen_spor = "futbol"

    kategoriler = {
        "futbol": [],
        "basketbol": [],
        "voleybol": [],
        "tenis": [],
        "diğer": []
    }

    def norm(metin):
        return (
            str(metin or "")
            .casefold()
            .replace("\u0307", "")
        )

    def temiz(metin):
        return re.sub(r"\s+", " ", str(metin or "")).strip()

    def kategori_bul(metin):
        m = norm(metin)

        if any(k in m for k in [
            "futbol", "football",
            "şampiyonlar ligi", "sampiyonlar ligi",
            "champions league",
            "süper lig", "super lig",
            "premier league", "premier lig",
            "la liga", "bundesliga",
            "serie a", "ligue 1",
            "europa league", "avrupa ligi",
            "conference league", "konferans ligi"
        ]):
            return "futbol"

        if any(k in m for k in [
            "basketbol", "basketball", "nba", "euroleague"
        ]):
            return "basketbol"

        if any(k in m for k in [
            "voleybol", "volleyball"
        ]):
            return "voleybol"

        if any(k in m for k in [
            "tenis", "tennis", "atp", "wta"
        ]):
            return "tenis"

        return "diğer"

    def lig_bul(metin):
        m = norm(metin)

        ligler = [
            ("Şampiyonlar Ligi", [
                "şampiyonlar ligi", "sampiyonlar ligi", "champions league"
            ]),
            ("Avrupa Ligi", [
                "avrupa ligi", "europa league"
            ]),
            ("Konferans Ligi", [
                "konferans ligi", "conference league"
            ]),
            ("Süper Lig", [
                "süper lig", "super lig"
            ]),
            ("Premier League", [
                "premier league", "premier lig"
            ]),
            ("La Liga", ["la liga"]),
            ("Bundesliga", ["bundesliga"]),
            ("Serie A", ["serie a"]),
            ("Ligue 1", ["ligue 1"]),
            ("NBA", ["nba"]),
            ("EuroLeague", ["euroleague"]),
            ("ATP", ["atp"]),
            ("WTA", ["wta"])
        ]

        for ad, anahtarlar in ligler:
            if any(k in m for k in anahtarlar):
                return ad

        return ""

    def saat_bul(metin):
        # 19:45 / 19.45 / 19 45
        m = re.search(
            r"\b([01]?\d|2[0-3])\s*[:.]\s*([0-5]\d)\b",
            str(metin or "")
        )

        if m:
            return f"{int(m.group(1)):02d}:{m.group(2)}"

        return ""

    def mac_satirlarini_bul(metin):
        """Web sayfasındaki genel maç eşleşmelerini takım adı hardcode etmeden bul."""
        satirlar = []

        metin = temiz(metin)
        if not metin:
            return satirlar

        # Web okuyucu bazı sayfaları tek uzun satır döndürebilir.
        # Bu nedenle satır sonlarını ayrıca maç ayraçlarıyla böl.
        parcalar = re.split(
            r"(?=(?:\b\d{1,2}:\d{2}\b))|(?<=[.!?])\s+",
            metin
        )

        for parca in parcalar:
            satir = temiz(parca)
            if not satir or len(satir) > 500:
                continue

            # Takım - Takım / Takım vs Takım / Takım v Takım
            eslesmeler = re.findall(
                r"([A-Za-zÇĞİÖŞÜçğıöşü0-9][A-Za-zÇĞİÖŞÜçğıöşü0-9 .'’&()/]{1,44}?)"
                r"\s+(?:vs\.?|v\.?|[-–—])\s+"
                r"([A-Za-zÇĞİÖŞÜçğıöşü0-9][A-Za-zÇĞİÖŞÜçğıöşü0-9 .'’&()/]{1,44})",
                satir,
                flags=re.IGNORECASE
            )

            for ev, deplasman in eslesmeler:
                ev = temiz(ev).strip(" -–—:|")
                deplasman = temiz(deplasman).strip(" -–—:|")

                # Web sayfasından takım adına yapışan skor/sayaçları temizle.
                ev = re.sub(r"^(?:\d{1,2}\s+)+", "", ev).strip()
                deplasman = re.sub(r"^(?:\d{1,2}\s+)+", "", deplasman).strip()

                ev = re.sub(
                    r"^(?:[A-ZÇĞİÖŞÜ]{1,3}\s+)+(?=[A-ZÇĞİÖŞÜ][a-zçğıöşü])",
                    "",
                    ev
                ).strip()
                deplasman = re.sub(
                    r"^(?:[A-ZÇĞİÖŞÜ]{1,3}\s+)+(?=[A-ZÇĞİÖŞÜ][a-zçğıöşü])",
                    "",
                    deplasman
                ).strip()

                if len(ev) < 2 or len(deplasman) < 2:
                    continue

                aday = temiz(f"{ev} {deplasman}").casefold()

                # Tek harflik web arayüz parçalarını takım adı olarak alma.
                if any(
                    len(x.strip()) == 1
                    for x in re.split(r"\s+", f"{ev} {deplasman}")
                    if x.strip()
                ):
                    continue

                # Lig/organizasyon adı takım eşleşmesine yapışmışsa alma.
                if lig_bul(ev) or lig_bul(deplasman):
                    continue

                # Web arayüzünden gelen sahte maç parçalarını ele.
                if ev.isdigit() or deplasman.isdigit():
                    continue

                # Arama sonuçlarındaki "Takım - Bugün" özetlerini maç sayma.
                if deplasman.strip().casefold() in ("bugün", "bugun", "yarın", "yarin"):
                    continue

                # "dk sonra Takım - Takım" biçimindeki arama başlıklarını maç sayma.
                if "dk sonra" in ev.casefold():
                    continue

                # Yayıncı adı takım adının başına yapışmışsa alma.
                if re.match(r"^(?:sport|spor|tivibu)\s+", ev, re.IGNORECASE):
                    continue

                if any(k in aday for k in (
                    "bilgisi bekleniyor",
                    "maç ayrıntısını aç",
                    "mac ayrintisini ac",
                    "tivibu spor",
                    "sport 2",
                    "sport plus",
                    "spor metro holding",
                    "kararı",
                    "karari",
                    "fikstür", "fikstur", "puan durumu",
                    "son dakika", "sonuçlar", "sonuclar",
                    "haberler", "canlı maçlar", "canli maclar",
                    "canlı skor", "canli skor", "maç programı",
                    "mac programi", "tv'de", "hangi maç",
                    "bugünkü maç", "bugunku mac",
                    "tamamlanan", "analizi hazır",
                    "digiturk", "beın sports", "bein sports",
                    "united states", "w-sport", "snow league"
                )):
                    continue

                if ".com" in aday or "http" in aday:
                    continue

                # Regex ile çıkarılan maçlarda sayfa/arayüz metninin
                # takım adına karışmasını engelle.
                aday_takim_metni = f"{ev} {deplasman}".casefold()

                sahte_parcalar = (
                    "maç", "mac", "bilgi", "detay",
                    "ilgini çekebilir", "ilgini cekebilir",
                    "tarih", "saat", "chevron",
                    "canlı", "canli", "lig",
                    "division", "championship", "league",
                    "kupasi", "kupası", "trendyol",
                    "primera division", "cev erkekler",
                    "cev kadınlar", "cev kadinlar"
                )

                if any(x in aday_takim_metni for x in sahte_parcalar):
                    continue

                if len(ev.split()) > 6 or len(deplasman.split()) > 6:
                    continue

                # Takım adının içine saat/skor metni karışmışsa sonucu alma.
                if re.search(r"\b\d{1,2}[.:]\d{2}\b", f"{ev} {deplasman}"):
                    continue

                # Kaynakların eklediği lig/sezon numarası takım adının parçasıysa alma.
                if re.search(r"\b(?:1\.|2\.|3\.)\s*$", f"{ev} {deplasman}"):
                    continue

                satirlar.append((ev, deplasman, satir))

        return satirlar

    # Yapılandırılmış spor verisini doğrudan kullan.
    # Böylece takım adları regex tarafından kesilmez.
    yapilandirilmis = []

    for sonuc in web_verisi:
        ev = temiz(sonuc.get("ev", ""))
        deplasman = temiz(sonuc.get("deplasman", ""))
        saat = temiz(sonuc.get("saat", ""))
        lig = temiz(sonuc.get("lig", ""))

        # Arama sonuçlarında maç durumu takım adına yapışabiliyor.
        # "Maç Bitti Torino - Roma" gerçek bir gelecek fikstürü değildir;
        # genel "bugün maç var mı?" sorgusunda tamamen dışarıda bırak.
        durum_ifadesi = re.compile(
            r"\b(?:maç|mac)\s+(?:bitti|başladı|basladi|oynanıyor|oynaniyor|ertelendi|iptal)\b",
            re.IGNORECASE
        )
        if durum_ifadesi.search(f"{ev} {deplasman}"):
            continue

        # Geçmiş saatleri yalnızca bugünkü fikstür sorgusunda ele.
        # Maç sonucu sorularında oynanmış maçlar korunmalıdır.
        if bugun_mu and not sonuc_mu and saat:
            try:
                saat_dt = datetime.strptime(saat, "%H:%M")
                simdi_dt = datetime.now()
                if (
                    saat_dt.hour < simdi_dt.hour
                    or (
                        saat_dt.hour == simdi_dt.hour
                        and saat_dt.minute <= simdi_dt.minute
                    )
                ):
                    continue
            except ValueError:
                pass

        # Web kaynaklarının takım adlarına eklediği skor/kod öneklerini temizle.
        ev = re.sub(r"^(?:\d{1,2}\s+)+", "", ev).strip()
        deplasman = re.sub(r"^(?:\d{1,2}\s+)+", "", deplasman).strip()

        ev = re.sub(
            r"^(?:[A-ZÇĞİÖŞÜ]{1,3}\s+)+(?=[A-ZÇĞİÖŞÜ][a-zçğıöşü])",
            "",
            ev
        ).strip()
        deplasman = re.sub(
            r"^(?:[A-ZÇĞİÖŞÜ]{1,3}\s+)+(?=[A-ZÇĞİÖŞÜ][a-zçğıöşü])",
            "",
            deplasman
        ).strip()

        # Genel maç sorgusunda sayfanın genel lig bilgisini maça taşıma.
        lig = ""

        if any(k in f"{ev} {deplasman}".casefold() for k in (
            "tekrar",
            "beın sports",
            "bein sports",
            "digiturk",
            "snow league",
            "w-sport"
        )):
            continue

        if not ev or not deplasman:
            continue

        # Yapılandırılmış sonuç gerçekten takım adı mı kontrol et.
        # Web sayfası başlıkları, lig açıklamaları ve arayüz metinleri
        # maç olarak kabul edilmez. Takım/lig/site hardcode edilmez.
        takim_metin = f"{ev} {deplasman}".casefold()

        sahte_mac_ifadeleri = (
            "maç", "mac", "bilgi", "detay", "ilgini çekebilir",
            "ilgini cekebilir", "tarih", "saat", "chevron",
            "ilk yarı", "ilk yari", "canlı", "canli",
            "lig", "division", "championship",
            "league", "kupasi", "kupası",
            "cev erkekler", "cev kadınlar", "cev kadinlar",
            "trendyo", "primera division"
        )

        if any(ifade in takim_metin for ifade in sahte_mac_ifadeleri):
            continue

        # Bir takım adı yerine uzun bir sayfa başlığı/snippet gelmişse ele.
        if len(ev.split()) > 6 or len(deplasman.split()) > 6:
            continue

        # HTML/arayıcı ve URL artıkları.
        if any(x in takim_metin for x in (
            "http://", "https://", ".com", ".net", ".org",
            "›", "»", "|"
        )):
            continue

        # Kaynak spor bilgisini vermiyorsa mevcut yapılandırılmış
        # sonucu gereksiz yere eleme.
        if istenen_spor and sonuc.get("spor") and sonuc.get("spor") != istenen_spor:
            continue

        # Kullanıcı belirli bir takım/oyuncu sorduysa sonucu onunla sınırla.
        if "takim" in locals() and takim:
            aday_takim = f"{ev} {deplasman}".casefold()
            if takim.casefold() not in aday_takim:
                continue

        parcalar = [f"⚽ {ev} - {deplasman}"]

        if lig:
            parcalar.append(f"[{lig}]")

        if sonuc_mu and sonuc.get("oynandi"):
            tarih = str(sonuc.get("tarih", "")).strip()
            ev_skor = sonuc.get("ev_skor")
            deplasman_skor = sonuc.get("deplasman_skor")

            if tarih:
                parcalar.append(f"— {tarih}")

            if ev_skor is not None and deplasman_skor is not None:
                parcalar.append(f"| {ev_skor}-{deplasman_skor}")
        elif saat:
            parcalar.append(f"— {saat}")

        yapilandirilmis.append(" ".join(parcalar))

    if yapilandirilmis:
        # Aynı maçın farklı kaynaklardaki takım adı varyasyonlarını tekilleştir.
        # Örn: "Como" / "Como 1907", "Torino" / "Torino FC".
        tekil = []
        anahtarlar = set()

        for satir in yapilandirilmis:
            mac = re.search(
                r"⚽\s*(.*?)\s+-\s+(.*?)\s+—\s+(.+)$",
                satir
            )
            if not mac:
                continue

            ev = temiz(mac.group(1))
            deplasman = temiz(mac.group(2))
            saat = mac.group(3)

            def takim_anahtari(ad):
                ad = norm(ad)
                ad = re.sub(r"\b(fc|fk|cf|ac|sc|1907)\b", "", ad)
                ad = re.sub(r"\s+", " ", ad).strip()
                return ad

            anahtar = (
                takim_anahtari(ev),
                takim_anahtari(deplasman),
                saat
            )

            if anahtar in anahtarlar:
                continue

            # Kaynaklardan biri takım adını kırpmış olabilir:
            # "Fenerbah" / "Fenerbahçe" gibi varyasyonları da aynı maç kabul et.
            from difflib import SequenceMatcher

            def benzer(a, b):
                a = takim_anahtari(a)
                b = takim_anahtari(b)
                if not a or not b:
                    return False
                if a == b:
                    return True
                return SequenceMatcher(None, a, b).ratio() >= 0.85

            ayni_mac = False
            for eski_ev, eski_deplasman, eski_saat in anahtarlar:
                if (
                    saat == eski_saat
                    and benzer(ev, eski_ev)
                    and benzer(deplasman, eski_deplasman)
                ):
                    ayni_mac = True
                    break

            if ayni_mac:
                continue

            anahtarlar.add(anahtar)
            tekil.append(satir)

        kategoriler["futbol"].extend(tekil)
        # Yapılandırılmış veri varsa eski regex ayrıştırmasını çalıştırma.

    # Yapılandırılmış maçlar bulunduysa eski sayfa/regex yolunu
    # çalıştırma. Bu yol menü, lig ve ülke adlarını takım adı sanabiliyor.
    if yapilandirilmis:
        web_verisi = []

    bulunan = set()

    for sonuc in web_verisi[:8]:
        baslik = temiz(sonuc.get("title", ""))
        ozet = temiz(sonuc.get("snippet", ""))

        kaynak = f"{baslik}\n{ozet}"

        # Arama sonucu sayfasını da oku.
        url = str(sonuc.get("url", "")).strip()

        if url:
            try:
                sayfa = web_sayfa_oku(url, limit=5000)
                if sayfa:
                    kaynak += "\n" + str(sayfa)
            except Exception as e:
                print(
                    f"⚠️ Spor fikstür sayfası okunamadı: {e}",
                    flush=True
                )

        kategori = kategori_bul(kaynak)

        # Kullanıcı belirli spor istedi ise diğer kategorileri alma.
        if istenen_spor and kategori != istenen_spor:
            continue

        # Genel maç sorgusunda sayfanın genel lig bilgisini
        # tek tek maçlara yanlışlıkla taşıma.
        lig = ""
        maclar = mac_satirlarini_bul(kaynak)



        for ev, deplasman, ham_satir in maclar:
            # Maç satırında gerçek saat yoksa maçı alma.
            saat_eslesme = re.search(
                r"\b([01]?\d|2[0-3])\s*[:.]\s*([0-5]\d)\b",
                ham_satir
            )
            if not saat_eslesme:
                continue

            saat = f"{int(saat_eslesme.group(1)):02d}:{saat_eslesme.group(2)}"

            # Navigasyon / takvim ifadelerini maç olarak alma.
            ham_norm = norm(ham_satir)
            if any(k in ham_norm for k in (
                "yaklaşan maç",
                "yaklasan mac",
                "yaklaşan takvim",
                "yaklasan takvim",
                "fikstür",
                "fikstur"
            )):
                continue

            # Arama sayfasının kırpılmış takım adlarını maç olarak alma.
            # Bugünün fikstüründe yarınki maçları gösterme.
            tarih_metni = norm(ham_satir)
            if re.search(r"\b(yarın|yarin)\b", tarih_metni):
                continue

            if len(ev.strip()) < 4 or len(deplasman.strip()) < 4:
                continue

            anahtar = norm(f"{ev}|{deplasman}")

            # Aynı maçın kırpılmış takım adı geldiyse tam adı tercih et.
            mevcut_kayit = None
            for mevcut in list(bulunan):
                mevcut_ev, mevcut_deplasman = mevcut.split("|", 1)
                if mevcut_ev == norm(ev):
                    if (
                        mevcut_deplasman.startswith(norm(deplasman))
                        or norm(deplasman).startswith(mevcut_deplasman)
                    ):
                        mevcut_kayit = mevcut
                        break

            if mevcut_kayit:
                mevcut_ev, mevcut_deplasman = mevcut_kayit.split("|", 1)
                if len(norm(deplasman)) <= len(mevcut_deplasman):
                    continue

                bulunan.remove(mevcut_kayit)
                eski_satir = f"⚽ {mevcut_ev} - {mevcut_deplasman}"
                kategoriler[kategori] = [
                    x for x in kategoriler[kategori]
                    if not x.startswith(eski_satir)
                ]

            if anahtar in bulunan:
                continue

            bulunan.add(anahtar)

            # Kaynakta lig adı varsa koru.
            parcalar = [f"⚽ {ev} - {deplasman}"]

            if lig:
                parcalar.append(f"[{lig}]")

            if saat:
                parcalar.append(f"— {saat}")

            kategoriler[kategori].append(" ".join(parcalar))

    # Tüm kaynaklar birleştirildikten sonra son duplicate temizliği.
    # Aynı maç farklı kaynaklarda farklı kulüp adlarıyla gelebilir:
    # "Como 1907 / Como", "Torino FC / Torino", "Fenerbah / Fenerbahçe" vb.
    from difflib import SequenceMatcher

    def mac_anahtari(ad):
        ad = norm(ad)
        ad = re.sub(r"\b(fc|fk|cf|ac|sc)\b", "", ad)
        ad = re.sub(r"\b\d{4}\b", "", ad)
        ad = re.sub(r"[^a-zçğıöşü0-9 ]+", " ", ad)
        return re.sub(r"\s+", " ", ad).strip()

    def takimlar_benzer(a, b):
        a = mac_anahtari(a)
        b = mac_anahtari(b)

        if not a or not b:
            return False
        if a == b:
            return True

        # Kaynak bir takım adını sonundan kırpmışsa.
        if len(a) >= 5 and len(b) >= 5:
            if a.startswith(b) or b.startswith(a):
                return True

        return SequenceMatcher(None, a, b).ratio() >= 0.85

    for kategori_adi, mac_listesi in kategoriler.items():
        temiz_maclar = []
        gorulen = []

        for satir in mac_listesi:
            eslesme = re.search(
                r"⚽\s*(.*?)\s+-\s+(.*?)\s+—\s+(.+)$",
                satir
            )

            if not eslesme:
                if satir not in temiz_maclar:
                    temiz_maclar.append(satir)
                continue

            ev = temiz(eslesme.group(1))
            deplasman = temiz(eslesme.group(2))
            saat = eslesme.group(3)

            ayni = False
            for eski_ev, eski_deplasman, eski_saat, eski_index in gorulen:
                if (
                    saat == eski_saat
                    and takimlar_benzer(ev, eski_ev)
                    and takimlar_benzer(deplasman, eski_deplasman)
                ):
                    # Daha uzun takım adı daha tam isimdir; onu koru.
                    if len(ev) + len(deplasman) > len(eski_ev) + len(eski_deplasman):
                        temiz_maclar[eski_index] = satir
                        gorulen.remove(
                            (eski_ev, eski_deplasman, eski_saat, eski_index)
                        )
                        gorulen.append(
                            (ev, deplasman, saat, eski_index)
                        )
                    ayni = True
                    break

            if not ayni:
                indeks = len(temiz_maclar)
                temiz_maclar.append(satir)
                gorulen.append((ev, deplasman, saat, indeks))

        kategoriler[kategori_adi] = temiz_maclar

    # Hiçbir gerçek maç çıkarılamadıysa normal EAGLE WEB cevabına
    # düşmek yerine boş dön; çağıran katman güvenli mesaj verecek.
    toplam = sum(len(v) for v in kategoriler.values())

    if toplam == 0:
        return ""

    spor_ikon = {
        "futbol": "⚽ FUTBOL",
        "basketbol": "🏀 BASKETBOL",
        "voleybol": "🏐 VOLEYBOL",
        "tenis": "🎾 TENİS",
        "diğer": "🏅 DİĞER SPORLAR"
    }

    satirlar = [
        "🏟️ EAGLE SPOR",
        "",
        (
            "📅 MAÇ SONUÇLARI"
            if sonuc_mu
            else {
                "bu_hafta": "📅 BU HAFTANIN MAÇLARI",
                "gelecek_hafta": "📅 GELECEK HAFTANIN MAÇLARI",
                "yarin": "📅 YARININ MAÇLARI",
                "dun": "📅 DÜNÜN MAÇLARI",
            }.get(zaman_kapsami, "📅 BUGÜNÜN MAÇLARI")
        )
    ]

    for kategori in [
        "futbol",
        "basketbol",
        "voleybol",
        "tenis",
        "diğer"
    ]:
        maclar = kategoriler[kategori]

        if not maclar:
            continue

        satirlar.extend([
            "",
            spor_ikon[kategori]
        ])

        # Aynı maçların tekrarını önle.
        for mac in list(dict.fromkeys(maclar))[:12]:
            satirlar.append(mac)

    return "\n".join(satirlar)


def web_sonuclari_metni(sonuclar):
    """Web arama sonuçlarını ve gerçek kaynak sayfalarını hazırlar."""
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
            satirlar.append(
                "GERÇEK SAYFA İÇERİĞİ: Okunamadı. "
                "Yalnızca arama özeti kullanılabilir.\n"
            )

    satirlar.append(
        "===== WEB ARAŞTIRMASI SONU ====="
    )

    return "\n".join(satirlar)


def eagle_ogrenme_ara(konu):
    konu = str(konu).strip().casefold()

    if not konu:
        return None

    veri = hafiza_yukle()
    sorgu_kelimeleri = set(
        konu.replace("(", " ").replace(")", " ").split()
    )

    for kayit in veri.get("eagle_ogrenme", []):
        if not isinstance(kayit, dict):
            continue

        kayit_konu = str(
            kayit.get("konu", "")
        ).strip().casefold()

        kayit_soru = str(
            kayit.get("soru", "")
        ).strip().casefold()

        if kayit_konu == konu or kayit_soru == konu:
            return kayit

        kayit_kelimeleri = set(
            (
                kayit_konu + " " + kayit_soru
            ).replace("(", " ").replace(")", " ").split()
        )

        ortak = sorgu_kelimeleri & kayit_kelimeleri

        anlamli_ortak = {
            kelime for kelime in ortak
            if (
                len(kelime) >= 3
                and kelime not in {
                    "python",
                    "nedir",
                    "nedeni",
                    "fonksiyonu",
                    "nasıl",
                    "ne",
                }
            )
        }

        if len(anlamli_ortak) >= 2:
            return kayit

    return None


def eagle_webden_ogren(
    konu,
    sonuclar,
    karar=None
):
    konu = str(konu).strip()

    if not konu:
        return False

    if not isinstance(sonuclar, list) or not sonuclar:
        sorgu = konu
        kelimeler = konu.casefold().split()

        if "python" in kelimeler and len(kelimeler) >= 2:
            sorgu = " ".join(kelime for kelime in kelimeler if kelime != "python")
            sorgu += " Python built-in function"

        sonuclar = web_arastir(sorgu, limit=6)

    if not isinstance(sonuclar, list):
        return False

    bilgiler = []
    kaynaklar = set()

    anahtarlar = [
        kelime for kelime in konu.casefold().split()
        if len(kelime) >= 3 and kelime not in {"python", "nedir", "fonksiyonu"}
    ]

    for sonuc in sonuclar:
        if not isinstance(sonuc, dict):
            continue

        baslik = str(sonuc.get("title", "")).strip()
        aciklama = str(sonuc.get("snippet", "")).strip()
        url = str(sonuc.get("url", "")).strip()

        metin = f"{baslik} {aciklama}".casefold()

        if not anahtarlar or not any(kelime in metin for kelime in anahtarlar):
            continue

        alan = ""
        if url.startswith(("http://", "https://")):
            parcalar = url.split("/")
            if len(parcalar) > 2:
                alan = parcalar[2].lower().split(":")[0]

        if alan:
            kaynaklar.add(alan)

        if baslik and aciklama:
            bilgiler.append(f"{baslik}: {aciklama}")

    if len(kaynaklar) < 2 or len(bilgiler) < 2:
        return False

    bilgi = " | ".join(bilgiler[:3])

    soru = konu

    intent = None
    arac = None
    strateji = "web"

    if isinstance(karar, dict):
        intent = karar.get("intent")
        arac = karar.get("arac")

    return eagle_ogrenme_ekle(
        konu,
        bilgi,
        "web",
        soru=soru,
        intent=intent,
        arac=arac,
        strateji=strateji
    )


def hafiza_metni():
    hafiza = hafiza_yukle()

    if not hafiza:
        return "Henüz kayıtlı kalıcı bilgi yok."

    if isinstance(hafiza, list):
        return "\n".join(
            f"- {bilgi}"
            for bilgi in hafiza
        )

    satirlar = []

    for bilgi in hafiza.get("kullanici", []):
        satirlar.append(f"- {bilgi}")

    for kayit in hafiza.get("eagle_ogrenme", []):
        if isinstance(kayit, dict):
            konu = str(kayit.get("konu", "")).strip()
            bilgi = str(kayit.get("bilgi", "")).strip()
            if konu or bilgi:
                satirlar.append(f"- {konu}: {bilgi}")

    for kayit in hafiza.get("sohbet", []):
        if isinstance(kayit, dict):
            soru = str(kayit.get("soru", "")).strip()
            cevap = str(kayit.get("cevap", "")).strip()
            if soru and cevap:
                satirlar.append(f"- Soru: {soru} | Cevap: {cevap}")

    return "\n".join(satirlar) if satirlar else "Henüz kayıtlı kalıcı bilgi yok."


@app.get("/")
def ana():
    return jsonify({
        "ok": True,
        "assistant": "Eagle-AI",
        "message": "🦅 Eagle-AI API çalışıyor."
    })


@app.get("/api/durum")
def durum():
    import subprocess

    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
    except Exception:
        commit = "bilinmiyor"

    return jsonify({
        "ok": True,
        "assistant": "Eagle-AI",
        "memory_count": len(hafiza_yukle()),
        "build_marker": "SPORTS_DIAGNOSTIC_20260911",
        "git_commit": commit
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


# 🧠 EAGLE KONUŞMA BAĞLAMI — geçici Smart Debt testi
SOHBET_BAGLAM_DOSYASI = Path(__file__).with_name("eagle_sohbet_baglam.json")

def sohbet_baglam_yukle():
    try:
        if not SOHBET_BAGLAM_DOSYASI.exists():
            return {}
        return json.loads(SOHBET_BAGLAM_DOSYASI.read_text(encoding="utf-8"))
    except Exception:
        return {}

def sohbet_baglam_kaydet(veri):
    SOHBET_BAGLAM_DOSYASI.write_text(
        json.dumps(veri, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def eagle_genel_baglam_coz(mesaj, gecmis=None):
    """
    🧠 EagleAI GENEL KONUŞMA BAĞLAMI
    Belirsiz/devam niteliğindeki mesajı yakın konuşma geçmişindeki
    konu ile birleştirir.

    Özel takım, şehir, Python konusu vb. hardcode etmez.
    Açık ve bağımsız yeni sorulara dokunmaz.
    """
    metin = str(mesaj or "").strip()
    if not metin or not gecmis:
        return metin

    m = metin.casefold().replace("\u0307", "")

    # Açık yeni konu olduğunu düşündüren ifadeler.
    acik_yeni_konu = [
        "hava", "hava durumu",
        "python", "kod", "hata",
        "borç", "borc",
        "hafıza", "hafiza",
        "haber", "güncel", "guncel",
        "hesapla", "kaç tl", "kac tl"
    ]

    # Mesaj kendi başına açık bir konu taşıyorsa geçmişi zorla ekleme.
    if any(x in m for x in acik_yeni_konu):
        return metin

    # Devam/belirsizlik ifadeleri.
    devam_ifadeleri = [
        "peki",
        "bunlar",
        "buna", "bunu", "bunun", "bunda",
        "şuna", "şunu", "şunun",
        "ona", "onu", "onun",
        "orada", "orası", "orasi",
        "aynısı", "aynisi",
        "aynı", "ayni",
        "sonra", "sonuç ne", "sonucu ne",
        "kaç kaç", "kac kac",
        "ne oldu", "neydi",
        "hangisi", "hangisiydi",
        "devam", "peki ya",
        "bir de", "peki bunun",
        "peki bu"
    ]

    if not any(
        re.search(r"(?<!\w)" + re.escape(x) + r"(?!\w)", m)
        for x in devam_ifadeleri
    ):
        return metin

    # En yakın anlamlı kullanıcı mesajını bul.
    adaylar = []
    for item in reversed(gecmis):
        if not isinstance(item, dict):
            continue

        role = str(item.get("role", "")).strip().lower()
        if role not in {"user", "assistant"}:
            continue

        icerik = str(
            item.get("text", item.get("content", ""))
        ).strip()

        if not icerik:
            continue

        adaylar.append(icerik)

        # En yakın iki mesaj yeterli; bağlamı gereksiz büyütme.
        if len(adaylar) >= 2:
            break

    if not adaylar:
        return metin

    # En yakın kullanıcı mesajını önceliklendir.
    onceki_kullanici = None
    for item in reversed(gecmis):
        if not isinstance(item, dict):
            continue
        if str(item.get("role", "")).strip().lower() != "user":
            continue

        icerik = str(
            item.get("text", item.get("content", ""))
        ).strip()

        if icerik:
            onceki_kullanici = icerik
            break

    konu = onceki_kullanici or adaylar[0]

    # Aynı mesajın kendisini tekrar ekleme.
    if konu.casefold().strip() == metin.casefold().strip():
        return metin

    # Karar motoru ve ilgili araçlar önceki konuyu görebilsin.
    return f"{konu}\n\nKullanıcının devam mesajı: {metin}"



def eagle_baglam_yonlendir(mesaj, karar, sohbet_baglam, borc_modulu, gecmis=None):
    """
    🧠 EagleAI konuşma bağlamı yönlendiricisi.
    Belirsiz devam mesajlarını aktif yerel konuya bağlar.
    Açıkça yeni bir konu varsa mevcut kararı bozmaz.
    """
    aktif_borc_id = sohbet_baglam.get("aktif_borc_id")

    # 🧠 Global bağlam boş olsa bile son konuşmadan aktif borcu bul
    if aktif_borc_id is None and gecmis:
        try:
            history_borc = borc_modulu.akilli_borc_historyden_bul(gecmis)
            if history_borc:
                aktif_borc_id = history_borc.get("id")
        except Exception:
            pass

    if aktif_borc_id is None:
        return karar

    # Açıkça başka bir yerel/güncel konuya geçilmişse bağlamı ezme.
    yeni_konu_araclari = {
        "hava_api",
        "spor_kaynaklari",
        "kod_analiz",
        "hafiza",
    }

    if karar.get("arac") in yeni_konu_araclari:
        return karar

    m = str(mesaj or "").strip().lower()

    # Aktif borca doğal devam / işlem ifadeleri.
    devam_ifadeleri = [
        "buna gerek yok",
        "buna artık gerek yok",
        "artık buna gerek yok",
        "artik buna gerek yok",
        "bunu sil",
        "bunu kaldır",
        "bunu kaldir",
        "bunu temizle",
        "şunu sil",
        "şunu kaldır",
        "şunu temizle",
        "sil gitsin",
        "kaldır gitsin",
        "kaldir gitsin",
        "temizle gitsin",
        "artık lazım değil",
        "artik lazim degil",
        "artık ihtiyacım yok",
        "artik ihtiyacim yok",
        "gerek kalmadı",
        "gerek kalmadi",
        "işimiz bitti",
        "isimiz bitti",
        "tamamdır kapat",
        "tamamdir kapat",
        "kapat bunu",
    ]

    if any(ifade in m for ifade in devam_ifadeleri):
        karar.update({
            "intent": "borc",
            "guven": "yüksek",
            "neden": "Önceki konuşmadaki aktif borç kaydına devam eden doğal dil isteği algılandı.",
            "arac": "borc_modulu",
            "islem": "veri_getir",
            "dogrulama": True,
            "baglamdan": True,
        })

    return karar

@app.post("/api/sohbet")
def sohbet():

    data = request.get_json(silent=True) or {}

    mesaj = str(
        data.get("message", "")
    ).strip()

    # 📷 EAGLE GÖRSEL ANLAMA
    # Android'den gelen Base64 görseli önce Gemini Vision'a gönder.
    # Görsel yoksa mevcut EagleAI akışı aynen devam eder.
    file_base64 = data.get("file_base64")
    file_mime = str(
        data.get("file_mime", "image/jpeg")
    ).strip()

    if file_base64:
        try:
            import os
            import requests

            gemini_key = os.getenv("GEMINI_API_KEY")

            if gemini_key:
                temiz_base64 = str(file_base64).strip()

                # Olası data:image/...;base64, önekini temizle.
                if ";base64," in temiz_base64:
                    temiz_base64 = temiz_base64.split(
                        ";base64,", 1
                    )[1]

                if file_mime.startswith("image/"):
                    gemini_url = (
                        "https://generativelanguage.googleapis.com/"
                        "v1beta/models/gemini-2.5-flash:generateContent"
                    )

                    goruntu_prompt = (
                        "Bu görseli genel amaçlı ve çok dikkatli şekilde analiz et. "
                        "Görselde ne varsa önce tanımla; yalnızca cihaz veya nesne "
                        "aramakla sınırlı kalma. İnsan, hayvan, bitki, araç, elektronik "
                        "cihaz, makine, parça, ev eşyası, yemek, yapı, manzara, belge, "
                        "ekran görüntüsü, tabela, yazı, harita veya başka herhangi bir "
                        "görsel içerik olabilir. "
                        "Kullanıcının sorusu: "
                        f"{mesaj}\n\n"
                        "Önce görseldeki ana nesneyi, kişiyi, canlıyı, yeri veya içeriği "
                        "belirle. Ardından kullanıcının sorusunu doğrudan görseldeki "
                        "bilgilere dayanarak cevapla. "
                        "Görsel üzerinde okunabilir marka, model, etiket, başlık, tabela "
                        "veya başka bir yazı varsa dikkate al ve gerektiğinde metni oku. "
                        "Bir nesnenin ne işe yaradığını soruyorsa, önce nesnenin ne "
                        "olduğunu belirle ve ardından temel kullanım amacını açıkla. "
                        "Görselde birden fazla önemli unsur varsa bunları ayırt et. "
                        "Görselin kesin olarak göstermediği model, teknik özellik, "
                        "konum veya başka bir bilgiyi uydurma. Emin olmadığın durumda "
                        "bunu açıkça belirt ve görselden doğrulanabilen bilgilerle "
                        "sınırlı kal. "
                        "Öncelik sırası: görseli anla, soruyu görsele göre cevapla, "
                        "ancak gerekirse daha sonra dış bilgi doğrulaması yapılabilir."
                    )

                    gemini_payload = {
                        "contents": [{
                            "parts": [
                                {
                                    "inline_data": {
                                        "mime_type": file_mime,
                                        "data": temiz_base64,
                                    }
                                },
                                {
                                    "text": goruntu_prompt
                                }
                            ]
                        }]
                    }

                    gemini_response = requests.post(
                        gemini_url,
                        params={"key": gemini_key},
                        headers={
                            "Content-Type":
                                "application/json"
                        },
                        json=gemini_payload,
                        timeout=45,
                    )

                    if gemini_response.ok:
                        gemini_data = gemini_response.json()
                        adaylar = gemini_data.get(
                            "candidates", []
                        )

                        if adaylar:
                            parcalar = adaylar[0].get(
                                "content", {}
                            ).get("parts", [])

                            goruntu_cevabi = "\n".join(
                                str(x.get("text", "")).strip()
                                for x in parcalar
                                if x.get("text")
                            ).strip()

                            if goruntu_cevabi:
                                return jsonify({
                                    "ok": True,
                                    "answer": (
                                        "📷 EAGLE GÖRSEL ANALİZİ\n\n"
                                        + goruntu_cevabi
                                    ),
                                    "eagle_direct": True,
                                    "image_analysis": True,
                                    "vision_model": "gemini-2.5-flash",
                                    "memory_count": len(
                                        hafiza_yukle()
                                    ),
                                })

                    print(
                        "⚠️ Gemini görsel analizi başarısız; "
                        "mevcut EagleAI akışına devam ediliyor.",
                        flush=True,
                    )

        except Exception as exc:
            print(
                f"⚠️ Görsel analiz hatası: {exc}",
                flush=True,
            )

    gecmis = data.get("history", [])
    sohbet_baglam = sohbet_baglam_yukle()
    aktif_borc_id = sohbet_baglam.get("aktif_borc_id")

    if not mesaj:
        return jsonify({
            "ok": False,
            "error": "Mesaj boş olamaz."
        }), 400

    hatirla_desenleri = ["hatırla:", "hatirla:", "unutma:"]
    sil_desenleri = ["hafızadan sil:", "hafizadan sil:", "hafızadan çıkar:", "hafizadan cikar:"]
    mesaj_kucuk = mesaj.lower()

    silindi = False
    for desen in sil_desenleri:
        if mesaj_kucuk.startswith(desen):
            bilgi = mesaj[len(desen):].strip()
            if bilgi:
                silindi = hafiza_sil(bilgi)
            break

    if sil_desenleri and any(mesaj_kucuk.startswith(d) for d in sil_desenleri):
        kalici_hafiza = hafiza_metni()
        return jsonify({
            "ok": True,
            "answer": (
                "🦅 Hafızadan sildim."
                if silindi
                else "🦅 Bu bilgi hafızamda bulunamadı."
            ),
            "eagle_direct": True,
            "memory_count": len(kalici_hafiza)
        })

    for desen in hatirla_desenleri:
        if mesaj_kucuk.startswith(desen):
            bilgi = mesaj[len(desen):].strip()
            eklendi = hafiza_ekle(bilgi) if bilgi else False
            kalici_hafiza = hafiza_metni()
            return jsonify({
                "ok": True,
                "answer": (
                    "🦅 Hafızama ekledim."
                    if eklendi
                    else "🦅 Bu bilgi zaten hafızamda."
                ),
                "eagle_direct": True,
                "memory_count": len(kalici_hafiza)
            })

    kalici_hafiza = hafiza_metni()
    autofix_istegi = False
    # 🧠 GENEL KONUŞMA BAĞLAMI
    # Belirsiz devam mesajlarını karar motorundan önce yakın geçmişle çöz.
    mesaj_orijinal = mesaj

    # Yeni Python kodu doğrudan geldiyse genel konuşma bağlamı
    # kodun içine önceki mesajları eklememeli.
    yeni_python_mesaji = bool(re.search(
        r'(?m)^\s*(?:from\s+\w+|import\s+\w+|def\s+\w+|class\s+\w+|print\s*\(|[A-Za-z_]\w*\s*=)',
        mesaj
    ))

    if yeni_python_mesaji:
        mesaj_karar = mesaj
    else:
        mesaj_karar = eagle_genel_baglam_coz(mesaj, gecmis)
    if mesaj_karar != mesaj_orijinal:
        print(
            f"🧠 EAGLE BAĞLAM ÇÖZÜLDÜ: {mesaj_karar}",
            flush=True
        )

    mesaj = mesaj_karar
    akil_plani = akil_motor.planla(mesaj_karar, gecmis)
    karar = akil_plani.get("karar", {})

    # 🧠 ÖĞRENİLMİŞ DAVRANIŞ ADAYI
    # Öğrenilmiş kayıt kararın yerine geçmez; yalnızca güvenli bir aday olarak tutulur.
    ogrenilmis_karar = eagle_ogrenme_ara(mesaj_karar)

    if (
        isinstance(ogrenilmis_karar, dict)
        and ogrenilmis_karar.get("arac")
        and ogrenilmis_karar.get("strateji")
    ):
        print(
            "🧠 ÖĞRENİLMİŞ DAVRANIŞ ADAYI: "
            f"{ogrenilmis_karar.get('arac')} / "
            f"{ogrenilmis_karar.get('strateji')}",
            flush=True
        )
        ogrenilmis_karar = None

    # 🧠 Hafıza soruları kod analizi değildir.
    hafiza_sorgusu = any(
        ifade in mesaj_kucuk
        for ifade in (
            "hafıza", "hafiza",
            "hatırla", "hatirla",
            "hatırlıyor musun", "hatirliyor musun",
            "neydi"
        )
    )

    if hafiza_sorgusu and karar.get("arac") == "kod_analiz":
        karar = {
            **karar,
            "intent": "sohbet",
            "arac": "eagle_sohbet",
            "neden": "Hafıza sorgusu kod analizi kararını geçersiz kıldı.",
        }

    # 🧠 AKTİF PYTHON KODU TAKİBİ
    aktif_kod = sohbet_baglam.get("aktif_kod", "")
    aktif_kod_takibi = False

    # Yeni mesajın içinde açık bir Python ataması varsa,
    # eski aktif kod yerine yeni kod kullanılacak.
    yeni_kod_eslesmesi = re.search(
        r'(?m)^\s*(?:from\s+\w+|import\s+\w+|def\s+\w+|class\s+\w+|print\s*\(|[A-Za-z_]\w*\s*=)',
        mesaj
    )
    yeni_kod_var = bool(yeni_kod_eslesmesi)

    if aktif_kod and not yeni_kod_var and not any(
        ifade in mesaj_kucuk
        for ifade in ("hafıza", "hafiza", "hatırla", "hatirla", "neydi")
    ):
        kod_takip_ifadeleri = [
            "bu kod",
            "yukarıdaki kod",
            "yukaridaki kod",
            "son kod",
            "kodun çıktısı",
            "kodun ciktisi",
            "çıktısı nedir",
            "ciktisi nedir",
            "ne yazdırır",
            "ne yazdirir",
            "çalışınca ne olur",
            "calisinca ne olur",
            "çalıştırınca ne olur",
            "calistirinca ne olur",
            "sonuç ne",
            "sonucu ne",
            "bu kodda hata var mı",
            "bu kodda hata var mi",
            "kodda hata var mı",
            "kodda hata var mi",
            "neden böyle çalışır",
            "neden boyle calisir",
            "kodu açıkla",
            "kodu acikla"
        ]

        if karar.get("intent") != "matematik" and any(x in mesaj_kucuk for x in kod_takip_ifadeleri):
            aktif_kod_takibi = True
            karar.update({
                "intent": "kod_hata",
                "guven": "yüksek",
                "neden": "Önceki mesajdaki aktif Python koduna devam eden istek algılandı.",
                "arac": "kod_analiz",
                "baglamdan": True
            })

    # 🧠 Önceki konuşmanın aktif konusu belirsiz mesajı açıklıyorsa kullan.
    # 🧠 Hafıza soruları kod analizi olarak yönlendirilmemeli.
    hafiza_sorgusu = any(
        ifade in mesaj_kucuk
        for ifade in (
            "hafızamda", "hafizamda",
            "hafızadaki", "hafizadaki",
            "hafızaya", "hafizaya",
            "hatırlıyor musun", "hatirliyor musun",
            "neydi", "ne olduğunu"
        )
    )

    if not hafiza_sorgusu:
        karar = eagle_baglam_yonlendir(
            mesaj,
            karar,
            sohbet_baglam,
            borc_modulu,
            gecmis
        )

    # 🧠 ÖĞRENİLMİŞ DAVRANIŞI UYGULA
    # Özel kararları (spor, hava, borç, kod vb.) ezmeden yalnızca
    # genel sohbet kararında öğrenilmiş aracı devreye al.
    if (
        ogrenilmis_karar
        and (
            karar.get("arac") == "eagle_sohbet"
            or (
                karar.get("intent") == "guncel_bilgi"
                and ogrenilmis_karar.get("arac") == "web_arastirma"
            )
        )
        and ogrenilmis_karar.get("arac")
        in ("eagle_sohbet", "web_arastirma", "spor_kaynaklari", "hava_api")
    ):
        karar = {
            **karar,
            "intent": ogrenilmis_karar.get("intent") or karar.get("intent"),
            "arac": ogrenilmis_karar.get("arac"),
            "neden": "Önceki başarılı öğrenmeden öğrenilmiş davranış kullanıldı.",
            "ogrenmeden": True,
            "ogrenilmis_bilgi": ogrenilmis_karar.get("bilgi", ""),
        }
        print(
            f"🧠 ÖĞRENİLMİŞ DAVRANIŞ UYGULANDI: "
            f"{karar.get('arac')}",
            flush=True
        )

    print(f"🧠 EAGLE KARAR: {karar}", flush=True)

    def eagle_yapistirilmis_kod_mu(metin):
        """Mesajın doğrudan Python kodu içerip içermediğini belirler."""
        satirlar = metin.strip().splitlines()

        # Tek satırlı veya soru içine gömülmüş Python atamasını yakala.
        if re.search(r'([A-Za-z_]\w*\s*=\s*[^?]+)$', metin):
            return True

        if re.search(r'(?m)^\s*print\s*\(', metin):
            return True

        if len(satirlar) < 2:
            return False

        kod_isaretleri = [
            "def ", "class ", "import ", "from ",
            "return ", "if ", "elif ", "else:",
            "for ", "while ", "try:", "except",
            "with ", "print(", " = ", "==",
            "raise ", "yield ", "async def "
        ]

        skor = 0

        for satir in satirlar:
            temiz = satir.strip()

            if not temiz:
                continue

            if temiz.startswith("#"):
                skor += 1
                continue

            if any(isaret in temiz for isaret in kod_isaretleri):
                skor += 1

        return skor >= 2

    # ▶️ AKTİF PYTHON KODU GERÇEK ÇIKTI TESTİ
    if aktif_kod_takibi and any(x in mesaj_kucuk for x in [
        "çıktısı", "ciktisi", "ne yazdırır", "ne yazdirir",
        "çalışınca", "calisinca", "çalıştırınca", "calistirinca",
        "sonuç ne", "sonucu ne"
    ]):
        try:
            import tempfile

            calisma_klasoru = Path(
                tempfile.mkdtemp(
                    prefix=".eagle_exec_",
                    dir=str(Path(__file__).resolve().parent)
                )
            )

            calisma_dosyasi = calisma_klasoru / "aktif_kod.py"
            calisma_dosyasi.write_text(
                aktif_kod,
                encoding="utf-8"
            )

            try:
                sonuc = subprocess.run(
                    [sys.executable, str(calisma_dosyasi)],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    cwd=str(calisma_klasoru)
                )

                stdout = (sonuc.stdout or "").strip()
                stderr = (sonuc.stderr or "").strip()

                cevap = [
                    "🦅 EAGLE PYTHON ÇIKTI ANALİZİ",
                    ""
                ]

                if stdout:
                    cevap.extend([
                        "📤 Gerçek çalışma çıktısı:",
                        "",
                        "```text",
                        stdout,
                        "```"
                    ])
                    cevap.append("📤 Kod çalıştı ancak ekrana çıktı yazdırmadı.")

                if stderr:
                    cevap.extend([
                        "",
                        "⚠️ Hata çıktısı:",
                        "",
                        "```text",
                        stderr,
                        "```"
                    ])

                if sonuc.returncode == 0:
                    cevap.extend([
                        "",
                        "✅ Python kodu başarıyla çalıştı."
                    ])
                    cevap.extend([
                        "",
                        f"❌ Python kodu hata koduyla sonlandı: {sonuc.returncode}"
                    ])

                return jsonify({
                    "ok": True,
                    "answer": "\n".join(cevap),
                    "eagle_direct": True,
                    "code_analysis": True,
                    "code_execution": True,
                    "return_code": sonuc.returncode,
                    "memory_count": len(hafiza_yukle())
                })

            finally:
                try:
                    if calisma_dosyasi.exists():
                        calisma_dosyasi.unlink()
                    if calisma_klasoru.exists():
                        calisma_klasoru.rmdir()
                except Exception:
                    pass

        except subprocess.TimeoutExpired:
            return jsonify({
                "ok": True,
                "answer": "🦅 EAGLE PYTHON ÇIKTI ANALİZİ\n\n⏱️ Kod 5 saniye içinde tamamlanmadı; güvenli süre sınırı nedeniyle durduruldu.",
                "eagle_direct": True,
                "code_analysis": True,
                "code_execution": False,
                "memory_count": len(hafiza_yukle())
            })

        except Exception as exc:
            print(f"❌ Python çıktı testi hatası: {exc}", flush=True)

    # 🧠 EAGLE YAPIŞTIRILMIŞ KOD ANALİZİ + AUTOFIX
    # Doğrudan Python kodu yapıştırıldığında:
    # analiz → mantık → güvenli düzeltme → syntax → test
    if karar.get("intent") != "matematik" and (eagle_yapistirilmis_kod_mu(mesaj) or aktif_kod_takibi):
        try:
            import tempfile

            if aktif_kod_takibi:
                kaynak_kod = aktif_kod.strip()
            elif eagle_yapistirilmis_kod_mu(mesaj):
                kaynak_kod = mesaj.strip()

                # Kodun arkasına eklenen doğal dil sorusunu Python kaynağına dahil etme.
                soru_isaretleri = (
                    "bu python kodunu",
                    "bu python kodu",
                    "bu kodu",
                    "kod ne yapıyor",
                    "kod ne yapiyor",
                    "fonksiyonunun adımları",
                    "fonksiyonunun adimlari",
                    "sonuç olarak ne yazdırır",
                    "sonuc olarak ne yazdirir",
                    "counter neden kullanılmış",
                    "counter neden kullanilmis",
                )
                satirlar = kaynak_kod.splitlines()
                for i, satir in enumerate(satirlar):
                    if any(
                        ifade in satir.strip().lower()
                        for ifade in soru_isaretleri
                    ):
                        kaynak_kod = "\n".join(satirlar[:i]).strip()
                        break
            elif yeni_kod_eslesmesi:
                # Yeni Python kodu, önceki konuşma bağlamından ayrıştırılır.
                yeni_mesaj = mesaj.strip()
                baglam_isareti = "Kullanıcının devam mesajı:"
                if baglam_isareti in yeni_mesaj:
                    yeni_mesaj = yeni_mesaj.rsplit(baglam_isareti, 1)[1].strip()

                # Kodun arkasındaki doğal dil sorusunu Python kaynağına dahil etme.
                satirlar = yeni_mesaj.splitlines()
                for i, satir in enumerate(satirlar):
                    if any(
                        ifade in satir.strip().lower()
                        for ifade in soru_isaretleri
                    ):
                        satirlar = satirlar[:i]
                        break

                kaynak_kod = "\n".join(satirlar).strip()


            # Markdown kod çitlerini temizle.
            if kaynak_kod.startswith("```") and kaynak_kod.endswith("```"):
                satirlar = kaynak_kod.splitlines()

                if satirlar and satirlar[0].strip().startswith("```"):
                    satirlar = satirlar[1:]

                if satirlar and satirlar[-1].strip() == "```":
                    satirlar = satirlar[:-1]

                kaynak_kod = "\n".join(satirlar).strip()
            # 🧠 Temizlenmiş Python kodunu konuşma bağlamına kaydet.
            sohbet_baglam["aktif_kod"] = kaynak_kod
            sohbet_baglam["aktif_kod_dili"] = "python"
            sohbet_baglam_kaydet(sohbet_baglam)

            # Ön analiz: syntax + mantık
            analiz_motoru = autofix_engine.analiz_motoru
            bulgular = analiz_motoru.analiz_et(kaynak_kod)
            mantik = analiz_motoru.mantik_analizi(
                kaynak_kod,
                bulgular
            )

            yuksek = [
                x for x in mantik
                if (
                    x.get("guven") == "yüksek"
                    and x.get("karar") in {
                        "DUZELTME_ADAYI",
                        "DUZELTME_GEREKLI"
                    }
                )
            ]

            # Geçici Python dosyası oluştur.
            gecici_klasor = Path(
                tempfile.mkdtemp(prefix=".eagle_code_", dir=str(Path(__file__).resolve().parent))
            )

            gecici_dosya = gecici_klasor / "pasted_code.py"
            gecici_dosya.write_text(
                kaynak_kod,
                encoding="utf-8"
            )

            try:
                # Yapıştırılmış Python kodunun gerçek çalışma çıktısını al.
                calisma_sonucu = subprocess.run(
                    [sys.executable, str(gecici_dosya)],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    cwd=str(gecici_klasor)
                )
                gercek_cikti = (calisma_sonucu.stdout or "").strip()
                gercek_hata = (calisma_sonucu.stderr or "").strip()

                # Mevcut güvenli AutoFix döngüsü.
                autofix_sonucu = autofix_engine.repair_loop(
                    gecici_dosya
                )

                cevap = [
                    "🦅 EAGLE KOD ANALİZİ + AUTOFIX",
                    "",
                    f"Bulgu: {len(bulgular)}",
                    f"Deneme: {autofix_sonucu.get('attempts', 0)}",
                    "",
                ]

                if autofix_sonucu.get("success"):
                    if gecici_dosya.exists():
                        duzeltilmis_kod = gecici_dosya.read_text(encoding="utf-8").strip()
                        if duzeltilmis_kod and duzeltilmis_kod != kaynak_kod:
                            cevap.extend([
                                "",
                                "📝 DÜZELTİLMİŞ KOD",
                                "",
                                "```python",
                                duzeltilmis_kod,
                                "```"
                            ])
                    cevap.extend([
                        "✅ DÜZELTME KABUL EDİLDİ",
                        "",
                        f"Neden: {autofix_sonucu.get('reason', '')}",
                    ])

                cevap.extend([
                    "",
                    "📤 Gerçek çalışma çıktısı:",
                    "",
                    "```text",
                    gercek_cikti if gercek_cikti else "(çıktı yok)",
                    "```"
                ])

                if gercek_hata:
                    cevap.extend([
                        "",
                        "⚠️ Gerçek çalışma hatası:",
                        "",
                        "```text",
                        gercek_hata,
                        "```"
                    ])

                if yuksek:
                    cevap.extend([
                        "",
                        "🧠 Yüksek güvenli analiz:"
                    ])

                    for bulgu in yuksek:
                        aday = bulgu.get("duzeltme_adayi")

                        satir = bulgu.get("satir", "?")
                        tur = bulgu.get("tur", "Bilinmeyen")
                        neden = bulgu.get("neden", "")

                        cevap.append(
                            f"• Satır {satir}: {tur} — {neden}"
                        )

                        if isinstance(aday, dict):
                            if aday.get("eski") is not None and aday.get("yeni") is not None:
                                cevap.append(
                                    f"  ↳ {aday.get('eski')} → {aday.get('yeni')}"
                                )

                return jsonify({
                    "ok": True,
                    "answer": "\n".join(cevap),
                    "eagle_direct": True,
                    "code_analysis": True,
                    "autofix": True,
                    "autofix_result": autofix_sonucu,
                    "findings": bulgular,
                    "logic_analysis": mantik,
                    "memory_count": len(hafiza_yukle())
                })

            finally:
                # Geçici dosyayı ve klasörü temizle.
                try:
                    if gecici_dosya.exists():
                        gecici_dosya.unlink()

                    if gecici_klasor.exists():
                        gecici_klasor.rmdir()
                except Exception as temizlik_hatasi:
                    print(
                        f"⚠️ Geçici dosya temizleme uyarısı: {temizlik_hatasi}",
                        flush=True
                    )

        except Exception as exc:
            print(
                f"⚠️ Yapıştırılmış kod AutoFix hatası: {exc}",
                flush=True
            )

    # 🛠️ EAGLE AUTOFIX — yalnızca açıkça bir Python dosyası belirtilirse
    if karar.get("arac") == "kod_analiz":

        dosya_eslesmesi = re.search(
            r"(?<![\w.-])([A-Za-z0-9_./~-]+\.py)(?![\w.-])",
            mesaj
        )

        if dosya_eslesmesi:
            hedef = Path(dosya_eslesmesi.group(1)).expanduser()

            if not hedef.is_absolute():
                hedef = Path(__file__).resolve().parent / hedef

            hedef = hedef.resolve()
            guvenli, guvenlik_nedeni = autofix_engine.is_safe_target(hedef)

            if guvenli:
                print(f"🛠️ AUTOFIX BAŞLADI: {hedef}", flush=True)
                autofix_sonucu = autofix_engine.repair_loop(hedef)

                if autofix_sonucu.get("success"):
                    print(
                        f"✅ AUTOFIX BAŞARILI: {hedef} "
                        f"({autofix_sonucu.get('attempts')} deneme)",
                        flush=True
                    )
                    print(
                        f"⚠️ AUTOFIX UYGULANAMADI: "
                        f"{autofix_sonucu.get('reason')}",
                        flush=True
                    )

                return jsonify({
                    "ok": True,
                    "answer": (
                        "🛠️ EAGLE AUTOFIX\\n\\n"
                        f"Dosya: {hedef.name}\\n"
                        f"Sonuç: {'Başarılı' if autofix_sonucu.get('success') else 'Düzeltilemedi'}\\n"
                        f"Deneme: {autofix_sonucu.get('attempts', 0)}\\n"
                        f"Neden: {autofix_sonucu.get('reason', '')}"
                    ),
                    "eagle_direct": True,
                    "autofix": True,
                    "autofix_result": autofix_sonucu,
                    "memory_count": len(hafiza_yukle())
                })

            print(
                f"🛡️ AUTOFIX ENGELLENDİ: {guvenlik_nedeni}",
                flush=True
            )

    # 🧠 Karar motorunun seçtiği aracı çalıştır
    borc_modulu_sonucu = ""
    if karar.get("arac") == "borc_modulu":
        try:
            akilli_sonuc = None
            yeni_aktif_borc_id = aktif_borc_id

            if hasattr(borc_modulu, "akilli_borc_isle"):
                akilli_sonuc, yeni_aktif_borc_id = borc_modulu.akilli_borc_isle(
                    mesaj,
                    aktif_borc_id,
                    gecmis
                )

            if akilli_sonuc:
                borc_modulu_sonucu = akilli_sonuc
                sohbet_baglam["aktif_borc_id"] = yeni_aktif_borc_id

                if yeni_aktif_borc_id is None:
                    sohbet_baglam.pop("aktif_borc_id", None)

                sohbet_baglam_kaydet(sohbet_baglam)
                print(
                    f"🧠 SMART DEBT AKTİF: {yeni_aktif_borc_id}",
                    flush=True
                )
                borc_modulu_sonucu = borc_modulu.borc_mesaji_isle(mesaj)
                print("🧾 BORÇ MODÜLÜ ÇALIŞTI", flush=True)

        except Exception as e:
            borc_modulu_sonucu = f"Borç modülü çalıştırılırken hata oluştu: {e}"
            print(f"❌ BORÇ MODÜLÜ HATASI: {e}", flush=True)

    hava_verisi = hava_durumu_getir(mesaj)

    # 🌐 Güncel bilgi gerekiyorsa ücretsiz web araştırması yap
    web_verisi = []
    cevap = ""
    live_sports_debug = False

    # 🇹🇷 Süper Lig sorgularında SofaScore takım aramasına girme.
    # Resmi TFF verisi aşağıdaki Süper Lig akışından alınır.
    mesaj_spor_oncesi = str(mesaj or "").lower().replace("\u0307", "")
    super_lig_oncesi = any(k in mesaj_spor_oncesi for k in [
        "süper lig",
        "super lig"
    ])

    if super_lig_oncesi:
        print(
            "🇹🇷 SÜPER LİG: SofaScore atlanıyor, resmi TFF verisi kullanılacak",
            flush=True
        )

    # 🏟️ İki takım + skor/canlı sonuç: önce doğrudan SofaScore.
    # Genel web aramasına düşmeden gerçek maç verisini kullan.
    if karar.get("intent") == "spor" and not super_lig_oncesi:
        live_sports_debug = True
        print(
            "🧪 LIVE DEBUG: SofaScore spor bloğuna girildi",
            flush=True
        )
        mesaj_kf = str(mesaj or "").casefold().replace("\u0307", "")
        mesaj_kf = re.sub(r"[^\w\s]", " ", mesaj_kf)

        skor_istegi = any(k in mesaj_kf for k in (
            "canlı sonuç", "canli sonuc",
            "canlı skor", "canli skor",
            "maç sonucu", "mac sonucu",
            "kaç kaç", "kac kac",
            "skor", "sonuç", "sonuc"
        ))

        mac_ifadesi = "maç" in mesaj_kf or "mac" in mesaj_kf

        if skor_istegi:
            temiz_mesaj = re.sub(
                r"\b(?:maçı|maci|maç|mac|canlı|canli|sonuç|sonuc|skor|kaç|kac|bitti|sonucu)\b",
                " ",
                mesaj_kf
            )
            kelimeler = [
                x for x in re.split(r"\s+", temiz_mesaj.strip())
                if x
            ]

            adaylar = []
            gorulen = set()

            # Takım adlarını sabit listeyle değil, SofaScore aramasıyla çöz.
            for uzunluk in range(min(4, len(kelimeler)), 0, -1):
                for i in range(len(kelimeler) - uzunluk + 1):
                    parca = " ".join(kelimeler[i:i + uzunluk]).strip()

                    # Takım adları arasındaki bağlaçları takım adayı olarak arama.
                    if uzunluk == 1 and parca in {"ile", "ve", "veya"}:
                        continue

                    if not parca or parca in gorulen:
                        continue

                    gorulen.add(parca)

                    takim = sofascore_takim_bul(parca)

                    if takim:
                        adaylar.append(
                            (i, i + uzunluk, uzunluk, takim)
                        )

            secilen = []
            kullanilan_araliklar = []

            for aday in sorted(
                adaylar,
                key=lambda x: (x[0], -x[2])
            ):
                bas, son, _, takim = aday

                if any(
                    bas < s and son > b
                    for b, s in kullanilan_araliklar
                ):
                    continue

                if any(
                    takim.get("id") == x.get("id")
                    for x in secilen
                ):
                    continue

                secilen.append(takim)
                kullanilan_araliklar.append((bas, son))

                if len(secilen) == 2:
                    break

            if len(secilen) == 2:
                mac = sofascore_takimlar_arasi_mac_getir(
                    secilen[0],
                    secilen[1]
                )

                if mac:
                    durum = mac.get("durum")
                    ev = mac.get("ev")
                    dep = mac.get("deplasman")
                    ev_skor = mac.get("ev_skor")
                    dep_skor = mac.get("deplasman_skor")

                    if durum in ("inprogress", "live"):
                        cevap = f"{ev} {ev_skor} - {dep_skor} {dep} (canlı)"
                    elif durum == "finished":
                        cevap = f"{ev} {ev_skor} - {dep_skor} {dep}"
                    elif durum == "notstarted":
                        cevap = f"{ev} - {dep} (henüz başlamadı)"
                    else:
                        cevap = f"{ev} - {dep}"

                    print(
                        f"⚽ SOFASCORE DOĞRUDAN CEVAP: {cevap}",
                        flush=True
                    )

                    return jsonify({
                        "ok": True,
                        "answer": cevap,
                        "web_search": True,
                        "eagle_direct": True,
                        "merkez_motor": False,
                        "memory_count": len(hafiza_yukle())
                    })

                else:
                    cevap = (
                        f"{secilen[0].get('name')} ile "
                        f"{secilen[1].get('name')} arasında "
                        "SofaScore'da güncel veya son maç bulunamadı."
                    )

                    return jsonify({
                        "ok": True,
                        "answer": cevap,
                        "web_search": True,
                        "eagle_direct": True,
                        "merkez_motor": False,
                        "memory_count": len(hafiza_yukle())
                    })

    if karar.get("arac") == "spor_kaynaklari":
        if karar.get("intent") == "spor":
            # 🏐 Spor sorularında önce resmi TVF kaynağı
            gecmis_mac = any(k in mesaj.lower() for k in [
                "dün", "dünkü", "dünün",
                "dun", "dunku", "dunun",
                "geçen maç", "gecen mac",
                "sonuç", "sonuc", "sonuçları", "sonuclari",
                "skor", "skorları", "skorlari",
        "kaç kaç", "kac kac",
        "kaç kaç bitti", "kac kac bitti"
            ])

            voleybol_mu = any(k in mesaj.lower() for k in [
                "voleybol",
                "filenin sultanları",
                "filenin efeleri"
            ])

            if voleybol_mu and not gecmis_mac:
                from datetime import datetime, timedelta

                mesaj_kucuk = mesaj.lower()
                bugun_istegi = any(k in mesaj_kucuk for k in [
                    "bugün", "bugun"
                ])
                yarin_istegi = any(k in mesaj_kucuk for k in [
                    "yarın", "yarin"
                ])

                if bugun_istegi:
                    hedef_tarih = datetime.now().strftime("%d.%m.%Y")
                    web_verisi = tvf_voleybol_getir(hedef_tarih=hedef_tarih)

                elif yarin_istegi:
                    hedef_tarih = (
                        datetime.now() + timedelta(days=1)
                    ).strftime("%d.%m.%Y")
                    web_verisi = tvf_voleybol_getir(hedef_tarih=hedef_tarih)

                    web_verisi = tvf_voleybol_getir()

                # 🏐 BUGÜN/YARIN VOLEYBOL: TVF SONUCU DOĞRUDAN CEVAPLA.
                # Genel web araması ve sayfa okuma.
                if bugun_istegi or yarin_istegi:
                    gun_adi = "bugün" if bugun_istegi else "yarın"

                    if not web_verisi:
                        return jsonify({
                            "ok": True,
                            "answer": f"🏐 {gun_adi.capitalize()} Türkiye'nin resmi voleybol fikstüründe maç görünmüyor.",
                            "eagle_direct": True,
                            "web_search": False,
                            "memory_count": len(hafiza_yukle())
                        })

                    satirlar = [
                        "🏐 GÜNCEL VOLEYBOL BİLGİSİ"
                    ]

                    for sonuc in web_verisi[:8]:
                        baslik = str(sonuc.get("title", "")).strip()
                        ozet = str(sonuc.get("snippet", "")).strip()

                        if baslik:
                            satirlar.append(baslik)
                        if ozet:
                            satirlar.append(ozet)

                    return jsonify({
                        "ok": True,
                        "answer": "\n".join(satirlar),
                        "eagle_direct": True,
                        "web_search": False,
                        "memory_count": len(hafiza_yukle())
                    })

                # 🏐 Bugün/yarın sorgusunda TVF boşsa genel spor aramasına düşme.
                if (bugun_istegi or yarin_istegi) and not web_verisi:
                    gun_adi = "bugün" if bugun_istegi else "yarın"
                    return jsonify({
                        "ok": True,
                        "answer": f"🏐 {gun_adi.capitalize()} Türkiye'nin resmi voleybol fikstüründe maç görünmüyor.",
                        "eagle_direct": True,
                        "web_search": False,
                        "memory_count": len(hafiza_yukle())
                    })

            mesaj_spor = mesaj.lower().replace("\u0307", "")

            # 🏟️ Genel maç sorgusu: kullanıcı açıkça bir lig belirtmediyse
            # UEFA'ya zorla yönlendirme yapma. Takım/oyuncu bağlamı korunur.
            genel_mac_sorgusu = any(k in mesaj_spor for k in [
                "maç var", "mac var",
                "bugün maç", "bugun mac",
                "hangi maç", "hangi mac",
                "maçlar var", "maclar var"
            ])

            # 🇬🇧 İngiltere / Premier League için resmi canlı API

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

            puan_durumu_istegi = any(k in mesaj_spor for k in [
                "puan durumu",
                "puan cetveli",
                "puan tablosu"
            ])

            super_lig_sonuc_istegi = any(k in mesaj_spor for k in [
                "sonuç", "sonuc", "sonuçları", "sonuclari",
                "maç sonucu", "mac sonucu",
                "maç sonuçları", "mac sonuclari",
                "oynanan maç", "oynanan mac",
                "oynanan maçlar", "oynanan maclar",
                "skor", "skorları", "skorlari",
                "kaç kaç", "kac kac", "kaç kaç bitti", "kac kac bitti"
            ])


            if super_lig_mi and puan_durumu_istegi and not web_verisi:
                web_verisi = super_lig_puan_durumu_getir()
            elif super_lig_mi or (
                not web_verisi
                and not ingiltere_mi
                and not voleybol_mu
                and not gecmis_mac
            ):
                # Sonuç/oynanan maç veya takım fikstürü isteğinde resmi TFF verisini kullan.
                # Fikstür/zaman kapsamı isteğinde ise güncel web araması yap;
                # böylece sistem yalnızca geçmiş sonuçlara kilitlenmez.

                # Süper Lig sonuç/fikstür sorgularında resmi TFF verisini kullan.
                web_verisi = super_lig_getir(mesaj)

            # 🇹🇷 Genel Süper Lig sonuçlarını resmi TFF verisinden doğrudan cevapla.
            # Takım adı aranmaz; yapılandırılmış TFF maç kayıtları kullanılır.
            if super_lig_sonuc_istegi and web_verisi:
                satirlar = ["🇹🇷 SÜPER LİG SONUÇLARI"]

                for mac in web_verisi:
                    ev = str(mac.get("ev", "")).strip()
                    deplasman = str(mac.get("deplasman", "")).strip()
                    ev_skor = mac.get("ev_skor")
                    deplasman_skor = mac.get("deplasman_skor")

                    if (
                        ev
                        and deplasman
                        and ev_skor is not None
                        and deplasman_skor is not None
                    ):
                        satirlar.append(
                            f"{ev} {ev_skor}-{deplasman_skor} {deplasman}"
                        )

                if len(satirlar) > 1:
                    return jsonify({
                        "ok": True,
                        "answer": "\n".join(satirlar),
                        "eagle_direct": True,
                        "web_search": False,
                        "memory_count": len(hafiza_yukle())
                    })

            # 🏐 Türkiye-İtalya voleybol sonucu: TVF resmi haber
            mesaj_kucuk = mesaj.lower().replace("\u0307", "")
            if (
                "voleybol" in mesaj_kucuk
                and "türkiye" in mesaj_kucuk
                and "italya" in mesaj_kucuk
                and any(k in mesaj_kucuk for k in [
                    "sonuç", "sonuc", "skor", "kaç kaç", "kac kac", "maç sonucu", "mac sonucu"
                ])
            ):
                tvf_haber_url = "https://tvf.org.tr/icerik/filenin-sultanlari-ikinci-kez-avrupa-sampiyonu"
                tvf_metin = web_sayfa_oku(tvf_haber_url)
                if tvf_metin:
                    web_verisi = [{
                        "title": "TVF - Filenin Sultanları, İkinci Kez Avrupa Şampiyonu!",
                        "url": tvf_haber_url,
                        "snippet": tvf_metin
                    }]

                            # 🏆 Şampiyonlar Ligi — UEFA resmi kaynak
            bugun_mac_sorgusu = any(k in mesaj_spor for k in [
                "maç var", "mac var", "bugün maç", "bugun mac",
                "hangi maç", "hangi mac"
            ])
            sampiyonlar_ligi_mi = any(k in mesaj_spor for k in [
                "şampiyonlar ligi",
                "sampiyonlar ligi",
                "champions league"
            ])

            if sampiyonlar_ligi_mi:
                web_verisi = uefa_sampiyonlar_ligi_getir(mesaj)

# 🌐 Genel spor veri kaynağı — UEFA/TFF/TVF boşsa ESPN
            # 🏟️ Geçmiş/son maç sonucu sorularında çoklu web araması.
            # 🇹🇷 Süper Lig'de resmi TFF verisi varsa onu ezme.
            if gecmis_mac and not super_lig_mi:
                arama_sorgusu = spor_arama_sorgusu(mesaj)
                web_verisi = web_arastir(
                    arama_sorgusu,
                    limit=8
                )

            # 🌐 Güncel spor soruları için yalnızca veri yoksa genel web araması yap.
            # Mevcut resmi/özel veri tekrar ezilmez.
            if not web_verisi:
                arama_sorgusu = spor_arama_sorgusu(mesaj)
                web_verisi = web_arastir(
                    arama_sorgusu,
                    limit=8
                )

    elif karar.get("arac") == "web_arastirma":
        # 🧠 Öğrenme hafızası: güncel olmayan genel konuda önce mevcut bilgiyi kullan
        mesaj_kucuk = mesaj.casefold()
        guncel_isaretleri = [
            "şimdi", "şu an", "son dakika", "güncel", "guncel",
            "haber", "haberler", "maç", "mac", "skor", "puan durumu",
            "bitcoin", "btc", "ethereum", "eth",
            "altın", "gram altın", "dolar", "euro", "sterlin",
            "en son", "son durum", "ne oldu"
        ]

        if not any(x in mesaj_kucuk for x in guncel_isaretleri):
            # 🧠 Öğrenilmiş kayıt artık cevabı doğrudan üretmez.
            # Üst akışta bulunan ogrenilmis_karar, öğrenilmiş davranış
            # için aday olarak kullanılacaktır.
            if ogrenilmis_karar:
                print(
                    "🧠 ÖĞRENİLMİŞ KAYIT KULLANILIYOR",
                    flush=True
                )

                karar_ogrenilmis = {
                    **karar,
                    "arac": "eagle_sohbet",
                    "ogrenmeden": True,
                    "ogrenilmis_bilgi": ogrenilmis_karar.get("bilgi", ""),
                }

                cevap = genel_sohbet(
                    mesaj,
                    gecmis=gecmis,
                    hafiza=kalici_hafiza,
                    karar=karar_ogrenilmis,
                    baglam=akil_plani.get("baglam", {}).get("son_mesaj", "")
                )

                return jsonify({
                    "ok": True,
                    "answer": cevap,
                    "web_search": False,
                    "memory_count": len(hafiza_yukle()),
                    "learned": True
                })

        arama_sorgusu = doviz_arama_sorgusu(mesaj)
        print(f"🌐 WEB SORGU: {arama_sorgusu!r}", flush=True)
        web_verisi = web_arastir(arama_sorgusu)
        print(f"🌐 WEB SONUÇ: {len(web_verisi)}", flush=True)

        if web_verisi and eagle_webden_ogren(mesaj, web_verisi, karar):
            print("🧠 WEB BİLGİSİ ÖĞRENME HAFIZASINA KAYDEDİLDİ", flush=True)



    # 🏟️ GENEL SPOR FİKSTÜRÜ
    # Genel spor/fikstür soruları merkezi web motoruna bırakılır.
    # Sabit site, takım veya regex tabanlı fikstür çıkarımı kullanılmaz.

    # 🧮 Sembolik denklem açıklaması
    if karar.get("denklem_aciklama"):
        return jsonify({
            "ok": True,
            "answer": (
                "🦅 Bu denklem, Taylor kuralının genişletilmiş bir biçimidir. "
                "Faiz oranı (i), nötr reel faiz (r*) ve hedef enflasyon (π*) "
                "üzerinden belirlenir. "
                "1.5(π - π*) enflasyon hedefinden sapmayı, "
                "0.5(y - y*) üretim açığını temsil eder. "
                "α(SOH - SOH*) ve β(BEM - BEM*) ise modele eklenmiş "
                "iki ek sapma/durum bileşenidir; SOH ve BEM'in anlamı "
                "bu denklemde ayrıca tanımlanmadığı için buradan kesin olarak "
                "belirlenemez. α ve β > 0 olması, bu iki bileşenin faiz oranını "
                "pozitif katsayılarla etkilediğini belirtir."
            ),
            "eagle_direct": True,
            "memory_count": len(hafiza_yukle())
        })

    # 🧮 Sembolik denklem çözümü
    if karar.get("denklem_coz"):
        denklem_sonucu = sembolik_denklem_coz(mesaj)

        if denklem_sonucu is not None:
            degisken = denklem_sonucu["degisken"]
            cozumler = denklem_sonucu["cozumler"]

            if cozumler:
                cozum_metni = ", ".join(
                    str(sp.simplify(x)) for x in cozumler
                )
                return jsonify({
                    "ok": True,
                    "answer": f"{degisken} = {cozum_metni}",
                    "eagle_direct": True,
                    "memory_count": len(hafiza_yukle())
                })

    # 🧮 Güvenli matematik doğrulaması
    hesaplama_metni = ""
    ifade = karar.get("matematik_ifadesi", "")

    if not ifade and re.fullmatch(r"[0-9+*/().%\-\s]+", mesaj):
        ifade = mesaj

    if ifade:
        ifade = ifade.replace("%", "/100")
        ok, sonuc_hesap = guvenli_hesapla(ifade)
        if ok:
            yuzde_turu = karar.get("yuzde_turu", "")
            if yuzde_turu == "zam":
                hesaplama_metni = f"Yeni fiyat: {sonuc_hesap} TL"
            elif yuzde_turu == "indirim":
                hesaplama_metni = f"İndirim sonrası fiyat: {sonuc_hesap} TL"
            elif yuzde_turu == "zam_miktari":
                hesaplama_metni = f"Zam miktarı: {sonuc_hesap} TL"
            elif yuzde_turu == "indirim_miktari":
                hesaplama_metni = f"İndirim miktarı: {sonuc_hesap} TL"
                hesaplama_metni = str(sonuc_hesap)

    mantiksal_metni = ""
    ok, sonuc_mantiksal = guvenli_mantiksal_hesapla(mesaj)
    if ok:
        mantiksal_metni = sonuc_mantiksal

    hava_metni = ""

    if hava_verisi and hava_verisi.get("ok"):
        sehir = hava_verisi.get("city", "Bilinmeyen şehir")
        current = hava_verisi.get("current", {}) or {}
        tahmin = hava_verisi.get("forecast", []) or []

        mesaj_kucuk = (mesaj or "").casefold()
        yarin_istegi = any(k in mesaj_kucuk for k in ["yarın", "yarin"])

        secilen_gun = tahmin[1] if yarin_istegi and len(tahmin) > 1 else (
            tahmin[0] if tahmin else {}
        )

        hava_metni = (
            f"📍 {sehir}\n"
            f"🌡️ {current.get('temperature', '—')}°C\n"
            f"🤒 Hissedilen: {current.get('feels_like', '—')}°C\n"
            f"💧 Nem: %{current.get('humidity', '—')}\n"
            f"💨 Rüzgar: {current.get('wind', '—')} km/s\n"
            f"☁️ {current.get('description', '—')}"
        )

        if secilen_gun:
            gun_etiketi = "Yarın" if yarin_istegi else "Bugün"
            hava_metni += (
                "\n\n"
                f"📅 {gun_etiketi}\n"
                f"{secilen_gun.get('min', '—')}°C — {secilen_gun.get('max', '—')}°C\n"
                f"🌧️ Yağış ihtimali: %{secilen_gun.get('rain_probability', '—')}"
            )

    elif hava_verisi and not hava_verisi.get("ok"):
        hava_metni = f"⚠️ {hava_verisi.get('error', 'Hava verisi alınamadı.')}"

    # 🧠 Eagle teknik bilgi bankası — doğrudan cevap
    bilgi_sonuclari = []
    if karar.get("arac") not in ("borc_modulu", "spor_kaynaklari", "hava_api", "guvenli_hesaplama", "kod_analiz") and not autofix_istegi:
        bilgi_sonuclari = bilgi_bankasi_ara(mesaj)

    if bilgi_sonuclari:
        cevap = "🦅 EAGLE BİLGİ BANKASI\n\n" + "\n".join(
            f"• {madde}" for madde in bilgi_sonuclari
        )
        return jsonify({
            "ok": True,
            "answer": cevap,
            "eagle_direct": True,
            "knowledge_base": True,
            "memory_count": len(hafiza_yukle())
        })

    if (
        karar.get("arac") == "bilgi_bankasi"
        and not bilgi_sonuclari
        and not autofix_istegi
    ):
        print("🌐 BİLGİ BANKASI SONUÇSUZ — WEB ARAŞTIRMASINA GEÇİLİYOR", flush=True)
        print(f"🌐 WEB SORGU: {mesaj!r}", flush=True)
        web_verisi = web_arastir(mesaj)
        print(f"🌐 WEB SONUÇ: {len(web_verisi)}", flush=True)

    # 🧠 Öğrenilmiş bilgi doğrudan cevap olarak basılmaz.
    # Öğrenilmiş kayıt üst akışta davranış/routing adayı olarak değerlendirilir.
    if ogrenilmis_karar:
        print(
            "🧠 ÖĞRENİLMİŞ DAVRANIŞ KAYDI HAZIR — ROUTING DEĞERLENDİRMESİ",
            flush=True
        )

    # 🌐 KB sonucu yoksa genel bilgi isteğini web ile tamamla.
    if (
        not bilgi_sonuclari
        and not autofix_istegi
        and karar.get("arac") == "eagle_sohbet"
        and karar.get("intent") != "basit_sohbet"
    ):
        print("🌐 KB SONUÇSUZ — WEB ARAŞTIRMASINA GEÇİLİYOR", flush=True)
        print(f"🌐 WEB SORGU: {mesaj!r}", flush=True)
        web_verisi = web_arastir(mesaj)
        print(f"🌐 WEB SONUÇ: {len(web_verisi)}", flush=True)

    # 🗣️ Genel sohbet modülü
    if karar.get("arac") == "eagle_sohbet" and not web_verisi:
        cevap = genel_sohbet(
            mesaj,
            gecmis=gecmis,
            hafiza=kalici_hafiza,
            karar=karar,
            baglam=akil_plani.get("baglam", {}).get("son_mesaj", "")
        )

        # Başarılı genel sohbeti kalıcı sohbet hafızasına kaydet.
        # 🏟️ İki takım + skor/canlı sonuç sorgularını doğrudan SofaScore'dan çöz.
    if karar.get("intent") == "spor":
        mesaj_kf = str(mesaj or "").casefold().replace("\u0307", "")
        mesaj_kf = re.sub(r"[^\w\s]", " ", mesaj_kf)
        skor_istegi = any(k in mesaj_kf for k in (
            "canlı sonuç", "canli sonuc", "canlı skor", "canli skor",
            "maç sonucu", "mac sonucu", "kaç kaç", "kac kac",
            "skor", "sonuç", "sonuc"
        ))

        if skor_istegi and "maç" in mesaj_kf or skor_istegi and "mac" in mesaj_kf:
            temiz_mesaj = re.sub(
                r"\b(?:maçı|maci|maç|mac|canlı|canli|sonuç|sonuc|skor|kaç|kac|kaç kaç|kac kac|bitti|sonucu)\b",
                " ",
                mesaj_kf,
                flags=re.IGNORECASE
            )
            kelimeler = [x for x in re.split(r"\s+", temiz_mesaj.strip()) if x]

            adaylar = []
            gorulen = set()

            # Tek ve çok kelimeli takım adlarını SofaScore üzerinden dinamik çöz.
            for uzunluk in range(min(4, len(kelimeler)), 0, -1):
                for i in range(len(kelimeler) - uzunluk + 1):
                    parca = " ".join(kelimeler[i:i + uzunluk]).strip()
                    if not parca or parca in gorulen:
                        continue
                    gorulen.add(parca)

                    takim = sofascore_takim_bul(parca)
                    if not takim:
                        continue

                    adaylar.append((i, i + uzunluk, uzunluk, takim))

            secilen = []
            kullanilan_araliklar = []
            for aday in sorted(adaylar, key=lambda x: (x[0], -x[2])):
                bas, son, _, takim = aday
                if any(bas < s and son > b for b, s in kullanilan_araliklar):
                    continue
                if any(takim.get("id") == x.get("id") for x in secilen):
                    continue
                secilen.append(takim)
                kullanilan_araliklar.append((bas, son))
                if len(secilen) == 2:
                    break

            if len(secilen) == 2:
                mac = sofascore_takimlar_arasi_mac_getir(secilen[0], secilen[1])

                if mac:
                    durum = mac.get("durum")
                    ev = mac.get("ev")
                    dep = mac.get("deplasman")
                    ev_skor = mac.get("ev_skor")
                    dep_skor = mac.get("deplasman_skor")

                    if durum in ("inprogress", "live"):
                        cevap = f"{ev} {ev_skor} - {dep_skor} {dep} (canlı)"
                    elif durum == "finished":
                        cevap = f"{ev} {ev_skor} - {dep_skor} {dep}"
                    elif durum == "notstarted":
                        cevap = f"{ev} - {dep} (henüz başlamadı)"
                    else:
                        cevap = f"{ev} - {dep}"

                    return jsonify({
                        "ok": True,
                        "answer": cevap,
                        "web_search": True,
                        "eagle_direct": True,
                        "merkez_motor": False,
                        "memory_count": len(hafiza_yukle())
                    })


    if cevap and str(cevap).strip():
        sohbet_hafizaya_ekle(mesaj, cevap, konu="genel_sohbet")

        return jsonify({
            "ok": True,
            "answer": cevap,
            "eagle_direct": True,
            "memory_count": len(hafiza_yukle())
        })

    # 🏟️ Spor fikstürü — karar/routing dalından bağımsız doğrudan cevapla.
    # Genel "Bugün maç var mı?" sorusu takım belirtmese de mevcut günün
    # spor fikstürünü web sonuçlarından çıkarır.
    if karar.get("intent") == "spor":
        spor_skor_cevap = spor_skoru_direkt_cevapla(
            mesaj,
            web_verisi=web_verisi
        )
        if spor_skor_cevap:
            return jsonify({
                "ok": True,
                "answer": spor_skor_cevap,
                "web_search": True,
                "eagle_direct": True,
                "merkez_motor": False,
                "memory_count": len(hafiza_yukle())
            })

        spor_cevap = spor_fikstur_direkt_cevapla(
            mesaj,
            web_verisi
        )
        if spor_cevap:
            return jsonify({
                "ok": True,
                "answer": spor_cevap,
                "web_search": True,
                "eagle_direct": True,
                "merkez_motor": False,
                "memory_count": len(hafiza_yukle())
            })

    # 🦅 Eagle'ın kendi çözebildiği istekleri doğrudan cevapla
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
            "answer": "🌤️ EAGLE HAVA\n\n" + hava_metni,
            "memory_count": len(hafiza_yukle()),
            "eagle_direct": True
        })

    if hesaplama_metni and karar.get("intent") == "matematik":
        return jsonify({
            "ok": True,
            "answer": hesaplama_metni,
            "eagle_direct": True,
            "memory_count": len(hafiza_yukle())
        })

    # 🇹🇷 Süper Lig puan durumu özel cevabı
    if (
        karar.get("intent") == "spor"
        and super_lig_mi
        and puan_durumu_istegi
        and web_verisi
    ):
        satirlar = [
            "🏟️ EAGLE SPOR",
            "",
            "🇹🇷 SÜPER LİG PUAN DURUMU",
            ""
        ]

        for takim in web_verisi:
            if not isinstance(takim, dict):
                continue

            sira = str(takim.get("sira", "")).strip()
            ad = str(takim.get("takim", "")).strip()
            puan = str(takim.get("puan", "")).strip()

            if sira and ad and puan:
                satirlar.append(f"{sira}. {ad} — {puan} puan")

        if len(satirlar) > 4:
            return jsonify({
                "ok": True,
                "answer": "\n".join(satirlar),
                "web_search": True,
                "eagle_direct": True,
                "spor_puan_durumu": True,
                "memory_count": len(hafiza_yukle())
            })

    # 🧠 EAGLE MERKEZ AKILLI MOTORU
    # Web sonuçları kullanıcıya ham liste olarak verilmez.
    # Merkezi motor gerçek cevabı çıkarmayı dener.
    if web_verisi and karar.get("intent") != "spor":
        try:
            merkez_sonuc = merkez_motor.calistir(
                mesaj=mesaj,
                karar=karar,
                web_verisi=web_verisi,
                sayfa_okuyucu=web_sayfa_oku,
                web_arayici=web_arastir,
            )

            if hasattr(merkez_sonuc, "as_dict"):
                merkez_sonuc = merkez_sonuc.as_dict()

            if isinstance(merkez_sonuc, dict):
                merkez_cevap = str(
                    merkez_sonuc.get(
                        "cevap",
                        merkez_sonuc.get("answer", "")
                    )
                ).strip()

                if (
                    merkez_sonuc.get("ok")
                    and merkez_cevap
                ):
                    return jsonify({
                        "ok": True,
                        "answer": merkez_cevap,
                        "web_search": True,
                        "eagle_direct": True,
                        "merkez_motor": True,
                        "memory_count": len(hafiza_yukle())
                    })

                # 🧠 Eagle cevap çıkaramadıysa Gemini yalnızca son çare.
                if merkez_sonuc.get("gemini_gerekli"):
                    try:
                        import os
                        import requests

                        gemini_key = os.getenv("GEMINI_API_KEY")

                        if gemini_key:
                            kaynaklar = []

                            for kaynak in web_verisi[:6]:
                                if not isinstance(kaynak, dict):
                                    continue

                                baslik = str(
                                    kaynak.get("title", "")
                                ).strip()
                                ozet = str(
                                    kaynak.get("snippet", "")
                                ).strip()
                                url = str(
                                    kaynak.get("url", "")
                                ).strip()

                                parca = " ".join(
                                    x for x in (baslik, ozet)
                                    if x
                                ).strip()

                                if parca:
                                    kaynaklar.append(
                                        f"- {parca}"
                                        + (
                                            f"\\nKaynak: {url}"
                                            if url
                                            else ""
                                        )
                                    )

                            web_icerigi = "\\n\\n".join(kaynaklar)

                            gemini_prompt = (
                                "Sen EagleAI'nin yalnızca son çare olarak "
                                "kullanılan cevap motorusun. Kullanıcının "
                                "sorusunu Türkçe ve doğrudan cevapla. "
                                "Web araştırmasındaki bilgiler dışına "
                                "çıkan güncel iddiaları uydurma. "
                                "Yeterli bilgi yoksa bunu açıkça belirt. "
                                "Gereksiz uzun anlatma.\\n\\n"
                                f"KULLANICI SORUSU:\\n{mesaj}\\n\\n"
                                f"WEB ARAŞTIRMASI:\\n{web_icerigi}"
                            )

                            gemini_url = (
                                "https://generativelanguage.googleapis.com/"
                                "v1beta/models/gemini-2.5-flash:generateContent"
                            )

                            gemini_payload = {
                                "contents": [
                                    {
                                        "parts": [
                                            {"text": gemini_prompt}
                                        ]
                                    }
                                ]
                            }

                            gemini_response = requests.post(
                                gemini_url,
                                params={"key": gemini_key},
                                json=gemini_payload,
                                timeout=30,
                            )

                            if gemini_response.ok:
                                gemini_data = gemini_response.json()
                                adaylar = gemini_data.get(
                                    "candidates",
                                    []
                                )

                                if adaylar:
                                    parts = (
                                        adaylar[0]
                                        .get("content", {})
                                        .get("parts", [])
                                    )

                                    gemini_cevap = " ".join(
                                        str(part.get("text", "")).strip()
                                        for part in parts
                                        if isinstance(part, dict)
                                        and part.get("text")
                                    ).strip()

                                    if gemini_cevap:
                                        return jsonify({
                                            "ok": True,
                                            "answer": gemini_cevap,
                                            "web_search": True,
                                            "eagle_direct": True,
                                            "merkez_motor": False,
                                            "gemini_fallback": True,
                                            "memory_count": len(hafiza_yukle())
                                        })

                            print(
                                "⚠️ Gemini text son çare cevap üretemedi.",
                                flush=True
                            )

                    except Exception as gemini_hatasi:
                        print(
                            "⚠️ Gemini text son çare hatası:",
                            gemini_hatasi,
                            flush=True
                        )

        except Exception as merkez_hatasi:
            print(
                "⚠️ Merkezi motor hatası:",
                merkez_hatasi
            )

        # 🛑 Merkezi motor ve Gemini güvenilir cevap üretemediyse
        # ham/alakasız web sonuçlarını kullanıcıya gösterme.
        return jsonify({
            "ok": True,
            "answer": (
                "🦅 Web araştırması yaptım ancak güvenilir ve "
                "doğrudan bir cevap çıkaramadım."
            ),
            "web_search": True,
            "eagle_direct": True,
            "merkez_motor": False,
            "memory_count": len(hafiza_yukle())
        })


    # 🦅 Hiçbir özel araç veya web sonucu yoksa Eagle doğrudan cevap verir
    return jsonify({
        "ok": True,
        "answer": (
            "🦅 Bu isteği kendi araçlarımla işleyemedim. "
            "Sorunu biraz daha açık yazarsan tekrar deneyebilirim."
        ),
        "eagle_direct": True,
        "web_search": False,
        "memory_count": len(hafiza_yukle()),
        "live_sports_debug": live_sports_debug
    })


if __name__ == "__main__":

    print("=" * 40)
    print("🦅 EAGLE-AI API")
    print("=" * 40)
    print("API: http://127.0.0.1:5001")
    print("Durum: http://127.0.0.1:5001/api/durum")
    print("Hafıza: http://127.0.0.1:5001/api/hafiza")
    print("=" * 40)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
