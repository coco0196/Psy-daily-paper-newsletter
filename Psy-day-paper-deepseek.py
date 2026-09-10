"""对候选文献进行 DeepSeek 语义筛选，并只生成 Newsletter。"""

import argparse
import hashlib
import json
import os
import re
import time

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from newsletter import NewsletterGenerator
from domain_config import CANONICAL_TOPIC_LABELS
from utils import (
    get_last_week_range,
    get_model_name,
    is_original_repo,
    require_auth,
    setup_logger,
    weekly_basename,
)


logger = setup_logger()

# 改动筛选准则时必须使旧缓存失效；否则同一篇论文会沿用旧提示词下的决定。
SCREENING_POLICY_VERSION = "2026-09-09-deepseek-final-labels-v5"


def _translation_marked_relevant(text):
    return bool(re.search(r"收录决定\s*[:：]\s*收录", str(text or "")))


def _translation_marked_irrelevant(text):
    return bool(re.search(r"收录决定\s*[:：]\s*排除", str(text or "")))


def _should_filter_by_relevance(text):
    return not _translation_marked_relevant(text) or _translation_marked_irrelevant(text)


def _response_has_required_fields(text):
    return all(marker in str(text or "") for marker in ("收录决定", "主题标签", "优先级", "标题", "摘要", "关键词"))


def _build_prompt(title, summary, journal="", journal_metrics=None):
    journal_metrics = journal_metrics or {}
    journal_context = "；".join(
        value
        for value in (
            f"期刊：{journal}" if journal else "",
            f"JCR：{journal_metrics.get('jcr_quartile')}" if journal_metrics.get("jcr_quartile") else "",
            f"IF：{journal_metrics.get('impact_factor')}" if journal_metrics.get("impact_factor") is not None else "",
            "旗舰期刊：是" if journal_metrics.get("is_flagship") else "",
        )
        if value
    ) or "期刊信息未提供"
    return f"""你是一名严谨的心理学学术编辑。请根据标题和摘要，判断论文是否与三条追踪主线具有明确、直接、高强度的连接，值得进入每周的前沿核心文献周报。

【三条追踪主线领域】
1. 心脑轴：研究脑—心/自主神经系统如何相互作用，包括心脑交互或耦合、神经内脏整合，以及与心理健康相关的 HRV、迷走神经、自主神经系统和 EEG-ECG 研究。
2. 生态瞬时研究：研究心理与行为如何在日常情境中动态变化、测量或适应性响应，包括 EMA/ESM、密集纵向、适应性干预、数字表型、被动感知、动态预测和日常多模态测量。
3. 心理微干预：研究低负担、短时的心理干预是否、如何产生改变，例如呼吸、正念、放松、生物反馈、自助练习与数字干预。

【共同纳入前提】
仅收录以人为研究对象、或主要讨论人类研究的综述和方法学研究，且处于心理学、健康心理学或神经科学语境。动物实验、细胞实验、体外实验，以及单纯神经、生物或生理机制分析一律排除。

【直接性阈值】
收录的文献必须与三条追踪主线领域高度相关。只有满足下列任一条件才收录：（1）论文的主要研究问题、核心方法或主要结局直接属于心脑轴、生态瞬时研究或心理微干预；（2）论文是以这些主题为核心对象的人类研究综述或方法综述。仅在背景中提及、仅为次要测量、泛相邻主题、泛方法、泛心理干预、泛数字健康、部分相关、无法确认或不十分相关时，一律排除。

【心脑轴特别规则】
HRV、迷走神经、自主神经系统或副交感神经相关研究，只有在明确在心理学语境下，涉及心理健康、身心交互、精神障碍、情绪、压力、心理干预、日常生活动态测量、神经科学等心理学相关问题下时才相关。纯心血管疾病、手术、药物、解剖、生理机制、生化机制及无心理行为意义的研究一律排除。

【生态瞬时研究特别规则】
直接研究 EMA/ESM、密集纵向测量、EMI、JITAI、微随机试验、数字表型、被动感知、动态预测或日常多模态测量中的至少一种，或用MA/ESM、密集纵向测量、EMI、JITAI、微随机试验等方法探究心理健康干预问题。仅因出现 ECG、PPG、HRV、EEG、可穿戴或 App，不能标注为本主题；这些要素必须构成日常动态研究设计、主要测量或适应性响应。若主要问题是心理生理、心脑交互、迷走神经或自主神经关系，应优先判断为“心脑轴”。

【心理微干预特别规则】
必须同时满足：（1）心理、情绪、行为、主观体验或心理生理指标是主要结局或核心目标；（2）研究实际聚焦明确的微干预、简短干预、自助练习、数字干预或身心干预。特别关注正念、呼吸训练、冥想、放松训练、HRV 生物反馈等身心取向干预。笼统的长程 CBT、ACT 等心理治疗若没有与 EMA/ESM、EMI/JITAI、微干预、数字递送、心脑或心理生理联系，一律排除。

标题：{title}
摘要：{summary}
{journal_context}

【输出规则】
若应排除，仅输出：收录决定：排除

若相关，严格逐行输出。不要使用方括号、中括号、引号、Markdown 列表或 JSON。
你无需提供标签判定依据。主题标签只能使用以下三个标准名称；多标签以中文分号分隔：心脑轴；生态瞬时研究；心理微干预，允许多选。

收录决定：收录
主题标签：标签1
优先级：重点推荐
标题：中文标题
摘要：中文摘要
关键词：关键词一；关键词二；关键词三

“重点推荐”与“是否收录”完全独立，仅用于以下任一情形：真实跨越两条及以上主线；明确将 EMA/ESM、EMI/JITAI 与 ECG、PPG、HRV等客观生理数据紧密结合；心脑指标被直接用于身心干预；同时测量 EEG 与 ECG；顶级期刊且具有显著方法学/临床价值的研究。其他直接相关论文一律标为“常规收录”。"""


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
            temperature=0,
        )
    except Exception:
        if not is_original_repo():
            logger.error("请确认 Fork 已配置有效的 DEEPSEEK_API_KEY")
        raise


