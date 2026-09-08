"""Crossref 请求参数的回归测试。"""

import os
import sys
import unittest
from unittest.mock import patch


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Paper_metadata_download import _crossref_query_params, _fetch_crossref, _normalised_title_key
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

    def test_psychological_microintervention_pubmed_retrieval_uses_micro_and_somatic_paths(self):
        self.assertIn(") AND (", PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"stress"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"breathing intervention"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"micro-intervention"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"self-help exercise"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"somatic intervention"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"body-oriented psychotherapy"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"digital mental health"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertIn('"app-based intervention"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertNotIn('"therapy"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertNotIn('"trial"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertNotIn('"protocol"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)
        self.assertNotIn('"programme"[Title/Abstract]', PUBMED_MENTAL_HEALTH_QUERY)

    def test_pubmed_has_three_confirmed_modules_with_requested_abbreviations(self):
        self.assertEqual(set(PUBMED_QUERY_MODULES), {"heart_brain", "emi", "mental_health"})
        self.assertIn('"hrv"[title/abstract]', PUBMED_QUERY_MODULES["heart_brain"].lower())
        self.assertIn('"ema"[title/abstract]', PUBMED_QUERY_MODULES["emi"].lower())
        self.assertIn('"dmhi"[title/abstract]', PUBMED_QUERY_MODULES["mental_health"].lower())

    def test_crossref_uses_the_confirmed_nine_focused_topic_queries(self):
        self.assertEqual(CROSSREF_TRACK_QUERIES, {
            "heart_brain": (
                "heart brain axis heart brain interaction heart brain coupling cardiac brain synchrony heart brain synchrony brain heart coherence cardiac neural coupling neurocardiac interoception",
                "neurovisceral integration heart rate variability HRV vagal tone cardiac vagal control respiratory sinus arrhythmia psychophysiology emotion stress",
                "EEG ECG electroencephalography electrocardiography heart brain coupling cardiac neural coupling heartbeat evoked potential heart rate variability HRV",
            ),
            "emi": (
                "ecological momentary assessment EMA experience sampling ambulatory assessment intensive longitudinal",
                "ecological momentary intervention EMI just-in-time adaptive intervention JITAI just-in-time intervention micro-randomized trial MRT digital micro-intervention",
                "digital phenotyping passive sensing mobile sensing wearable sensing digital biomarkers",
            ),
            "mental_health": (
                "digital mental health digital psychological intervention smartphone intervention mobile intervention app-based intervention mHealth intervention iCBT",
                "digital therapeutics DMHI AI-assisted intervention wearable intervention mental health",
                "micro-intervention microintervention brief intervention single-session intervention mindfulness meditation breathing relaxation biofeedback somatic intervention stress emotion",
            ),
        })

    def test_crossref_limits_each_query_to_thirty_published_records_without_cursor(self):
        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"message": {"items": []}}

        with patch.dict(os.environ, {"CROSSREF_INTER_REQUEST_DELAY_SEC": "0"}), patch(
            "Paper_metadata_download._api_get", return_value=FakeResponse()
        ) as api_get:
            _fetch_crossref(object(), "2026-08-24", max_results_per_query=100)

        self.assertEqual(api_get.call_count, 9)
        for call in api_get.call_args_list:
            params = call.kwargs["params"]
            self.assertEqual(params["rows"], 30)
            self.assertNotIn("cursor", params)
            self.assertIn("from-pub-date:2026-08-24", params["filter"])
            self.assertIn("until-pub-date:2026-08-24", params["filter"])
            self.assertNotIn("index-date", params["filter"])


if __name__ == "__main__":
    unittest.main()
