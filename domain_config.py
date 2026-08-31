"""领域配置：心脑轴、日常密集测量与数字心理健康追踪。"""

REPORT_TITLE = "心脑与数字心理健康文献周报"
REPORT_SHORT_TITLE = "心脑与数字心理健康"

# 每个主题组都独立入选；同一篇论文命中多组时，在报告中标为重点推荐。
TOPIC_GROUPS = {
    "heart_brain": {
        "label": "心脑轴/心脑耦合",
        "terms": [
            "heart-brain axis", "brain-heart axis",
            "brain-heart interaction", "brain-heart interactions",
            "heart-brain interaction", "heart-brain interactions",
            "brain-heart coupling", "heart-brain coupling",
            "brain-heart dynamics", "neurovisceral integration",
            "central autonomic network", "heart rate variability",
            "vagally mediated heart rate variability",
            "respiratory heart rate variability", "respiratory sinus arrhythmia",
            "heartbeat evoked potential", "heartbeat evoked potentials",
        ],
    },
    "ema": {
        "label": "EMA/ESM 与密集纵向测量",
        "terms": [
            "ecological momentary assessment", "experience sampling",
            "experience sampling method", "ambulatory assessment",
            "intensive longitudinal", "intensive longitudinal data",
            "daily diary",
        ],
    },
    "digital_intervention": {
        "label": "EMI/JITAI 与微干预",
        "terms": [
            "ecological momentary intervention", "just-in-time adaptive intervention",
            "just-in-time intervention", "micro-randomized trial",
            "micro-randomized trials", "digital micro-intervention",
            "digital micro-interventions", "microintervention", "microinterventions",
            "context-aware intervention", "adaptive intervention",
            "adaptive treatment", "personalized intervention",
            "personalised intervention", "digital phenotyping",
            "passive sensing", "mobile sensing", "mobile health",
        ],
    },
    "mental_health": {
        "label": "心理健康与数字心理干预",
        "terms": [
            "mental health", "mental well-being", "mental wellbeing",
            "psychological well-being", "psychological wellbeing", "flourishing",
            "resilience", "emotion regulation", "self-guided intervention",
            "self-guided interventions", "self-help intervention",
            "self-help interventions", "digital intervention", "digital interventions",
            "mobile intervention", "mobile interventions", "behavioral activation",
            "acceptance and commitment therapy", "mindfulness",
        ],
    },
}

# Crossref 的查询质量通常低于 PubMed；限制为特异性最高的主题词，完整性由
# PubMed 覆盖，Crossref 用来补充尚未进入 PubMed 的带摘要记录。
CROSSREF_QUERY_TERMS = [
    "heart-brain interaction", "heart rate variability",
    "ecological momentary assessment", "experience sampling",
    "just-in-time adaptive intervention", "ecological momentary intervention",
    "micro-randomized trial", "digital phenotyping", "digital mental health",
]


def iter_topic_terms():
    """按主题组依次返回不重复的 PubMed 检索词。"""
    seen = set()
    for group in TOPIC_GROUPS.values():
        for term in group["terms"]:
            key = term.lower()
            if key not in seen:
                seen.add(key)
                yield term


# 本地预筛在调用 DeepSeek 前运行。它并不替代后续的语义筛选：目标是剔除仅因
# "mental health"、"mobile health"、"heart rate variability" 等宽泛词而被检索到、
# 但与本周报主题明显无关的记录，从而降低 API 调用量。
#
# 核心术语单独命中即可进入 AI 评审；宽泛术语必须同时命中一个心理/行为、数字
# 干预或脑-心研究语境词。四条主题线仍独立处理，任一主题线满足条件就会保留。
LOCAL_PREFILTER_BROAD_TERMS = {
    "heart_brain": {
        "heart rate variability",
        "autonomic nervous system",
    },
    "ema": set(),
    "digital_intervention": {
        "adaptive intervention",
        "adaptive treatment",
        "personalized intervention",
        "personalised intervention",
        "digital phenotyping",
        "passive sensing",
        "mobile sensing",
        "mobile health",
    },
    "mental_health": {
        "mental health",
        "mental well-being",
        "mental wellbeing",
        "psychological well-being",
        "psychological wellbeing",
        "flourishing",
        "resilience",
        "emotion regulation",
        "mindfulness",
        "digital intervention",
        "digital interventions",
        "mobile intervention",
        "mobile interventions",
    },
}

LOCAL_PREFILTER_CONTEXT_TERMS = {
    "mental", "psycholog", "psychiatr", "well-being", "wellbeing",
    "depress", "anxiety", "stress", "emotion", "behavior", "behaviour",
    "cognitive", "intervention", "treatment", "therap", "mindfulness",
    "ecological", "experience sampling", "ambulatory", "daily diary",
    "digital", "mobile", "smartphone", "wearable", "passive sensing",
    "brain", "neural", "neuro", "heart-brain", "brain-heart",
}


def _contains_term(text, term):
    """不依赖第三方库的大小写不敏感短语匹配。"""
    return term.casefold() in text.casefold()


def local_prefilter_decision(title, abstract):
    """返回本地预筛结论及命中的主题线，供下载脚本记录与测试。"""
    text = " ".join(str(value or "") for value in (title, abstract))
    core_groups = []
    broad_groups = []
    broad_hits = []

    for group_id, group in TOPIC_GROUPS.items():
        broad_terms = LOCAL_PREFILTER_BROAD_TERMS.get(group_id, set())
        terms = group["terms"]
        if any(
            _contains_term(text, term)
            for term in terms
            if term not in broad_terms
        ):
            core_groups.append(group_id)

        matched_broad = [
            term for term in broad_terms if _contains_term(text, term)
        ]
        if matched_broad:
            broad_groups.append(group_id)
            broad_hits.extend(matched_broad)

    context_hits = [
        term for term in LOCAL_PREFILTER_CONTEXT_TERMS
        if _contains_term(text, term)
    ]
    accepted = bool(core_groups) or (bool(broad_groups) and bool(context_hits))
    accepted_groups = list(dict.fromkeys(core_groups + (broad_groups if context_hits else [])))
    return {
        "accepted": accepted,
        "groups": accepted_groups,
        "reason": "core_term" if core_groups else ("broad_term_with_context" if accepted else "no_qualifying_term"),
        "broad_hits": sorted(set(broad_hits)),
        "context_hits": sorted(set(context_hits)),
    }
