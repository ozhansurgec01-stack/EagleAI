# -*- coding: utf-8 -*-
"""
EAGLE FİNANSAL ANALİZ MODÜLÜ

Kullanıcının verdiği göstergeleri (gelir, gider, nakit akışı, borç, stok,
alacak, kâr marjı) okur: hangi gösterge hangi yönde (artış/düşüş) ve varsa kaç
yüzde değişmiş. Bu yön ve büyüklüklerden kural tabanlı bir değerlendirme üretir.
Model veya web gerektirmez; aynı girdi her zaman aynı çıktıyı verir.

Sınırlar:
- Yalnızca yön ve yüzde okunur. Tutarlar, dönem, sektör ve bilanço kalemleri
  verilmediyse bunlar "eksik bilgi" olarak listelenir.
- Çıktı ön analizdir; denetim veya yatırım tavsiyesi değildir.

Kullanım (afet koordinasyon modülüyle aynı örüntü):
    cevap, guven = finansal_analiz_cevabi(mesaj, gorev_turu=karar.get("islem"))
    # Uygun değilse ("", 0.0) döner.
"""
import re
import unicodedata

GOSTERGELER = {
    "gelir": ("gelir", "ciro", "satis", "hasilat"),
    "gider": ("gider", "masraf", "maliyet"),
    "nakit": ("nakit",),
    "borc": ("borc",),
    "stok": ("stok", "envanter"),
    "alacak": ("alacak", "tahsilat"),
    "marj": ("marj",),
}
ETIKET = {
    "gelir": "Gelir", "gider": "Gider", "nakit": "Nakit akışı",
    "borc": "Borç", "stok": "Stok", "alacak": "Alacaklar",
    "marj": "Kâr marjı",
}
_GOSTERGE_ISTISNA = ("giderek", "gidermek", "giderme", "alacagim", "alacagiz")

_YUKARI = ("art", "yuksel", "birik", "buyu", "cogal", "tirman", "sisti")
_ASAGI = ("dus", "azal", "gerile", "erim", "eridi", "eriy", "kucul", "daral", "kayb")
_YON_ISTISNA = ("artik", "artir", "arttir", "dusun", "dusman", "yuksek", "buyuk")

_ANALIZ_NIYETI = (
    "analiz", "acikla", "degerlendir", "neden", "risk", "cozum", "plan",
    "yorumla", "celiski", "ne yapmali", "ne yapilmali", "oneri",
    "yol haritasi", "yorum",
)
_KOD_OLUMSUZ = (
    "kod yazmadan", "kod yazmasan", "kod yazmayarak", "kod yazmaksizin",
    "kodsuz", "kod olmadan", "kod vermeden", "kod istemiyorum",
    "program yazmadan", "program yazmasan",
)


def _norm(metin):
    t = unicodedata.normalize("NFKD", str(metin or "").casefold())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.replace("ı", "i")


def _kod_istegi_mu(n):
    """Gerçek bir program/kod isteği mi? ("Kod yazmadan" olumsuzdur.)"""
    if any(x in n for x in _KOD_OLUMSUZ):
        return False
    if re.search(r"\b(python|java|kotlin|javascript|sql|flask)\b", n):
        return True
    return bool(re.search(
        r"\b(program|kod|yazilim|uygulama|script|sistem)\w*\s+"
        r"(yaz|gelistir|olustur|uret)", n))


def _gosterge_adi(token):
    if token.startswith(_GOSTERGE_ISTISNA):
        return None
    for ad, kokler in GOSTERGELER.items():
        if token.startswith(kokler):
            return ad
    return None


def _yon(token):
    if not token.isalpha() or token.startswith(_YON_ISTISNA):
        return 0
    if token.startswith(_YUKARI):
        return 1
    if token.startswith(_ASAGI):
        return -1
    return 0


def _yuzde(token):
    m = re.fullmatch(r"%(\d+(?:[.,]\d+)?)|(\d+(?:[.,]\d+)?)%", token)
    if not m:
        return None
    return float((m.group(1) or m.group(2)).replace(",", "."))


def _s(x):
    x = float(x)
    return str(int(x)) if x.is_integer() else str(round(x, 1)).replace(".", ",")


