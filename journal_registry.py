"""三主线文献追踪的 ISSN 白名单。

筛选规则：期刊必须同时满足“与三条主线直接相关”与“JCR Q1/Q2”。ISSN
精确匹配优先；只有原始记录没有 ISSN 时才使用严格的期刊全名/唯一缩写匹配。

指标来自 impact_factor 1.1.3（PyPI 于 2025-11-25 发布，自述为 2025 数据）。
该第三方库没有为每条记录提供 JIF 统计年度或 JCR 学科分类明细，故本文件不将其
伪称为 Clarivate 官方导出；将来获得官方导出后可按 ISSN 覆盖相应字段。
"""

import os
import re


METRICS_SOURCE = "impact_factor 1.1.3（2025-11-25 发布）"
METRICS_RELEASE_YEAR = 2025

HEART_BRAIN = "心脑轴"
EMA_EMI = "生态瞬时干预"
MENTAL_HEALTH = "心理健康与数字心理干预"


# name, pISSN, eISSN, IF, JCR, tracks, aliases
# "-" 表示该库未给出对应 ISSN；数值与分区均直接取自其 SQLite 数据库。
_JOURNAL_ROWS = (
    # 心脑轴、心理生理、神经科学
    ("Psychophysiology", "0048-5772", "1469-8986", 2.8, "Q1", (HEART_BRAIN,), ()),
    ("International Journal of Psychophysiology", "0167-8760", "1872-7697", 2.6, "Q2", (HEART_BRAIN,), ()),
    ("Biological Psychology", "0301-0511", "1873-6246", 2.9, "Q1", (HEART_BRAIN,), ()),
    ("Autonomic Neuroscience: Basic and Clinical", "1566-0702", "1872-7484", 3.3, "Q2", (HEART_BRAIN,), ("Autonomic Neuroscience",)),
    ("Psychosomatic Medicine", "0033-3174", "1534-7796", 2.4, "Q2", (HEART_BRAIN, MENTAL_HEALTH), ()),
    ("Psychoneuroendocrinology", "0306-4530", "1873-3360", 3.6, "Q1", (HEART_BRAIN, MENTAL_HEALTH), ()),
    ("Journal of Psychosomatic Research", "0022-3999", "1879-1360", 3.3, "Q2", (HEART_BRAIN, MENTAL_HEALTH), ()),
    ("Applied Psychophysiology and Biofeedback", "1090-0586", "1573-3270", 2.4, "Q2", (HEART_BRAIN,), ()),
    ("Neuroscience & Biobehavioral Reviews", "0149-7634", "1873-7528", 7.9, "Q1", (HEART_BRAIN,), ("Neuroscience and Biobehavioral Reviews",)),
    ("Network Neuroscience", "2472-1751", "2472-1751", 3.1, "Q2", (HEART_BRAIN,), ()),
    ("NeuroImage", "1053-8119", "1095-9572", 4.5, "Q1", (HEART_BRAIN,), ()),
    ("Cerebral Cortex", "1047-3211", "1460-2199", 2.9, "Q2", (HEART_BRAIN,), ()),
    ("Social Cognitive and Affective Neuroscience", "1749-5016", "1749-5024", 3.1, "Q1", (HEART_BRAIN, MENTAL_HEALTH), ("SCAN",)),
    ("Nature Neuroscience", "1097-6256", "1546-1726", 20.0, "Q1", (HEART_BRAIN,), ()),
    ("Nature Reviews Neuroscience", "1471-003X", "1471-0048", 26.7, "Q1", (HEART_BRAIN,), ()),
    ("Biological Psychiatry", "0006-3223", "1873-2402", 9.0, "Q1", (HEART_BRAIN, MENTAL_HEALTH), ()),
    ("Biological Psychiatry: Cognitive Neuroscience and Neuroimaging", "2451-9022", "2451-9030", 4.8, "Q1", (HEART_BRAIN,), ()),
    ("Brain, Behavior, and Immunity", "0889-1591", "1090-2139", 7.6, "Q1", (HEART_BRAIN, MENTAL_HEALTH), ("Brain Behavior and Immunity",)),
    ("Stress", "1025-3890", "1607-8888", 2.9, "Q1", (HEART_BRAIN, MENTAL_HEALTH), ("Stress-The International Journal on the Biology of Stress",)),

    # EMA / ESM、EMI / JITAI、数字表型与方法学
    ("Psychological Methods", "1082-989X", "1939-1463", 3.5, "Q1", (EMA_EMI,), ()),
    ("Behavior Research Methods", "1554-351X", "1554-3528", 3.9, "Q1", (EMA_EMI,), ()),
    ("Multivariate Behavioral Research", "0027-3171", "1532-7906", 3.5, "Q1", (EMA_EMI,), ()),
    ("Assessment", "1073-1911", "1552-3489", 3.4, "Q1", (EMA_EMI,), ()),
    ("Advances in Methods and Practices in Psychological Science", "2515-2459", "2515-2467", 13.4, "Q1", (EMA_EMI,), ("AMPPS",)),
    ("Psychological Assessment", "1040-3590", "1939-134X", 3.3, "Q1", (EMA_EMI, MENTAL_HEALTH), ()),
    ("npj Digital Medicine", "-", "2398-6352", 15.1, "Q1", (EMA_EMI, MENTAL_HEALTH), ()),
    ("The Lancet Digital Health", "-", "2589-7500", 24.1, "Q1", (EMA_EMI, MENTAL_HEALTH), ("Lancet Digital Health",)),
    ("Journal of Medical Internet Research", "1438-8871", "-", 6.0, "Q1", (EMA_EMI, MENTAL_HEALTH), ("JMIR",)),
    ("JMIR Mental Health", "2368-7959", "2368-7959", 5.8, "Q1", (EMA_EMI, MENTAL_HEALTH), ()),
    ("JMIR mHealth and uHealth", "2291-5222", "2291-5222", 6.2, "Q1", (EMA_EMI, MENTAL_HEALTH), ()),
    ("Internet Interventions", "-", "2214-7829", 4.1, "Q1", (EMA_EMI, MENTAL_HEALTH), ("Internet Interventions-The Application of Information Technology in Mental and Behavioural Health",)),
    ("DIGITAL HEALTH", "2055-2076", "2055-2076", 3.3, "Q1", (EMA_EMI, MENTAL_HEALTH), ("Digital Health",)),
    ("Frontiers in Digital Health", "-", "2673-253X", 3.8, "Q1", (EMA_EMI, MENTAL_HEALTH), ()),
    ("Journal of the American Medical Informatics Association", "1067-5027", "1527-974X", 4.6, "Q1", (EMA_EMI, MENTAL_HEALTH), ("JAMIA",)),
    ("Journal of Biomedical Informatics", "1532-0464", "1532-0480", 4.5, "Q2", (EMA_EMI,), ()),
    ("Pervasive and Mobile Computing", "1574-1192", "1873-1589", 3.5, "Q2", (EMA_EMI,), ()),
    ("Computers in Human Behavior", "0747-5632", "1873-7692", 8.9, "Q1", (EMA_EMI, MENTAL_HEALTH), ()),
    ("Cyberpsychology, Behavior, and Social Networking", "2152-2715", "2152-2723", 3.9, "Q1", (EMA_EMI, MENTAL_HEALTH), ("Cyberpsychology Behavior and Social Networking",)),
    ("Journal of Contextual Behavioral Science", "2212-1447", "2212-1455", 3.0, "Q1", (EMA_EMI, MENTAL_HEALTH), ()),

    # 心理健康、情绪调节、临床与数字/移动心理干预
    ("Journal of Consulting and Clinical Psychology", "0022-006X", "1939-2117", 5.0, "Q1", (MENTAL_HEALTH,), ("JCCP",)),
    ("Behaviour Research and Therapy", "0005-7967", "1873-622X", 4.5, "Q1", (MENTAL_HEALTH,), ()),
    ("Clinical Psychology Review", "0272-7358", "1873-7811", 12.2, "Q1", (MENTAL_HEALTH,), ()),
    ("Clinical Psychological Science", "2167-7026", "2167-7034", 4.1, "Q1", (MENTAL_HEALTH,), ()),
    ("Health Psychology", "0278-6133", "1930-7810", 3.2, "Q1", (MENTAL_HEALTH,), ()),
    ("Health Psychology Review", "1743-7199", "1743-7202", 9.7, "Q1", (MENTAL_HEALTH,), ()),
    ("Behavior Therapy", "0005-7894", "1878-1888", 3.8, "Q1", (MENTAL_HEALTH,), ()),
    ("Annual Review of Clinical Psychology", "1548-5943", "1548-5951", 16.5, "Q1", (MENTAL_HEALTH,), ()),
    ("The Lancet Psychiatry", "2215-0374", "-", 24.8, "Q1", (MENTAL_HEALTH,), ("Lancet Psychiatry",)),
    ("JAMA Psychiatry", "2168-622X", "2168-6238", 17.1, "Q1", (MENTAL_HEALTH,), ()),
    ("Molecular Psychiatry", "1359-4184", "1476-5578", 10.1, "Q1", (HEART_BRAIN, MENTAL_HEALTH), ()),
    ("Psychological Medicine", "0033-2917", "1469-8978", 5.5, "Q1", (MENTAL_HEALTH,), ()),
    ("Nature Mental Health", "-", "2731-6076", 8.7, "Q1", (MENTAL_HEALTH,), ()),
    ("World Psychiatry", "1723-8617", "2051-5545", 65.8, "Q1", (MENTAL_HEALTH,), ()),
    ("American Journal of Psychiatry", "0002-953X", "1535-7228", 14.7, "Q1", (MENTAL_HEALTH,), ()),
    ("British Journal of Psychiatry", "0007-1250", "1472-1465", 7.6, "Q1", (MENTAL_HEALTH,), ()),
    ("Journal of Affective Disorders", "0165-0327", "1573-2517", 4.9, "Q1", (MENTAL_HEALTH,), ()),
    ("Depression and Anxiety", "1091-4269", "1520-6394", 3.3, "Q1", (MENTAL_HEALTH,), ()),
    ("Journal of Anxiety Disorders", "0887-6185", "1873-7897", 4.5, "Q1", (MENTAL_HEALTH,), ()),
    ("Clinical Psychology: Science and Practice", "0969-5893", "1468-2850", 6.6, "Q1", (MENTAL_HEALTH,), ()),
    ("Journal of Clinical Psychology", "0021-9762", "1097-4679", 2.5, "Q2", (MENTAL_HEALTH,), ()),
    ("Cognitive Behaviour Therapy", "1650-6073", "1651-2316", 3.2, "Q1", (MENTAL_HEALTH,), ()),
    ("Cognitive Therapy and Research", "0147-5916", "1573-2819", 2.0, "Q2", (MENTAL_HEALTH,), ()),
    ("Mindfulness", "1868-8527", "1868-8535", 3.5, "Q1", (MENTAL_HEALTH,), ()),
    ("Psychological Trauma: Theory, Research, Practice, and Policy", "1942-9681", "1942-969X", 2.3, "Q2", (MENTAL_HEALTH,), ("Psychological Trauma-Theory Research Practice and Policy",)),
    ("European Journal of Psychotraumatology", "2000-8198", "2000-8066", 4.1, "Q1", (MENTAL_HEALTH,), ()),
    ("Psychiatry Research", "0165-1781", "1872-7123", 3.9, "Q1", (MENTAL_HEALTH,), ()),
    ("Journal of Psychiatric Research", "0022-3956", "1879-1379", 3.2, "Q2", (MENTAL_HEALTH,), ()),
    ("Social Psychiatry and Psychiatric Epidemiology", "0933-7954", "1433-9285", 3.5, "Q1", (MENTAL_HEALTH,), ()),
    ("Frontiers in Psychiatry", "1664-0640", "1664-0640", 3.2, "Q2", (MENTAL_HEALTH,), ()),
    ("BMC Psychiatry", "-", "1471-244X", 3.6, "Q1", (MENTAL_HEALTH,), ()),
    ("Translational Psychiatry", "2158-3188", "2158-3188", 6.2, "Q1", (MENTAL_HEALTH,), ()),
    ("Journal of Child Psychology and Psychiatry", "0021-9630", "1469-7610", 7.0, "Q1", (MENTAL_HEALTH,), ()),
    ("European Child & Adolescent Psychiatry", "1018-8827", "1435-165X", 4.9, "Q1", (MENTAL_HEALTH,), ()),

    # 仅保留与三主线有直接发表交集的跨学科旗舰刊
    ("Nature", "0028-0836", "1476-4687", 48.5, "Q1", (HEART_BRAIN, EMA_EMI, MENTAL_HEALTH), ()),
    ("Science", "0036-8075", "1095-9203", 45.8, "Q1", (HEART_BRAIN, EMA_EMI, MENTAL_HEALTH), ()),
    ("Nature Communications", "-", "2041-1723", 15.7, "Q1", (HEART_BRAIN, EMA_EMI, MENTAL_HEALTH), ()),
    ("Science Advances", "2375-2548", "2375-2548", 12.5, "Q1", (HEART_BRAIN, EMA_EMI, MENTAL_HEALTH), ()),
    ("Proceedings of the National Academy of Sciences of the United States of America", "0027-8424", "1091-6490", 9.1, "Q1", (HEART_BRAIN, EMA_EMI, MENTAL_HEALTH), ("PNAS",)),
    ("Nature Human Behaviour", "2397-3374", "2397-3374", 15.9, "Q1", (EMA_EMI, MENTAL_HEALTH), ("Nature Human Behavior",)),
    ("Nature Medicine", "1078-8956", "1546-170X", 50.0, "Q1", (HEART_BRAIN, MENTAL_HEALTH), ()),
    ("The Lancet", "0140-6736", "1474-547X", 88.5, "Q1", (HEART_BRAIN, EMA_EMI, MENTAL_HEALTH), ("Lancet",)),
    ("JAMA", "0098-7484", "1538-3598", 55.0, "Q1", (HEART_BRAIN, EMA_EMI, MENTAL_HEALTH), ("JAMA-Journal of the American Medical Association",)),
    ("BMJ", "0959-535X", "1756-1833", 42.7, "Q1", (HEART_BRAIN, EMA_EMI, MENTAL_HEALTH), ("BMJ-British Medical Journal",)),
)


