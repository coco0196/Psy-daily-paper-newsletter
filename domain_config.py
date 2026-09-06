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
            "acceptance and commitment therapy", "mindfulness-based intervention",
            "mindfulness intervention", "mind-body intervention", "meditation intervention",
            "relaxation intervention", "breathing intervention", "biofeedback",
            "heart rate variability biofeedback", "hrv biofeedback",
            "somatic intervention", "body-oriented psychotherapy",
            "micro-intervention", "microintervention",
        ],
    },
}

# Crossref 的 bibliographic 查询不是严格的布尔检索。按主线拆分可避免宽词
# 在同一查询中相互放大，并让每条主线都有稳定的召回入口。
CROSSREF_TRACK_QUERIES = {
    "heart_brain": (
        "heart brain interaction coupling neurovisceral autonomic vagal HRV psychological neuroscience",
        "EEG ECG heart rate variability psychophysiology emotion cognition stress intervention",
    ),
    "emi": (
        "ecological momentary assessment experience sampling intervention just in time adaptive physiological wearable",
        "digital phenotyping passive sensing intensive longitudinal mental health psychology",
    ),
    "mental_health": (
        "mental health emotion regulation stress anxiety psychological intervention psychotherapy",
        "mind body mindfulness meditation breathing relaxation biofeedback somatic body oriented",
    ),
}

# EEG 与 ECG 同步测量是心脑耦合的重要证据，但任一信号单独出现都不足以
# 说明论文属于心脑轴。检索与本地筛选均要求两类信号同时出现，且带有心理学
# 语境，避免把一般神经电生理或心电临床监测纳入。
EEG_TERMS = {
    "eeg", "electroencephalography", "electroencephalogram",
}
ECG_TERMS = {
    "ecg", "electrocardiography", "electrocardiogram",
}
EEG_ECG_PUBMED_QUERY = (
    '(("electroencephalography"[Title/Abstract] OR '
    '"electroencephalogram"[Title/Abstract] OR EEG[Title/Abstract]) '
    'AND ("electrocardiography"[Title/Abstract] OR '
    '"electrocardiogram"[Title/Abstract] OR ECG[Title/Abstract]) '
    'AND (psychological[Title/Abstract] OR mental[Title/Abstract] OR '
    'emotion[Title/Abstract] OR stress[Title/Abstract] OR cognitive[Title/Abstract] '
    'OR behavior[Title/Abstract] OR behaviour[Title/Abstract] OR '
    'intervention[Title/Abstract]))'
)

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
    "neuroscience", "neuroscientific", "neural", "brain", "eeg",
}

# 这些信号几乎总是基础/医学研究而非本项目所需的心理学或神经科学语境。
# 疾病名称本身不再一刀切排除：若其确实研究心理行为或身心干预，交由
# DeepSeek 根据摘要作最终判断。
HEART_BRAIN_EXCLUSION_TERMS = {
    "animal", "mice", "mouse", "rat", "rats", "rodent", "canine", "porcine",
    "cell culture", "in vitro", "anatomical", "anatomy", "histology",
    "cardiac surgery", "postoperative", "post-operative", "catheter", "stent",
    "drug administration", "dose response",
}

MENTAL_HEALTH_OUTCOME_TERMS = {
    "mental health", "mental well-being", "mental wellbeing",
    "psychological well-being", "psychological wellbeing", "emotion regulation",
    "depress", "anxiety", "psychiatr", "psychological distress", "stress",
    "suicid", "self-harm", "wellbeing", "well-being", "mood", "affect",
    "emotion", "loneliness", "quality of life", "coping", "self-efficacy",
    "health behavior", "health behaviour", "behavior change", "behaviour change",
    "self-regulation", "sleep", "insomnia", "pain", "medication adherence",
    "treatment adherence", "heart rate variability", "hrv", "heart rate",
    "psychophysiological", "psychophysiology",
}

MENTAL_HEALTH_DIGITAL_DELIVERY_TERMS = {
    "digital", "mobile", "smartphone", "smartphone app", "mobile app", "app-based",
    "web-based", "online", "mhealth", "telehealth", "internet-based",
}

MENTAL_HEALTH_INTERVENTION_TERMS = {
    "intervention", "therapy", "treatment", "psychotherap", "trial", "randomized",
    "randomised", "protocol", "programme", "program", "self-guided", "self-help",
    "micro-intervention", "microintervention", "biofeedback", "hrv biofeedback",
    "mind-body intervention", "mindfulness-based", "mindfulness intervention",
    "meditation intervention", "relaxation intervention", "breathing intervention",
    "somatic intervention", "body-oriented psychotherapy",
}

