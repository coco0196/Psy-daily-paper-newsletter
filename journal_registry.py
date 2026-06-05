"""
目标心理学顶刊 ISSN 与名称对照表。

ISSN 来源：NLM Catalog、APA PsycArticles、ISSN Portal、出版社官网（2026-06 核对）。
筛选策略：ISSN 精确匹配优先；仅当文献缺失 ISSN 时，才回退到期刊名称/缩写模糊匹配。
"""

import re

# pissn / eissn 均为带连字符的标准 ISSN 格式；无纸质版时 pissn 为 None
TARGET_JOURNALS = [
    {
        "name": "Emotion",
        "pissn": "1528-3542",
        "eissn": "1931-1516",
    },
    {
        "name": "Social Cognitive and Affective Neuroscience",
        "pissn": "1749-5016",
        "eissn": "1749-5024",
    },
    {
        "name": "Journal of Personality and Social Psychology",
        "pissn": "0022-3514",
        "eissn": "1939-1315",
    },
    {
        "name": "Journal of Experimental Social Psychology",
        "pissn": "0022-1031",
        "eissn": "1095-9920",
    },
    {
        "name": "Emotion Review",
        "pissn": "1754-0739",
        "eissn": "1754-0747",
    },
    {
        "name": "Cognition & Emotion",
        "pissn": "0269-9931",
        "eissn": "1464-0600",
    },
    {
        "name": "British Journal of Social Psychology",
        "pissn": "0144-6665",
        "eissn": "2044-8309",
    },
    {
        "name": "Personality and Social Psychology Review",
        "pissn": "1088-8683",
        "eissn": "1532-7965",
    },
    {
        "name": "European Review Of Social Psychology",
        "pissn": "1046-3283",
        "eissn": "1479-277X",
    },
    {
        "name": "Advances In Methods And Practices In Psychological Science",
        "pissn": "2515-2459",
        "eissn": "2515-2467",
    },
    {
        "name": "Motivation and Emotion",
        "pissn": "0146-7239",
        "eissn": "1573-6644",
    },
    {
        "name": "Perspectives on Psychological Science",
        "pissn": "1745-6916",
        "eissn": "1745-6924",
    },
    {
        "name": "Current Directions in Psychological Science",
        "pissn": "0963-7214",
        "eissn": "1467-8721",
    },
    {
        "name": "Psychological Inquiry",
        "pissn": "1047-840X",
        "eissn": "1532-7965",
    },
    {
        "name": "Current Opinion in Psychology",
        "pissn": "2352-250X",
        "eissn": "2352-2518",
    },
    {
        "name": "Journal of Nonverbal Behavior",
        "pissn": "0191-5886",
        "eissn": "1573-3653",
    },
    {
        "name": "Psychology of Aesthetics, Creativity, and the Arts",
        "pissn": "1931-3896",
        "eissn": "1931-390X",
    },
    {
        "name": "Nature",
        "pissn": "0028-0836",
        "eissn": "1476-4687",
    },
    {
        "name": "Science",
        "pissn": "0036-8075",
        "eissn": "1095-9203",
    },
    {
        "name": "Nature Communications",
        "pissn": None,
        "eissn": "2041-1723",
    },
    {
        "name": "Nature Human Behaviour",
        "pissn": None,
        "eissn": "2397-3374",
    },
    {
        "name": "Proceedings of the National Academy of Sciences",
        "pissn": "0027-8424",
        "eissn": "1091-6490",
    },
    {
        "name": "Psychological Science",
        "pissn": "0956-7976",
        "eissn": "1467-9280",
    },
    {
        "name": "American Psychologist",
        "pissn": "0003-066X",
        "eissn": "1935-990X",
    },
    {
        "name": "Computers in Human Behavior",
        "pissn": "0747-5632",
        "eissn": "1873-7692",
    },
    {
        "name": "Science Advances",
        "pissn": None,
        "eissn": "2375-2548",
    },
    {
        "name": "Psychological Bulletin",
        "pissn": "0033-2909",
        "eissn": "1939-1455",
    },
    {
        "name": "Psychological Review",
        "pissn": "0033-295X",
        "eissn": "1939-1471",
    },
    {
        "name": "Psychological Methods",
        "pissn": "1082-989X",
        "eissn": "1939-1463",
    },
    {
        "name": "Social Psychological and Personality Science",
        "pissn": "1948-5506",
        "eissn": "1948-5514",
    },
    {
        "name": "Personality and Social Psychology Bulletin",
        "pissn": "0146-1672",
        "eissn": "1552-7433",
    },
    {
        "name": "Journal of Experimental Psychology: General",
        "pissn": "0096-3445",
        "eissn": "1939-2222",
    },
    {
        "name": "Cultural Diversity & Ethnic Minority Psychology",
        "pissn": "1099-9809",
        "eissn": "1939-0106",
    },
    {
        "name": "Journal of Cross-Cultural Psychology",
        "pissn": "0022-0222",
        "eissn": "1552-5422",
    },
    {
        "name": "Journal of Social and Personal Relationships",
        "pissn": "0265-4075",
        "eissn": "1461-7188",
    },
]


