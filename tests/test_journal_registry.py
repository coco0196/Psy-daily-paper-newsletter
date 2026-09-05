import unittest

from journal_registry import filter_by_journal, get_journal_profile
from Paper_metadata_download import _attach_journal_profile


class JournalRegistryTests(unittest.TestCase):
    def test_user_seed_journal_is_recognised(self):
        profile = get_journal_profile("JMIR")
        self.assertEqual(profile["name"], "Journal of Medical Internet Research")
        self.assertEqual(profile["jcr_quartile"], "Q1")
        self.assertIn("生态瞬时干预", profile["tracks"])

    def test_unknown_journal_is_not_mislabelled(self):
        self.assertIsNone(get_journal_profile("A New Journal"))

    def test_issn_match_is_required_when_issn_is_present(self):
        self.assertTrue(filter_by_journal(issns=["1438-8871"]))
        self.assertFalse(filter_by_journal(journal_name="JMIR", issns=["0000-0000"]))

    def test_q3_journal_is_not_in_whitelist(self):
        self.assertFalse(filter_by_journal(issns=["1070-5503"]))

    def test_download_record_receives_journal_metadata(self):
        paper = _attach_journal_profile(
            {"journal": "Journal of Medical Internet Research", "issns": ["1438-8871"]}
        )
        self.assertEqual(paper["journal_metrics"]["impact_factor"], 6.0)
        self.assertEqual(paper["journal_metrics"]["jcr_quartile"], "Q1")


if __name__ == "__main__":
    unittest.main()
