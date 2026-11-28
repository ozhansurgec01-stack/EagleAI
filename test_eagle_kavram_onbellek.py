import unittest
from unittest.mock import patch

import eagle_api
import eagle_kavram_onbellek as cache


class KavramOnbellekTest(unittest.TestCase):

    def setUp(self):
        with cache._KILIT:
            cache._CACHE.clear()

        self.soru = "Venüs hakkında bilgi"

        self.kaynaklar = [{
            "title": "Venüs",
            "url": "https://tr.wikipedia.org/?curid=1911",
            "content_loaded": True,
            "english_title": "Venus",
            "topic_aliases": ["Venüs", "Venus"],
            "snippet": "Venüs bir gezegendir."
        }]

    def tearDown(self):
        with cache._KILIT:
            cache._CACHE.clear()

    def test_saklama_ve_okuma(self):
        self.assertTrue(
            cache.kaynaklari_sakla(
                self.soru, self.kaynaklar
            )
        )

        self.assertEqual(
            cache.kaynaklari_al(self.soru),
            self.kaynaklar
        )

    def test_bilinmeyen_soru(self):
        self.assertEqual(
            cache.kaynaklari_al("Bilinmeyen konu"),
            []
        )

    def test_guvensiz_kaynak(self):
        kaynak = dict(self.kaynaklar[0])
        kaynak["url"] = "https://example.com/venus"

        self.assertFalse(
            cache.kaynaklari_sakla(
                self.soru, [kaynak]
            )
        )

    def test_dogrulanmamis_kaynak(self):
        kaynak = dict(self.kaynaklar[0])
        kaynak["content_loaded"] = False

        self.assertFalse(
            cache.kaynaklari_sakla(
                self.soru, [kaynak]
            )
        )

    def test_sure_dolumu(self):
        with patch.object(
            cache.time, "monotonic", return_value=100
        ):
            cache.kaynaklari_sakla(
                self.soru, self.kaynaklar
            )

        with patch.object(
            cache.time, "monotonic", return_value=401
        ):
            self.assertEqual(
                cache.kaynaklari_al(self.soru), []
            )

    def test_kapasite(self):
        with patch.object(cache, "KAPASITE", 2):
            for soru in ["Bir", "Iki", "Uc"]:
                cache.kaynaklari_sakla(
                    soru, self.kaynaklar
                )

            self.assertEqual(len(cache._CACHE), 2)
            self.assertEqual(
                cache.kaynaklari_al("Bir"), []
            )

    def test_veri_izolasyonu(self):
        cache.kaynaklari_sakla(
            self.soru, self.kaynaklar
        )

        sonuc = cache.kaynaklari_al(self.soru)
        sonuc[0]["english_title"] = "Yanlis"

        self.assertEqual(
            cache.kaynaklari_al(self.soru)[0]
            ["english_title"],
            "Venus"
        )

    def test_apk_endpoint_cache_hit(self):
        cache.kaynaklari_sakla(
            self.soru, self.kaynaklar
        )

        with patch.object(
            eagle_api,
            "_eagle_gorsel_galerisi_uygun_mu",
            return_value=True
        ), patch.object(
            eagle_api,
            "_eagle_yer_gorsellerini_guvenli_getir",
            return_value=[]
        ) as motor:

            with eagle_api.app.test_request_context(
                "/api/gorseller",
                method="POST",
                json={
                    "message": self.soru,
                    "answer": "Venüs bir gezegendir."
                }
            ):
                cevap = eagle_api.eagle_bagimsiz_gorseller()

            self.assertTrue(cevap.get_json()["ok"])

            motor.assert_called_once_with(
                self.soru,
                "Venüs bir gezegendir.",
                kaynaklar=self.kaynaklar
            )

    def test_apk_endpoint_cache_miss(self):
        with patch.object(
            eagle_api,
            "_eagle_gorsel_galerisi_uygun_mu",
            return_value=True
        ), patch.object(
            eagle_api,
            "_eagle_yer_gorsellerini_guvenli_getir",
            return_value=[]
        ) as motor:

            with eagle_api.app.test_request_context(
               "/api/gorseller",
                method="POST",
                json={
                    "message": self.soru,
                    "answer": "Venüs bir gezegendir."
                }
            ):
                cevap = eagle_api.eagle_bagimsiz_gorseller()

            self.assertTrue(cevap.get_json()["ok"])

            motor.assert_called_once_with(
                self.soru,
                "Venüs bir gezegendir."
            )


if __name__ == "__main__":
    unittest.main()
