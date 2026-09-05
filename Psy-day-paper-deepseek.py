"""对候选文献进行 DeepSeek 语义筛选，并只生成 Newsletter。"""

import argparse
import json
import os
import re
import time

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from newsletter import NewsletterGenerator
from utils import (
    get_last_week_range,
    get_model_name,
    is_original_repo,
    require_auth,
    setup_logger,
    weekly_basename,
)


logger = setup_logger()


def _translation_marked_relevant(text):
    return bool(re.search(r"相关性\s*[:：]\s*是", str(text or "")))


def _translation_marked_irrelevant(text):
    return bool(re.search(r"相关性\s*[:：]\s*否", str(text or "")))


def _should_filter_by_relevance(text):
    return not _translation_marked_relevant(text) or _translation_marked_irrelevant(text)


def _response_has_required_fields(text):
    return all(marker in str(text or "") for marker in ("主题标签", "优先级", "标题", "摘要", "关键词"))


def _build_prompt(title, summary):
    return f"""你是一名严格的心理学与数字健康领域学术编辑。请根据标题和摘要判断论文是否应纳入文献周报。

【三条追踪主线】
1. 心脑轴：心脑交互/耦合、神经内脏整合、中央自主神经网络，以及与心理健康相关的 HRV、迷走神经和自主神经系统研究。
2. 生态瞬时干预：EMA/ESM、密集纵向测量、EMI、JITAI、微随机试验、数字表型、被动感知和实时个体化干预。
3. 心理健康与数字心理干预：心理健康、情绪调节、幸福感/复原力，以及数字、移动、自助或心理治疗干预。

【心脑轴特别规则】
HRV、迷走神经、自主神经系统或副交感神经相关研究，只有在明确涉及心理健康、精神障碍、情绪、压力、认知、行为、心理干预或日常生活动态测量时才相关。纯心血管疾病、手术、药物、解剖、生理机制、动物/细胞研究及无心理行为意义的研究一律排除。

标题：{title}
摘要：{summary}

【输出规则】
若不相关，仅输出：相关性：否

若相关，严格逐行输出。不要使用方括号、中括号、引号、Markdown 列表或 JSON。
主题标签只能使用以下三个标准名称；多标签以中文分号分隔：心脑轴；生态瞬时干预；心理健康与数字心理干预。

相关性：是
主题标签：心脑轴；生态瞬时干预
优先级：重点推荐
标题：中文标题
摘要：中文摘要
关键词：关键词一；关键词二；关键词三

“重点推荐”仅用于跨越两条及以上主线、或直接研究心脑指标与心理健康数字干预交叉的论文；否则标为“常规收录”。"""


@require_auth
def init_api_client():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("未设置 DEEPSEEK_API_KEY 环境变量")
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")


client = init_api_client()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
@require_auth
def call_deepseek_api(prompt):
    try:
        return client.chat.completions.create(
            model=get_model_name(),
            messages=[
                {
                    "role": "system",
                    "content": "你是严谨的心理学文献筛选与学术翻译助手。",
                },
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )
    except Exception:
        if not is_original_repo():
            logger.error("请确认 Fork 已配置有效的 DEEPSEEK_API_KEY")
        raise


def _paper_url(paper):
    paper_id = paper.get("id", "")
    if paper.get("source") == "Crossref":
        return f"https://doi.org/{paper_id}" if paper_id else ""
    return f"https://pubmed.ncbi.nlm.nih.gov/{paper_id}/" if paper_id else ""


def _read_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return default


def _remove_if_exists(*paths):
    for path in paths:
        if os.path.exists(path):
            os.remove(path)


def process_papers(start_date=None, end_date=None, weekly_key=None):
    if not weekly_key:
        if not start_date or not end_date:
            start_date, end_date = get_last_week_range()
        weekly_key = weekly_basename(start_date, end_date)
    elif not start_date or not end_date:
        start_date, end_date = weekly_key.split("_to_", 1)

    input_file = os.path.join("Paper_metadata_download", f"{weekly_key}_weekly.json")
    if not os.path.exists(input_file):
        logger.error("找不到候选文献数据：%s", input_file)
        return False
    papers = _read_json(input_file, [])
    if not papers:
        logger.error("候选文献数据为空：%s", input_file)
        return False

    work_dir = "Psy-day-paper-deepseek"
    os.makedirs(work_dir, exist_ok=True)
    temp_file = os.path.join(work_dir, f"{weekly_key}_temp.json")
    filtered_file = os.path.join(work_dir, f"{weekly_key}_filtered_titles.json")
    output_file = os.path.join(work_dir, f"{weekly_key}_Psy_deepseek_clean.json")
    results = _read_json(temp_file, [])
    filtered_titles = set(_read_json(filtered_file, []))
    processed_titles = {item.get("title") for item in results if item.get("title")} | filtered_titles

    success_count = 0
    error_count = 0
    delay = float(os.getenv("DEEPSEEK_INTER_REQUEST_DELAY_SECONDS", "3"))
    for index, entry in enumerate(papers, start=1):
        paper = entry.get("paper", {})
        title, summary = paper.get("title", ""), paper.get("summary", "")
        if not title or not summary or title in processed_titles:
            continue
        try:
            logger.info("正在处理第 %d/%d 篇候选文献", index, len(papers))
            response = call_deepseek_api(_build_prompt(title, summary))
            translation = (response.choices[0].message.content or "").strip()
            if _should_filter_by_relevance(translation):
                filtered_titles.add(title)
                with open(filtered_file, "w", encoding="utf-8") as handle:
                    json.dump(sorted(filtered_titles), handle, ensure_ascii=False, indent=2)
                continue
            if not _response_has_required_fields(translation):
                raise ValueError("DeepSeek 返回格式不完整")

            results.append(
                {
                    "title": title,
                    "summary": summary,
                    "translation": translation,
                    "url": _paper_url(paper),
                    "source": paper.get("source", "PubMed"),
                    "authors": paper.get("authors", []),
                    "journal": paper.get("journal", ""),
                    "published_at": paper.get("publishedAt", ""),
                    "issns": paper.get("issns", []),
                    "journal_metrics": paper.get("journal_metrics", {}),
                    "local_prefilter_groups": paper.get("local_prefilter_groups", []),
                }
            )
            processed_titles.add(title)
            success_count += 1
            with open(temp_file, "w", encoding="utf-8") as handle:
                json.dump(results, handle, ensure_ascii=False, indent=2)
        except Exception as exc:
            error_count += 1
            logger.error("第 %d 篇处理失败：%s", index, exc)
        if delay > 0:
            time.sleep(delay)

    logger.info("筛选完成：候选 %d，收录 %d，失败 %d", len(papers), success_count, error_count)
    if not results:
        return False
    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2)

    generated = NewsletterGenerator().generate_newsletter(start_date, end_date, weekly_key)
    if generated:
        # 成功后不保留中间筛选数据；工作流只提交 Newsletter。
        _remove_if_exists(temp_file, filtered_file, output_file)
    return generated


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="筛选文献并生成 Newsletter")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--weekly-key")
    args = parser.parse_args()
    raise SystemExit(0 if process_papers(args.start_date, args.end_date, args.weekly_key) else 1)
