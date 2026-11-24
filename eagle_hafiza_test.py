"""EagleAI hafıza eşleşmesi testleri. Geçici dizinde çalışır."""
import json, os, tempfile
import eagle_cevap_motoru as m

NOTLAR = [
    "EagleMusic benim Android müzik çalar projem.",
    "/expert → Uzman seviyesinde yanıtlar ver",
    "/eli5 → 5 yaşında birine anlatır gibi açıkla",
]


def _gecici(fn):
    eski = os.getcwd()
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "eagle_ai_memory.json"), "w", encoding="utf-8") as f:
            json.dump({"kullanici": NOTLAR}, f, ensure_ascii=False)
        os.chdir(d)
        try:
            return fn()
        finally:
            os.chdir(eski)


def test_proje_sorulari_eslesir():
    def calis():
        for s in ("EagleMusic projem neydi?", "Hangi projemden bahsetmiştim?",
                  "Hangi projeydi?"):
            assert m._hafizadan_bilgi_cek(s.casefold()) == NOTLAR[0], s
    _gecici(calis)


def test_komut_satirlari_hafiza_sayilmaz():
    def calis():
        for s in ("daha önce expert hatırlıyor musun",
                  "daha önce eli5 hatırlıyor musun"):
            assert m._hafizadan_bilgi_cek(s) is None, s
    _gecici(calis)


def test_konu_istekleri_hafizaya_dusmez():
    def calis():
        for s in ("Franz Kafka ve yolda ağlayan kızın hikayesi",
                  "Jules Verne", "Selamlar Jules Verne nasıl biri"):
            assert not m._hafiza_uygun_mu(s.casefold()), s
            assert "Hafızamda" not in str(m._yerel_cevap(s)), s
    _gecici(calis)


def test_hafiza_sorusu_kayitli_bilgiyi_icerir():
    def calis():
        cevap = str(m._yerel_cevap("Hangi projemden bahsetmiştim?"))
        assert "EagleMusic" in cevap, cevap
    _gecici(calis)


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
