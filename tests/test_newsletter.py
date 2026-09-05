import json
import os
import tempfile
import unittest

from domain_config import normalize_topic_labels
from newsletter import NewsletterGenerator


class NewsletterFormattingTests(unittest.TestCase):
    def test_legacy_json_style_label_is_normalized(self):
        self.assertEqual(
            normalize_topic_labels('["心理健康与数字心理干预"]'),
            ["心理健康与数字心理干预"],
        )

    def test_legacy_ema_and_emi_labels_merge(self):
        self.assertEqual(
            normalize_topic_labels("EMA/ESM 与密集纵向测量；EMI/JITAI 与微干预"),
            ["生态瞬时干预"],
        )

    def test_markdown_uses_three_sections_and_clean_labels(self):
        generator = NewsletterGenerator()
        paper = generator.extract_paper_info(
            {
                "title": "A mobile intervention for anxiety",
                "translation": """相关性：是
主题标签： [\"心理健康与数字心理干预\"]
优先级：常规收录
标题：焦虑的移动干预
摘要：一项随机试验。
关键词：焦虑；移动干预""",
                "authors": [{"name": "Ada Lovelace"}],
                "journal": "Example Journal",
                "published_at": "2026-09-01",
                "url": "https://example.org/paper",
                "source": "PubMed",
            }
        )
        rendered = generator.render_markdown([paper], "2026-09-01 至 2026-09-07")
        self.assertIn("## 心脑轴", rendered)
        self.assertIn("## 生态瞬时干预", rendered)
        self.assertIn("## 心理健康与数字心理干预", rendered)
        self.assertIn("主题标签：心理健康与数字心理干预", rendered)
        self.assertNotIn('["心理健康与数字心理干预"]', rendered)

    def test_end_to_end_newsletter_keeps_verified_journal_metadata(self):
        payload = [{
            "title": "A just-in-time intervention for anxiety",
            "translation": """相关性：是
主题标签：生态瞬时干预；心理健康与数字心理干预
优先级：重点推荐
标题：焦虑的即时干预
摘要：一项数字心理干预研究。
关键词：JITAI；焦虑""",
            "authors": [{"name": "Ada Lovelace"}],
            "journal": "Journal of Medical Internet Research",
            "published_at": "2026-09-01",
            "url": "https://example.org/paper",
            "source": "PubMed",
            "journal_metrics": {"impact_factor": 6.0, "jcr_quartile": "Q1"},
        }]
        original = os.getcwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                os.makedirs("Psy-day-paper-deepseek")
                with open(
                    "Psy-day-paper-deepseek/2026-09-01_to_2026-09-07_Psy_deepseek_clean.json",
                    "w",
                    encoding="utf-8",
                ) as handle:
                    json.dump(payload, handle, ensure_ascii=False)
                self.assertTrue(
                    NewsletterGenerator().generate_newsletter(
                        start_date="2026-09-01",
                        end_date="2026-09-07",
                        weekly_key="2026-09-01_to_2026-09-07",
                    )
                )
                with open(
                    "newsletters/2026-09-01_to_2026-09-07_weekly_paper.md",
                    encoding="utf-8",
                ) as handle:
                    rendered = handle.read()
                self.assertIn("IF：6.0", rendered)
                self.assertIn("JCR 分区：Q1", rendered)
                self.assertIn("主题标签：生态瞬时干预；心理健康与数字心理干预", rendered)
                self.assertTrue(os.path.exists("newsletters/2026-09-01_to_2026-09-07_weekly_paper.html"))
            finally:
                os.chdir(original)


if __name__ == "__main__":
    unittest.main()
