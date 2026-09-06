"""为三主线 Newsletter 生成可追溯的周度统计和图表。"""

import json
import os
import re
from collections import Counter
from datetime import datetime, timezone

import matplotlib
import jieba

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from wordcloud import WordCloud

from domain_config import CANONICAL_TOPIC_LABELS


ANALYTICS_DIR = "analytics"
METRICS_PATH = os.path.join(ANALYTICS_DIR, "weekly_metrics.json")
ASSETS_DIR = os.path.join("newsletters", "assets")

_CHINESE_STOPWORDS = {
    "研究", "结果", "方法", "分析", "影响", "作用", "相关", "患者", "样本",
    "干预", "心理", "健康", "心理健康", "数字", "研究者", "数据", "模型",
}
_ENGLISH_STOPWORDS = {
    "study", "studies", "research", "result", "results", "method", "methods",
    "analysis", "effect", "effects", "health", "mental", "psychological", "digital",
    "intervention", "interventions", "participants", "participant", "using", "based",
}
_FONT_CANDIDATES = (
    os.getenv("ANALYTICS_FONT_PATH", ""),
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
)
_TRACK_COLORS = ("#C44E52", "#4C72B0", "#55A868")


def _find_cjk_font():
    return next((path for path in _FONT_CANDIDATES if path and os.path.isfile(path)), None)


