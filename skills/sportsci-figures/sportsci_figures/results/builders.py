# -*- coding: utf-8 -*-
"""Sections (figures + tables + results sentences) for each design, in the active language.

Every builder returns a list of sections: {"heading": str, "items": [("p", text) | ("fig", png_path, caption) | ("tab", DataFrame, caption, note)]}.
`build.py` turns that one structure into docx, markdown and xlsx, so text, tables and figures can never disagree.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..pubstyle import figures as pf
from ..pubstyle.style import (C_AMBER, C_CORAL, C_GREY, C_INK, C_MAGENTA, C_MID, C_SLATE, C_TEAL, DOUBLE, dose_colors, fmt_p, hair_y, panel_letter, panel_title, save_figure, wrap_label)
from ..pubstyle.tables import fmt_ci, fmt_num, fmt_p_table
from . import plots
from .spec import lab, orient

CAT_COLORS = [C_MAGENTA, C_SLATE, C_TEAL, C_CORAL, C_MID, C_AMBER]


class Ctx:
    def __init__(self, spec: Dict[str, Any], res: Dict[str, Any], df: pd.DataFrame, lang: str, fig_dir: Path):
        self.spec, self.res, self.df, self.lang, self.fig_dir = spec, res, df, lang, Path(fig_dir)
        self.sim = bool(spec.get("simulated"))
        self.fig_dir.mkdir(parents=True, exist_ok=True)
        self.nfig = 0

    # ---- language helpers
    def T(self, zh: str, en: str) -> str:
        return zh if self.lang == "zh" else en

    def L(self, obj, default="") -> str:
        return lab(obj, self.lang, default)

    def minus(self, s: str) -> str:
        return s.replace("-", "−") if self.lang == "en" else s

    def num(self, x, nd=None) -> str:
        return self.minus(fmt_num(x, nd))

    def ci(self, lo, hi, nd=None) -> str:
        sep = "～" if self.lang == "zh" else " to "
        return self.minus(f"95% CI {fmt_num(lo, nd)}{sep}{fmt_num(hi, nd)}")

    def cell_ci(self, est, lo, hi, nd=None) -> str:
        return self.minus(fmt_ci(est, lo, hi, nd))

    def P(self, p) -> str:
        return fmt_p(p)

    def padj(self, c) -> str:
        m = c.get("adj_method", "")
        p = c.get("p_adj")
        if p is None:
            return ""
        body = "< 0.001" if p < 0.001 else f"= {p:.3f}"
        return (f"Holm P {body}" if m == "Holm" else f"BH q {body}")

    # ---- spec labels
    def glabel(self, g: str) -> str:
        return self.L(self.spec.get("groups", {}).get("labels", {}).get(g, g), g)

    def clabel(self, c: str) -> str:
        return self.L(self.spec.get("conditions", {}).get("labels", {}).get(c, c), c)

    def tlabel(self, t: str) -> str:
        return self.L(self.spec.get("times", {}).get("labels", {}).get(t, t), t)

    def catlabel(self, c: str) -> str:
        return self.L(self.spec.get("category_labels", {}).get(c, c), c)

    def olabel(self, o: Dict[str, Any], unit: bool = True) -> str:
        base = self.L(o["label"], o["name"])
        return f"{base} ({o['unit']})" if unit and o.get("unit") else base

    def ocolors(self, cats: List[str]) -> Dict[str, str]:
        return {c: CAT_COLORS[i % len(CAT_COLORS)] for i, c in enumerate(cats)}

    def save(self, fig, name: str) -> Path:
        self.nfig += 1
        stem = self.fig_dir / f"fig{self.nfig}_{name}"
        save_figure(fig, stem, simulated=self.sim)
        return stem.with_suffix(".png")


def _colors(order: List[str], control: str) -> Dict[str, str]:
    arms = [g for g in order if g != control]
    ramp = dose_colors(len(arms)) if len(arms) > 1 else [C_MAGENTA]
    out = {control: C_AMBER}
    out.update(dict(zip(arms, ramp)))
    return out


def _cat_header_rows(rows: List[List[str]], cats: List[str], ncol: int, cx: Ctx) -> List[List[str]]:
    """Insert one label row per category (only when there is more than one category)."""
    if len(set(cats)) < 2:
        return rows
    out, last = [], None
    for r, c in zip(rows, cats):
        if c != last:
            out.append([cx.catlabel(c)] + [""] * (ncol - 1))
            last = c
        out.append(r)
    return out


def _forest_std(cx: Ctx, rows: List[dict], cats: List[str], xlabel: str, foot: str, name: str) -> Path:
    cc = cx.ocolors(cats)
    fig = pf.fig_forest_effects(rows, [cx.catlabel(c) for c in cats], {cx.catlabel(c): cc[c] for c in cats}, xlabel, footnote=foot, width=DOUBLE)
    return cx.save(fig, name)


def _trunc(parts, n=5, more=" …"):
    return parts if len(parts) <= n else parts[:n] + [more.strip()]


def _sig(c) -> bool:
    return c.get("p_adj", c["p"]) < 0.05


# ============================================================================ parallel pre/post
def build_parallel(cx: Ctx) -> List[Dict[str, Any]]:
    s, r, T = cx.spec, cx.res, cx.T
    order, ctrl, arms = r["groups"], r["control"], r["arms"]
    col = _colors(order, ctrl)
    gl = {g: cx.glabel(g) for g in order}
    t0, t1 = r["times"]
    secs: List[Dict[str, Any]] = []
    outs = r["outcomes"]
    prim = [o for o in outs if o["primary"]]
    sec = [o for o in outs if not o["primary"]]
    nd = lambda o: o.get("decimals")

    # ---- participants & baseline
    items: List[Any] = []
    ntot = sum(r["n_group"].values())
    nstr = T("、", ", ").join(f"{gl[g]} {r['n_group'][g]}" for g in order)
    comp = prim[0]["n_model"] if prim else 0
    items.append(("p", T(f"共纳入 {ntot} 名受试者（{nstr} 名）；{cx.olabel(prim[0], False)} 在基线与随访均有数据者 {comp} 名纳入主要分析。",
                         f"{ntot} participants were included ({nstr}); {comp} had both baseline and follow-up values for the primary outcome and entered the primary analysis.")))
    if r["baseline"]:
        header = [T("变量", "Variable")] + [f"{gl[g]} (n = {r['n_group'][g]})" for g in order] + [T("全体", "All")] + [f"SMD ({gl[a]} vs {gl[ctrl]})" if len(arms) > 1 else "SMD" for a in arms] + ["P"]
        rows = []
        imb = []
        for b in r["baseline"]:
            spec_v = next((v for v in s["baseline_vars"] if v["name"] == b["name"]), {})
            nm = cx.L(spec_v.get("label", b["name"]), b["name"])
            if b["kind"] == "cont":
                row = [nm] + [f"{fmt_num(b['groups'][g][0])} ± {fmt_num(b['groups'][g][1])}" for g in order] + [f"{fmt_num(b['total'][0])} ± {fmt_num(b['total'][1])}"] + \
                      [fmt_num(b["smd"][a], 2) for a in arms] + [fmt_p_table(b["p"])]
                if any(abs(b["smd"][a]) >= 0.5 for a in arms if np.isfinite(b["smd"][a])):
                    imb.append(nm)
                rows.append([cx.minus(x) for x in row])
            else:
                rows.append([nm + T("，n (%)", ", n (%)")] + [""] * (len(order) + 1) + [""] * len(arms) + [fmt_p_table(b["p"])])
                for lv, per in b["levels"].items():
                    rows.append(["   " + str(lv)] + [f"{k} ({100 * k / n:.0f}%)" if n else "—" for k, n in (per[g] for g in order)] +
                                [f"{b['total_levels'][lv][0]} ({100 * b['total_levels'][lv][0] / b['total_levels'][lv][1]:.0f}%)"] + [""] * len(arms) + [""])
        df1 = pd.DataFrame(rows, columns=header)
        items.append(("tab", df1, T("受试者基线特征", "Baseline characteristics of participants"),
                      T("连续变量为均值 ± SD，分类变量为 n (%)。SMD 为标准化均数差（对照组为参照）；P 值为 Welch t 检验/单因素方差分析（连续）或 Fisher 精确/χ² 检验（分类）。",
                        "Continuous variables are mean ± SD, categorical variables n (%). SMD, standardised mean difference versus control; P from Welch t / one-way ANOVA (continuous) or Fisher exact / χ² test (categorical).")))
        if imb:
            items.append(("p", T(f"按 |SMD| ≥ 0.5 判断，存在基线不均衡的变量为 {'、'.join(imb)}；主要分析已将基线值作为协变量。", f"Using |SMD| ≥ 0.5, baseline imbalance was present for {', '.join(imb)}; the primary analysis adjusts for the baseline value.")))
        else:
            items.append(("p", T("各基线变量 |SMD| 均小于 0.5，未见明显的基线不均衡。", "No baseline variable had |SMD| ≥ 0.5; there was no marked baseline imbalance.")))
    secs.append(dict(heading=T("参与者与基线特征", "Participants and baseline characteristics"), items=items))

    # ---- primary outcome(s)
    for o in prim:
        items = []
        un = o["unit"]
        for c in o["contrasts"]:
            a = c["arm"]
            d = o["desc"]
            dirw = T("高", "higher") if c["diff"] >= 0 else T("低", "lower")
            sg = _sig(c)
            items.append(("p", T(
                f"主要结局{cx.olabel(o, False)}：调整基线值后，{gl[a]}较{gl[ctrl]}平均{dirw} {cx.num(abs(c['diff']), nd(o))} {un}（{cx.ci(c['lo'], c['hi'], nd(o))}，{cx.P(c['p'])}"
                f"{'，' + cx.padj(c) if len(o['contrasts']) > 1 or len(prim) > 1 else ''}；Hedges g = {cx.num(c['g'], 2)}，基于变化量），差异{'具有' if sg else '未达'}统计学意义。",
                f"Primary outcome, {cx.olabel(o, False)}: adjusted for baseline, {gl[a]} was {cx.num(abs(c['diff']), nd(o))} {un} {dirw} than {gl[ctrl]} ({cx.ci(c['lo'], c['hi'], nd(o))}; {cx.P(c['p'])}"
                f"{'; ' + cx.padj(c) if len(o['contrasts']) > 1 or len(prim) > 1 else ''}; Hedges g = {cx.num(c['g'], 2)} on change scores); the difference {'was' if sg else 'was not'} statistically significant.")))
        wi = []
        for g in order:
            m = d[g]["chg"]
            wi.append(T(f"{gl[g]}由 {fmt_num(d[g]['pre'][0], nd(o))} 变为 {fmt_num(d[g]['post'][0], nd(o))}（变化 {cx.num(m[0], nd(o))}，{cx.ci(m[1], m[2], nd(o))}）",
                        f"{gl[g]} changed from {fmt_num(d[g]['pre'][0], nd(o))} to {fmt_num(d[g]['post'][0], nd(o))} (change {cx.num(m[0], nd(o))}; {cx.ci(m[1], m[2], nd(o))})"))
        items.append(("p", T("组内变化：" + "；".join(wi) + "。", "Within-group change: " + "; ".join(wi) + ".")))
        # figure
        w = o["_wide"]
        lg = pd.concat([pd.DataFrame({"id": w.index, "g": w["g"].map(gl).values, "t": 0, "y": w["pre"].values}),
                        pd.DataFrame({"id": w.index, "g": w["g"].map(gl).values, "t": 1, "y": w["post"].values})])
        fig = plt.figure(figsize=(DOUBLE, 3.2))
        gs = fig.add_gridspec(1, 3, width_ratios=[1.5, 1.0, 0.62 + 0.28 * len(arms)], wspace=0.42)
        a1, a2, a3 = (fig.add_subplot(gs[0, i]) for i in range(3))
        pf.ax_prepost(a1, lg, "id", "g", "t", "y", [gl[g] for g in order], {gl[g]: col[g] for g in order}, [cx.tlabel(t0), cx.tlabel(t1)], cx.olabel(o))
        panel_title(a1, "a", T("个体变化轨迹", "Individual trajectories"))
        pf.ax_raincloud(a2, {gl[g]: w[w["g"] == g]["chg"].dropna().values for g in order}, {gl[g]: col[g] for g in order}, ylabel=T("相对基线变化", "Change from baseline") + (f" ({un})" if un else ""))
        a2.axhline(0, color=C_GREY, lw=0.7, ls=(0, (3, 2)))
        panel_title(a2, "b", T("相对基线的变化", "Change from baseline"))
        dfe = max(o["n_model"] - len(arms) - 2, 1)
        rows = [dict(label=wrap_label(f"{gl[c['arm']]} − {gl[ctrl]}", 12), est=c["diff"], lo=c["lo"], hi=c["hi"], color=col[c["arm"]], df=dfe,
                     text=cx.minus(f"{fmt_num(c['diff'], nd(o))}\n[{fmt_num(c['lo'], nd(o))}, {fmt_num(c['hi'], nd(o))}]\n{cx.P(c['p'])}")) for c in o["contrasts"]]
        plots.diff_estimate(a3, rows, T("调整后组间差值", "Adjusted difference") + (f" ({un})" if un else ""), decimals=nd(o) or 2)
        panel_title(a3, "c", T("ANCOVA 估计", "ANCOVA estimate"))
        png = cx.save(fig, f"primary_{o['name']}")
        items.append(("fig", png, T(
            f"主要结局{cx.olabel(o, False)}。a，各受试者{cx.tlabel(t0)}与{cx.tlabel(t1)}观测值（细线）及组均值 ± SEM；b，相对基线的变化量（点为个体，曲线为分布密度，灰线为 IQR，菱形与竖线为均值 ± 95% CI）；"
            "c，以基线值为协变量的 ANCOVA 调整后组间差值：点与竖线为估计值及 95% CI，阴影为其抽样分布（t 分布），深色部分对应 95% CI。",
            f"Primary outcome, {cx.olabel(o, False)}. a, individual values at {cx.tlabel(t0)} and {cx.tlabel(t1)} (thin lines) with group mean ± SEM; b, change from baseline (points are participants, curve is the density, grey bar is the IQR, diamond and bar are mean ± 95% CI); "
            "c, ANCOVA-adjusted between-group difference (baseline as covariate): point and bar are the estimate and 95% CI, the shaded curve is its sampling distribution (t), darker inside the 95% CI.")))
        secs.append(dict(heading=T("主要结局：", "Primary outcome: ") + cx.olabel(o, False), items=items))

    # ---- all outcomes table + forest
    items = []
    hdr = [T("结局", "Outcome")] + sum(([f"{gl[g]} {cx.tlabel(t0)}", f"{gl[g]} {cx.tlabel(t1)}"] for g in order), []) + \
          [T("调整后差值 (95% CI)", "Adjusted difference (95% CI)"), "P", T("校正后 P", "Adj. P"), "Hedges g"]
    if len(arms) > 1:
        hdr.insert(1, T("对比", "Contrast"))
    rows, cats = [], []
    for o in outs:
        for c in o["contrasts"]:
            base = [cx.olabel(o)] + ([f"{gl[c['arm']]} − {gl[ctrl]}"] if len(arms) > 1 else [])
            cells = [f"{fmt_num(o['desc'][g][k][0], nd(o))} ± {fmt_num(o['desc'][g][k][1], nd(o))}" for g in order for k in ("pre", "post")]
            row = base + cells + [cx.cell_ci(c["diff"], c["lo"], c["hi"], nd(o)), fmt_p_table(c["p"]), fmt_p_table(c.get("p_adj")), cx.num(c["g"], 2)]
            rows.append([cx.minus(x) for x in row])
            cats.append(o["category"])
    df2 = pd.DataFrame(_cat_header_rows(rows, cats, len(hdr), cx), columns=hdr)
    items.append(("tab", df2, T("各结局的基线、随访值与组间比较", "Baseline, follow-up values and between-group comparisons for all outcomes"),
                  T("基线与随访为均值 ± SD。调整后差值为以基线值为协变量的 ANCOVA 估计（对比组 − 对照组）；Hedges g 基于变化量。校正后 P：主要结局 Holm，次要结局按类别 BH-FDR（q）。",
                    "Baseline and follow-up are mean ± SD. Adjusted difference is the ANCOVA estimate (comparison − control) with baseline as covariate; Hedges g is based on change scores. Adj. P: Holm for the primary outcome, Benjamini–Hochberg (q) within category for secondary outcomes.")))
    nsig = [(o, c) for o in sec for c in o["contrasts"] if _sig(c)]
    if sec:
        if nsig:
            lst = T("；", "; ").join(T(f"{cx.olabel(o, False)}（{gl[c['arm']]}较{gl[ctrl]}差值 {cx.num(c['diff'], nd(o))} {o['unit']}，{cx.padj(c)}）", f"{cx.olabel(o, False)} ({gl[c['arm']]} vs {gl[ctrl]} {cx.num(c['diff'], nd(o))} {o['unit']}; {cx.padj(c)})") for o, c in nsig)
            items.append(("p", T(f"在 {len(sec)} 个次要结局中，{len(nsig)} 项对比在按类别 BH 校正后差异有统计学意义：{lst}。其余次要结局差异未达统计学意义。次要结局仅作探索性解释。",
                                 f"Of {len(sec)} secondary outcomes, {len(nsig)} contrast(s) remained statistically significant after Benjamini–Hochberg adjustment within category: {lst}. The remaining secondary differences were not statistically significant. Secondary outcomes are exploratory.")))
        else:
            items.append(("p", T(f"{len(sec)} 个次要结局在按类别 BH 校正后均未达统计学意义，仅作探索性描述。", f"None of the {len(sec)} secondary outcomes reached statistical significance after Benjamini–Hochberg adjustment within category; they are reported as exploratory.")))
    rows_f, cat_list = [], []
    for o in outs:
        for c in o["contrasts"]:
            if o["category"] not in cat_list:
                cat_list.append(o["category"])
            sgn = o["orient"]
            rows_f.append(dict(category=cx.catlabel(o["category"]), label=cx.olabel(o, False) + (f" · {gl[c['arm']]}" if len(arms) > 1 else ""), g=float(np.clip(sgn * c["g"], -3, 3)),
                               lo=float(np.clip(min(sgn * c["glo"], sgn * c["ghi"]), -3, 3)), hi=float(np.clip(max(sgn * c["glo"], sgn * c["ghi"]), -3, 3)), sig=_sig(c), neutral=o.get("direction") == "neutral",
                               text=cx.minus(f"{c['g'] * sgn:.2f} ({min(sgn * c['glo'], sgn * c['ghi']):.2f}, {max(sgn * c['glo'], sgn * c['ghi']):.2f})")))
    png = _forest_std(cx, rows_f, cat_list, T("标准化效应量 Hedges g（正值 = 获益方向）", "Standardised effect, Hedges g (positive = favourable)"),
                      T("实心：校正后显著（主要 Holm，次要 BH）", "Filled: significant after adjustment (Holm primary, BH secondary)"), "forest_effects")
    items.append(("fig", png, T("全部结局的标准化效应量（Hedges g，95% CI）。", "Standardised effects (Hedges g, 95% CI) for all outcomes. ") + T("效应量已按获益方向统一；实心点表示按预设家族校正后 P < 0.05。", "Signs are oriented so that positive values are favourable; filled markers indicate adjusted P < 0.05 within the pre-specified family.")))
    if sec:
        fig, axs = plots.small_grid(len(sec[:9]), 2, cell=(3.6, 2.7))
        for k, (ax, o) in enumerate(zip(axs, sec[:9])):
            w = o["_wide"]
            lg = pd.concat([pd.DataFrame({"id": w.index, "g": w["g"].map(gl).values, "t": 0, "y": w["pre"].values}), pd.DataFrame({"id": w.index, "g": w["g"].map(gl).values, "t": 1, "y": w["post"].values})])
            pf.ax_prepost(ax, lg, "id", "g", "t", "y", [gl[g] for g in order], {gl[g]: col[g] for g in order}, [cx.tlabel(t0), cx.tlabel(t1)], cx.olabel(o), title=None)
            panel_title(ax, "abcdefghi"[k], cx.olabel(o, False))
        fig.subplots_adjust(wspace=0.55, hspace=0.6)
        png = cx.save(fig, "secondary_prepost")
        items.append(("fig", png, T("次要结局的个体变化与组均值 ± SEM。", "Individual changes and group mean ± SEM for secondary outcomes.")))
    secs.append(dict(heading=T("全部结局与次要结局", "All outcomes and secondary outcomes"), items=items))
    return secs


# ============================================================================ crossover
def build_crossover(cx: Ctx) -> List[Dict[str, Any]]:
    s, r, T = cx.spec, cx.res, cx.T
    conds, ctrl = r["conditions"], r["control"]
    arms = [c for c in conds if c != ctrl]
    col = _colors(conds, ctrl)
    cl = {c: cx.clabel(c) for c in conds}
    outs = r["outcomes"]
    prim = [o for o in outs if o["primary"]]
    sec = [o for o in outs if not o["primary"]]
    nd = lambda o: o.get("decimals")
    dose = {str(k): float(v) for k, v in s["conditions"].get("dose", {}).items()}
    dunit = cx.L(s["conditions"].get("dose_unit", ""), "")
    secs: List[Dict[str, Any]] = []

    items = [("p", T(f"{r['n_id']} 名受试者完成随机交叉设计，每名受试者按随机顺序完成 {len(conds)} 个条件（{'、'.join(cl[c] for c in conds)}）。"
                     f"{'模型调整了试验周期。' if r['period_adjusted'] else ''}缺失值由线性混合模型（受试者随机截距，REML）按可得数据处理。",
                     f"{r['n_id']} participants completed the randomised crossover, each undergoing {len(conds)} conditions ({', '.join(cl[c] for c in conds)}) in random order. "
                     f"{'The model was adjusted for period. ' if r['period_adjusted'] else ''}Missing values were handled under a linear mixed model (participant random intercept, REML) using all available data."))]
    secs.append(dict(heading=T("参与者与设计", "Participants and design"), items=items))

    for o in prim:
        items = []
        un = o["unit"]
        parts_zh, parts_en = [], []
        for c in o["contrasts"]:
            sg = _sig(c)
            dirw_zh, dirw_en = ("高", "higher") if c["diff"] >= 0 else ("低", "lower")
            parts_zh.append(f"{cl[c['arm']]}较{cl[ctrl]}{dirw_zh} {cx.num(abs(c['diff']), nd(o))} {un}（{cx.ci(c['lo'], c['hi'], nd(o))}，{cx.P(c['p'])}，{cx.padj(c)}；配对 d_z = {cx.num(c['dz'], 2)}）")
            parts_en.append(f"{cl[c['arm']]} was {cx.num(abs(c['diff']), nd(o))} {un} {dirw_en} than {cl[ctrl]} ({cx.ci(c['lo'], c['hi'], nd(o))}; {cx.P(c['p'])}; {cx.padj(c)}; paired d_z = {cx.num(c['dz'], 2)})")
        nall = all(_sig(c) for c in o["contrasts"])
        items.append(("p", T(f"主要结局{cx.olabel(o, False)}：" + "；".join(parts_zh) + f"。{'各干预条件校正后均有统计学意义。' if nall else '校正后并非所有条件均达统计学意义，见上。'}",
                             f"Primary outcome, {cx.olabel(o, False)}: " + "; ".join(parts_en) + f". {'Each active condition remained significant after adjustment.' if nall else 'Not every condition remained significant after adjustment; see above.'}")))
        for pr in o["pairs"]:
            items.append(("p", T(f"{cl[pr['a']]}与{cl[pr['b']]}相差 {cx.num(pr['diff'], nd(o))} {un}（{cx.ci(pr['lo'], pr['hi'], nd(o))}，{cx.P(pr['p'])}，Holm 校正后 P {'< 0.001' if pr['p_adj'] < 0.001 else '= ' + format(pr['p_adj'], '.3f')}），差异{'有' if pr['p_adj'] < 0.05 else '未达'}统计学意义；未检出差异不等同于等效，如需推断等效需另行做等效性检验。",
                                 f"{cl[pr['a']]} and {cl[pr['b']]} differed by {cx.num(pr['diff'], nd(o))} {un} ({cx.ci(pr['lo'], pr['hi'], nd(o))}; {cx.P(pr['p'])}; Holm P {'< 0.001' if pr['p_adj'] < 0.001 else '= ' + format(pr['p_adj'], '.3f')}); the difference {'was' if pr['p_adj'] < 0.05 else 'was not'} statistically significant. "
                                 f"A non-significant difference does not establish equivalence; an equivalence test is required for that claim.")))
        if "trend" in o:
            tr_ = o["trend"]
            items.append(("p", T(f"剂量—反应：{'每增加 1 ' + dunit if dunit else '每增加 1 个剂量单位'}，{cx.olabel(o, False)}平均变化 {cx.num(tr_['est'], 3)} {un}（{cx.ci(tr_['lo'], tr_['hi'], 3)}，{cx.P(tr_['p'])}）。",
                                 f"Dose–response: per 1 {dunit or 'dose unit'}, {cx.olabel(o, False)} changed by {cx.num(tr_['est'], 3)} {un} ({cx.ci(tr_['lo'], tr_['hi'], 3)}; {cx.P(tr_['p'])}).")))
        wide = o["_wide"]
        has_dose = "trend" in o
        fig = plt.figure(figsize=(DOUBLE, 3.2))
        gs = fig.add_gridspec(1, 3 if has_dose else 2, width_ratios=[1.3, 0.95, 0.85] if has_dose else [1.35, 1.2], wspace=0.95 if has_dose else 0.7)
        a1, a2 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
        pf.ax_paired_estimate(a1, wide, conds, col, o["emm"], cx.olabel(o), label_map=cl)
        panel_title(a1, "a", T("个体观测与模型估计", "Participants and model estimates"))
        rows = [dict(label=cl[c["arm"]], est=c["diff"], lo=c["lo"], hi=c["hi"], color=col[c["arm"]],
                     text=cx.minus(f"{fmt_num(c['diff'], nd(o))} ({fmt_num(c['lo'], nd(o))}, {fmt_num(c['hi'], nd(o))})\n{cx.padj(c)}")) for c in o["contrasts"]]
        for pr in o["pairs"]:
            rows.append(dict(label=f"{cl[pr['a']]} − {cl[pr['b']]}", est=pr["diff"], lo=pr["lo"], hi=pr["hi"], color=C_GREY, hollow=True,
                             text=cx.minus(f"{fmt_num(pr['diff'], nd(o))} ({fmt_num(pr['lo'], nd(o))}, {fmt_num(pr['hi'], nd(o))})\nHolm P {'< 0.001' if pr['p_adj'] < 0.001 else '= ' + format(pr['p_adj'], '.3f')}")))
        plots.est_forest(a2, rows, T("较对照的差值", "Difference vs control") + (f" ({un})" if un else ""), decimals=nd(o) or 2, text_x=1.04)
        panel_title(a2, "b", T("条件间差值", "Contrasts"), dx=-0.55)
        if has_dose:
            a3 = fig.add_subplot(gs[0, 2])
            dd = {cl[c]: dict(x=dose[c], diffs=(wide[c] - wide[ctrl]).dropna().values, est=o["emm"][c][0] - o["emm"][ctrl][0], lo=[x for x in [next(k for k in o["contrasts"] if k["arm"] == c)]][0]["lo"],
                              hi=next(k for k in o["contrasts"] if k["arm"] == c)["hi"]) for c in arms if c in dose}
            pf.ax_dose_response(a3, dd, {cl[c]: col[c] for c in arms if c in dose}, (T("剂量", "Dose") + (f" ({dunit})" if dunit else "")), T("相对对照的差值", "Difference vs control") + (f" ({un})" if un else ""),
                                trend=(o["trend"]["est"], 0.0), xtick_labels={cl[c]: f"{dose[c]:g}" for c in arms if c in dose})
            panel_title(a3, "c", T("剂量–反应", "Dose–response"))
        png = cx.save(fig, f"primary_{o['name']}")
        items.append(("fig", png, T(
            f"主要结局{cx.olabel(o, False)}。a，各条件观测值（点；灰线连接同一受试者）与混合模型估计边际均值 ± 95% CI；b，各条件较对照的差值及 95% CI（实心为校正后 P，空心菱形为预设两两比较）；" + ("c，剂量—反应（点为个体差值，虚线为线性趋势）。" if has_dose else ""),
            f"Primary outcome, {cx.olabel(o, False)}. a, observed values per condition (points; grey lines join each participant) with mixed-model estimated marginal means ± 95% CI; b, differences versus control with 95% CI (filled: adjusted P; open diamond: pre-specified pairwise); " + ("c, dose–response (points are individual differences; dashed line is the linear trend)." if has_dose else ""))))
        secs.append(dict(heading=T("主要结局：", "Primary outcome: ") + cx.olabel(o, False), items=items))

    items = []
    hdr = [T("结局", "Outcome")] + [cl[c] for c in conds]
    rows, cats = [], []
    for o in outs:
        rows.append([cx.olabel(o)] + [cx.cell_ci(*o["emm"][c], nd(o)) for c in conds])
        cats.append(o["category"])
    items.append(("tab", pd.DataFrame(_cat_header_rows(rows, cats, len(hdr), cx), columns=hdr), T("各条件下的估计边际均值", "Estimated marginal means by condition"),
                  T("线性混合模型（受试者随机截距）估计的边际均值（95% CI）。", "Estimated marginal means (95% CI) from a linear mixed model with a participant random intercept.")))
    hdr = [T("结局", "Outcome"), T("对比", "Contrast"), T("差值 (95% CI)", "Difference (95% CI)"), T("变化 (%)", "Change (%)"), "P", T("校正后 P", "Adj. P"), "d_z"]
    rows, cats = [], []
    for o in outs:
        for c in o["contrasts"]:
            rows.append([cx.olabel(o), f"{cl[c['arm']]} − {cl[ctrl]}", cx.cell_ci(c["diff"], c["lo"], c["hi"], nd(o)), cx.num(c["pct"], 0), fmt_p_table(c["p"]), fmt_p_table(c["p_adj"]), cx.num(c["dz"], 2)])
            cats.append(o["category"])
    items.append(("tab", pd.DataFrame(_cat_header_rows(rows, cats, len(hdr), cx), columns=hdr), T("各条件较对照的差值", "Differences between each condition and control"),
                  T("差值与 P 值来自线性混合模型的预设对比（Wald t，自由度 n−1）；校正后 P：主要结局 Holm，次要结局按类别 BH。d_z 为配对效应量。", "Differences and P from pre-specified contrasts of the linear mixed model (Wald t, n−1 df). Adj. P: Holm for the primary outcome, Benjamini–Hochberg within category for secondary outcomes. d_z, paired effect size.")))
    if sec:
        nsig = [(o, c) for o in sec for c in o["contrasts"] if _sig(c)]
        lst = T("；", "; ").join(_trunc([T(f"{cx.olabel(o, False)}（{cl[c['arm']]}，{cx.num(c['diff'], nd(o))} {o['unit']}，{cx.padj(c)}）", f"{cx.olabel(o, False)} ({cl[c['arm']]}, {cx.num(c['diff'], nd(o))} {o['unit']}; {cx.padj(c)})") for o, c in nsig]))
        items.append(("p", T(f"次要结局中，{len(nsig)}/{sum(len(o['contrasts']) for o in sec)} 项对比校正后差异有统计学意义" + (f"：{lst}" if nsig else "") + "。次要结局仅作探索性解释。",
                             f"Among secondary outcomes, {len(nsig)}/{sum(len(o['contrasts']) for o in sec)} contrasts remained significant after adjustment" + (f": {lst}" if nsig else "") + ". Secondary outcomes are exploratory.")))
    rows_f, cat_list = [], []
    for o in outs:
        for c in o["contrasts"]:
            if o["category"] not in cat_list:
                cat_list.append(o["category"])
            n = o["n_id"]
            se = np.sqrt(1 / n + c["dz"] ** 2 / (2 * n)) if np.isfinite(c["dz"]) else np.nan
            sgn = o["orient"]
            g, lo, hi = sgn * c["dz"], sgn * c["dz"] - 1.96 * se, sgn * c["dz"] + 1.96 * se
            rows_f.append(dict(category=cx.catlabel(o["category"]), label=f"{cx.olabel(o, False)} · {cl[c['arm']]}", g=float(np.clip(g, -3, 3)), lo=float(np.clip(lo, -3, 3)), hi=float(np.clip(hi, -3, 3)),
                               sig=_sig(c), neutral=False, text=cx.minus(f"{g:.2f} ({lo:.2f}, {hi:.2f})")))
    png = _forest_std(cx, rows_f, cat_list, T("配对效应量 d_z（正值 = 获益方向）", "Paired effect size d_z (positive = favourable)"),
                      T("实心：校正后显著（主要 Holm，次要 BH）；d_z 的 CI 为近似值", "Filled: significant after adjustment (Holm primary, BH secondary); CI of d_z is approximate"), "forest_effects")
    items.append(("fig", png, T("各结局各条件较对照的配对效应量（d_z，近似 95% CI）。", "Paired effect sizes (d_z, approximate 95% CI) of each condition versus control for all outcomes.")))
    secs.append(dict(heading=T("全部结局", "All outcomes"), items=items))
    return secs


# ============================================================================ multitime
def build_multitime(cx: Ctx) -> List[Dict[str, Any]]:
    s, r, T = cx.spec, cx.res, cx.T
    order, ctrl, arms, times = r["groups"], r["control"], r["arms"], r["times"]
    pt = r["primary_time"]
    col = _colors(order, ctrl)
    gl = {g: cx.glabel(g) for g in order}
    tl = [cx.tlabel(t) for t in times]
    outs = r["outcomes"]
    prim = [o for o in outs if o["primary"]]
    sec = [o for o in outs if not o["primary"]]
    nd = lambda o: o.get("decimals")
    df = r["_long"].copy()
    c = s["columns"]
    dfl = df.copy()
    dfl[c["group"]] = dfl[c["group"]].map(gl)
    secs: List[Dict[str, Any]] = []
    ntot = sum(r["n_group"].values())
    items = [("p", T(f"共 {ntot} 名受试者（{'、'.join(f'{gl[g]} {r['n_group'][g]}' for g in order)}），在 {len(times)} 个时点（{'、'.join(tl)}）接受测量；采用{'约束基线的' if r['constrained'] else ''}纵向线性混合模型（受试者随机截距，组 × 时间）分析，以所有可得数据估计，主要时点为{cx.tlabel(pt)}。",
                     f"{ntot} participants ({', '.join(f'{gl[g]} {r['n_group'][g]}' for g in order)}) were assessed at {len(times)} time points ({', '.join(tl)}). A {'constrained-baseline ' if r['constrained'] else ''}longitudinal linear mixed model (participant random intercept, group × time) used all available data; the primary time point was {cx.tlabel(pt)}."))]
    if r["baseline"]:
        header = [T("变量", "Variable")] + [f"{gl[g]} (n = {r['n_group'][g]})" for g in order] + [T("全体", "All"), "P"]
        rows = []
        for b in r["baseline"]:
            v = next((v for v in s["baseline_vars"] if v["name"] == b["name"]), {})
            nm = cx.L(v.get("label", b["name"]), b["name"])
            if b["kind"] == "cont":
                rows.append([cx.minus(x) for x in [nm] + [f"{fmt_num(b['groups'][g][0])} ± {fmt_num(b['groups'][g][1])}" for g in order] + [f"{fmt_num(b['total'][0])} ± {fmt_num(b['total'][1])}", fmt_p_table(b["p"])]])
            else:
                rows.append([nm + T("，n (%)", ", n (%)")] + [""] * (len(order) + 1) + [fmt_p_table(b["p"])])
                for lv, per in b["levels"].items():
                    rows.append(["   " + str(lv)] + [f"{k} ({100 * k / n:.0f}%)" if n else "—" for k, n in (per[g] for g in order)] + [f"{b['total_levels'][lv][0]} ({100 * b['total_levels'][lv][0] / b['total_levels'][lv][1]:.0f}%)", ""])
        items.append(("tab", pd.DataFrame(rows, columns=header), T("受试者基线特征", "Baseline characteristics of participants"), T("连续变量为均值 ± SD，分类变量为 n (%)。", "Continuous variables mean ± SD; categorical variables n (%).")))
    secs.append(dict(heading=T("参与者与基线特征", "Participants and baseline characteristics"), items=items))

    def traj_fig(o, ax, indiv=0.12, labels=True):
        pf.ax_multitime(ax, dfl, c["id"], c["group"], c["time"], o["column"], [gl[g] for g in order], {gl[g]: col[g] for g in order}, times, tl, cx.olabel(o),
                        indiv_alpha=indiv, band=True, dashed=[gl[ctrl]], direct_labels={gl[g]: gl[g] for g in order} if labels else None)
        ax.set_xlim(-0.25, len(times) - 1 + (0.75 if labels else 0.25))

    for o in prim:
        items = []
        un = o["unit"]
        for ct in [k for k in o["contrasts"] if k["time"] == pt]:
            sg = _sig(ct)
            dirw = T("高", "higher") if ct["diff"] >= 0 else T("低", "lower")
            items.append(("p", T(f"主要结局{cx.olabel(o, False)}：{cx.tlabel(pt)}时，{gl[ct['arm']]}较{gl[ctrl]}平均{dirw} {cx.num(abs(ct['diff']), nd(o))} {un}（{cx.ci(ct['lo'], ct['hi'], nd(o))}，{cx.P(ct['p'])}，{cx.padj(ct)}），差异{'具有' if sg else '未达'}统计学意义；组 × 时间交互 {cx.P(o['p_group_time'])}。",
                                 f"Primary outcome, {cx.olabel(o, False)}: at {cx.tlabel(pt)}, {gl[ct['arm']]} was {cx.num(abs(ct['diff']), nd(o))} {un} {dirw} than {gl[ctrl]} ({cx.ci(ct['lo'], ct['hi'], nd(o))}; {cx.P(ct['p'])}; {cx.padj(ct)}); the difference {'was' if sg else 'was not'} statistically significant; group × time interaction {cx.P(o['p_group_time'])}.")))
        earlier = [k for k in o["contrasts"] if k["time"] != pt]
        if earlier:
            lst = T("；", "; ").join(f"{cx.tlabel(k['time'])}: {cx.num(k['diff'], nd(o))} ({cx.num(k['lo'], nd(o))}～{cx.num(k['hi'], nd(o))}; {cx.P(k['p'])})" if cx.lang == "zh" else f"{cx.tlabel(k['time'])}: {cx.num(k['diff'], nd(o))} ({cx.num(k['lo'], nd(o))} to {cx.num(k['hi'], nd(o))}; {cx.P(k['p'])})" for k in earlier)
            items.append(("p", T(f"其他时点的组间差值（未校正，仅作描述）：{lst}。", f"Between-group differences at the other time points (unadjusted, descriptive): {lst}.")))
        fig = plt.figure(figsize=(DOUBLE, 3.1))
        gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1.0], wspace=0.32)
        a1, a2 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
        traj_fig(o, a1)
        panel_title(a1, "a", T("各组时间进程", "Time course by group"))
        post = times[1:]
        xs = np.arange(len(times))
        for a in arms:
            ks = [next(k for k in o["contrasts"] if k["arm"] == a and k["time"] == t) for t in post]
            d = np.array([0.0] + [k["diff"] for k in ks])
            lo_ = np.array([0.0] + [k["lo"] for k in ks])
            hi_ = np.array([0.0] + [k["hi"] for k in ks])
            a2.fill_between(xs, lo_, hi_, color=col[a], alpha=0.16, lw=0)
            a2.plot(xs, d, "-", color=col[a], lw=1.9)
            a2.plot(xs[1:], d[1:], "o", ms=5, color=col[a], mec="white", mew=0.8, zorder=4)
            for x_, k in zip(xs[1:], ks):
                a2.annotate(cx.minus(f"{fmt_num(k['diff'], nd(o))}\n{cx.P(k['p'])}"), xy=(x_, k["hi"]), xytext=(0, 3), textcoords="offset points",
                            ha="center", va="bottom", fontsize=5.4, color=C_INK if k["time"] == pt else C_GREY, fontweight="bold" if k["time"] == pt else "normal")
        a2.axhline(0, color=C_GREY, lw=0.8, ls=(0, (3, 2)))
        a2.annotate(T("无差异", "no difference"), xy=(len(times) - 1, 0), xytext=(0, -3), textcoords="offset points", fontsize=5.4, color=C_GREY, ha="right", va="top")
        a2.set_xticks(xs)
        a2.set_xticklabels(tl)
        a2.tick_params(axis="x", length=0)
        a2.set_ylabel(T(f"组间差值 ({gl[arms[0]]} − {gl[ctrl]})", f"Difference ({gl[arms[0]]} − {gl[ctrl]})") + (f", {un}" if un else "") if len(arms) == 1 else T("组间差值", "Between-group difference") + (f" ({un})" if un else ""))
        lo_all, hi_all = a2.get_ylim()
        a2.set_ylim(lo_all, hi_all + 0.12 * (hi_all - lo_all))
        hair_y(a2)
        panel_title(a2, "b", T("混合模型组间差值", "Model-based difference"))
        png = cx.save(fig, f"primary_{o['name']}")
        items.append(("fig", png, T(f"主要结局{cx.olabel(o, False)}的时间进程。a，各时点组均值（线）及 95% CI（阴影），浅色细线为个体轨迹，对照组为虚线；b，混合模型估计的各时点组间差值（线）及 95% CI（阴影），加粗标注为主要时点（{cx.tlabel(pt)}）。",
                                    f"Time course of the primary outcome, {cx.olabel(o, False)}. a, group means (lines) with 95% CI (shading); faint lines are individual trajectories, control dashed; b, mixed-model between-group difference (line) with 95% CI (shading); the primary time point ({cx.tlabel(pt)}) is labelled in bold.")))
        secs.append(dict(heading=T("主要结局：", "Primary outcome: ") + cx.olabel(o, False), items=items))

    items = []
    hdr = [T("结局", "Outcome"), T("组别", "Group")] + tl
    rows, cats = [], []
    for o in outs:
        for g in order:
            rows.append([cx.olabel(o), gl[g]] + [cx.minus(f"{fmt_num(o['desc'][g][t][0], nd(o))} ± {fmt_num(o['desc'][g][t][1], nd(o))}") for t in times])
            cats.append(o["category"])
    items.append(("tab", pd.DataFrame(_cat_header_rows(rows, cats, len(hdr), cx), columns=hdr), T("各时点观测值", "Observed values at each time point"), T("均值 ± SD（可得数据）。", "Mean ± SD (available data).")))
    hdr = [T("结局", "Outcome")] + ([T("对比", "Contrast")] if len(arms) > 1 else []) + [f"{tl[times.index(t)]}" for t in times[1:]] + [T("组×时间 P", "Group × time P"), T(f"校正后 P（{cx.tlabel(pt)}）", f"Adj. P ({cx.tlabel(pt)})")]
    rows, cats = [], []
    for o in outs:
        for a in arms:
            cs = {k["time"]: k for k in o["contrasts"] if k["arm"] == a}
            rows.append([cx.olabel(o)] + ([f"{gl[a]} − {gl[ctrl]}"] if len(arms) > 1 else []) + [cx.cell_ci(cs[t]["diff"], cs[t]["lo"], cs[t]["hi"], nd(o)) for t in times[1:]] +
                        [fmt_p_table(o.get("p_group_time")), fmt_p_table(cs[pt].get("p_adj"))])
            cats.append(o["category"])
    items.append(("tab", pd.DataFrame(_cat_header_rows(rows, cats, len(hdr), cx), columns=hdr), T("各时点的组间差值", "Between-group differences at each follow-up"),
                  T("线性混合模型估计，差值（95% CI）= 对比组 − 对照组。校正后 P 仅针对主要时点：主要结局 Holm，次要结局按类别 BH；其余时点未校正。", "Linear mixed model; difference (95% CI) = comparison − control. Adjusted P applies to the primary time point only (Holm for primary, Benjamini–Hochberg within category for secondary outcomes); other time points are unadjusted.")))
    nsig = [(o, k) for o in sec for k in o["contrasts"] if k["time"] == pt and _sig(k)]
    if sec:
        lst = T("；", "; ").join(T(f"{cx.olabel(o, False)}（{cx.num(k['diff'], nd(o))} {o['unit']}，{cx.padj(k)}）", f"{cx.olabel(o, False)} ({cx.num(k['diff'], nd(o))} {o['unit']}; {cx.padj(k)})") for o, k in nsig)
        items.append(("p", T(f"次要结局中，{cx.tlabel(pt)}时有 {len(nsig)} 项对比校正后差异有统计学意义" + (f"：{lst}" if nsig else "") + "。次要结局仅作探索性解释。",
                             f"Among secondary outcomes, {len(nsig)} contrast(s) at {cx.tlabel(pt)} remained significant after adjustment" + (f": {lst}" if nsig else "") + ". Secondary outcomes are exploratory.")))
    if sec:
        fig, axs = plots.small_grid(len(sec[:9]), 2, cell=(3.6, 2.6))
        for k, (ax, o) in enumerate(zip(axs, sec[:9])):
            traj_fig(o, ax, 0.07, labels=k == 0)
            panel_title(ax, "abcdefghi"[k], cx.olabel(o, False))
        fig.subplots_adjust(wspace=0.5, hspace=0.6)
        png = cx.save(fig, "secondary_traj")
        items.append(("fig", png, T("次要结局的时间进程（组均值及 95% CI 阴影，对照组为虚线）。", "Time course of secondary outcomes (group means with shaded 95% CI; control dashed).")))
    rows_f, cat_list = [], []
    for o in outs:
        for k in [x for x in o["contrasts"] if x["time"] == pt]:
            if o["category"] not in cat_list:
                cat_list.append(o["category"])
            sgn = o["orient"]
            se = np.sqrt(1 / max(r["n_group"][k["arm"]], 2) + 1 / max(r["n_group"][ctrl], 2))
            g = sgn * k["g"]
            lo, hi = g - 1.96 * se, g + 1.96 * se
            rows_f.append(dict(category=cx.catlabel(o["category"]), label=cx.olabel(o, False) + (f" · {gl[k['arm']]}" if len(arms) > 1 else ""), g=float(np.clip(g, -3, 3)), lo=float(np.clip(lo, -3, 3)), hi=float(np.clip(hi, -3, 3)),
                               sig=_sig(k), neutral=False, text=cx.minus(f"{g:.2f} ({lo:.2f}, {hi:.2f})")))
    png = _forest_std(cx, rows_f, cat_list, T(f"{cx.tlabel(pt)}时标准化组间差 (g，正值 = 获益方向)", f"Standardised between-group difference at {cx.tlabel(pt)} (g; positive = favourable)"),
                      T("实心：校正后显著（主要 Holm，次要 BH）；CI 为近似值", "Filled: significant after adjustment (Holm primary, BH secondary); CI approximate"), "forest_effects")
    items.append(("fig", png, T(f"{cx.tlabel(pt)}时各结局的标准化组间差。", f"Standardised between-group differences at {cx.tlabel(pt)} for all outcomes.")))
    secs.append(dict(heading=T("全部结局", "All outcomes"), items=items))
    return secs


# ============================================================================ meta-analysis
def build_meta(cx: Ctx) -> List[Dict[str, Any]]:
    s, r, T = cx.spec, cx.res, cx.T
    m = s.get("meta", {})
    d = r["studies"]
    P = r["pooled"]
    eff = {"smd": T("标准化均数差 (Hedges g)", "Standardised mean difference (Hedges g)"), "md": T("均数差 (MD)", "Mean difference (MD)"), "generic": T("效应量", "Effect size")}[r["effect"]]
    oname = cx.L(m.get("outcome_label", ""), "")
    secs: List[Dict[str, Any]] = []
    ntot = int((d["n1"] + d["n2"]).sum()) if "n1" in d else None
    meth = T("DerSimonian–Laird 随机效应模型" + ("，Hartung–Knapp 调整的置信区间" if r["hksj"] else ""), "DerSimonian–Laird random-effects model" + (" with Hartung–Knapp-adjusted confidence intervals" if r["hksj"] else ""))
    fav = {"lower_better": T("正值表示干预使结局降低（获益）", "positive values indicate a reduction in the outcome (favourable)")}.get(m.get("direction"), T("正值表示干预组更高", "positive values favour the higher value in the intervention arm"))
    items = [("p", T(f"共纳入 {r['k']} 项研究" + (f"，合计 {ntot} 名受试者" if ntot else "") + f"。效应量为{eff}，{fav}；采用{meth}合并。",
                     f"{r['k']} studies" + (f" with {ntot} participants in total" if ntot else "") + f" were included. The effect measure was the {eff}; {fav}. Studies were pooled with a {meth}."))]
    hdr = [T("研究", "Study")] + ([T("干预组 n", "n (int.)"), T("对照组 n", "n (ctrl.)")] if "n1" in d else []) + ([T("亚组", "Subgroup")] if "subgroup" in d else []) + ([T("调节变量", "Moderator")] if "moderator" in d else []) + [f"{eff.split(' ')[0] if r['effect'] != 'smd' else 'g'} (95% CI)", T("权重 (%)", "Weight (%)")]
    rows = []
    for _, x in d.iterrows():
        rows.append([str(x["study"])] + ([str(int(x["n1"])), str(int(x["n2"]))] if "n1" in d else []) + ([str(x["subgroup"])] if "subgroup" in d else []) + ([fmt_num(x["moderator"], 0)] if "moderator" in d else []) +
                    [cx.cell_ci(x["es"], x["lo"], x["hi"], 2), f"{x['w']:.1f}"])
    items.append(("tab", pd.DataFrame(rows, columns=hdr), T("纳入研究的特征与效应量", "Characteristics and effect sizes of included studies"), T("效应量已按获益方向统一；权重来自随机效应模型。", "Effect sizes are oriented so that positive values are favourable; weights are from the random-effects model.")))
    pi = P.get("pi")
    sg = P["p"] < 0.05
    items.append(("p", T(f"随机效应合并{eff.split('(')[0].strip()}{oname and '（' + oname + '）'}为 {cx.num(P['est'], 2)}（{cx.ci(P['lo'], P['hi'], 2)}，{cx.P(P['p'])}），合并效应{'具有' if sg else '未达'}统计学意义。"
                         f"研究间异质性 I² = {P['I2']:.0f}%，τ² = {P['tau2']:.3f}，Q 检验 {cx.P(P['Qp'])}" + (f"；95% 预测区间 {cx.num(pi[0], 2)}～{cx.num(pi[1], 2)}" if pi else "") + "。",
                         f"The pooled {eff.split('(')[0].strip().lower()}{oname and ' for ' + oname} was {cx.num(P['est'], 2)} ({cx.ci(P['lo'], P['hi'], 2)}; {cx.P(P['p'])}); the pooled effect {'was' if sg else 'was not'} statistically significant. "
                         f"Between-study heterogeneity was I² = {P['I2']:.0f}%, τ² = {P['tau2']:.3f}, Q test {cx.P(P['Qp'])}" + (f"; the 95% prediction interval was {cx.num(pi[0], 2)} to {cx.num(pi[1], 2)}" if pi else "") + ".")))
    subs = r.get("subgroups")
    sub_colors = None
    if subs:
        sub_colors = {sub["level"]: CAT_COLORS[i % len(CAT_COLORS)] for i, sub in enumerate(subs)}
        qb = r["Q_between"]
        sl = cx.L(m.get("subgroup_label", ""), T("亚组", "subgroup"))
        txt_zh = "；".join(f"{sub['level']}（k = {sub['k']}）{cx.num(sub['est'], 2)}（{cx.ci(sub['lo'], sub['hi'], 2)}）" for sub in subs)
        txt_en = "; ".join(f"{sub['level']} (k = {sub['k']}) {cx.num(sub['est'], 2)} ({cx.ci(sub['lo'], sub['hi'], 2)})" for sub in subs)
        items.append(("p", T(f"按{sl}的亚组分析：{txt_zh}；亚组间差异检验 Q = {qb['Q']:.2f}，df = {qb['df']}，{cx.P(qb['p'])}。亚组分析为探索性。",
                             f"Subgroup analysis by {sl}: {txt_en}; test for subgroup differences Q = {qb['Q']:.2f}, df = {qb['df']}, {cx.P(qb['p'])}. Subgroup analyses are exploratory.")))
    fig = plots.meta_forest(d, P, T(f"{eff}（正值 = 获益）", f"{eff} (positive = favourable)"), T("研究", "Study"), T("效应量 (95% CI)", "Effect (95% CI)"), T("随机效应合并", "Random-effects pooled"),
                            f"I² = {P['I2']:.0f}%, τ² = {P['tau2']:.3f}, Q {cx.P(P['Qp'])}", subs=subs, sub_col="subgroup" if subs else None, sub_colors=sub_colors,
                            favour=(T("← 对照更优", "← Favours control"), T("干预更优 →", "Favours intervention →")))
    png = cx.save(fig, "forest")
    items.append(("fig", png, T("各研究效应量与随机效应合并结果的森林图。方块面积与权重成正比，菱形为合并估计及 95% CI" + ("，颜色区分亚组" if subs else "") + "。", "Forest plot of study effect sizes and the random-effects pooled estimate. Square area is proportional to weight; diamonds are pooled estimates with 95% CI" + ("; colours denote subgroups" if subs else "") + ".")))
    secs.append(dict(heading=T("合并效应与异质性", "Pooled effect and heterogeneity"), items=items))

    items = []
    eg = r["egger"]
    if eg:
        items.append(("p", T(f"漏斗图目测{'基本对称' if eg['p'] >= 0.1 else '存在不对称'}；Egger 回归截距 {cx.num(eg['intercept'], 2)}（{cx.P(eg['p'])}）。", f"The funnel plot looked {'broadly symmetric' if eg['p'] >= 0.1 else 'asymmetric'}; Egger regression intercept {cx.num(eg['intercept'], 2)} ({cx.P(eg['p'])}).")))
    else:
        items.append(("p", T(f"纳入研究少于 10 项（k = {r['k']}），未做 Egger 检验，漏斗图仅供目测，发表偏倚评估把握有限。", f"With fewer than 10 studies (k = {r['k']}) the Egger test was not performed; the funnel plot is shown for visual inspection and the assessment of publication bias is limited.")))
    if r["loo"]:
        lo_ = [x["est"] for x in r["loo"]]
        items.append(("p", T(f"留一法敏感性分析显示合并效应在 {cx.num(min(lo_), 2)} 至 {cx.num(max(lo_), 2)} 之间，{'每次剔除后 95% CI 均不跨 0' if all(x['lo'] > 0 or x['hi'] < 0 for x in r['loo']) else '部分剔除后 95% CI 跨越 0'}。",
                             f"Leave-one-out analysis gave pooled estimates between {cx.num(min(lo_), 2)} and {cx.num(max(lo_), 2)}; {'the 95% CI excluded zero after every omission' if all(x['lo'] > 0 or x['hi'] < 0 for x in r['loo']) else 'the 95% CI included zero after some omissions'}.")))
    mr = r.get("metareg")
    if mr:
        ml = cx.L(m.get("moderator_label", ""), mr["name"] or "")
        items.append(("p", T(f"以{ml}为调节变量的 meta 回归（k = {mr['k']}）：每增加 1 个单位，效应量变化 {cx.num(mr['slope'], 3)}（{cx.ci(mr['lo'], mr['hi'], 3)}，{cx.P(mr['p'])}）；该分析为探索性，且仅为研究水平关联。",
                             f"Meta-regression on {ml} (k = {mr['k']}): per 1-unit increase the effect size changed by {cx.num(mr['slope'], 3)} ({cx.ci(mr['lo'], mr['hi'], 3)}; {cx.P(mr['p'])}); this analysis is exploratory and reflects study-level association only.")))
    npan = 1 + (1 if mr else 0) + (1 if r["loo"] else 0)
    fig = plt.figure(figsize=(DOUBLE, 2.9))
    gs = fig.add_gridspec(1, npan, wspace=0.75, width_ratios=[1.0] * npan)
    axs = [fig.add_subplot(gs[0, i]) for i in range(npan)]
    plots.funnel(axs[0], d["es"].values, d["se"].values, P["est"], T(f"{eff.split('(')[0].strip()}", eff.split("(")[0].strip()), T("标准误", "Standard error"))
    panel_title(axs[0], "a", T("漏斗图", "Funnel plot"))
    i = 1
    if mr:
        plots.bubble_metareg(axs[i], pd.to_numeric(d["moderator"]).values, d["es"].values, d["w"].values, mr, cx.L(m.get("moderator_label", ""), "moderator"), T("效应量", "Effect size"))
        panel_title(axs[i], "b", T("meta 回归", "Meta-regression"))
        i += 1
    if r["loo"]:
        rows = [dict(label=x["omit"], est=x["est"], lo=x["lo"], hi=x["hi"], color=C_SLATE, text="") for x in r["loo"]]
        plots.est_forest(axs[i], rows, T("剔除该研究后的合并效应", "Pooled effect omitting study"), decimals=2, text_x=1.02)
        for tl_ in axs[i].get_yticklabels():
            tl_.set_fontsize(4.8)
        panel_title(axs[i], "c" if mr else "b", T("留一法", "Leave-one-out"))
    png = cx.save(fig, "funnel_sensitivity")
    items.append(("fig", png, T("发表偏倚与敏感性分析。a，漏斗图；" + ("b，meta 回归气泡图（面积 ∝ 权重）；" if mr else "") + (("c，" if mr else "b，") + "留一法敏感性分析。" if r["loo"] else ""),
                                "Publication bias and sensitivity analyses. a, funnel plot; " + ("b, meta-regression bubble plot (area ∝ weight); " if mr else "") + (("c, " if mr else "b, ") + "leave-one-out sensitivity analysis." if r["loo"] else ""))))
    rows = [[T("研究数 k", "Studies, k"), str(P["k"])], [T("合并效应 (95% CI)", "Pooled effect (95% CI)"), cx.cell_ci(P["est"], P["lo"], P["hi"], 2)], ["P", fmt_p_table(P["p"])],
            ["I² (%)", f"{P['I2']:.0f}"], ["τ²", f"{P['tau2']:.3f}"], [T("Q 检验 P", "Q test P"), fmt_p_table(P["Qp"])]]
    if pi:
        rows.append([T("95% 预测区间", "95% prediction interval"), cx.minus(f"({pi[0]:.2f}, {pi[1]:.2f})")])
    for sub in subs or []:
        rows.append([f"{T('亚组', 'Subgroup')}: {sub['level']} (k = {sub['k']})", cx.cell_ci(sub["est"], sub["lo"], sub["hi"], 2)])
    if subs:
        rows.append([T("亚组间 Q 检验 P", "Between-subgroup Q test P"), fmt_p_table(r["Q_between"]["p"])])
    if eg:
        rows.append([T("Egger 截距 (P)", "Egger intercept (P)"), f"{cx.num(eg['intercept'], 2)} ({fmt_p_table(eg['p'])})"])
    if mr:
        rows.append([T("Meta 回归斜率 (95% CI)", "Meta-regression slope (95% CI)"), cx.cell_ci(mr["slope"], mr["lo"], mr["hi"], 3)])
    items.append(("tab", pd.DataFrame(rows, columns=[T("指标", "Item"), T("结果", "Result")]), T("Meta 分析汇总", "Summary of the meta-analysis"), T("随机效应模型" + ("（Hartung–Knapp 调整）" if r["hksj"] else "") + "；I²、τ² 为异质性指标。", "Random-effects model" + (" (Hartung–Knapp adjusted)" if r["hksj"] else "") + "; I² and τ² describe heterogeneity.")))
    secs.append(dict(heading=T("发表偏倚、敏感性与调节分析", "Publication bias, sensitivity and moderator analyses"), items=items))
    return secs


def _build_single(cx: Ctx) -> List[Dict[str, Any]]:
    from .builders_single import build_single
    return build_single(cx)


def _build_survey(cx: Ctx) -> List[Dict[str, Any]]:
    from .builders_survey import build_survey
    return build_survey(cx)


def _build_multitime_spss(cx: Ctx) -> List[Dict[str, Any]]:
    """LMM sections + a supplementary group × time mixed-ANOVA table (SPSS convention)."""
    secs = build_multitime(cx)
    T = cx.T
    rows = []
    for o in cx.res["outcomes"]:
        ma = o.get("mixed_anova") or {}
        if "effects" not in ma:
            continue
        name = {"group": T("组别", "Group"), "time": T("时间", "Time"), "group_x_time": T("组别 × 时间", "Group × time")}
        for i, e in enumerate(ma["effects"]):
            dfs = f"{e['df1']:.2f}, {e['df2']:.2f}" if (ma["gg_applied"] and e["effect"] != "group") else f"{e['df1']:.0f}, {e['df2']:.0f}"
            rows.append([cx.olabel(o) if i == 0 else "", name[e["effect"]] + ("†" if ma["gg_applied"] and e["effect"] != "group" else ""), dfs, cx.num(e["F"], 2), fmt_p_table(e["p"]), f"{e['np2']:.3f}",
                         str(ma["n"]) if i == 0 else ""])
    if rows:
        tab = pd.DataFrame(rows, columns=[T("结局", "Outcome"), T("效应", "Effect"), "df", "F", "P", T("偏 η²", "Partial η²"), "n"])
        secs.append(dict(heading=T("补充分析：重复测量方差分析", "Supplementary analysis: repeated-measures ANOVA"), items=[
            ("p", T("为便于与常用统计软件（SPSS）的输出对照，另以数据完整者做组别 × 时间的混合设计方差分析。主要结论以上文的线性混合模型为准（可利用全部观测值，对缺失更稳健）。",
                    "For comparison with standard software output (SPSS), a group × time mixed-design ANOVA was run on complete cases. Conclusions rest on the linear mixed model above, which uses all available observations and is more robust to missing data.")),
            ("tab", tab, T("组别 × 时间混合设计方差分析", "Group × time mixed-design ANOVA"),
             T("仅纳入全部时间点数据完整者；† 不满足球形假设（Mauchly P < 0.05），自由度与 P 为 Greenhouse–Geisser 校正值。", "Complete cases only; † sphericity rejected (Mauchly P < 0.05), Greenhouse–Geisser-corrected df and P."))]))
    return secs


BUILDERS = {"parallel_prepost": build_parallel, "crossover": build_crossover, "multitime": _build_multitime_spss, "meta": build_meta,
            "single_group": _build_single, "survey": _build_survey}
