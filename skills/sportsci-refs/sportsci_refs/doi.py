"""DOI verification against Crossref, and CSL-JSON retrieval by DOI (content negotiation on doi.org).

Status per reference:
    OK        DOI resolves and the Crossref title matches (similarity >= 0.80)
    EXISTS    DOI resolves, but no title was given to compare — it may still belong to another paper
    MISMATCH  DOI resolves to a DIFFERENT paper — the most dangerous case (a real DOI attached to the wrong reference)
    404       DOI does not exist
    NODOI     the reference has no DOI (Chinese journals often lack one: check on CNKI / Wanfang by hand)
    ERR       network problem; re-run
"""
from __future__ import annotations

import difflib
import json
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from .net import HTTPFailure, fetch, get_json


def norm_title(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", (s or "").lower())
    return " ".join(re.sub(r"[^a-z0-9一-鿿]+", " ", s).split())


def title_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm_title(a), norm_title(b)).ratio()


def clean_doi(doi: str) -> str:
    d = (doi or "").strip()
    d = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", d, flags=re.I)
    return d.rstrip(".").strip()


def check_one(ref: Dict, threshold: float = 0.80) -> Dict:
    doi = clean_doi(ref.get("doi", ""))
    base = dict(num=ref.get("num"), doi=doi, title=ref.get("title", ""))
    if not doi:
        return dict(base, status="NODOI", similarity=None, crossref_title="")
    try:
        j = get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))["message"]
    except HTTPFailure as e:
        return dict(base, status="404" if e.status == 404 else "ERR", similarity=None, crossref_title="", error=str(e))
    ct = (j.get("title") or [""])[0]
    sim = title_similarity(ref.get("title", ""), ct) if ref.get("title") else None
    status = "EXISTS" if sim is None else ("OK" if sim >= threshold else "MISMATCH")
    issued = (j.get("issued", {}).get("date-parts") or [[None]])[0][0]
    return dict(base, status=status, similarity=sim, crossref_title=ct, crossref_year=issued,
                crossref_journal=(j.get("container-title") or [""])[0], volume=j.get("volume"), issue=j.get("issue"), page=j.get("page"))


def check_dois(refs: List[Dict], workers: int = 6) -> List[Dict]:
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(check_one, refs))


def csl_by_doi(doi: str) -> Optional[Dict]:
    """CSL-JSON record for a DOI (for items not yet in Zotero, or to fill missing fields)."""
    try:
        raw = fetch("https://doi.org/" + urllib.parse.quote(clean_doi(doi)), headers={"Accept": "application/vnd.citationstyles.csl+json"})
    except HTTPFailure:
        return None
    return json.loads(raw.decode("utf-8", "replace"))


def report_md(results: List[Dict]) -> str:
    from collections import Counter
    c = Counter(r["status"] for r in results)
    L = ["# DOI 核验报告（Crossref）", "", "汇总：" + "，".join(f"{k} {v}" for k, v in sorted(c.items())), "",
         "| # | 状态 | 相似度 | DOI | 文中题名 | Crossref 题名 |", "|---|---|---|---|---|---|"]
    for r in results:
        sim = f"{r['similarity']:.2f}" if r.get("similarity") is not None else ""
        L.append(f"| {r.get('num', '')} | {r['status']} | {sim} | {r['doi']} | {(r['title'] or '')[:60]} | {(r.get('crossref_title') or '')[:60]} |")
    L += ["", "- **EXISTS**：DOI 存在，但没有题名可比对——仍可能指向别的论文，请对照 Crossref 题名人工确认。", "- **MISMATCH**：DOI 真实存在但指向另一篇论文——必须修正，这是最隐蔽的错误。", "- **404**：DOI 不存在，核对原文。",
          "- **NODOI**：中文期刊常无 DOI，请在知网/万方人工核对作者、年、卷期页。", "- 核验只说明“这篇文献存在且元数据一致”，**不说明它支持正文里那句话**——引用内容须由作者本人对照原文确认。"]
    return "\n".join(L) + "\n"