def normalize_issn(issn):
    """去除连字符并大写，便于集合比较。"""
    if not issn:
        return ""
    return re.sub(r"[^0-9X]", "", str(issn).upper())


def _build_target_issn_set():
    issns = set()
    for journal in TARGET_JOURNALS:
        for key in ("pissn", "eissn"):
            value = journal.get(key)
            normalized = normalize_issn(value)
            if normalized:
                issns.add(normalized)
    return issns


TARGET_ISSN_SET = _build_target_issn_set()


def _normalize_journal_name(name):
    if not name:
        return ""
    normalized = str(name).strip().lower()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


# 名称匹配备用规则（特异性从高到低）
_TARGET_JOURNAL_PATTERN_STRINGS = [
    r"social cognitive and affective neuroscience|soc cogn affect neurosci|\bscan\b",
    r"motivation and emotion|motiv emot",
    r"cognition and emotion|cogn(?:ition)? emotion",
    r"personality and social psychology review|pers soc psychol rev|\bpspr\b",
    r"personality and social psychology bulletin|pers soc psychol bull|\bpspb\b",
    r"social psychological and personality science|soc psychol personal sci|\bspps\b",
    r"journal of personality and social psychology|j pers soc psychol|\bjpsp\b",
    r"journal of experimental social psychology|j exp soc psychol|\bjesp\b",
    r"journal of experimental psychology[:,\s]+general|j exp psychol gen",
    r"journal of cross[- ]cultural psychology|j cross cult psychol",
    r"journal of social and personal relationships|j soc pers relat",
    r"cultural diversity (?:and|&) ethnic minority psychology",
    r"psychology of aesthetics, creativity, and the arts|psychol aesthet creat arts",
    r"advances in methods and practices in psychological science|\bampps\b",
    r"perspectives on psychological science|perspect psychol sci",
    r"current directions in psychological science|curr dir psychol sci",
    r"current opinion in psychology|curr opin psychol",
    r"european review of social psychology|eur rev soc psychol",
    r"british journal of social psychology|br j soc psychol",
    r"journal of nonverbal behavior|j nonverbal behav",
    r"proceedings of the (?:national academy of sciences|natl acad sci)|\bpna?s\b",
    r"nature human behaviour|nature human behavior|nat hum behav",
    r"nature communications|nat commun",
    r"computers in human behavior|comput human behav|\bchb\b",
    r"science advances|sci adv",
    r"psychological bulletin|psychol bull",
    r"psychological review|psychol rev",
    r"psychological methods|psychol methods",
    r"psychological science|psychol sci",
    r"american psychologist|am psychol",
    r"psychological inquiry",
    r"emotion review",
    r"^emotion$",
    r"^nature$",
    r"^science$",
]

_JOURNAL_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in _TARGET_JOURNAL_PATTERN_STRINGS
]


def _coerce_issn_list(issns):
    if not issns:
        return []
    if isinstance(issns, str):
        issns = [issns]
    out = []
    for value in issns:
        normalized = normalize_issn(value)
        if normalized:
            out.append(normalized)
    return out


def _match_journal_name(journal_name):
    normalized = _normalize_journal_name(journal_name)
    if not normalized:
        return False
    return any(pattern.search(normalized) for pattern in _JOURNAL_PATTERNS)


def filter_by_journal(journal_name=None, issns=None, journal_names=None):
    """
    期刊筛选：ISSN 优先，名称模糊匹配为辅。

    - 若文献带有 ISSN：仅当命中 TARGET_ISSN_SET 时通过，否则丢弃（不再回退名称）。
    - 若文献缺失 ISSN：对 journal_name / journal_names 做名称匹配。
    """
    normalized_issns = _coerce_issn_list(issns)
    if normalized_issns:
        return bool(set(normalized_issns) & TARGET_ISSN_SET)

    names = []
    if journal_names:
        if isinstance(journal_names, str):
            names.append(journal_names)
        else:
            names.extend(journal_names)
    if journal_name:
        names.append(journal_name)

    seen = set()
    for name in names:
        key = _normalize_journal_name(name)
        if not key or key in seen:
            continue
        seen.add(key)
        if _match_journal_name(name):
            return True
    return False
