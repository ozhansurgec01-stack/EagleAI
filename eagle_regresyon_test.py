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



def bilgi_bankasi_alakasiz_eslesme_test():
    from eagle_api import bilgi_bankasi_ara

    deprem_sorusu = (
        "Bir deprem sonrasında 5 hastane, 20 ambulans ve 3.000 yaralı var. "
        "Elektrik ve internet kesilmiş. Hastaları aciliyetlerine göre "
        "sınıflandırır, ambulansları yönlendirir ve kaynakları dağıtırsın. "
        "Karar algoritması ve örnek senaryo ver. Kod yazmadan açıkla."
    )

    sonuc = bilgi_bankasi_ara(deprem_sorusu)
    assert not any("Yapay zekâ nedir?" in madde for madde in sonuc), (
        f"Alakasız yapay zekâ kaydı döndürüldü: {sonuc}"
    )

    dogrudan_soru = bilgi_bankasi_ara("Yapay zekâ nedir?")
    assert any("Yapay zekâ nedir?" in madde for madde in dogrudan_soru), (
        "Doğrudan yapay zekâ bilgi bankası cevabı kayboldu."
    )


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


    tarihsel_sorgu = "1923 yılında Finlandiya'da görülen kuyruklu yıldız"
    yil_1923 = {
        "title": "1923 yılında Finlandiya'da görülen kuyruklu yıldız",
        "snippet": "Finlandiya'da 1923 yılında gözlemlenen kuyruklu yıldız.",
    }
    yil_2023 = {
        "title": "2023 yılında görülen kuyruklu yıldız",
        "snippet": "Finlandiya ve kuyruklu yıldız hakkında bilgiler.",
    }
    yilsiz_sorgu_sonucu = {
        "title": "2023 Finlandiya'da görülen kuyruklu yıldız",
        "snippet": "Finlandiya'da görülen kuyruklu yıldız.",
    }

    assert eagle_api._web_sonucu_sorguyla_ilgili_mi(
        tarihsel_sorgu, yil_1923
    ), "1923 tarihli doğru sonuç kabul edilmedi"
    assert not eagle_api._web_sonucu_sorguyla_ilgili_mi(
        tarihsel_sorgu, yil_2023
    ), "1923 sorgusunda 2023 sonucu kabul edildi"
    assert eagle_api._web_sonucu_sorguyla_ilgili_mi(
        "Finlandiya'da görülen kuyruklu yıldız",
        yilsiz_sorgu_sonucu,
    ), "Yıl içermeyen normal sorgunun davranışı bozuldu"


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

    # Takvim soruları özel hesaplama aracına yönlendirilmeli.
    takvim_sorulari = (
        "14 Kasım hangi güne geliyor?",
        "14 Kasım 2026 hangi güne geliyor?",
        "Bugün hangi gün?",
        "Yarın hangi gün?",
    )
    for soru in takvim_sorulari:
        sonuc = eagle_api.eagle_karar_motoru(soru, [])
        assert sonuc.get("intent") == "takvim", (
            f"Takvim intent hatalı: {soru} -> {sonuc}"
        )
        assert sonuc.get("arac") == "takvim_hesaplama", (
            f"Takvim aracı seçilmedi: {soru} -> {sonuc}"
        )

    referans_gun = eagle_api.datetime(2026, 11, 8).date()
    assert eagle_api.eagle_takvim_tarihini_coz(
        "14 Kasım hangi güne geliyor?", referans_gun
    ) == eagle_api.datetime(2026, 11, 14).date()
    assert eagle_api.eagle_takvim_tarihini_coz(
        "Bugün hangi gün?", referans_gun
    ) == referans_gun
    assert eagle_api.eagle_takvim_tarihini_coz(
        "Yarın hangi gün?", referans_gun
    ) == eagle_api.datetime(2026, 11, 9).date()
    assert eagle_api.eagle_takvim_tarihini_coz(
        "31 Şubat hangi güne geliyor?", referans_gun
    ) is None

    rss = eagle_api.eagle_karar_motoru("RSS haber merkezi oluştur", [])
    assert rss.get("intent") == "program_yazma", (
        f"RSS isteği yanlış yönlendirildi: {rss}"
    )
    assert rss.get("arac") == "program_yazma", (
        f"RSS üretim aracı seçilmedi: {rss}"
    )

    # Kod yazılmamasını isteyen açıklama sorusu program üretimine düşmemeli.
    deprem = eagle_api.eagle_karar_motoru(
        "Bir deprem anında hastaneler ve ambulanslar nasıl koordine edilmelidir? Kod yazmadan açıkla.",
        []
    )
    assert deprem.get("intent") != "program_yazma", (
        f"Kod yazmadan açıklama isteği yanlışlıkla program üretimine yönlendi: {deprem}"
    )
    assert deprem.get("arac") != "program_yazma", (
        f"Program üretme aracı yanlış seçildi: {deprem}"
    )
    assert deprem.get("intent") != "kod_hata", (
        f"Kod yazmadan açıklama isteği kod hatası olarak sınıflandırıldı: {deprem}"
    )
    assert deprem.get("arac") != "kod_analiz", (
        f"Kod yazmadan açıklama isteğinde kod analiz aracı seçildi: {deprem}"
    )

    kod_yazmadan = eagle_api.eagle_karar_motoru("Kod yazmadan anlat", [])
    assert kod_yazmadan.get("intent") != "kod_hata", (
        f"Kod yazmadan anlat isteği kod hatası sayıldı: {kod_yazmadan}"
    )
    assert kod_yazmadan.get("arac") != "kod_analiz", (
        f"Kod yazmadan anlat isteğinde kod analiz aracı seçildi: {kod_yazmadan}"
    )

    assert deprem.get("arac") != "web_arastirma", (
        f"Ambulans kelimesi yanlışlıkla web aramasını tetikledi: {deprem}"
    )
    assert not eagle_api.web_arastirma_gerekli(
        "Bir deprem anında hastaneler ve ambulanslar nasıl koordine edilmelidir? Kod yazmadan açıkla."
    ), "Genel deprem açıklaması web araştırmasına yönlendirilmemeli."

    finans_kodsuz = eagle_api.eagle_karar_motoru(
        "Bir şirketin gelirleri %30 artarken nakit akışı %40 düşmüş, "
        "kısa vadeli borçları %50 yükselmiş ve stokları %60 birikmiş. "
        "Bu çelişkiyi analiz et. Olası nedenleri, finansal riskleri, "
        "kontrol edilmesi gereken göstergeleri ve 90 günlük uygulanabilir "
        "çözüm planını hazırla. Kod yazmadan açıkla.",
        []
    )
    assert finans_kodsuz.get("arac") != "program_yazma", (
        f"Kodsuz finansal analiz program üretimine yönlendirildi: {finans_kodsuz}"
    )
    assert finans_kodsuz.get("arac") != "borc_modulu", (
        f"Finansal analiz borç modülüne yönlendirildi: {finans_kodsuz}"
    )
    assert finans_kodsuz.get("arac") != "web_arastirma", (
        f"Genel finansal analiz gereksiz web aramasına yönlendirildi: {finans_kodsuz}"
    )

    # Gerçek program üretme isteği çalışmaya devam etmeli.
    program = eagle_api.eagle_karar_motoru(
        "Python ile basit bir program yaz", []
    )
    assert program.get("intent") == "program_yazma", (
        f"Gerçek program isteği yanlış yönlendirildi: {program}"
    )
    assert program.get("arac") == "program_yazma", (
        f"Program üretme aracı seçilmedi: {program}"
    )

    guncel = eagle_api.eagle_karar_motoru("Son dakika haberleri var mı?", [])
    assert guncel.get("intent") == "guncel_bilgi", (
        f"Güncel haber isteği bozuldu: {guncel}"
    )

    # Gerçek borç işlemleri borç modülüne gitmeye devam etmeli.
    borc_sorulari = (
        "Borçlarımı göster",
        "Toplam borç ne kadar?",
        "5000 TL borç ekle",
        "Elektrik faturası ödendi",
    )
    for soru in borc_sorulari:
        sonuc = eagle_api.eagle_karar_motoru(soru, [])
        assert sonuc.get("arac") == "borc_modulu", (
            f"Borç/fatura işlemi yanlış yönlendirildi: {soru} -> {sonuc}"
        )

    # Borç kelimesi içeren Python proje isteği program üretimine gitmeli.
    risk_programi = (
        "Python ile bir finansal risk analiz sistemi geliştir. "
        "Sistem CSV dosyasından gelir, gider, nakit akışı, borç ve stok "
        "verilerini okusun. Risk puanı hesaplasın, kritik durumları "
        "tespit etsin ve anlaşılır rapor oluştursun."
    )
    risk_karari = eagle_api.eagle_karar_motoru(risk_programi, [])
    assert risk_karari.get("intent") == "program_yazma", (
        f"Finansal risk sistemi yanlış yönlendirildi: {risk_karari}"
    )
    assert risk_karari.get("arac") == "program_yazma", (
        f"Program üreticisi seçilmedi: {risk_karari}"
    )

    # Soru işareti içermeyen genel bilgi başlıkları web'e yönlenmeli.
    genel_bilgi_basliklari = [
        "1923 yılında Finlandiya'da görülen kuyruklu yıldız",
        "Finlandiya'da görülen kuyruklu yıldız",
        "Finlandiya tarihi",
    ]
    for soru in genel_bilgi_basliklari:
        sonuc = eagle_api.eagle_karar_motoru(soru, [])
        assert sonuc.get("arac") == "web_arastirma", (
            f"Genel bilgi başlığı web'e yönlenmedi: {soru} -> {sonuc}"
        )

    # Sosyal sohbet ifadeleri genel bilgi araması olarak algılanmamalı.
    for soru in ("Nasılsın?", "Sence bu film güzel mi?", "Bugün çok yoruldum"):
        assert not eagle_api.web_arastirma_gerekli(soru), (
            f"Sosyal ifade web araması tetikledi: {soru}"
        )

    # Dizi algılama genel olmalı; belirli yapım adlarına özel kural olmamalı.
    dizi_tanitim_sorulari = [
        "Doctor Who dizisi",
        "X Files dizisi ile ilgili bilgiler verir misin?",
        "Uzak Şehir dizisi hakkında bilgi ver",
        "Gönül Dağı dizisini anlat",
    ]
    for soru in dizi_tanitim_sorulari:
        sonuc = eagle_api.eagle_karar_motoru(soru, [])
        assert sonuc.get("intent") == "guncel_bilgi", (
            f"Dizi tanıtım isteği web araştırmasına yönlenmedi: {soru} -> {sonuc}"
        )
        assert sonuc.get("arac") == "web_arastirma", (
            f"Dizi tanıtımında web aracı seçilmedi: {soru} -> {sonuc}"
        )

    dizi_detay_sorulari = [
        "Doctor Who dizisinin son bölümü hangisi?",
        "Bir dizinin kaçıncı sezonunda olduğunu öğrenmek istiyorum",
    ]
    for soru in dizi_detay_sorulari:
        sonuc = eagle_api.eagle_karar_motoru(soru, [])
        assert sonuc.get("arac") == "web_arastirma", (
            f"Dizi detay isteği web araştırmasına yönlenmedi: {soru} -> {sonuc}"
        )
        assert eagle_api._eagle_dizi_sorgu_turu(soru) == "detay", (
            f"Dizi detay isteği tanıtım olarak sınıflandırıldı: {soru}"
        )


    # Film sorguları: başlık doğrulaması ve yanlış pozitif kontrolleri.
    film_olumlu = [
        "Inception filmi hakkında bilgi ver",
        "Interstellar filminin konusu nedir?",
        "The Godfather oyuncuları kimler?",
        "Oppenheimer filmi",
    ]
    for soru in film_olumlu:
        sonuc = eagle_api.eagle_karar_motoru(soru, [])
        assert sonuc.get("intent") == "guncel_bilgi", (
            f"Film tanıtım isteği yanlış yönlendirildi: {soru} -> {sonuc}"
        )
        assert sonuc.get("arac") == "web_arastirma", (
            f"Film sorgusunda web araştırması seçilmedi: {soru} -> {sonuc}"
        )
        assert sonuc.get("media_query") is True, (
            f"Film sorgusu medya sorgusu olarak işaretlenmedi: {soru}"
        )
        assert eagle_api._eagle_film_baslik_cikar(soru), (
            f"Film başlığı çıkarılamadı: {soru}"
        )

    # Kişisel görüş soruları film tanıtımı olarak sınıflandırılmamalı.
    gorus_sorusu = "Sence bu film güzel mi?"
    assert eagle_api._eagle_film_baslik_cikar(gorus_sorusu) is None
    gorus_karari = eagle_api.eagle_karar_motoru(gorus_sorusu, [])
    assert gorus_karari.get("arac") == "eagle_sohbet", (
        f"Kişisel film görüşü sohbet olarak kalmadı: {gorus_karari}"
    )

    film_olumsuz = [
        "Bugün hava nasıl?",
        "Bir film önerir misin?",
        "Bana film öner",
        "Film tavsiyesi istiyorum",
        "Film hakkında bilgi ver",
        "Lityum aküler hakkında bilgi verir misin?",
        "Güneş panelleri hakkında bilgi verir misin?",
        "LiFePO4 akü nedir?",
    ]
    for soru in film_olumsuz:
        assert eagle_api._eagle_film_sorgu_turu(soru) is None, (
            f"Başlıksız veya ilgisiz sorgu film tanıtımı sayıldı: {soru}"
        )

    teknik_konu_sorulari = [
        "Lityum aküler hakkında bilgi verir misin?",
        "Güneş panelleri hakkında bilgi verir misin?",
        "LiFePO4 akü nedir?",
    ]
    for soru in teknik_konu_sorulari:
        sonuc = eagle_api.eagle_karar_motoru(soru, [])
        assert sonuc.get("media_query") is not True, (
            f"Teknik bilgi sorusu TMDb medya sorgusuna yönlendirildi: {soru} -> {sonuc}"
        )


