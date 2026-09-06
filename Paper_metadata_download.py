import os
import re
import json
import html
import time
import datetime
import unicodedata
from difflib import SequenceMatcher
from math import ceil
import requests
import argparse
import xml.etree.ElementTree as ET
from requests.adapters import HTTPAdapter
from urllib3.exceptions import ProtocolError
from urllib3.util.retry import Retry
from utils import setup_logger, get_last_week_range, weekly_basename, iter_date_range
from journal_registry import filter_by_journal, get_journal_profile
from domain_config import (
    CROSSREF_TRACK_QUERIES,
    EEG_ECG_PUBMED_QUERY,
    PUBMED_MENTAL_HEALTH_QUERY,
    iter_topic_terms,
    local_prefilter_decision,
)

# 设置日志记录器
logger = setup_logger()

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CROSSREF_WORKS_URL = "https://api.crossref.org/works"
CROSSREF_USER_AGENT = "hf-daily-paper-bot/1.0 (mailto:zhugamen@gmail.com)"

def _make_api_session():
    """
    使用连接池 + urllib3 自动重试，供 NCBI E-utilities 与 Crossref REST API 共用，
    降低 TLS/连接被对端 RST（如 WinError 10054）时的失败率。
    """
    retry = Retry(
        total=10,
        connect=6,
        read=6,
        backoff_factor=1.2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=4, pool_maxsize=8)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": os.getenv("API_USER_AGENT", CROSSREF_USER_AGENT),
            "Accept-Encoding": "identity",
        }
    )
    return session


def _api_get(session, url, params, timeout, label="API"):
    """
    在 urllib3 重试之外再包一层：捕获连接被重置、超时等，做有限次指数退避重试。
    """
    max_rounds = int(os.getenv("NCBI_MANUAL_RETRIES", "5"))
    base = float(os.getenv("NCBI_MANUAL_RETRY_BASE_SEC", "1.5"))
    last_exc = None
    for round_idx in range(max_rounds):
        try:
            r = session.get(url, params=params, timeout=timeout)
            return r
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ChunkedEncodingError,
            ProtocolError,
        ) as e:
            last_exc = e
            if round_idx >= max_rounds - 1:
                raise
            wait = base * (2**round_idx)
            logger.warning(
                "%s 请求异常 (%s)，%.1fs 后进行第 %d/%d 次重试",
                label,
                e,
                wait,
                round_idx + 2,
                max_rounds,
            )
            time.sleep(wait)
    raise last_exc  # pragma: no cover


def _ncbi_post(session, url, data, timeout, label="NCBI"):
    """与 _api_get 相同的手动退避重试，用于 POST（长 term 避免 GET URL 超限）。"""
    max_rounds = int(os.getenv("NCBI_MANUAL_RETRIES", "5"))
    base = float(os.getenv("NCBI_MANUAL_RETRY_BASE_SEC", "1.5"))
    last_exc = None
    for round_idx in range(max_rounds):
        try:
            r = session.post(url, data=data, timeout=timeout)
            return r
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ChunkedEncodingError,
            ProtocolError,
        ) as e:
            last_exc = e
            if round_idx >= max_rounds - 1:
                raise
            wait = base * (2**round_idx)
            logger.warning(
                "%s POST 异常 (%s)，%.1fs 后进行第 %d/%d 次重试",
                label,
                e,
                wait,
                round_idx + 2,
                max_rounds,
            )
            time.sleep(wait)
    raise last_exc  # pragma: no cover


def _ncbi_common_params():
    """NCBI 推荐附带 tool / email；api_key 提高速率上限。"""
    params = {
        "tool": os.getenv("NCBI_TOOL", "hf-daily-paper-pubmed"),
        "email": os.getenv("NCBI_EMAIL", "anonymous@example.local"),
    }
    api_key = os.getenv("NCBI_API_KEY")
    if api_key:
        params["api_key"] = api_key
    return params


