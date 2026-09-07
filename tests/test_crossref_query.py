"""Crossref 请求参数的回归测试。"""

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Paper_metadata_download import _crossref_query_params, _normalised_title_key
from domain_config import CROSSREF_TRACK_QUERIES, PUBMED_MENTAL_HEALTH_QUERY, PUBMED_QUERY_MODULES


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

    def test_mental_health_pubmed_retrieval_uses_focused_general_and_somatic_paths(self):
        self.assertIn(") AND (", PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"stress"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"breathing intervention"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"therapy"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"somatic intervention"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"body-oriented psychotherapy"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"digital mental health"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"app-based intervention"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertNotIn('"trial"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertNotIn('"protocol"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertNotIn('"programme"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)

    def test_pubmed_has_three_confirmed_modules_with_requested_abbreviations(self):
        self.assertEqual(set(PUBMED_QUERY_MODULES), {"heart_brain", "emi", "mental_health"})
        self.assertIn('"hrv"[title/abstract]', PUBMED_QUERY_MODULES["heart_brain"].lower())
        self.assertIn('"ema"[title/abstract]', PUBMED_QUERY_MODULES["emi"].lower())
        self.assertIn('"dmhi"[title/abstract]', PUBMED_QUERY_MODULES["mental_health"].lower())

    def test_crossref_uses_the_confirmed_seven_topic_queries(self):
        self.assertEqual(set(CROSSREF_TRACK_QUERIES), {"heart_brain", "emi", "mental_health"})
        self.assertEqual(sum(len(queries) for queries in CROSSREF_TRACK_QUERIES.values()), 7)
        self.assertIn("MRT", CROSSREF_TRACK_QUERIES["emi"][1])
        self.assertIn("digital therapeutics", CROSSREF_TRACK_QUERIES["mental_health"][0])


if __name__ == "__main__":
    unittest.main()
