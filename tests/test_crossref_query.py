"""Crossref 请求参数的回归测试。"""

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Paper_metadata_download import _crossref_query_params


class CrossrefQueryParamsTests(unittest.TestCase):
    def test_uses_supported_bibliographic_field_query(self):
        params = _crossref_query_params("ecological momentary assessment intervention")

        self.assertIn("query.bibliographic", params)
        self.assertNotIn("query.abstract", params)
        self.assertEqual(
            params["query.bibliographic"],
            "ecological momentary assessment intervention",
        )


if __name__ == "__main__":
    unittest.main()