def _strip_ns(tag):
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _local_name(elem):
    return _strip_ns(elem.tag) if elem is not None else ""


def _text_join(parts):
    return " ".join(p for p in parts if p and p.strip()).strip()


def _normalise_doi(value):
    """将 URL、doi: 前缀等归一为用于匹配的 DOI。"""
    doi = str(value or "").strip().casefold()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
    doi = re.sub(r"^doi:\s*", "", doi)
    return doi.strip()


def _parse_pubmed_xml_batch(xml_bytes):
    """
    解析 efetch 返回的 PubMed XML（可能含多篇 PubmedArticle），
    返回 list[dict]: {pmid, title, abstract, authors: [{name}], published_at}
    """
    root = ET.fromstring(xml_bytes)
    results = []

    for article in root:
        if _local_name(article) != "PubmedArticle":
            continue

        pmid = None
        title = ""
        abstract_parts = []
        authors_out = []
        published_at = ""
        publication_date_source = ""
        doi = ""
        journal_title = ""
        journal_abbrev = ""
        journal_issns = []

        medline = None
        pubmed_data = None
        for child in article:
            ln = _local_name(child)
            if ln == "MedlineCitation":
                medline = child
            elif ln == "PubmedData":
                pubmed_data = child

        article_date = ""
        issue_date = ""
        if medline is not None:
            for mc in medline:
                ln = _local_name(mc)
                if ln == "PMID":
                    pmid = (mc.text or "").strip()
                elif ln == "Article":
                    for ac in mc:
                        aln = _local_name(ac)
                        if aln == "ArticleTitle":
                            title = "".join(ac.itertext()).strip()
                        elif aln == "Abstract":
                            for ab in ac:
                                if _local_name(ab) == "AbstractText":
                                    label = ab.attrib.get("Label")
                                    chunk = "".join(ab.itertext()).strip()
                                    if chunk:
                                        if label:
                                            abstract_parts.append(f"{label}: {chunk}")
                                        else:
                                            abstract_parts.append(chunk)
                        elif aln == "AuthorList":
                            for auth in ac:
                                if _local_name(auth) != "Author":
                                    continue
                                collective = None
                                last = fore = initials = ""
                                for ael in auth:
                                    an = _local_name(ael)
                                    if an == "CollectiveName":
                                        collective = (ael.text or "").strip()
                                    elif an == "LastName":
                                        last = (ael.text or "").strip()
                                    elif an == "ForeName":
                                        fore = (ael.text or "").strip()
                                    elif an == "Initials":
                                        initials = (ael.text or "").strip()
                                if collective:
                                    name = collective
                                else:
                                    name = _text_join([fore or initials, last])
                                if name:
                                    authors_out.append({"name": name})

        # 论文发表日期与 PubMed 收录/索引日期是不同概念。前者应优先展示；后者
        # 仅在 XML 未提供论文实际日期时作为明确标记的回退值。
        def parse_pub_date_elem(elem):
            if elem is None:
                return ""
            year = month = day = ""
            for el in elem:
                n = _local_name(el)
                if n == "Year":
                    year = (el.text or "").strip()
                elif n == "Month":
                    t = (el.text or "").strip()
                    month = t
                elif n == "Day":
                    day = (el.text or "").strip()
            if not year:
                return ""
            # 月份可能是数字或 JAN/FEB
            month_norm = month
            if month and not month.isdigit():
                mmap = {
                    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04",
                    "MAY": "05", "JUN": "06", "JUL": "07", "AUG": "08",
                    "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
                }
                month_norm = mmap.get(month[:3].upper(), "01")
            elif month.isdigit():
                month_norm = month.zfill(2)
            else:
                month_norm = ""
            day_norm = day.zfill(2) if day.isdigit() else ""
            try:
                if month_norm and day_norm:
                    datetime.date(int(year), int(month_norm), int(day_norm))
                    return f"{year}-{month_norm}-{day_norm}"
                if month_norm:
                    datetime.date(int(year), int(month_norm), 1)
                    return f"{year}-{month_norm}"
                return year
            except ValueError:
                return year

        indexed_at = ""
        if pubmed_data is not None:
            for pd in pubmed_data:
                if _local_name(pd) == "ArticleIdList":
                    for article_id in pd:
                        if article_id.attrib.get("IdType", "").casefold() == "doi":
                            doi = _normalise_doi(article_id.text)
                elif _local_name(pd) == "History":
                    for hp in pd:
                        if _local_name(hp) != "PubMedPubDate":
                            continue
                        status = hp.attrib.get("PubStatus", "")
                        if status in ("pubmed", "medline", "entrez"):
                            indexed_at = parse_pub_date_elem(hp)
                            if indexed_at:
                                break

        if medline is not None:
            for mc in medline:
                if _local_name(mc) != "Article":
                    continue
                for ac in mc:
                    if _local_name(ac) != "Journal":
                        continue
                    for jc in ac:
                        jln = _local_name(jc)
                        if jln == "ISSN":
                            issn_val = (jc.text or "").strip()
                            if issn_val:
                                journal_issns.append(issn_val)
                        elif jln == "Title":
                            journal_title = "".join(jc.itertext()).strip() or journal_title
                        elif jln == "ISOAbbreviation":
                            journal_abbrev = (jc.text or "").strip() or journal_abbrev

        if medline is not None:
            for mc in medline:
                if _local_name(mc) != "Article":
                    continue
                for ac in mc:
                    aln = _local_name(ac)
                    if aln == "ArticleDate":
                        article_date = parse_pub_date_elem(ac) or article_date
                    elif aln == "Journal":
                        for jc in ac:
                            if _local_name(jc) == "JournalIssue":
                                for ji in jc:
                                    if _local_name(ji) == "PubDate":
                                        issue_date = parse_pub_date_elem(ji)
                                        if issue_date:
                                            break

        if article_date:
            published_at = article_date
            publication_date_source = "article"
        elif issue_date:
            published_at = issue_date
            publication_date_source = "journal_issue"

        if not published_at and indexed_at:
            published_at = indexed_at
            publication_date_source = "pubmed_indexed_fallback"

        abstract = "\n".join(abstract_parts).strip()

        if not pmid:
            continue

        journal_name = journal_title or journal_abbrev
        if not filter_by_journal(
            journal_names=[journal_title, journal_abbrev],
            issns=journal_issns,
        ):
            logger.debug(
                "PubMed 期刊过滤丢弃 PMID=%s, journal=%r, abbrev=%r, issns=%r",
                pmid,
                journal_title,
                journal_abbrev,
                journal_issns,
            )
            continue

        results.append(
            {
                "pmid": pmid,
                "doi": doi,
                "title": title,
                "abstract": abstract,
                "authors": authors_out,
                "published_at": published_at,
                "publication_date_source": publication_date_source,
                "journal": journal_name,
                "issns": journal_issns,
            }
        )

    return results


