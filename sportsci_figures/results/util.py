# -*- coding: utf-8 -*-
"""Small statistical helpers shared by the analysis modules."""
from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np
from scipy import stats


def holm(p: Sequence[float]) -> np.ndarray:
    p = np.asarray(p, float)
    n = len(p)
    adj = np.empty(n)
    run = 0.0
    for rank, i in enumerate(np.argsort(p)):
        run = max(run, (n - rank) * p[i])
        adj[i] = min(1.0, run)
    return adj


def bh(p: Sequence[float]) -> np.ndarray:
    p = np.asarray(p, float)
    n = len(p)
    adj = np.empty(n)
    run = 1.0
    for rank, i in enumerate(np.argsort(p)[::-1]):
        run = min(run, p[i] * n / (n - rank))
        adj[i] = run
    return adj


def hedges_g(x, y) -> Tuple[float, float, float]:
    """Hedges g (x - y) with 95% CI (large-sample SE)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    x, y = x[np.isfinite(x)], y[np.isfinite(y)]
    n1, n2 = len(x), len(y)
    sp = np.sqrt(((n1 - 1) * x.var(ddof=1) + (n2 - 1) * y.var(ddof=1)) / (n1 + n2 - 2))
    if not sp > 0:
        return 0.0, 0.0, 0.0
    j = 1 - 3 / (4 * (n1 + n2) - 9)
    g = j * (x.mean() - y.mean()) / sp
    se = np.sqrt((n1 + n2) / (n1 * n2) + g * g / (2 * (n1 + n2)))
    return float(g), float(g - 1.96 * se), float(g + 1.96 * se)


def paired_dz(a, b) -> float:
    d = np.asarray(a, float) - np.asarray(b, float)
    d = d[np.isfinite(d)]
    return float(d.mean() / d.std(ddof=1)) if len(d) > 2 and d.std(ddof=1) > 0 else float("nan")


def mean_ci(x) -> Tuple[float, float, float, int]:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 2:
        return (float(x.mean()) if n else float("nan")), float("nan"), float("nan"), n
    se = x.std(ddof=1) / np.sqrt(n)
    tc = stats.t.ppf(0.975, n - 1)
    return float(x.mean()), float(x.mean() - tc * se), float(x.mean() + tc * se), n


def smd_between(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    sp = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return float((a.mean() - b.mean()) / sp) if sp > 0 else float("nan")


def adjust_families(items: List[Dict]) -> None:
    """In-place multiplicity adjustment. items: dicts with p, primary, category.

    Family rule (stated in every table note):
      primary outcomes   -> Holm across all contrasts of the primary outcome(s)
      secondary outcomes -> Benjamini-Hochberg within outcome category
    Adds 'p_adj' and 'adj_method'.
    """
    prim = [i for i in items if i["primary"]]
    if prim:
        for i, a in zip(prim, holm([i["p"] for i in prim])):
            i["p_adj"], i["adj_method"] = float(a), "Holm"
    sec = [i for i in items if not i["primary"]]
    for cat in sorted({i["category"] for i in sec}):
        fam = [i for i in sec if i["category"] == cat]
        for i, a in zip(fam, bh([i["p"] for i in fam])):
            i["p_adj"], i["adj_method"] = float(a), "BH"
