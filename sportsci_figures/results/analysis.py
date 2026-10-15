# -*- coding: utf-8 -*-
"""Statistical engine: one function per design, all returning plain dicts (json-serialisable apart from the raw frames kept under '_').

  parallel_prepost  parallel groups, baseline + one follow-up   -> ANCOVA (follow-up ~ group + baseline), change scores, Hedges g
  crossover         every participant in every condition        -> linear mixed model (random intercept), EMMs, contrasts, trend
  multitime         parallel groups, >= 3 time points           -> constrained longitudinal LMM (or full group x time)
  meta              study-level effect sizes                    -> DerSimonian-Laird + Hartung-Knapp, subgroups, leave-one-out, Egger, meta-regression

Multiplicity (always stated in the table notes): primary outcome(s) Holm, secondary outcomes Benjamini-Hochberg within category.
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from .spec import orient
from .util import adjust_families, hedges_g, holm, mean_ci, paired_dz, smd_between


# ----------------------------------------------------------------------------- io
def load_data(path) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(p)
    return pd.read_csv(p, encoding="utf-8-sig")


def _prep(df: pd.DataFrame, spec: Dict[str, Any]) -> pd.DataFrame:
    """Cast key columns to str so that spec labels and data always match; check that outcome columns exist."""
    df = df.copy()
    c = spec["columns"]
    for k in ("id", "group", "time", "condition", "period"):
        if c.get(k):
            if c[k] not in df.columns:
                raise KeyError(f"column '{c[k]}' (columns.{k}) not found in data; available: {list(df.columns)[:20]}")
            df[c[k]] = df[c[k]].astype(str)
    for o in spec["outcomes"]:
        if o["column"] not in df.columns:
            raise KeyError(f"outcome column '{o['column']}' not found in data; available: {list(df.columns)[:20]}")
        df[o["column"]] = pd.to_numeric(df[o["column"]], errors="coerce")
    return df


# ----------------------------------------------------------------------------- linear-model helpers
def _contrast(beta: np.ndarray, cov: np.ndarray, L: np.ndarray, df: float) -> Dict[str, float]:
    est = float(L @ beta)
    se = float(np.sqrt(max(L @ cov @ L, 0)))
    tc = stats.t.ppf(0.975, df)
    p = float(2 * stats.t.sf(abs(est / se), df)) if se > 0 else float("nan")
    return dict(est=est, se=se, lo=est - tc * se, hi=est + tc * se, p=p)


def _fit_lmm(y: np.ndarray, X: np.ndarray, ids: np.ndarray) -> Tuple[np.ndarray, np.ndarray, str]:
    """Random-intercept LMM (REML). Falls back to fixed-effects OLS with participant dummies if the optimiser fails."""
    import statsmodels.api as sm
    k = X.shape[1]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            m = sm.MixedLM(y, X, groups=ids).fit(reml=True)
            beta = np.asarray(m.fe_params, float)
            cov = np.asarray(m.cov_params(), float)[:k, :k]
            if np.all(np.isfinite(beta)) and np.all(np.isfinite(cov)):
                return beta, cov, "LMM"
        except Exception:
            pass
    u = pd.Series(ids).astype("category").cat.codes.values
    D = np.eye(u.max() + 1)[u][:, 1:]
    XX = np.hstack([X, D])
    pin = np.linalg.pinv(XX.T @ XX)
    b = pin @ XX.T @ y
    r = y - XX @ b
    s2 = float(r @ r / max(len(y) - np.linalg.matrix_rank(XX), 1))
    return b[:k], (s2 * pin)[:k, :k], "FE-OLS"


def _desc(x) -> Tuple[float, float, int]:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return (float(x.mean()), float(x.std(ddof=1)) if len(x) > 1 else float("nan"), len(x)) if len(x) else (float("nan"), float("nan"), 0)


def _ostub(o: Dict[str, Any]) -> Dict[str, Any]:
    return dict(name=o["name"], column=o["column"], label=o["label"], unit=o["unit"], category=o["category"], primary=bool(o["primary"]),
                orient=orient(o), direction=o.get("direction"), decimals=o.get("decimals"))


# ----------------------------------------------------------------------------- baseline table (parallel / multitime)
def baseline_table(df: pd.DataFrame, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    c = spec["columns"]
    gc, idc = c["group"], c["id"]
    order = spec["groups"]["order"]
    ctrl = spec["groups"]["control"]
    one = df.drop_duplicates(idc)
    rows = []
    for v in spec.get("baseline_vars", []):
        col = v.get("column", v["name"])
        if col not in one.columns:
            continue
        kind = v.get("type", "cont")
        r = dict(name=v["name"], label=v.get("label", v["name"]), unit=v.get("unit", ""), kind=kind)
        if kind == "cont":
            x = pd.to_numeric(one[col], errors="coerce")
            r["groups"] = {g: _desc(x[one[gc] == g]) for g in order}
            r["total"] = _desc(x)
            r["smd"] = {g: smd_between(x[one[gc] == g], x[one[gc] == ctrl]) for g in order if g != ctrl}
            samples = [x[one[gc] == g].dropna() for g in order]
            r["p"] = float(stats.ttest_ind(*samples, equal_var=False).pvalue) if len(order) == 2 else float(stats.f_oneway(*samples).pvalue)
        else:
            s = one[col].astype(str)
            levels = list(v.get("levels") or sorted(s.unique()))
            r["levels"] = {lv: {g: (int(((s == lv) & (one[gc] == g)).sum()), int((one[gc] == g).sum())) for g in order} for lv in levels}
            r["total_levels"] = {lv: (int((s == lv).sum()), len(s)) for lv in levels}
            tab = pd.crosstab(s, one[gc]).reindex(columns=order).fillna(0).values
            if tab.shape == (2, 2):
                r["p"] = float(stats.fisher_exact(tab)[1])
            else:
                r["p"] = float(stats.chi2_contingency(tab)[1]) if tab.shape[0] > 1 and (tab.sum(0) > 0).all() else float("nan")
            r["smd"] = {}
        rows.append(r)
    return rows


# ============================================================================ parallel pre/post
def analyze_parallel(df: pd.DataFrame, spec: Dict[str, Any]) -> Dict[str, Any]:
    df = _prep(df, spec)
    c = spec["columns"]
    idc, gc, tc = c["id"], c["group"], c["time"]
    t0, t1 = [str(x) for x in spec["times"]["order"]]
    order = [str(g) for g in spec["groups"]["order"]]
    ctrl = str(spec["groups"]["control"])
    arms = [g for g in order if g != ctrl]
    gmap = df.drop_duplicates(idc).set_index(idc)[gc]
    res = dict(design="parallel_prepost", groups=order, control=ctrl, arms=arms, times=[t0, t1], outcomes=[], n_group={g: int((gmap == g).sum()) for g in order})
    items = []
    for o in spec["outcomes"]:
        w = df.pivot_table(index=idc, columns=tc, values=o["column"], aggfunc="first").reindex(columns=[t0, t1])
        w.columns = ["pre", "post"]
        w["g"] = gmap.reindex(w.index)
        w = w[w["g"].isin(order)]
        w["chg"] = w["post"] - w["pre"]
        r = _ostub(o)
        r["desc"] = {}
        for g in order:
            s = w[w["g"] == g]
            r["desc"][g] = dict(pre=_desc(s["pre"]), post=_desc(s["post"]), chg=mean_ci(s["chg"]) + (
                float(stats.ttest_1samp(s["chg"].dropna(), 0).pvalue) if s["chg"].notna().sum() > 2 else float("nan"),))
        cc = w.dropna(subset=["pre", "post"])
        X = np.column_stack([np.ones(len(cc))] + [(cc["g"] == a).astype(float).values for a in arms] + [cc["pre"].values])
        y = cc["post"].values
        n, k = X.shape
        pin = np.linalg.pinv(X.T @ X)
        b = pin @ X.T @ y
        s2 = float(((y - X @ b) ** 2).sum() / (n - k))
        cov = s2 * pin
        r["contrasts"] = []
        for i, a in enumerate(arms):
            L = np.zeros(k)
            L[1 + i] = 1
            ct = _contrast(b, cov, L, n - k)
            g, glo, ghi = hedges_g(cc.loc[cc["g"] == a, "chg"], cc.loc[cc["g"] == ctrl, "chg"])
            d = dict(arm=a, diff=ct["est"], lo=ct["lo"], hi=ct["hi"], p=ct["p"], g=g, glo=glo, ghi=ghi, n_arm=int((cc["g"] == a).sum()), n_ctl=int((cc["g"] == ctrl).sum()),
                     primary=r["primary"], category=r["category"], outcome=o["name"])
            r["contrasts"].append(d)
            items.append(d)
        r["n_model"] = int(n)
        r["_wide"] = w
        res["outcomes"].append(r)
    adjust_families(items)
    res["baseline"] = baseline_table(df, spec)
    return res


# ============================================================================ crossover
def _crossover_X(d: pd.DataFrame, conds: List[str], ctrl: str, period_col):
    others = [x for x in conds if x != ctrl]
    cols = [np.ones(len(d))] + [(d["_cond"] == x).astype(float).values for x in others]
    plev = []
    if period_col is not None:
        plev = sorted(d[period_col].unique())[1:]
        cols += [(d[period_col] == p).astype(float).values for p in plev]
    X = np.column_stack(cols)
    pmean = X[:, 1 + len(others):].mean(0) if plev else np.array([])
    return X, others, pmean


def analyze_crossover(df: pd.DataFrame, spec: Dict[str, Any]) -> Dict[str, Any]:
    df = _prep(df, spec)
    c = spec["columns"]
    idc, cc_ = c["id"], c["condition"]
    pc = c.get("period")
    conds = [str(x) for x in spec["conditions"]["order"]]
    ctrl = str(spec["conditions"]["control"])
    dose = {str(k): float(v) for k, v in spec["conditions"].get("dose", {}).items()}
    pairs = [(str(a), str(b)) for a, b in spec["conditions"].get("pairs", [])]
    df["_cond"] = df[cc_]
    df = df[df["_cond"].isin(conds)]
    if pc and df[pc].nunique() < 2:
        pc = None
    res = dict(design="crossover", conditions=conds, control=ctrl, outcomes=[], n_id=int(df[idc].nunique()), period_adjusted=bool(pc))
    items = []
    for o in spec["outcomes"]:
        d = df[[idc, "_cond", o["column"]] + ([pc] if pc else [])].dropna(subset=[o["column"]]).reset_index(drop=True)
        X, others, pmean = _crossover_X(d, conds, ctrl, pc)
        y = d[o["column"]].values.astype(float)
        beta, cov, model = _fit_lmm(y, X, d[idc].values)
        n_id = d[idc].nunique()
        dfree = max(n_id - 1, 1)
        k = X.shape[1]
        rowv = {x: np.concatenate([[1], [1.0 if x == oo else 0.0 for oo in others], pmean]) for x in conds}
        r = _ostub(o)
        r["model"], r["n_obs"], r["n_id"] = model, int(len(d)), int(n_id)
        r["emm"] = {}
        for x in conds:
            ct = _contrast(beta, cov, rowv[x], dfree)
            r["emm"][x] = (ct["est"], ct["lo"], ct["hi"])
        wide = d.pivot_table(index=idc, columns="_cond", values=o["column"], aggfunc="first")
        r["_wide"] = wide
        r["desc"] = {x: _desc(wide[x]) if x in wide else (np.nan, np.nan, 0) for x in conds}
        r["contrasts"] = []
        for x in others:
            ct = _contrast(beta, cov, rowv[x] - rowv[ctrl], dfree)
            dz = paired_dz(wide[x], wide[ctrl]) if x in wide and ctrl in wide else float("nan")
            dd = dict(arm=x, diff=ct["est"], lo=ct["lo"], hi=ct["hi"], p=ct["p"], dz=dz, primary=r["primary"], category=r["category"], outcome=o["name"],
                      pct=(100 * ct["est"] / r["emm"][ctrl][0]) if r["emm"][ctrl][0] else float("nan"))
            r["contrasts"].append(dd)
            items.append(dd)
        r["pairs"] = []
        for a, b in pairs:
            if a in rowv and b in rowv:
                ct = _contrast(beta, cov, rowv[a] - rowv[b], dfree)
                r["pairs"].append(dict(a=a, b=b, diff=ct["est"], lo=ct["lo"], hi=ct["hi"], p=ct["p"]))
        if r["pairs"]:
            for pr, ad in zip(r["pairs"], holm([p["p"] for p in r["pairs"]])):
                pr["p_adj"] = float(ad)
        if dose and sum(1 for x in conds if x in dose) >= 3:
            ds = d[d["_cond"].isin(dose)].reset_index(drop=True)
            Xd = np.column_stack([np.ones(len(ds)), ds["_cond"].map(dose).values] + ([(ds[pc] == p).astype(float).values for p in sorted(ds[pc].unique())[1:]] if pc else []))
            bd, cd, _ = _fit_lmm(ds[o["column"]].values.astype(float), Xd, ds[idc].values)
            L = np.zeros(Xd.shape[1])
            L[1] = 1
            r["trend"] = _contrast(bd, cd, L, dfree) | dict(intercept=float(bd[0]))
        res["outcomes"].append(r)
    adjust_families(items)
    return res


# ============================================================================ multitime
def mixed_anova(d: pd.DataFrame, idc: str, gc: str, tc: str, col: str, times: List[str]) -> Dict[str, Any]:
    """Group × time mixed ANOVA on complete cases (the SPSS 'repeated measures' table Chinese supervisors expect).

    Reported next to the LMM as a supplementary analysis. Greenhouse–Geisser correction is applied to the time and the
    interaction effects whenever Mauchly's test rejects sphericity (same ε for both, as in SPSS).
    """
    import pingouin as pg
    w = d.pivot_table(index=idc, columns=tc, values=col, aggfunc="first").reindex(columns=times).dropna()
    keep = w.index
    sub = d[d[idc].isin(keep) & d[tc].isin(times)][[idc, gc, tc, col]].dropna()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        a = pg.mixed_anova(sub, dv=col, within=tc, between=gc, subject=idc, correction=True)
    pcol = "p-unc" if "p-unc" in a.columns else "p_unc"
    rows = {r["Source"]: r for _, r in a.iterrows()}
    tr = rows.get(tc, {})
    eps = float(tr.get("eps", 1.0)) if pd.notna(tr.get("eps", np.nan)) else 1.0
    gg = bool(pd.notna(tr.get("p-spher", np.nan)) and tr.get("p-spher") < 0.05)
    out = dict(n=int(len(keep)), eps=eps, gg_applied=gg, mauchly_p=float(tr.get("p-spher", np.nan)) if pd.notna(tr.get("p-spher", np.nan)) else float("nan"), effects=[])
    for src, key in ((gc, "group"), (tc, "time"), ("Interaction", "group_x_time")):
        r = rows[src]
        df1, df2, F = float(r["DF1"]), float(r["DF2"]), float(r["F"])
        within = key != "group"
        if within and gg:
            df1, df2 = df1 * eps, df2 * eps
        out["effects"].append(dict(effect=key, F=F, df1=df1, df2=df2, p=float(stats.f.sf(F, df1, df2)) if within and gg else float(r[pcol]), np2=float(r["np2"])))
    return out


def analyze_multitime(df: pd.DataFrame, spec: Dict[str, Any]) -> Dict[str, Any]:
    df = _prep(df, spec)
    c = spec["columns"]
    idc, gc, tc = c["id"], c["group"], c["time"]
    times = [str(x) for x in spec["times"]["order"]]
    order = [str(g) for g in spec["groups"]["order"]]
    ctrl = str(spec["groups"]["control"])
    arms = [g for g in order if g != ctrl]
    constrained = bool(spec.get("multitime", {}).get("constrained_baseline", True))
    ptime = str(spec["times"].get("primary", times[-1]))
    post = times[1:]
    res = dict(design="multitime", groups=order, control=ctrl, arms=arms, times=times, primary_time=ptime, constrained=constrained, outcomes=[],
               n_group={g: int(df[df[gc] == g][idc].nunique()) for g in order})
    items = []
    for o in spec["outcomes"]:
        d = df[df[gc].isin(order) & df[tc].isin(times)][[idc, gc, tc, o["column"]]].dropna().reset_index(drop=True)
        names = ["(Intercept)"] + [f"T:{t}" for t in post] + ([] if constrained else [f"G:{a}" for a in arms]) + [f"G:{a}*T:{t}" for a in arms for t in post]

        def row(g, t):
            v = [1.0] + [1.0 if t == tt else 0.0 for tt in post]
            if not constrained:
                v += [1.0 if g == a else 0.0 for a in arms]
            v += [1.0 if (g == a and t == tt) else 0.0 for a in arms for tt in post]
            return np.array(v)
        X = np.array([row(g, t) for g, t in zip(d[gc], d[tc])])
        beta, cov, model = _fit_lmm(d[o["column"]].values.astype(float), X, d[idc].values)
        dfree = max(d[idc].nunique() - len(order), 1)
        r = _ostub(o)
        r["model"], r["n_obs"] = model, int(len(d))
        r["emm"] = {g: {t: (lambda ct: (ct["est"], ct["lo"], ct["hi"]))(_contrast(beta, cov, row(g, t), dfree)) for t in times} for g in order}
        r["desc"] = {g: {t: _desc(d[(d[gc] == g) & (d[tc] == t)][o["column"]]) for t in times} for g in order}
        r["contrasts"] = []
        for a in arms:
            for t in post:
                ct = _contrast(beta, cov, row(a, t) - row(ctrl, t), dfree)
                obs_a = d[(d[gc] == a) & (d[tc] == t)][o["column"]]
                obs_c = d[(d[gc] == ctrl) & (d[tc] == t)][o["column"]]
                dd = dict(arm=a, time=t, diff=ct["est"], lo=ct["lo"], hi=ct["hi"], p=ct["p"], g=smd_between(obs_a, obs_c), primary=r["primary"], category=r["category"], outcome=o["name"],
                          at_primary=(t == ptime))
                r["contrasts"].append(dd)
                if t == ptime:
                    items.append(dd)
        try:
            r["mixed_anova"] = mixed_anova(df, idc, gc, tc, o["column"], times)
        except Exception as exc:  # supplementary only; never break the primary LMM analysis
            r["mixed_anova"] = dict(error=str(exc))
        idx = [i for i, nm in enumerate(names) if nm.startswith("G:") and "*T:" in nm]
        if idx:
            bb = beta[idx]
            W = float(bb @ np.linalg.pinv(cov[np.ix_(idx, idx)]) @ bb)
            r["p_group_time"] = float(stats.chi2.sf(W, len(idx)))
        res["outcomes"].append(r)
    adjust_families(items)
    res["baseline"] = baseline_table(df, spec)
    res["_long"] = df
    return res


# ============================================================================ meta-analysis
def pool(es: np.ndarray, var: np.ndarray, hksj: bool = True) -> Dict[str, Any]:
    es, var = np.asarray(es, float), np.asarray(var, float)
    k = len(es)
    w = 1 / var
    fe = (w * es).sum() / w.sum()
    Q = float((w * (es - fe) ** 2).sum())
    C = w.sum() - (w ** 2).sum() / w.sum()
    tau2 = max(0.0, (Q - (k - 1)) / C) if k > 1 and C > 0 else 0.0
    wr = 1 / (var + tau2)
    est = float((wr * es).sum() / wr.sum())
    se = float(np.sqrt(1 / wr.sum()))
    if hksj and k > 1:
        q = float((wr * (es - est) ** 2).sum() / (k - 1))
        se = float(np.sqrt(max(1.0, q) / wr.sum()))
        crit = stats.t.ppf(0.975, k - 1)
        p = float(2 * stats.t.sf(abs(est / se), k - 1))
    else:
        crit = 1.96
        p = float(2 * stats.norm.sf(abs(est / se)))
    out = dict(k=k, est=est, se=se, lo=est - crit * se, hi=est + crit * se, p=p, tau2=tau2, tau=float(np.sqrt(tau2)), Q=Q, Qp=float(stats.chi2.sf(Q, k - 1)) if k > 1 else float("nan"),
               I2=float(max(0.0, (Q - (k - 1)) / Q) * 100) if Q > 0 and k > 1 else 0.0, w=wr / wr.sum() * 100, hksj=bool(hksj and k > 1))
    if k >= 3:
        pc = stats.t.ppf(0.975, k - 2)
        spi = np.sqrt(tau2 + se ** 2)
        out["pi"] = (est - pc * spi, est + pc * spi)
    return out


def effect_sizes(df: pd.DataFrame, spec: Dict[str, Any]) -> pd.DataFrame:
    c, m = spec["columns"], spec.get("meta", {})
    mode = m.get("effect", "smd")
    d = pd.DataFrame({"study": df[c["study"]].astype(str).values})
    if mode in ("smd", "md"):
        n1, m1, s1, n2, m2, s2 = [pd.to_numeric(df[c[k]], errors="coerce").values.astype(float) for k in ("n1", "m1", "sd1", "n2", "m2", "sd2")]
        if mode == "smd":
            sp = np.sqrt(((n1 - 1) * s1 ** 2 + (n2 - 1) * s2 ** 2) / (n1 + n2 - 2))
            g = (m1 - m2) / sp * (1 - 3 / (4 * (n1 + n2 - 2) - 1))
            es, var = g, (n1 + n2) / (n1 * n2) + g ** 2 / (2 * (n1 + n2))
        else:
            es, var = m1 - m2, s1 ** 2 / n1 + s2 ** 2 / n2
    else:
        es = pd.to_numeric(df[c["es"]], errors="coerce").values.astype(float)
        if c.get("se"):
            var = pd.to_numeric(df[c["se"]], errors="coerce").values.astype(float) ** 2
        else:
            var = ((pd.to_numeric(df[c["hi"]], errors="coerce").values - pd.to_numeric(df[c["lo"]], errors="coerce").values) / (2 * 1.96)) ** 2
    sign = -1.0 if m.get("direction") == "lower_better" else 1.0
    d["es"], d["var"] = sign * es, var
    if mode in ("smd", "md"):
        d["n1"], d["n2"] = n1, n2
    d["se"] = np.sqrt(var)
    d["lo"], d["hi"] = d["es"] - 1.96 * d["se"], d["es"] + 1.96 * d["se"]
    for k in ("subgroup", "moderator"):
        if c.get(k):
            d[k] = df[c[k]].values
    if c.get("year"):
        d["year"] = df[c["year"]].values
    d = d.dropna(subset=["es", "var"]).reset_index(drop=True)
    return d


def analyze_meta(df: pd.DataFrame, spec: Dict[str, Any]) -> Dict[str, Any]:
    m = spec.get("meta", {})
    hksj = bool(m.get("hksj", True))
    d = effect_sizes(df, spec)
    if len(d) < 2:
        raise ValueError("meta-analysis needs at least 2 studies with complete data")
    res = dict(design="meta", effect=m.get("effect", "smd"), k=len(d), hksj=hksj)
    P = pool(d["es"].values, d["var"].values, hksj)
    d["w"] = P["w"]
    res["pooled"] = {k: v for k, v in P.items() if k != "w"}
    res["studies"] = d
    res["loo"] = [dict(omit=d["study"][i], **{k: v for k, v in pool(d["es"].drop(i).values, d["var"].drop(i).values, hksj).items() if k in ("est", "lo", "hi", "I2")}) for i in range(len(d))] if len(d) >= 3 else []
    if "subgroup" in d:
        subs = []
        for lv in sorted(d["subgroup"].dropna().astype(str).unique()):
            s = d[d["subgroup"].astype(str) == lv]
            if len(s) >= 2:
                pp = pool(s["es"].values, s["var"].values, hksj)
            else:
                pp = dict(k=1, est=float(s["es"].iloc[0]), se=float(s["se"].iloc[0]), lo=float(s["lo"].iloc[0]), hi=float(s["hi"].iloc[0]), p=float("nan"), I2=float("nan"), tau2=float("nan"))
            subs.append(dict(level=lv, **{k: v for k, v in pp.items() if k != "w"}))
        if len(subs) >= 2:
            ws = np.array([1 / s["se"] ** 2 for s in subs])
            es_ = np.array([s["est"] for s in subs])
            comb = (ws * es_).sum() / ws.sum()
            Qb = float((ws * (es_ - comb) ** 2).sum())
            res["subgroups"] = subs
            res["Q_between"] = dict(Q=Qb, df=len(subs) - 1, p=float(stats.chi2.sf(Qb, len(subs) - 1)))
    if len(d) >= 10:
        z, prec = d["es"].values / d["se"].values, 1 / d["se"].values
        Xe = np.column_stack([np.ones(len(d)), prec])
        be, *_ = np.linalg.lstsq(Xe, z, rcond=None)
        rr = z - Xe @ be
        s2 = rr @ rr / (len(d) - 2)
        se_i = np.sqrt(s2 * np.linalg.inv(Xe.T @ Xe)[0, 0])
        res["egger"] = dict(intercept=float(be[0]), se=float(se_i), p=float(2 * stats.t.sf(abs(be[0] / se_i), len(d) - 2)))
    else:
        res["egger"] = None
    if "moderator" in d:
        dm = d.dropna(subset=["moderator"]).copy()
        dm["moderator"] = pd.to_numeric(dm["moderator"], errors="coerce")
        dm = dm.dropna(subset=["moderator"])
        if len(dm) >= 4:
            X = np.column_stack([np.ones(len(dm)), dm["moderator"].values])
            y, v = dm["es"].values, dm["var"].values
            W = np.diag(1 / v)
            Pm = W - W @ X @ np.linalg.inv(X.T @ W @ X) @ X.T @ W
            tau2 = max(0.0, (y @ Pm @ y - (len(dm) - 2)) / np.trace(Pm))
            wr = 1 / (v + tau2)
            XtW = X.T * wr
            cov = np.linalg.inv(XtW @ X)
            b = cov @ XtW @ y
            QE = float((wr * (y - X @ b) ** 2).sum())
            sc = max(1.0, QE / (len(dm) - 2))
            se = float(np.sqrt(cov[1, 1] * sc))
            tcrit = stats.t.ppf(0.975, len(dm) - 2)
            res["metareg"] = dict(slope=float(b[1]), intercept=float(b[0]), se=se, lo=float(b[1] - tcrit * se), hi=float(b[1] + tcrit * se),
                                  p=float(2 * stats.t.sf(abs(b[1] / se), len(dm) - 2)), k=len(dm), tau2=tau2, name=spec["columns"].get("moderator"))
    return res


# ----------------------------------------------------------------------------- dispatcher
def analyze(df: pd.DataFrame, spec: Dict[str, Any]) -> Dict[str, Any]:
    from .analysis_single import analyze_single
    from .analysis_survey import analyze_survey
    return {"parallel_prepost": analyze_parallel, "crossover": analyze_crossover, "multitime": analyze_multitime, "meta": analyze_meta,
            "single_group": analyze_single, "survey": analyze_survey}[spec["design"]](df, spec)