def _esearch_pubmed(session, date_str, retmax=10000):
    """按日期 + 标题/摘要关键词检索 PubMed；retmax 默认 10000。"""
    keyword_query = " OR ".join(
        [f'"{term}"[Title/Abstract]' for term in iter_topic_terms()]
        + [EEG_ECG_PUBMED_QUERY, PUBMED_MENTAL_HEALTH_QUERY]
    )
    term = f'"{date_str}"[dp] AND ({keyword_query})'
    url = f"{EUTILS_BASE}/esearch.fcgi"
    params = {
        **_ncbi_common_params(),
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retmax": str(retmax),
    }
    r = _ncbi_post(session, url, params, timeout=120, label="esearch")
    r.raise_for_status()
    try:
        data = r.json()
    except ValueError as e:
        raise requests.RequestException(f"无法解析 esearch JSON: {e}") from e
    idlist = data.get("esearchresult", {}).get("idlist") or []
    return idlist


def _efetch_pubmed_xml_single(session, pmids_chunk):
    """单次 efetch（一批 PMID）；使用 POST 避免 id 列表过长。"""
    url = f"{EUTILS_BASE}/efetch.fcgi"
    params = {
        **_ncbi_common_params(),
        "db": "pubmed",
        "id": ",".join(pmids_chunk),
        "retmode": "xml",
    }
    r = _ncbi_post(session, url, params, timeout=180, label="efetch")
    r.raise_for_status()
    return r.content