def kod_analiz_import_test():
    import eagle_kod_analiz_motoru
    assert eagle_kod_analiz_motoru is not None


def autofix_import_test():
    import eagle_autofix
    assert eagle_autofix is not None


def assertion_autofix_regresyon_test():
    from eagle_autofix import EagleAutoFixEngine

    test_file = Path("assertion_regresyon_gecici.py")
    kaynak = 'assert False, "beklenen doğrulama hatası"\n'
    test_file.write_text(kaynak, encoding="utf-8")

    try:
        motor = EagleAutoFixEngine()
        hata = motor.analyze_error(
            'Traceback (most recent call last):\n'
            '  File "assertion_regresyon_gecici.py", line 1, in <module>\n'
            '    assert False, "beklenen doğrulama hatası"\n'
            'AssertionError: beklenen doğrulama hatası'
        )
        assert hata.get("type") == "AssertionError", hata

        sonuc = motor.repair_loop(test_file)
        assert sonuc.get("success") is False, (
            f"Başarısız assert başarılı sayıldı: {sonuc}"
        )
        assert sonuc.get("fix_applied") is False, sonuc
        assert "Assert doğrulaması başarısız" in sonuc.get("reason", ""), sonuc
        assert test_file.read_text(encoding="utf-8") == kaynak, (
            "AssertionError durumunda kaynak dosya değiştirildi."
        )
    finally:
        if test_file.exists():
            test_file.unlink()


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



