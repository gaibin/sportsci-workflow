"""Candidate literature search across Crossref, Europe PMC and OpenAlex.

The output is a CANDIDATE list for a person to screen. Which papers are cited is a human decision; nothing here
invents or completes a reference from memory. Known data-quality traps handled in code:
  1. Crossref returns peer-review records ("Review for <title>", DOI .../review3, type=peer-review) -> removed
  2. Europe PMC titles carry <i>/<sup> HTML -> cleaned
  3. Crossref relevance ranking is weak -> use all three sources and screen
  4. Chinese keywords only work on Crossref / OpenAlex
"""
from __future__ import annotations

import html
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .config import load_config
from .net import HTTPFailure, get_json

JUNK_TYPES = {"peer-review", "component", "grant", "dataset", "standard"}


def clean_text(t) -> str:
    t = re.sub(r"<[^>]+>", "", t or "")
    return " ".join(html.unescape(t).split())


def _year(v) -> int:
    m = re.search(r"(19|20)\d{2}", str(v or ""))
    return int(m.group(0)) if m else 0


def src_crossref(q: str, n: int) -> List[Dict]:
    j = get_json("https://api.crossref.org/works?query.bibliographic=" + urllib.parse.quote(q) +
                 f"&rows={n}&sort=relevance&select=DOI,title,author,issued,container-title,is-referenced-by-count,type")
    out = []
    for it in (j.get("message", {}) or {}).get("items", []):
        au = (it.get("author") or [{}])[0]
        try:
            yr = it["issued"]["date-parts"][0][0] or 0
        except (KeyError, IndexError, TypeError):
            yr = 0
        out.append(dict(doi=(it.get("DOI") or "").lower(), title=clean_text((it.get("title") or [""])[0]),
                        author=clean_text(f"{au.get('family') or au.get('name') or ''} {au.get('given') or ''}") or "—", year=yr,
                        journal=clean_text((it.get("container-title") or [""])[0]), cites=it.get("is-referenced-by-count") or 0,
                        type=it.get("type") or "", source="Crossref"))
    return out


def src_europepmc(q: str, n: int) -> List[Dict]:
    j = get_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=" + urllib.parse.quote(q) + f"&format=json&pageSize={n}&resultType=core")
    out = []
    for it in (j.get("resultList", {}) or {}).get("result", []):
        out.append(dict(doi=(it.get("doi") or "").lower(), title=clean_text(it.get("title")), author=clean_text(it.get("authorString")) or "—",
                        year=_year(it.get("pubYear")), journal=clean_text(it.get("journalInfo", {}).get("journal", {}).get("title") or it.get("journalTitle")),
                        cites=it.get("citedByCount") or 0, type=it.get("pubType") or "", source="EuropePMC", pmid=it.get("pmid") or ""))
    return out


def src_openalex(q: str, n: int) -> List[Dict]:
    mail = load_config().contact_email
    j = get_json("https://api.openalex.org/works?search=" + urllib.parse.quote(q) + f"&per-page={n}" + (f"&mailto={urllib.parse.quote(mail)}" if mail else ""))
    out = []
    for it in j.get("results") or []:
        au = (it.get("authorships") or [{}])[0].get("author", {})
        pl = (it.get("primary_location") or {}).get("source") or {}
        out.append(dict(doi=(it.get("doi") or "").replace("https://doi.org/", "").lower(), title=clean_text(it.get("title")),
                        author=clean_text(au.get("display_name")) or "—", year=it.get("publication_year") or 0, journal=clean_text(pl.get("display_name")),
                        cites=it.get("cited_by_count") or 0, type=it.get("type") or "", source="OpenAlex"))
    return out


SOURCES: Dict[str, Callable[[str, int], List[Dict]]] = {"crossref": src_crossref, "europepmc": src_europepmc, "openalex": src_openalex}


