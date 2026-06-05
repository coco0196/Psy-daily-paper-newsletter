import os
import re
import json
import html
import time
import datetime
import requests
import argparse
import xml.etree.ElementTree as ET
from requests.adapters import HTTPAdapter
from urllib3.exceptions import ProtocolError
from urllib3.util.retry import Retry
from utils import setup_logger, get_last_week_range, weekly_basename, iter_date_range
from journal_registry import filter_by_journal

# 设置日志记录器
logger = setup_logger()

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CROSSREF_WORKS_URL = "https://api.crossref.org/works"
CROSSREF_USER_AGENT = "hf-daily-paper-bot/1.0 (mailto:zhugamen@gmail.com)"

# 垂直领域：标题/摘要中需匹配的关键词（OR 组合，与当日 [dp] 联检）
KEYWORDS = [
    "Cross-culture",
    "Impression",
    "Emotion",
    "Face",
    "Voice",
    "Feeling",
    "Mood",
    "Social Cognition",
    "Emotion Perception",
    "Emotion Expression",
    "Emotion Experience",
    "Facial Expression",
    "Vocal Expression",
    "Interpersonal Relationship",
    "Personality",
    "anger",
    "fear",
    "happiness",
    "surprise",
    "disgust",
    "sadness",
    "anxiety",
    "depression"
]


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

        # 优先从 PubmedData / History 取电子化发表日期，其次 MedlineCitation 内日期
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
                month_norm = "01"
            day_norm = day.zfill(2) if day.isdigit() else "01"
            try:
                datetime.date(int(year), int(month_norm), int(day_norm))
                return f"{year}-{month_norm}-{day_norm}"
            except ValueError:
                return year

        if pubmed_data is not None:
            for pd in pubmed_data:
                if _local_name(pd) != "History":
                    continue
                for hp in pd:
                    if _local_name(hp) != "PubMedPubDate":
                        continue
                    status = hp.attrib.get("PubStatus", "")
                    if status in ("pubmed", "medline", "entrez"):
                        d = parse_pub_date_elem(hp)
                        if d:
                            published_at = d
                            break
                if published_at:
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

        if medline is not None and not published_at:
            for mc in medline:
                if _local_name(mc) != "Article":
                    continue
                for ac in mc:
                    aln = _local_name(ac)
                    if aln == "ArticleDate":
                        published_at = parse_pub_date_elem(ac) or published_at
                    elif aln == "Journal":
                        for jc in ac:
                            if _local_name(jc) == "JournalIssue":
                                for ji in jc:
                                    if _local_name(ji) == "PubDate":
                                        published_at = parse_pub_date_elem(ji) or published_at

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
                "title": title,
                "abstract": abstract,
                "authors": authors_out,
                "published_at": published_at,
                "journal": journal_name,
                "issns": journal_issns,
            }
        )

    return results


def _esearch_pubmed(session, date_str, retmax=10000):
    """按日期 + 标题/摘要关键词检索 PubMed；retmax 默认 10000。"""
    keyword_query = " OR ".join([f'"{kw}"[Title/Abstract]' for kw in KEYWORDS])
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


def _crossref_query_params():
    """
    构建 Crossref 检索参数：截断关键词并用 query.abstract OR 组合，
    避免将全部关键词 AND 进 query 导致空结果或无效查询。
    """
    max_kw = int(os.getenv("CROSSREF_QUERY_KEYWORDS_MAX", "10"))
    max_kw = max(1, min(max_kw, len(KEYWORDS)))
    kw_subset = KEYWORDS[:max_kw]
    abstract_query = " OR ".join(kw_subset)
    return {"query.abstract": abstract_query}


def _fetch_crossref(session, date_str, retmax=80):
    """
    从 Crossref REST API 拉取指定 index-date 起入库、含摘要的文献，映射为与 PubMed 一致的结构，并标记 source=Crossref。
    retmax 在此作为 rows 上限，最大 100，避免单次请求过大。
    失败时记录 warning 并返回空列表，不向上抛出以免中断主流程。
    """
    try:
        filter_str = f"from-index-date:{date_str},has-abstract:true"
        params = {
            **_crossref_query_params(),
            "filter": filter_str,
            "rows": min(int(retmax), 100),
            "mailto": os.getenv("CROSSREF_MAILTO", "zhugamen@gmail.com"),
        }
        r = _api_get(
            session,
            CROSSREF_WORKS_URL,
            params=params,
            timeout=90,
            label="Crossref",
        )
        r.raise_for_status()
        payload = r.json()
        items = (payload.get("message") or {}).get("items") or []
        out = []
        for item in items:
            doi = (item.get("DOI") or "").strip()
            titles = item.get("title") or []
            title = (titles[0] if titles else "").strip()
            container_titles = item.get("container-title") or []
            journal_name = (container_titles[0] if container_titles else "").strip()
            if not journal_name:
                short_titles = item.get("short-container-title") or []
                journal_name = (short_titles[0] if short_titles else "").strip()
            item_issns = item.get("ISSN") or []
            if isinstance(item_issns, str):
                item_issns = [item_issns]
            if not filter_by_journal(journal_name=journal_name, issns=item_issns):
                logger.debug(
                    "Crossref 期刊过滤丢弃 DOI=%s, journal=%r, issns=%r",
                    doi,
                    journal_name,
                    item_issns,
                )
                continue
            raw_abs = item.get("abstract")
            if raw_abs is None:
                continue
            if isinstance(raw_abs, list):
                raw_abs = " ".join(str(x) for x in raw_abs)
            summary = _strip_crossref_abstract(raw_abs)
            authors_out = []
            for a in item.get("author") or []:
                if not isinstance(a, dict):
                    continue
                name = f"{a.get('given', '') or ''} {a.get('family', '') or ''}".strip()
                if name:
                    authors_out.append({"name": name})
            if not doi or not title or not summary:
                continue
            if not authors_out:
                authors_out.append({"name": "Unknown"})
            out.append(
                {
                    "paper": {
                        "id": doi,
                        "title": title,
                        "summary": summary,
                        "authors": authors_out,
                        "publishedAt": date_str,
                        "source": "Crossref",
                        "journal": journal_name,
                        "issns": item_issns,
                    }
                }
            )
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
                            "paper": {
                                "id": rec["pmid"],
                                "title": rec["title"],
                                "summary": rec["abstract"],
                                "authors": rec["authors"],
                                "publishedAt": rec["published_at"] or target_date,
                                    "source": "PubMed",
                                    "journal": rec.get("journal", ""),
                                    "issns": rec.get("issns", []),
                                }
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
    return papers


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
        seen_ids = set()
        for day in iter_date_range(target_start, target_end):
            day_papers = download_papers_for_date(day, retmax=retmax)
            for paper in day_papers:
                paper_id = paper.get("paper", {}).get("id")
                if paper_id and paper_id in seen_ids:
                    continue
                if paper_id:
                    seen_ids.add(paper_id)
                merged.append(paper)

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
