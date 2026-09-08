import unittest

from journal_registry import filter_by_journal, get_journal_profile, journal_filter_decision
from Paper_metadata_download import _attach_journal_profile


class JournalRegistryTests(unittest.TestCase):
    def test_uploaded_jcr_profile_is_recognised(self):
        profile = get_journal_profile("JMIR")
        self.assertEqual(profile["name"], "JOURNAL OF MEDICAL INTERNET RESEARCH")
        self.assertEqual(profile["jcr_quartile"], "Q1")
        self.assertEqual(profile["impact_factor"], 8.2)
        self.assertEqual(profile["impact_factor_year"], 2025)

    def test_unknown_journal_is_not_mislabelled(self):
        self.assertIsNone(get_journal_profile("A New Journal"))

    def test_unknown_journal_or_issn_is_retained(self):
        self.assertTrue(filter_by_journal(issns=["1438-8871"]))
        self.assertTrue(filter_by_journal(journal_name="JMIR", issns=["0000-0000"]))

    def test_unknown_journal_is_retained_for_no_automatic_exclusion(self):
        self.assertTrue(filter_by_journal(journal_name="A New Journal", issns=["0000-0000"]))

    def test_relevant_q1_flagship_is_in_whitelist_but_still_needs_topic_screening(self):
        self.assertTrue(filter_by_journal(issns=["0028-0836"]))

    def test_user_allowlisted_q3_journal_is_retained(self):
        self.assertTrue(filter_by_journal(issns=["1566-0702"]))
        self.assertEqual(
            journal_filter_decision(issns=["1566-0702"])[1], "q3_allowlisted"
        )

    def test_user_allowlisted_q4_journal_is_retained(self):
        self.assertTrue(filter_by_journal(journal_name="Journal of Psychophysiology"))
        self.assertEqual(
            journal_filter_decision(journal_name="Journal of Psychophysiology")[1],
            "q4_allowlisted",
        )

    def test_nonallowlisted_q4_journal_is_excluded(self):
        self.assertFalse(filter_by_journal(issns=["1947-2579"]))
        self.assertEqual(
            journal_filter_decision(issns=["1947-2579"])[1], "q4_excluded"
        )

    def test_best_quartile_is_used_when_journal_has_multiple_categories(self):
        profile = get_journal_profile(issns=["0048-5772"])
        self.assertEqual(profile["jcr_quartile"], "Q1")
        self.assertTrue(filter_by_journal(issns=["0048-5772"]))

    def test_download_record_receives_journal_metadata(self):
        paper = _attach_journal_profile(
            {"journal": "Journal of Medical Internet Research", "issns": ["1438-8871"]}
        )
        self.assertEqual(paper["journal_metrics"]["impact_factor"], 8.2)
        self.assertEqual(paper["journal_metrics"]["jcr_quartile"], "Q1")


if __name__ == "__main__":
    unittest.main()
