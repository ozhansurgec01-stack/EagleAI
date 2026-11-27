#!/usr/bin/env python3
"""Eagle merkez motoru için bağımsız regresyon testleri (ağ bağlantısı gerektirmez)."""
from __future__ import annotations

import importlib.util
import sys
import types
from unittest.mock import patch
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


BASE = Path(__file__).resolve().parent
SOURCE = BASE / "eagle_merkez_motoru.py"

# Test sırasında dış servisleri devre dışı bırak.
afet = types.ModuleType("eagle_afet_koordinasyon")
afet.afet_koordinasyon_cevabi = lambda mesaj: ""
finans = types.ModuleType("eagle_finansal_analiz")
finans.finansal_analiz_cevabi = lambda *args, **kwargs: ("", 0.0)
requests = types.ModuleType("requests")


class FakeResponse:
    status_code = 503

    def json(self):
        return {}


requests.get = lambda *args, **kwargs: FakeResponse()

sanal = types.ModuleType("eagle_sanalkuyumculuk")
sanal.API_URL = "https://test.invalid/sanal"
sanal.parse_payload = lambda payload: []
altin = types.ModuleType("eagle_altinkaynak")
altin.API_URL = "https://test.invalid/altin"
altin.parse_payload = lambda payload: []

spec = importlib.util.spec_from_file_location("eagle_motor_regresyon", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Motor dosyası yüklenemedi: {SOURCE}")
motor_mod = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {
    "eagle_afet_koordinasyon": afet,
    "eagle_finansal_analiz": finans,
    "requests": requests,
    "eagle_sanalkuyumculuk": sanal,
    "eagle_altinkaynak": altin,
    spec.name: motor_mod,
}):
    spec.loader.exec_module(motor_mod)

motor = motor_mod.EagleMerkezMotoru()
BUGUN = datetime.now(ZoneInfo("Europe/Istanbul")).date().isoformat()


def test_html_tablo_guncel_tarih_olmadan_kullanilmaz():
    try:
        import bs4  # noqa: F401
    except ImportError:
        print("[ATLA] bs4 kurulu değil; HTML tablo tarih testi atlandı")
        return

    gercek_okuyucu = motor_mod.altin_tablo_oku

    class HtmlResponse:
        status_code = 200

        def __init__(self, html):
            self.text = html

    tarih_gorunur = datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%d.%m.%Y")
    html_guncel = (
        f"<p>Son güncelleme: {tarih_gorunur}</p><table>"
        "<tr><td>Çeyrek Altın</td><td>Alış 5.000,00 TL</td>"
        "<td>Satış 5.200,00 TL</td></tr></table>"
    )
    requests.get = lambda *args, **kwargs: HtmlResponse(html_guncel)
    with patch.dict(sys.modules, {"requests": requests}):
        guncel = gercek_okuyucu("https://altinveri.com/altin")
    assert guncel and guncel[0].get("tarih") == BUGUN, guncel

    html_tarihsiz = (
        "<p>Çeyrek altın fiyatları</p><table>"
        "<tr><td>Çeyrek Altın</td><td>Alış 5.000,00 TL</td>"
        "<td>Satış 5.200,00 TL</td></tr></table>"
    )
    requests.get = lambda *args, **kwargs: HtmlResponse(html_tarihsiz)
    with patch.dict(sys.modules, {"requests": requests}):
        tarihsiz = gercek_okuyucu("https://altinveri.com/altin")
    assert not tarihsiz, tarihsiz

    html_eski = (
        "<p>Son güncelleme: 01.01.2020</p><table>"
        "<tr><td>Çeyrek Altın</td><td>Alış 5.000,00 TL</td>"
        "<td>Satış 5.200,00 TL</td></tr></table>"
    )
    requests.get = lambda *args, **kwargs: HtmlResponse(html_eski)
    with patch.dict(sys.modules, {"requests": requests}):
        eski = gercek_okuyucu("https://altinveri.com/altin")
    assert not eski, eski

    motor_mod.altin_tablo_oku = gercek_okuyucu
    requests.get = lambda *args, **kwargs: FakeResponse()


