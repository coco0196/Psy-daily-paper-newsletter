import json
import os
import tempfile
import unittest

from analytics import AnalyticsGenerator


def _paper(labels, keywords):
    return {"topic_labels": labels, "keywords": keywords}


class AnalyticsTests(unittest.TestCase):
    def test_weekly_metrics_and_images_are_created_and_updated_idempotently(self):
        original = os.getcwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                generator = AnalyticsGenerator()
                first = generator.generate(
                    [
                        _paper(["心脑轴"], "心率变异性；压力"),
                        _paper(["生态瞬时干预", "心理健康与数字心理干预"], "JITAI；焦虑"),
                    ],
                    "2026-08-24_to_2026-08-30",
                    "2026-08-24 至 2026-08-30",
                )
                self.assertTrue(os.path.exists(first["wordcloud_path"]))
                self.assertTrue(os.path.exists(first["trend_path"]))
                self.assertIn("热门主题", first["markdown"])
                self.assertIn("关键词云图", first["markdown"])
                self.assertIn("三主线周度趋势", first["markdown"])

                generator.generate(
                    [_paper(["心理健康与数字心理干预"], "抑郁；移动干预")],
                    "2026-08-31_to_2026-09-06",
                    "2026-08-31 至 2026-09-06",
                )
                generator.generate(
                    [_paper(["心脑轴"], "迷走神经；情绪")],
                    "2026-08-24_to_2026-08-30",
                    "2026-08-24 至 2026-08-30",
                )
                with open("analytics/weekly_metrics.json", encoding="utf-8") as handle:
                    metrics = json.load(handle)
                self.assertEqual(len(metrics["weeks"]), 2)
                self.assertEqual(
                    metrics["weeks"]["2026-08-24_to_2026-08-30"]["total_papers"], 1
                )
            finally:
                os.chdir(original)


if __name__ == "__main__":
    unittest.main()
