# -*- coding: utf-8 -*-
"""eagle_finansal_analiz.py testleri. Çalıştırma: python eagle_finansal_analiz_test.py"""
import sys
from eagle_finansal_analiz import finansal_analiz_cevabi, finansal_gorev_mu

SENARYO = ("Bir şirketin gelirleri %30 artarken nakit akışı %40 düşmüş, kısa vadeli borçları %50 yükselmiş "
           "ve stokları %60 birikmiş. Bu çelişkiyi analiz et. Olası nedenleri, finansal riskleri, kontrol "
           "edilmesi gereken göstergeleri ve 90 günlük uygulanabilir çözüm planını hazırla. Kod yazmadan açıkla.")
TERS = ("Bir şirketin gelirleri %30 düşerken nakit akışı %40 artmış, kısa vadeli borçları %50 azalmış "
        "ve stokları %60 erimiş. Bu durumu analiz et.")
BASARI = []; HATA = []

def test(ad, fn):
    try:
        fn(); BASARI.append(ad); print("[OK]", ad)
    except AssertionError as e:
        HATA.append(ad); print("[HATA]", ad, "->", e)

def t_mevcut_testin_sartlari():
    c, g = finansal_analiz_cevabi(SENARYO)
    for s in ("DSO", "DIO", "DPO", "90 günlük", "Likidite"):
        assert s in c, f"'{s}' yok"
    assert g >= 0.9, g

def t_ters_senaryo_farkli():
    c1, _ = finansal_analiz_cevabi(SENARYO)
    c2, g2 = finansal_analiz_cevabi(TERS)
    assert c2 and c1 != c2, "ters senaryo aynı metni verdi"
    assert "büyüme nakde dönüşmüyor" not in c2, "ters senaryoda yanlış teşhis"
    assert "artıyor: artış satış gücünden değil" in c2 or "nakit akışı artıyor" in c2.lower() or "Gelir düşerken nakit" in c2
    assert "▼ düşüş (%30)" in c2 and "▲ artış (%40)" in c2, "yön/yüzde okunamadı"
    assert g2 >= 0.9

def t_rakamsiz_kelime_sorusu():
    c, g = finansal_analiz_cevabi("Gelir, nakit akışı ve borç hakkında neden analiz yapılır?")
    assert c == "" and g == 0.0

def t_kod_istegi_reddedilir():
    for m in ("Python ile gelir ve nakit akışı düşerken borcu artan şirket için risk analiz sistemi geliştir.",
              "Gelir arttı nakit düştü, bunun için bir program yaz ve analiz et."):
        c, _ = finansal_analiz_cevabi(m)
        assert c == "", m

def t_kod_yazmadan_calisir():
    c, _ = finansal_analiz_cevabi("Gelir arttı, nakit düştü. Kod yazmadan analiz et.")
    assert c.startswith("## Finansal durum analizi")

def t_iki_gosterge_dusuk_guven():
    c, g = finansal_analiz_cevabi("Gelirler %20 arttı, nakit %10 düştü, neden olabilir?")
    assert c and 0.7 <= g < 0.9, g

def t_rakamsiz_yon_guven_dusuk():
    _, g1 = finansal_analiz_cevabi("Gelir arttı, nakit düştü, borç yükseldi, stok birikti. Analiz et.")
    _, g2 = finansal_analiz_cevabi(SENARYO)
    assert g1 < g2, (g1, g2)

def t_gider_gelir_karsilastirma():
    c, _ = finansal_analiz_cevabi("Gelirler %10 arttı, giderler %25 arttı. Neden kâr düştü, analiz et.")
    assert "aşıyor" in c, "gider artışı gelirden yüksekken uyarı yok"
    c2, _ = finansal_analiz_cevabi("Gelirler %25 arttı, giderler %10 arttı. Analiz et.")
    assert "altında" in c2 and "aşıyor" not in c2

def t_yazim_varyasyonlari():
    c, g = finansal_analiz_cevabi("GELİRLER YÜZDE 30 ARTARKEN NAKİT AKIŞI YÜZDE 40 DÜŞTÜ, STOKLAR ARTTI. ANALİZ ET")
    assert "▲ artış (%30)" in c and "▼ düşüş (%40)" in c and "Stok: ▲" in c, c[:300]

