# -*- coding: utf-8 -*-
"""Sections for the questionnaire / cross-sectional design (问卷调查 / 横断面研究). Same contract as builders.py.

Order follows the usual Chinese thesis chapter: 样本特征 → 共同方法偏差 → 信效度 → 描述统计与相关 → 人口学差异 → 回归 → 中介 → 调节.
"""
from __future__ import annotations

from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..pubstyle import figures as pf
from ..pubstyle.style import C_AMBER, C_GREY, C_INK, C_MAGENTA, C_MID, C_SLATE, DOUBLE, SINGLE, hair_y, panel_letter, panel_title
from ..pubstyle.tables import fmt_num, fmt_p_table
from . import plots
from .builders import Ctx


def _slab(cx: Ctx, name: str) -> str:
    sc = next((s for s in cx.spec["scales"] if s["name"] == name), None)
    if sc is not None:
        return cx.L(sc.get("label"), name)
    dv = next((v for v in cx.spec.get("demographics", []) if v["name"] == name or v.get("column") == name), None)
    return cx.L(dv.get("label"), name) if dv else name


def _lvl(cx: Ctx, var: str, lv: str) -> str:
    dv = next((v for v in cx.spec.get("demographics", []) if v["name"] == var), {})
    return cx.L(dv.get("level_labels", {}).get(lv, lv), lv)


def _term(cx: Ctx, term: str) -> str:
    """Regression term → label; dummies 'sex_女' → '性别（女 vs 参照）'."""
    for v in cx.spec.get("demographics", []):
        col = v.get("column", v["name"])
        if term.startswith(col + "_"):
            return f"{_slab(cx, v['name'])}（{_lvl(cx, v['name'], term[len(col) + 1:])}）" if cx.lang == "zh" else f"{_slab(cx, v['name'])} ({_lvl(cx, v['name'], term[len(col) + 1:])})"
    return _slab(cx, term)


def _sig_word(cx: Ctx, p: float) -> str:
    return cx.T("具有统计学意义", "statistically significant") if p < 0.05 else cx.T("未达统计学意义", "not statistically significant")


