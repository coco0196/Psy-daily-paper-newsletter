import unittest

from domain_config import local_prefilter_decision


class LocalKeywordPrefilterTests(unittest.TestCase):
    def test_each_topic_line_can_pass_independently(self):
        examples = [
            ("Brain-heart coupling during affective stress", "Adult participants completed a neurovisceral integration study."),
            ("Ecological momentary assessment of mood with PPG", "Participants completed smartphone prompts and wearable physiological monitoring."),
            ("A just-in-time adaptive intervention for anxiety", "Adult participants received mobile intervention support."),
            ("A mobile behavioral activation programme for depression", "Participants received a self-guided digital psychological intervention."),
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
            "Adult participants completed a daily-life study of psychological stress.",
        )
        self.assertFalse(rejected["accepted"])
        self.assertTrue(accepted["accepted"])

    def test_brain_or_neural_words_do_not_supply_heart_brain_context(self):
        result = local_prefilter_decision(
            "Heart rate variability and brain structure",
            "We examined neural signals in healthy adults.",
        )
        self.assertFalse(result["accepted"])

    def test_heart_brain_medical_or_animal_record_is_rejected(self):
        result = local_prefilter_decision(
            "Heart-brain axis after myocardial infarction in mice",
            "We examined autonomic function following cardiac surgery in an animal model.",
        )
        self.assertFalse(result["accepted"])

    def test_animal_study_cannot_bypass_through_mental_health_track(self):
        result = local_prefilter_decision(
            "Mindfulness-related intervention for depression-like behavior in mice",
            "A mouse model received treatment and behavioral testing.",
        )
        self.assertFalse(result["accepted"])
        self.assertEqual(result["reason"], "animal_term_in_title_or_abstract")

    def test_synchronous_eeg_ecg_with_psychological_context_is_heart_brain(self):
        result = local_prefilter_decision(
            "Concurrent EEG and ECG during emotion regulation",
            "We examined brain-heart coupling during psychological stress in adult participants.",
        )
        self.assertTrue(result["accepted"])
        self.assertIn("eeg_ecg_psych_context", result["reason"])

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
            "Adult participants received a randomized mobile mental health intervention.",
        )
        rejected = local_prefilter_decision(
            "Digital monitoring of depression symptoms",
            "A smartphone observational study of symptom trajectories.",
        )
        self.assertTrue(accepted["accepted"])
        self.assertFalse(rejected["accepted"])

    def test_non_digital_mind_body_intervention_is_eligible(self):
        result = local_prefilter_decision(
            "HRV biofeedback for stress and insomnia",
            "Adult participants received a relaxation intervention assessing perceived stress and heart rate variability.",
        )
        self.assertTrue(result["accepted"])
        self.assertIn("mental_microintervention_candidate", result["reason"])

    def test_somatic_intervention_is_eligible(self):
        result = local_prefilter_decision(
            "Body-oriented psychotherapy for anxiety",
            "Patients received a somatic intervention evaluating emotional distress and psychological wellbeing.",
        )
        self.assertTrue(result["accepted"])
        self.assertIn("mental_microintervention_candidate", result["reason"])

    def test_direct_psychological_intervention_review_does_not_need_a_fixed_outcome_word(self):
        result = local_prefilter_decision(
            "A systematic review of psychological interventions",
            "This review synthesizes human psychological research on self-guided intervention methods.",
        )
        self.assertTrue(result["accepted"])
        self.assertIn("mental_microintervention_candidate", result["reason"])

    def test_review_without_an_actual_intervention_is_not_automatically_accepted(self):
        result = local_prefilter_decision(
            "A scoping review of mental wellbeing and emotion regulation",
            "This review synthesizes descriptive research in adults.",
        )
        self.assertFalse(result["accepted"])

    def test_local_prefilter_does_not_assign_topic_labels(self):
        result = local_prefilter_decision(
            "Concurrent EEG and ECG during emotion regulation",
            "Adult participants underwent brain-heart coupling measurement during psychological stress.",
        )
        self.assertTrue(result["accepted"])
        self.assertNotIn("groups", result)

    def test_questionnaire_only_ema_is_accepted_for_deepseek_screening(self):
        questionnaire_only = local_prefilter_decision(
            "Ecological momentary assessment of mood",
            "Participants completed repeated self-report questionnaires.",
        )
        physiology_ema = local_prefilter_decision(
            "Experience sampling with ECG and PPG",
            "Adult participants underwent ambulatory physiological monitoring of affect in daily life.",
        )
        emi = local_prefilter_decision(
            "A just-in-time adaptive intervention for anxiety",
            "Adult participants received smartphone intervention support in daily life.",
        )
        digital_phenotyping = local_prefilter_decision(
            "Digital phenotyping in intensive longitudinal mental health research",
            "Participants provided passive sensing data on daily-life behavioral signals.",
        )
        self.assertTrue(questionnaire_only["accepted"])
        self.assertTrue(physiology_ema["accepted"])
        self.assertTrue(emi["accepted"])
        self.assertTrue(digital_phenotyping["accepted"])

    def test_reviews_follow_the_same_rules_as_other_records(self):
        heart_review = local_prefilter_decision(
            "A systematic review of neurovisceral integration and emotion",
            "This review synthesizes human heart rate variability research in affective neuroscience.",
        )
        ema_review = local_prefilter_decision(
            "A systematic review of ecological momentary assessment in depression",
            "We review intensive longitudinal psychological assessment methods.",
        )
        self.assertTrue(heart_review["accepted"])
        self.assertTrue(ema_review["accepted"])

    def test_review_with_ema_and_objective_measurement_can_pass_normally(self):
        result = local_prefilter_decision(
            "A systematic review of digital phenotyping in depression",
            "This review synthesizes human intensive longitudinal passive sensing and wearable studies of mood.",
        )
        self.assertTrue(result["accepted"])
        self.assertIn("ecological_momentary_candidate", result["reason"])

    def test_animal_term_in_human_background_is_directly_rejected(self):
        result = local_prefilter_decision(
            "Heart rate variability and stress regulation",
            "Although relevant to human health, mice were exposed to chronic stress and received treatment.",
        )
        self.assertFalse(result["accepted"])
        self.assertEqual(result["reason"], "animal_term_in_title_or_abstract")

    def test_pure_mechanistic_record_without_required_signal_is_rejected(self):
        result = local_prefilter_decision(
            "Molecular mechanism of autonomic receptor signaling",
            "We characterized receptor expression and a signaling pathway in vitro.",
        )
        self.assertFalse(result["accepted"])
        self.assertEqual(result["reason"], "pure_mechanistic_without_required_signal")

    def test_generic_clinical_intervention_without_psychology_or_neuroscience_is_rejected(self):
        result = local_prefilter_decision(
            "Pain treatment after orthopedic surgery",
            "A randomized trial of postoperative analgesic treatment.",
        )
        self.assertFalse(result["accepted"])

    def test_generic_long_cbt_without_a_microintervention_anchor_is_rejected(self):
        result = local_prefilter_decision(
            "Cognitive behavioral therapy for depression",
            "Adult participants received a randomized psychotherapy program for depression.",
        )
        self.assertFalse(result["accepted"])

    def test_developmental_does_not_match_the_whole_word_mental(self):
        result = local_prefilter_decision(
            "Developmental outcomes after surgery",
            "Children received a rehabilitation intervention after surgery.",
        )
        self.assertFalse(result["accepted"])

    def test_human_signal_is_not_a_global_requirement(self):
        result = local_prefilter_decision(
            "A breathing intervention for stress",
            "A brief intervention assessed stress reduction.",
        )
        self.assertTrue(result["accepted"])

    def test_unrelated_record_is_rejected(self):
        result = local_prefilter_decision(
            "Novel surgical repair for hip fracture",
            "A randomized trial of orthopedic fixation techniques.",
        )
        self.assertFalse(result["accepted"])


if __name__ == "__main__":
    unittest.main()