def _oku(n):
    """Normalize metinden {gösterge: (yön, yüzde)} ve anılan göstergeleri çıkarır."""
    n = re.sub(r"yuzde\s*(\d+(?:[.,]\d+)?)", r"%\1", n)
    tokenler = re.findall(r"%\d+(?:[.,]\d+)?|\d+(?:[.,]\d+)?%|\d+(?:[.,]\d+)?|[a-z]+", n)

    kayitlar = []
    for i, t in enumerate(tokenler):
        ad = _gosterge_adi(t)
        if not ad:
            continue
        if kayitlar and kayitlar[-1]["ad"] == ad and i - kayitlar[-1]["i"] <= 2:
            continue  # "kisa vadeli borc borcu" gibi tekrarları birleştir
        kayitlar.append({"ad": ad, "i": i, "yon": 0, "yuzde": None})

    def en_yakin_onceki(j):
        onceki = [r for r in kayitlar if r["i"] < j and j - r["i"] <= 8]
        return onceki[-1] if onceki else None

    def ilk_sonraki(j):
        for r in kayitlar:
            if r["i"] > j and r["i"] - j <= 3:
                return r
        return None

    for j, t in enumerate(tokenler):
        yon = _yon(t)
        if yon:
            r = en_yakin_onceki(j)
            if r is None or r["yon"]:
                r = ilk_sonraki(j)
                if r is not None and r["yon"]:
                    r = None
            if r is not None:
                r["yon"] = yon
                # "stok ve borç arttı": yakın, yönsüz önceki gösterge aynı yönü alır.
                k = kayitlar.index(r)
                if k > 0 and not kayitlar[k - 1]["yon"] and r["i"] - kayitlar[k - 1]["i"] <= 3:
                    kayitlar[k - 1]["yon"] = yon
            continue
        yz = _yuzde(t)
        if yz is not None:
            r = en_yakin_onceki(j)
            if r is None or r["yuzde"] is not None:
                r = ilk_sonraki(j)
                if r is not None and r["yuzde"] is not None:
                    r = None
            if r is not None:
                r["yuzde"] = yz

    veri = {}
    for r in kayitlar:
        if r["yon"] and r["ad"] not in veri:
            veri[r["ad"]] = (r["yon"], r["yuzde"])
    anilan = {r["ad"] for r in kayitlar}
    return veri, anilan


def finansal_gorev_mu(mesaj):
    """Karar motoru için: mesaj bir finansal durum analizi görevi mi?"""
    n = _norm(mesaj)
    if _kod_istegi_mu(n):
        return False
    veri, _ = _oku(n)
    return len(veri) >= 2 and any(w in n for w in _ANALIZ_NIYETI)


# ----------------------------------------------------------------- plan metni
_PLAN = {
    "tahsilat": [
        "Vadesi geçen alacakları müşteri bazında sıralayın; tahsilat sorumlusu ve takvimi belirleyin.",
        "Büyük alacaklar için tahsilat veya yapılandırma görüşmelerini tamamlayın; yeni satışlarda vade ve peşinat koşullarını gözden geçirin.",
        "Müşteri bazlı kredi limiti ve ödeme koşullarını yeniden belirleyin; satış hedeflerini tahsilata bağlamayı değerlendirin.",
        "DSO'yu haftalık izleyin; hedeften sapan müşteriler için düzeltici aksiyon atayın.",
    ],
    "borc": [
        "Vadesi gelen borçların takvimini çıkarın; hangilerinin nakitle kapanacağını netleştirin.",
        "Bankalar ve tedarikçilerle vade uzatma veya yeniden yapılandırma görüşmelerini başlatın.",
        "Kısa vadeli borcu uzun vadeye çevirme seçeneklerini ve faiz maliyetini karşılaştırın.",
        "Kısa vadeli borç oranını ve cari oranı aylık izleyin; limit ve vade yoğunlaşması risklerini takip edin.",
    ],
    "stok": [
        "Yeni stok alımlarını sınırlayın; yavaş dönen stokları ürün bazında ayırın.",
        "Yavaş dönen stoklar için tasfiye veya kampanya planı yapın; satın alma limitlerini gerçek satış hızına bağlayın.",
        "Talep tahmini ve yeniden sipariş noktalarını güncelleyin; tedarikçilerle iade veya esnek sevkiyat görüşün.",
        "DIO ve stok devir hızını haftalık izleyin; hedef stok seviyesini sabitleyin.",
    ],
    "maliyet": [
        "Kritik olmayan harcamaları ve yeni alımları gözden geçirin.",
        "Gider kalemlerini gelir değişimiyle karşılaştırın; en hızlı artan kalemleri belirleyin.",
        "Kârlılığı düşük ürünleri, iskontoları ve müşteri koşullarını inceleyin.",
        "Brüt kâr marjını ve faaliyet giderleri / gelir oranını aylık izleyin.",
    ],
    "gelir": [
        "Gelir değişiminin kaynağını ürün, müşteri ve kanal bazında ayrıştırın.",
        "Fiyat ve hacim etkisini ayırın; kayıp müşteri ve talep nedenlerini belirleyin.",
        "Satış ve fiyat aksiyonlarını etki büyüklüğüne göre önceliklendirin.",
        "Gelir hedeflerini haftalık izleyin; erken uyarı eşiği tanımlayın.",
    ],
    "surdurulebilirlik": [
        "Nakit değişiminin kaynağını (faaliyet, finansman, yatırım) kalem bazında ayrıştırın.",
        "Tek seferlik kalemleri (varlık satışı, yeni borç, ertelenen ödeme) ayırın.",
        "Ertelenen harcamaların ve vadeli yükümlülüklerin gelecek dönem etkisini hesaplayın.",
        "Faaliyet nakit akışını ayrı hedefle haftalık izleyin.",
    ],
}
_PLAN_ONCELIK = ("tahsilat", "borc", "stok", "maliyet", "gelir", "surdurulebilirlik")
_PLAN_BASLIK = (
    "İlk 0-15 gün", "16-30 gün", "31-60 gün", "61-90 gün",
)
_PLAN_OZEL = {
    "tahsilat": "nakit tahsilatı", "borc": "borç vade yapısı",
    "stok": "stok kontrolü", "maliyet": "maliyet ve marj disiplini",
    "gelir": "gelirin kaynağı", "surdurulebilirlik": "nakit artışının sürdürülebilirliği",
}


