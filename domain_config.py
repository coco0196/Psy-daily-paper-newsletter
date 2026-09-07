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
            "central autonomic network", "cardiac interoception", "interoception",
            "cardiac-brain synchrony", "heart-brain synchrony",
            "brain-heart coherence", "cardiac-neural coupling",
            "interoceptive inference", "neurocardiac", "baroreceptor",
            "heart rate variability",
            "vagally mediated heart rate variability",
            "respiratory heart rate variability", "respiratory sinus arrhythmia",
            "heartbeat evoked potential", "heartbeat evoked potentials",
            "vagus nerve", "vagal tone", "cardiac vagal control",
            "parasympathetic nervous system", "autonomic nervous system",
            "autonomic regulation", "autonomic function",
            "hrv", "vmhrv", "rsa",
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
            "ema", "esm", "emi", "jitai", "mrt", "mhealth",
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
            "digital mental health", "dmh", "dmhi", "ehealth", "icbt",
            "digital therapeutics", "ai-assisted intervention",
            "virtual reality intervention", "wearable intervention",
            "brief intervention", "single-session intervention",
        ],
    },
}

# Crossref 的 bibliographic 查询不是严格的布尔检索。按主线拆分可避免宽词
# 在同一查询中相互放大，并让每条主线都有稳定的召回入口。
CROSSREF_TRACK_QUERIES = {
    "heart_brain": (
        "heart brain interaction coupling synchrony coherence neurovisceral autonomic vagal cardiac neural coupling interoception",
        "heart rate variability HRV respiratory sinus arrhythmia baroreflex vagal tone cardiac autonomic regulation allostatic load",
        "EEG ECG electroencephalography electrocardiography heart rate variability HRV respiratory sinus arrhythmia emotion stress cognition intervention",
    ),
    "emi": (
        "ecological momentary assessment EMA experience sampling ambulatory assessment daily diary intensive longitudinal mobile sensing passive sensing",
        "ecological momentary intervention EMI just-in-time adaptive intervention JITAI micro-randomized trial MRT context-aware intervention adaptive intervention",
        "digital phenotyping passive sensing mobile sensing digital biomarkers intensive longitudinal mental health psychology",
    ),
    "mental_health": (
        "digital intervention mobile intervention smartphone intervention app-based intervention internet-based intervention digital therapeutics eHealth iCBT virtual reality intervention wearable intervention",
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
    "hrv", "heart rate variability", "hr", "heart rate", "rsa",
    "respiratory sinus arrhythmia", "heartbeat-evoked response",
}
EEG_ECG_PUBMED_QUERY = (
    '(("electroencephalography"[Title/Abstract] OR '
    '"electroencephalogram"[Title/Abstract] OR "EEG"[Title/Abstract]) '
    'AND ("electrocardiography"[Title/Abstract] OR '
    '"electrocardiogram"[Title/Abstract] OR "ECG"[Title/Abstract] OR '
    '"heart rate variability"[Title/Abstract] OR "HRV"[Title/Abstract] OR '
    '"heart rate"[Title/Abstract] OR "HR"[Title/Abstract] OR '
    '"respiratory sinus arrhythmia"[Title/Abstract] OR "RSA"[Title/Abstract] OR '
    '"heartbeat-evoked response"[Title/Abstract]))'
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
    "daily monitoring", "dynamic measurement", "dynamic monitoring",
    "neuroscience", "neuroscientific", "neuroimaging", "neural", "brain", "eeg",
    "erp", "hep", "psychophysiolog", "interoception",
}

# 这些信号几乎总是基础/医学研究而非本项目所需的心理学或神经科学语境。
# 疾病名称本身不再一刀切排除：若其确实研究心理行为或身心干预，交由
# DeepSeek 根据摘要作最终判断。
NONHUMAN_OR_CELL_TERMS = {
    "animal", "animal model", "mice", "mouse", "murine", "rat", "rats", "rodent",
    "canine", "porcine", "zebrafish", "cell culture", "cell line", "in vitro",
    "ex vivo", "histology", "immunofluorescence", "western blot",
}
HUMAN_STUDY_TERMS = {
    "human", "humans", "participant", "participants", "patient", "patients",
    "adult", "adults", "adolescent", "adolescents", "child", "children",
    "healthy volunteer", "healthy volunteers", "people", "individuals", "cohort",
}
PURE_MECHANISTIC_TERMS = {
    "cellular mechanism", "molecular mechanism", "biological mechanism",
    "physiological mechanism", "neural mechanism", "receptor expression",
    "protein expression", "gene expression", "histology", "immunofluorescence",
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
    "flourishing", "resilience", "emotion experience", "subjective experience",
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
    "mindfulness-based intervention", "mindfulness intervention", "mindfulness practice",
    "meditation training", "meditation program", "loving-kindness meditation",
    "compassion meditation", "body scan", "mindful movement",
    "relaxation therapy", "relaxation training", "relaxation technique",
    "progressive muscle relaxation", "autogenic training", "guided imagery",
    "breathing exercise", "paced breathing", "slow breathing", "slow-paced breathing",
    "mindful breathing", "diaphragmatic breathing", "deep breathing", "breathwork",
    "somatic therapy", "somatic experiencing", "body psychotherapy",
    "dance movement therapy", "mind-body exercise", "mind-body therapy",
    "behavioral activation", "behavioural activation", "brief intervention",
    "single-session intervention",
}

# PubMed 是严格布尔检索。第三主线使用“核心心理/行为主题 AND 一般干预”
# 作为宽召回入口；高特异身心干预另设入口。协议、trial、programme 等泛词
# 不单独用于检索，避免把大量一般医学研究引入候选池。
MENTAL_HEALTH_RETRIEVAL_OUTCOME_TERMS = (
    "mental health", "emotion regulation", "psychological distress", "stress",
    "anxiety", "depression", "mood", "affect", "well-being",
    "mental wellbeing", "psychological well-being", "flourishing", "resilience",
    "loneliness", "coping", "self-efficacy", "quality of life",
    "health behavior", "health behaviour", "self-regulation",
    "sleep", "insomnia", "pain",
)
MENTAL_HEALTH_RETRIEVAL_INTERVENTION_TERMS = (
    "intervention", "therapy", "treatment", "psychotherapy", "randomized",
    "randomised", "psychological intervention", "self-guided intervention",
    "self-help intervention", "digital intervention", "mobile intervention",
)
MENTAL_HEALTH_HIGH_SPECIFIC_INTERVENTION_TERMS = (
    "mind-body intervention",
    "mindfulness-based intervention", "mindfulness intervention",
    "mindfulness practice", "meditation intervention", "meditation training",
    "meditation program", "loving-kindness meditation", "compassion meditation",
    "body scan", "mindful movement", "relaxation intervention", "relaxation therapy",
    "relaxation training", "relaxation technique", "progressive muscle relaxation",
    "autogenic training", "guided imagery", "breathing intervention", "breathing exercise",
    "paced breathing", "slow breathing", "slow-paced breathing", "mindful breathing",
    "diaphragmatic breathing", "deep breathing", "breathwork",
    "biofeedback", "heart rate variability biofeedback", "hrv biofeedback",
    "somatic intervention", "somatic therapy", "somatic experiencing",
    "body-oriented psychotherapy", "body psychotherapy", "dance movement therapy",
    "mind-body exercise", "mind-body therapy", "micro-intervention", "microintervention",
    "brief intervention", "single-session intervention", "behavioral activation",
    "behavioural activation",
)
MENTAL_HEALTH_DIGITAL_RETRIEVAL_TERMS = (
    "digital mental health", "digital psychological intervention", "digital intervention",
    "mobile intervention", "smartphone intervention", "app-based intervention",
    "web-based intervention", "internet-based intervention", "mhealth intervention",
    "digital therapeutics", "dmhi", "ehealth", "icbt", "ai-assisted intervention",
    "virtual reality intervention", "wearable intervention", "brief intervention",
    "single-session intervention",
)


def _pubmed_title_abstract_any(terms):
    return " OR ".join(f'"{term}"[Title/Abstract]' for term in terms)


PUBMED_MENTAL_HEALTH_QUERY = (
    f"(({_pubmed_title_abstract_any(MENTAL_HEALTH_RETRIEVAL_OUTCOME_TERMS)}) "
    f"AND ({_pubmed_title_abstract_any(MENTAL_HEALTH_RETRIEVAL_INTERVENTION_TERMS)})) "
    f"OR ({_pubmed_title_abstract_any(MENTAL_HEALTH_HIGH_SPECIFIC_INTERVENTION_TERMS)}) "
    f"OR ({_pubmed_title_abstract_any(MENTAL_HEALTH_DIGITAL_RETRIEVAL_TERMS)}))"
)

# PubMed 检索按三条主线分为三个 tiab 模块。语境限制放在本地预筛和
# DeepSeek 阶段，以首先建立宽而结构化的候选池。
PUBMED_HEART_BRAIN_QUERY = (
    f"(({_pubmed_title_abstract_any(TOPIC_GROUPS['heart_brain']['terms'])}) "
    f"OR ({EEG_ECG_PUBMED_QUERY}))"
)
PUBMED_EMA_EMI_QUERY = (
    f"({_pubmed_title_abstract_any(TOPIC_GROUPS['emi']['terms'])})"
)
PUBMED_QUERY_MODULES = {
    "heart_brain": PUBMED_HEART_BRAIN_QUERY,
    "emi": PUBMED_EMA_EMI_QUERY,
    "mental_health": PUBMED_MENTAL_HEALTH_QUERY,
}

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
    "ema", "esm", "emi", "jitai", "mrt", "mobile health", "mhealth",
}
EMA_EMI_INTERVENTION_TERMS = {
    "ecological momentary intervention", "just-in-time adaptive intervention",
    "just-in-time intervention", "micro-randomized trial", "micro-randomized trials",
    "digital micro-intervention", "digital micro-interventions", "microintervention",
    "microinterventions", "context-aware intervention", "adaptive intervention",
    "adaptive treatment", "personalized intervention", "personalised intervention",
    "emi", "jitai", "mrt",
}
EMA_EMI_PHYSIOLOGICAL_TERMS = {
    "ecg", "electrocardiography", "electrocardiogram", "ppg", "photoplethysmography",
    "heart rate", "heart rate variability", "hrv", "electrodermal activity",
    "skin conductance", "galvanic skin response", "physiological", "physiologic",
    "biosensor", "biosensors", "wearable", "wearables", "actigraphy",
    "respiration", "respiratory", "accelerometry", "digital phenotyping",
    "passive sensing", "mobile sensing",
    "hr", "hrv", "eeg", "ecg",
}
DIGITAL_PHENOTYPING_HUMAN_HEALTH_TERMS = {
    "digital phenotyping", "passive sensing", "mobile sensing", "wearable",
    "wearables", "health", "healthcare", "public health", "patient", "patients",
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
    "sleep", "insomnia", "pain", "adherence", "coping", "self-efficacy",
    "loneliness", "flourishing", "health behavior", "health behaviour",
    "self-regulation", "motivation", "attention", "executive", "decision",
    "social cognition", "daily monitoring", "dynamic measurement", "dynamic monitoring",
    "ambulatory monitoring", "ecological", "experience sampling", "ema", "esm",
    "neuroimaging", "fmri", "erp", "hep", "interoception", "hrv", "heart rate",
}

