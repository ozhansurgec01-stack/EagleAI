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


def program_uretme_regresyon_test():
    from eagle_program_uretme_motoru import EagleProgramUretmeMotoru

    motor = EagleProgramUretmeMotoru()

    sorular = [
        "Merhaba Dünya programı yaz",
        "İki sayının toplamını hesaplayan program yaz",
        "Python\u0027da iki sayıyı toplayan basit bir program yaz.",
        "Bir sayının faktöriyelini hesaplayan program yaz",
        "Python'da bir klasörü recursive olarak tarayan .py dosyalarını AST ile analiz eden ve JSON oluşturan program yaz",
    ]

    for soru in sorular:
        sonuc = motor.uret(soru)

        assert isinstance(sonuc, dict), f"Sonuç sözlük değil: {soru}"
        assert sonuc.get("ok") is True, f"Program üretilemedi: {soru}"
        assert sonuc.get("dil") == "python", f"Dil Python değil: {soru}"

        kod = sonuc.get("kod", "")
        assert isinstance(kod, str) and kod.strip(), f"Kod boş: {soru}"

        compile(kod, "<program_regresyon>", "exec")

    ast_sonuc = motor.uret(sorular[-1])
    assert ast_sonuc.get("ana_dosya") == "python_ast_analyzer.py"
    assert "--path" in ast_sonuc.get("kod", "")
    assert "ast" in ast_sonuc.get("kod", "")
    assert "json" in ast_sonuc.get("kod", "").lower()


def yagmur_ormani_web_test():
    from eagle_merkez_motoru import EagleMerkezMotoru

    motor = EagleMerkezMotoru()
    cevap, guven = motor.genel_web_cevabi(
        "Amazon Ormanları hangi ülkelerde bulunur?",
        [{
            "title": "Amazon Ormanları",
            "snippet": "Amazon yağmur ormanları Güney Amerika'da bulunur.",
            "url": "https://example.com/amazon",
        }],
    )
    assert guven >= 0.75, f"Amazon cevabının güveni düşük: {guven}"
    for ulke in (
        "Brezilya", "Peru", "Kolombiya", "Bolivya", "Venezuela",
        "Ekvador", "Guyana", "Surinam", "Fransız Guyanası",
    ):
        assert ulke.casefold() in cevap.casefold(), (
            f"Amazon cevabında {ulke} eksik: {cevap}"
        )


def web_url_tekillestirme_test():
    from eagle_api import web_url_tekillestirme_anahtari

    a = web_url_tekillestirme_anahtari(
        "HTTPS://Example.com/bilgi/#bolum"
    )
    b = web_url_tekillestirme_anahtari(
        "https://example.com/bilgi"
    )
    assert a == b, f"Aynı sayfa tekilleşmedi: {a!r} != {b!r}"


def atlas_okyanusu_sayfa_onceligi_test():
    from eagle_merkez_motoru import EagleMerkezMotoru

    kaynaklar = [{
        "title": "Atlas Okyanusu",
        "snippet": (
            "Atlas Okyanusu hakkında bilgi almak için "
            "sitemizdeki menüleri ve diğer bağlantıları inceleyebilirsiniz."
        ),
        "url": "https://test.example/atlas",
    }]
    sayfa = (
        "Ayrıca bakınız değiştir Okyanusların sınırları. "
        "Atlas Okyanusu, Amerika kıtalarını Avrupa ve Afrika'dan "
        "ayıran büyük bir okyanustur. Dünya üzerindeki önemli "
        "deniz ulaşım yollarından bazıları bu okyanustan geçer. "
        "Okyanusları ayırmıştır: Atlas Okyanusu Hint Okyanusu "
        "Arktik Okyanusu Pasifik Okyanusu Güney Okyanusu. "
        "Genel bilgiler Tür Okyanus Koordinatlar 0 derece "
        "Ortalama derinlik 3646 m En derin noktası Porto Riko "
        "Çukuru Yüzölçümü 106 milyon km2 Su hacmi 310 milyon km3."
    )

    cevap, guven = EagleMerkezMotoru.genel_web_cevabi(
        "Atlas Okyanusu hakkında bilgi",
        kaynaklar,
        sayfa_okuyucu=lambda url: sayfa,
    )

    assert cevap, "EagleAI genel bilgi cevabı üretemedi"
    assert "Afrika" in cevap and "Amerika" in cevap, (
        f"Sayfa içeriği yerine alakasız özet seçilmiş: {cevap}"
    )
    assert "Arktik Okyanusu Pasifik Okyanusu" not in cevap, (
        f"Liste metni cevaba sızdı: {cevap}"
    )
    assert "neredeyse" not in cevap.casefold(), (
        f"Muğlak yüzölçümü karşılaştırması cevaba sızdı: {cevap}"
    )
    assert guven >= 0.75, f"Beklenmeyen güven puanı: {guven}"