# PubMed 是严格布尔检索。第三主线使用“核心心理/行为主题 AND 一般干预”
# 作为宽召回入口；高特异身心干预另设入口。协议、trial、programme 等泛词
# 不单独用于检索，避免把大量一般医学研究引入候选池。
MENTAL_HEALTH_RETRIEVAL_OUTCOME_TERMS = (
    "mental health", "emotion regulation", "psychological distress", "stress",
    "anxiety", "depression", "mood", "affect", "well-being",
)
MENTAL_HEALTH_RETRIEVAL_INTERVENTION_TERMS = (
    "intervention", "therapy", "treatment", "psychotherapy", "randomized",
    "randomised", "psychological intervention", "self-guided intervention",
    "self-help intervention", "digital intervention", "mobile intervention",
)
MENTAL_HEALTH_HIGH_SPECIFIC_INTERVENTION_TERMS = (
    "mind-body intervention",
    "mindfulness-based intervention", "mindfulness intervention",
    "meditation intervention", "relaxation intervention", "breathing intervention",
    "biofeedback", "heart rate variability biofeedback", "hrv biofeedback",
    "somatic intervention", "body-oriented psychotherapy", "micro-intervention",
    "behavioral activation",
)


def _pubmed_title_abstract_any(terms):
    return " OR ".join(f'"{term}"[Title/Abstract]' for term in terms)


PUBMED_MENTAL_HEALTH_QUERY = (
    f"(({_pubmed_title_abstract_any(MENTAL_HEALTH_RETRIEVAL_OUTCOME_TERMS)}) "
    f"AND ({_pubmed_title_abstract_any(MENTAL_HEALTH_RETRIEVAL_INTERVENTION_TERMS)})) "
    f"OR ({_pubmed_title_abstract_any(MENTAL_HEALTH_HIGH_SPECIFIC_INTERVENTION_TERMS)}))"
)

# EMA/ESM 的一般自评问卷研究数量很大，且未必符合本项目的重点。EMA/EMI
# 主线要求明确的瞬时/密集纵向方法，并进一步要求：要么是主动干预，要么结合
# 客观生理数据（含心血管与可穿戴感测）。数字表型和被动感测被视为传感路径，
# 但仍需明确属于 EMA/ESM 或密集纵向设计。
EMA_EMI_CORE_METHOD_TERMS = {
    "ecological momentary assessment", "experience sampling",
    "experience sampling method", "ambulatory assessment", "intensive longitudinal",
    "intensive longitudinal data", "daily diary", "ecological momentary intervention",
    "just-in-time adaptive intervention", "just-in-time intervention",
    "micro-randomized trial", "micro-randomized trials", "digital phenotyping",
    "passive sensing", "mobile sensing",
}
EMA_EMI_INTERVENTION_TERMS = {
    "ecological momentary intervention", "just-in-time adaptive intervention",
    "just-in-time intervention", "micro-randomized trial", "micro-randomized trials",
    "digital micro-intervention", "digital micro-interventions", "microintervention",
    "microinterventions", "context-aware intervention", "adaptive intervention",
    "adaptive treatment", "personalized intervention", "personalised intervention",
}
EMA_EMI_PHYSIOLOGICAL_TERMS = {
    "ecg", "electrocardiography", "electrocardiogram", "ppg", "photoplethysmography",
    "heart rate", "heart rate variability", "hrv", "electrodermal activity",
    "skin conductance", "galvanic skin response", "physiological", "physiologic",
    "biosensor", "biosensors", "wearable", "wearables", "actigraphy",
    "respiration", "respiratory", "accelerometry", "digital phenotyping",
    "passive sensing", "mobile sensing",
}

REVIEW_TERMS = {
    "systematic review", "scoping review", "narrative review", "literature review",
    "meta-analysis", "meta analysis", "umbrella review", "review article",
}

# 除直接的心脑术语外，三条主线都应落在心理学、精神健康、行为科学、
# 心理生理或神经科学的语境中。该集合用于本地阶段拦截泛临床/工程噪声；
# 不是最终的学术相关性判断。
PSYCHOLOGY_NEUROSCIENCE_CONTEXT_TERMS = {
    "mental", "psycholog", "psychiatr", "depress", "anxiety", "stress",
    "emotion", "affect", "mood", "cognitive", "behavior", "behaviour",
    "wellbeing", "well-being", "quality of life", "subjective", "experience",
    "neuroscience", "neural", "brain", "eeg", "psychophysiolog", "hrv",
    "mindfulness", "meditation", "relaxation", "breathing", "biofeedback",
    "sleep", "insomnia", "pain", "adherence",
}

