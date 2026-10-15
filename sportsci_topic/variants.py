"""Variant matrix: change one axis of the question at a time and count the overlap again.

The point is differentiation. Two students who start from the same idea should not end with the same topic, and a topic
that sits one step away from the crowd is usually easier to defend than one inside it. The tool does not invent variants:
the brief lists alternatives per axis (population / intervention / comparator / outcome) and the tool counts them.

A zero is only informative if the variant's own vocabulary occurs somewhere in the record set. A variant that matches
nothing at all may simply not have been searched for; it is reported as "not assessable".
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import asdict, dataclass
from itertools import product
from typing import Dict, List, Optional, Sequence

from .brief import FACET_KEYS, Brief, Facet
from .evidence import classify, core_facets
from .records import Record


@dataclass
class Variant:
    axes: Dict[str, str]            # axis -> label (empty dict = the base question)
    n_facet_records: Dict[str, int]  # axis -> records matching that variant facet alone
    direct_all: int
    direct_recent: int
    delta_recent: int               # vs base
    assessable: bool
    note: str = ""

    def name(self) -> str:
        return " + ".join(f"{a}={l}" for a, l in self.axes.items()) or "base"

    def to_dict(self) -> Dict:
        return asdict(self) | {"name": self.name()}


def _count(records: Sequence[Record], facets: Dict[str, Facet], lo_year: int) -> Dict:
    hits = classify(records, facets)
    core = set(core_facets(facets))
    direct = [h for h in hits if core <= h.facets]
    return {"all": len(direct), "recent": sum(1 for h in direct if h.record.year >= lo_year),
            "facet": {k: sum(1 for h in hits if k in h.facets) for k in facets if facets[k].terms}}


def build_variants(records: Sequence[Record], b: Brief, *, this_year: Optional[int] = None, recent_years: int = 5,
                   two_axis: bool = False, limit: int = 40) -> List[Variant]:
    this_year = this_year or _dt.date.today().year
    lo = this_year - recent_years + 1
    base_facets = {k: b.facets[k] for k in FACET_KEYS if k in b.facets}
    base = _count(records, base_facets, lo)
    out = [Variant({}, base["facet"], base["all"], base["recent"], 0, True, note="base")]

    axes = [a for a in FACET_KEYS if b.variants.get(a)]
    combos: List[Dict[str, Facet]] = []
    for a in axes:
        combos += [{a: v} for v in b.variants[a]]
    if two_axis:
        for a1 in axes:
            for a2 in axes:
                if FACET_KEYS.index(a1) < FACET_KEYS.index(a2):
                    combos += [{a1: v1, a2: v2} for v1, v2 in product(b.variants[a1], b.variants[a2])]
    for combo in combos[:limit]:
        facets = dict(base_facets)
        facets.update(combo)
        c = _count(records, facets, lo)
        own = {a: c["facet"].get(a, 0) for a in combo}
        assessable = all(n > 0 for n in own.values())
        out.append(Variant({a: f.label or "/".join(f.terms[:1]) for a, f in combo.items()}, own, c["all"], c["recent"],
                           c["recent"] - base["recent"], assessable, note=" / ".join(f.note for f in combo.values() if f.note)))
    return out


def rank(vs: List[Variant]) -> List[Variant]:
    """Base first, then assessable variants with the fewest recent direct overlaps, then the rest."""
    base = [v for v in vs if not v.axes]
    rest = [v for v in vs if v.axes]
    rest.sort(key=lambda v: (not v.assessable, v.direct_recent, v.direct_all, v.name()))
    return base + rest