def konum_sorusunda_tamamlayici_cumle_test():
    from eagle_merkez_motoru import EagleMerkezMotoru

    testler = [
        (
            "Dünyanın en derin çukuru nerededir?",
            "Mariana Çukuru, Pasifik Okyanusu'nun batısında ve "
            "Guam Adası'nın güneybatısında yer alır. "
            "Dünyanın en derin noktası, Mariana Çukuru içindeki "
            "Challenger Derinliği olarak kabul edilir.",
            ["Pasifik", "Guam"],
        ),
        (
            "Everest Dağı nerede bulunur?",
            "Everest Dağı, Himalayalar'da Nepal ile Tibet sınırında "
            "yer alır. Dağın kuzey yamacı Çin'in Tibet bölgesindedir.",
            ["Himalayalar", "Nepal", "Tibet"],
        ),
        (
            "Büyük Set Resifi nerede bulunur?",
            "Büyük Set Resifi, Avustralya'nın kuzeydoğu kıyısı "
            "açıklarında Mercan Denizi'nde bulunur. "
            "Queensland kıyısı boyunca uzanır.",
            ["Avustralya", "Mercan Denizi", "Queensland"],
        ),
        (
            "Sahra Çölü nerede bulunur?",
            "Sahra Çölü, Kuzey Afrika'da yer alır. "
            "Çöl, Cezayir ve Libya gibi birçok ülkeye yayılır.",
            ["Kuzey Afrika", "Cezayir", "Libya"],
        ),
    ]

    for soru, sayfa, beklenen in testler:
        kaynaklar = [{
            "title": soru,
            "snippet": "",
            "url": "https://test.example/konum",
        }]
        cevap, guven = EagleMerkezMotoru.genel_web_cevabi(
            soru,
            kaynaklar,
            sayfa_okuyucu=lambda url, icerik=sayfa: icerik,
        )

        eksik = [
            bilgi for bilgi in beklenen
            if bilgi.casefold() not in cevap.casefold()
        ]
        assert not eksik, (
            f"{soru}: eksik konum bilgileri {eksik}; cevap: {cevap}"
        )
        assert guven >= 0.75, (
            f"{soru}: beklenmeyen güven puanı {guven}"
        )


def genel_web_cikti_kalitesi_test():
    from eagle_merkez_motoru import EagleMerkezMotoru

    vakalar = [
        (
            "Atlas Okyanusu hakkında bilgi",
            "Atlas Okyanusu",
            "Atlas Okyanusu, Amerika kıtalarını Avrupa ve Afrika'dan ayırır. "
            "Hayalinizi gerçeğe dönüştürüyor.",
            ["Amerika", "Afrika"],
        ),
        (
            "Büyük Okyanus hakkında bilgi",
            "Büyük Okyanus",
            "Büyük Okyanus, dünyanın en büyük okyanusudur. "
            "Listemizde derlemeye karar verdik.",
            ["en büyük okyanus"],
        ),
        (
            "Kanada'nın başkenti neresidir?",
            "Kanada'nın başkenti",
            "Ottawa, Kanada'nın başkentidir ve Ontario eyaletinin güneydoğusunda yer alır. "
            "Ottawa, Kanada'nın başkentidir ve Ontario eyaletinin güneydoğusunda yer alır.",
            ["Ottawa"],
        ),
        (
            "Mısır piramitleri nerede bulunur?",
            "Mısır piramitleri",
            "[3] [4] [5] Bilinen bazı yapılar Sakkara'dadır. "
            "Gize Piramitleri, Mısır'ın Kahire yakınlarındaki Gize bölgesindedir. "
            "Tüm Mısır piramitleri Nil'in batı kıyısında inşa edildi. "
            "Mısır'daki piramitlerin büyük çoğunluğu Nil'in batı kıyısında yer alır. "
            "Piramitler firavunlar için mezar yapıları olarak kullanılmıştır.",
            ["Gize", "Kahire"],
        ),
    ]

    for i, (soru, baslik, sayfa, beklenen) in enumerate(vakalar):
        cevap, guven = EagleMerkezMotoru.genel_web_cevabi(
            soru,
            [{
                "title": baslik,
                "snippet": "",
                "url": f"https://test.example/kalite-{i}",
            }],
            sayfa_okuyucu=lambda url, icerik=sayfa: icerik,
        )
        norm = cevap.casefold()
        assert cevap, f"{soru}: cevap boş"
        for bilgi in beklenen:
            assert bilgi.casefold() in norm, (
                f"{soru}: gerekli bilgi eksik ({bilgi}): {cevap}"
            )
        for yasak in (
            "hayalinizi gerçeğe dönüştürüyor",
            "listemizde derlemeye karar verdik",
            "[3]", "[4]", "[5]",
        ):
            assert yasak not in norm, (
                f"{soru}: düşük kaliteli metin kaldı ({yasak}): {cevap}"
            )
        assert cevap.count("Ottawa, Kanada'nın başkentidir.") <= 1, (
            f"Tekrarlı cevap: {cevap}"
        )
        if soru == "Mısır piramitleri nerede bulunur?":
            assert norm.count("nil") <= 1, (
                f"Aynı Nil bilgisi tekrarlandı: {cevap}"
            )
        assert guven >= 0.75, f"{soru}: beklenmeyen güven {guven}"