def bitcoin_fiyat_regresyon_test():
    from types import SimpleNamespace
    import eagle_api
    from eagle_merkez_motoru import EagleMerkezMotoru

    finans_algilama_ornekleri = [
        ("Merhaba", False),
        ("Şampiyonlar Ligi maç sonuçları", False),
        ("Bitcoin nedir?", False),
        ("Bitcoin fiyatı", True),
        ("BTC kaç dolar?", True),
        ("Dolar kaç TL?", True),
        ("Gram altın ne kadar?", True),
        ("Euro nedir?", False),
    ]
    for mesaj, beklenen in finans_algilama_ornekleri:
        assert eagle_api.finans_fiyat_sorgusu_mu(mesaj) is beklenen, mesaj

    assert not EagleMerkezMotoru.finans_fiyat_sorgusu_mu("Bitcoin nedir?")
    assert EagleMerkezMotoru.finans_fiyat_sorgusu_mu("Bitcoin fiyatı")
    assert EagleMerkezMotoru.finans_fiyat_sorgusu_mu("BTC kaç dolar?")
    assert not EagleMerkezMotoru.finans_fiyat_sorgusu_mu(
        "Şampiyonlar Ligi maç sonuçları"
    )

    assert eagle_api.bitcoin_fiyat_sorgusu_mu("Güncel Bitcoin fiyatı")
    assert eagle_api.bitcoin_fiyat_sorgusu_mu(
        "Bitcoin şu anda dolar karşısında ne kadar?"
    )
    assert eagle_api.bitcoin_fiyat_sorgusu_mu("BTC kaç dolar?")
    assert not eagle_api.bitcoin_fiyat_sorgusu_mu("Bitcoin nedir?")
    assert not eagle_api.bitcoin_fiyat_sorgusu_mu("Bitcoin nasıl çalışır?")
    assert not eagle_api.bitcoin_fiyat_sorgusu_mu("Ethereum fiyatı")

    orijinal_get = eagle_api.requests.get
    try:
        eagle_api.requests.get = lambda *a, **k: SimpleNamespace(
            json=lambda: {"bitcoin": {
                "usd": 75684.25,
                "last_updated_at": 1794000000,
            }},
            raise_for_status=lambda: None,
        )
        sonuc = eagle_api.bitcoin_fiyatini_getir()
        assert sonuc is not None, "Geçerli yanıt reddedildi"
        assert sonuc["price"] == 75684.25
        assert sonuc["updated_at"]

        eagle_api.requests.get = lambda *a, **k: SimpleNamespace(
            json=lambda: {"bitcoin": {"usd": "hatalı"}},
            raise_for_status=lambda: None,
        )
        assert eagle_api.bitcoin_fiyatini_getir() is None

        def hata_get(*a, **k):
            raise RuntimeError("test bağlantı hatası")

        eagle_api.requests.get = hata_get
        assert eagle_api.bitcoin_fiyatini_getir() is None
    finally:
        eagle_api.requests.get = orijinal_get




