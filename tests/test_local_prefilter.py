import unittest

from domain_config import local_prefilter_decision


class LocalKeywordPrefilterTests(unittest.TestCase):
    def test_each_topic_line_can_pass_independently(self):
        examples = [
            ("Brain-heart coupling during affective stress", "A neurovisceral integration study."),
            ("Ecological momentary assessment of mood", "Participants completed smartphone prompts."),
            ("A just-in-time adaptive intervention for anxiety", "The mobile intervention adapts support."),
            ("Behavioral activation for depression", "A self-guided psychological intervention trial."),
        ]
        for title, abstract in examples:
            with self.subTest(title=title):
                self.assertTrue(local_prefilter_decision(title, abstract)["accepted"])

    def test_broad_term_needs_relevant_context(self):
        rejected = local_prefilter_decision(
            "Heart rate variability in postoperative recovery",
            "Cardiac monitoring after abdominal surgery.",
        )
        accepted = local_prefilter_decision(
            "Heart rate variability and emotion regulation",
            "A daily-life study of psychological stress.",
        )
        self.assertFalse(rejected["accepted"])
        self.assertTrue(accepted["accepted"])

    def test_unrelated_record_is_rejected(self):
        result = local_prefilter_decision(
            "Novel surgical repair for hip fracture",
            "A randomized trial of orthopedic fixation techniques.",
        )
        self.assertFalse(result["accepted"])


if __name__ == "__main__":
    unittest.main()