def genel_bilgi_konu_alakasi_ve_guven_test():
    from eagle_merkez_motoru import EagleMerkezMotoru

    vakalar = [
        (
            "Atlas Okyanusu hakkında bilgi verir misin?",
            "Atlas Okyanusu",
            (
                "Ayrıca dünyanın en uzun okyanus sıradağı olan Orta Atlas "
                "Sırtı bu okyanusta bulunur. "
                "Atlas Okyanusu, Amerika kıtalarını Avrupa ve Afrika'dan "
                "ayıran büyük bir okyanustur. "
                "Atlas Okyanusu veya Atlantik Okyanusu, 106.460.000 km² "
                "yüzölçümü ile Dünya'nın en büyük ikinci okyanusudur. "
                "Atlantik köle ticareti veya trans-atlantik köle ticareti, "
                "Afrikalı kölelerin Avrupalılar tarafından esir edilmelerini "
                "ve satılmalarını içeren Atlas Okyanusu ve kıyılarında "
                "gerçekleşen faaliyetler dönemi."
            ),
            ("Avrupa", "Afrika", "ikinci büyük okyanusudur"),
            ("köle ticareti", "Orta Atlas Sırtı", "92 milyon km²"),
        ),
        (
            "Fotosentez nedir?",
            "Fotosentez",
            (
                "Çoğu bitki, çoğu alg ve siyanobakteri fotosentez yapar; "
                "bu tür canlılara fotoototroflar denir. "
                "Fotosentez, bitkilerin ışık enerjisini kimyasal enerjiye "
                "dönüştürdüğü süreçtir. "
                "İç katman fotosentez pigmentleri enzimleriyle klorofil "
                "içeren yassı keseciklere dönüşmüştür. "
                "Fotosentez sırasında bitkiler karbondioksit ve su kullanarak "
                "glikoz üretir ve oksijen açığa çıkar."
            ),
            ("süreçtir", "ışık enerjisini kimyasal enerjiye"),
            ("İç katman fotosentez pigmentleri",),
        ),
        (
            "Türkiye hakkında bilgi verir misin?",
            "Türkiye",
            (
                "Avrupa ve Asya kıtalarının kavşak noktalarında yer alan "
                "Türkiye, bu benzersiz coğrafi konumu sayesinde önemli bir "
                "jeostratejik güç olarak kabul edilir. "
                "Türkiye, Ekonomik İşbirliği ve Kalkınma Örgütü (OECD), "
                "G20 ve Türk Devletleri Teşkilatı'nın kurucu üyeleri "
                "arasında yer almaktadır. "
                "Aralık 2021'de cumhurbaşkanı Recep Tayyip Erdoğan, "
                "ihracatta Made in Türkiye ibaresinin kullanılmasına "
                "ilişkin bir genelge yayımladı."
            ),
            ("Türkiye", "Avrupa", "Asya"),
            ("genelge yayımladı",),
        ),
    ]

    for i, (soru, baslik, sayfa, gerekli, yasak) in enumerate(vakalar):
        cevap, guven = EagleMerkezMotoru.genel_web_cevabi(
            soru,
            [{
                "title": baslik,
                "snippet": "",
                "url": f"https://test.example/konu-alakasi-{i}",
            }],
            sayfa_okuyucu=lambda url, icerik=sayfa: icerik,
        )
        assert cevap, f"{soru}: cevap boş"
        if soru == "Fotosentez nedir?":
            assert cevap.startswith("Fotosentez,"), (
                f"Tanım sorusunda örnek cümlesi tanımdan önce geldi: {cevap}"
            )
        for bilgi in gerekli:
            assert bilgi.casefold() in cevap.casefold(), (
                f"{soru}: gerekli bilgi eksik ({bilgi}): {cevap}"
            )
        for ifade in yasak:
            assert ifade.casefold() not in cevap.casefold(), (
                f"{soru}: konu dışı cümle kaldı ({ifade}): {cevap}"
            )
        assert 0.75 <= guven < 0.88, (
            f"{soru}: güven puanı sabit/esassız görünüyor: {guven}"
        )