def normalize_issn(value):
    """将 ISSN 规范化为无连字符的大写形式。"""
    return re.sub(r"[^0-9X]", "", str(value or "").upper())


def _normalise_name(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


JOURNAL_WHITELIST = []
_BY_ISSN = {}
_BY_NAME = {}
for _name, _pissn, _eissn, _factor, _quartile, _tracks, _aliases in _JOURNAL_ROWS:
    _profile = {
        "name": _name,
        "pissn": None if _pissn == "-" else _pissn,
        "eissn": None if _eissn == "-" else _eissn,
        "impact_factor": _factor,
        "jcr_quartile": _quartile,
        "tracks": list(_tracks),
        "aliases": list(_aliases),
        "metrics_source": METRICS_SOURCE,
        "metrics_release_year": METRICS_RELEASE_YEAR,
    }
    JOURNAL_WHITELIST.append(_profile)
    for _issn in (_profile["pissn"], _profile["eissn"]):
        _key = normalize_issn(_issn)
        if _key:
            _BY_ISSN[_key] = _profile
    for _variant in (_name, *_aliases):
        _BY_NAME[_normalise_name(_variant)] = _profile


def get_journal_profile(journal_name=None, issns=None):
    """按 ISSN 或严格名称返回期刊元数据；未知期刊返回 None。"""
    candidates = [issns] if isinstance(issns, str) else (issns or [])
    for issn in candidates:
        profile = _BY_ISSN.get(normalize_issn(issn))
        if profile:
            return dict(profile)
    return dict(_BY_NAME[_normalise_name(journal_name)]) if _normalise_name(journal_name) in _BY_NAME else None


def filter_by_journal(journal_name=None, issns=None, journal_names=None):
    """默认启用领域白名单；仅显式设为 false 时供本地调试绕过。"""
    if os.getenv("JOURNAL_FILTER_ENABLED", "true").strip().lower() in {"0", "false", "no", "off"}:
        return True
    candidates = [issns] if isinstance(issns, str) else (issns or [])
    if candidates:
        return any(normalize_issn(issn) in _BY_ISSN for issn in candidates)
    names = [journal_name] if journal_name else []
    if journal_names:
        names.extend([journal_names] if isinstance(journal_names, str) else journal_names)
    return any(_normalise_name(name) in _BY_NAME for name in names if name)