def _load_metrics():
    if not os.path.exists(METRICS_PATH):
        return {"schema_version": 1, "weeks": {}}
    try:
        with open(METRICS_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {"schema_version": 1, "weeks": {}}
    if not isinstance(data, dict) or not isinstance(data.get("weeks"), dict):
        return {"schema_version": 1, "weeks": {}}
    data["schema_version"] = 1
    return data


def _write_metrics(metrics):
    os.makedirs(ANALYTICS_DIR, exist_ok=True)
    with open(METRICS_PATH, "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _normalise_topic(term):
    term = re.sub(r"\s+", " ", str(term or "").strip())
    if not term:
        return ""
    folded = term.casefold()
    if folded in _ENGLISH_STOPWORDS or term in _CHINESE_STOPWORDS:
        return ""
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", term))
    english_chars = len(re.findall(r"[a-zA-Z]", term))
    if chinese_chars < 2 and english_chars < 3:
        return ""
    return term


def _keyword_frequencies(papers):
    frequencies = Counter()
    for paper in papers:
        seen = set()
        raw_keywords = str(paper.get("keywords") or "")
        terms = re.split(r"[；;，,、|\n]+", raw_keywords)
        if not raw_keywords.strip():
            terms = list(jieba.cut(str(paper.get("title") or "")))
        for term in terms:
            topic = _normalise_topic(term)
            if not topic:
                continue
            key = topic.casefold()
            if key not in seen:
                frequencies[topic] += 1
                seen.add(key)
    return frequencies


def _track_counts(papers):
    counts = {label: 0 for label in CANONICAL_TOPIC_LABELS}
    for paper in papers:
        for label in set(paper.get("topic_labels") or []):
            if label in counts:
                counts[label] += 1
    return counts


def _week_label(weekly_key):
    try:
        start, end = weekly_key.split("_to_", 1)
        return f"{start[5:]}\n{end[5:]}"
    except ValueError:
        return weekly_key


class AnalyticsGenerator:
    """生成可嵌入 Newsletter 的统计片段及其长期数据。"""

    def _write_wordcloud(self, frequencies, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        font_path = _find_cjk_font()
        if not frequencies:
            figure, axis = plt.subplots(figsize=(10, 5))
            axis.text(0.5, 0.5, "本期无可用于统计的关键词", ha="center", va="center", fontsize=16)
            axis.axis("off")
            figure.savefig(output_path, dpi=180, bbox_inches="tight")
            plt.close(figure)
            return
        cloud = WordCloud(
            width=1600,
            height=900,
            background_color="white",
            colormap="viridis",
            font_path=font_path,
            collocations=False,
        ).generate_from_frequencies(dict(frequencies.most_common(80)))
        figure, axis = plt.subplots(figsize=(12, 7))
        axis.imshow(cloud, interpolation="bilinear")
        axis.axis("off")
        figure.savefig(output_path, dpi=180, bbox_inches="tight")
        plt.close(figure)

    def _write_trend(self, weeks, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        ordered_keys = sorted(weeks)
        labels = [_week_label(key) for key in ordered_keys]
        font_path = _find_cjk_font()
        font_properties = FontProperties(fname=font_path) if font_path else None
        font_kwargs = {"fontproperties": font_properties} if font_properties else {}
        track_labels = CANONICAL_TOPIC_LABELS
        title = "三条主线周度收录趋势"
        x_label = "周次（起止日期）"
        y_label = "收录论文数"
        if not font_properties:
            # 本地开发环境未安装中文字体时仍可读；GitHub Actions 会安装 Noto CJK。
            track_labels = ("Heart-brain", "EMA/EMI", "Digital mental health")
            title = "Weekly three-track publication trend"
            x_label = "Week (start/end)"
            y_label = "Included papers"
        figure, axis = plt.subplots(figsize=(10, 5.5))
        for canonical_label, display_label, color in zip(CANONICAL_TOPIC_LABELS, track_labels, _TRACK_COLORS):
            values = [weeks[key].get("track_counts", {}).get(canonical_label, 0) for key in ordered_keys]
            axis.plot(labels, values, marker="o", linewidth=2.2, label=display_label, color=color)
        axis.set_title(title, **font_kwargs)
        axis.set_xlabel(x_label, **font_kwargs)
        axis.set_ylabel(y_label, **font_kwargs)
        axis.set_ylim(bottom=0)
        axis.grid(axis="y", alpha=0.28)
        axis.legend(prop=font_properties)
        figure.tight_layout()
        figure.savefig(output_path, dpi=180, bbox_inches="tight")
        plt.close(figure)

    @staticmethod
    def _previous_record(weeks, weekly_key):
        earlier = [key for key in weeks if key < weekly_key]
        return weeks[max(earlier)] if earlier else None

    def _render_markdown(self, record, previous, weekly_key):
        hot_topics = record["hot_topics"]
        topic_text = "；".join(f"{item['topic']}（{item['count']}）" for item in hot_topics) or "暂无可用关键词"
        track_text = "；".join(
            f"{label} {record['track_counts'].get(label, 0)} 篇" for label in CANONICAL_TOPIC_LABELS
        )
        change_line = "首个统计周，后续周报将显示与前一周的变化。"
        if previous:
            delta = record["total_papers"] - previous.get("total_papers", 0)
            change_line = f"较上一统计周 {'增加' if delta >= 0 else '减少'} {abs(delta)} 篇。"
        return "\n".join(
            [
                "## 数据分析",
                "",
                f"- 本周唯一收录：{record['total_papers']} 篇。",
                f"- 三条主线：{track_text}。",
                f"- {change_line}",
                "- 提示：交叉研究可同时计入多条主线，因此三条主线之和可能高于唯一论文数。",
                "",
                "### 热门主题",
                "",
                topic_text,
                "",
                "### 关键词云图",
                "",
                f"![{weekly_key} 关键词云图](assets/{weekly_key}_wordcloud.png)",
                "",
                "### 三主线周度趋势",
                "",
                f"![{weekly_key} 三主线周度趋势](assets/{weekly_key}_trend.png)",
            ]
        )

    def generate(self, papers, weekly_key, date_range):
        frequencies = _keyword_frequencies(papers)
        metrics = _load_metrics()
        previous = self._previous_record(metrics["weeks"], weekly_key)
        record = {
            "date_range": date_range,
            "total_papers": len(papers),
            "track_counts": _track_counts(papers),
            "hot_topics": [
                {"topic": topic, "count": count}
                for topic, count in frequencies.most_common(12)
            ],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        metrics["weeks"][weekly_key] = record
        _write_metrics(metrics)

        wordcloud_path = os.path.join(ASSETS_DIR, f"{weekly_key}_wordcloud.png")
        trend_path = os.path.join(ASSETS_DIR, f"{weekly_key}_trend.png")
        self._write_wordcloud(frequencies, wordcloud_path)
        self._write_trend(metrics["weeks"], trend_path)
        return {
            "markdown": self._render_markdown(record, previous, weekly_key),
            "wordcloud_path": wordcloud_path,
            "trend_path": trend_path,
            "metrics_path": METRICS_PATH,
        }