def genel_tanitimda_nesnel_bilgi_onceligi_test():
    from eagle_merkez_motoru import EagleMerkezMotoru

    sayfa = (
        "Türkiye, benzersiz coğrafi konumu sayesinde önemli bir "
        "jeostratejik güç olarak kabul edilir. "
        "Türkiye'nin başkenti Ankara'dır. "
        "Türkiye'nin resmi dili Türkçedir. "
        "Türkiye'nin nüfusu ve yüzölçümü ülke hakkında temel "
        "demografik ve coğrafi bilgiler sunar. "
        "Tarafsız ve partisiz cumhurbaşkanlığını savunan Türkiye'deki ilk "
        "parti, Mustafa Kemal Paşa'nın hem CHP genel başkanı hem de "
        "cumhurbaşkanı olmasına karşı çıkan Terakkiperver Cumhuriyet "
        "Fırkası'dır."
    )
    cevap, guven = EagleMerkezMotoru.genel_web_cevabi(
        "Türkiye hakkında bilgi verir misin?",
        [{
            "title": "Türkiye hakkında temel bilgiler",
            "snippet": "",
            "url": "https://test.example/turkiye-temel-bilgi",
        }],
        sayfa_okuyucu=lambda url: sayfa,
    )

    assert cevap, "Türkiye tanıtım sorusu boş cevap verdi"
    assert "Ankara" in cevap or "Türkçedir" in cevap, (
        f"Nesnel temel bilgi öne çıkmadı: {cevap}"
    )
    assert "jeostratejik güç" not in cevap.casefold(), (
        f"Editoryal değerlendirme cevaba girdi: {cevap}"
    )
    assert "terakkiperver cumhuriyet fırkası" not in cevap.casefold(), (
        f"Genel tanıtıma ilgisiz tarihî ayrıntı girdi: {cevap}"
    )
    assert guven < 0.88, f"Genel web cevabına aşırı güven verildi: {guven}"


def tanim_sorusunda_ornek_cumlesi_reddet_test():
    from eagle_merkez_motoru import EagleMerkezMotoru

    kaynaklar = [{
        "title": "Fotosentez",
        "snippet": "",
        "url": "https://test.example/fotosentez",
    }]

    # Kavramın geçtiği ama onu tanımlamayan bir cümle, "nedir?" cevabı olamaz.
    zayif_sayfa = (
        "Çoğu bitki, çoğu alg ve siyanobakteri fotosentez yapar; "
        "bu tür canlılara fotoototroflar denir."
    )
    cevap, guven = EagleMerkezMotoru.genel_web_cevabi(
        "Fotosentez nedir?",
        kaynaklar,
        sayfa_okuyucu=lambda url: zayif_sayfa,
    )
    assert not cevap and guven == 0.0, (
        f"Tanım bulunmadığı halde örnek cümlesi cevap seçildi: {cevap} ({guven})"
    )

    # Açık tanım varsa onu seç; aynı sayfadaki örnek cümlesi cevabı bozmasın.
    iyi_sayfa = (
        "Çoğu bitki, çoğu alg ve siyanobakteri fotosentez yapar; "
        "bu tür canlılara fotoototroflar denir. "
        "Fotosentez, bitkilerin ışık enerjisini kimyasal enerjiye "
        "dönüştürdüğü süreçtir."
    )
    cevap, guven = EagleMerkezMotoru.genel_web_cevabi(
        "Fotosentez nedir?",
        kaynaklar,
        sayfa_okuyucu=lambda url: iyi_sayfa,
    )
    assert cevap.startswith("Fotosentez,"), (
        f"Tanım cümlesi seçilmedi: {cevap}"
    )
    assert "fotoototroflar" not in cevap.casefold(), (
        f"Tanım olmayan örnek cevaba karıştı: {cevap}"
    )
    assert 0.75 <= guven < 0.88, f"Beklenmeyen güven puanı: {guven}"

    # Konu adıyla başlayan fakat tanım vermeyen ikinci cümle cevaba girmemeli.
    karisik_sayfa = (
        "Fotosentez, ışık enerjisini kimyasal bağ enerjisine dönüştüren "
        "biyolojik bir mekanizmadır. "
        "Fotosentez yapma yeteneği kazanmış ilkin hücrelerin içine girerek "
        "simbiyoz yaşamış ve kloroplastları meydana getirmiştir."
    )
    cevap, _ = EagleMerkezMotoru.genel_web_cevabi(
        "Fotosentez nedir?",
        kaynaklar,
        sayfa_okuyucu=lambda url: karisik_sayfa,
    )
    assert "mekanizmadır" in cevap.casefold(), f"Tanım cümlesi kayboldu: {cevap}"
    assert "simbiyoz" not in cevap.casefold(), (
        f"Tanım olmayan yan cümle cevaba karıştı: {cevap}"
    )


