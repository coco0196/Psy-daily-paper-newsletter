import unittest

from domain_config import local_prefilter_decision


class LocalKeywordPrefilterTests(unittest.TestCase):
    def test_each_topic_line_can_pass_independently(self):
        examples = [
            ("Brain-heart coupling during affective stress", "A neurovisceral integration study."),
            ("Ecological momentary assessment of mood with PPG", "Participants completed smartphone prompts and wearable physiological monitoring."),
            ("A just-in-time adaptive intervention for anxiety", "The mobile intervention adapts support."),
            ("A mobile behavioral activation programme for depression", "A self-guided digital psychological intervention trial."),
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

    def test_heart_brain_medical_or_animal_record_is_rejected(self):
        result = local_prefilter_decision(
            "Heart-brain axis after myocardial infarction in mice",
            "We examined autonomic function following cardiac surgery in an animal model.",
        )
        self.assertFalse(result["accepted"])

    def test_synchronous_eeg_ecg_with_psychological_context_is_heart_brain(self):
        result = local_prefilter_decision(
            "Concurrent EEG and ECG during emotion regulation",
            "We examined brain-heart coupling during psychological stress.",
        )
        self.assertTrue(result["accepted"])
        self.assertIn("心脑轴", result["groups"])

    def test_eeg_or_ecg_alone_is_not_a_heart_brain_signal(self):
        result = local_prefilter_decision(
            "EEG markers of attention",
            "We examined cognitive processing in healthy adults.",
        )
        self.assertFalse(result["accepted"])

    def test_general_wellbeing_without_digital_or_intervention_signal_is_rejected(self):
        result = local_prefilter_decision(
            "Mindfulness and psychological wellbeing in university students",
            "A cross-sectional study of flourishing and resilience.",
        )
        self.assertFalse(result["accepted"])

    def test_mental_digital_track_requires_outcome_delivery_and_intervention(self):
        accepted = local_prefilter_decision(
            "A smartphone cognitive behavioral intervention for depression",
            "A randomized trial of a mobile mental health treatment.",
        )
        rejected = local_prefilter_decision(
            "Digital monitoring of depression symptoms",
            "A smartphone observational study of symptom trajectories.",
        )
        self.assertTrue(accepted["accepted"])
        self.assertFalse(rejected["accepted"])

    def test_questionnaire_only_ema_is_rejected_but_physiology_or_emi_is_accepted(self):
        questionnaire_only = local_prefilter_decision(
            "Ecological momentary assessment of mood",
            "Participants completed repeated self-report questionnaires.",
        )
        physiology_ema = local_prefilter_decision(
            "Experience sampling with ECG and PPG",
            "Ambulatory physiological monitoring assessed affect in daily life.",
        )
        emi = local_prefilter_decision(
            "A just-in-time adaptive intervention for anxiety",
            "A smartphone intervention delivered support in daily life.",
        )
        digital_phenotyping = local_prefilter_decision(
            "Digital phenotyping in intensive longitudinal mental health research",
            "Passive sensing captured daily-life behavioral signals.",
        )
        self.assertFalse(questionnaire_only["accepted"])
        self.assertTrue(physiology_ema["accepted"])
        self.assertTrue(emi["accepted"])
        self.assertTrue(digital_phenotyping["accepted"])

    def test_unrelated_record_is_rejected(self):
        result = local_prefilter_decision(
            "Novel surgical repair for hip fracture",
            "A randomized trial of orthopedic fixation techniques.",
        )
        self.assertFalse(result["accepted"])


if __name__ == "__main__":
    unittest.main()