def _efetch_pubmed_parsed(session, pmids):
    """对大量 PMID 分批 efetch 并解析合并（与 retmax 增大配套）。"""
    if not pmids:
        return []
    chunk_size = int(os.getenv("NCBI_EFETCH_BATCH_SIZE", "250"))
    inter = float(os.getenv("NCBI_INTER_REQUEST_DELAY_SEC", "0.35"))
    out = []
    for i in range(0, len(pmids), chunk_size):
        chunk = pmids[i : i + chunk_size]
        xml_bytes = _efetch_pubmed_xml_single(session, chunk)
        out.extend(_parse_pubmed_xml_batch(xml_bytes))
        if i + chunk_size < len(pmids) and inter > 0:
            time.sleep(inter)
    return out


def _strip_crossref_abstract(raw):
    """去除 Crossref 摘要中的 JATS/XML 标签，并做 HTML 实体反转义。"""
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", "", str(raw))
    return html.unescape(text).strip()


def _crossref_query_params(query_text):
    """
    构建 Crossref 检索参数。

    Crossref ``/works`` 不支持 ``query.abstract``；使用该字段会返回
    ``400 field-query-not-available``。这里使用官方支持的
    ``query.bibliographic``，再由期刊白名单和本地关键词预筛保证领域相关性。
    """
    return {"query.bibliographic": query_text}


def _crossref_published_date(item, fallback):
    """优先保留 Crossref 提供的实际发表日期。"""
    for key in ("published-online", "published-print", "published", "issued"):
        date_parts = ((item.get(key) or {}).get("date-parts") or [[]])[0]
        if date_parts:
            year, *rest = date_parts
            month = rest[0] if rest else 1
            day = rest[1] if len(rest) > 1 else 1
            try:
                return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
            except (TypeError, ValueError):
                continue
    return fallback


