import re
import unicodedata


def _normalize(metin):
    metin = unicodedata.normalize("NFKD", str(metin or "").lower())
    metin = "".join(c for c in metin if not unicodedata.combining(c))
    return metin.replace("ı", "i")


def _sayi_bul(metin, terimler):
    for terim in terimler:
        eslesme = re.search(
            r"(?<!\d)(\d[\d.,]*)\s+" + re.escape(terim) + r"\b",
            metin
        )
        if eslesme:
            rakamlar = re.sub(r"\D", "", eslesme.group(1))
            if rakamlar:
                return f"{int(rakamlar):,}".replace(",", ".")
    return "belirtilmemiş"


def afet_koordinasyon_cevabi(mesaj):
    soru = _normalize(mesaj)

    afet_isaretleri = (
        "deprem", "afet", "enkaz", "toplu yaralanma",
        "yarali", "sahra hastanesi"
    )
    koordinasyon_isaretleri = (
        "triyaj", "aciliyet", "hastane", "ambulans",
        "kaynak", "siniflandir", "yonlendir"
    )

    if not (
        any(kelime in soru for kelime in afet_isaretleri)
        and any(kelime in soru for kelime in koordinasyon_isaretleri)
    ):
        return None

    hastane = _sayi_bul(soru, ("hastane", "hastaneler"))
    ambulans = _sayi_bul(soru, ("ambulans", "ambulanslar"))
    yarali = _sayi_bul(soru, ("yarali", "yaralilar", "hasta", "hastalar"))

    return f"""## Afet koordinasyon ve müdahale planı

**Senaryo girdileri:** {hastane} hastane, {ambulans} ambulans, {yarali} yaralı.

Bu plan karar desteğidir. Tıbbi triyaj ve sevk kararları yetkili sağlık ekipleri ve yürürlükteki afet protokolleri tarafından verilmelidir.

### 1. Olay yönetimi
- Tek bir koordinasyon merkezi kurulur; hastane, saha, ambulans ve lojistik sorumluları belirlenir.
- Her hastanenin hasarı, kullanılabilir yatakları, yoğun bakım kapasitesi, personeli ve kabul edebileceği hasta türleri teyit edilir.
- Bölge, güvenli erişim ve enkaz durumuna göre operasyon alanlarına ayrılır.

### 2. Triyaj
Eğitimli sağlık ekipleri, geçerli saha protokolünü kullanarak hastaları yeniden değerlendirir:
- **Kırmızı:** Acil ve gecikmeden müdahale/sevk gerekenler.
- **Sarı:** Ciddi yaralanması bulunan, kısa süreli gecikmeyi tolere edebilenler.
- **Yeşil:** Yürüyebilen ve daha hafif yaralanması olanlar; güvenli ayrı alanda değerlendirilir.
- **Siyah:** Yalnızca sahada yürürlükte olan triyaj protokolünün tanımına göre sınıflandırılır. Yaşam belirtisi bulunmaması veya beklenen/yaşam şansı çok düşük kategori değerlendirmesi, protokolün ölçütleri ve yetkili sağlık ekibinin kararıyla belirlenir. Sadece kaynak yetersizliği nedeniyle otomatik sınıflandırma yapılmaz.

Triyaj tek seferlik değildir; hastanın durumu değişebileceği için düzenli tekrar yapılır. Sayısal dağılım, sahadan gelen gerçek değerlendirme olmadan varsayılmaz.

### 3. Hastane dağıtımı
- Her hastanenin gerçek kabul kapasitesi ve uzmanlık alanı sürekli güncellenir.
- Hastalar yalnızca en yakın hastaneye değil, uygun tedaviyi güvenle sağlayabilecek ve kabulü doğrulanmış hastaneye yönlendirilir.
- Kırmızı hastalar için uygun acil müdahale kapasitesi önceliklendirilir.
- Hastane dolulukları ve yol erişimi değiştikçe sevk planı yeniden hesaplanır.

### 4. Ambulans yönlendirme
- Ambulanslar konum, ekipman, personel ve görev durumuna göre kayıt altına alınır.
- Görev ataması; hastanın önceliği, olay bölgesi, yol güvenliği ve hastane kabul bilgisine göre yapılır.
- Her görevde çıkış, hasta teslimi, hedef hastane ve ambulansın yeniden göreve hazır olma zamanı kaydedilir.
- Tek bir ambulansın aynı anda iki göreve atanması engellenir.

### 5. Elektrik ve internet yokken haberleşme
- Telsiz kanalları, sabit kontrol noktaları ve belirlenmiş haberci ekipleri kullanılır.
- Standart kâğıt formlar ve numaralı hasta/sevk kayıtları tutulur.
- Her kayıt için saat, konum, triyaj, ekip, hedef hastane ve teslim bilgisi yazılır.
- Haberleşme kesintilerinde son doğrulanmış bilgi ve kayıt zamanı esas alınır; belirsiz bilgi kesin kabul edilmez.

### 6. Kaynakların dağıtımı
- Oksijen, kan ürünleri, ilaç, sarf malzemesi, yakıt ve personel stokları düzenli sayılır.
- Dağıtım; klinik ihtiyaç, mevcut stok, yeniden tedarik süresi ve hizmetin devamlılığına göre yapılır.
- Kritik stoklar için asgari eşik belirlenir; eşik aşılınca ikmal talebi başlatılır.
- Bir hastaneye aşırı yığılma yerine, doğrulanmış kapasiteye göre dengeli dağıtım yapılır.

### 7. Örnek karar döngüsü
1. Saha ekipleri hastaları değerlendirip triyaj kayıtlarını oluşturur.
2. Koordinasyon merkezi hastane kabul kapasitesini telsizle doğrular.
3. Ambulans sorumlusu uygun ekibi ve güvenli güzergâhı atar.
4. Hastane teslimi telsiz ve kâğıt kayıtla teyit edilir.
5. Boşalan ambulans yeniden görevlendirilir; stok ve kapasite tablosu güncellenir.
6. Yeni bilgiler geldikçe triyaj ve sevk kararları tekrar değerlendirilir.

### 8. Temsili örnek uygulama
- Beş hastane H1-H5 olarak kaydedilir. Her birinin kabul durumu, travma/cerrahi imkânı, yoğun bakım kapasitesi ve güvenli ulaşım durumu telsizle doğrulanır.
- Cerrahi müdahale gerektiren kırmızı kategorideki bir hasta, yalnızca kabulü ve uygun uzmanlık kapasitesi doğrulanmış hastaneye gönderilir.
- Durumu kısa süreli gecikmeyi tolere edebilen sarı kategorideki hasta, uygun kapasitesi bulunan başka bir hastaneye yönlendirilerek tek merkeze yığılma azaltılır.
- Yeşil kategorideki hastalar, acil müdahale alanından ayrı güvenli bir değerlendirme noktasına alınır.
- Yirmi ambulansın tamamı aynı anda görevlendirilmez; aktif görev, ekip uygunluğu, yakıt ve dönüş süresi izlenerek hazır araçlar korunur.
- Bu örnek bir karar akışıdır; hasta sayıları veya hastanelere dağılım oranları gerçek saha verisi olmadan varsayılmaz. Elektronik sistemler devre dışı kalsa da kayıt, teyit ve sorumluluk zinciri sürdürülmelidir."""
