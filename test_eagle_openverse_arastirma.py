import unittest
from unittest.mock import patch

from eagle_openverse_arastirma import (
    kavram_coz, arastir
)


class OpenverseArastirmaTest(unittest.TestCase):

    def test_mitokondri(self):
        self.assertIn(
            "mitochondria",
            kavram_coz("Mitokondri")
        )

    def test_atp(self):
        self.assertIn(
            "adenosine triphosphate",
            kavram_coz("ATP")
        )

    def test_norvec(self):
        self.assertIn(
            "Norway",
            kavram_coz("Norveç")
        )

    def test_dinamik_kavram(self):
        self.assertEqual(
            kavram_coz("Ribozom", "Ribosome")[0],
            "Ribosome"
        )

    @patch("eagle_openverse_arastirma.dogrula")
    @patch("eagle_openverse_arastirma.ara")
    def test_erisim_ve_metadata(self, ara, dogrula):
        ara.return_value = [
            {
                "url": "https://live.staticflickr.com/a.jpg",
                "creator": "NIH",
                "license": "pdm",
                "source": "https://www.flickr.com/photos/test/1"
            },
            {
                "url": "https://live.staticflickr.com/b.jpg"
            }
        ]

        dogrula.side_effect = [True, False]

        sonuc = arastir("Mitokondri", "science")

        self.assertEqual(len(sonuc), 1)
        self.assertEqual(sonuc[0]["creator"], "NIH")
        self.assertEqual(sonuc[0]["license"], "pdm")

    @patch("eagle_openverse_arastirma.ara")
    def test_bos_sonuc(self, ara):
        ara.return_value = []
        self.assertEqual(
            arastir("ATP", "science"), []
        )


if __name__ == "__main__":
    unittest.main()