def okyanus_konu_disina_cikma_test():
    kaynaklar = [
        {"title": "Atlas Okyanusu", "url": "https://example.com/atlas",
         "snippet": "Atlas Okyanusu Dünya'nın en büyük ikinci okyanusudur."},
        {"title": "Arktik Okyanusu", "url": "https://example.com/arktik",
         "snippet": "Arktik Okyanusu Kuzey Kutbu'nu kapsayan buzlarla kaplı bir okyanustur."},
    ]
    cevap, _ = EagleMerkezMotoru.genel_web_cevabi(
        "Atlas Okyanusu hakkında bilgi verir misin?", kaynaklar,
        sayfa_okuyucu=lambda url: (
            "Atlas Okyanusu, Dünya'nın en büyük ikinci okyanusudur. "
            if 'atlas' in url else
            "Arktik Okyanusu Kuzey Kutbu'nu kapsayan, buzlarla kaplı bir okyanustur."
        ),
    )
    assert "Arktik Okyanusu" not in cevap, f"Konu dışı okyanus cevaba girdi: {cevap}"


def wikipedia_gezinme_metni_temizleme_test():
    from eagle_merkez_motoru import EagleMerkezMotoru

    sayfa = (
        "Ayrıca bakınız değiştir Mısır Piramitleri Büyük Gize Sfenksi. "
        "Gize Piramitleri, Mısır'ın Kahire yakınlarındaki Gize bölgesindedir."
    )
    cevap, _ = EagleMerkezMotoru.genel_web_cevabi(
        "Mısır piramitleri nerede bulunur?",
        [{
            "title": "Mısır piramitleri",
            "snippet": "",
            "url": "https://test.example/wikipedia-gezinme",
        }],
        sayfa_okuyucu=lambda url: sayfa,
    )
    norm = cevap.casefold()
    assert "gize" in norm and "kahire" in norm, (
        f"Yararlı bilgi kayboldu: {cevap}"
    )
    assert "ayrıca bakınız" not in norm, (
        f"Gezinme metni cevapta kaldı: {cevap}"
    )
    assert "büyük gize sfenksi" not in norm, (
        f"Gezinme bağlantısı cevapta kaldı: {cevap}"
    )