def _fetch_crossref(session, date_str, retmax=80):
    """
    从 Crossref REST API 拉取指定发表日、含摘要的文献，映射为与 PubMed 一致的结构，并标记 source=Crossref。
    retmax 在此作为 rows 上限，最大 100，避免单次请求过大。
    失败时记录 warning 并返回空列表，不向上抛出以免中断主流程。
    """
    try:
        out = []
        seen_dois = set()
        filter_str = f"from-pub-date:{date_str},until-pub-date:{date_str},has-abstract:true"
        per_track_rows = max(1, min(100, ceil(int(retmax) / len(CROSSREF_TRACK_QUERIES))))
        track_queries = list(CROSSREF_TRACK_QUERIES.items())
        crossref_delay = float(os.getenv("CROSSREF_INTER_REQUEST_DELAY_SEC", "1.0"))
        for index, (track, query_text) in enumerate(track_queries):
            params = {
                **_crossref_query_params(query_text),
                "filter": filter_str,
                "rows": per_track_rows,
                "mailto": os.getenv("CROSSREF_MAILTO", "zhugamen@gmail.com"),
            }
            r = _api_get(session, CROSSREF_WORKS_URL, params=params, timeout=90, label=f"Crossref:{track}")
            r.raise_for_status()
            items = ((r.json().get("message") or {}).get("items") or [])
            logger.info("Crossref %s 查询返回 %d 条", track, len(items))
            for item in items:
                doi = (item.get("DOI") or "").strip()
                if not doi or doi.casefold() in seen_dois:
                    continue
                seen_dois.add(doi.casefold())
                titles = item.get("title") or []
                title = (titles[0] if titles else "").strip()
                container_titles = item.get("container-title") or []
                journal_name = (container_titles[0] if container_titles else "").strip()
                if not journal_name:
                    journal_name = ((item.get("short-container-title") or [""])[0] or "").strip()
                item_issns = item.get("ISSN") or []
                if isinstance(item_issns, str):
                    item_issns = [item_issns]
                if not filter_by_journal(journal_name=journal_name, issns=item_issns):
                    continue
                raw_abs = item.get("abstract")
                if isinstance(raw_abs, list):
                    raw_abs = " ".join(str(x) for x in raw_abs)
                summary = _strip_crossref_abstract(raw_abs)
                authors_out = [
                    {"name": f"{author.get('given', '') or ''} {author.get('family', '') or ''}".strip()}
                    for author in item.get("author") or []
                    if isinstance(author, dict)
                    and f"{author.get('given', '') or ''} {author.get('family', '') or ''}".strip()
                ]
                if not title or not summary:
                    continue
                out.append({"paper": _attach_journal_profile({
                    "id": doi,
                    "doi": _normalise_doi(doi),
                    "title": title,
                    "summary": summary,
                    "authors": authors_out or [{"name": "Unknown"}],
                    "publishedAt": _crossref_published_date(item, date_str),
                    "publicationDateSource": "crossref_published",
                    "source": "Crossref",
                    "sources": ["Crossref"],
                    "journal": journal_name,
                    "issns": item_issns,
                })})
            if index + 1 < len(track_queries) and crossref_delay > 0:
                time.sleep(crossref_delay)
        return out
    except (
        requests.exceptions.RequestException,
        ValueError,
    ) as e:
        logger.warning("Crossref 数据拉取失败，将跳过: %s", e)
        return []


def _validate_and_save_papers(papers, output_file, label):
    """校验论文字段并写入 JSON 文件。"""
    valid_papers = []
    skipped_papers = []

    for paper in papers:
        paper_info = paper.get("paper", {})
        paper_id = paper_info.get("id", "unknown")

        is_valid = True
        reasons = []

        if not paper_info:
            is_valid = False
            reasons.append("缺少paper字段")
        else:
            if not paper_info.get("title"):
                is_valid = False
                reasons.append("缺少标题")
            if not paper_info.get("summary"):
                is_valid = False
                reasons.append("缺少摘要")
            if not paper_info.get("id"):
                is_valid = False
                reasons.append("缺少ID")
            if not paper_info.get("authors"):
                is_valid = False
                reasons.append("缺少作者信息")
            if not paper_info.get("publishedAt"):
                is_valid = False
                reasons.append("缺少发布时间")

        if is_valid:
            valid_papers.append(paper)
            logger.debug(f"接受论文: {paper_id}")
        else:
            skipped_papers.append({"id": paper_id, "reasons": reasons})
            logger.warning(f"跳过论文 {paper_id}: {', '.join(reasons)}")

    logger.info(f"{label} 原始数据: {len(papers)}篇")
    logger.info(f"{label} 有效论文: {len(valid_papers)}篇")
    logger.info(f"{label} 跳过论文: {len(skipped_papers)}篇")

    if skipped_papers:
        logger.info("跳过的论文详情:")
        for skip_info in skipped_papers:
            logger.info(f"  ID: {skip_info['id']}, 原因: {', '.join(skip_info['reasons'])}")

    if not valid_papers:
        return []

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(valid_papers, f, ensure_ascii=False, indent=2)
    logger.info(f"成功保存 {len(valid_papers)} 篇有效论文数据到 {output_file}")
    return valid_papers


def _local_prefilter_enabled():
    """允许在紧急回溯或 A/B 对比时以环境变量关闭预筛。"""
    return os.getenv("LOCAL_KEYWORD_PREFILTER_ENABLED", "true").strip().lower() not in {
        "0", "false", "no", "off"
    }


