import unittest

from eagle_gorsel_kalite import (
    uygun_mu,
    genel_gorsel_cesitlendir
)


class GenelGorselKaliteTest(unittest.TestCase):

    def sec(self, tur, basliklar):
        return [
            x["name"]
            for x in genel_gorsel_cesitlendir(
                [
                    {
                        "name": b,
                        "_score": 65,
                        "url": str(i)
                    }
                    for i, b in enumerate(basliklar)
                ],
                tur
            )
        ]

    def test_portre_tekrari(self):
        sonuc = self.sec("person", [
            "Albert Einstein Head.jpg",
            "Albert Einstein Head cropped.jpg",
            "Albert Einstein Head cleaned.jpg",
            "Albert Einstein Portrait.jpg"
        ])

        self.assertEqual(len(sonuc), 2)

        self.assertEqual(
            sonuc[0],
            "Albert Einstein Portrait.jpg"
        )

    def test_astronomi_onceligi(self):
        sonuc = self.sec("astronomy", [
            "Venus Transit Viewing",
            "Venus Surface"
        ])

        self.assertEqual(
            sonuc[0], "Venus Surface"
        )

    def test_nesne_onceligi(self):
        sonuc = self.sec("object", [
            "Violin Teacher",
            "Violin Player",
            "Violin Structure"
        ])

        self.assertEqual(
            sonuc[0], "Violin Structure"
        )

    def test_ilgisiz_kisi_gorselleri(self):
        for baslik in [
            "Albert Einstein Ariane Rollout",
            "Raumfrachter Albert Einstein",
            "Albert Einstein Ship",
            "Albert Einstein Statue"
        ]:
            with self.subTest(baslik=baslik):
                self.assertFalse(
                    uygun_mu(baslik, "", "person")
                )

    def test_gecerli_portre(self):
        self.assertTrue(
            uygun_mu(
                "Albert Einstein Portrait",
                "",
                "person"
            )
        )

    def test_baska_konular(self):
        for tur, iyi, kotu in [
            (
                "astronomy",
                "Mars Surface",
                "Mars Observation Event"
            ),
            (
                "object",
                "Piano Structure",
                "Piano Teacher"
            ),
            (
                "person",
                "Nikola Tesla Portrait",
                "Nikola Tesla Rollout"
            )
        ]:
            with self.subTest(tur=tur):
                self.assertEqual(
                    self.sec(tur, [kotu, iyi])[0],
                    iyi
                )


if __name__ == "__main__":
    unittest.main()