def web_sonuc_ilgililik_test():
    import eagle_api

    ilgili = {
        "title": "Amazon Ormanları",
        "snippet": "Amazon yağmur ormanları Güney Amerika'da bulunur.",
    }
    alakasiz = {
        "title": "Kaplan kedisi",
        "snippet": "Amerika'nın tropik yağmur ormanlarında yaşar.",
    }

    assert eagle_api._web_sonucu_sorguyla_ilgili_mi(
        "yağmur ormanları nerelerde bulunur", ilgili
    ), "İlgili Amazon Ormanları sonucu elendi"

    assert not eagle_api._web_sonucu_sorguyla_ilgili_mi(
        "yağmur ormanları nerelerde bulunur", alakasiz
    ), "Başlığı ilgisiz hayvan sonucu kabul edildi"

    radar = {
        "title": "Yağmur radarı Türkiye",
        "snippet": "Güncel yağış ve sağanak yağış tahminleri.",
    }
    assert not eagle_api._web_sonucu_sorguyla_ilgili_mi(
        "yağmur ormanları nerelerde bulunur", radar
    ), "Yağmur radarı sonucu yanlışlıkla kabul edildi"

    kanada_tr = {
        "title": "Kanada - Genel Bilgiler",
        "snippet": "Kanada, Kuzey Amerika'da bulunan bir ülkedir.",
    }
    assert eagle_api._web_sonucu_sorguyla_ilgili_mi(
        "Kanada hakkında bilgi verir misin", kanada_tr
    ), "Türkçe Kanada sorgusunda soru ekleri sonucu elememeli"

    kanada_en = {
        "title": "Canada - Geography",
        "snippet": "Canada is a country in North America.",
    }
    assert eagle_api._web_sonucu_sorguyla_ilgili_mi(
        "Kanada hakkında bilgi verir misin", kanada_en
    ), "Kanada sorgusu İngilizce Canada başlığıyla eşleşmeli"


def web_eslesme_esigi_test():
    import eagle_api

    beklenenler = {
        1: 1,
        2: 1,
        3: 2,
        4: 2,
        5: 3,
        6: 3,
    }
    for kelime_sayisi, beklenen in beklenenler.items():
        sonuc = eagle_api._gerekli_web_eslesme_sayisi(kelime_sayisi)
        assert sonuc == beklenen, (
            f"{kelime_sayisi} kelime için {beklenen} bekleniyordu, {sonuc} bulundu"
        )


def konu_eslesme_test():
    import eagle_api

    sonuc = eagle_api.bilgi_bankasi_ara("Python'da zip nedir?")
    assert sonuc, "zip sorusuna cevap bulunamadı"

    sonuc = eagle_api.bilgi_bankasi_ara("Python'da lambda nedir?")
    assert sonuc, "lambda sorusuna cevap bulunamadı"

    sonuc = eagle_api.bilgi_bankasi_ara("Python'da NameError nedir?")
    assert sonuc, "NameError sorusuna cevap bulunamadı"


def temel_python_soru_cevap_test():
    import eagle_api

    kontroller = [
        ("Python'da liste nasıl oluşturulur?", "sayilar = [1, 2, 3]"),
        ("Python listesi nedir?", "sıralı"),
        ("Python'da sözlük nasıl oluşturulur?", '"ad": "Ali"'),
        ("Python'da fonksiyon nasıl yazılır?", "def selamla(isim):"),
    ]

    for soru, beklenen in kontroller:
        sonuc = eagle_api.bilgi_bankasi_ara(soru)
        metin = "\n".join(str(x) for x in sonuc) if sonuc else ""
        assert beklenen.lower() in metin.lower(), (
            f"{soru!r} için beklenen içerik bulunamadı: {sonuc!r}"
        )

    append_sonuc = eagle_api.bilgi_bankasi_ara(
        "Python listesinde append() ne işe yarar?"
    )
    assert len(append_sonuc or []) == 1, (
        f"append() için tek cevap bekleniyordu: {append_sonuc!r}"
    )

    filtre_sonuc = eagle_api.bilgi_bankasi_ara(
        "Python filter() kullanmadan yeni liste nasıl oluşturulur?"
    )
    assert not any(
        "dictionary comprehension" in str(cevap).lower()
        for cevap in (filtre_sonuc or [])
    ), f"Liste sorusuna sözlük cevabı karıştı: {filtre_sonuc!r}"


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

    rss = eagle_api.eagle_karar_motoru("RSS haber merkezi oluştur", [])
    assert rss.get("intent") == "program_yazma", (
        f"RSS isteği yanlış yönlendirildi: {rss}"
    )
    assert rss.get("arac") == "program_yazma", (
        f"RSS üretim aracı seçilmedi: {rss}"
    )

    guncel = eagle_api.eagle_karar_motoru("Son dakika haberleri var mı?", [])
    assert guncel.get("intent") == "guncel_bilgi", (
        f"Güncel haber isteği bozuldu: {guncel}"
    )


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