def build_survey(cx: Ctx) -> List[Dict[str, Any]]:
    s, r, T = cx.spec, cx.res, cx.T
    secs: List[Dict[str, Any]] = []

    # ---- 1 sample
    items: List[Any] = [("p", T(f"共回收有效问卷 {r['n']} 份。", f"{r['n']} valid questionnaires were analysed."))]
    if r["demographics"]:
        rows = []
        for dm in r["demographics"]:
            nm = _slab(cx, dm["name"])
            if dm["kind"] == "cont":
                rows.append([nm, T("均值 ± SD", "Mean ± SD"), cx.minus(f"{fmt_num(dm['mean'], 1)} ± {fmt_num(dm['sd'], 1)}")])
            else:
                for i, (lv, k) in enumerate(dm["levels"].items()):
                    rows.append([nm if i == 0 else "", _lvl(cx, dm["name"], lv), f"{k} ({100 * k / dm['n']:.1f}%)" if dm["n"] else "—"])
        items.append(("tab", pd.DataFrame(rows, columns=[T("变量", "Variable"), T("类别", "Category"), T("n (%) / 均值 ± SD", "n (%) / mean ± SD")]),
                      T("样本人口学特征", "Demographic characteristics of the sample"), T("分类变量为 n (%)，连续变量为均值 ± SD。", "Categorical variables n (%); continuous variables mean ± SD.")))
    secs.append(dict(heading=T("样本特征", "Sample characteristics"), items=items))

    # ---- 2 common-method bias
    if r.get("harman"):
        h = r["harman"]
        ok = h["first_pct"] < 40
        secs.append(dict(heading=T("共同方法偏差检验", "Common-method bias"), items=[("p", T(
            f"采用 Harman 单因素检验，对全部 {h['n_items']} 个题项做未旋转的主成分分析，特征根大于 1 的因子共 {h['n_eig_gt1']} 个，第一个因子解释变异量为 {h['first_pct']:.2f}%，"
            + ("低于 40% 的临界标准，提示不存在严重的共同方法偏差。" if ok else "超过 40% 的临界标准，提示可能存在共同方法偏差，结果解释需谨慎。"),
            f"Harman's single-factor test (unrotated principal components of all {h['n_items']} items) gave {h['n_eig_gt1']} factors with eigenvalue > 1; the first factor explained "
            f"{h['first_pct']:.2f}% of the variance, " + ("below the 40% threshold, so serious common-method bias is unlikely." if ok else "above the 40% threshold, so common-method bias may be present and results should be read with caution.")))]))

    # ---- 3 reliability & validity
    items = []
    rows = []
    for sc in r["scales"]:
        rit = [x["r_it"] for x in sc["items"]]
        adel = max(x["alpha_del"] for x in sc["items"])
        rows.append([_slab(cx, sc["name"]), str(sc["k"]), f"{sc['alpha']:.3f}", f"{min(rit):.3f}–{max(rit):.3f}", f"{adel:.3f}", cx.minus(f"{fmt_num(sc['mean'], 2)} ± {fmt_num(sc['sd'], 2)}")])
    items.append(("tab", pd.DataFrame(rows, columns=[T("量表", "Scale"), T("题项数", "Items"), "Cronbach α", T("校正题总相关", "Corrected item–total r"),
                                                     T("删题后 α 最大值", "Max α if item deleted"), T("得分 均值 ± SD", "Score mean ± SD")]),
                  T("各量表的内部一致性信度", "Internal-consistency reliability of the scales"),
                  T("反向计分题已转换后计算；得分为题项均值。α ≥ 0.70 通常视为可接受。", "Reverse-keyed items recoded before analysis; scores are item means. α ≥ 0.70 is usually considered acceptable.")))
    low = [_slab(cx, sc["name"]) for sc in r["scales"] if not sc["alpha"] >= 0.70]
    rng_ = (min(sc["alpha"] for sc in r["scales"]), max(sc["alpha"] for sc in r["scales"]))
    items.append(("p", T(f"各量表 Cronbach α 系数为 {rng_[0]:.3f}～{rng_[1]:.3f}" + (f"，其中{'、'.join(low)}低于 0.70，信度偏低。" if low else "，均高于 0.70，内部一致性良好。"),
                         f"Cronbach's α ranged from {rng_[0]:.3f} to {rng_[1]:.3f}" + (f"; {', '.join(low)} fell below 0.70." if low else "; all exceeded 0.70."))))
    if r.get("efa"):
        e = r["efa"]
        nf = e["n_factors"]
        b = e["bartlett"]
        items.append(("p", T(
            f"KMO 值为 {e['kmo']:.3f}，Bartlett 球形检验 χ²({b['df']}) = {b['chi2']:.2f}，{cx.P(b['p'])}，" + ("适合进行因子分析。" if e["kmo"] >= 0.6 and b["p"] < 0.05 else "不完全满足因子分析的前提，结果仅供参考。")
            + f"采用主轴因子法提取、最大方差法旋转，{'按预设' if e['n_factors_rule'] == 'spec' else '按特征根大于 1'}提取 {nf} 个因子，累计解释方差 {e['cum_pct'][-1]:.2f}%。"
            "探索性因子分析与验证性因子分析宜在不同样本中进行；本节未做验证性因子分析（可在 lavaan / AMOS 中完成）。",
            f"KMO = {e['kmo']:.3f}; Bartlett's test χ²({b['df']}) = {b['chi2']:.2f}, {cx.P(b['p'])}, " + ("supporting factor analysis. " if e["kmo"] >= 0.6 and b["p"] < 0.05 else "so the data only partly meet the prerequisites. ")
            + f"Principal-axis factoring with varimax rotation retained {nf} factor(s) ({'pre-specified' if e['n_factors_rule'] == 'spec' else 'eigenvalue > 1'}), explaining {e['cum_pct'][-1]:.2f}% of the variance in total. "
            "Exploratory and confirmatory factor analyses should use different samples; CFA was not performed here (use lavaan or AMOS).")))
        L = np.array(e["loadings"])
        fac = [f"F{j + 1}" for j in range(nf)]
        rows = [[it, _slab(cx, scn)] + [cx.minus(f"{v:.3f}") if abs(v) >= 0.30 else "" for v in L[i]] + [f"{e['communality'][i]:.3f}"] for i, (it, scn) in enumerate(zip(e["items"], e["item_scale"]))]
        rows.append([T("解释方差 (%)", "Variance explained (%)"), ""] + [f"{v:.2f}" for v in e["var_pct"]] + [""])
        rows.append([T("累计解释方差 (%)", "Cumulative (%)"), ""] + [f"{v:.2f}" for v in e["cum_pct"]] + [""])
        items.append(("tab", pd.DataFrame(rows, columns=[T("题项", "Item"), T("所属量表", "Scale")] + fac + ["h²"]),
                      T("探索性因子分析的旋转后因子载荷", "Rotated factor loadings from exploratory factor analysis"),
                      T("主轴因子法，最大方差旋转；|载荷| < 0.30 未显示；h² 为共同度。", "Principal-axis factoring, varimax rotation; |loadings| < 0.30 suppressed; h², communality.")))
        fig = plt.figure(figsize=(DOUBLE, 3.6))
        gs = fig.add_gridspec(1, 2, width_ratios=[0.9, 1.3], wspace=0.45)
        a1, a2 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
        eig = np.array(e["eigen"])
        xs = np.arange(1, len(eig) + 1)
        a1.plot(xs, eig, "-o", color=C_MAGENTA, ms=3.5, lw=1.2, mec="white", mew=0.6)
        a1.axhline(1, color=C_GREY, lw=0.7, ls=":")
        a1.text(len(eig), 1.05, T("特征根 = 1", "eigenvalue = 1"), fontsize=5.4, color=C_GREY, ha="right", va="bottom")
        a1.set_xlabel(T("因子序号", "Factor number"))
        a1.set_ylabel(T("特征根", "Eigenvalue"))
        hair_y(a1)
        panel_title(a1, "a", T("碎石图", "Scree plot"))
        pf.ax_heatmap(a2, L, list(e["items"]), fac, vmin=-1, vmax=1, annotate=True, fmt="{:.2f}")
        for txt in a2.texts:
            txt.set_text(cx.minus(txt.get_text()))
        panel_title(a2, "b", T("旋转后因子载荷", "Rotated loadings"), dx=-0.2)
        png = cx.save(fig, "efa")
        items.append(("fig", png, T("探索性因子分析。a，碎石图（虚线为特征根 = 1）；b，旋转后因子载荷矩阵。", "Exploratory factor analysis. a, scree plot (dotted line, eigenvalue = 1); b, rotated factor loadings.")))
    secs.append(dict(heading=T("信度与效度检验", "Reliability and validity"), items=items))

    # ---- 4 descriptives & correlations
    c = r["corr"]
    names = c["names"]
    R, P = np.array(c["r"]), np.array(c["p"])
    k = len(names)
    rows = []
    for i, nm in enumerate(names):
        sc = r["scales"][i]
        cells = []
        for j in range(k):
            cells.append("1" if i == j else (cx.minus(f"{R[i, j]:.3f}") if j < i else fmt_p_table(P[i, j])))
        rows.append([f"{i + 1}. {_slab(cx, nm)}", cx.minus(f"{fmt_num(sc['mean'], 2)} ± {fmt_num(sc['sd'], 2)}")] + cells)
    items = [("tab", pd.DataFrame(rows, columns=[T("变量", "Variable"), T("均值 ± SD", "Mean ± SD")] + [str(j + 1) for j in range(k)]),
              T("各变量的描述统计与 Pearson 相关", "Descriptive statistics and Pearson correlations"),
              T("对角线下方为相关系数 r，上方为对应的双侧 P 值。", "Correlation coefficients r below the diagonal; two-sided P values above the diagonal."))]
    pairs = [(i, j) for i in range(k) for j in range(i)]
    sig = [(i, j) for i, j in pairs if P[i, j] < 0.05]
    if pairs:
        rr = [abs(R[i, j]) for i, j in pairs]
        items.append(("p", T(f"{len(pairs)} 对变量中 {len(sig)} 对相关具有统计学意义，|r| 范围为 {min(rr):.3f}～{max(rr):.3f}。" +
                             "；".join(f"{_slab(cx, names[i])}与{_slab(cx, names[j])} r = {cx.minus(f'{R[i, j]:.3f}')}（{cx.P(P[i, j])}）" for i, j in pairs) + "。",
                             f"{len(sig)} of {len(pairs)} correlations were statistically significant (|r| {min(rr):.3f} to {max(rr):.3f}): " +
                             "; ".join(f"{_slab(cx, names[i])}–{_slab(cx, names[j])} r = {cx.minus(f'{R[i, j]:.3f}')} ({cx.P(P[i, j])})" for i, j in pairs) + ".")))
        fig, ax = plt.subplots(figsize=(SINGLE, SINGLE * 0.9))
        im = pf.ax_corr_heatmap(ax, R, [_slab(cx, n) for n in names], pvals=P)
        cb = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
        cb.set_label("r", fontsize=6)
        cb.ax.tick_params(labelsize=5.5)
        png = cx.save(fig, "correlation")
        items.append(("fig", png, T("各变量的 Pearson 相关矩阵（加粗为 P < 0.05）。", "Pearson correlation matrix (bold, P < 0.05).")))
    secs.append(dict(heading=T("描述统计与相关分析", "Descriptive statistics and correlations"), items=items))

    # ---- 5 group differences
    if r["group_compare"]:
        items = []
        for var in dict.fromkeys(g["var"] for g in r["group_compare"]):
            gs_ = [g for g in r["group_compare"] if g["var"] == var]
            lv = gs_[0]["levels"]
            three = gs_[0]["test"] == "F"
            hdr = [T("量表", "Scale")] + [f"{_lvl(cx, var, x)} (n = {gs_[0]['desc'][x][2]})" for x in lv] + (["F", "P", "q", "η²"] if three else ["t", "P", "q", "Hedges g"])
            rows = []
            for g in gs_:
                cells = [cx.minus(f"{fmt_num(g['desc'][x][0], 2)} ± {fmt_num(g['desc'][x][1], 2)}") for x in lv]
                es = f"{g['es']:.3f}" if three else cx.num(g["es"], 2)
                rows.append([_slab(cx, g["outcome"])] + cells + [cx.num(g["stat"], 2), fmt_p_table(g["p"]), fmt_p_table(g["q"]), es])
            items.append(("tab", pd.DataFrame(rows, columns=hdr), T(f"不同{_slab(cx, var)}的各量表得分比较", f"Scale scores by {_slab(cx, var).lower()}"),
                          (T("单因素方差分析；η² 为效应量；两两比较采用 Welch t 检验并 Holm 校正。", "One-way ANOVA; η², effect size; pairwise Welch t tests with Holm adjustment. ") if three else
                           T("Welch t 检验；Hedges g 为前一类别相对后一类别的标准化差值。", "Welch t test; Hedges g compares the first with the second category. "))
                          + T("q 为全部人口学比较的 BH-FDR 校正值，属探索性分析。均值 ± SD。", "q, Benjamini–Hochberg-adjusted across all demographic comparisons (exploratory). Values are mean ± SD.")))
        sig = [g for g in r["group_compare"] if g["q"] < 0.05]
        if sig:
            parts = []
            for g in sig:
                hi_ = max(g["levels"], key=lambda x: g["desc"][x][0])
                pw = [p for p in g.get("pairs", []) if p["p_adj"] < 0.05]
                pwt = (T("（两两比较：", " (pairwise: ") + T("，", ", ").join(f"{_lvl(cx, g['var'], p['a'])} vs {_lvl(cx, g['var'], p['b'])} Holm {cx.P(p['p_adj'])}" for p in pw) + T("）", ")")) if pw else ""
                stat = f"F{tuple(g['df'])} = {cx.num(g['stat'], 2)}" if g["test"] == "F" else f"t({g['df']:.1f}) = {cx.num(g['stat'], 2)}"
                parts.append(T(f"{_slab(cx, g['outcome'])}在{_slab(cx, g['var'])}上存在差异（{stat}，{cx.P(g['p'])}，q = {g['q']:.3f}），{_lvl(cx, g['var'], hi_)}得分最高{pwt}",
                               f"{_slab(cx, g['outcome'])} differed by {_slab(cx, g['var']).lower()} ({stat}, {cx.P(g['p'])}, q = {g['q']:.3f}), highest in {_lvl(cx, g['var'], hi_)}{pwt}"))
            items.append(("p", T("；".join(parts) + "。其余比较经 BH 校正后差异未达统计学意义。", "; ".join(parts) + ". The remaining comparisons were not significant after Benjamini–Hochberg adjustment.")))
        else:
            items.append(("p", T("经 BH 校正后，各量表得分在人口学变量上的差异均未达统计学意义。", "No demographic difference in scale scores remained significant after Benjamini–Hochberg adjustment.")))
        secs.append(dict(heading=T("人口学变量的差异分析", "Differences by demographic characteristics"), items=items))

    # ---- 6 regression
    for mi, m in enumerate(r["regression"]):
        items = []
        rows = [[_term(cx, cf["term"]), cx.num(cf["B"], 3), f"{cf['se']:.3f}", cx.num(cf["beta"], 3), cx.num(cf["t"], 2), fmt_p_table(cf["p"]),
                 cx.minus(f"{fmt_num(cf['lo'], 3)}, {fmt_num(cf['hi'], 3)}"), f"{cf['vif']:.2f}"] for cf in m["coefs"]]
        covtxt = T("、", ", ").join(_slab(cx, x) for x in m["covs"])
        items.append(("tab", pd.DataFrame(rows, columns=[T("预测变量", "Predictor"), "B", "SE", "β", "t", "P", "95% CI (B)", "VIF"]),
                      T(f"{_slab(cx, m['y'])}的多元线性回归分析", f"Multiple linear regression of {_slab(cx, m['y']).lower()}"),
                      T(f"R² = {m['r2']:.3f}，调整 R² = {m['adj_r2']:.3f}，F({m['df1']}, {m['df2']}) = {m['F']:.2f}，{cx.P(m['p_model'])}；n = {m['n']}。B 为非标准化系数，β 为标准化系数。"
                        + (f"控制变量：{covtxt}。" if m["covs"] else ""),
                        f"R² = {m['r2']:.3f}, adjusted R² = {m['adj_r2']:.3f}, F({m['df1']}, {m['df2']}) = {m['F']:.2f}, {cx.P(m['p_model'])}; n = {m['n']}. B, unstandardised; β, standardised coefficient."
                        + (f" Covariates: {covtxt}." if m["covs"] else ""))))
        focal = [cf for cf in m["coefs"] if not cf["is_cov"]]
        txt = T("；", "; ").join(T(f"{_term(cx, cf['term'])} β = {cx.num(cf['beta'], 3)}（{cx.P(cf['p'])}）", f"{_term(cx, cf['term'])} β = {cx.num(cf['beta'], 3)} ({cx.P(cf['p'])})") for cf in focal)
        vmax = max(cf["vif"] for cf in m["coefs"])
        items.append(("p", T(f"以{_slab(cx, m['y'])}为因变量的回归模型解释了 {100 * m['r2']:.1f}% 的变异（{cx.P(m['p_model'])}）。{txt}。各预测变量 VIF 最大为 {vmax:.2f}，" + ("未见明显多重共线性。" if vmax < 5 else "提示存在一定多重共线性。"),
                             f"The model for {_slab(cx, m['y']).lower()} explained {100 * m['r2']:.1f}% of the variance ({cx.P(m['p_model'])}). {txt}. The largest VIF was {vmax:.2f}" + (", so multicollinearity was not a concern." if vmax < 5 else ", indicating some multicollinearity."))))
        rows_f = [dict(label=_term(cx, cf["term"]), est=cf["beta"], lo=min(cf["beta_lo"], cf["beta_hi"]), hi=max(cf["beta_lo"], cf["beta_hi"]),
                       color=C_SLATE if cf["is_cov"] else C_MAGENTA, hollow=cf["p"] >= 0.05, text=cx.minus(f"{cf['beta']:.3f}\n{cx.P(cf['p'])}")) for cf in m["coefs"]]
        fig, ax = plt.subplots(figsize=(SINGLE + 0.6, 0.32 * len(rows_f) + 1.0))
        plots.est_forest(ax, rows_f, T("标准化回归系数 β（95% CI）", "Standardised coefficient β (95% CI)"), decimals=3, text_x=1.04)
        png = cx.save(fig, f"regression_{mi + 1}")
        items.append(("fig", png, T(f"{_slab(cx, m['y'])}回归模型的标准化系数及 95% CI（空心：P ≥ 0.05；灰色为控制变量）。", f"Standardised coefficients with 95% CI in the model for {_slab(cx, m['y']).lower()} (hollow, P ≥ 0.05; grey, covariates).")))
        secs.append(dict(heading=T("回归分析：", "Regression: ") + _slab(cx, m["y"]), items=items))

    # ---- 7 mediation
    for mi, m in enumerate(r["mediation"]):
        X, M, Y = _slab(cx, m["x"]), _slab(cx, m["m"]), _slab(cx, m["y"])
        ind = m["indirect"]
        sig_ind = not (ind["lo"] <= 0 <= ind["hi"])
        f3 = lambda v: cx.minus(f"{v:.3f}")
        rows = [[f"a ({X} → {M})", f3(m["a"]["est"]), f"{m['a']['se']:.3f}", cx.minus(f"{fmt_num(m['a']['lo'], 3)}, {fmt_num(m['a']['hi'], 3)}"), fmt_p_table(m["a"]["p"])],
                [f"b ({M} → {Y})", f3(m["b"]["est"]), f"{m['b']['se']:.3f}", cx.minus(f"{fmt_num(m['b']['lo'], 3)}, {fmt_num(m['b']['hi'], 3)}"), fmt_p_table(m["b"]["p"])],
                [T(f"c（总效应）", "c (total effect)"), f3(m["c"]["est"]), f"{m['c']['se']:.3f}", cx.minus(f"{fmt_num(m['c']['lo'], 3)}, {fmt_num(m['c']['hi'], 3)}"), fmt_p_table(m["c"]["p"])],
                [T(f"c′（直接效应）", "c′ (direct effect)"), f3(m["cp"]["est"]), f"{m['cp']['se']:.3f}", cx.minus(f"{fmt_num(m['cp']['lo'], 3)}, {fmt_num(m['cp']['hi'], 3)}"), fmt_p_table(m["cp"]["p"])],
                [T("a × b（间接效应）", "a × b (indirect effect)"), f3(ind["est"]), f"{ind['boot_se']:.3f}", cx.minus(f"{fmt_num(ind['lo'], 3)}, {fmt_num(ind['hi'], 3)}"), T("Bootstrap", "Bootstrap")]]
        covtxt = T("、", ", ").join(_slab(cx, x) for x in m["covs"])
        items = [("tab", pd.DataFrame(rows, columns=[T("路径", "Path"), T("效应", "Effect"), "SE", "95% CI", "P"]),
                  T(f"{M}在{X}与{Y}之间的中介效应", f"Mediating role of {M.lower()} between {X.lower()} and {Y.lower()}"),
                  T(f"Hayes PROCESS 模型 4，非标准化系数；间接效应的 95% CI 为 {m['n_boot']} 次 Bootstrap 抽样的百分位区间，不含 0 即视为显著。n = {m['n']}。" + (f"控制变量：{covtxt}。" if m["covs"] else ""),
                    f"Hayes PROCESS model 4, unstandardised coefficients; the 95% CI of the indirect effect is the percentile interval from {m['n_boot']} bootstrap samples (significant if it excludes 0). n = {m['n']}." + (f" Covariates: {covtxt}." if m["covs"] else "")))]
        if sig_ind:
            kind = T("部分中介", "partial mediation") if m["cp"]["p"] < 0.05 else T("完全中介", "full mediation")
            prop = f"{100 * m['prop_mediated']:.1f}%" if np.isfinite(m["prop_mediated"]) else "—"
            items.append(("p", T(f"{X}经{M}影响{Y}的间接效应为 {f3(ind['est'])}（Bootstrap 95% CI {fmt_num(ind['lo'], 3)}～{fmt_num(ind['hi'], 3)}，不含 0），中介效应显著；控制{M}后{X}对{Y}的直接效应"
                                 f"{'仍' if m['cp']['p'] < 0.05 else '不再'}具有统计学意义（c′ = {f3(m['cp']['est'])}，{cx.P(m['cp']['p'])}），呈{kind}，间接效应占总效应的 {prop}。横断面数据不能确立因果顺序。",
                                 f"The indirect effect of {X.lower()} on {Y.lower()} through {M.lower()} was {f3(ind['est'])} (bootstrap 95% CI {cx.minus(fmt_num(ind['lo'], 3))} to {cx.minus(fmt_num(ind['hi'], 3))}, excluding 0). "
                                 f"The direct effect {'remained' if m['cp']['p'] < 0.05 else 'was no longer'} significant (c′ = {f3(m['cp']['est'])}, {cx.P(m['cp']['p'])}), consistent with {kind}; the indirect effect accounted for {prop} of the total effect. Cross-sectional data cannot establish causal order.")))
        else:
            items.append(("p", T(f"间接效应为 {f3(ind['est'])}（Bootstrap 95% CI {fmt_num(ind['lo'], 3)}～{fmt_num(ind['hi'], 3)}，包含 0），{M}的中介效应不显著。",
                                 f"The indirect effect was {f3(ind['est'])} (bootstrap 95% CI {cx.minus(fmt_num(ind['lo'], 3))} to {cx.minus(fmt_num(ind['hi'], 3))}, including 0); mediation by {M.lower()} was not supported.")))
        fig, ax = plt.subplots(figsize=(SINGLE + 0.9, 2.3))

        def lab_(pp):
            return cx.minus(f"{pp['est']:.3f} ({cx.P(pp['p'])})")
        pf.ax_mediation(ax, (X, M, Y), lab_(m["a"]), lab_(m["b"]), lab_(m["c"]), lab_(m["cp"]), cx.minus(f"{ind['est']:.3f} [{ind['lo']:.3f}, {ind['hi']:.3f}]"))
        png = cx.save(fig, f"mediation_{mi + 1}")
        items.append(("fig", png, T("中介模型路径图（非标准化系数及 P 值；间接效应方括号内为 Bootstrap 95% CI）。", "Mediation model (unstandardised coefficients with P; bootstrap 95% CI of the indirect effect in brackets).")))
        secs.append(dict(heading=T("中介效应检验：", "Mediation: ") + M, items=items))

    # ---- 8 moderation
    for mi, m in enumerate(r["moderation"]):
        X, W, Y = _slab(cx, m["x"]), _slab(cx, m["w"]), _slab(cx, m["y"])
        tl = {m["x"]: X, m["w"]: W, f"{m['x']}×{m['w']}": f"{X} × {W}"}
        rows = [[tl[t["term"]], cx.num(t["B"], 3), f"{t['se']:.3f}", cx.num(t["t"], 2), fmt_p_table(t["p"]), cx.minus(f"{fmt_num(t['lo'], 3)}, {fmt_num(t['hi'], 3)}")] for t in m["terms"]]
        lvl = {"-1SD": T("低（−1 SD）", "Low (−1 SD)"), "mean": T("均值", "Mean"), "+1SD": T("高（+1 SD）", "High (+1 SD)")}
        for sl in m["slopes"]:
            rows.append([T(f"简单斜率：{W}", f"Simple slope: {W} ") + lvl[sl["level"]], cx.num(sl["est"], 3), f"{sl['se']:.3f}", "", fmt_p_table(sl["p"]), cx.minus(f"{fmt_num(sl['lo'], 3)}, {fmt_num(sl['hi'], 3)}")])
        it = m["terms"][2]
        items = [("tab", pd.DataFrame(rows, columns=[T("项", "Term"), "B", "SE", "t", "P", "95% CI"]),
                  T(f"{W}在{X}与{Y}关系中的调节效应", f"Moderating role of {W.lower()} in the association between {X.lower()} and {Y.lower()}"),
                  T(f"Hayes PROCESS 模型 1；自变量与调节变量均中心化。交互项 ΔR² = {m['dr2']:.4f}，F(1, {m['df2']}) = {m['F_change']:.2f}，{cx.P(m['p_change'])}；n = {m['n']}。",
                    f"Hayes PROCESS model 1; predictor and moderator mean-centred. Interaction ΔR² = {m['dr2']:.4f}, F(1, {m['df2']}) = {m['F_change']:.2f}, {cx.P(m['p_change'])}; n = {m['n']}."))]
        if it["p"] < 0.05:
            items.append(("p", T(f"{X}与{W}的交互项具有统计学意义（B = {cx.num(it['B'], 3)}，{cx.P(it['p'])}，ΔR² = {m['dr2']:.4f}），{W}调节了{X}与{Y}的关系。简单斜率分析见表。",
                                 f"The {X.lower()} × {W.lower()} interaction was significant (B = {cx.num(it['B'], 3)}, {cx.P(it['p'])}, ΔR² = {m['dr2']:.4f}); {W.lower()} moderated the association between {X.lower()} and {Y.lower()} (simple slopes in the table).")))
        else:
            items.append(("p", T(f"{X}与{W}的交互项未达统计学意义（B = {cx.num(it['B'], 3)}，{cx.P(it['p'])}），未发现{W}的调节作用。",
                                 f"The {X.lower()} × {W.lower()} interaction was not significant (B = {cx.num(it['B'], 3)}, {cx.P(it['p'])}); moderation by {W.lower()} was not supported.")))
        pl = m["_plot"]
        xs = np.linspace(max(-2 * pl["x_sd"], pl["x_min"] - pl["x_mean"]), min(2 * pl["x_sd"], pl["x_max"] - pl["x_mean"]), 50)  # observed range only
        fig, ax = plt.subplots(figsize=(SINGLE, 2.6))
        for (lv, wv), col, ls in zip((("-1SD", -pl["w_sd"]), ("mean", 0.0), ("+1SD", pl["w_sd"])), (C_AMBER, C_MID, C_MAGENTA), ((0, (3, 2)), "-", "-")):
            yv = pl["b0"] + pl["b"][0] * xs + pl["b"][1] * wv + pl["b"][2] * xs * wv
            ax.plot(xs + pl["x_mean"], yv, color=col, lw=1.6, ls=ls)
            ax.text(xs[-1] + pl["x_mean"], yv[-1], " " + lvl[lv], fontsize=5.6, color=col, va="center")
        ax.set_xlabel(X)
        ax.set_ylabel(T(f"{Y}（预测值）", f"{Y} (predicted)"))
        hair_y(ax)
        png = cx.save(fig, f"moderation_{mi + 1}")
        items.append(("fig", png, T(f"不同{W}水平下{X}与{Y}的简单斜率（控制变量取均值）。", f"Simple slopes of {X.lower()} on {Y.lower()} at low, mean and high {W.lower()} (covariates at their means).")))
        secs.append(dict(heading=T("调节效应检验：", "Moderation: ") + W, items=items))
    return secs
