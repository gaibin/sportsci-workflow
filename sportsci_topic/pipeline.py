"""Brief + records -> card. One function the command line, the tests and an AI agent all call."""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from . import card as cardmod
from .brief import Brief, FACET_KEYS, load_brief, require_valid
from .designmap import DesignChoice, choose_design
from .evidence import Evidence, build_evidence
from .feasibility import assess
from .power import SamplePlan, plan_sample
from .records import Record, dedupe, from_search_dicts, load_records
from .variants import Variant, build_variants, rank


@dataclass
class Result:
    brief: Brief
    choice: DesignChoice
    plan: SamplePlan
    evidence: Optional[Evidence]
    assessment: Dict
    variants: List[Variant]
    warnings: List[str]
    draft: Dict
    card: str
    lang: str


def _first(terms: Sequence[str], cjk: bool) -> str:
    for t in terms:
        if any("一" <= ch <= "鿿" for ch in t) == cjk:
            return t
    return ""


def search_queries(b: Brief) -> List[str]:
    """Pairwise + full queries from each facet's first English and first Chinese term."""
    qs: List[str] = []
    for cjk in (False, True):
        pick = {k: _first(b.facet(k).terms, cjk) for k in ("population", "intervention", "outcome")}
        pick = {k: v for k, v in pick.items() if v}
        keys = list(pick)
        combos = [("population", "intervention"), ("intervention", "outcome"), ("population", "outcome"), ("population", "intervention", "outcome")]
        for combo in combos:
            if all(k in pick for k in combo):
                q = " ".join(pick[k] for k in combo)
                if q not in qs:
                    qs.append(q)
    return qs


def fetch_records(b: Brief, n: int = 25, year_from: int = 0):
    """Search through sportsci-refs when it is installed. Returns (records, retrieval_log, errors)."""
    try:
        from sportsci_refs.search import search  # type: ignore
    except ImportError as e:  # pragma: no cover - depends on the environment
        raise RuntimeError("--fetch needs the sportsci-refs package (pip install sportsci-refs); "
                           "or export records from CNKI / PubMed / Zotero and pass them with --records") from e
    recs: List[Record] = []
    log: List[Dict] = []
    errs: List[str] = []
    for q in search_queries(b):
        res = search(q, n=n, year_from=year_from)
        got = from_search_dicts(res["records"])
        recs += got
        log.append({"source": "sportsci-refs", "query": q, "n": len(got)})
        errs += [f"{k}: {v}" for k, v in res.get("errors", {}).items()]
    return dedupe(recs), log, errs


def run(brief_path: str | Path, record_paths: Sequence[str | Path] = (), *, fetch: bool = False, fetch_n: int = 25,
        year_from: int = 0, this_year: Optional[int] = None, lang: Optional[str] = None, two_axis: bool = False,
        today: Optional[_dt.date] = None) -> Result:
    b = load_brief(brief_path)
    warnings = require_valid(b)
    lang = lang or b.language
    recs: List[Record] = []
    log: List[Dict] = []
    for p in record_paths:
        got = load_records([p])
        recs += got
        log.append({"source": Path(p).name, "query": "", "n": len(got)})
    if fetch:
        got, flog, errs = fetch_records(b, fetch_n, year_from)
        recs += got
        log += flog
        warnings += [f"search error — {e}" for e in errs]
    recs = dedupe(recs)

    choice = choose_design(b, lang)
    plan = plan_sample(b, choice, lang)
    ev = build_evidence(recs, b, this_year=this_year, retrieval=log, lang=lang) if recs else None
    variants = rank(build_variants(recs, b, this_year=this_year, two_axis=two_axis)) if recs and b.variants else []
    assessment = assess(b, choice, plan, ev, lang)
    draft = cardmod.build_design_draft(b, choice)
    md = cardmod.render_card(b, choice, plan, ev, assessment, variants, warnings, lang, today)
    return Result(b, choice, plan, ev, assessment, variants, warnings, draft, md, lang)
