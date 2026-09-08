"""心脑、生态瞬时干预与心理微干预文献追踪配置。"""

import re

REPORT_TITLE = "心脑、生态瞬时干预与心理微干预文献周报"

# 这三个值既是 DeepSeek 的唯一允许输出，也是 Newsletter 的固定分栏顺序。
CANONICAL_TOPIC_LABELS = (
    "心脑轴",
    "生态瞬时干预",
    "心理微干预",
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
        "label": "心理微干预",
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
        "heart brain axis heart brain interaction heart brain coupling cardiac brain synchrony heart brain synchrony brain heart coherence cardiac neural coupling neurocardiac interoception",
        "neurovisceral integration heart rate variability HRV vagal tone cardiac vagal control respiratory sinus arrhythmia psychophysiology emotion stress",
        "EEG ECG electroencephalography electrocardiography heart brain coupling cardiac neural coupling heartbeat evoked potential heart rate variability HRV",
    ),
    "emi": (
        "ecological momentary assessment EMA experience sampling ambulatory assessment intensive longitudinal",
        "ecological momentary intervention EMI just-in-time adaptive intervention JITAI just-in-time intervention micro-randomized trial MRT digital micro-intervention",
        "digital phenotyping passive sensing mobile sensing wearable sensing digital biomarkers",
    ),
    "mental_health": (
        "digital mental health digital psychological intervention smartphone intervention mobile intervention app-based intervention mHealth intervention iCBT",
        "digital therapeutics DMHI AI-assisted intervention wearable intervention mental health",
        "micro-intervention microintervention brief intervention single-session intervention mindfulness meditation breathing relaxation biofeedback somatic intervention stress emotion",
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
    "well-being", "resilience", "feeling", "mindfulness", "intervention",
    "daily monitoring", "dynamic measurement", "dynamic monitoring",
    "neuroscience", "neuroimaging", "hrv", "hep", "psychophysiolog",
    "interoception",
}

# 这些信号几乎总是基础/医学研究而非本项目所需的心理学或神经科学语境。
# 疾病名称本身不再一刀切排除：若其确实研究心理行为或身心干预，交由
# DeepSeek 根据摘要作最终判断。
ANIMAL_TITLE_TERMS = {
    "animal", "animal model", "mice", "mouse", "murine", "rat", "rats", "rodent",
    "rodents", "zebrafish", "canine", "porcine", "swine", "pig", "pigs",
    "dog", "dogs", "canines", "rabbit", "rabbits", "hamster", "hamsters",
    "guinea pig", "guinea pigs", "macaque", "macaques", "primate", "primates",
    "nonhuman primate", "monkey", "monkeys", "drosophila", "c. elegans",
    "knockout mouse", "transgenic mouse",
}
PURE_MECHANISTIC_TERMS = {
    "cellular", "cell culture", "cell line", "in vitro", "ex vivo", "histology",
    "immunofluorescence", "western blot", "molecular mechanism",
    "cellular mechanism", "biological mechanism", "physiological mechanism",
    "neural mechanism", "neurophysiological mechanism", "receptor expression",
    "receptor binding", "protein expression", "gene expression", "genetic expression",
    "molecular pathway", "signaling pathway", "mechanistic study",
    "organoid", "organoids", "tissue culture", "neuronal culture", "cell assay",
    "immunoblot", "rna sequencing", "rna-seq", "transcriptomic", "proteomic",
    "knockout", "transgenic", "gene knockout", "receptor agonist", "receptor antagonist",
}