def t_ortak_yon_ve_sifat():
    c, _ = finansal_analiz_cevabi("Stok ve borç arttı, nakit azaldı. Risklerini değerlendir.")
    assert "Stok: ▲" in c and "Borç: ▲" in c and "Nakit akışı: ▼" in c

def t_gorev_turu_niyet_kelimesi_gerektirmez():
    c1, _ = finansal_analiz_cevabi("Gelir arttı, nakit düştü.")
    c2, _ = finansal_analiz_cevabi("Gelir arttı, nakit düştü.", gorev_turu="finansal_analiz")
    assert c1 == "" and c2

def t_gorev_mu():
    assert finansal_gorev_mu(SENARYO) is True
    assert finansal_gorev_mu("Bugün dolar kaç TL?") is False
    assert finansal_gorev_mu("Python ile finansal risk analiz sistemi geliştir, gelir ve nakit düşüyor") is False

def t_alakasiz_mesajlar():
    for m in ("Merhaba nasılsın", "İskoçya hakkında bilgi verir misin",
              "Giderek artan bir ilgi var, bunu açıkla", "Galatasaray maçı kaç kaç bitti"):
        assert finansal_analiz_cevabi(m)[0] == "", m

def t_veriyle_celismeyen_nedenler():
    c, _ = finansal_analiz_cevabi(TERS)   # borç AZALIYOR
    assert "Yeni borçlanma" not in c, "borç azalırken 'yeni borçlanma' nedeni yazıldı"
    c2, _ = finansal_analiz_cevabi("Gelir düştü, nakit arttı, borç arttı. Analiz et.")
    assert "Yeni borçlanma" in c2

def t_deterministik():
    assert finansal_analiz_cevabi(SENARYO) == finansal_analiz_cevabi(SENARYO)

def t_tekil_gosterge_fallback():
    c, _ = finansal_analiz_cevabi("Marj düştü ve gider arttı, analiz et.")
    assert "Kâr marjı düşüyor" in c and "Gider artarken gelir artmıyor" in c

for ad, fn in [
    ("Mevcut regresyon testinin şartları (DSO/DIO/DPO/90 günlük/Likidite, güven>=0.9)", t_mevcut_testin_sartlari),
    ("Ters senaryo farklı ve doğru teşhis üretir", t_ters_senaryo_farkli),
    ("Rakamsız kelime sorusu analiz üretmez", t_rakamsiz_kelime_sorusu),
    ("Gerçek kod isteği reddedilir", t_kod_istegi_reddedilir),
    ("'Kod yazmadan' olumsuzlaması çalışır", t_kod_yazmadan_calisir),
    ("İki gösterge düşük güven", t_iki_gosterge_dusuk_guven),
    ("Rakamsız yön okuma güveni düşürür", t_rakamsiz_yon_guven_dusuk),
    ("Gider-gelir yüzdeleri karşılaştırılır", t_gider_gelir_karsilastirma),
    ("Büyük harf ve 'yüzde N' yazımı", t_yazim_varyasyonlari),
    ("'Stok ve borç arttı' ortak yön", t_ortak_yon_ve_sifat),
    ("Görev türü niyet kelimesini gerektirmez", t_gorev_turu_niyet_kelimesi_gerektirmez),
    ("finansal_gorev_mu sınıflandırması", t_gorev_mu),
    ("Alakasız mesajlarda sessiz kalır", t_alakasiz_mesajlar),
    ("Nedenler verilen yönlerle çelişmez", t_veriyle_celismeyen_nedenler),
    ("Deterministik çıktı", t_deterministik),
    ("Tekil gösterge değerlendirmesi", t_tekil_gosterge_fallback),
]:
    test(ad, fn)

print(f"\nTOPLAM: {len(BASARI) + len(HATA)}  BAŞARILI: {len(BASARI)}  HATALI: {len(HATA)}")
sys.exit(1 if HATA else 0)
