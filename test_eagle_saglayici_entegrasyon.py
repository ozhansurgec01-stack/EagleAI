import unittest
from unittest.mock import patch
import requests
import eagle_derin_arastirma as m

from eagle_saglayici_kontrol import SaglayiciKontrol


class EntegrasyonTest(unittest.TestCase):

    def test_saglayici_koruma(self):
        r = requests.Response()
        r.status_code = 403

        calls = []

        def fake_search(provider, query, locale):
            calls.append((provider, query))

            if provider == "mojeek":
                raise requests.HTTPError(response=r)

            return [{"title": query}]

        with patch.object(
            m, "_SAGLAYICI_KONTROL",
            SaglayiciKontrol()
        ), patch.object(
            m, "_search_rows_raw",
            side_effect=fake_search
        ):
            with self.assertRaises(requests.HTTPError):
                m._search_rows(
                    "mojeek", "ATP", "tr-TR"
                )

            result = m._search_rows(
                "mojeek", "DNA", "tr-TR"
            )

            self.assertEqual(result, [])
            self.assertEqual(len(calls), 1)

            print("OK: Mojeek ikinci istek engellendi")

            for query in ("ATP", "DNA"):
                result = m._search_rows(
                    "ddg-lite", query, "tr-TR"
                )
                self.assertTrue(result)

            self.assertEqual(len(calls), 3)

            print("OK: DuckDuckGo calisiyor")
            print("OK: Alternatif sorgular korunuyor")
            print("OK: Saglayicilar bagimsiz")


if __name__ == "__main__":
    unittest.main()
