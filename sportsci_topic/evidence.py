"""Evidence map: what the student's own record set says about the question, counted, not summarised.

Every number comes from matching the brief's search vocabulary against the records. A "gap" here is a *statement about the
record set* ("12 records mention the population and the intervention, none mentions the outcome"), never a claim about the
whole literature. The retrieval log and a coverage flag travel with every result so a thin record set cannot pass for proof.
"""
from __future__ import annotations

import datetime as _dt
import re
from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

from .brief import FACET_CODE, FACET_KEYS, Brief, Facet
from .records import Record

LOW_COVERAGE = 30          # fewer records than this: the map is a sketch, not evidence
CROWDED = 4                # recent records matching population + intervention + outcome
VERY_CROWDED = 10
GAP_MIN_PAIR = 3           # a pair needs this many records before the missing third facet is worth naming

DESIGN_PATTERNS: List[Tuple[str, str]] = [
    ("meta", r"meta-?analy|荟萃|元分析|meta分析"),
    ("review", r"systematic review|scoping review|系统综述|文献综述|综述|review"),
    ("rct", r"random|rct\b|随机"),
    ("crossover", r"cross-?over|交叉"),
    ("quasi", r"quasi|准实验"),
    ("cohort", r"cohort|longitudinal|队列|纵向"),
    ("cross_sectional", r"cross-?sectional|横断面"),
    ("survey", r"survey|questionnaire|问卷|调查"),
    ("pilot", r"pilot|预实验|预试验"),
    ("experiment", r"experiment|intervention|trial|实验|干预|训练"),
]


def term_regex(term: str) -> Optional[re.Pattern]:
    t = term.strip().lower()
    if not t:
        return None
    if re.fullmatch(r"[a-z0-9][a-z0-9 \-/+.']*", t):
        body = re.sub(r"[\s\-]+", r"[\\s-]+", re.escape(t).replace(r"\ ", " ").replace(r"\-", "-"))
        return re.compile(r"(?<![a-z0-9])" + body + r"(?:s|es)?(?![a-z0-9])")
    return re.compile(re.escape(t))


def compile_facet(f: Facet) -> List[re.Pattern]:
    return [p for p in (term_regex(t) for t in f.terms) if p is not None]


def match_facets(text: str, compiled: Dict[str, List[re.Pattern]]) -> FrozenSet[str]:
    return frozenset(k for k, pats in compiled.items() if any(p.search(text) for p in pats))


def detect_design(text: str) -> str:
    for label, pat in DESIGN_PATTERNS:
        if re.search(pat, text):
            return label
    return "other"


@dataclass
class Hit:
    record: Record
    facets: FrozenSet[str]
    design: str

    def code(self) -> str:
        return "+".join(FACET_CODE[k] for k in FACET_KEYS if k in self.facets) or "-"


@dataclass
class Evidence:
    n_records: int
    n_without_year: int
    years: Dict[int, int]
    window: Tuple[int, int]
    coverage: str                                     # "ok" | "low"
    facet_counts: Dict[str, int]
    combos_all: Dict[str, int]
    combos_recent: Dict[str, int]
    direct_all: int
    direct_recent: int
    tier: str                                         # none | few | crowded | very_crowded
    design_mix: Dict[str, int]                        # among records matching >= 2 facets
    direct_design_mix: Dict[str, int]
    nearest: List[Hit]
    gaps: List[Dict]
    retrieval: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "n_records": self.n_records, "n_without_year": self.n_without_year, "years": {str(k): v for k, v in sorted(self.years.items())},
            "window": list(self.window), "coverage": self.coverage, "facet_counts": self.facet_counts,
            "combos_all": self.combos_all, "combos_recent": self.combos_recent, "direct_all": self.direct_all,
            "direct_recent": self.direct_recent, "tier": self.tier, "design_mix": self.design_mix,
            "direct_design_mix": self.direct_design_mix,
            "nearest": [dict(h.record.to_dict(), facets=h.code(), design=h.design) for h in self.nearest],
            "gaps": self.gaps, "retrieval": self.retrieval,
        }


def _combo_key(keys: Iterable[str]) -> str:
    return "+".join(FACET_CODE[k] for k in FACET_KEYS if k in set(keys))


def classify(records: Sequence[Record], facets: Dict[str, Facet]) -> List[Hit]:
    compiled = {k: compile_facet(f) for k, f in facets.items() if k in FACET_KEYS and f.terms}
    return [Hit(r, match_facets(r.text, compiled), detect_design(r.text)) for r in records]


def core_facets(facets: Dict[str, Facet]) -> List[str]:
    return [k for k in ("population", "intervention", "outcome") if facets.get(k) and facets[k].terms]