def _apply_local_keyword_prefilter(papers):
    """在调用 DeepSeek 前，筛去未满足关键词组合的候选记录。"""
    if not _local_prefilter_enabled():
        logger.info("本地关键词预筛已通过 LOCAL_KEYWORD_PREFILTER_ENABLED 关闭")
        return papers

    accepted = []
    rejected = 0
    reasons = {}
    for item in papers:
        paper = item.get("paper", {})
        decision = local_prefilter_decision(
            paper.get("title", ""),
            paper.get("summary", ""),
        )
        if decision["accepted"]:
            # 保留可追溯信息；后续 DeepSeek 仍独立做语义相关性判断。
            paper["local_prefilter_groups"] = decision["groups"]
            paper["local_prefilter_reason"] = decision["reason"]
            accepted.append(item)
        else:
            rejected += 1
            reason = decision["reason"]
            reasons[reason] = reasons.get(reason, 0) + 1

    logger.info(
        "本地关键词预筛：输入 %d 篇，保留 %d 篇，剔除 %d 篇（%s）",
        len(papers),
        len(accepted),
        rejected,
        ", ".join(f"{key}={value}" for key, value in sorted(reasons.items())) or "无",
    )
    return accepted


def _attach_journal_profile(paper):
    """把可展示的期刊优先级资料随候选记录传到 Newsletter 阶段。"""
    paper["journal_metrics"] = get_journal_profile(
        journal_name=paper.get("journal"),
        issns=paper.get("issns"),
    )
    return paper


def download_papers_for_date(date_str, retmax=10000):
    """
    从 PubMed 与 Crossref 下载指定日期的论文元数据（已按目标期刊过滤）。
    返回 list[dict] 或空列表。
    """
    retmax = int(retmax)
    if retmax < 1:
        retmax = 1
    if retmax > 100000:
        logger.warning("retmax 超过 100000，已截断为 100000（贴近 NCBI esearch 实务上限）")
        retmax = 100000

    target_date = date_str
    logger.info(
        f"正在获取 {target_date} 的论文数据：PubMed（retmax={retmax}）+ Crossref"
    )

    pubmed_papers = []
    crossref_papers = []
    inter_delay = float(os.getenv("NCBI_INTER_REQUEST_DELAY_SEC", "0.35"))
    crossref_rows = int(os.getenv("CROSSREF_ROWS", "80"))
    session = _make_api_session()
    try:
        try:
            pmids = _esearch_pubmed(session, target_date, retmax=retmax)
            logger.info(f"PubMed esearch 返回 PMID 数量: {len(pmids)}")
            if pmids:
                if inter_delay > 0:
                    time.sleep(inter_delay)
                parsed = _efetch_pubmed_parsed(session, pmids)
                by_pmid = {p["pmid"]: p for p in parsed if p.get("pmid")}
                for pmid in pmids:
                    rec = by_pmid.get(pmid)
                    if not rec:
                        continue
                    pubmed_papers.append(
                        {
                            "paper": _attach_journal_profile({
                                "id": rec["pmid"],
                                "pmid": rec["pmid"],
                                "doi": rec.get("doi", ""),
                                "title": rec["title"],
                                "summary": rec["abstract"],
                                "authors": rec["authors"],
                                "publishedAt": rec["published_at"] or target_date,
                                "publicationDateSource": rec.get("publication_date_source", ""),
                                "source": "PubMed",
                                "sources": ["PubMed"],
                                "journal": rec.get("journal", ""),
                                "issns": rec.get("issns", []),
                                })
                        }
                    )
        except requests.RequestException as e:
            logger.error(f"PubMed 请求失败（将仅使用 Crossref 若可用）: {e}")
        except ET.ParseError as e:
            logger.error(f"解析 PubMed XML 失败: {e}")

        crossref_papers = _fetch_crossref(session, target_date, retmax=crossref_rows)
        logger.info(f"Crossref 返回条目数量: {len(crossref_papers)}")
    finally:
        session.close()

    papers = pubmed_papers + crossref_papers
    if not papers:
        logger.warning(f"{target_date} PubMed 与 Crossref 均无可用论文数据")
        return []

    logger.info(
        f"{target_date} 合并后原始条目: PubMed {len(pubmed_papers)} 篇 + Crossref {len(crossref_papers)} 篇 = {len(papers)} 篇"
    )
    return _apply_local_keyword_prefilter(_deduplicate_papers(papers, f"{target_date} 跨来源"))


