"""Hafızada olmayan, araştırılabilir konu isteği web araştırmasına gitmeli."""
from eagle_api import eagle_karar_motoru, web_arastirma_gerekli

ARASTIRILACAK = (
    "Franz Kafka ve yolda ağlayan kızın hikayesi",
    "Franz Kafka ve yolda ağlayan kızın hikâyesi",
)
ARASTIRILMAYACAK = (
    "merhaba", "Nasılsınız?", "bana bir hikaye anlat",
    "Bana kedimin hikayesi lazım",
    "EagleMusic projem neydi?", "Hangi projemden bahsetmiştim?",
)


def test_arastirilabilir_konu_web_arastirmasina_gider():
    for m in ARASTIRILACAK:
        assert web_arastirma_gerekli(m), m
        assert eagle_karar_motoru(m).get("arac") == "web_arastirma", m


def test_sohbet_ve_hafiza_sorulari_web_e_gitmez():
    for m in ARASTIRILMAYACAK:
        assert eagle_karar_motoru(m).get("arac") != "web_arastirma", m


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
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
