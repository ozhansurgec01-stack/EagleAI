"""EagleAI root-cause regression checks. Run from repository root."""
from unittest.mock import patch


def test_franz_kafka_biyografi():
    from eagle_merkez_motoru import EagleMerkezMotoru

    hermann = (
        "Hermann, biyografi yazarı Stanley Corngold tarafından iri, bencil, "
        "zorba bir iş insanı ve Franz Kafka tarafından güçte, sağlıkta "
        "gerçek bir Kafka olarak tanımlanmıştır."
    )
    franz = (
        "Franz Kafka, 1883 yılında Prag'da doğmuş Almanca yazan bir yazardır. "
        "Dönüşüm ve Dava en tanınmış eserleri arasındadır. "
        "Kafka, 1924 yılında hayatını kaybetmiştir."
    )
    cevap, guven = EagleMerkezMotoru.genel_web_cevabi(
        "Franz Kafka hakkında bilgi",
        [
            {"title": "Hermann Kafka", "snippet": hermann, "url": "https://test.example/hermann"},
            {"title": "Franz Kafka", "snippet": franz, "url": "https://test.example/franz"},
        ],
        sayfa_okuyucu=lambda url: hermann if "hermann" in url else franz,
    )
    assert cevap and "1883" in cevap and "Prag" in cevap, (cevap, guven)
    assert "Hermann" not in cevap, cevap
    assert guven >= 0.75, guven


def test_altin_hedefli_arama_dort_genel_sonuc_ile_de_atlanmaz():
    from eagle_merkez_motoru import EagleMerkezMotoru

    cagrilar = []
    def arama(sorgu, limit=8):
        cagrilar.append(sorgu)
        return [{"url": f"https://news{i}.example", "title": "Maaş haberi", "snippet": "Zam haberi"} for i in range(8)]

    ilk = [{"url": f"https://genel{i}.example", "title": "Genel sonuç", "snippet": "İlgisiz"} for i in range(4)]
    with patch("requests.get", side_effect=RuntimeError("test için kapalı")):
        cevap, guven = EagleMerkezMotoru().genel_altin_cevabi(
            "güncel altın fiyatları", ilk, web_arayici=arama
        )
    assert len(cagrilar) == 1 and "altın fiyatları bugün" in cagrilar[0].casefold(), cagrilar
    assert cevap == "" and guven == 0.0, (cevap, guven)


def test_finans_sorgularina_gorsel_galerisi_eklenmez():
    from eagle_api import _eagle_gorsel_galerisi_uygun_mu
    assert not _eagle_gorsel_galerisi_uygun_mu("güncel altın fiyatları", None)
    assert not _eagle_gorsel_galerisi_uygun_mu("dolar kuru", None)
    assert _eagle_gorsel_galerisi_uygun_mu("Franz Kafka hakkında bilgi", None)


if __name__ == "__main__":
    tests = [
        ("Franz Kafka biyografi", test_franz_kafka_biyografi),
        ("Altın hedefli arama", test_altin_hedefli_arama_dort_genel_sonuc_ile_de_atlanmaz),
        ("Finans görsel galerisi", test_finans_sorgularina_gorsel_galerisi_eklenmez),
    ]
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
