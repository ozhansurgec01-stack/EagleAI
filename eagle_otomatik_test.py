from pathlib import Path
import ast
import sys

from eagle_autofix import EagleAutoFixEngine


TESTLER = [
    {
        "ad": "BooleanComparison",
        "kod": """def kontrol_et(aktif):
    if aktif == True:
        print("Aktif")
    else:
        print("Pasif")

kontrol_et(True)
kontrol_et(False)
""",
        "beklenen": "if aktif:",
        "olmamasi": "if aktif == True:",
    },
    {
        "ad": "BareExcept",
        "kod": """try:
    print("test")
except:
    print("hata")
""",
        "beklenen": "except Exception:",
        "olmamasi": "except:",
    },
    {
        "ad": "UnusedVariable",
        "kod": """def test():
    kullanilmayan = 42
    print("tamam")

test()
""",
        "beklenen": 'print("tamam")',
        "olmamasi": "kullanilmayan = 42",
    },
    {
        "ad": "MissingColon",
        "kod": """def test()
    print("tamam")

test()
""",
        "beklenen": 'def test():',
        "olmamasi": "def test()\n",
    },
    {
        "ad": "ReservedKeyword",
        "kod": """for class in [1, 2]:
    print(class)
""",
        "beklenen": "for class_deger in [1, 2]:",
        "olmamasi": "for class in [1, 2]:",
    },
    {
        "ad": "UnclosedParen",
        "kod": """print("test"
""",
        "beklenen": 'print("test")',
        "olmamasi": 'print("test"\n',
    },
    {
        "ad": "OffByOneRange",
        "kod": """liste = [1, 2, 3]
for i in range(len(liste) - 1):
    print(liste[i])
""",
        "beklenen": "range(len(liste))",
        "olmamasi": "range(len(liste) - 1)",
    },
]


def sonuc_yaz(ad, ok, detay=""):
    durum = "OK" if ok else "HATA"
    print(f"[{durum}] {ad}")
    if detay:
        print(f"      {detay}")


def test_autofix(test):
    ad = test["ad"]
    tmp = Path(".eagle_otomatik_test_tmp")
    tmp.mkdir(exist_ok=True)
    hedef = tmp / f"{ad.lower()}.py"
    orijinal = test["kod"]
    hedef.write_text(orijinal, encoding="utf-8")

    try:
        motor = EagleAutoFixEngine()
        sonuc = motor.repair_loop(hedef)

        if not sonuc.get("success"):
            sonuc_yaz(
                ad,
                False,
                f"AutoFix başarısız: {sonuc.get('reason')}",
            )
            return False

        duzeltilmis = hedef.read_text(encoding="utf-8")

        if duzeltilmis == orijinal:
            sonuc_yaz(
                ad,
                False,
                "Dosyada gerçek bir kod değişikliği yapılmadı.",
            )
            return False

        if test["beklenen"] not in duzeltilmis:
            sonuc_yaz(
                ad,
                False,
                "Beklenen düzeltilmiş kod bulunamadı.",
            )
            return False

        if test["olmamasi"] in duzeltilmis:
            sonuc_yaz(
                ad,
                False,
                "Eski hatalı kod hâlâ dosyada.",
            )
            return False

        try:
            compile(duzeltilmis, str(hedef), "exec")
        except SyntaxError as e:
            sonuc_yaz(
                ad,
                False,
                f"Düzeltilmiş kod syntax hatası veriyor: {e}",
            )
            return False

        fixed_code = sonuc.get("fixed_code")
        if not fixed_code:
            sonuc_yaz(
                ad,
                False,
                "Sonuç içinde fixed_code yok.",
            )
            return False

        if fixed_code.strip() != duzeltilmis.strip():
            sonuc_yaz(
                ad,
                False,
                "fixed_code ile dosyadaki düzeltilmiş kod aynı değil.",
            )
            return False

        sonuc_yaz(
            ad,
            True,
            "Gerçek kod değişikliği + fixed_code + syntax testi başarılı.",
        )
        return True

    except Exception as e:
        sonuc_yaz(ad, False, f"Test hatası: {e}")
        return False


def test_report_only():
    kod = """def test():
    liste = []
    sifir = 0

    if liste:
        print(liste[0])

    if sifir != 0:
        print(10 / sifir)

    print("tamam")

test()
"""

    try:
        from eagle_kod_analiz_motoru import EagleKodAnalizMotoru

        motor = EagleKodAnalizMotoru()
        bulgular = motor.analiz_et(kod)
        turler = {b.get("tur") for b in bulgular}

        beklenen = {"EmptyListAccess", "ZeroDivision"}

        eksik = beklenen - turler

        if eksik:
            sonuc_yaz(
                "Report-only analizler",
                False,
                f"Eksik bulgular: {sorted(eksik)}",
            )
            return False

        sonuc_yaz(
            "Report-only analizler",
            True,
            "EmptyListAccess / ZeroDivision analiz katmanında mevcut.",
        )
        return True

    except Exception as exc:
        sonuc_yaz(
            "Report-only analizler",
            False,
            str(exc),
        )
        return False


def main():
    print("===== EAGLEAI OTOMATİK AUTOFIX TEST =====")
    print()

    basarili = 0
    hatali = 0

    for test in TESTLER:
        if test_autofix(test):
            basarili += 1
        else:
            hatali += 1

    if test_report_only():
        basarili += 1
    else:
        hatali += 1

    print()
    print("===== SONUÇ =====")
    print(f"TOPLAM: {basarili + hatali}")
    print(f"BAŞARILI: {basarili}")
    print(f"HATALI: {hatali}")

    if hatali == 0:
        print("DURUM: OTOMATİK AUTOFIX TESTİ OK")
        return 0

    print("DURUM: OTOMATİK AUTOFIX TESTİ HATALI")
    return 1


if __name__ == "__main__":
    sys.exit(main())
