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

# Crossref 的 bibliographic 查询不是严格的布尔检索。按主线拆分可避免宽词
# 在同一查询中相互放大，并让每条主线都有稳定的召回入口。
CROSSREF_TRACK_QUERIES = {
    "heart_brain": "heart brain interaction neurovisceral HRV psychological",
    "emi": "ecological momentary assessment intervention just in time adaptive",
    "mental_health": "digital mobile mental health psychological intervention",
}

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

# 高精度心脑轴模式：这些医学/基础研究信号一旦出现，即不作为心理学周报候选。
HEART_BRAIN_EXCLUSION_TERMS = {
    "animal", "mice", "mouse", "rat", "rats", "rodent", "canine", "porcine",
    "cell culture", "in vitro", "anatomical", "anatomy", "histology",
    "cardiac surgery", "postoperative", "post-operative", "catheter", "stent",
    "myocardial infarction", "heart failure", "arrhythmia", "pharmacological",
    "drug administration", "dose response",
}

MENTAL_HEALTH_OUTCOME_TERMS = {
    "mental health", "mental well-being", "mental wellbeing",
    "psychological well-being", "psychological wellbeing", "emotion regulation",
    "depress", "anxiety", "psychiatr", "psychological distress", "stress",
    "suicid", "self-harm", "wellbeing", "well-being",
}

MENTAL_HEALTH_DIGITAL_DELIVERY_TERMS = {
    "digital", "mobile", "smartphone", "app", "web-based", "online", "mhealth",
    "telehealth", "internet-based",
}

MENTAL_HEALTH_INTERVENTION_TERMS = {
    "intervention", "therapy", "treatment", "psychotherap", "trial", "randomized",
    "randomised", "protocol", "programme", "program",
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


def _has_any_whole_phrase(text, terms):
    """用于排除词，避免 ``rat`` 误匹配 ``heart rate`` 之类的子串。"""
    normalized = str(text or "").casefold()
    for term in terms:
        phrase = re.escape(term.casefold()).replace(r"\ ", r"\s+")
        if re.search(rf"(?<!\w){phrase}(?!\w)", normalized):
            return True
    return False


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
            if _has_any_whole_phrase(text, HEART_BRAIN_EXCLUSION_TERMS):
                continue
            # 高精度模式下，直接心脑术语也必须具备心理/行为语境；不能仅因
            # 心血管或神经生理术语而放行。
            if not _has_any(text, HEART_BRAIN_PSYCHOLOGICAL_CONTEXT_TERMS):
                continue
            accepted_groups.append(group["label"])
            reasons.append("heart_brain_psych_context")
            continue
        if group_id == "mental_health":
            has_outcome = _has_any(text, MENTAL_HEALTH_OUTCOME_TERMS)
            has_delivery = _has_any(text, MENTAL_HEALTH_DIGITAL_DELIVERY_TERMS)
            has_intervention = _has_any(text, MENTAL_HEALTH_INTERVENTION_TERMS)
            # 心理健康/情绪问题必须是研究对象，且至少同时出现数字递送方式或
            # 干预/治疗/试验/方案信号；一般正念或泛幸福感研究不再自动放行。
            if not has_outcome or not (has_delivery or has_intervention):
                continue
            accepted_groups.append(group["label"])
            reasons.append("mental_health_high_precision")
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