def junk_reason(r: Dict) -> str:
    if not r["title"]:
        return "空题名 / empty title"
    if r["title"].lower().startswith("review for ") or "/review" in r["doi"]:
        return "同行评审记录 / peer-review record"
    if (r["type"] or "").lower().replace("_", "-") in JUNK_TYPES:
        return f"非文献类型 / not a paper ({r['type']})"
    return ""


def _key(r: Dict) -> str:
    return "doi:" + r["doi"] if r["doi"] else "ti:" + re.sub(r"[^a-z0-9一-鿿]+", "", (r["title"] or "").lower())


def merge(groups: Dict[str, List[Dict]], year_from: int = 0) -> Tuple[List[Dict], List[Tuple[Dict, str]]]:
    merged: Dict[str, Dict] = {}
    dropped: List[Tuple[Dict, str]] = []
    for s, recs in groups.items():
        for r in recs:
            why = junk_reason(r)
            if why:
                dropped.append((r, why))
                continue
            k = _key(r)
            if k not in merged:
                merged[k] = dict(r, also=[])
            else:
                merged[k]["also"].append(r["source"])
                merged[k]["cites"] = max(merged[k]["cites"], r["cites"])
    recs = [r for r in merged.values() if r["year"] >= year_from]
    recs.sort(key=lambda r: (-r["year"], -r["cites"]))
    return recs, dropped


def search(query: str, sources: Sequence[str] = ("crossref", "europepmc", "openalex"), n: int = 15, year_from: int = 0) -> Dict:
    use = [s for s in sources if s in SOURCES]
    errors: Dict[str, str] = {}

    def run(s):
        try:
            return SOURCES[s](query, n)
        except (HTTPFailure, ValueError) as e:
            errors[s] = str(e)
            return []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=max(1, len(use))) as ex:
        groups = dict(zip(use, ex.map(run, use)))
    recs, dropped = merge(groups, year_from)
    return dict(query=query, sources=use, n_raw=sum(len(g) for g in groups.values()), records=recs, dropped=dropped, errors=errors, seconds=time.time() - t0)


def write_candidates(res: Dict, path) -> Path:
    p = Path(path)
    recs, dropped = res["records"], res["dropped"]
    esc = lambda s: (s or "").replace("|", "\\|")
    L = [f"# 文献检索候选：{res['query']}", "",
         f"源：{', '.join(res['sources'])}｜原始 {res['n_raw']} 条 → 剔除 {len(dropped)} 条 → 去重后 **{len(recs)}** 条｜{res['seconds']:.1f}s", "",
         "> ⚠️ 这是**候选**，不是参考文献表。逐条人工过目（题名、摘要、是否真的支持你要写的那句话）后再决定是否入库。", ""]
    if res["errors"]:
        L += ["**检索失败的源**（结果不完整）："] + [f"- {k}: {v}" for k, v in res["errors"].items()] + [""]
    L += ["| # | 年 | 第一作者 | 题名 | 期刊 | 被引 | DOI | 命中源 |", "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(recs, 1):
        L.append(f"| {i} | {r['year'] or '—'} | {esc(r['author'])} | {esc(r['title'])} | {esc(r['journal'])} | {r['cites']} | {r['doi'] or '—'} | {'+'.join([r['source']] + r['also'])} |")
    dois = [r["doi"] for r in recs if r["doi"]]
    L += ["", f"## DOI 列表（{len(dois)} 条，可直接用于 `cli.py refs check-doi`）", "", "```"] + dois + ["```"]
    nod = [r for r in recs if not r["doi"]]
    if nod:
        L += ["", f"## 缺 DOI（{len(nod)} 条，人工补全或弃用）", ""] + [f"- [{r['year'] or '—'}] {r['title']} — {r['journal']}" for r in nod]
    if dropped:
        L += ["", f"## 已剔除的非文献条目（{len(dropped)} 条，供核对）", ""] + [f"- [{why}] {r['title'][:80]} — `{r['doi']}`" for r, why in dropped[:60]]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(L) + "\n", encoding="utf-8")
    return p