def _normalised_title_key(title):
    """为跨 PubMed/Crossref 去重生成稳健的标题键。

    同一 DOI 在两个来源的标题经常只相差句末标点、连字符或大小写；两边的
    记录 ID 又分别是 PMID 和 DOI。因此在保留原始标题用于展示的同时，以
    Unicode 规范化后的字母数字标题作为第二重去重键。
    """
    text = unicodedata.normalize("NFKC", str(title or "")).casefold()
    return re.sub(r"[^\w]+", "", text, flags=re.UNICODE)


def _normalised_issn(value):
    return re.sub(r"[^0-9x]", "", str(value or "").casefold())


def _first_author_key(authors):
    if not authors:
        return ""
    value = authors[0]
    name = value.get("name", "") if isinstance(value, dict) else str(value)
    return _normalised_title_key(name.split()[-1] if name else "")


def _bibliographic_key(metadata):
    """无 DOI 时的保守书目信息键，防止仅因标题相同误合并。"""
    title = _normalised_title_key(metadata.get("title"))
    author = _first_author_key(metadata.get("authors", []))
    journal = _normalised_title_key(metadata.get("journal"))
    year = str(metadata.get("publishedAt", ""))[:4]
    issns = sorted(_normalised_issn(value) for value in metadata.get("issns", []) if value)
    if not title or not year or not (author or journal or issns):
        return ""
    return "|".join((title, author, journal, year, ",".join(issns)))


def _merge_record_provenance(existing, duplicate):
    """将同一论文的 DOI、PMID 和来源合并到一条可追溯记录。"""
    target = existing.get("paper", {})
    incoming = duplicate.get("paper", {})
    target_sources = target.setdefault("sources", [target.get("source", "")])
    for source in incoming.get("sources", [incoming.get("source", "")]):
        if source and source not in target_sources:
            target_sources.append(source)
    for field in ("doi", "pmid"):
        if not target.get(field) and incoming.get(field):
            target[field] = incoming[field]
    if target.get("doi"):
        target["id"] = target["doi"]


def _deduplicate_papers(papers, stage):
    """按 DOI、保守书目信息和高阈值标题相似度合并候选论文。"""
    retained = []
    by_doi = {}
    by_bibliographic = {}
    duplicate_counts = {"doi": 0, "bibliographic": 0, "title_similarity": 0}

    for candidate in papers:
        metadata = candidate.get("paper", {})
        doi = _normalise_doi(metadata.get("doi"))
        biblio = _bibliographic_key(metadata)
        existing = by_doi.get(doi) if doi else None
        reason = "doi" if existing else ""
        if existing is None and biblio:
            existing = by_bibliographic.get(biblio)
            reason = "bibliographic" if existing else ""

        if existing is None:
            title = _normalised_title_key(metadata.get("title"))
            author = _first_author_key(metadata.get("authors", []))
            journal = _normalised_title_key(metadata.get("journal"))
            year = str(metadata.get("publishedAt", ""))[:4]
            for prior in retained:
                old = prior.get("paper", {})
                if (
                    author
                    and author == _first_author_key(old.get("authors", []))
                    and journal
                    and journal == _normalised_title_key(old.get("journal"))
                    and year
                    and year == str(old.get("publishedAt", ""))[:4]
                    and SequenceMatcher(None, title, _normalised_title_key(old.get("title"))).ratio() >= 0.985
                ):
                    existing = prior
                    reason = "title_similarity"
                    break

        if existing is not None:
            duplicate_counts[reason] += 1
            _merge_record_provenance(existing, candidate)
            continue

        retained.append(candidate)
        if doi:
            by_doi[doi] = candidate
        if biblio:
            by_bibliographic[biblio] = candidate

    duplicates = sum(duplicate_counts.values())
    if duplicates:
        logger.info(
            "%s 去重：输入 %d 篇，合并 %d 篇，保留 %d 篇（DOI=%d，书目信息=%d，标题相似=%d）",
            stage, len(papers), duplicates, len(retained), duplicate_counts["doi"],
            duplicate_counts["bibliographic"], duplicate_counts["title_similarity"],
        )
    return retained


