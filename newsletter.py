"""生成按三条主线分栏的 Markdown / HTML Newsletter。"""

import argparse
import json
import os
import re
from collections import defaultdict

import markdown

from domain_config import CANONICAL_TOPIC_LABELS, REPORT_TITLE, normalize_topic_labels
from utils import get_last_week_range, get_logger, weekly_basename


logger = get_logger()


def _field(translation, name, multiline=False):
    pattern = rf"{re.escape(name)}\s*[:：]\s*(.+?)"
    end = r"(?=\n\s*(?:主题标签|优先级|标题|摘要|关键词)\s*[:：]|\Z)"
    match = re.search(pattern + (end if multiline else r"(?=\n|\Z)"), translation or "", re.DOTALL)
    return match.group(1).strip() if match else ""


def _authors_text(authors):
    if not authors:
        return "未提供"
    names = []
    for author in authors:
        if isinstance(author, dict):
            name = author.get("name") or " ".join(filter(None, (author.get("given"), author.get("family"))))
        else:
            name = str(author)
        if name:
            names.append(name)
    return ", ".join(names) if names else "未提供"


class NewsletterGenerator:
    def extract_paper_info(self, paper_data):
        translation = paper_data.get("translation", "") or ""
        labels = normalize_topic_labels(_field(translation, "主题标签"))
        priority = _field(translation, "优先级")
        priority = "重点推荐" if "重点" in priority else "常规收录"
        metrics = paper_data.get("journal_metrics") or {}
        return {
            "title": _field(translation, "标题") or paper_data.get("title", "未提供"),
            "original_title": paper_data.get("title", "未提供"),
            "summary": _field(translation, "摘要", multiline=True) or "未提供",
            "keywords": _field(translation, "关键词") or "未提供",
            "topic_labels": labels or ["未标注"],
            "priority": priority,
            "authors": _authors_text(paper_data.get("authors")),
            "journal": paper_data.get("journal") or "未提供",
            "published_at": paper_data.get("published_at") or paper_data.get("publishedAt") or "未提供",
            "impact_factor": metrics.get("impact_factor"),
            "impact_factor_year": metrics.get("impact_factor_year") or "",
            "jcr_quartile": metrics.get("jcr_quartile") or "待 JCR 数据核验",
            "metrics_status": metrics.get("metrics_status") or "待 JCR 数据核验",
            "paper_url": paper_data.get("url", ""),
            "source": paper_data.get("source", "原始来源"),
            "is_flagship": bool(metrics.get("is_flagship")),
        }

    @staticmethod
    def is_featured(paper):
        return (
            paper["priority"] == "重点推荐"
            or len([label for label in paper["topic_labels"] if label != "未标注"]) >= 2
            or paper["is_flagship"]
        )

    def _render_paper(self, paper, index):
        labels = "；".join(paper["topic_labels"])
        impact_factor = str(paper["impact_factor"] or paper["metrics_status"])
        if paper["impact_factor"] is not None and paper["impact_factor_year"]:
            impact_factor += f"（{paper['impact_factor_year']}）"
        return f"""### {index}. {paper['title']}

- 原文标题：{paper['original_title']}
- 作者：{paper['authors']}
- 期刊：{paper['journal']}
- IF：{impact_factor}
- JCR 分区：{paper['jcr_quartile']}
- 发表时间：{paper['published_at']}
- 主题标签：{labels}
- 优先级：{paper['priority']}
- 关键词：{paper['keywords']}

**摘要**：{paper['summary']}

**原文链接**：[{paper['source']}]({paper['paper_url']})
"""

    def render_markdown(self, papers, date_range):
        featured = [paper for paper in papers if self.is_featured(paper)]
        grouped = defaultdict(list)
        for paper in papers:
            if paper in featured:
                continue
            for label in paper["topic_labels"]:
                if label in CANONICAL_TOPIC_LABELS:
                    grouped[label].append(paper)

        lines = [f"# {REPORT_TITLE}（{date_range}）", "", f"本期收录 {len(papers)} 篇文献。"]
        if featured:
            lines.extend(["", "## 重点推荐", ""])
            lines.extend(self._render_paper(paper, index + 1) for index, paper in enumerate(featured))
        for label in CANONICAL_TOPIC_LABELS:
            lines.extend(["", f"## {label}", ""])
            section = grouped.get(label, [])
            if not section:
                lines.append("本期无符合条件的文献。")
            else:
                lines.extend(self._render_paper(paper, index + 1) for index, paper in enumerate(section))
        return "\n".join(lines).strip() + "\n"

    def generate_newsletter(self, start_date=None, end_date=None, weekly_key=None):
        if not weekly_key:
            start_date, end_date = get_last_week_range()
            weekly_key = weekly_basename(start_date, end_date)
        elif "_to_" in weekly_key:
            start_date, end_date = weekly_key.split("_to_", 1)
        source_file = os.path.join("Psy-day-paper-deepseek", f"{weekly_key}_Psy_deepseek_clean.json")
        if not os.path.exists(source_file):
            logger.error("未找到周报处理数据：%s", source_file)
            return False
        with open(source_file, "r", encoding="utf-8") as handle:
            raw_papers = json.load(handle)
        papers = [self.extract_paper_info(item) for item in raw_papers]
        if not papers:
            logger.info("%s 无入选论文，跳过 Newsletter", weekly_key)
            return False
        output_dir = "newsletters"
        os.makedirs(output_dir, exist_ok=True)
        markdown_text = self.render_markdown(papers, f"{start_date} 至 {end_date}")
        md_path = os.path.join(output_dir, f"{weekly_key}_weekly_paper.md")
        html_path = os.path.join(output_dir, f"{weekly_key}_weekly_paper.html")
        with open(md_path, "w", encoding="utf-8") as handle:
            handle.write(markdown_text)
        with open(html_path, "w", encoding="utf-8") as handle:
            handle.write(markdown.markdown(markdown_text, extensions=["extra"]))
        logger.info("Newsletter 已生成：%s 与 %s", md_path, html_path)
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成三主线文献 Newsletter")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--weekly-key")
    args = parser.parse_args()
    if not NewsletterGenerator().generate_newsletter(args.start_date, args.end_date, args.weekly_key):
        raise SystemExit(1)