def test_franz_kafka_biyografisi():
    soru = "Franz Kafka hakkında bilgi"
    iyi_1 = "Franz Kafka, 1883 yılında Prag'da doğmuş Almanca yazan bir yazardır."
    iyi_2 = "Franz Kafka'nın en tanınmış eserleri arasında Dönüşüm ve Dava bulunur."
    ilgisiz = (
        "Hermann, biyografi yazarı Stanley Corngold tarafından iri, bencil ve "
        "zorba bir iş insanı olarak tanımlanmıştır; Franz Kafka da babasını "
        "güçlü bir figür olarak anlatmıştır."
    )
    cevap, guven = motor.genel_web_cevabi(soru, [{
        "title": "Franz Kafka - Biyografi",
        "snippet": f"{iyi_1} {iyi_2} {ilgisiz}",
        "url": "https://example.org/franz-kafka",
    }])
    assert guven >= 0.75, (cevap, guven)
    assert "Franz Kafka" in cevap
    assert "Hermann" not in cevap, cevap
    assert "Dönüşüm" in cevap, cevap
    assert motor_mod.EagleMerkezMotoru._genel_bilgi_kisi_cumlesi_mi(
        "Atlas Okyanusu hakkında bilgi",
        "Atlas Okyanusu, dünyanın en büyük okyanuslarından biridir.",
    )


def altin_kayit(url, alis, satis, tarih=BUGUN):
    return {
        "urun": "Çeyrek Altın",
        "alis": alis,
        "satis": satis,
        "url": url,
        "tarih": tarih,
    }


def gold_call(second_buy, second_sell, second_url="https://www.ahaber.com.tr/finans/altin",
              second_date=BUGUN):
    def fake_table_reader(url):
        if "altinveri.com/" in url:
            return [altin_kayit(url, 5000.0, 5200.0)]
        if "ahaber.com.tr/" in url:
            return [altin_kayit(url, second_buy, second_sell, second_date)]
        return []

    motor_mod.altin_tablo_oku = fake_table_reader
    return motor.genel_altin_cevabi("Çeyrek altın fiyatı", [
        {
            "title": "Canlı fiyat tablosu",
            "snippet": "Güncel alış ve satış tablosu",
            "url": "https://altinveri.com/altin",
        },
        {
            "title": "Canlı fiyat tablosu",
            "snippet": "Güncel alış ve satış tablosu",
            "url": second_url,
        },
    ])


def test_altin_fiyat_uyumsuz_kaynaklari_reddeder():
    cevap, guven = gold_call(6000.0, 6200.0)
    assert not cevap and guven == 0.0, (cevap, guven)


def test_altin_fiyat_uyumlu_kaynaklari_ortalama_alir():
    cevap, guven = gold_call(5050.0, 5250.0)
    assert guven >= 0.75, (cevap, guven)
    assert "5.025,00 TL" in cevap, cevap
    assert "5.225,00 TL" in cevap, cevap


def test_altin_eski_tarihli_kaynagi_reddeder():
    cevap, guven = gold_call(5010.0, 5210.0, second_date="2020-01-01")
    assert not cevap and guven == 0.0, (cevap, guven)


def test_altin_sahte_alan_adini_reddeder():
    def fake_table_reader(url):
        return [altin_kayit(url, 5000.0, 5200.0)]
    motor_mod.altin_tablo_oku = fake_table_reader
    cevap, guven = motor.genel_altin_cevabi("Çeyrek altın fiyatı", [
        {
            "title": "Canlı fiyat tablosu",
            "snippet": "Güncel alış ve satış tablosu",
            "url": "https://altinveri.com.fake.example/altin",
        },
        {
            "title": "Canlı fiyat tablosu",
            "snippet": "Güncel alış ve satış tablosu",
            "url": "https://www.ahaber.com.tr/finans/altin",
        },
    ])
    assert not cevap and guven == 0.0, (cevap, guven)


def main():
    tests = [
        test_html_tablo_guncel_tarih_olmadan_kullanilmaz,
        test_franz_kafka_biyografisi,
        test_altin_fiyat_uyumsuz_kaynaklari_reddeder,
        test_altin_fiyat_uyumlu_kaynaklari_ortalama_alir,
        test_altin_eski_tarihli_kaynagi_reddeder,
        test_altin_sahte_alan_adini_reddeder,
    ]
    failed = 0
    for test in tests:
        try:
            with patch.dict(sys.modules, {
                "requests": requests,
                "eagle_sanalkuyumculuk": sanal,
                "eagle_altinkaynak": altin,
            }):
                test()
            print(f"[OK] {test.__name__}")
        except Exception as exc:
            failed += 1
            print(f"[HATA] {test.__name__}: {exc}")
    print(f"Sonuç: {len(tests) - failed}/{len(tests)} test başarılı")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