# 第三主线允许睡眠、疼痛、身体活动或依从性作为身心干预结局，但这些健康词
# 本身不能把一般临床试验带入周报；还须有心理/行为、心理生理或身心方法语境。
MENTAL_HEALTH_CONTEXT_TERMS = {
    "mental", "psycholog", "psychiatr", "depress", "anxiety", "stress",
    "emotion", "affect", "mood", "cognitive", "behavior", "behaviour",
    "wellbeing", "well-being", "quality of life", "subjective", "experience",
    "psychophysiolog", "heart rate variability", "hrv", "biofeedback",
    "mindfulness", "meditation", "relaxation", "breathing", "mind-body",
    "somatic", "body-oriented", "coping", "self-efficacy", "loneliness",
    "flourishing", "health behavior", "health behaviour", "self-regulation",
    "daily monitoring", "dynamic measurement", "dynamic monitoring", "hrv", "heart rate",
}
MENTAL_HEALTH_SUPPORTING_OUTCOME_TERMS = {
    "sleep", "insomnia", "pain", "physical activity", "adherence",
    "medication adherence", "treatment adherence",
}
MENTAL_HEALTH_MINDBODY_INTERVENTION_TERMS = {
    "mindfulness", "meditation", "relaxation", "breathing", "mind-body",
    "biofeedback", "hrv biofeedback", "somatic", "body-oriented",
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
    has_human_signal = _has_any_whole_phrase(text, HUMAN_STUDY_TERMS)
    has_nonhuman_or_cell_signal = _has_any_whole_phrase(text, NONHUMAN_OR_CELL_TERMS)
    # 动物、细胞与体外研究是全局排除项。人类研究或人类综述偶尔会提及
    # 动物证据，故有明确人类信号时不在本地阶段误删，交由 DeepSeek 终审。
    if has_nonhuman_or_cell_signal and not has_human_signal:
        return {
            "accepted": False,
            "groups": [],
            "reason": "nonhuman_or_cell_study",
        }
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
            has_intervention = _has_any(text, MENTAL_HEALTH_INTERVENTION_TERMS)
            has_delivery = _has_any(text, MENTAL_HEALTH_DIGITAL_DELIVERY_TERMS)
            has_context = _has_any(text, MENTAL_HEALTH_CONTEXT_TERMS)
            has_supporting_outcome = _has_any(text, MENTAL_HEALTH_SUPPORTING_OUTCOME_TERMS)
            has_mindbody_intervention = _has_any(
                text, MENTAL_HEALTH_MINDBODY_INTERVENTION_TERMS
            )
            has_eligible_context = has_context or (
                has_supporting_outcome and has_mindbody_intervention
            )
            # 第三主线只排除明显无关的记录：不再强制要求命中特定结局词。只要
            # 具备心理/身心/心理生理语境和干预信号即可送入 DeepSeek；直接相关
            # 综述也保留，由模型判断是否足够直接。
            if not (
                (has_eligible_context and has_intervention)
                or (is_review and has_eligible_context)
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
            is_human_health_digital_phenotyping_review = (
                is_review
                and _has_any(text, {"digital phenotyping", "passive sensing", "mobile sensing"})
                and _has_any(text, DIGITAL_PHENOTYPING_HUMAN_HEALTH_TERMS)
            )
            # 排除只做自评问卷的 EMA/ESM；需为直接干预，或结合客观生理/传感
            # 指标。两者兼具的论文会在 DeepSeek 阶段获得重点推荐资格。
            # EMA/ESM 的方法学门槛保持不变；但直接讨论该方法学的综述也有
            # 长期追踪价值，不按“简单问卷研究”处理。
            if not (
                has_core_method
                and (has_intervention or has_physiology or is_review)
                and (has_psych_neuro_context or is_human_health_digital_phenotyping_review)
            ):
                continue
            accepted_groups.append(group["label"])
            if is_review and not (has_intervention or has_physiology):
                reasons.append("ema_emi_review")
            elif has_intervention and has_physiology:
                reasons.append("emi_with_intervention_and_physiology")
            elif has_intervention:
                reasons.append("emi_with_intervention")
            else:
                reasons.append("ema_with_physiology")
            continue
        broad_terms = LOCAL_PREFILTER_BROAD_TERMS.get(group_id, set())
        only_broad = all(term in broad_terms for term in hits)
        if only_broad and not _has_any(text, LOCAL_PREFILTER_CONTEXT_TERMS):
            continue
        accepted_groups.append(group["label"])
        reasons.append("broad_term_with_context" if only_broad else "specific_term")
    if not accepted_groups and _has_any_whole_phrase(text, PURE_MECHANISTIC_TERMS):
        return {
            "accepted": False,
            "groups": [],
            "reason": "pure_mechanistic_without_target_context",
        }
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