def finans_api_veri_ayristirma_test():
    import eagle_api

    altin = eagle_api.finans_verisini_ayristir(
        "**Gram Altın**\nAlış: 6.500,00 TL | Satış: 6.550,00 TL\n"
        "**Çeyrek Altın**\nAlış: 10.400,00 TL | Satış: 10.600,00 TL"
    )
    assert altin == {
        "type": "gold",
        "items": [
            {"name": "Gram Altın", "buy": "6.500,00", "sell": "6.550,00"},
            {"name": "Çeyrek Altın", "buy": "10.400,00", "sell": "10.600,00"},
        ],
    }, altin

    doviz = eagle_api.finans_verisini_ayristir(
        "USD: 42,50 TL\nEUR: 49,20 TL"
    )
    assert doviz == {
        "type": "currency",
        "items": [
            {"code": "USD", "value": "42,50"},
            {"code": "EUR", "value": "49,20"},
        ],
    }, doviz

    assert eagle_api.finans_verisini_ayristir(
        "Güncel fiyat doğrulanamadı."
    ) is None


def merkez_finans_bos_web_verisi_test():
    from eagle_merkez_motoru import EagleMerkezMotoru

    # Döviz: ilk web sonucu boş olsa bile döviz fonksiyonuna ulaşılmalı.
    motor = EagleMerkezMotoru()
    cagrilar = []

    def doviz(mesaj, veriler, web_arayici=None):
        cagrilar.append("doviz")
        return "USD: 42,50 TL", 0.82

    motor.genel_doviz_cevabi = doviz
    sonuc = motor.calistir(
        "Dolar ne kadar?",
        web_verisi=[],
        web_arayici=lambda *a, **k: [],
    )
    assert sonuc.ok and "42,50" in sonuc.cevap, sonuc
    assert cagrilar == ["doviz"], cagrilar

    # Altın: döviz sonucu yoksa altın fonksiyonuna ulaşılmalı.
    motor = EagleMerkezMotoru()
    cagrilar = []

    def doviz_yok(mesaj, veriler, web_arayici=None):
        cagrilar.append("doviz")
        return None, 0.0

    def altin(mesaj, veriler, web_arayici=None, sayfa_okuyucu=None):
        cagrilar.append("altin")
        return "Gram Altın: doğrulanmış test fiyatı", 0.82

    motor.genel_doviz_cevabi = doviz_yok
    motor.genel_altin_cevabi = altin
    sonuc = motor.calistir(
        "Gram altın ne kadar?",
        web_verisi=[],
        web_arayici=lambda *a, **k: [],
    )
    assert sonuc.ok and "test fiyatı" in sonuc.cevap, sonuc
    assert cagrilar == ["doviz", "altin"], cagrilar

    # Doğrulanmış fiyat yoksa güvenli hata cevabı korunmalı.
    motor = EagleMerkezMotoru()
    motor.genel_doviz_cevabi = lambda *a, **k: (None, 0.0)
    motor.genel_altin_cevabi = lambda *a, **k: ("", 0.0)
    sonuc = motor.calistir(
        "Dolar ne kadar?",
        web_verisi=[],
        web_arayici=lambda *a, **k: [],
    )
    assert "doğrulayamadım" in sonuc.cevap.casefold(), sonuc


