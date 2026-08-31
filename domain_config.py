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
