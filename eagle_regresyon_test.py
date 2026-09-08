import ast
import json
import sys
import traceback
from pathlib import Path

BASARILI = 0
HATALI = 0


def test(ad, fonksiyon):
    global BASARILI, HATALI

    try:
        sonuc = fonksiyon()
        if sonuc is False:
            raise AssertionError("Test sonucu False döndü")

        print(f"[OK] {ad}")
        BASARILI += 1
    except Exception as e:
        print(f"[HATA] {ad}")
        print(f"       {type(e).__name__}: {e}")
        HATALI += 1


def bilgi_bankasi_test():
    with open("eagle_bilgi.json", encoding="utf-8") as f:
        bilgi = json.load(f)

    assert isinstance(bilgi, dict)

    python = bilgi.get("python", {})
    assert isinstance(python, dict)

    dict_maddeleri = []
    for maddeler in python.values():
        if isinstance(maddeler, list):
            dict_maddeleri.extend(
                m for m in maddeler if isinstance(m, dict)
            )

    assert len(dict_maddeleri) >= 49, (
        f"Yeni Python kayıtları eksik: {len(dict_maddeleri)}"
    )

    print(f"       Python soru/cevap kaydı: {len(dict_maddeleri)}")


def python_syntax_test():
    kodlar = [
        "x = 10\nprint(x)",
        "for i in range(5):\n    print(i)",
        "def topla(a, b):\n    return a + b",
        "liste = [x * 2 for x in range(5)]",
        "try:\n    x = 10 / 0\nexcept ZeroDivisionError:\n    print('hata')",
    ]

    for kod in kodlar:
        ast.parse(kod)
        compile(kod, "<regresyon>", "exec")


def konu_eslesme_test():
    import eagle_api

    sonuc = eagle_api.bilgi_bankasi_ara("Python'da zip nedir?")
    assert sonuc, "zip sorusuna cevap bulunamadı"

    sonuc = eagle_api.bilgi_bankasi_ara("Python'da lambda nedir?")
    assert sonuc, "lambda sorusuna cevap bulunamadı"

    sonuc = eagle_api.bilgi_bankasi_ara("Python'da NameError nedir?")
    assert sonuc, "NameError sorusuna cevap bulunamadı"


def matematik_test():
    import eagle_api

    # Matematik bilgi bankası kaydı
    sonuc = eagle_api.bilgi_bankasi_ara("12 ve 18'in EBOB'u kaçtır?")
    assert sonuc, "EBOB bilgi bankası cevabı bulunamadı"
    assert any("6" in str(x) for x in sonuc), "EBOB sonucu 6 bekleniyordu"

    # Doğal dil matematik kararları
    testler = [
        (
            "Bir sayının %20'si 36 ise bu sayı kaçtır?",
            "36 * 100 / 20",
            "ters_yuzde",
        ),
        (
            "200 TL'lik ürüne %10 zam yapılırsa kaç TL olur?",
            "200 + (200 * 10 / 100)",
            "zam",
        ),
        (
            "200 TL'lik üründe %20 indirim yapılırsa kaç TL olur?",
            "200 - (200 * 20 / 100)",
            "indirim",
        ),
    ]

    for soru, beklenen_ifade, beklenen_tur in testler:
        karar = eagle_api.eagle_karar_motoru(soru, [])
        assert karar is not None, f"Karar üretilemedi: {soru}"
        assert karar.get("intent") == "matematik", f"Intent hatalı: {soru}"
        assert karar.get("matematik_ifadesi") == beklenen_ifade, (
            f"Matematik ifadesi hatalı: {soru}"
        )
        assert karar.get("yuzde_turu") == beklenen_tur, (
            f"Yüzde türü hatalı: {soru}"
        )


def karar_motoru_test():
    import eagle_api

    sorular = [
        "Python'da decorator nedir?",
        "Python'da pathlib nedir?",
        "Python'da async await nedir?",
    ]

    for soru in sorular:
        sonuc = eagle_api.eagle_karar_motoru(soru, [])
        assert sonuc is not None, f"Karar motoru sonuç üretmedi: {soru}"


def kod_analiz_import_test():
    import eagle_kod_analiz_motoru
    assert eagle_kod_analiz_motoru is not None


def autofix_import_test():
    import eagle_autofix
    assert eagle_autofix is not None


def boolean_autofix_test():
    from eagle_autofix import EagleAutoFixEngine

    test_file = Path("boolean_regresyon_gecici.py")

    kod = "\n".join([
        "def kontrol_et(aktif):",
        "    if aktif == True:",
        '        print("Aktif")',
        "    else:",
        '        print("Pasif")',
        "",
        "kontrol_et(True)",
        "kontrol_et(False)",
        "",
    ])

    test_file.write_text(kod, encoding="utf-8")

    try:
        motor = EagleAutoFixEngine()
        sonuc = motor.repair_loop(test_file)

        assert sonuc.get("success") is True, (
            f"Boolean AutoFix başarısız: {sonuc.get('reason')}"
        )

        duzeltilmis = test_file.read_text(encoding="utf-8")

        assert "if aktif:" in duzeltilmis, (
            "Boolean karşılaştırması sadeleştirilmedi"
        )

        assert "if aktif == True:" not in duzeltilmis, (
            "Eski 'if aktif == True:' kodu hâlâ mevcut"
        )

        compile(duzeltilmis, "<boolean_regresyon>", "exec")

    finally:
        if test_file.exists():
            test_file.unlink()


def api_fonksiyon_test():
    import eagle_api

    assert hasattr(eagle_api, "sohbet")
    assert hasattr(eagle_api, "app")


print("===== EAGLEAI REGRESYON TEST =====")
print()

test("Bilgi bankası JSON ve 49 yeni Python kaydı", bilgi_bankasi_test)
test("Python syntax temel testleri", python_syntax_test)
test("Python konu eşleşmesi", konu_eslesme_test)
test("Matematik bilgi bankası", matematik_test)
test("Karar motoru", karar_motoru_test)
test("Kod analiz motoru", kod_analiz_import_test)
test("AutoFix", autofix_import_test)
test("BooleanComparison AutoFix", boolean_autofix_test)
test("API /api/sohbet altyapısı", api_fonksiyon_test)

print()
print("===== SONUÇ =====")
print(f"TOPLAM: {BASARILI + HATALI}")
print(f"BAŞARILI: {BASARILI}")
print(f"HATALI: {HATALI}")

if HATALI == 0:
    print("DURUM: REGRESYON TESTİ OK")
    sys.exit(0)
else:
    print("DURUM: REGRESYON TESTİ HATALI")
    sys.exit(1)
