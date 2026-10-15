# -*- coding: utf-8 -*-
"""Sections for the single-group design (单组前后测 / 单组重复测量). Same contract as builders.py."""
from __future__ import annotations

from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..pubstyle import figures as pf
from ..pubstyle.style import C_GREY, C_MAGENTA, DOUBLE, panel_title, wrap_label
from ..pubstyle.tables import fmt_num, fmt_p_table
from . import plots
from .builders import Ctx, _cat_header_rows, _forest_std, _sig


def _caution(cx: Ctx) -> str:
    return cx.T("本研究为单组设计，未设对照组，观察到的变化不能完全归因于干预本身（可能混有时间、练习、季节或均值回归效应），解释时应保持谨慎。",
                "This was a single-group design without a control arm, so the changes cannot be attributed to the intervention alone "
                "(time, practice, seasonal and regression-to-the-mean effects may contribute).")


def _test_text(cx: Ctx, o: Dict[str, Any]) -> str:
    T, t = cx.T, o["test"]
    nd = o.get("decimals")
    ch = o["change"]
    t0, t1 = cx.res["times"][0], cx.res["times"][-1]
    un = o["unit"]
    sg = _sig(o["main"])
    adj = f"{cx.T('，', '; ')}{cx.padj(o['main'])}" if o["main"].get("p_adj") is not None and len(cx.res["outcomes"]) > 1 else ""
    if t["kind"] == "paired_t":
        wil = f"{T('；Wilcoxon 符号秩检验 ', '; Wilcoxon signed-rank ')}{cx.P(t['wilcoxon_p'])}" if np.isfinite(t["wilcoxon_p"]) else ""
        return T(f"{cx.olabel(o, False)}：{cx.tlabel(t1)}较{cx.tlabel(t0)}平均变化 {cx.num(ch['diff'], nd)} {un}（{cx.ci(ch['lo'], ch['hi'], nd)}；"
                 f"配对 t({t['df']}) = {cx.num(t['t'], 2)}，{cx.P(t['p'])}{adj}；d_z = {cx.num(ch['dz'], 2)}{wil}），差异{'具有' if sg else '未达'}统计学意义。",
                 f"{cx.olabel(o, False)}: from {cx.tlabel(t0)} to {cx.tlabel(t1)} the mean change was {cx.num(ch['diff'], nd)} {un} ({cx.ci(ch['lo'], ch['hi'], nd)}; "
                 f"paired t({t['df']}) = {cx.num(t['t'], 2)}, {cx.P(t['p'])}{adj}; d_z = {cx.num(ch['dz'], 2)}{wil}); the change {'was' if sg else 'was not'} statistically significant.")
    sph = T(f"Mauchly 球形检验 W = {t['mauchly_W']:.3f}，{cx.P(t['mauchly_p'])}", f"Mauchly's W = {t['mauchly_W']:.3f}, {cx.P(t['mauchly_p'])}")
    corr = T(f"，不满足球形假设，采用 Greenhouse–Geisser 校正（ε = {t['eps_gg']:.3f}）", f"; sphericity was violated and the Greenhouse–Geisser correction was applied (ε = {t['eps_gg']:.3f})") \
        if t["gg_applied"] else T("，满足球形假设", "; sphericity was not rejected")
    main = T(f"{cx.olabel(o, False)}：重复测量方差分析显示时间主效应 F({t['df1_report']:.2f}, {t['df2_report']:.2f}) = {cx.num(t['F'], 2)}，{cx.P(t['p_report'])}{adj}，偏 η² = {t['np2']:.3f}"
             f"（{sph}{corr}），{'具有' if sg else '未达'}统计学意义。",
             f"{cx.olabel(o, False)}: repeated-measures ANOVA showed a main effect of time F({t['df1_report']:.2f}, {t['df2_report']:.2f}) = {cx.num(t['F'], 2)}, {cx.P(t['p_report'])}{adj}, "
             f"partial η² = {t['np2']:.3f} ({sph}{corr}); the effect {'was' if sg else 'was not'} statistically significant.")
    pairs = [p for p in o.get("pairs", []) if p["p_bonf"] < 0.05]
    if pairs and sg:
        lst = T("；", "; ").join(f"{cx.tlabel(p['b'])} vs {cx.tlabel(p['a'])} {cx.num(p['diff'], nd)} {un}（Bonferroni {cx.P(p['p_bonf'])}）" if cx.lang == "zh" else
                                f"{cx.tlabel(p['b'])} vs {cx.tlabel(p['a'])} {cx.num(p['diff'], nd)} {un} (Bonferroni {cx.P(p['p_bonf'])})" for p in pairs)
        main += T(f"两两比较中差异有统计学意义的为：{lst}。", f" Pairwise comparisons that differed: {lst}.")
    elif sg:
        main += T("经 Bonferroni 校正后，两两比较均未达统计学意义。", " No pairwise comparison remained significant after Bonferroni correction.")
    return main


