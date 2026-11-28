import unittest
from unittest.mock import patch
import eagle_api


class MerkeziEntegrasyonTest(unittest.TestCase):

    def test_iki_saglayici(self):

        def saglayici(ad, puan):
            def fabrika(*args, **kwargs):
                def calistir(yayinla, kalan):
                    yayinla({
                        "url": (
                            "https://upload.wikimedia.org/"
                            + ad + ".jpg"
                        ),
                        "name": ad,
                        "provider": ad,
                        "_score": puan
                    })
                return calistir
            return fabrika

        with patch(
            "eagle_gorsel_saglayicilar.openverse_saglayici",
            side_effect=saglayici("Openverse", 90)
        ), patch(
            "eagle_gorsel_saglayicilar.wikimedia_saglayici",
            side_effect=saglayici("Wikimedia Commons", 75)
        ):
            gelecek = eagle_api._openverse_baslat(
                "Test konu",
                "unknown",
                "Test entity",
                []
            )

            self.assertIsNotNone(gelecek)

            sonuc = gelecek.result(timeout=10)

            self.assertEqual(len(sonuc), 2)

            self.assertEqual(
                [x["provider"] for x in sonuc],
                ["Openverse", "Wikimedia Commons"]
            )

            self.assertEqual(sonuc[0]["_score"], 90)


if __name__ == "__main__":
    unittest.main()
