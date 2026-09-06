"""Crossref 请求参数的回归测试。"""

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Paper_metadata_download import _crossref_query_params, _normalised_title_key
from domain_config import CROSSREF_TRACK_QUERIES, PUBMED_MENTAL_HEALTH_QUERY


class CrossrefQueryParamsTests(unittest.TestCase):
    def test_uses_supported_bibliographic_field_query(self):
        params = _crossref_query_params("ecological momentary assessment intervention")

        self.assertIn("query.bibliographic", params)
        self.assertNotIn("query.abstract", params)
        self.assertEqual(
            params["query.bibliographic"],
            "ecological momentary assessment intervention",
        )

    def test_title_key_deduplicates_terminal_punctuation_across_sources(self):
        pubmed_title = (
            "Immediate and Sustained Improvements in Mood and Stress Associated With Yuna, "
            "an AI-Powered Digital Mental Health Intervention: Real-World Retrospective Study."
        )
        crossref_title = pubmed_title.rstrip(".")
        self.assertEqual(_normalised_title_key(pubmed_title), _normalised_title_key(crossref_title))

    def test_mental_health_pubmed_retrieval_keeps_boolean_outcome_intervention_gate(self):
        self.assertIn(") AND (", PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"stress"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"breathing intervention"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"trial"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"therapy"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)

    def test_crossref_uses_two_targeted_queries_per_track(self):
        self.assertEqual(set(CROSSREF_TRACK_QUERIES), {"heart_brain", "emi", "mental_health"})
        self.assertTrue(all(len(queries) == 2 for queries in CROSSREF_TRACK_QUERIES.values()))


if __name__ == "__main__":
    unittest.main()