# 此集合专用于“纯机制”排除条件；心率、HRV 等生理指标本身不构成心理结局。
PSYCHOLOGICAL_OUTCOME_TERMS = {
    "mental", "psycholog", "psychiatr", "depress", "anxiety", "stress",
    "emotion", "affect", "mood", "cognitive", "behavior", "behaviour",
    "wellbeing", "well-being", "quality of life", "subjective", "experience",
    "sleep", "insomnia", "pain", "coping", "self-efficacy", "loneliness",
    "flourishing", "resilience", "self-regulation", "health behavior",
    "health behaviour", "attention", "executive", "decision", "social cognition",
}
OBJECTIVE_DYNAMIC_MEASUREMENT_TERMS = {
    "ecological momentary assessment", "experience sampling", "ambulatory assessment",
    "intensive longitudinal", "daily diary", "digital phenotyping", "passive sensing",
    "mobile sensing", "wearable", "wearables", "biosensor", "biosensors",
    "actigraphy", "accelerometry", "electrodermal activity", "skin conductance",
    "photoplethysmography", "ppg", "ecg", "eeg", "heart rate variability", "hrv",
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

# 心理微干预必须先命中明确的干预锚点；泛 ``therapy/treatment/trial/protocol``
# 不能单独构成干预证据，以免普通长程 CBT/ACT 或一般医疗治疗进入候选池。
MENTAL_MICRO_OUTCOME_TERMS = {
    "mental health", "mental", "psycholog", "psychiatr", "depress", "anxiety",
    "stress", "emotion", "affect", "mood", "cognitive", "behavior", "behaviour",
    "wellbeing", "well-being", "quality of life", "subjective", "experience",
    "psychophysiolog", "heart rate variability", "hrv",
}
MENTAL_MICRO_EXPLICIT_TERMS = {
    "micro-intervention", "microintervention", "brief intervention",
    "single-session intervention", "single session", "self-guided intervention",
    "self-help intervention", "self-help exercise",
}
MENTAL_MICRO_MINDBODY_TERMS = {
    "mindfulness-based intervention", "mindfulness intervention", "mindfulness practice",
    "meditation intervention", "meditation training", "meditation program",
    "loving-kindness meditation", "compassion meditation", "body scan", "mindful movement",
    "relaxation intervention", "relaxation therapy", "relaxation training",
    "progressive muscle relaxation", "autogenic training", "guided imagery",
    "breathing intervention", "breathing exercise", "paced breathing", "slow breathing",
    "slow-paced breathing", "mindful breathing", "diaphragmatic breathing",
    "deep breathing", "breathwork", "biofeedback", "hrv biofeedback",
    "heart rate variability biofeedback", "somatic intervention", "somatic therapy",
    "somatic experiencing", "body-oriented psychotherapy", "body psychotherapy",
    "dance movement therapy", "mind-body exercise", "mind-body intervention",
    "mind-body therapy", "behavioral activation", "behavioural activation",
}
MENTAL_MICRO_DIGITAL_TERMS = {
    "digital intervention", "digital psychological intervention", "mobile intervention",
    "smartphone intervention", "app-based intervention", "web-based intervention",
    "internet-based intervention", "mhealth intervention", "digital therapeutics",
    "dmhi", "icbt", "ai-assisted intervention", "virtual reality intervention",
    "wearable intervention",
}
# 这些词只有与明确实施形式成对出现时，才可作为数字递送心理微干预锚点。
MENTAL_MICRO_DELIVERY_TERMS = {
    "digital", "mobile", "smartphone", "app", "web", "internet", "mhealth",
    "ehealth", "wearable", "virtual reality", "ai-assisted",
}
MENTAL_MICRO_IMPLEMENTATION_TERMS = {
    "intervention", "training", "exercise", "program", "programme", "session",
}
MENTAL_MICRO_ANY_INTERVENTION_TERMS = (
    MENTAL_MICRO_EXPLICIT_TERMS
    | MENTAL_MICRO_MINDBODY_TERMS
    | MENTAL_MICRO_DIGITAL_TERMS
)

# PubMed 是严格布尔检索。第三主线采用“心理/行为/动态/心理生理语境
# AND 微干预词”作为入口；高特异身心或简短干预另设入口。泛治疗、随机化
# 与方案词不单独用于检索，避免把大量一般医学研究引入候选池。
MENTAL_HEALTH_RETRIEVAL_OUTCOME_TERMS = (
    "mental health", "emotion regulation", "psychological distress", "stress",
    "anxiety", "depression", "mood", "affect", "well-being",
    "mental wellbeing", "psychological well-being", "flourishing", "resilience",
    "loneliness", "coping", "self-efficacy", "quality of life",
    "health behavior", "health behaviour", "self-regulation",
    "sleep", "insomnia", "pain", "mental", "psycholog", "psychiatr", "emotion",
    "cognitive", "behavior", "behaviour", "subjective", "experience", "wellbeing",
    "daily monitoring", "dynamic measurement", "dynamic monitoring",
    "ambulatory monitoring", "ecological", "experience sampling", "ema", "esm",
    "psychophysiolog", "heart rate variability", "hrv", "heart rate",
    "eeg", "erp", "hep", "interoception", "neuroimaging", "fmri", "neuroscience",
    "neural", "brain", "mindfulness", "meditation", "relaxation", "breathing",
    "biofeedback", "adherence", "motivation", "attention", "executive", "decision",
    "social cognition",
)
MENTAL_HEALTH_RETRIEVAL_MICROINTERVENTION_TERMS = (
    "micro-intervention", "self-guided intervention", "self-help intervention",
    "digital intervention", "mobile intervention", "self-help exercise",
    "digital mental health", "digital psychological intervention", "app-based intervention",
    "mhealth intervention", "digital therapeutics", "dmhi", "ehealth", "icbt",
    "ai-assisted intervention", "wearable intervention", "brief intervention",
    "single-session intervention",
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
def _pubmed_title_abstract_any(terms):
    return " OR ".join(f'"{term}"[Title/Abstract]' for term in terms)


PUBMED_MENTAL_HEALTH_QUERY = (
    f"(({_pubmed_title_abstract_any(MENTAL_HEALTH_RETRIEVAL_OUTCOME_TERMS)}) "
    f"AND ({_pubmed_title_abstract_any(MENTAL_HEALTH_RETRIEVAL_MICROINTERVENTION_TERMS)})) "
    f"OR ({_pubmed_title_abstract_any(MENTAL_HEALTH_HIGH_SPECIFIC_INTERVENTION_TERMS)}))"
)

# PubMed 检索按三条主线分为三个 tiab 模块。心理微干预模块已在检索入口
# 引入语境限制；其余直接主题的最终直接性判断仍由本地预筛和 DeepSeek 完成。
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
# 仅供 EMA/ESM、EMI/JITAI 分支使用；词干 psycholog/psychiatr/depress
# 由 _SAFE_STEM_PREFIXES 以 ``*`` 语义匹配其派生形式。
PSYCHOLOGY_NEUROSCIENCE_CONTEXT_TERMS = {
    "mental", "psycholog", "psychiatr", "depress", "anxiety", "stress",
    "emotion", "affect", "mood", "cognitive", "behavior", "behaviour",
    "wellbeing", "well-being", "quality of life", "subjective",
    "psychophysiolog", "hrv", "heart rate", "wearable", "passive sensing",
    "mobile sensing", "daily monitoring", "dynamic measurement", "neuroimaging",
    "sleep", "insomnia", "pain", "adherence", "mindfulness", "meditation",
    "relaxation", "breathing", "biofeedback",
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
    "心理微干预": (
        "心理微干预", "心理健康与数字心理干预", "心理健康", "数字心理干预",
        "数字/移动心理干预",
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


_SAFE_STEM_PREFIXES = {
    "psycholog", "psychiatr", "depress", "intervention", "behavior",
    "behaviour", "psychophysiolog", "psychotherap",
}


def _contains_term(text, term):
    """以整词/整短语匹配正向词；仅允许少数安全词干匹配派生形式。"""
    normalized = str(text or "").casefold()
    normalized_term = str(term or "").casefold().strip()
    if not normalized_term:
        return False
    phrase = re.escape(normalized_term).replace(r"\ ", r"\s+")
    if normalized_term in _SAFE_STEM_PREFIXES:
        phrase = re.escape(normalized_term) + r"\w*"
    return bool(re.search(rf"(?<!\w){phrase}(?!\w)", normalized))


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
    title_text = str(title or "")
    abstract_text = str(abstract or "")
    text = " ".join((title_text, abstract_text))
    # 用户确认：动物词一旦出现在标题或摘要中，即直接排除，不再区分背景提及
    # 与实际动物对象。
    if _has_any_whole_phrase(text, ANIMAL_TITLE_TERMS):
        return {
            "accepted": False,
            "groups": [],
            "reason": "animal_term_in_title_or_abstract",
        }
    has_psychological_outcome = _has_any(text, PSYCHOLOGICAL_OUTCOME_TERMS)
    has_any_intervention = (
        _has_any(text, MENTAL_MICRO_ANY_INTERVENTION_TERMS)
        or _has_any(text, EMA_EMI_INTERVENTION_TERMS)
    )
    has_ema_or_objective_dynamic_measurement = _has_any_whole_phrase(
        text, OBJECTIVE_DYNAMIC_MEASUREMENT_TERMS
    )
    # 纯细胞、分子、受体、基因表达或纯神经/生理机制研究，只有在具有人类
    # 心理结局、实际干预、或 EMA/客观动态测量之一时才保留候选资格。
    if (
        _has_any_whole_phrase(text, PURE_MECHANISTIC_TERMS)
        and not (
            has_psychological_outcome
            or has_any_intervention
            or has_ema_or_objective_dynamic_measurement
        )
    ):
        return {
            "accepted": False,
            "groups": [],
            "reason": "pure_mechanistic_without_required_signal",
        }
    has_psych_neuro_context = _has_any(text, PSYCHOLOGY_NEUROSCIENCE_CONTEXT_TERMS)
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
            # HRV/迷走/自主神经等词非常宽泛，仍需心理或神经科学语境；综述
            # 不享有例外，和其他文章使用同一判断。
            if not _has_any(text, HEART_BRAIN_PSYCHOLOGICAL_CONTEXT_TERMS):
                continue
            accepted_groups.append(group["label"])
            reasons.append(
                "eeg_ecg_psych_context" if has_eeg_ecg_pair else "heart_brain_psych_context"
            )
            continue
        if group_id == "mental_health":
            has_outcome = _has_any(text, MENTAL_MICRO_OUTCOME_TERMS)
            has_explicit_micro = _has_any(text, MENTAL_MICRO_EXPLICIT_TERMS)
            has_mindbody_micro = _has_any(text, MENTAL_MICRO_MINDBODY_TERMS)
            has_direct_digital_micro = _has_any(text, MENTAL_MICRO_DIGITAL_TERMS)
            has_digital_delivery_pair = (
                _has_any(text, MENTAL_MICRO_DELIVERY_TERMS)
                and _has_any(text, MENTAL_MICRO_IMPLEMENTATION_TERMS)
            )
            has_microintervention_anchor = (
                has_explicit_micro
                or has_mindbody_micro
                or has_direct_digital_micro
                or has_digital_delivery_pair
            )
            # 必须同时有心理/情绪/行为/主观体验/心理生理结局与明确微干预锚点。
            # 泛 therapy/treatment/trial/protocol 不再单独放行普通长程治疗。
            if not (has_outcome and has_microintervention_anchor):
                continue
            accepted_groups.append(group["label"])
            reasons.append("mental_microintervention")
            continue
        if group_id == "emi":
            has_core_method = _has_any(text, EMA_EMI_CORE_METHOD_TERMS)
            has_intervention = _has_any(text, EMA_EMI_INTERVENTION_TERMS)
            has_physiology = _has_any_whole_phrase(text, EMA_EMI_PHYSIOLOGICAL_TERMS)
            # 排除只做自评问卷的 EMA/ESM；需为直接干预，或结合客观生理/传感
            # 指标。综述不单独放行，和其他文章采用同一方法/语境要求。
            if not (
                has_core_method
                and (has_intervention or has_physiology)
                and has_psych_neuro_context
            ):
                continue
            accepted_groups.append(group["label"])
            if has_intervention and has_physiology:
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
