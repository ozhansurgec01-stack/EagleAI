from pathlib import Path
import py_compile
import tempfile
import re
import sys

DOSYA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("eagle_api.py")


def hata_bilgisi(path):
    try:
        py_compile.compile(str(path), doraise=True)
        return None, None
    except py_compile.PyCompileError as e:
        text = str(e)
        m = re.search(r"line (\d+)", text)
        return (int(m.group(1)) if m else None), text


def test_et(lines):
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False
    ) as f:
        f.write("\n".join(lines) + "\n")
        tmp = Path(f.name)

    try:
        return hata_bilgisi(tmp)
    finally:
        tmp.unlink(missing_ok=True)


def duzelt():
    lines = DOSYA.read_text().splitlines()

    print(f"🔎 Otomatik Python hata taraması: {DOSYA}")

    for tur in range(50):
        satir_no, hata = hata_bilgisi(DOSYA)

        if satir_no is None:
            print("✅ DOSYA HATASIZ: Python derleme kontrolü geçti.")
            return True

        idx = satir_no - 1

        if idx < 0 or idx >= len(lines):
            print("❌ Hata satırı bulunamadı.")
            return False

        mevcut = lines[idx]
        kod = mevcut.lstrip()

        print()
        print(f"⚠️ Tur {tur + 1}")
        print(f"📍 Satır: {satir_no}")
        print(f"🧩 Kod: {kod}")

        adaylar = []

        # 0'dan 20 boşluğa kadar bütün seviyeleri dene.
        for bosluk in range(0, 21):
            aday = lines.copy()
            aday[idx] = (" " * bosluk) + kod

            yeni_satir, yeni_hata = test_et(aday)

            # Dosya tamamen düzeldiyse en iyi sonuç.
            if yeni_satir is None:
                adaylar.append((0, bosluk, aday))
                continue

            # Hata daha aşağı bir satıra taşındıysa ilerleme var.
            ilerleme = yeni_satir - satir_no

            if ilerleme > 0:
                adaylar.append((-ilerleme, bosluk, aday))

        if not adaylar:
            print("❌ Bu hata için otomatik ve güvenli bir çözüm bulunamadı.")
            print(hata)
            return False

        adaylar.sort(key=lambda x: (x[0], x[1]))
        _, secilen_bosluk, yeni_lines = adaylar[0]

        eski_bosluk = len(mevcut) - len(kod)

        print(
            f"🔧 Girinti otomatik değiştiriliyor: "
            f"{eski_bosluk} → {secilen_bosluk} boşluk"
        )

        lines = yeni_lines
        DOSYA.write_text("\n".join(lines) + "\n")

    print("❌ 50 otomatik düzeltme sonunda dosya hâlâ hatalı.")
    return False


if __name__ == "__main__":
    sys.exit(0 if duzelt() else 1)