def voleybol_takim_eslesme_regresyon_test():
    import eagle_api

    orijinal = eagle_api.tvf_voleybol_sonuclari_getir
    sahte = [
        {
            "ev": "Yeşilyurt", "ev_skor": "0",
            "deplasman": "Bahçelievler", "deplasman_skor": "3",
            "lig": "Test Ligi", "setler": [], "kaynak": "TVF"
        },
        {
            "ev": "Fenerbahçe", "ev_skor": "3",
            "deplasman": "Eczacıbaşı", "deplasman_skor": "1",
            "lig": "Test Ligi", "setler": [], "kaynak": "TVF"
        },
        {
            "ev": "Zeren Spor", "ev_skor": "3",
            "deplasman": "Aras Kargo", "deplasman_skor": "0",
            "lig": "Test Ligi", "setler": [], "kaynak": "TVF"
        }
    ]

    try:
        eagle_api.tvf_voleybol_sonuclari_getir = lambda *a, **k: sahte
        istemci = eagle_api.app.test_client()

        r1 = istemci.post("/api/sohbet", json={
            "message": "Bodrum Fenerbahçe voleybol maç sonucu"
        })
        assert r1.status_code == 200, f"Takım sorgusu HTTP {r1.status_code}"
        cevap1 = str((r1.get_json() or {}).get("answer", ""))
        assert "Yeşilyurt" not in cevap1, "Alakasız maç gösterildi"
        assert "doğrulanmış bir maç sonucu bulamadım" in cevap1, (
            "Eşleşme yok mesajı verilmedi"
        )

        r2 = istemci.post("/api/sohbet", json={
            "message": "voleybol maç sonucu"
        })
        assert r2.status_code == 200, f"Genel sorgu HTTP {r2.status_code}"
        cevap2 = str((r2.get_json() or {}).get("answer", ""))
        assert "Yeşilyurt" in cevap2, "Genel sonuçlar korunmadı"

        r3 = istemci.post("/api/sohbet", json={
            "message": "Fenerbahçe kadın voleybol sonucu"
        })
        assert r3.status_code == 200, f"Kadın voleybol sorgusu HTTP {r3.status_code}"
        cevap3 = str((r3.get_json() or {}).get("answer", ""))
        assert "Fenerbahçe" in cevap3, (
            "Kadın voleybolu niteleyicisi geçerli takım eşleşmesini engelledi"
        )
        assert "Yeşilyurt" not in cevap3, (
            "Kadın voleybolu takım sorgusunda alakasız maç gösterildi"
        )

        r4 = istemci.post("/api/sohbet", json={
            "message": "Zerenspor voleybol maç sonucu"
        })
        assert r4.status_code == 200, f"Zerenspor sorgusu HTTP {r4.status_code}"
        cevap4 = str((r4.get_json() or {}).get("answer", ""))
        assert "Zeren Spor" in cevap4, (
            f"Zerenspor ve Zeren Spor eşleşmedi: {cevap4}"
        )
        assert "Yeşilyurt" not in cevap4, (
            "Normalizasyon sorgusunda alakasız maç gösterildi"
        )
    finally:
        eagle_api.tvf_voleybol_sonuclari_getir = orijinal


def tvf_tarih_eslesme_regresyon_test():
    import requests
    import eagle_api
    from types import SimpleNamespace

    sonuc_html = """
    <section class="tvf-results">
      <div class="tvf-result">
        <div class="tvf-result__league">Arabica Coffee House Erkekler Voleybol 1.Ligi</div>
        <div class="tvf-result__row">
          <span class="tvf-result__team">Fenerbahçe</span>
          <span class="tvf-result__score">3</span>
        </div>
        <div class="tvf-result__row">
          <span class="tvf-result__team">Eczacıbaşı</span>
          <span class="tvf-result__score">0</span>
        </div>
        <table class="tvf-result__sets">
          <tr><th title="Fenerbahçe"></th>
            <td>25</td><td>25</td><td>25</td>
            <td class="tvf-result__sets-total">3</td></tr>
          <tr><th title="Eczacıbaşı"></th>
            <td>20</td><td>20</td><td>20</td>
            <td class="tvf-result__sets-total">0</td></tr>
        </table>
      </div>
    </section>
    """
    ana_html = '<a href="/FSM/test">Arabica Coffee House Erkekler 1. Lig</a>'

    def lig_html(tarihler):
        satirlar = ""
        for tarih, saat in tarihler:
            hucreler = [
                tarih, saat, "Erkekler", "Test",
                "Fenerbahçe", "3", "0", "Eczacıbaşı", "Tamamlandı"
            ]
            satirlar += "<tr>" + "".join(
                f"<td>{h}</td>" for h in hucreler
            ) + "</tr>"
        return "<table>" + satirlar + "</table>"

    orijinal_get = requests.get

    def calistir(tarihler):
        def sahte_get(url, *args, **kwargs):
            if url == "https://tvf.org.tr/":
                html = sonuc_html
            elif url == "https://fikstur.tvf.org.tr/":
                html = ana_html
            elif url == "https://fikstur.tvf.org.tr/FSM/test":
                html = lig_html(tarihler)
            else:
                raise AssertionError(f"Beklenmeyen URL: {url}")

            return SimpleNamespace(
                text=html,
                raise_for_status=lambda: None
            )

        requests.get = sahte_get
        return eagle_api.tvf_voleybol_sonuclari_getir()

    try:
        tek = calistir([("18.10.2026", "15:30")])
        assert len(tek) == 1, f"Sonuç ayrıştırılamadı: {tek}"
        assert tek[0].get("tarih") == "18.10.2026", tek
        assert tek[0].get("saat") == "15:30", tek

        cakisma = calistir([
            ("18.10.2026", "15:30"),
            ("19.10.2026", "16:30")
        ])
        assert len(cakisma) == 1, cakisma
        assert "tarih" not in cakisma[0], (
            f"Çakışmada yanlış tarih atandı: {cakisma[0]}"
        )
        assert "saat" not in cakisma[0], (
            f"Çakışmada yanlış saat atandı: {cakisma[0]}"
        )
    finally:
        requests.get = orijinal_get

