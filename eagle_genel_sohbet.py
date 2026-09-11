# -*- coding: utf-8 -*-

def genel_sohbet(mesaj):
    """
    EagleAI genel sohbet modülü.
    Ana motora bağlanmadan bağımsız olarak test edilebilir.
    """

    metin = str(mesaj or "").strip().lower()

    if not metin:
        return "🦅 Buradayım. Bir şey sorabilirsin."

    # Selamlaşma
    if any(x in metin for x in (
        "merhaba", "selam", "selamlar", "hey"
    )):
        return "Merhaba! 🦅 Nasıl gidiyor?"

    # Kimlik
    if "kimsin" in metin or "sen kimsin" in metin:
        return "🦅 Ben EagleAI. Sorularını anlayıp uygun şekilde yardımcı olmaya çalışırım."

    # Yetenekler
    if "ne yapabilirsin" in metin or "ne yapabiliyorsun" in metin:
        return (
            "🦅 Bilgi, matematik, Python, hava durumu, spor ve güncel konularda "
            "yardımcı olabilirim. Ayrıca günlük konularda fikir de üretebilirim."
        )

    # Nasılsın
    if "nasılsın" in metin or "nasilsin" in metin:
        return "İyiyim 😄 Hazırım, ne konuşalım?"

    # Teşekkür
    if any(x in metin for x in (
        "teşekkür", "tesekkur", "sağ ol", "sag ol"
    )):
        return "Rica ederim! 🦅"

    # Yemek önerisi
    if any(x in metin for x in (
        "ne pişirsem",
        "ne pisirsem",
        "ne yemek yapsam",
        "ne yemek yapayım",
        "ne yemek yapayim",
        "ne yemek yapabilirim"
    )):
        return (
            "Bugün için birkaç fikir: 🍝 makarna, 🍗 fırında tavuk, "
            "🥘 sebzeli yemek veya 🥪 pratik bir tost. "
            "İstersen seçtiğin yemeğin nasıl yapılacağını da anlatabilirim."
        )

    # Evde yapılabilecekler
    if "evde ne yapabilirim" in metin or "evde ne yapayım" in metin:
        return (
            "Evde yapabileceğin birkaç şey: film/dizi izlemek, kitap okumak, "
            "müzik dinlemek, kısa bir egzersiz yapmak veya yeni bir şey öğrenmek. 🦅"
        )

    # Can sıkıntısı
    if "canım sıkılıyor" in metin or "canim sıkılıyor" in metin:
        return (
            "O zaman küçük bir değişiklik iyi gelebilir 😄 "
            "Bir film açabilir, müzik dinleyebilir, oyun oynayabilir "
            "veya birlikte kısa bir sohbet/mini oyun yapabiliriz."
        )

    # Doğum günü / kutlama
    if "doğum gün" in metin or "dogum gun" in metin:
        return (
            "Samimi bir mesaj, küçük bir sürpriz veya birlikte güzel bir etkinlik "
            "iyi bir kutlama olabilir. İstersen sana kısa ve güzel bir doğum günü mesajı hazırlayabilirim."
        )

    # 🍗 Yemek takip soruları
    if "fırında tavuk" in metin and any(x in metin for x in (
        "nasıl yapılır", "nasil yapilir", "nasıl yapılır?", "tarif"
    )):
        return (
            "🍗 Fırında tavuk için: Tavukları baharat ve az yağla harmanla. "
            "İstersen yanına patates ve sebze ekle. Önceden ısıtılmış fırında "
            "tavuk tamamen pişene kadar pişir. Pişirme süresi parçanın türüne "
            "ve büyüklüğüne göre değişir."
        )

    if "makarna" in metin and any(x in metin for x in (
        "nasıl yapılır", "nasil yapilir", "tarif"
    )):
        return (
            "🍝 Makarna için: Suyu kaynatıp tuz ekle, makarnayı paketteki "
            "önerilen süre boyunca haşla. Süzdükten sonra istediğin sosla "
            "karıştır. Domatesli, yoğurtlu veya peynirli sos tercih edebilirsin."
        )

    # 🏠 Arkadaşlarla yapılabilecekler
    if "arkadaş" in metin and any(x in metin for x in (
        "ne yapabiliriz", "ne yapalım", "ne yapabilir"
    )):
        return (
            "🏠 Birlikte film gecesi yapabilir, kutu/masa oyunu oynayabilir, "
            "bir şeyler pişirebilir veya müzik açıp sohbet edebilirsiniz."
        )

    # 🎁 Doğum günü takip soruları
    if "doğum gün" in metin and any(x in metin for x in (
        "ne yapabilirim", "ne yapayım", "nasıl kutla", "ne alabilirim"
    )):
        return (
            "🎁 Küçük ama kişisel bir sürpriz güzel olabilir: sevdiği bir şeyi "
            "hazırlamak, birlikte vakit geçirmek veya samimi bir mesaj yazmak. "
            "İstersen bütçene göre birkaç farklı fikir de önerebilirim."
        )

    # Genel varsayılan
    return (
        "🦅 Bunu genel sohbet konusu olarak değerlendirdim. "
        "Biraz daha ayrıntı verirsen birlikte düşünebiliriz."
    )


if __name__ == "__main__":
    testler = [
        "Merhaba",
        "Kimsin?",
        "Ne yapabilirsin?",
        "Nasılsın?",
        "Teşekkür ederim",
        "Bugün ne pişirsem?",
        "Evde ne yapabilirim?",
        "Canım sıkılıyor",
        "Bir arkadaşımın doğum gününü nasıl kutlayabilirim?",
    ]

    for soru in testler:
        print(f"\nSORU: {soru}")
        print(f"CEVAP: {genel_sohbet(soru)}")
