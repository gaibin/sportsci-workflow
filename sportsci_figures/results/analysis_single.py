# -*- coding: utf-8 -*-
"""Single-group designs (design "single_group"): one group measured at 2 or more time points (单组前后测 / 单组重复测量).

  2 time points   paired t test (mean change, 95% CI, d_z) + Wilcoxon signed-rank as sensitivity; Shapiro–Wilk on the changes
  ≥ 3 time points one-way repeated-measures ANOVA: F, partial η², Mauchly's test, Greenhouse–Geisser ε and corrected P
                  (the corrected P is the one reported whenever sphericity is rejected — the SPSS convention),
                  all pairwise paired t tests with Bonferroni adjustment (SPSS default) and last-vs-first change with d_z

There is no control group, so a change over time cannot be attributed to the intervention alone (time, practice,
season, regression to the mean). The builder states this in the Results text and in every table note.
Multiplicity across outcomes: primary Holm, secondary BH within category (util.adjust_families).
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats

from .util import adjust_families, mean_ci, paired_dz


def _prep(df: pd.DataFrame, spec: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    c = spec["columns"]
    for k in ("id", "time"):
        if c[k] not in df.columns:
            raise KeyError(f"column '{c[k]}' (columns.{k}) not found in data; available: {list(df.columns)[:20]}")
        df[c[k]] = df[c[k]].astype(str)
    for o in spec["outcomes"]:
        if o["column"] not in df.columns:
            raise KeyError(f"outcome column '{o['column']}' not found in data; available: {list(df.columns)[:20]}")
        df[o["column"]] = pd.to_numeric(df[o["column"]], errors="coerce")
    return df


def rm_anova(Y: np.ndarray) -> Dict[str, float]:
    """One-way repeated-measures ANOVA on a complete n × k matrix, with Mauchly's test and Greenhouse–Geisser correction."""
    n, k = Y.shape
    gm = Y.mean()
    ss_time = n * ((Y.mean(0) - gm) ** 2).sum()
    ss_subj = k * ((Y.mean(1) - gm) ** 2).sum()
    ss_err = ((Y - gm) ** 2).sum() - ss_time - ss_subj
    df1, df2 = k - 1, (k - 1) * (n - 1)
    F = (ss_time / df1) / (ss_err / df2) if ss_err > 0 else float("inf")
    p = float(stats.f.sf(F, df1, df2))
    S = np.cov(Y, rowvar=False)
    # orthonormal contrasts (k × k-1)
    M = np.linalg.qr(np.column_stack([np.ones(k), np.eye(k)[:, :k - 1]]))[0][:, 1:]
    Sm = M.T @ S @ M
    eps = float(np.trace(Sm) ** 2 / (df1 * np.trace(Sm @ Sm))) if np.trace(Sm @ Sm) > 0 else 1.0
    eps = min(1.0, max(eps, 1.0 / df1))
    if k > 2:
        W = float(np.linalg.det(Sm) / (np.trace(Sm) / df1) ** df1)
        f = 1 - (2 * df1 ** 2 + df1 + 2) / (6 * df1 * (n - 1))
        chi = float(-(n - 1) * f * np.log(W)) if W > 0 else float("inf")
        dfm = df1 * (df1 + 1) / 2 - 1
        pm = float(stats.chi2.sf(chi, dfm))
    else:
        W, chi, dfm, pm = 1.0, 0.0, 0.0, 1.0
    p_gg = float(stats.f.sf(F, df1 * eps, df2 * eps))
    use_gg = pm < 0.05
    return dict(F=float(F), df1=df1, df2=df2, p=p, np2=float(ss_time / (ss_time + ss_err)) if ss_time + ss_err > 0 else float("nan"),
                mauchly_W=W, mauchly_chi2=chi, mauchly_df=dfm, mauchly_p=pm, eps_gg=eps, p_gg=p_gg, gg_applied=use_gg,
                p_report=p_gg if use_gg else p, df1_report=df1 * eps if use_gg else df1, df2_report=df2 * eps if use_gg else df2, n=n)


def analyze_single(df: pd.DataFrame, spec: Dict[str, Any]) -> Dict[str, Any]:
    df = _prep(df, spec)
    c = spec["columns"]
    idc, tc = c["id"], c["time"]
    times = [str(x) for x in spec["times"]["order"]]
    res: Dict[str, Any] = dict(design="single_group", times=times, n_id=int(df[idc].nunique()), outcomes=[])
    items: List[Dict[str, Any]] = []
    for o in spec["outcomes"]:
        w = df.pivot_table(index=idc, columns=tc, values=o["column"], aggfunc="first").reindex(columns=times)
        cc = w.dropna()
        r = dict(name=o["name"], column=o["column"], label=o["label"], unit=o["unit"], category=o["category"], primary=bool(o["primary"]),
                 direction=o.get("direction"), orient=-1 if o.get("direction") == "lower_better" else 1, decimals=o.get("decimals"))
        r["desc"] = {t: (float(w[t].mean()), float(w[t].std(ddof=1)), int(w[t].notna().sum())) for t in times}
        r["n_complete"] = int(len(cc))
        r["_wide"] = w
        chg = cc[times[-1]] - cc[times[0]]
        m, lo, hi, n = mean_ci(chg)
        dz = paired_dz(cc[times[-1]], cc[times[0]])
        se_dz = np.sqrt(1 / n + dz ** 2 / (2 * n)) if n > 1 and np.isfinite(dz) else float("nan")
        r["change"] = dict(diff=m, lo=lo, hi=hi, dz=dz, dz_lo=dz - 1.96 * se_dz, dz_hi=dz + 1.96 * se_dz, n=n,
                           shapiro_p=float(stats.shapiro(chg).pvalue) if 3 <= n <= 5000 else float("nan"))
        if len(times) == 2:
            t = stats.ttest_rel(cc[times[1]], cc[times[0]])
            wil = stats.wilcoxon(chg) if n >= 6 and (chg != 0).any() else None
            r["test"] = dict(kind="paired_t", t=float(t.statistic), df=n - 1, p=float(t.pvalue), wilcoxon_p=float(wil.pvalue) if wil else float("nan"))
            p_main = float(t.pvalue)
        else:
            a = rm_anova(cc.values.astype(float)) if n >= 3 else dict(p_report=float("nan"))
            r["test"] = dict(kind="rm_anova", **a)
            pairs = []
            for i in range(len(times)):
                for j in range(i + 1, len(times)):
                    d = cc[times[j]] - cc[times[i]]
                    mm, l2, h2, _ = mean_ci(d)
                    pp = float(stats.ttest_rel(cc[times[j]], cc[times[i]]).pvalue) if n > 2 else float("nan")
                    npair = len(times) * (len(times) - 1) / 2
                    pairs.append(dict(a=times[i], b=times[j], diff=mm, lo=l2, hi=h2, p=pp, p_bonf=min(1.0, pp * npair)))
            r["pairs"] = pairs
            p_main = a["p_report"]
        main = dict(outcome=o["name"], p=p_main, primary=r["primary"], category=r["category"])
        r["main"] = main
        items.append(main)
        res["outcomes"].append(r)
    adjust_families(items)
    return res