def api_fonksiyon_test():
    import eagle_api

    assert hasattr(eagle_api, "sohbet")
    assert hasattr(eagle_api, "app")


def genel_soru_algilama_test():
    from eagle_cevap_motoru import _soru_gibi_mi

    sorular = [
        "EagleAI, Türkiye'nin başkenti neresidir? Yalnızca kısa cevap ver.",
        "Türkiye'nin başkenti neresi?",
    ]
    import eagle_api

    for soru in sorular:
        assert _soru_gibi_mi(soru), f"Genel bilgi sorusu algılanmadı: {soru}"
        cevaplar = eagle_api.bilgi_bankasi_ara(soru)
        assert "Ankara" in cevaplar, f"Başkent cevabı bulunamadı: {soru} -> {cevaplar}"


print("===== EAGLEAI REGRESYON TEST =====")
print()

test("Bilgi bankası JSON ve 49 yeni Python kaydı", bilgi_bankasi_test)
test("Python syntax temel testleri", python_syntax_test)
test("Program üretme regresyonu", program_uretme_regresyon_test)
test("Yağmur ormanı web araması", yagmur_ormani_web_test)
test("Web URL tekilleştirme", web_url_tekillestirme_test)
test("Atlas Okyanusu sayfa içeriği önceliği", atlas_okyanusu_sayfa_onceligi_test)
test("Konum sorusunda tamamlayıcı cümle", konum_sorusunda_tamamlayici_cumle_test)
test("Genel web cevap kalitesi", genel_web_cikti_kalitesi_test)
test("Genel tanıtımda nesnel bilgi önceliği", genel_tanitimda_nesnel_bilgi_onceligi_test)
test("Tanım sorusunda örnek cümlesi reddedilir", tanim_sorusunda_ornek_cumlesi_reddet_test)
test("Genel bilgi konu alâkası ve güven puanı", genel_bilgi_konu_alakasi_ve_guven_test)
test("Wikipedia gezinme metni temizleme", wikipedia_gezinme_metni_temizleme_test)
test("Web sonucu konu ilgililiği", web_sonuc_ilgililik_test)
test("Web araması kelime eşleşme eşiği", web_eslesme_esigi_test)
test("Python konu eşleşmesi", konu_eslesme_test)
test("Temel Python soru-cevap kalitesi", temel_python_soru_cevap_test)
test("Matematik bilgi bankası", matematik_test)
test("Karar motoru", karar_motoru_test)
test("Kod analiz motoru", kod_analiz_import_test)
test("AutoFix", autofix_import_test)
test("BooleanComparison AutoFix", boolean_autofix_test)
test("Voleybol takım eşleşmesi ve genel sonuçlar", voleybol_takim_eslesme_regresyon_test)
test("TVF tarih eşleşmesi ve çakışma kontrolü", tvf_tarih_eslesme_regresyon_test)
test("API /api/sohbet altyapısı", api_fonksiyon_test)
test("Genel bilgi soru algılama", genel_soru_algilama_test)

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