def _paper_url(paper):
    doi = str(paper.get("doi", "")).strip()
    if doi:
        return f"https://doi.org/{doi}"
    paper_id = paper.get("id", "")
    if paper.get("source") == "Crossref":
        return f"https://doi.org/{paper_id}" if paper_id else ""
    return f"https://pubmed.ncbi.nlm.nih.gov/{paper_id}/" if paper_id else ""


def _screening_identity(paper):
    doi = str(paper.get("doi", "")).strip().casefold()
    if doi:
        return f"doi:{doi}"
    pmid = str(paper.get("pmid", "")).strip()
    if pmid:
        return f"pmid:{pmid}"
    title = re.sub(r"\W+", "", str(paper.get("title", "")).casefold())
    summary = str(paper.get("summary", "")).casefold()
    return "text:" + hashlib.sha256(f"{title}\n{summary}".encode("utf-8")).hexdigest()


def _content_hash(title, summary):
    return hashlib.sha256(
        f"{SCREENING_POLICY_VERSION}\n{title}\n{summary}".encode("utf-8")
    ).hexdigest()


def _topic_labels_line(translation):
    match = re.search(r"^主题标签\s*[:：]\s*(.+)$", translation or "", re.MULTILINE)
    return match.group(1).strip() if match else ""


def _replace_topic_labels(translation, labels):
    value = "；".join(labels)
    return re.sub(
        r"^主题标签\s*[:：]\s*.+$",
        f"主题标签：{value}",
        translation,
        count=1,
        flags=re.MULTILINE,
    )


def _validated_model_labels(translation):
    """验证 DeepSeek 的最终标签，不以本地关键词覆写或补充标签。"""
    raw_labels = _topic_labels_line(translation)
    labels = [part.strip() for part in re.split(r"[；;]", raw_labels) if part.strip()]
    if not labels or len(labels) != len(set(labels)):
        return ""
    if any(label not in CANONICAL_TOPIC_LABELS for label in labels):
        return ""
    return _replace_topic_labels(translation, labels)


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