def build_single(cx: Ctx) -> List[Dict[str, Any]]:
    r, T = cx.res, cx.T
    times = r["times"]
    tl = [cx.tlabel(t) for t in times]
    outs = r["outcomes"]
    prim = [o for o in outs if o["primary"]]
    sec = [o for o in outs if not o["primary"]]
    secs: List[Dict[str, Any]] = []
    design_word = T("配对 t 检验", "paired t tests") if len(times) == 2 else T("单因素重复测量方差分析", "one-way repeated-measures ANOVA")

    comp = T("、", ", ").join(f"{cx.olabel(o, False)} {o['n_complete']}" for o in outs)
    secs.append(dict(heading=T("受试者与数据完整性", "Participants and data completeness"), items=[
        ("p", T(f"共 {r['n_id']} 名受试者在 {len(times)} 个时间点（{'、'.join(tl)}）接受测试；各结局全部时间点数据完整的人数分别为：{comp}。统计分析采用{design_word}，仅纳入数据完整者。",
                f"{r['n_id']} participants were tested at {len(times)} time points ({', '.join(tl)}). Complete cases per outcome: {comp}. Analyses used {design_word} on complete cases.")),
        ("p", _caution(cx))]))

    for o in prim:
        items = [("p", _test_text(cx, o))]
        w = o["_wide"].dropna()
        nd = o.get("decimals")
        long_ = w.reset_index().melt(id_vars=w.index.name or "index", var_name="t", value_name="y").rename(columns={w.index.name or "index": "id"})
        long_["g"] = "all"
        npair = len(o.get("pairs", [])) or 1
        fig = plt.figure(figsize=(DOUBLE, 3.2))
        gs = fig.add_gridspec(1, 3, width_ratios=[1.35, 0.7, 0.45 + 0.4 * npair], wspace=0.42)
        a1, a2, a3 = (fig.add_subplot(gs[0, i]) for i in range(3))
        pf.ax_multitime(a1, long_, "id", "g", "t", "y", ["all"], {"all": C_MAGENTA}, times, tl, cx.olabel(o), indiv_alpha=0.22, band=True)
        panel_title(a1, "a", T("个体轨迹与均值", "Individuals and mean"))
        chg = (w[times[-1]] - w[times[0]]).values
        pf.ax_raincloud(a2, {T("变化", "Change"): chg}, {T("变化", "Change"): C_MAGENTA},
                        ylabel=f"{tl[-1]} − {tl[0]}" + (f" ({o['unit']})" if o["unit"] else ""))
        a2.axhline(0, color=C_GREY, lw=0.7, ls=(0, (3, 2)))
        panel_title(a2, "b", T("个体变化", "Change"))
        if o["test"]["kind"] == "rm_anova":
            rows = [dict(label=f"{cx.tlabel(p['b'])}\n− {cx.tlabel(p['a'])}", est=p["diff"], lo=p["lo"], hi=p["hi"], color=C_MAGENTA, df=o["n_complete"] - 1,
                         text=cx.minus(f"{fmt_num(p['diff'], nd)}\n[{fmt_num(p['lo'], nd)}, {fmt_num(p['hi'], nd)}]\n" + "Bonf. " + cx.P(p["p_bonf"]))) for p in o["pairs"]]
        else:
            ch = o["change"]
            rows = [dict(label=f"{tl[-1]}\n− {tl[0]}", est=ch["diff"], lo=ch["lo"], hi=ch["hi"], color=C_MAGENTA, df=ch["n"] - 1,
                         text=cx.minus(f"{fmt_num(ch['diff'], nd)}\n[{fmt_num(ch['lo'], nd)}, {fmt_num(ch['hi'], nd)}]\n{cx.P(o['test']['p'])}"))]
        plots.diff_estimate(a3, rows, T("均值差", "Mean difference") + (f" ({o['unit']})" if o["unit"] else ""), decimals=nd or 2, width=0.3)
        panel_title(a3, "c", T("时间点间差值", "Differences"))
        png = cx.save(fig, f"primary_{o['name']}")
        items.append(("fig", png, T(
            f"主要结局{cx.olabel(o, False)}。a，各受试者在各时间点的观测值（细线）及均值 ± 95% CI；b，{tl[-1]}相对{tl[0]}的个体变化量（竖线为 IQR，菱形/误差线为均值 ± 95% CI）；c，时间点间的均值差（点与竖线为估计值及 95% CI，阴影为抽样分布）"
            + ("，Bonf. P 为 Bonferroni 校正 P 值。" if o["test"]["kind"] == "rm_anova" else "（配对 t 检验）。"),
            f"Primary outcome, {cx.olabel(o, False)}. a, individual values (thin lines) with mean ± 95% CI at each time point; b, individual change from {tl[0]} to {tl[-1]} "
            "(bar is IQR; marker and whiskers are mean ± 95% CI); c, mean differences between time points (point and bar: estimate and 95% CI; shading: sampling distribution)"
            + ("; Bonf. P, Bonferroni-adjusted P." if o["test"]["kind"] == "rm_anova" else " (paired t test)."))))
        secs.append(dict(heading=T("主要结局：", "Primary outcome: ") + cx.olabel(o, False), items=items))

    # all outcomes
    items = []
    k2 = len(times) == 2
    hdr = [T("结局", "Outcome")] + tl + ([f"{tl[-1]} − {tl[0]} (95% CI)", "t", "P"] if k2 else ["F", "P", T("偏 η²", "Partial η²")]) + [T("校正后 P", "Adj. P"), "d_z"]
    rows, cats = [], []
    for o in outs:
        nd, t, ch = o.get("decimals"), o["test"], o["change"]
        cells = [f"{fmt_num(o['desc'][tt][0], nd)} ± {fmt_num(o['desc'][tt][1], nd)}" for tt in times]
        stat = [cx.cell_ci(ch["diff"], ch["lo"], ch["hi"], nd), cx.num(t["t"], 2), fmt_p_table(t["p"])] if k2 else \
               [cx.num(t["F"], 2) + ("†" if t.get("gg_applied") else ""), fmt_p_table(t["p_report"]), f"{t['np2']:.3f}"]
        rows.append([cx.minus(x) for x in [cx.olabel(o)] + cells + stat + [fmt_p_table(o["main"].get("p_adj")), cx.num(ch["dz"], 2)]])
        cats.append(o["category"])
    df2 = pd.DataFrame(_cat_header_rows(rows, cats, len(hdr), cx), columns=hdr)
    note = T("各时间点为均值 ± SD。", "Values at each time point are mean ± SD. ") + (
        T("配对 t 检验；d_z 为配对差值的标准化均值。", "Paired t tests; d_z is the standardised mean of the paired differences. ") if k2 else
        T(f"单因素重复测量方差分析；† 不满足球形假设（Mauchly P < 0.05），报告 Greenhouse–Geisser 校正结果；d_z 为 {tl[-1]} 相对 {tl[0]} 的变化。",
          f"One-way repeated-measures ANOVA; † sphericity rejected (Mauchly P < 0.05), Greenhouse–Geisser-corrected result reported; d_z refers to the change from {tl[0]} to {tl[-1]}. ")) + \
        T("校正后 P：主要结局 Holm，次要结局按类别 BH-FDR。单组设计，无对照组。", "Adj. P: Holm for the primary outcome, Benjamini–Hochberg within category for secondary outcomes. Single-group design without a control arm.")
    items.append(("tab", df2, T("各结局在各时间点的测量值与时间效应", "Values at each time point and effect of time for all outcomes"), note))
    if sec:
        nsig = [o for o in sec if _sig(o["main"])]
        items.append(("p", T(f"{len(sec)} 个次要结局中，{len(nsig)} 项在按类别 BH 校正后时间效应有统计学意义" + (f"（{'、'.join(cx.olabel(o, False) for o in nsig)}）" if nsig else "") + "，次要结局仅作探索性解释。",
                             f"Of {len(sec)} secondary outcomes, {len(nsig)} showed a time effect that remained significant after Benjamini–Hochberg adjustment within category"
                             + (f" ({', '.join(cx.olabel(o, False) for o in nsig)})" if nsig else "") + "; secondary outcomes are exploratory.")))
    rows_f, cat_list = [], []
    for o in outs:
        if o["category"] not in cat_list:
            cat_list.append(o["category"])
        sgn, ch = o["orient"], o["change"]
        lo_, hi_ = sorted((sgn * ch["dz_lo"], sgn * ch["dz_hi"]))
        rows_f.append(dict(category=cx.catlabel(o["category"]), label=cx.olabel(o, False), g=float(np.clip(sgn * ch["dz"], -3, 3)), lo=float(np.clip(lo_, -3, 3)),
                           hi=float(np.clip(hi_, -3, 3)), sig=_sig(o["main"]), neutral=o.get("direction") == "neutral", text=cx.minus(f"{sgn * ch['dz']:.2f} ({lo_:.2f}, {hi_:.2f})")))
    png = _forest_std(cx, rows_f, cat_list, T(f"标准化变化 d_z（{tl[-1]} vs {tl[0]}，正值 = 改善方向）", f"Standardised change d_z ({tl[-1]} vs {tl[0]}; positive = improvement)"),
                      T("实心：时间效应校正后显著", "Filled: time effect significant after adjustment"), "forest_dz")
    items.append(("fig", png, T(f"全部结局{tl[-1]}相对{tl[0]}的标准化变化量（d_z，95% CI），已按改善方向统一符号。", f"Standardised change from {tl[0]} to {tl[-1]} (d_z, 95% CI) for all outcomes, signed so that positive values indicate improvement.")))
    secs.append(dict(heading=T("全部结局", "All outcomes"), items=items))
    return secs
