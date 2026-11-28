import threading
import time

from concurrent.futures import ThreadPoolExecutor


class GorselMotoru:

    def __init__(self, kapasite=6):
        self._havuz = ThreadPoolExecutor(
            max_workers=kapasite,
            thread_name_prefix="eagle-image"
        )
        self._kapasite = threading.BoundedSemaphore(
            kapasite
        )

    def arastir(
        self,
        saglayicilar,
        secici,
        sure=8.0,
        limit=4
    ):
        baslangic = time.monotonic()
        son_zaman = baslangic + max(0, sure)

        kosul = threading.Condition()
        bulunan = []
        gorulen = {}
        durumlar = {}
        kapali = False

        def kalan():
            return max(
                0.0,
                son_zaman - time.monotonic()
            )

        def yayinla(aday):
            if not isinstance(aday, dict):
                return False

            url = aday.get("url")

            if not isinstance(url, str):
                return False

            if not url.startswith("https://"):
                return False

            with kosul:
                if kapali or kalan() <= 0:
                    return False

                if url in gorulen:
                    indeks = gorulen[url]
                    eski = bulunan[indeks]
                    if aday.get("_score", 0) <= eski.get("_score", 0):
                        return False
                    bulunan[indeks] = dict(aday)
                else:
                    gorulen[url] = len(bulunan)
                    bulunan.append(dict(aday))
                kosul.notify_all()

                return True

        def calistir(ad, fonksiyon):
            durum = "tamamlandi"

            try:
                if kalan() > 0:
                    fonksiyon(yayinla, kalan)
                else:
                    durum = "zaman_asimi"

            except Exception as hata:
                durum = "hata"
                print(
                    f"GORSEL SAGLAYICI HATA: {ad}: {hata}",
                    flush=True
                )

            finally:
                self._kapasite.release()

                with kosul:
                    durumlar[ad] = durum
                    kosul.notify_all()

        with kosul:
            for ad, fonksiyon in saglayicilar.items():

                if not self._kapasite.acquire(
                    blocking=False
                ):
                    durumlar[ad] = "yogun"
                    continue

                durumlar[ad] = "calisiyor"

                try:
                    self._havuz.submit(
                        calistir,
                        ad,
                        fonksiyon
                    )
                except Exception:
                    self._kapasite.release()
                    durumlar[ad] = "baslatilamadi"

            while True:


                if not any(
                    x == "calisiyor"
                    for x in durumlar.values()
                ):
                    break

                bekleme = kalan()

                if bekleme <= 0:
                    break

                kosul.wait(timeout=bekleme)

            kapali = True

            sonuc = secici(
                [dict(x) for x in bulunan],
                limit
            )

            son_durumlar = {
                ad: (
                    "zaman_asimi"
                    if durum == "calisiyor"
                    and kalan() <= 0
                    else "sonuc_hazir"
                    if durum == "calisiyor"
                    else durum
                )
                for ad, durum in durumlar.items()
            }

        return {
            "images": sonuc[:limit],
            "providers": son_durumlar,
            "elapsed": round(
                time.monotonic() - baslangic,
                3
            )
        }

    def kapat(self):
        self._havuz.shutdown(
            wait=False,
            cancel_futures=False
        )
