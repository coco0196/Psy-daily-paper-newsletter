import os
import json
from datetime import datetime
import markdown
from jinja2 import Template
from utils import get_logger, get_last_week_range, weekly_basename
import re
import argparse
from collections import Counter
from domain_config import REPORT_TITLE

logger = get_logger()

class NewsletterGenerator:
    def __init__(self):
        self.template = """
# {{ report_title }}（{{ date_range }}）

## 📊 本周论文统计
- 总论文数：{{ total_papers }}
- 热门领域：{{ hot_topics }}

## 📝 论文详情

{% for paper in papers %}
### {{ loop.index }}. {{ paper.title }}

**原文标题：** {{ paper.original_title }}

**主题标签：** {{ paper.topic_labels }}  
**优先级：** {{ paper.priority }}

**摘要：**
{{ paper.summary }}

**关键词：** {{ paper.keywords }}

**论文链接：** [{{ paper.source }}]({{ paper.paper_url }})

{% if paper.code_url %}
**代码链接：** [GitHub]({{ paper.code_url }})
{% endif %}

---
{% endfor %}

## 🔍 关键词云图
![关键词云图](../images/keywords_wordcloud.png)

## 📈 近期论文趋势
![论文趋势](../images/daily_papers.png)

## 🎙️ 语音播报
- [收听本周论文解读](../{{ audio_path }})
"""

    def extract_paper_info(self, paper_data):
        """从论文数据中提取关键信息"""
        translation = paper_data.get("translation", "") or ""

        title_match = re.search(r"标题[:：]\s*([^\n]+)(?=\s*\n\s*摘要[:：]|\Z)", translation, re.DOTALL)
        summary_match = re.search(
            r"摘要[:：]\s*(.+?)(?=\s*(?:\n\s*关键词[:：]|\Z))",
            translation,
            re.DOTALL,
        )

        if not title_match:
            title_match = re.search(r"^([^\n]+)\n\s*摘要[:：]", translation, re.MULTILINE)

        title = (title_match.group(1) if title_match else paper_data.get("title", "")).strip()
        summary = (summary_match.group(1) if summary_match else "").strip()

        if not summary:
            for sep in ("摘要：", "摘要:"):
                if sep in translation:
                    tail = translation.split(sep, 1)[1].strip()
                    parts = re.split(r"(?:^|\n)\s*关键词\s*[:：]", tail, maxsplit=1)
                    summary = parts[0].strip()
                    break

        keywords_match = re.search(r"关键词\s*[:：]\s*([^\n]+)", translation)
        raw_kw = keywords_match.group(1).strip() if keywords_match else ""
        keywords = raw_kw if raw_kw else "未提取"
        topics_match = re.search(r"主题标签\s*[:：]\s*([^\n]+)", translation)
        priority_match = re.search(r"优先级\s*[:：]\s*([^\n]+)", translation)

        return {
            "title": title,
            "original_title": paper_data.get("title", ""),
            "summary": summary,
            "keywords": keywords,
            "topic_labels": topics_match.group(1).strip() if topics_match else "未标注",
            "priority": priority_match.group(1).strip() if priority_match else "常规收录",
            "paper_url": paper_data.get("url", ""),
            "source": paper_data.get("source", "未知来源"),
            "code_url": paper_data.get("paper", {}).get("code", ""),
        }

    def get_hot_topics(self, papers):
        """按 DeepSeek 主题标签汇总本周覆盖方向。"""
        topics = Counter()
        for paper in papers:
            raw_labels = paper.get("topic_labels", "")
            for label in re.split(r"[、,，;；/]", raw_labels):
                label = label.strip(" []")
                if label and label != "未标注":
                    topics[label] += 1
        return "、".join(label for label, _ in topics.most_common(4)) or "综合领域"

    def generate_newsletter(self, start_date=None, end_date=None, weekly_key=None):
        """生成每周论文简报"""
        if not weekly_key:
            if not start_date or not end_date:
                start_date, end_date = get_last_week_range()
            weekly_key = weekly_basename(start_date, end_date)
        else:
            if "_to_" in weekly_key:
                start_date, end_date = weekly_key.split("_to_", 1)
            elif not start_date or not end_date:
                start_date, end_date = get_last_week_range()

        date_range = f"{start_date} 至 {end_date}"

        try:
            json_file = os.path.join(
                'Psy-day-paper-deepseek', f"{weekly_key}_Psy_deepseek_clean.json"
            )
            if not os.path.exists(json_file):
                logger.error(f"未找到 {weekly_key} 的论文数据文件")
                return False

            with open(json_file, 'r', encoding='utf-8') as f:
                papers_data = json.load(f)

            if not isinstance(papers_data, list) or len(papers_data) == 0:
                logger.info(f"{date_range} 没有论文数据，跳过生成周报")
                return False

            papers = [self.extract_paper_info(paper) for paper in papers_data]
            if not papers:
                logger.warning("没有提取到有效的论文信息")
                return False

            audio_path = f'audio/{weekly_key}_weekly_papers.mp3'
            template_data = {
                'report_title': REPORT_TITLE,
                'date_range': date_range,
                'total_papers': len(papers),
                'hot_topics': self.get_hot_topics(papers),
                'papers': papers,
                'wordcloud_path': f'images/keywords_wordcloud.png',
                'trend_path': f'images/daily_papers.png',
                'audio_path': audio_path,
            }

            template = Template(self.template)
            newsletter_md = template.render(**template_data)
            newsletter_html = markdown.markdown(newsletter_md)

            output_dir = 'newsletters'
            os.makedirs(output_dir, exist_ok=True)

            md_path = os.path.join(output_dir, f"{weekly_key}_weekly_paper.md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(newsletter_md)

            html_path = os.path.join(output_dir, f"{weekly_key}_weekly_paper.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(newsletter_html)

            logger.info(f"周报已生成：{md_path}")
            return True

        except Exception as e:
            logger.error(f"生成周报时出错：{str(e)}")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='生成心理学论文周报')
    parser.add_argument('--start-date', type=str, help='周报起始日期 (YYYY-MM-DD格式)')
    parser.add_argument('--end-date', type=str, help='周报结束日期 (YYYY-MM-DD格式)')
    parser.add_argument('--weekly-key', type=str, help='周报文件基名，如 2026-05-26_to_2026-06-01')
    args = parser.parse_args()

    generator = NewsletterGenerator()
    success = generator.generate_newsletter(
        start_date=args.start_date,
        end_date=args.end_date,
        weekly_key=args.weekly_key,
    )
    if not success:
        exit(1)
    exit(0)