def api_fonksiyon_test():
    import eagle_api
    from unittest.mock import patch

    assert hasattr(eagle_api, "sohbet")
    assert hasattr(eagle_api, "app")

    class SahteProgramMotoru:
        cagri_sayisi = 0

        def uret(self, mesaj):
            type(self).cagri_sayisi += 1
            return {
                "ok": False,
                "error": "TEST_PROGRAM_SENTINEL",
            }

    SahteProgramMotoru.cagri_sayisi = 0

    with (
        patch.object(eagle_api, "hava_durumu_getir", return_value={"ok": False}),
        patch.object(eagle_api, "web_arastir", return_value=[]),
        patch.object(
            eagle_api.merkez_motor,
            "calistir",
            return_value={
                "ok": True,
                "cevap": "TEST: Deprem koordinasyonu açıklama zincirine ulaştı.",
            },
        ) as deprem_merkez_mock,
        patch.object(
            eagle_api,
            "EagleProgramUretmeMotoru",
            SahteProgramMotoru,
        ),
    ):
        istemci = eagle_api.app.test_client()

        deprem = istemci.post(
            "/api/sohbet",
            json={
                "message": (
                    "Bir deprem sonrasında 5 hastane, 20 ambulans ve "
                    "3.000 yaralı var. Elektrik ve internet kesilmiş. "
                    "Hastaları aciliyetlerine göre nasıl sınıflandırır, "
                    "ambulansları nasıl yönlendirir ve kaynakları nasıl "
                    "dağıtırsın? Karar algoritması ve örnek senaryo ver. "
                    "Kod yazmadan açıkla."
                )
            },
        )

        assert deprem.status_code == 200, deprem.get_data(as_text=True)
        deprem_data = deprem.get_json() or {}
        assert deprem_data.get("ok") is True, deprem_data
        assert (
            "TEST: Deprem koordinasyonu açıklama zincirine ulaştı."
            in deprem_data.get("answer", "")
        ), deprem_data
        assert deprem_merkez_mock.call_count == 1, (
            "Deprem senaryosu bilgi bankasında kalmamalı, merkez motora ulaşmalı."
        )
        assert "Program üretilemedi" not in deprem_data.get("answer", ""), deprem_data
        assert deprem_data.get("program_yazma") is not True, deprem_data
        assert SahteProgramMotoru.cagri_sayisi == 0, (
            "Kod yazmadan açıklama isteğinde program üreticisi çağrıldı."
        )

        # Finansal analiz: açıklama isteği program, borç veya web modülüne sapmamalı.
        finans_merkez_cagrilari = []
        finans_web_cagrilari = []
        finans_borc_cagrilari = []

        def finans_merkez_sahte(*args, **kwargs):
            finans_merkez_cagrilari.append((args, kwargs))
            return {
                "ok": True,
                "cevap": "TEST: Finansal analiz merkez motoruna ulaştı.",
            }

        def finans_web_sahte(*args, **kwargs):
            finans_web_cagrilari.append((args, kwargs))
            return []

        def finans_borc_sahte(*args, **kwargs):
            finans_borc_cagrilari.append((args, kwargs))
            return None, None

        def finans_borc_mesaji_sahte(*args, **kwargs):
            finans_borc_cagrilari.append((args, kwargs))
            return "TEST_BORC_MODULU_CAGRILDI"

        with (
            patch.object(
                eagle_api.merkez_motor,
                "calistir",
                side_effect=finans_merkez_sahte,
            ),
            patch.object(
                eagle_api,
                "web_arastir",
                side_effect=finans_web_sahte,
            ),
            patch.object(
                eagle_api.borc_modulu,
                "akilli_borc_isle",
                side_effect=finans_borc_sahte,
            ),
            patch.object(
                eagle_api.borc_modulu,
                "borc_mesaji_isle",
                side_effect=finans_borc_mesaji_sahte,
            ),
        ):
            finans = istemci.post(
                "/api/sohbet",
                json={
                    "message": (
                        "Bir şirketin gelirleri %30 artarken nakit akışı %40 düşmüş, "
                        "kısa vadeli borçları %50 yükselmiş ve stokları %60 birikmiş. "
                        "Bu çelişkiyi analiz et. Olası nedenleri, finansal riskleri, "
                        "kontrol edilmesi gereken göstergeleri ve 90 günlük "
                        "uygulanabilir çözüm planını hazırla. Kod yazmadan açıkla."
                    )
                },
            )

        assert finans.status_code == 200, finans.get_data(as_text=True)
        finans_data = finans.get_json() or {}
        assert finans_data.get("ok") is True, finans_data
        assert finans_data.get("merkez_motor") is True, finans_data
        assert "TEST: Finansal analiz merkez motoruna ulaştı." in finans_data.get("answer", ""), finans_data
        assert len(finans_merkez_cagrilari) == 1, finans_merkez_cagrilari
        assert len(finans_web_cagrilari) == 0, (
            "Kod yazmadan finansal analiz isteğinde web araştırması çağrıldı."
        )
        assert len(finans_borc_cagrilari) == 0, (
            "Genel finansal analiz isteğinde borç modülü çağrıldı."
        )
        assert SahteProgramMotoru.cagri_sayisi == 0, (
            "Kod yazmadan finansal analiz isteğinde program üreticisi çağrıldı."
        )

        program = istemci.post(
            "/api/sohbet",
            json={"message": "Python ile basit bir program yaz."},
        )

        assert program.status_code == 200, program.get_data(as_text=True)
        program_data = program.get_json() or {}
        assert program_data.get("program_yazma") is True, program_data
        assert "TEST_PROGRAM_SENTINEL" in program_data.get("answer", ""), program_data
        assert SahteProgramMotoru.cagri_sayisi == 1, (
            "Açık program isteğinde program üreticisi tam bir kez çağrılmalı."
        )

        risk_programi = istemci.post(
            "/api/sohbet",
            json={
                "message": (
                    "Python ile bir finansal risk analiz sistemi geliştir. "
                    "Sistem CSV dosyasından gelir, gider, nakit akışı, borç ve stok "
                    "verilerini okusun. Risk puanı hesaplasın, kritik durumları "
                    "tespit etsin ve anlaşılır rapor oluştursun."
                )
            },
        )
        assert risk_programi.status_code == 200, risk_programi.get_data(as_text=True)
        risk_data = risk_programi.get_json() or {}
        assert risk_data.get("program_yazma") is True, risk_data
        assert "TEST_PROGRAM_SENTINEL" in risk_data.get("answer", ""), risk_data
        assert SahteProgramMotoru.cagri_sayisi == 2, (
            "Finansal risk sistemi isteğinde program üreticisi çağrılmadı."
        )