def _kurallar(veri):
    y = lambda ad: veri.get(ad, (0, None))[0]
    p = lambda ad: veri.get(ad, (0, None))[1]
    liste = []

    def ekle(ozet, nedenler, riskler, gostergeler, plan, kapsam):
        liste.append({"ozet": ozet, "nedenler": nedenler, "riskler": riskler,
                      "gostergeler": gostergeler, "plan": plan, "kapsam": set(kapsam)})

    if y("gelir") > 0 and y("nakit") < 0:
        fark = ""
        if p("gelir") is not None and p("nakit") is not None:
            fark = (f" Gelir %{_s(p('gelir'))} artarken nakit %{_s(p('nakit'))} düşüyor; "
                    f"yönler arasındaki fark yaklaşık {_s(p('gelir') + p('nakit'))} puan.")
        ekle("Gelir artarken nakit akışı düşüyor: büyüme nakde dönüşmüyor." + fark,
             ["Vadeli satışların artması ve alacak tahsilatının gecikmesi; ciro muhasebeleşirken nakit henüz tahsil edilmemiş olabilir.",
              "Tedarikçi ödemeleri, ücretler ve diğer işletme giderlerinin tahsilattan önce yapılması."],
             ["Likidite açığı ve maaş/tedarikçi ödemelerinde gecikme."],
             ["Alacak tahsil süresi (DSO) ve borç ödeme süresi (DPO)",
              "Nakit dönüşüm döngüsü: DSO + DIO - DPO",
              "Faaliyet nakit akışı / net kâr"],
             ["tahsilat"], ["gelir", "nakit"])
    if y("gelir") < 0 and y("nakit") < 0:
        ekle("Gelir ve nakit akışı birlikte düşüyor: sorun talepten başlıyor olabilir.",
             ["Talep, fiyat veya pazar payı kaybı; kayıp müşteriler.",
              "Sabit giderlerin düşen gelire göre yüksek kalması."],
             ["Likidite açığı; gelir toparlanmazsa yükümlülüklerin karşılanamaması."],
             ["Gelir kırılımı (ürün, müşteri, kanal)", "Sabit gider / gelir oranı", "Cari oran ve asit-test oranı"],
             ["gelir", "maliyet"], ["gelir", "nakit"])
    if y("gelir") < 0 and y("nakit") > 0:
        ekle("Gelir düşerken nakit akışı artıyor: artış satış gücünden değil, başka kaynaklardan geliyor olabilir.",
             ["Alacakların tahsil edilmesi ve stokların eritilmesiyle işletme sermayesinin nakde çevrilmesi.",
              "Yatırım ve işletme harcamalarının ertelenmesi.",
              ("Varlık satışı veya sermaye girişi." if y("borc") < 0
               else "Yeni borçlanma veya varlık satışı.")],
             ["Nakit artışının tek seferlik olması; gelir kaybı sürerse sürdürülemezlik.",
              "Ertelenen harcamaların sonraki dönemde nakit baskısı yaratması."],
             ["Faaliyet / finansman / yatırım nakit akışı ayrımı", "Gelir kırılımı", "Nakit dönüşüm döngüsü (DSO, DIO, DPO)"],
             ["surdurulebilirlik", "gelir"], ["gelir", "nakit"])
    if y("stok") > 0 and y("gelir") > 0:
        ekle("Stok, gelirden hızlı birikiyor: satış hızı stok alımını karşılamıyor olabilir.",
             ["Stok alımlarının satışlardan hızlı artması; yavaş dönen, fazla veya modası geçen stokun birikmesi."],
             ["Stok değer düşüklüğü, bozulma ve elde tutma maliyeti."],
             ["Stokta kalma süresi (DIO) ve stok devir hızı"], ["stok"], ["stok"])
    elif y("stok") > 0 and y("gelir") <= 0:
        ekle("Stok artarken satışlar artmıyor: talep ile stok planı uyumsuz.",
             ["Talep tahmininin yanlış kalması; satılamayan stokun birikmesi."],
             ["Stok değer düşüklüğü, bozulma ve elde tutma maliyeti."],
             ["Stokta kalma süresi (DIO) ve stok devir hızı"], ["stok"], ["stok"])
    if y("stok") < 0 and y("gelir") < 0:
        ekle("Stok ve gelir birlikte düşüyor: stok satıştan çok tasfiye veya yeniden sipariş vermeme ile eriyor olabilir.",
             ["İndirimli tasfiye veya yeniden sipariş verilmemesi.",
              "Düşen satışların stoktan karşılanması."],
             ["Sonraki dönemde stok yetersizliği ve teslimat riski."],
             ["Stok devir hızı (DIO)", "Brüt kâr marjı"], ["stok", "gelir"], ["stok"])
    elif y("stok") < 0 and y("gelir") > 0:
        ekle("Stok azalırken gelir artıyor: stok devri hızlanıyor.",
             ["Satış hızının stok alımından yüksek olması."],
             ["Stok yetersizliği ve sipariş kaçırma riski."],
             ["Stok devir hızı (DIO)"], [], ["stok"])
    if y("borc") > 0 and y("nakit") < 0:
        ekle("Nakit azalırken kısa vadeli borç artıyor: işletme sermayesi borçla finanse ediliyor olabilir.",
             ["Kısa vadeli kredi kullanımı, kredi yenileme veya vadelerin yakın döneme yoğunlaşması."],
             ["Likidite baskısı ve kısa vadeli borçların çevrilememesi.",
              "Faiz yükünün artması."],
             ["Cari oran, asit-test oranı, net işletme sermayesi",
              "Vadesi gelen borç takvimi ve 13 haftalık nakit tahmini"],
             ["borc"], ["borc", "nakit"])
    elif y("borc") > 0:
        ekle("Kısa vadeli borç artıyor: vade yoğunlaşması ve faiz yükü izlenmeli.",
             ["Yeni borçlanma veya vadelerin yakın döneme kayması."],
             ["Kısa vadeli borçların çevrilememesi ve faiz yükünün artması."],
             ["Kısa vadeli borç / toplam borç oranı", "Cari oran"], ["borc"], ["borc"])
    if y("borc") < 0 and y("nakit") > 0:
        ekle("Nakit artarken borç azalıyor: likidite toparlanıyor.",
             ["Nakit üretiminin borç geri ödemesine dönüşmesi."],
             ["Nakdin tamamen borca gitmesi halinde operasyonel esnekliğin azalması."],
             ["Cari oran", "Net borç / faaliyet nakit akışı"], ["surdurulebilirlik"], ["borc", "nakit"])
    if y("alacak") > 0 and y("gelir") > 0:
        ekle("Alacaklar gelirle birlikte artıyor: satışların bir kısmı vadeli ve tahsil edilmeyi bekliyor.",
             ["Uzayan vadeler ve gevşek kredi politikası."],
             ["Tahsil edilemeyen alacaklar ve büyüyen işletme sermayesi ihtiyacı."],
             ["Alacak tahsil süresi (DSO)", "Alacak yaşlandırma raporu"], ["tahsilat"], ["alacak"])
    elif y("alacak") > 0:
        ekle("Alacaklar artıyor: tahsilat süreci yavaşlamış olabilir.",
             ["Müşterilerin geç ödemesi."],
             ["Tahsil edilemeyen alacaklar."],
             ["Alacak tahsil süresi (DSO)"], ["tahsilat"], ["alacak"])
    if y("alacak") < 0 and y("nakit") > 0:
        ekle("Alacaklar azalırken nakit artıyor: tahsilat iyileşiyor.",
             ["Tahsilat disiplininin güçlenmesi."],
             ["Satışların gevşeyen vade koşullarından kaçınılmasının gelir etkisi."],
             ["Alacak tahsil süresi (DSO)"], [], ["alacak", "nakit"])
    if y("gider") > 0 and y("gelir") > 0:
        gp, rp = p("gider"), p("gelir")
        if gp is not None and rp is not None and gp > rp:
            ozet = (f"Gider artışı (%{_s(gp)}) gelir artışını (%{_s(rp)}) aşıyor: kâr marjı baskı altında.")
        elif gp is not None and rp is not None:
            ozet = (f"Gider artışı (%{_s(gp)}) gelir artışının (%{_s(rp)}) altında: marj için doğrudan baskı görünmüyor.")
        else:
            ozet = "Gider ve gelir birlikte artıyor: artış oranları karşılaştırılmalı."
        ekle(ozet, ["Maliyet enflasyonu veya hacimden hızlı büyüyen işletme giderleri."],
             ["Kâr marjının erimesi ve nakit üretiminin zayıflaması."],
             ["Brüt kâr marjı", "Faaliyet giderleri / gelir oranı"], ["maliyet"], ["gider"])
    elif y("gider") > 0:
        ekle("Gider artarken gelir artmıyor: maliyet kontrolü gerekiyor.",
             ["Sabit giderlerin ve maliyetlerin gelir artışından bağımsız büyümesi."],
             ["Kâr marjının erimesi ve nakit yakımı."],
             ["Brüt kâr marjı", "Faaliyet giderleri / gelir oranı"], ["maliyet"], ["gider"])
    if y("marj") < 0:
        ekle("Kâr marjı düşüyor: büyüme kârlılıkla desteklenmiyor.",
             ["İskonto, ürün karması veya maliyet artışı."],
             ["Kârlılığın nakit üretimini desteklememesi."],
             ["Brüt kâr marjı", "Ürün ve müşteri bazlı kârlılık"], ["maliyet"], ["marj"])

    # Hiçbir kuralla kapsanmayan göstergeler için tekil değerlendirme.
    kapsanan = set().union(*[k["kapsam"] for k in liste]) if liste else set()
    tekil = {
        ("gelir", 1): ("Gelir artıyor: artışın hacim mi fiyat mı kaynaklı olduğu ayrıştırılmalı.", ["gelir"]),
        ("gelir", -1): ("Gelir düşüyor: talep, fiyat ve müşteri kaybı ayrıştırılmalı.", ["gelir"]),
        ("nakit", -1): ("Nakit akışı düşüyor: kısa vadeli ödeme gücü zayıflıyor.", ["borc"]),
        ("nakit", 1): ("Nakit akışı artıyor: kaynağı (faaliyet, finansman, yatırım) ayrıştırılmalı.", ["surdurulebilirlik"]),
        ("borc", -1): ("Borç azalıyor: geri ödemenin nakit ve vade etkisi izlenmeli.", []),
        ("stok", -1): ("Stok azalıyor: devir hızı ve stok yetersizliği riski izlenmeli.", []),
        ("alacak", -1): ("Alacaklar azalıyor: tahsilat veya satış vadesi değişimi doğrulanmalı.", []),
        ("gider", -1): ("Gider azalıyor: kalıcı tasarruf mu erteleme mi olduğu doğrulanmalı.", []),
        ("marj", 1): ("Kâr marjı artıyor: kalıcı mı geçici mi olduğu doğrulanmalı.", []),
    }
    for ad, (yon, _) in veri.items():
        if ad in kapsanan:
            continue
        ozet, plan = tekil.get((ad, yon), (f"{ETIKET[ad]} değişimi tek başına yorumlanamıyor.", []))
        riskler = ["Likidite açığı."] if (ad == "nakit" and yon < 0) else []
        ekle(ozet, [], riskler, [], plan, [ad])
    return liste


