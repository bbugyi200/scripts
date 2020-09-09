from pathlib import Path
import unittest

from bs4 import BeautifulSoup
from gutils.result import Err
from parameterized import parameterized
import suntimes


DATA_DIR = Path(__file__).parent / "data"


class TestSuntimes(unittest.TestCase):
    @parameterized.expand(
        [
            (
                "grise_20200813",
                "google_sunrise_search__20200813",
                suntimes.RiseOrSet.Rise,
                "06:10",
            ),
            (
                "gset_20200813",
                "google_sunset_search__20200813",
                suntimes.RiseOrSet.Set,
                "19:58",
            ),
        ]
    )
    def test_get_ts_from_google_search(
        self,
        _name: str,
        html_basename: str,
        rise_or_set: suntimes.RiseOrSet,
        expected_time_string: str,
    ) -> None:
        html_path = DATA_DIR / f"{html_basename}.html"
        soup = BeautifulSoup(html_path.read_text(), "lxml")
        time_string_result = suntimes._get_ts_from_google_search(
            soup, rise_or_set
        )

        if isinstance(time_string_result, Err):
            self.fail(
                "Error while scraping web page for suntime"
                " [type(time_string_result) == Err]."
            )

        time_string = time_string_result.ok()
        self.assertEqual(time_string, expected_time_string)


if __name__ == '__main__':
    unittest.main()