def api_gercek_afet_uçtan_uça_test():
    import eagle_api
    from pathlib import Path
    from unittest.mock import patch

    soru = (
        "Bir deprem sonrasında 5 hastane, 20 ambulans ve "
        "3.000 yaralı var. Elektrik ve internet kesilmiş. "
        "Hastaları aciliyetlerine göre nasıl sınıflandırır, "
        "ambulansları nasıl yönlendirir ve kaynakları nasıl "
        "dağıtırsın? Karar algoritması ve örnek senaryo ver. "
        "Kod yazmadan açıkla."
    )

    json_dosyasi = (
        Path(eagle_api.__file__).resolve().parent
        / "eagle_sohbet_baglam.json"
    )
    json_vardi = json_dosyasi.exists()
    json_once = json_dosyasi.read_bytes() if json_vardi else None

    try:
        with (
            patch.object(
                eagle_api, "web_arastir", return_value=[]
            ) as web_mock,
            patch.object(
                eagle_api, "hava_durumu_getir",
                return_value={"ok": False}
            ),
            patch.object(
                eagle_api, "web_sayfa_oku", return_value=""
            ),
            patch.object(
                eagle_api.requests, "get",
                side_effect=AssertionError(
                    "Test sırasında dış GET isteği engellendi."
                )
            ),
            patch.object(
                eagle_api.requests, "post",
                side_effect=AssertionError(
                    "Test sırasında dış POST isteği engellendi."
                )
            ),
        ):
            yanit = eagle_api.app.test_client().post(
                "/api/sohbet",
                json={"message": soru},
            )

        veri = yanit.get_json() or {}
        cevap = str(veri.get("answer", ""))

        assert yanit.status_code == 200, veri
        assert veri.get("ok") is True, veri
        assert veri.get("merkez_motor") is True, veri
        assert "3.000 yaralı" in cevap, cevap
        assert "Triyaj" in cevap, cevap
        assert "Haberleşme" in cevap, cevap
        assert "EAGLE BİLGİ BANKASI" not in cevap, cevap
        assert web_mock.call_count == 0, web_mock.call_count

    finally:
        if json_vardi:
            if not json_dosyasi.exists() or json_dosyasi.read_bytes() != json_once:
                json_dosyasi.write_bytes(json_once)
        elif json_dosyasi.exists():
            json_dosyasi.unlink()


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




def finans_doviz_normalizasyon_test():
    import eagle_api

    assert eagle_api.doviz_arama_sorgusu("Euro ne kadar?") == "1 EUR kaç TL"
    assert eagle_api.doviz_arama_sorgusu("Dolar kaç TL?") == "1 USD kaç TL"
    assert eagle_api.doviz_arama_sorgusu("Euro nedir?") == "Euro nedir?"


def finans_doviz_kaynak_onceligi_test():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from unittest.mock import patch
    from eagle_merkez_motoru import EagleMerkezMotoru

    bugun = datetime.now(ZoneInfo("Europe/Istanbul"))
    aramalar = []

    ilk_veriler = [
        {
            "url": "https://kur-a.example/usd",
            "text": f"1 USD = 40 TL bugün {bugun.year}",
        },
        {
            "url": "https://kur-b.example/usd",
            "text": f"1 USD = 40 TL bugün {bugun.year}",
        },
    ]

    def ek_arama(sorgu, limit=6):
        aramalar.append(sorgu)
        return [{
            "url": "https://kur-c.example/usd",
            "text": f"1 USD = 39 TL bugün {bugun.year}",
        }]

    # Bu test web kaynak önceliğini sınar; TCMB çağrısını izole et.
    with patch(
        "eagle_merkez_motoru.tcmb_doviz_kurlarini_getir",
        return_value=None,
    ):
        cevap, guven = EagleMerkezMotoru.genel_doviz_cevabi(
            "Dolar kaç TL?",
            ilk_veriler,
            web_arayici=ek_arama,
        )

    assert cevap and "40" in cevap, f"İki kaynakla doğrulanan kur korunmadı: {cevap}"
    assert "39" not in cevap, f"Tek kaynaklı zayıf kur seçildi: {cevap}"
    assert len(aramalar) == 1
    assert bugun.strftime("%d.%m.%Y") in aramalar[0], (
        f"Arama tarihi dinamik değil: {aramalar[0]}"
    )
    assert guven > 0