def _guven(n_yonlu, rakam_var):
    taban = {2: 0.75, 3: 0.86, 4: 0.92}.get(n_yonlu, 0.95 if n_yonlu >= 5 else 0.0)
    return round(taban - (0.0 if rakam_var else 0.03), 2)


def _tekil(liste, sinir):
    gorulen, sonuc = set(), []
    for x in liste:
        if x not in gorulen:
            gorulen.add(x)
            sonuc.append(x)
    return sonuc[:sinir]


def finansal_analiz_cevabi(mesaj, gorev_turu=None):
    """(cevap, güven) döndürür; uygun değilse ("", 0.0)."""
    n = _norm(mesaj)
    if _kod_istegi_mu(n):
        return "", 0.0
    veri, anilan = _oku(n)
    if len(veri) < 2:
        return "", 0.0
    if gorev_turu != "finansal_analiz" and not any(w in n for w in _ANALIZ_NIYETI):
        return "", 0.0

    rakam_var = any(v[1] is not None for v in veri.values())
    guven = _guven(len(veri), rakam_var)

    kurallar = _kurallar(veri)
    nedenler = _tekil([x for k in kurallar for x in k["nedenler"]], 6)
    riskler = _tekil([x for k in kurallar for x in k["riskler"]], 5)
    gostergeler = _tekil([x for k in kurallar for x in k["gostergeler"]], 7)
    plan_anahtari = _tekil([a for k in kurallar for a in k["plan"]], 6)
    plan_anahtari = [a for a in _PLAN_ONCELIK if a in plan_anahtari][:3] or ["surdurulebilirlik"]

    satirlar = ["## Finansal durum analizi", ""]
    satirlar.append("**Okunan veriler**")
    for ad in GOSTERGELER:
        if ad in veri:
            yon, yz = veri[ad]
            etiket = "▲ artış" if yon > 0 else "▼ düşüş"
            satirlar.append(f"- {ETIKET[ad]}: {etiket}" + (f" (%{_s(yz)})" if yz is not None else ""))
    satirlar.append("")

    ozetler = [k["ozet"] for k in kurallar][:2]
    satirlar.append("**Ön değerlendirme:** " + " ".join(ozetler)
                    + " Tek başına bu veriler kesin nedeni kanıtlamaz.")
    satirlar.append("")

    if nedenler:
        satirlar.append("**Olası nedenler**")
        satirlar.extend("- " + x for x in nedenler)
        satirlar.append("")
    if riskler:
        satirlar.append("**Başlıca finansal riskler**")
        satirlar.extend("- " + x for x in riskler)
        satirlar.append("")
    if gostergeler:
        satirlar.append("**Kontrol edilecek göstergeler**")
        satirlar.extend("- " + x for x in gostergeler)
        satirlar.append("")

    satirlar.append("**90 günlük uygulanabilir plan**")
    for i, baslik in enumerate(_PLAN_BASLIK):
        parcalar = []
        if i == 0:
            parcalar.append("Günlük nakit pozisyonu ve 13 haftalık nakit akış tahmini oluşturun.")
        parcalar.extend(_PLAN[a][i] for a in plan_anahtari)
        if i == 3:
            parcalar.append("Hedeflerden sapmalar için sorumlu ve düzeltici aksiyon atayın.")
        satirlar.append(f"{i + 1}. **{baslik}:** " + " ".join(parcalar))
    satirlar.append("")

    oncelik = " → ".join(_PLAN_OZEL[a] for a in plan_anahtari)
    satirlar.append(f"**Öncelik sırası:** {oncelik}.")

    eksik = [ETIKET[a] for a in GOSTERGELER if a not in veri]
    eksik_metin = (", ".join(eksik) + " verilmedi; ") if eksik else ""
    satirlar.append(
        f"**Eksik bilgi:** {eksik_metin}tutarlar, dönem, sektör ve bilanço kalemleri "
        "olmadan nedenler kesinleşmez. Yüzde değişimler tek başına yeterli değildir."
    )
    satirlar.append("")
    satirlar.append("Bu değerlendirme ön analizdir; denetim veya yatırım tavsiyesi değildir.")
    return "\n".join(satirlar), guven