def build_evidence(records: Sequence[Record], b: Brief, *, this_year: Optional[int] = None, recent_years: int = 5,
                   retrieval: Optional[List[Dict]] = None, lang: str = "zh", nearest_n: int = 10) -> Evidence:
    this_year = this_year or _dt.date.today().year
    lo = this_year - recent_years + 1
    hits = classify(records, b.facets)
    core = core_facets(b.facets)
    is_recent = lambda h: h.record.year >= lo

    facet_counts = {k: sum(1 for h in hits if k in h.facets) for k in FACET_KEYS if b.facets.get(k) and b.facets[k].terms}
    combos_all: Dict[str, int] = {}
    combos_recent: Dict[str, int] = {}
    for n in range(2, len(core) + 1):
        for combo in combinations(core, n):
            k = _combo_key(combo)
            sel = [h for h in hits if set(combo) <= h.facets]
            combos_all[k] = len(sel)
            combos_recent[k] = sum(1 for h in sel if is_recent(h))
    full = _combo_key(core)
    direct = [h for h in hits if set(core) <= h.facets] if len(core) == 3 else []
    direct_recent = [h for h in direct if is_recent(h)]
    n_dr = len(direct_recent)
    tier = "none" if n_dr == 0 else "few" if n_dr < CROWDED else "very_crowded" if n_dr >= VERY_CROWDED else "crowded"

    multi = [h for h in hits if len(h.facets & set(core)) >= 2]
    nearest = sorted(multi or [h for h in hits if h.facets], key=lambda h: (-len(h.facets & set(core)), -h.record.year, h.record.title))[:nearest_n]

    years = Counter(h.record.year for h in hits if h.record.year)
    cov = "ok" if len(records) >= LOW_COVERAGE else "low"
    ev = Evidence(
        n_records=len(records), n_without_year=sum(1 for h in hits if not h.record.year), years=dict(years), window=(lo, this_year),
        coverage=cov, facet_counts=facet_counts, combos_all=combos_all, combos_recent=combos_recent,
        direct_all=len(direct), direct_recent=n_dr, tier=tier,
        design_mix=dict(Counter(h.design for h in multi)), direct_design_mix=dict(Counter(h.design for h in direct)),
        nearest=nearest, gaps=[], retrieval=retrieval or [],
    )
    ev.gaps = gap_statements(ev, b, lang)
    return ev


# --------------------------------------------------------------------------------------------------------- gaps

def _label(b: Brief, k: str) -> str:
    return b.facet(k).label or k


def gap_statements(ev: Evidence, b: Brief, lang: str = "zh") -> List[Dict]:
    """Facts about the record set, each with the counts it rests on. Order: strongest first."""
    zh = lang == "zh"
    P, I, O = (_label(b, k) for k in ("population", "intervention", "outcome"))
    ca = ev.combos_all
    out: List[Dict] = []

    def add(kind: str, text: str, counts: Dict[str, int]):
        out.append({"kind": kind, "text": text, "counts": counts})

    if ev.direct_all == 0 and ca.get("P+I+O", 0) == 0 and "P+I+O" in ca:
        pi, io, po = ca.get("P+I", 0), ca.get("I+O", 0), ca.get("P+O", 0)
        if pi >= GAP_MIN_PAIR:
            add("missing_outcome",
                (f"记录集中有 {pi} 条同时涉及「{P}」与「{I}」，但没有一条同时涉及「{O}」" if zh else
                 f"{pi} records cover '{P}' and '{I}' together, none also covers '{O}'"), {"P+I": pi, "P+I+O": 0})
        if io >= GAP_MIN_PAIR:
            add("missing_population",
                (f"记录集中有 {io} 条同时涉及「{I}」与「{O}」，但没有一条是在「{P}」中做的" if zh else
                 f"{io} records cover '{I}' and '{O}', none in '{P}'"), {"I+O": io, "P+I+O": 0})
        if po >= GAP_MIN_PAIR:
            add("missing_intervention",
                (f"记录集中有 {po} 条同时涉及「{P}」与「{O}」，但没有一条使用「{I}」" if zh else
                 f"{po} records cover '{P}' and '{O}', none uses '{I}'"), {"P+O": po, "P+I+O": 0})
    elif ev.direct_all > 0:
        add("direct_overlap",
            (f"记录集中有 {ev.direct_all} 条同时涉及「{P}」「{I}」「{O}」（近 {ev.window[1] - ev.window[0] + 1} 年 {ev.direct_recent} 条）；"
             "题目必须说明与它们的区别" if zh else
             f"{ev.direct_all} records cover '{P}', '{I}' and '{O}' ({ev.direct_recent} in the last "
             f"{ev.window[1] - ev.window[0] + 1} years); the proposal must say how it differs"), {"P+I+O": ev.direct_all})
        if ev.direct_design_mix:
            mix = ev.direct_design_mix
            if b.question_type == "effect" and not any(mix.get(k) for k in ("rct", "crossover", "quasi")):
                add("design_gap",
                    ("直接重叠的记录里没有一条是随机或准实验设计（题名/摘要中未检出）" if zh else
                     "none of the directly overlapping records is randomised or quasi-experimental (by title/abstract)"), dict(mix))
    if ev.n_records == 0:
        out.insert(0, {"kind": "empty", "text": "没有任何记录，无法绘制证据地图" if zh else "no records: the evidence map cannot be drawn", "counts": {}})
    return out


TIER_TEXT = {
    "zh": {"none": "近年未见直接重叠", "few": "有少量直接近邻", "crowded": "较拥挤", "very_crowded": "高度拥挤"},
    "en": {"none": "no direct overlap in the window", "few": "a few direct neighbours", "crowded": "crowded", "very_crowded": "very crowded"},
}
