"""EagleAI niyet sınıflandırma regresyon testleri. Kökten çalıştır."""
from eagle_karar_sohbet import (
    konu_adi_mi, yazim_normalle, erken_sohbet_karari,
)


def test_konu_adlari():
    for ad in ("Jules Verne", "Franz Kafka", "Atatürk", "Jules Verne?"):
        assert konu_adi_mi(ad), ad


def test_konu_adi_degil():
    for m in ("merhaba", "Tamam", "Evet", "Verne anlat", "Bunu anlat misin"):
        assert not konu_adi_mi(m), m


def test_yazim_normalizasyonu():
    assert yazim_normalle("Verirmisin") == "verir misin"
    assert yazim_normalle("verir misin?") == "verir misin"


def test_selam_hala_calisir():
    for m in ("merhaba", "Selam", "iyi akşamlar", "sen kimsin"):
        assert erken_sohbet_karari(m, {}) is not None, m


def test_selam_ve_konu_basit_sohbet_degil():
    assert erken_sohbet_karari("Selamlar Jules Verne nasıl biri", {}) is None
    assert erken_sohbet_karari("Jules Verne", {}) is None


def test_karar_motoru_web_arastirma():
    from eagle_api import eagle_karar_motoru
    for ad in ("Jules Verne", "Franz Kafka", "Atatürk"):
        assert eagle_karar_motoru(ad).get("arac") == "web_arastirma", ad


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"[OK] {name}")
        except Exception as exc:
            failed += 1
            print(f"[HATA] {name}: {type(exc).__name__}: {exc}")
    print(f"Sonuç: {len(tests)-failed}/{len(tests)} başarılı")
    raise SystemExit(1 if failed else 0)