def finans_tcmb_xml_dogrulama_test():
    import io
    from unittest.mock import patch
    from eagle_merkez_motoru import EagleMerkezMotoru

    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <Tarih_Date Date="06.11.2026">
      <Currency CurrencyCode="USD">
        <ForexBuying>42.1234</ForexBuying>
        <ForexSelling>42.4567</ForexSelling>
      </Currency>
      <Currency CurrencyCode="EUR">
        <ForexBuying>48.1234</ForexBuying>
        <ForexSelling>48.4567</ForexSelling>
      </Currency>
      <Currency CurrencyCode="GBP">
        <ForexBuying>55.1234</ForexBuying>
        <ForexSelling>55.4567</ForexSelling>
      </Currency>
    </Tarih_Date>"""

    with patch("urllib.request.urlopen", return_value=io.BytesIO(xml)):
        cevap, guven = EagleMerkezMotoru.genel_doviz_cevabi(
            "Dolar kaç TL?", []
        )

    assert cevap and "42,1234" in cevap, cevap
    assert "42,4567" in cevap, cevap
    assert "06.11.2026" in cevap, cevap
    assert "TCMB" in cevap, cevap
    assert guven == 0.95

    with patch("urllib.request.urlopen", return_value=io.BytesIO(xml)):
        cevap, guven = EagleMerkezMotoru.genel_doviz_cevabi(
            "Euro kaç TL?", []
        )

    assert "48,1234" in cevap, cevap
    assert "48,4567" in cevap, cevap


def finans_gram_altin_dogrulama_test():
    from eagle_merkez_motoru import EagleMerkezMotoru
    motor = EagleMerkezMotoru()

    veriler = [
        {
            "url": "https://altin-a.example/fiyat",
            "text": "Gram Altın alış 6500 TL satış 6550 TL",
        },
        {
            "url": "https://altin-b.example/fiyat",
            "text": "Gram Altın alış 6500 TL satış 6550 TL",
        },
    ]

    from unittest.mock import patch
    with patch("requests.get", side_effect=RuntimeError("API bu testte devre dışı")):
        cevap, guven = motor.genel_altin_cevabi(
            "Gram altın fiyatı",
            veriler,
        )

    assert not cevap, f"API doğrulaması yokken HTML'den Gram Altın üretildi: {cevap}"
    assert guven == 0.0


def finans_genel_altin_esik_test():
    from eagle_merkez_motoru import EagleMerkezMotoru
    from eagle_altin_entegrasyon_test import responses
    from unittest.mock import patch

    motor = EagleMerkezMotoru()
    veriler = [
        {
            "url": "https://altin-a.example/fiyat",
            "text": "Gram Altın alış 6500 TL satış 6550 TL",
        },
        {
            "url": "https://altin-b.example/fiyat",
            "text": "Gram Altın alış 6500 TL satış 6550 TL",
        },
    ]

    data = responses()
    with patch("requests.get", side_effect=lambda url, **kw: data[url]):
        cevap, guven = motor.genel_altin_cevabi("Altın ne kadar?", veriler)

    assert "Gram Altın" in cevap, f"Doğrulanmış Gram Altın genel sorguda gösterilmedi: {cevap}"
    assert "6.562,11 TL" in cevap, f"Ortalama alış fiyatı hatalı: {cevap}"
    assert guven > 0.0, f"Doğrulanmış fiyat için güven puanı üretilmedi: {guven}"


def finans_altin_genel_sayisal_engeli_test():
    from eagle_merkez_motoru import EagleMerkezMotoru

    motor = EagleMerkezMotoru()
    veriler = [
        {
            "url": "https://ornek-a.example",
            "text": "Gram altın 6.555,36 TL",
        },
        {
            "url": "https://ornek-b.example",
            "text": "Gram altın fiyatı 6.555,36 TL",
        },
    ]

    for soru in (
        "Gram altın ne kadar?",
        "Gram altın kaç TL?",
        "Gram altın fiyatı",
    ):
        cevap, guven = motor.net_sayisal_cevap(soru, veriler)
        assert cevap is None and guven == 0.0, (soru, cevap, guven)



def finansal_celiski_dogrudan_analiz_test():
    from eagle_merkez_motoru import EagleMerkezMotoru

    soru = (
        "Bir şirketin gelirleri %30 artarken nakit akışı %40 düşmüş, "
        "kısa vadeli borçları %50 yükselmiş ve stokları %60 birikmiş. "
        "Bu çelişkiyi analiz et. Olası nedenleri, finansal riskleri, "
        "kontrol edilmesi gereken göstergeleri ve 90 günlük uygulanabilir "
        "çözüm planını hazırla. Kod yazmadan açıkla."
    )
    cevap, guven = EagleMerkezMotoru.genel_web_cevabi(soru, [])
    assert cevap and guven >= 0.9, (cevap, guven)
    for ifade in ("DSO", "DIO", "DPO", "90 günlük", "Likidite"):
        assert ifade.lower() in cevap.lower(), ifade



def finansal_celiski_cagri_zinciri_test():
    from eagle_merkez_motoru import EagleMerkezMotoru

    motor = EagleMerkezMotoru()
    soru = (
        "Bir şirketin gelirleri %30 artarken nakit akışı %40 düşmüş, "
        "kısa vadeli borçları %50 yükselmiş ve stokları %60 birikmiş. "
        "Bu çelişkiyi analiz et. Olası nedenleri, finansal riskleri, "
        "kontrol edilmesi gereken göstergeleri ve 90 günlük uygulanabilir "
        "çözüm planını hazırla. Kod yazmadan açıkla."
    )

    senaryolar = {
        "bos_web_verisi": [],
        "web_verisi_var": [
            {
                "title": "Şirket finansal göstergeleri",
                "snippet": (
                    "Gelir, gider, nakit akışı, kısa vadeli borç ve stok değişimleri."
                ),
                "url": "https://example.com/finans",
            }
        ],
    }

    for ad, veriler in senaryolar.items():
        sonuc = motor.calistir(
            mesaj=soru,
            karar={"intent": "genel"},
            web_verisi=veriler,
        )
        assert sonuc.ok, (ad, sonuc)
        assert sonuc.guven >= 0.9, (ad, sonuc.guven)
        assert sonuc.gemini_gerekli is False, (ad, sonuc.gemini_gerekli)

        cevap = (sonuc.cevap or "").lower()
        for ifade in ("dso", "dio", "dpo", "90 günlük", "likidite"):
            assert ifade in cevap, (ad, ifade, sonuc.cevap)


def finansal_csv_planlayici_test():
    from eagle_uygulama_planlayici import EagleUygulamaPlanlayici

    soru = (
        "Python ile finansal risk analiz sistemi geliştir. CSV dosyasından "
        "gelir, gider, nakit akışı, borç ve stok verilerini okuyup risk "
        "puanı hesaplasın."
    )
    plan = EagleUygulamaPlanlayici().planla(soru)
    assert plan is not None
    assert plan.get("finansal_risk_csv") is True, plan
    assert plan.get("csv_girdisi") is True
    assert plan["varliklar"] == ["finansal_kayit"]
    assert plan["alanlar"]["finansal_kayit"] == [
        "id", "tarih", "gelir", "gider", "nakit_akisi", "borc", "stok"
    ]


def finansal_csv_uretici_test():
    from eagle_uygulama_planlayici import EagleUygulamaPlanlayici
    from eagle_genel_uygulama_uretici import EagleGenelUygulamaUretici

    soru = (
        "Python ile finansal risk analiz sistemi geliştir. CSV dosyasından "
        "gelir, gider, nakit akışı, borç ve stok verilerini okuyup risk "
        "puanı hesaplasın."
    )
    plan = EagleUygulamaPlanlayici().planla(soru)
    sonuc = EagleGenelUygulamaUretici().uret(plan)
    assert sonuc["validation_ok"], sonuc
    assert sonuc["profil"] == "finansal_risk_csv"
    assert "csv.DictReader" in sonuc["dosyalar"]["app.py"]
    assert "/api/analiz" in sonuc["dosyalar"]["app.py"]
    assert "test_csv_analiz_risk_puani" in sonuc["dosyalar"]["tests/test_core.py"]
    app_kodu = sonuc["dosyalar"]["app.py"]
    test_kodu = sonuc["dosyalar"]["tests/test_core.py"]
    assert 'MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024' in app_kodu
    assert "MAX_CSV_ROWS = 10000" in app_kodu
    assert "Belirsiz sayı biçimi" in app_kodu
    assert "test_csv_belirsiz_sayi_reddedilir" in test_kodu
    assert "test_csv_satir_limiti" in test_kodu
    assert "test_csv_dosya_boyutu_limiti" in test_kodu


def genel_stok_uretimi_koruma_test():
    from eagle_uygulama_planlayici import EagleUygulamaPlanlayici

    plan = EagleUygulamaPlanlayici().planla(
        "Stok takip sistemi geliştir, ürün miktarlarını listele."
    )
    assert plan is not None
    assert not plan.get("finansal_risk_csv")
    assert "stok" in plan["varliklar"]



def afet_koordinasyon_regresyon_test():
    from eagle_afet_koordinasyon import afet_koordinasyon_cevabi

    soru = (
        "Bir deprem sonrasında 5 hastane, 20 ambulans ve 3.000 yaralı var. "
        "Elektrik ve internet kesilmiş. Hastaları aciliyetlerine göre "
        "sınıflandırır, ambulansları yönlendirir ve kaynakları dağıtırsın. "
        "Karar algoritması ve örnek senaryo ver. Kod yazmadan açıkla."
    )

    cevap = afet_koordinasyon_cevabi(soru)
    assert cevap, "Afet talebi tanınmadı."
    assert "5 hastane" in cevap
    assert "20 ambulans" in cevap
    assert "3.000 yaralı" in cevap
    assert "Triyaj" in cevap
    assert "Haberleşme" in cevap

    assert afet_koordinasyon_cevabi("Python'da liste nasıl sıralanır?") is None
    assert afet_koordinasyon_cevabi("Boş ambulanslar için rota planla.") is None


def afet_merkez_motoru_cagri_test():
    from eagle_merkez_motoru import EagleMerkezMotoru

    motor = EagleMerkezMotoru()
    soru = (
        "Bir deprem sonrasında 5 hastane, 20 ambulans ve 3.000 yaralı var. "
        "Elektrik ve internet kesilmiş. Hastaları aciliyetlerine göre "
        "sınıflandırır, ambulansları yönlendirir ve kaynakları dağıtırsın. "
        "Karar algoritması ve örnek senaryo ver. Kod yazmadan açıkla."
    )

    sonuc = motor.calistir(mesaj=soru, karar={}, web_verisi=[])
    assert sonuc.ok is True
    assert "3.000 yaralı" in sonuc.cevap
    assert "Triyaj" in sonuc.cevap

    mevcut = motor.calistir(
        mesaj=soru,
        karar={},
        web_verisi=[],
        mevcut_cevap="MEVCUT CEVAP KORUNDU"
    )
    assert mevcut.cevap == "MEVCUT CEVAP KORUNDU"

print("===== EAGLEAI REGRESYON TEST =====")
print()

test("Kodsuz finansal çelişki doğrudan analizi", finansal_celiski_dogrudan_analiz_test)
test("Finansal çelişki merkezi motor çağrı zinciri", finansal_celiski_cagri_zinciri_test)
test("Finansal CSV planlayıcı profili", finansal_csv_planlayici_test)
test("Finansal CSV uygulama üretimi ve doğrulaması", finansal_csv_uretici_test)
test("Genel stok üretimi korunuyor", genel_stok_uretimi_koruma_test)
test("Altın sorgusunda doğrulanmamış tekil sayı engeli", finans_altin_genel_sayisal_engeli_test)
test("Bilgi bankası JSON ve 49 yeni Python kaydı", bilgi_bankasi_test)
test("Bilgi bankası alakasız eşleşme engeli", bilgi_bankasi_alakasiz_eslesme_test)
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
test("AssertionError doğrulama", assertion_autofix_regresyon_test)
test("BooleanComparison AutoFix", boolean_autofix_test)
test("Voleybol takım eşleşmesi ve genel sonuçlar", voleybol_takim_eslesme_regresyon_test)
test("TVF tarih eşleşmesi ve çakışma kontrolü", tvf_tarih_eslesme_regresyon_test)
test("Bitcoin fiyatı CoinGecko doğrulaması", bitcoin_fiyat_regresyon_test)
test("Boş web sonucunda finans ek araması", merkez_finans_bos_web_verisi_test)
test("Döviz sorgusu normalizasyonu", finans_doviz_normalizasyon_test)
test("Döviz kaynak önceliği ve dinamik tarih", finans_doviz_kaynak_onceligi_test)
test("TCMB XML döviz alış/satış doğrulaması", finans_tcmb_xml_dogrulama_test)
test("Gram altın iki kaynak doğrulaması", finans_gram_altin_dogrulama_test)
test("Genel altın sorgusu ürün eşiği", finans_genel_altin_esik_test)
test("Finans API veri ayrıştırma", finans_api_veri_ayristirma_test)
test("API kod yazmadan açıklama ve program üretimi yönlendirmesi", api_fonksiyon_test)
test("Genel bilgi soru algılama", genel_soru_algilama_test)
test("Gerçek Flask afet API uçtan uca", api_gercek_afet_uçtan_uça_test)
test("Afet koordinasyon modülü", afet_koordinasyon_regresyon_test)
test("Afet koordinasyon merkez motoru entegrasyonu", afet_merkez_motoru_cagri_test)

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