def _result_from_paper(paper, translation):
    return {
        "title": paper.get("title", ""),
        "summary": paper.get("summary", ""),
        "translation": translation,
        "url": _paper_url(paper),
        "source": " + ".join(paper.get("sources", []) or [paper.get("source", "PubMed")]),
        "authors": paper.get("authors", []),
        "journal": paper.get("journal", ""),
        "published_at": paper.get("publishedAt", ""),
        "publication_date_source": paper.get("publicationDateSource", ""),
        "issns": paper.get("issns", []),
        "journal_metrics": paper.get("journal_metrics", {}),
    }


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
    cache_file = os.path.join(work_dir, f"{weekly_key}_screening_cache.json")
    output_file = os.path.join(work_dir, f"{weekly_key}_Psy_deepseek_clean.json")
    cache = _read_json(cache_file, {"schema_version": 1, "entries": {}})
    if not isinstance(cache, dict) or cache.get("schema_version") != 1:
        cache = {"schema_version": 1, "entries": {}}
    cache_entries = cache.setdefault("entries", {})
    results = []

    success_count = 0
    error_count = 0
    cache_hit_count = 0
    seen_identities = set()
    delay = float(os.getenv("DEEPSEEK_INTER_REQUEST_DELAY_SECONDS", "3"))
    for index, entry in enumerate(papers, start=1):
        paper = entry.get("paper", {})
        title, summary = paper.get("title", ""), paper.get("summary", "")
        identity = _screening_identity(paper)
        if not title or not summary or identity in seen_identities:
            continue
        seen_identities.add(identity)
        fingerprint = _content_hash(title, summary)
        cached = cache_entries.get(identity, {})
        if cached.get("content_hash") == fingerprint:
            cache_hit_count += 1
            if cached.get("decision") == "accepted" and cached.get("translation"):
                results.append(_result_from_paper(paper, cached["translation"]))
            continue
        try:
            logger.info("正在处理第 %d/%d 篇候选文献", index, len(papers))
            response = call_deepseek_api(
                _build_prompt(title, summary, paper.get("journal", ""), paper.get("journal_metrics"))
            )
            translation = (response.choices[0].message.content or "").strip()
            if _should_filter_by_relevance(translation):
                cache_entries[identity] = {
                    "content_hash": fingerprint,
                    "decision": "rejected",
                    "translation": translation,
                }
                with open(cache_file, "w", encoding="utf-8") as handle:
                    json.dump(cache, handle, ensure_ascii=False, indent=2)
                continue
            if not _response_has_required_fields(translation):
                raise ValueError("DeepSeek 返回格式不完整")
            translation = _validated_model_labels(translation)
            if not translation:
                raise ValueError("DeepSeek 返回的主题标签为空、重复或不属于三个标准标签")
            results.append(_result_from_paper(paper, translation))
            cache_entries[identity] = {
                "content_hash": fingerprint,
                "decision": "accepted",
                "translation": translation,
            }
            success_count += 1
            with open(cache_file, "w", encoding="utf-8") as handle:
                json.dump(cache, handle, ensure_ascii=False, indent=2)
        except Exception as exc:
            error_count += 1
            logger.error("第 %d 篇处理失败：%s", index, exc)
        if delay > 0:
            time.sleep(delay)

    logger.info(
        "筛选完成：候选 %d，新收录 %d，缓存复用 %d，失败 %d",
        len(papers), success_count, cache_hit_count, error_count,
    )
    if not results:
        return False
    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2)

    generated = NewsletterGenerator().generate_newsletter(start_date, end_date, weekly_key)
    if generated:
        # 工作流只提交 Newsletter。筛选缓存由 GitHub Actions 缓存保存，不进入仓库。
        _remove_if_exists(output_file)
    return generated


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="筛选文献并生成 Newsletter")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--weekly-key")
    args = parser.parse_args()
    raise SystemExit(0 if process_papers(args.start_date, args.end_date, args.weekly_key) else 1)
