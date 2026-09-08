"""基于 2026 年度 JCR 表（2025 IF）的期刊分区索引与过滤规则。"""

import csv
import os
import re


METRICS_SOURCE = "2026年度JCR期刊分区表.xlsx"
METRICS_RELEASE_YEAR = 2026
IMPACT_FACTOR_YEAR = 2025
_DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "jcr_2026_journals.csv")


# 用户确认：这些期刊即使最高分区为 Q3/Q4，也允许进入后续本地主题筛选。
LOWER_QUARTILE_ALLOWLIST_NAMES = (
    "Psychological Services",
    "Journal of Clinical Psychology in Medical Settings",
    "Ansiedad y Estres-Anxiety and Stress",
    "American Journal of Lifestyle Medicine",
    "Arts & Health",
    "Women & Health",
    "Brain and Cognition",
    "Brain Connectivity",
    "Cerebral Cortex",
    "Psychiatry Research-Neuroimaging",
    "Social Neuroscience",
    "Behavioral Sleep Medicine",
    "Neuropsychological Rehabilitation",
    "Applied Clinical Informatics",
    "Health Informatics Journal",
    "International Journal of Telemedicine and Applications",
    "Telemedicine and e-Health",
    "Telemedicine Reports",
    "JMIR Research Protocols",
    "JMIR XR and Spatial Computing",
    "IEEE Pervasive Computing",
    "AUTONOMIC NEUROSCIENCE-BASIC & CLINICAL",
    "Adaptive Human Behavior and Physiology",
    "Health Psychology Open",
    "Health Psychology Report",
    "Smart Health",
    "Journal of Psychophysiology",
    "Behavioral Medicine",
    "European Journal of Health Psychology",
    "Annual Review of CyberTherapy and Telemedicine",
)


def normalize_issn(value):
    """将 ISSN 规范化为无连字符的大写形式。"""
    return re.sub(r"[^0-9X]", "", str(value or "").upper())


def _normalise_name(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


_ALLOWLIST_NAME_KEYS = {_normalise_name(name) for name in LOWER_QUARTILE_ALLOWLIST_NAMES}
_BY_ISSN = {}
_BY_NAME = {}


def _parse_impact_factor(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.startswith("<"):
        return raw
    try:
        return float(raw)
    except ValueError:
        return raw


def _load_registry():
    if not os.path.exists(_DATA_FILE):
        raise RuntimeError(f"缺少 JCR 运行时索引: {_DATA_FILE}")
    with open(_DATA_FILE, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            name = (row.get("journal_name") or "").strip()
            quartiles = [q for q in (row.get("all_quartiles") or "").split("|") if q]
            profile = {
                "name": name,
                "pissn": (row.get("pissn") or "").strip() or None,
                "eissn": (row.get("eissn") or "").strip() or None,
                "impact_factor": _parse_impact_factor(row.get("impact_factor")),
                "impact_factor_year": IMPACT_FACTOR_YEAR,
                "jcr_quartile": (row.get("best_quartile") or "").strip() or None,
                "jcr_quartiles": quartiles,
                "metrics_source": METRICS_SOURCE,
                "metrics_release_year": METRICS_RELEASE_YEAR,
                "metrics_status": "matched",
            }
            profile["lower_quartile_allowlisted"] = (
                _normalise_name(name) in _ALLOWLIST_NAME_KEYS
            )
            for issn in (profile["pissn"], profile["eissn"]):
                key = normalize_issn(issn)
                if key:
                    _BY_ISSN[key] = profile
            name_key = _normalise_name(name)
            if name_key:
                _BY_NAME[name_key] = profile


_load_registry()


# 仅用于没有 ISSN 且来源使用常见简称的记录；不做模糊刊名匹配。
_NAME_ALIASES = {
    "JMIR": "JOURNAL OF MEDICAL INTERNET RESEARCH",
    "Autonomic Neuroscience": "AUTONOMIC NEUROSCIENCE-BASIC & CLINICAL",
    "Internet Interventions": (
        "Internet Interventions-The Application of Information Technology in Mental and Behavioural Health"
    ),
    "The Lancet Digital Health": "Lancet Digital Health",
}
for alias, canonical in _NAME_ALIASES.items():
    profile = _BY_NAME.get(_normalise_name(canonical))
    if profile:
        _BY_NAME[_normalise_name(alias)] = profile


_ALLOWLIST_ISSNS = {
    normalize_issn(issn)
    for profile in _BY_NAME.values()
    if profile.get("lower_quartile_allowlisted")
    for issn in (profile.get("pissn"), profile.get("eissn"))
    if normalize_issn(issn)
}


def get_journal_profile(journal_name=None, issns=None):
    """按 ISSN 或严格规范化刊名返回 JCR 资料；未知期刊返回 None。"""
    candidates = [issns] if isinstance(issns, str) else (issns or [])
    for issn in candidates:
        profile = _BY_ISSN.get(normalize_issn(issn))
        if profile:
            return dict(profile)
    profile = _BY_NAME.get(_normalise_name(journal_name))
    return dict(profile) if profile else None


def journal_filter_decision(journal_name=None, issns=None, journal_names=None):
    """返回期刊是否保留、原因及匹配资料。未知分区保留。"""
    if os.getenv("JOURNAL_FILTER_ENABLED", "true").strip().lower() in {
        "0", "false", "no", "off"
    }:
        return True, "filter_disabled", get_journal_profile(journal_name, issns)

    candidates = [issns] if isinstance(issns, str) else (issns or [])
    names = [journal_name] if journal_name else []
    if journal_names:
        names.extend([journal_names] if isinstance(journal_names, str) else journal_names)

    profile = None
    for issn in candidates:
        profile = _BY_ISSN.get(normalize_issn(issn))
        if profile:
            break
    if profile is None:
        for name in names:
            profile = _BY_NAME.get(_normalise_name(name))
            if profile:
                break
    if profile is None:
        return True, "unknown_journal", None

    quartile = profile.get("jcr_quartile")
    allowlisted = profile.get("lower_quartile_allowlisted") or any(
        normalize_issn(issn) in _ALLOWLIST_ISSNS for issn in candidates
    )
    if quartile in {"Q3", "Q4"}:
        if allowlisted:
            return True, f"{quartile.lower()}_allowlisted", dict(profile)
        return False, f"{quartile.lower()}_excluded", dict(profile)
    if quartile in {"Q1", "Q2"}:
        return True, f"{quartile.lower()}_retained", dict(profile)
    return True, "unknown_quartile", dict(profile)


def filter_by_journal(journal_name=None, issns=None, journal_names=None):
    """排除非白名单 Q3/Q4；Q1/Q2、未知期刊及未知分区保留。"""
    allowed, _, _ = journal_filter_decision(
        journal_name=journal_name,
        issns=issns,
        journal_names=journal_names,
    )
    return allowed


JOURNAL_WHITELIST = [
    dict(profile)
    for profile in {id(p): p for p in _BY_ISSN.values()}.values()
    if profile.get("lower_quartile_allowlisted")
]