def download_papers(start_date=None, end_date=None, date_str=None, retmax=10000):
    """
    下载论文元数据并保存为 JSON。

    - 未指定任何日期时：自动获取上周一至上周日，合并为周报文件。
    - 指定 start_date / end_date：下载该区间内每天的数据并合并。
    - 指定 date_str：兼容单日下载（写入 {date}.json）。
    """
    target_start = start_date
    target_end = end_date

    try:
        if date_str:
            papers = download_papers_for_date(date_str, retmax=retmax)
            if not papers:
                return {"status": "no_data", "date": date_str}
            output_file = os.path.join("Paper_metadata_download", f"{date_str}.json")
            valid = _validate_and_save_papers(papers, output_file, date_str)
            if not valid:
                return {"status": "no_data", "date": date_str}
            return {"status": "success", "date": date_str, "count": len(valid)}

        if target_start is None and target_end is None:
            target_start, target_end = get_last_week_range()
        elif target_start and not target_end:
            target_end = target_start
        elif target_end and not target_start:
            target_start = target_end

        logger.info(f"周报模式：下载 {target_start} 至 {target_end} 的论文数据")
        merged = []
        for day in iter_date_range(target_start, target_end):
            day_papers = download_papers_for_date(day, retmax=retmax)
            for paper in day_papers:
                merged.append(paper)

        merged = _deduplicate_papers(merged, "周报候选")

        basename = weekly_basename(target_start, target_end)
        output_file = os.path.join("Paper_metadata_download", f"{basename}_weekly.json")

        if not merged:
            logger.warning(f"{target_start} 至 {target_end} 无可用论文数据")
            return {
                "status": "no_data",
                "start_date": target_start,
                "end_date": target_end,
            }

        valid = _validate_and_save_papers(merged, output_file, basename)
        if not valid:
            return {
                "status": "no_data",
                "start_date": target_start,
                "end_date": target_end,
            }

        return {
            "status": "success",
            "start_date": target_start,
            "end_date": target_end,
            "count": len(valid),
            "file": output_file,
        }

    except Exception as e:
        logger.error(f"下载论文数据时发生错误: {str(e)}")
        return {
            "status": "error",
            "date": date_str,
            "start_date": target_start,
            "end_date": target_end,
            "message": str(e),
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 PubMed 与 Crossref 下载论文元数据（默认周报模式）")
    parser.add_argument("--date", type=str, help="单日下载 (YYYY-MM-DD)，写入 {date}.json")
    parser.add_argument("--start-date", type=str, help="周报起始日期 (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="周报结束日期 (YYYY-MM-DD)")
    parser.add_argument(
        "--retmax",
        type=int,
        default=10000,
        help="esearch 返回的最大 PMID 数量（默认 10000）",
    )
    args = parser.parse_args()

    result = download_papers(
        start_date=args.start_date,
        end_date=args.end_date,
        date_str=args.date,
        retmax=args.retmax,
    )
    logger.info(f"下载结果: {result}")
    if result["status"] == "error":
        exit(1)
    exit(0)
