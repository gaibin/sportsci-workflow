# -*- coding: utf-8 -*-
"""Questionnaire / cross-sectional survey analysis (design "survey") — the most common design in Chinese
sport-science master's theses (体育社会学、运动心理、学校体育).

Pipeline (each block runs only if the spec asks for it):
  scale scoring        reverse-keyed items, mean or sum score per scale
  reliability          Cronbach α, corrected item–total r, α if item deleted
  validity (EFA)       KMO, Bartlett's test, principal-axis factoring + varimax, eigenvalues, variance explained
  common-method bias   Harman single-factor test (first unrotated factor, threshold 40 %)
  descriptives         mean ± SD of scale scores, Pearson correlation matrix with exact P
  group differences    Welch t (2 levels, Hedges g) / one-way ANOVA (≥3 levels, η², Holm pairwise); BH q across all
  regression           OLS, unstandardised B, standardised β, 95% CI, VIF, R², adjusted R², F
  mediation            Hayes model 4, percentile bootstrap CI for the indirect effect
  moderation           Hayes model 1, mean-centred interaction, ΔR², simple slopes at −1 SD / mean / +1 SD

CFA / SEM are not done here (they need lavaan / AMOS / semopy); the Results text says so when EFA is reported.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from .util import bh, hedges_g, holm


# ----------------------------------------------------------------------------- scoring
def score_scales(df: pd.DataFrame, spec: Dict[str, Any]) -> pd.DataFrame:
    """Adds one column per scale (named after the scale) holding the mean (or sum) of its items, reverse items recoded."""
    out = df.copy()
    for sc in spec["scales"]:
        lo, hi = float(sc.get("min", 1)), float(sc.get("max", 5))
        X = out[sc["items"]].apply(pd.to_numeric, errors="coerce")
        for it in sc.get("reverse", []):
            X[it] = lo + hi - X[it]
        out[[f"_r_{it}" for it in sc["items"]]] = X.values
        out[sc["name"]] = X.sum(axis=1, min_count=len(sc["items"])) if sc.get("score") == "sum" else X.mean(axis=1, skipna=False)
    return out


def recoded_items(df: pd.DataFrame, sc: Dict[str, Any]) -> pd.DataFrame:
    return df[[f"_r_{it}" for it in sc["items"]]].set_axis(sc["items"], axis=1)


# ----------------------------------------------------------------------------- reliability
def cronbach_alpha(X: pd.DataFrame) -> float:
    X = X.dropna()
    k = X.shape[1]
    if k < 2 or len(X) < 3:
        return float("nan")
    tot = X.sum(axis=1).var(ddof=1)
    return float(k / (k - 1) * (1 - X.var(ddof=1).sum() / tot)) if tot > 0 else float("nan")


def item_stats(X: pd.DataFrame) -> List[Dict[str, Any]]:
    X = X.dropna()
    rows = []
    for c in X.columns:
        rest = X.drop(columns=c)
        r = float(np.corrcoef(X[c], rest.sum(axis=1))[0, 1]) if X[c].std() > 0 else float("nan")
        rows.append(dict(item=c, mean=float(X[c].mean()), sd=float(X[c].std(ddof=1)), r_it=r, alpha_del=cronbach_alpha(rest)))
    return rows


# ----------------------------------------------------------------------------- factor analysis
def kmo(R: np.ndarray) -> float:
    inv = np.linalg.pinv(R)
    d = np.sqrt(np.outer(np.diag(inv), np.diag(inv)))
    P = -inv / d
    off = ~np.eye(len(R), dtype=bool)
    r2, p2 = (R[off] ** 2).sum(), (P[off] ** 2).sum()
    return float(r2 / (r2 + p2))


def bartlett(R: np.ndarray, n: int) -> Tuple[float, int, float]:
    p = len(R)
    sign, logdet = np.linalg.slogdet(R)
    chi2 = float(-(n - 1 - (2 * p + 5) / 6) * logdet) if sign > 0 else float("inf")
    df = p * (p - 1) // 2
    return chi2, df, float(stats.chi2.sf(chi2, df))


def paf(R: np.ndarray, nf: int, iters: int = 200, tol: float = 1e-6) -> np.ndarray:
    """Principal-axis factoring (iterated communalities, SMC start)."""
    h2 = np.clip(1 - 1 / np.diag(np.linalg.pinv(R)), 0.05, 0.995)
    for _ in range(iters):
        Rr = R.copy()
        np.fill_diagonal(Rr, h2)
        val, vec = np.linalg.eigh(Rr)
        idx = np.argsort(val)[::-1][:nf]
        L = vec[:, idx] * np.sqrt(np.clip(val[idx], 0, None))
        new = np.clip((L ** 2).sum(1), 0.005, 0.995)
        if np.max(np.abs(new - h2)) < tol:
            break
        h2 = new
    return L


def varimax(L: np.ndarray, iters: int = 500, tol: float = 1e-8) -> np.ndarray:
    p, k = L.shape
    if k < 2:
        return L
    Rm = np.eye(k)
    d = 0.0
    for _ in range(iters):
        Lr = L @ Rm
        u, s, vt = np.linalg.svd(L.T @ (Lr ** 3 - Lr @ np.diag((Lr ** 2).sum(0)) / p))
        Rm = u @ vt
        if s.sum() - d < tol:
            break
        d = s.sum()
    Lr = L @ Rm
    # sign convention: each factor's largest loading positive; order by variance explained
    Lr = Lr * np.sign(Lr[np.abs(Lr).argmax(0), range(k)])
    return Lr[:, np.argsort(-(Lr ** 2).sum(0))]


def efa(items: pd.DataFrame, n_factors: Optional[int] = None) -> Dict[str, Any]:
    X = items.dropna()
    R = np.corrcoef(X.values, rowvar=False)
    eig = np.sort(np.linalg.eigvalsh(R))[::-1]
    nf = int(n_factors) if n_factors else max(1, int((eig > 1).sum()))
    L = varimax(paf(R, nf))
    p = R.shape[0]
    ss = (L ** 2).sum(0)
    chi2, df, bp = bartlett(R, len(X))
    return dict(n=int(len(X)), items=list(X.columns), n_factors=nf, eigen=eig.tolist(), kmo=kmo(R), bartlett=dict(chi2=chi2, df=df, p=bp),
                loadings=L.tolist(), communality=(L ** 2).sum(1).tolist(), var_pct=(ss / p * 100).tolist(), cum_pct=np.cumsum(ss / p * 100).tolist(),
                n_factors_rule="spec" if n_factors else "Kaiser (eigenvalue > 1)")


def harman(items: pd.DataFrame) -> Dict[str, float]:
    X = items.dropna()
    eig = np.sort(np.linalg.eigvalsh(np.corrcoef(X.values, rowvar=False)))[::-1]
    return dict(first_pct=float(eig[0] / len(eig) * 100), n_eig_gt1=int((eig > 1).sum()), n_items=int(len(eig)))


# ----------------------------------------------------------------------------- OLS helpers
def _design(df: pd.DataFrame, cols: Sequence[str]) -> pd.DataFrame:
    """Numeric design matrix; non-numeric columns become treatment-coded dummies."""
    parts = []
    for c in cols:
        x = pd.to_numeric(df[c], errors="coerce")
        if x.notna().sum() >= 0.9 * df[c].notna().sum() and df[c].notna().any():
            parts.append(x.rename(c))
        else:
            parts.append(pd.get_dummies(df[c].astype(str), prefix=c, drop_first=True, dtype=float))
    return pd.concat(parts, axis=1)


def _ols(y: np.ndarray, X: np.ndarray) -> Dict[str, Any]:
    n, k = X.shape
    XtX = np.linalg.pinv(X.T @ X)
    b = XtX @ X.T @ y
    r = y - X @ b
    dfe = n - k
    s2 = float(r @ r / dfe)
    se = np.sqrt(np.diag(XtX) * s2)
    t = b / se
    p = 2 * stats.t.sf(np.abs(t), dfe)
    tss = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - float(r @ r) / tss if tss > 0 else float("nan")
    return dict(b=b, se=se, t=t, p=p, df=dfe, r2=r2, cov=XtX * s2, n=n, k=k)


def regression(df: pd.DataFrame, y: str, xs: Sequence[str], covs: Sequence[str] = ()) -> Dict[str, Any]:
    preds = list(xs) + list(covs)
    D = pd.concat([pd.to_numeric(df[y], errors="coerce").rename(y), _design(df, preds)], axis=1).dropna()
    names = [c for c in D.columns if c != y]
    X = np.column_stack([np.ones(len(D)), D[names].values])
    m = _ols(D[y].values, X)
    sdx, sdy = D[names].std(ddof=1).values, D[y].std(ddof=1)
    tc = stats.t.ppf(0.975, m["df"])
    k = len(names)
    f = (m["r2"] / k) / ((1 - m["r2"]) / m["df"]) if k and m["r2"] < 1 else float("nan")
    vif = []
    for j in range(k):
        if k == 1:
            vif.append(1.0)
            continue
        others = np.column_stack([np.ones(len(D)), np.delete(D[names].values, j, axis=1)])
        rj = _ols(D[names].values[:, j], others)["r2"]
        vif.append(float(1 / (1 - rj)) if rj < 1 else float("inf"))
    coefs = [dict(term=nm, B=float(m["b"][j + 1]), se=float(m["se"][j + 1]), beta=float(m["b"][j + 1] * sdx[j] / sdy) if sdy > 0 else float("nan"),
                  t=float(m["t"][j + 1]), p=float(m["p"][j + 1]), lo=float(m["b"][j + 1] - tc * m["se"][j + 1]), hi=float(m["b"][j + 1] + tc * m["se"][j + 1]),
                  beta_lo=float((m["b"][j + 1] - tc * m["se"][j + 1]) * sdx[j] / sdy), beta_hi=float((m["b"][j + 1] + tc * m["se"][j + 1]) * sdx[j] / sdy),
                  vif=vif[j], is_cov=nm not in xs and not any(nm.startswith(f"{x}_") for x in xs))
             for j, nm in enumerate(names)]
    return dict(y=y, xs=list(xs), covs=list(covs), n=int(len(D)), r2=float(m["r2"]), adj_r2=float(1 - (1 - m["r2"]) * (len(D) - 1) / m["df"]),
                F=float(f), df1=k, df2=int(m["df"]), p_model=float(stats.f.sf(f, k, m["df"])) if np.isfinite(f) else float("nan"), coefs=coefs)


def mediation(df: pd.DataFrame, x: str, m: str, y: str, covs: Sequence[str] = (), n_boot: int = 5000, seed: int = 1) -> Dict[str, Any]:
    """Hayes PROCESS model 4 (simple mediation) with percentile bootstrap CI for a·b."""
    D = pd.concat([pd.to_numeric(df[c], errors="coerce").rename(c) for c in (x, m, y)] + ([_design(df, covs)] if covs else []), axis=1).dropna()
    C = D.drop(columns=[x, m, y]).values if covs else np.empty((len(D), 0))
    one = np.ones((len(D), 1))
    Xa = np.hstack([one, D[[x]].values, C])
    Xb = np.hstack([one, D[[x, m]].values, C])
    Xc = np.hstack([one, D[[x]].values, C])
    ma, mb, mc = _ols(D[m].values, Xa), _ols(D[y].values, Xb), _ols(D[y].values, Xc)

    def path(mm, j):
        tc = stats.t.ppf(0.975, mm["df"])
        return dict(est=float(mm["b"][j]), se=float(mm["se"][j]), lo=float(mm["b"][j] - tc * mm["se"][j]), hi=float(mm["b"][j] + tc * mm["se"][j]), p=float(mm["p"][j]))
    a, b, cp, c = path(ma, 1), path(mb, 2), path(mb, 1), path(mc, 1)
    rng = np.random.default_rng(seed)
    n = len(D)
    yv, mv = D[y].values, D[m].values
    boots = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        ba = np.linalg.lstsq(Xa[idx], mv[idx], rcond=None)[0][1]
        bb = np.linalg.lstsq(Xb[idx], yv[idx], rcond=None)[0][2]
        boots[i] = ba * bb
    ind = a["est"] * b["est"]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    sdx, sdy = D[x].std(ddof=1), D[y].std(ddof=1)
    return dict(x=x, m=m, y=y, covs=list(covs), n=int(n), n_boot=int(n_boot), a=a, b=b, c=c, cp=cp,
                indirect=dict(est=float(ind), lo=float(lo), hi=float(hi), boot_se=float(boots.std(ddof=1)), std=float(ind * sdx / sdy) if sdy > 0 else float("nan")),
                prop_mediated=float(ind / c["est"]) if c["est"] != 0 and np.sign(ind) == np.sign(c["est"]) else float("nan"))


def moderation(df: pd.DataFrame, x: str, w: str, y: str, covs: Sequence[str] = ()) -> Dict[str, Any]:
    """Hayes PROCESS model 1: y ~ x + w + x·w (mean-centred), simple slopes at w = −1 SD, mean, +1 SD."""
    D = pd.concat([pd.to_numeric(df[c], errors="coerce").rename(c) for c in (x, w, y)] + ([_design(df, covs)] if covs else []), axis=1).dropna()
    C = D.drop(columns=[x, w, y]).values if covs else np.empty((len(D), 0))
    C = C - C.mean(0) if C.size else C  # centred covariates: intercept = predicted y at the covariate means
    xc, wc = D[x] - D[x].mean(), D[w] - D[w].mean()
    one = np.ones((len(D), 1))
    X1 = np.hstack([one, np.column_stack([xc, wc]), C])
    X2 = np.hstack([one, np.column_stack([xc, wc, xc * wc]), C])
    m1, m2 = _ols(D[y].values, X1), _ols(D[y].values, X2)
    dr2 = m2["r2"] - m1["r2"]
    fch = dr2 / ((1 - m2["r2"]) / m2["df"])
    tc = stats.t.ppf(0.975, m2["df"])
    sdw = float(D[w].std(ddof=1))
    slopes = []
    for lab_, wv in (("-1SD", -sdw), ("mean", 0.0), ("+1SD", sdw)):
        est = m2["b"][1] + m2["b"][3] * wv
        se = float(np.sqrt(m2["cov"][1, 1] + wv ** 2 * m2["cov"][3, 3] + 2 * wv * m2["cov"][1, 3]))
        slopes.append(dict(level=lab_, w=float(D[w].mean() + wv), est=float(est), se=se, lo=float(est - tc * se), hi=float(est + tc * se),
                           p=float(2 * stats.t.sf(abs(est / se), m2["df"]))))
    terms = []
    for j, nm in enumerate((x, w, f"{x}×{w}")):
        terms.append(dict(term=nm, B=float(m2["b"][j + 1]), se=float(m2["se"][j + 1]), t=float(m2["t"][j + 1]), p=float(m2["p"][j + 1]),
                          lo=float(m2["b"][j + 1] - tc * m2["se"][j + 1]), hi=float(m2["b"][j + 1] + tc * m2["se"][j + 1])))
    return dict(x=x, w=w, y=y, covs=list(covs), n=int(len(D)), terms=terms, r2=float(m2["r2"]), dr2=float(dr2), F_change=float(fch),
                p_change=float(stats.f.sf(fch, 1, m2["df"])), df2=int(m2["df"]), slopes=slopes,
                _plot=dict(x_mean=float(D[x].mean()), x_sd=float(D[x].std(ddof=1)), x_min=float(D[x].min()), x_max=float(D[x].max()), b0=float(m2["b"][0]), b=m2["b"][1:4].tolist(), w_sd=sdw))


# ----------------------------------------------------------------------------- group differences
def group_compare(df: pd.DataFrame, var: str, outcome: str, levels: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    s = df[[var, outcome]].dropna()
    s[var] = s[var].astype(str)
    lv = [str(x) for x in (levels or sorted(s[var].unique()))]
    lv = [x for x in lv if (s[var] == x).sum() >= 2]
    samples = [pd.to_numeric(s.loc[s[var] == x, outcome], errors="coerce").dropna().values for x in lv]
    desc = {x: (float(v.mean()), float(v.std(ddof=1)), int(len(v))) for x, v in zip(lv, samples)}
    r = dict(var=var, outcome=outcome, levels=lv, desc=desc)
    if len(lv) == 2:
        t = stats.ttest_ind(samples[0], samples[1], equal_var=False)
        g, glo, ghi = hedges_g(samples[0], samples[1])
        v1, v2 = samples[0].var(ddof=1) / len(samples[0]), samples[1].var(ddof=1) / len(samples[1])
        dfw = (v1 + v2) ** 2 / (v1 ** 2 / (len(samples[0]) - 1) + v2 ** 2 / (len(samples[1]) - 1))
        r.update(test="t", stat=float(t.statistic), df=float(dfw), p=float(t.pvalue), es=g, es_lo=glo, es_hi=ghi, es_name="g", pairs=[])
    elif len(lv) >= 3:
        f = stats.f_oneway(*samples)
        allv = np.concatenate(samples)
        ssb = sum(len(v) * (v.mean() - allv.mean()) ** 2 for v in samples)
        sst = ((allv - allv.mean()) ** 2).sum()
        pairs = []
        for i in range(len(lv)):
            for j in range(i + 1, len(lv)):
                tt = stats.ttest_ind(samples[i], samples[j], equal_var=False)
                pairs.append(dict(a=lv[i], b=lv[j], diff=float(samples[i].mean() - samples[j].mean()), p=float(tt.pvalue)))
        for pr, ad in zip(pairs, holm([pp["p"] for pp in pairs])):
            pr["p_adj"] = float(ad)
        r.update(test="F", stat=float(f.statistic), df=(len(lv) - 1, len(allv) - len(lv)), p=float(f.pvalue), es=float(ssb / sst) if sst > 0 else float("nan"),
                 es_name="eta2", pairs=pairs)
    else:
        r.update(test=None, p=float("nan"))
    return r


# ----------------------------------------------------------------------------- main
def analyze_survey(df: pd.DataFrame, spec: Dict[str, Any]) -> Dict[str, Any]:
    d = score_scales(df, spec)
    scales = spec["scales"]
    names = [sc["name"] for sc in scales]
    res: Dict[str, Any] = dict(design="survey", n=int(len(d)), scales=[], _data=d)
    # sample description
    res["demographics"] = []
    for v in spec.get("demographics", []):
        col = v.get("column", v["name"])
        if col not in d:
            continue
        if v.get("type", "cat") == "cont":
            x = pd.to_numeric(d[col], errors="coerce")
            res["demographics"].append(dict(name=v["name"], kind="cont", mean=float(x.mean()), sd=float(x.std(ddof=1)), n=int(x.notna().sum())))
        else:
            s = d[col].dropna().astype(str)
            lv = [str(x) for x in (v.get("levels") or sorted(s.unique()))]
            res["demographics"].append(dict(name=v["name"], kind="cat", levels={x: int((s == x).sum()) for x in lv}, n=int(len(s))))
    # reliability
    for sc in scales:
        X = recoded_items(d, sc)
        res["scales"].append(dict(name=sc["name"], k=len(sc["items"]), alpha=cronbach_alpha(X), items=item_stats(X), n_complete=int(X.dropna().shape[0]),
                                  mean=float(d[sc["name"]].mean()), sd=float(d[sc["name"]].std(ddof=1)), score=sc.get("score", "mean"),
                                  min=sc.get("min", 1), max=sc.get("max", 5)))
    all_items = pd.concat([recoded_items(d, sc) for sc in scales], axis=1)
    if spec.get("common_method_bias", True) and all_items.shape[1] >= 3:
        res["harman"] = harman(all_items)
    ef = spec.get("efa", {})
    if ef.get("enabled", True) and all_items.shape[1] >= 3:
        nf = ef.get("n_factors") or (len(scales) if len(scales) > 1 else None)
        res["efa"] = efa(all_items, nf)
        res["efa"]["item_scale"] = [next(sc["name"] for sc in scales if it in sc["items"]) for it in res["efa"]["items"]]
    # correlations among scale scores
    S = d[names].apply(pd.to_numeric, errors="coerce")
    k = len(names)
    R, P = np.eye(k), np.zeros((k, k))
    for i in range(k):
        for j in range(i + 1, k):
            ok = S[[names[i], names[j]]].dropna()
            rr, pp = stats.pearsonr(ok.iloc[:, 0], ok.iloc[:, 1]) if len(ok) > 3 else (np.nan, np.nan)
            R[i, j] = R[j, i] = float(rr)
            P[i, j] = P[j, i] = float(pp)
    res["corr"] = dict(names=names, r=R.tolist(), p=P.tolist())
    # group differences (exploratory, BH across all tests)
    comps = []
    for var in spec.get("group_compare", []):
        dv = next((v for v in spec.get("demographics", []) if v["name"] == var), {})
        col = dv.get("column", var)
        if col not in d:
            continue
        for nm in names:
            g = group_compare(d, col, nm, dv.get("levels"))
            g["var"] = var
            if g.get("test"):
                comps.append(g)
    if comps:
        for g, q in zip(comps, bh([g["p"] for g in comps])):
            g["q"] = float(q)
    res["group_compare"] = comps
    res["regression"] = [regression(d, r["y"], r["x"], r.get("covariates", [])) for r in spec.get("regression", [])]
    res["mediation"] = [mediation(d, m["x"], m["m"], m["y"], m.get("covariates", []), int(m.get("n_boot", 5000)), int(m.get("seed", 1))) for m in spec.get("mediation", [])]
    res["moderation"] = [moderation(d, m["x"], m["w"], m["y"], m.get("covariates", [])) for m in spec.get("moderation", [])]
    return res
