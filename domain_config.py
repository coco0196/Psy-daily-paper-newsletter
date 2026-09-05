"""心脑、生态瞬时干预与数字心理健康文献追踪配置。"""

import re

REPORT_TITLE = "心脑、生态瞬时干预与数字心理健康文献周报"

# 这三个值既是 DeepSeek 的唯一允许输出，也是 Newsletter 的固定分栏顺序。
CANONICAL_TOPIC_LABELS = (
    "心脑轴",
    "生态瞬时干预",
    "心理健康与数字心理干预",
)

TOPIC_GROUPS = {
    "heart_brain": {
        "label": "心脑轴",
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
            "vagus nerve", "vagal tone", "cardiac vagal control",
            "parasympathetic nervous system", "autonomic nervous system",
            "autonomic regulation", "autonomic function",
        ],
    },
    "emi": {
        "label": "生态瞬时干预",
        "terms": [
            "ecological momentary assessment", "experience sampling",
            "experience sampling method", "ambulatory assessment",
            "intensive longitudinal", "intensive longitudinal data", "daily diary",
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

CROSSREF_QUERY_TERMS = [
    "heart-brain interaction", "vagus nerve mental health",
    "heart rate variability psychological", "ecological momentary assessment",
    "just-in-time adaptive intervention", "ecological momentary intervention",
    "micro-randomized trial", "digital phenotyping mental health",
    "digital mental health",
]

# 以下心脑术语在纯心血管/解剖/生理文献中也常见，必须带心理学语境才放行。
HEART_BRAIN_CONTEXT_REQUIRED_TERMS = {
    "heart rate variability", "vagally mediated heart rate variability",
    "respiratory heart rate variability", "respiratory sinus arrhythmia",
    "vagus nerve", "vagal tone", "cardiac vagal control",
    "parasympathetic nervous system", "autonomic nervous system",
    "autonomic regulation", "autonomic function",
}

HEART_BRAIN_PSYCHOLOGICAL_CONTEXT_TERMS = {
    "mental", "psycholog", "psychiatr", "depress", "anxiety", "stress",
    "emotion", "affect", "cognitive", "behavior", "behaviour", "wellbeing",
    "well-being", "resilience", "mindfulness", "intervention", "therapy",
    "treatment", "ecological", "experience sampling", "ambulatory", "daily diary",
}

LOCAL_PREFILTER_BROAD_TERMS = {
    "emi": {
        "adaptive intervention", "adaptive treatment", "personalized intervention",
        "personalised intervention", "digital phenotyping", "passive sensing",
        "mobile sensing", "mobile health",
    },
    "mental_health": {
        "mental health", "mental well-being", "mental wellbeing",
        "psychological well-being", "psychological wellbeing", "flourishing",
        "resilience", "emotion regulation", "mindfulness", "digital intervention",
        "digital interventions", "mobile intervention", "mobile interventions",
    },
}

LOCAL_PREFILTER_CONTEXT_TERMS = {
    "mental", "psycholog", "psychiatr", "depress", "anxiety", "stress",
    "emotion", "affect", "behavior", "behaviour", "cognitive", "intervention",
    "treatment", "therap", "mindfulness", "ecological", "experience sampling",
    "ambulatory", "daily diary", "digital", "mobile", "smartphone", "wearable",
}

_TOPIC_ALIASES = {
    "心脑轴": ("心脑轴", "心脑耦合", "心脑轴/心脑耦合", "heart-brain"),
    "生态瞬时干预": (
        "生态瞬时干预", "ema/esm", "密集纵向", "emi/jitai", "即时自适应",
        "生态瞬时评估", "经验取样", "数字表型",
    ),
    "心理健康与数字心理干预": (
        "心理健康与数字心理干预", "心理健康", "数字心理干预", "数字/移动心理干预",
    ),
}


def iter_topic_terms():
    """按主线返回不重复的 PubMed 标题/摘要检索词。"""
    seen = set()
    for group in TOPIC_GROUPS.values():
        for term in group["terms"]:
            key = term.casefold()
            if key not in seen:
                seen.add(key)
                yield term


def _contains_term(text, term):
    return term.casefold() in text.casefold()


def _has_any(text, terms):
    return any(_contains_term(text, term) for term in terms)


def local_prefilter_decision(title, abstract):
    """在 API 调用前执行可解释的本地候选预筛。"""
    text = " ".join(str(value or "") for value in (title, abstract))
    accepted_groups = []
    reasons = []
    for group_id, group in TOPIC_GROUPS.items():
        hits = [term for term in group["terms"] if _contains_term(text, term)]
        if not hits:
            continue
        if group_id == "heart_brain":
            only_context_required = all(term in HEART_BRAIN_CONTEXT_REQUIRED_TERMS for term in hits)
            if only_context_required and not _has_any(text, HEART_BRAIN_PSYCHOLOGICAL_CONTEXT_TERMS):
                continue
            accepted_groups.append(group["label"])
            reasons.append("heart_brain_psych_context" if only_context_required else "heart_brain_specific")
            continue
        broad_terms = LOCAL_PREFILTER_BROAD_TERMS.get(group_id, set())
        only_broad = all(term in broad_terms for term in hits)
        if only_broad and not _has_any(text, LOCAL_PREFILTER_CONTEXT_TERMS):
            continue
        accepted_groups.append(group["label"])
        reasons.append("broad_term_with_context" if only_broad else "specific_term")
    return {
        "accepted": bool(accepted_groups),
        "groups": accepted_groups,
        "reason": "；".join(reasons) if reasons else "no_qualifying_term",
    }


def normalize_topic_labels(raw_labels):
    """将 DeepSeek 的新旧标签、JSON 样式与引号统一为三个标准标签。"""
    if isinstance(raw_labels, (list, tuple, set)):
        text = "；".join(str(item) for item in raw_labels)
    else:
        text = str(raw_labels or "")
    text = text.casefold()
    text = re.sub(r"[\[\]\[\]\(\)（）{}\"'`]+", " ", text)
    labels = []
    for canonical in CANONICAL_TOPIC_LABELS:
        if any(alias.casefold() in text for alias in _TOPIC_ALIASES[canonical]):
            labels.append(canonical)
    return labels