# 第三主线允许睡眠、疼痛、身体活动或依从性作为身心干预结局，但这些健康词
# 本身不能把一般临床试验带入周报；还须有心理/行为、心理生理或身心方法语境。
MENTAL_HEALTH_CONTEXT_TERMS = {
    "mental", "psycholog", "psychiatr", "depress", "anxiety", "stress",
    "emotion", "affect", "mood", "cognitive", "behavior", "behaviour",
    "wellbeing", "well-being", "quality of life", "subjective", "experience",
    "psychophysiolog", "heart rate variability", "hrv", "biofeedback",
    "mindfulness", "meditation", "relaxation", "breathing", "mind-body",
    "somatic", "body-oriented",
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
    """返回心脑轴与 EMA/EMI 的 PubMed 标题/摘要检索词。

    第三主线使用 PUBMED_MENTAL_HEALTH_QUERY 的结局—干预组合，而不是把其
    局部词逐个放入同一 OR 查询。
    """
    seen = set()
    for group_id, group in TOPIC_GROUPS.items():
        if group_id == "mental_health":
            continue
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
    """在 API 调用前执行“宽召回、可解释”的候选预筛。

    本层只移除明显不属于心理学/神经科学三条主线的记录；最终的直接相关性
    由 DeepSeek 判定。因此它不把“不是重点推荐”误当作“不能收录”。
    """
    text = " ".join(str(value or "") for value in (title, abstract))
    has_psych_neuro_context = _has_any(text, PSYCHOLOGY_NEUROSCIENCE_CONTEXT_TERMS)
    is_review = _has_any(text, REVIEW_TERMS)
    accepted_groups = []
    reasons = []
    for group_id, group in TOPIC_GROUPS.items():
        hits = [term for term in group["terms"] if _contains_term(text, term)]
        has_eeg_ecg_pair = (
            _has_any_whole_phrase(text, EEG_TERMS)
            and _has_any_whole_phrase(text, ECG_TERMS)
        )
        if (
            group_id != "mental_health"
            and not hits
            and not (group_id == "heart_brain" and has_eeg_ecg_pair)
        ):
            continue
        if group_id == "heart_brain":
            if _has_any_whole_phrase(text, HEART_BRAIN_EXCLUSION_TERMS):
                continue
            # HRV/迷走/自主神经等词非常宽泛，仍需心理或神经科学语境；直接
            # 心脑研究和综述同样须落在这一语境，而不是纯心血管生理。
            if not (
                _has_any(text, HEART_BRAIN_PSYCHOLOGICAL_CONTEXT_TERMS)
                or (is_review and has_psych_neuro_context)
            ):
                continue
            accepted_groups.append(group["label"])
            reasons.append(
                "eeg_ecg_psych_context" if has_eeg_ecg_pair else "heart_brain_psych_context"
            )
            continue
        if group_id == "mental_health":
            has_outcome = _has_any(text, MENTAL_HEALTH_OUTCOME_TERMS)
            has_intervention = _has_any(text, MENTAL_HEALTH_INTERVENTION_TERMS)
            has_delivery = _has_any(text, MENTAL_HEALTH_DIGITAL_DELIVERY_TERMS)
            # 第三主线要求心理、行为、主观体验或心理生理指标等研究结局，且
            # 必须实际评估干预、治疗、试验或方案。数字/移动递送仅作为相关性
            # 增强信号，不再误排除非数字的心理与身心干预。
            if not (
                has_outcome
                and has_intervention
                and _has_any(text, MENTAL_HEALTH_CONTEXT_TERMS)
            ):
                continue
            accepted_groups.append(group["label"])
            reasons.append(
                "mental_health_intervention_with_digital_delivery"
                if has_delivery
                else "mental_health_intervention"
            )
            continue
        if group_id == "emi":
            has_core_method = _has_any(text, EMA_EMI_CORE_METHOD_TERMS)
            has_intervention = _has_any(text, EMA_EMI_INTERVENTION_TERMS)
            has_physiology = _has_any_whole_phrase(text, EMA_EMI_PHYSIOLOGICAL_TERMS)
            # 排除只做自评问卷的 EMA/ESM；需为直接干预，或结合客观生理/传感
            # 指标。两者兼具的论文会在 DeepSeek 阶段获得重点推荐资格。
            # EMA/ESM 的方法学门槛保持不变；但直接讨论该方法学的综述也有
            # 长期追踪价值，不按“简单问卷研究”处理。
            if not (
                has_core_method
                and (has_intervention or has_physiology or is_review)
                and has_psych_neuro_context
            ):
                continue
            accepted_groups.append(group["label"])
            reasons.append(
                "emi_with_intervention_and_physiology"
                "ema_emi_review"
                if is_review and not (has_intervention or has_physiology)
                else "emi_with_intervention_and_physiology"
                if has_intervention and has_physiology
                else "emi_with_intervention"
                if has_intervention
                else "ema_with_physiology"
            )
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


def topic_label_eligibility(title, abstract):
    """返回可由本地可解释规则支持的主题标签。

    DeepSeek 负责语义判断，程序只用此函数阻止明显不成立的标签。例如，单纯
    EEG/HRV/EDA 实验不会因含生理指标而获得“生态瞬时干预”标签。
    """
    return local_prefilter_decision(title, abstract)["groups"]
