"""
pubstyle_demo.py — the reference implementation of the house figure/table style, in BOTH languages.

    python examples/pubstyle_demo.py                 # writes outputs/pubstyle_demo/zh and /en
    python examples/pubstyle_demo.py --lang en       # only English
    python examples/pubstyle_demo.py --out some/dir

It builds a complete mini "Results" section from SYNTHETIC data (clearly tagged as simulated):
    Fig 1 participant flow            Fig 4 pre/post individual trajectories (2 arms)
    Fig 2 time-course compound        Fig 5 grouped forest plot of standardised effects
    Fig 3 paired estimation compound  Fig 6 composition bars + AGP-style profile + dose scatter
    Tables 1-3 (three-line) + Excel workbook + results.docx

An AI agent should COPY THIS FILE as a template: keep the structure (apply_style -> blocks -> panel letters ->
save_figure -> ResultsDoc), replace the synthetic data with the real analysis output, and keep every rule in
reference/STYLE_SPEC_{ZH,EN}.md. The language switch lives only in the LABELS dictionary below.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt  # noqa: E402

from sportsci_figures.pubstyle import (DOUBLE, ResultsDoc, apply_style, arm_colors, condition_colors, fmt_ci, fmt_msd, fmt_n_pct, fmt_num, fmt_p, fmt_p_table,  # noqa: E402
                                     panel_letter, save_figure, save_tables_xlsx, t)
from sportsci_figures.pubstyle import figures as pf  # noqa: E402
from sportsci_figures.pubstyle.style import C_AMBER, C_CORAL, C_GREY, C_MAGENTA, C_SLATE, C_TEAL  # noqa: E402

# ----------------------------------------------------------------------------- the ONLY language-dependent part
LABELS = {
    "zh": dict(
        conds=["CON", "RT20", "RT30", "RT45"], cond_names={"CON": "CON 静坐", "RT20": "RT20", "RT30": "RT30", "RT45": "RT45"},
        arms=("对照组", "干预组"), baseline="基线", wk="12周", xt="时钟时间 (h)", yt="血糖 (mmol/L)", dt="与 CON 的配对差 (mmol/L)",
        rel_t="干预开始后时间 (h)", rel_y="相对基线变化 (mmol/L)", meal="餐", window="干预", sub_a="a  24 h 曲线", auc="0–6 h net iAUC (mmol·h/L)",
        contrast="条件间差值 (mmol·h/L)\n← 降幅更大", thr="10% 临床阈值", dose="每次训练总组数", dose_y="较 CON 的变化 (mmol·h/L)", sets=["12组\nRT20", "18组\nRT30", "24组\nRT45"],
        trend="线性趋势 {b:.2f}/6组, {p}", eff="干预组 − 对照组 变化量的标准化效应量（Hedges g，95% CI）\n获益方向为正；灰色为安全性/中性指标",
        foot="实心 = BH-FDR q<0.05；† = 对数转换分析", cats=["血糖指标", "血液指标", "功能指标"], tin="TIR 3.9–10.0", tar="TAR >10.0", tbr="TBR <3.9",
        pct="占读数比例 (%)", clock="钟表时间", adh="训练依从性 (%)", dy="TIR 变化 (百分点)", resp="干预组 14 d 日内曲线", group_diff="组间差 {b:+.2f} ({lo:.2f}, {hi:.2f})\n{p}",
        t1="研究二两组基线特征", t1n="连续变量为均值 ± SD，分类变量为 n (%)。P 为独立样本 t 检验或 Fisher 精确检验；SMD 为标准化均数差。", var="变量",
        tot="全体", age="年龄 (岁)", bmi="BMI (kg/m²)", male="男性", t2="研究一结局的估计边际均值（95% CI）", t2n="模型估计值；括号内为 95% CI。", out="结局", t3="研究二次要结局",
        t3n="组间差异为时间×组别交互项（95% CI）；BH q 为类别内校正。", ind="指标", chg="变化量 (干预组)", chg_c="变化量 (对照组)", diff="组间差 (95% CI)",
        f1="受试者流程。蓝灰框为受试者流动，深蓝框为进入主要结局分析的样本量。", f2="四个干预日血糖曲线。a，均值 ± SEM；b，相对基线变化；c，与 CON 的逐点配对差及 95% CI（未校正）。",
        f3="主要结局。a，个体观测与模型估计 ± 95% CI；b，条件间差值；c，剂量–反应。", f4="关键结局的个体前后轨迹。细线为个体，粗线为组均值 ± SEM。",
        f5="全部结局的标准化效应量森林图。", f6="a，TAR/TIR/TBR 占比；b，日内曲线（中位数与 IQR）；c，依从性与改善幅度。", res="3  结果", s1="3.1  受试者与流程", s2="3.2  主要结局",
        txt="共纳入 {n} 名受试者，按 1∶1 分为干预组与对照组。主要结局上，三个运动条件均低于 CON（图 2、图 3，表 2）。以下全部数字来自合成数据，仅用于演示版式。",
        names=["血糖 TIR (%)", "平均血糖 (mmol/L)", "HbA1c (%)", "空腹胰岛素†", "总胆固醇", "血红蛋白", "骨骼肌量 (kg)", "体脂率 (%)", "握力 (kg)", "30 s 坐站 (次)", "TUG (s)", "步速 (m/s)"],
        flow=dict(a="入组\nn = {n}", b="随机 1∶1\nn = {n}", c="对照组  n = {n}", d="干预组  n = {n}", e="完成第 12 周\nn = {n}", f="可分析\nn = {n}"),
    ),
    "en": dict(
        conds=["CON", "RT20", "RT30", "RT45"], cond_names={"CON": "CON (seated)", "RT20": "RT20", "RT30": "RT30", "RT45": "RT45"},
        arms=("Control", "Intervention"), baseline="Baseline", wk="Week 12", xt="Clock time (h)", yt="Glucose (mmol/L)", dt="Paired difference vs CON (mmol/L)",
        rel_t="Time after start (h)", rel_y="Change from baseline (mmol/L)", meal="Meal", window="Exercise", sub_a="a  24-h curves", auc="0–6 h net iAUC (mmol·h/L)",
        contrast="Difference between conditions (mmol·h/L)\n← greater reduction", thr="10% clinical threshold", dose="Total sets per session", dose_y="Change vs CON (mmol·h/L)",
        sets=["12 sets\nRT20", "18 sets\nRT30", "24 sets\nRT45"], trend="Linear trend {b:.2f} per 6 sets, {p}",
        eff="Change in intervention − control (Hedges g, 95% CI)\nPositive = favourable; grey = safety / neutral outcomes",
        foot="Filled = BH-FDR q < 0.05; † = log-transformed analysis", cats=["Glycaemic", "Blood", "Function"], tin="TIR 3.9–10.0", tar="TAR >10.0", tbr="TBR <3.9",
        pct="Share of readings (%)", clock="Clock time", adh="Training adherence (%)", dy="Change in TIR (percentage points)", resp="Intervention arm, 14-d daily profile",
        group_diff="Between-group {b:+.2f} ({lo:.2f}, {hi:.2f})\n{p}",
        t1="Baseline characteristics by arm", t1n="Mean ± SD or n (%). P: independent t test or Fisher exact test; SMD: standardised mean difference.", var="Variable",
        tot="All", age="Age (years)", bmi="BMI (kg/m²)", male="Male", t2="Estimated marginal means for the crossover outcomes (95% CI)", t2n="Model estimates; 95% CI in parentheses.", out="Outcome",
        t3="Secondary outcomes of the parallel-group study", t3n="Between-group difference is the time × group interaction (95% CI); BH q is adjusted within category.",
        ind="Outcome", chg="Change (intervention)", chg_c="Change (control)", diff="Between-group difference (95% CI)",
        f1="Participant flow. Grey-blue boxes show participant flow; the navy-edged box gives the sample entering the primary analysis.",
        f2="Intervention-day glucose curves. a, mean ± SEM; b, change from baseline; c, pointwise paired difference vs CON with 95% CI (unadjusted).",
        f3="Primary outcome. a, individual observations and model estimate ± 95% CI; b, differences between conditions; c, dose–response.",
        f4="Individual pre–post trajectories of key outcomes. Thin lines are individuals; thick lines are group mean ± SEM.",
        f5="Forest plot of standardised effects for all outcomes.", f6="a, TAR/TIR/TBR composition; b, daily profile (median and IQR); c, adherence versus improvement.",
        res="3  Results", s1="3.1  Participants and flow", s2="3.2  Primary outcome",
        txt="A total of {n} participants were allocated 1∶1 to the intervention or control arm. For the primary outcome, all three exercise conditions were lower than CON "
            "(Figures 2 and 3; Table 2). Every number below comes from synthetic data and serves only to demonstrate the layout.",
        names=["TIR (%)", "Mean glucose (mmol/L)", "HbA1c (%)", "Fasting insulin†", "Total cholesterol", "Haemoglobin", "Skeletal muscle mass (kg)", "Body fat (%)", "Grip strength (kg)",
               "30-s sit-to-stand (reps)", "TUG (s)", "Gait speed (m/s)"],
        flow=dict(a="Enrolled\nn = {n}", b="Randomised 1∶1\nn = {n}", c="Control  n = {n}", d="Intervention  n = {n}", e="Completed week 12\nn = {n}", f="Analysed\nn = {n}"),
    ),
}


# ----------------------------------------------------------------------------- synthetic data (replace with real analysis output)
def synth(seed=7):
    rng = np.random.default_rng(seed)
    n = 40
    h = np.arange(0, 24.01, 0.25)                                    # hours after t0
    def meal(h, t0, amp, tp=1.1):
        u = np.maximum(h - t0, 0)
        return amp * ((u / tp) * np.exp(1 - u / tp)) ** 2 * (u > 0)
    base = 7.0 + 0.9 * rng.standard_normal(n)
    eff = {"CON": 0.0, "RT20": 0.7, "RT30": 0.85, "RT45": 1.0}
    curves = {}
    for c, e in eff.items():
        arr = np.empty((n, len(h)))
        for i in range(n):
            drop = e * 1.5 * (1 - np.exp(-h / 0.4)) * np.exp(-h / 2.5) / 0.627
            amp = 3.6 * (1 - 0.25 * e * np.exp(-np.maximum(h - 3, 0) / 10))
            arr[i] = base[i] + 1.2 * meal(h, -1.5, 3.4) + meal(h, 3, amp) + meal(h, 9, 3.0) + meal(h, 22.5, 3.6) - drop + rng.normal(0, 0.45, len(h))
        curves[c] = arr
    return rng, n, h, base, curves


def run(lang: str, out: Path) -> None:
    L = LABELS[lang]
    apply_style(lang)
    rng, n, h, base, curves = synth()
    conds = L["conds"]
    col = condition_colors(conds)
    figdir = out / "figures"
    # ------------------------------------------------------------------ Fig 2: time-course compound
    fig = plt.figure(figsize=(DOUBLE, 5.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 1], hspace=0.52, wspace=0.28)
    ax = fig.add_subplot(gs[0, :])
    ser = {c: (curves[c].mean(0), curves[c].std(0, ddof=1) / np.sqrt(n)) for c in conds}
    ax.axhspan(3.9, 10.0, color="#F3F4F6", lw=0, zorder=0)
    pf.ax_bands(ax, h, ser, col, dashed=["CON"])
    ax.set_xlim(0, 24); ax.set_ylim(3, 15)
    pf.shade_window(ax, 0, 1, text_y=3.25, text=L["window"])
    pf.mark_events(ax, [(3, L["meal"] + " 12:30"), (9, L["meal"] + " 18:30")], y=15.0, label_dy=0.3)
    ax.set_xlabel(L["xt"]); ax.set_ylabel(L["yt"])
    for c, (x, y) in zip(conds, [(11.6, 14), (11.6, 13), (16.4, 14), (16.4, 13)]):
        ax.plot([x - 0.9, x - 0.2], [y, y], color=col[c], lw=1.6, ls=(0, (3, 2)) if c == "CON" else "-")
        ax.text(x, y, f"{L['cond_names'][c]} (n={n})", va="center", fontsize=6.5)
    panel_letter(ax, "a", dx=-0.045)
    ax = fig.add_subplot(gs[1, 0])
    k = h <= 6
    delta = {c: curves[c][:, k] - curves[c][:, :1] for c in conds}
    pf.ax_bands(ax, h[k], {c: (delta[c].mean(0), delta[c].std(0, ddof=1) / np.sqrt(n)) for c in conds}, col, dashed=["CON"])
    ax.axhline(0, color=C_GREY, lw=0.5); pf.shade_window(ax, 0, 1)
    ax.set_xlabel(L["rel_t"]); ax.set_ylabel(L["rel_y"]); panel_letter(ax, "b", dx=-0.14)
    ax = fig.add_subplot(gs[1, 1])
    diffs = {c: pf.pointwise_diff_ci(curves[c][:, k], curves["CON"][:, k]) for c in conds[1:]}
    pf.ax_diff_band(ax, h[k], diffs, col, ref_label="CON"); pf.shade_window(ax, 0, 1)
    ax.set_xlabel(L["rel_t"]); ax.set_ylabel(L["dt"]); panel_letter(ax, "c", dx=-0.14)
    save_figure(fig, figdir / "fig2_timecourse")

    # ------------------------------------------------------------------ Fig 3: paired estimate compound
    auc = {c: np.trapz(curves[c][:, k] - curves[c][:, :1], h[k], axis=1) for c in conds}
    wide = pd.DataFrame(auc)
    for c in conds:                                                  # some missing observations, as in real trials
        wide.loc[rng.choice(n, 4, replace=False), c] = np.nan
    est = {}
    for c in conds:
        v = wide[c].dropna(); se = v.std(ddof=1) / np.sqrt(len(v)); tc = stats.t.ppf(0.975, len(v) - 1)
        est[c] = (v.mean(), v.mean() - tc * se, v.mean() + tc * se)
    fig = plt.figure(figsize=(DOUBLE, 3.35))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1.0, 0.95], wspace=0.5)
    ax = fig.add_subplot(gs[0])
    nfull = pf.ax_paired_estimate(ax, wide, conds, col, est, L["auc"], label_map=L["cond_names"])
    panel_letter(ax, "a", dx=-0.16, dy=1.07)
    ax = fig.add_subplot(gs[1])
    rows = []
    for c in conds[1:]:
        d = (wide[c] - wide["CON"]).dropna(); se = d.std(ddof=1) / np.sqrt(len(d)); tc = stats.t.ppf(0.975, len(d) - 1)
        rows.append(dict(label=f"{c} − CON", est=d.mean(), lo=d.mean() - tc * se, hi=d.mean() + tc * se, color=col[c], ptext=fmt_p(stats.ttest_1samp(d, 0).pvalue)))
    pf.ax_contrast_forest(ax, rows, L["contrast"], threshold=-0.1 * abs(est["CON"][0]), threshold_label=L["thr"])
    panel_letter(ax, "b", dx=-0.42, dy=1.07)
    ax = fig.add_subplot(gs[2])
    doses = {}
    for c, s in zip(conds[1:], (12, 18, 24)):
        d = (wide[c] - wide["CON"]).dropna(); se = d.std(ddof=1) / np.sqrt(len(d)); tc = stats.t.ppf(0.975, len(d) - 1)
        doses[c] = dict(x=s, diffs=d.values, est=d.mean(), lo=d.mean() - tc * se, hi=d.mean() + tc * se)
    xs = np.array([12, 18, 24]); ys = np.array([doses[c]["est"] for c in conds[1:]]); b1, b0 = np.polyfit(xs, ys, 1)
    pf.ax_dose_response(ax, doses, col, L["dose"], L["dose_y"], trend=(b1, b0), note=L["trend"].format(b=b1 * 6, p=fmt_p(stats.linregress(xs, ys).pvalue)),
                        xtick_labels=dict(zip(conds[1:], L["sets"])))
    panel_letter(ax, "c", dx=-0.2, dy=1.07)
    save_figure(fig, figdir / "fig3_paired_estimate")

    # ------------------------------------------------------------------ study B synthetic outcomes
    m = 40
    arm = np.array([0] * (m // 2) + [1] * (m // 2))
    spec = [  # name, baseline mean, sd, true change (intervention), control drift, direction, category, log
        (L["names"][0], 78, 14, 7.0, -1.0, 1, 0, False), (L["names"][1], 8.5, 1.2, -0.6, 0.0, -1, 0, False), (L["names"][2], 7.8, 0.9, -0.6, -0.1, -1, 1, False),
        (L["names"][3], 8.5, 3, -1.0, -0.3, -1, 1, True), (L["names"][4], 5.0, 0.9, -0.2, 0.0, -1, 1, False), (L["names"][5], 138, 11, 0.0, 0.0, 0, 1, False),
        (L["names"][6], 25, 5, 0.7, -0.1, 1, 2, False), (L["names"][7], 29, 5, -1.0, 0.0, -1, 2, False), (L["names"][8], 29, 8, 1.8, 0.2, 1, 2, False),
        (L["names"][9], 14, 4, 3.0, 0.4, 1, 2, False), (L["names"][10], 7.7, 1.4, -0.8, -0.1, -1, 2, False), (L["names"][11], 1.15, 0.17, 0.07, 0.01, 1, 2, False)]
    z = rng.normal(size=m)
    long_rows, eff_rows, tab3 = [], [], []
    for name, mu, sd, dch, cdr, dr, cat, lg in spec:
        b = rng.normal(mu, sd, m)
        ch = np.where(arm == 1, dch, cdr) + 0.5 * np.sign(dch) * (sd * 0.25) * z * (arm == 1) + rng.normal(0, sd * 0.22, m)
        p = b + ch
        for i in range(m):
            long_rows.append((name, i, int(arm[i]), 0, b[i]))
            long_rows.append((name, i, int(arm[i]), 1, p[i]))
        a_, c_ = ch[arm == 1], ch[arm == 0]
        sp = np.sqrt(((len(a_) - 1) * a_.var(ddof=1) + (len(c_) - 1) * c_.var(ddof=1)) / (len(a_) + len(c_) - 2))
        g = (a_.mean() - c_.mean()) / sp * (1 - 3 / (4 * m - 9)); se = np.sqrt(m / (len(a_) * len(c_)) + g ** 2 / (2 * m))
        pval = stats.ttest_ind(a_, c_).pvalue
        sg = dr if dr else 1                                    # orient so that + = favourable; swap bounds when the sign flips
        glo, ghi = sorted([(g - 1.96 * se) * sg, (g + 1.96 * se) * sg])
        eff_rows.append(dict(name=name, cat=cat, g=g * sg, lo=glo, hi=ghi, p=pval, neutral=dr == 0,
                             d=a_.mean() - c_.mean(), lo_d=(a_.mean() - c_.mean()) - 1.96 * sp * np.sqrt(1 / len(a_) + 1 / len(c_)), hi_d=(a_.mean() - c_.mean()) + 1.96 * sp * np.sqrt(1 / len(a_) + 1 / len(c_)),
                             mi=a_.mean(), mc=c_.mean()))
    # BH within category
    for cat in range(3):
        idx = [i for i, r in enumerate(eff_rows) if r["cat"] == cat]
        ps = np.array([eff_rows[i]["p"] for i in idx]); o = np.argsort(ps); adj = np.empty(len(ps)); prev = 1.0
        for rank in range(len(ps) - 1, -1, -1):
            prev = min(prev, ps[o[rank]] * len(ps) / (rank + 1)); adj[o[rank]] = prev
        for i, a in zip(idx, adj):
            eff_rows[i]["q"] = a
    long_df = pd.DataFrame(long_rows, columns=["name", "id", "arm", "t", "y"])
    arms = L["arms"]
    long_df["group"] = long_df["arm"].map({0: arms[0], 1: arms[1]})
    acol = arm_colors(*arms)

    # ------------------------------------------------------------------ Fig 4: pre/post
    fig, axes = plt.subplots(2, 3, figsize=(DOUBLE, 5.2), gridspec_kw=dict(hspace=0.62, wspace=0.38))
    pick = [0, 2, 6, 8, 9, 10]
    for kx, (ix, ax) in enumerate(zip(pick, axes.ravel())):
        r = eff_rows[ix]
        sub = long_df[long_df["name"] == r["name"]]
        title = L["group_diff"].format(b=r["d"], lo=r["lo_d"], hi=r["hi_d"], p=fmt_p(r["p"]))
        pf.ax_prepost(ax, sub, "id", "group", "t", "y", arms, acol, [L["baseline"], L["wk"]], r["name"], title=title)
        panel_letter(ax, "abcdef"[kx], dx=-0.22, dy=1.22)
    save_figure(fig, figdir / "fig4_prepost")

    # ------------------------------------------------------------------ Fig 5: forest
    cat_cols = {L["cats"][0]: C_MAGENTA, L["cats"][1]: C_CORAL, L["cats"][2]: C_TEAL}
    rows = [dict(category=L["cats"][r["cat"]], label=r["name"], g=r["g"], lo=r["lo"], hi=r["hi"], sig=r["q"] < 0.05 and not r["neutral"], neutral=r["neutral"],
                 text="q < 0.001" if r["q"] < 0.001 else f"q = {r['q']:.3f}") for r in eff_rows]
    fig = pf.fig_forest_effects(rows, L["cats"], cat_cols, L["eff"], footnote=L["foot"], row_h=0.25)
    save_figure(fig, figdir / "fig5_forest")

    # ------------------------------------------------------------------ Fig 6: composition + profile + scatter
    fig = plt.figure(figsize=(DOUBLE, 2.9))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1.2, 1], wspace=0.42)
    ax = fig.add_subplot(gs[0])
    bars = []
    for gi in (0, 1):
        for tt, lab in ((0, L["baseline"]), (1, L["wk"])):
            v = long_df[(long_df["name"] == L["names"][0]) & (long_df["arm"] == gi) & (long_df["t"] == tt)]["y"].clip(0, 100)
            tir = float(v.mean()); tbr = 0.6; tar = 100 - tir - tbr
            bars.append((lab, {"TBR": tbr, "TIR": tir, "TAR": tar}))
    pf.ax_stacked_bars(ax, bars, ["TBR", "TIR", "TAR"], {"TBR": C_CORAL, "TIR": C_SLATE, "TAR": C_AMBER}, L["pct"], positions=[0, 0.9, 2.2, 3.1],
                       group_labels=[(0.45, arms[0], acol[arms[0]]), (2.65, arms[1], acol[arms[1]])])
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in (C_AMBER, C_SLATE, C_CORAL)], labels=[L["tar"], L["tin"], L["tbr"]], loc="upper center",
              bbox_to_anchor=(0.5, 1.22), ncol=3, fontsize=5.5, handlelength=1, columnspacing=0.8)
    panel_letter(ax, "a", dx=-0.2, dy=1.1)
    ax = fig.add_subplot(gs[1])
    xh = np.arange(288) * 5 / 60
    for c_, lab, colr in ((0, L["baseline"], C_SLATE), (1, L["wk"], C_MAGENTA)):
        shift = 0.0 if c_ == 0 else -0.8
        curve = 7.5 + shift + 2.6 * np.exp(-0.5 * ((xh - 9) / 1.1) ** 2) + 2.2 * np.exp(-0.5 * ((xh - 13.5) / 1.1) ** 2) + 2.2 * np.exp(-0.5 * ((xh - 19.5) / 1.1) ** 2)
        q = {50: curve, 25: curve - 1.0, 75: curve + 1.2, 5: curve - 2.0, 95: curve + 3.4}
        pf.ax_agp(ax, xh, q, colr, lab)
    ax.set_xlim(0, 24); ax.set_xticks(range(0, 25, 6)); ax.set_xlabel(L["clock"]); ax.set_ylabel(L["yt"]); ax.legend(loc="upper left", fontsize=6)
    ax.set_title(L["resp"], loc="left", fontsize=7, pad=4)
    panel_letter(ax, "b", dx=-0.2, dy=1.1)
    ax = fig.add_subplot(gs[2])
    adh = rng.uniform(55, 98, 20); dtir = 0.35 * (adh - 80) + rng.normal(6, 7, 20)
    pf.ax_scatter_fit(ax, adh, dtir, C_MAGENTA, L["adh"], L["dy"])
    panel_letter(ax, "c", dx=-0.2, dy=1.1)
    save_figure(fig, figdir / "fig6_composition_profile_scatter")

    # ------------------------------------------------------------------ Fig 1: flow
    fig, ax = plt.subplots(figsize=(DOUBLE, 3.2))
    F = L["flow"]
    boxes = [dict(x=0.5, y=0.9, w=0.3, h=0.12, text=F["a"].format(n=m + 10), fc="#F5F3FA"), dict(x=0.5, y=0.68, w=0.3, h=0.12, text=F["b"].format(n=m)),
             dict(x=0.27, y=0.46, w=0.3, h=0.12, text=F["c"].format(n=m // 2), ec=C_AMBER, fc="#FEF7E6"), dict(x=0.73, y=0.46, w=0.3, h=0.12, text=F["d"].format(n=m // 2), ec=C_MAGENTA, fc="#F7E9F3"),
             dict(x=0.27, y=0.24, w=0.3, h=0.12, text=F["e"].format(n=m // 2 - 2), ec=C_AMBER), dict(x=0.73, y=0.24, w=0.3, h=0.12, text=F["e"].format(n=m // 2 - 3), ec=C_MAGENTA),
             dict(x=0.5, y=0.03, w=0.46, h=0.1, text=F["f"].format(n=m - 5), ec=C_MAGENTA, lw=1.2)]
    arrows = [(0.5, 0.84, 0.5, 0.74), (0.45, 0.62, 0.3, 0.52), (0.55, 0.62, 0.7, 0.52), (0.27, 0.4, 0.27, 0.3), (0.73, 0.4, 0.73, 0.3), (0.3, 0.18, 0.4, 0.08), (0.7, 0.18, 0.6, 0.08)]
    pf.draw_flow(ax, boxes, arrows, ylim=(-0.05, 1.0))
    save_figure(fig, figdir / "fig1_flow")

    # ------------------------------------------------------------------ tables
    T1 = pd.DataFrame([[L["age"], fmt_msd(rng.normal(62, 5, m)), fmt_msd(rng.normal(62, 5, 20)), fmt_msd(rng.normal(62, 5, 20)), "0.05", "0.80"],
                       [L["bmi"], fmt_msd(rng.normal(26, 2.4, m)), fmt_msd(rng.normal(26, 2.4, 20)), fmt_msd(rng.normal(26, 2.4, 20)), "0.10", "0.61"],
                       [L["male"], fmt_n_pct(rng.random(m) < .5), fmt_n_pct(rng.random(20) < .5), fmt_n_pct(rng.random(20) < .5), "0.20", "0.53"]],
                      columns=[L["var"], f"{L['tot']} (n={m})", f"{arms[0]} (n=20)", f"{arms[1]} (n=20)", "SMD", "P"])
    T2 = pd.DataFrame([[L["auc"]] + [fmt_ci(*est[c], nd=1) for c in conds]], columns=[L["out"]] + [L["cond_names"][c] for c in conds])
    T3 = pd.DataFrame([[r["name"] + ("†" if "†" in r["name"] else ""), msd_(r, "mi"), msd_(r, "mc"), fmt_ci(r["d"], r["lo_d"], r["hi_d"]), fmt_p_table(r["p"]), fmt_p_table(r["q"])] for r in eff_rows],
                      columns=[L["ind"], f"{L['chg']}", f"{L['chg_c']}", L["diff"], "P", "BH q"])
    save_tables_xlsx({"Table1": T1, "Table2": T2, "Table3": T3}, out / "tables" / "tables.xlsx")

    # ------------------------------------------------------------------ docx
    d = ResultsDoc(lang)
    d.title(L["res"]); d.notice()
    d.heading(L["s1"], 2); d.para(L["txt"].format(n=m))
    d.figure(figdir / "fig1_flow.png", L["f1"], 15)
    d.table(T1, L["t1"], L["t1n"], col_widths=[4.6, 3.0, 3.0, 3.0, 1.6, 1.6])
    d.heading(L["s2"], 2)
    d.figure(figdir / "fig2_timecourse.png", L["f2"]); d.figure(figdir / "fig3_paired_estimate.png", L["f3"])
    d.table(T2, L["t2"], L["t2n"], col_widths=[4.2, 3.2, 3.2, 3.2, 3.2])
    d.figure(figdir / "fig4_prepost.png", L["f4"]); d.figure(figdir / "fig5_forest.png", L["f5"], 15); d.figure(figdir / "fig6_composition_profile_scatter.png", L["f6"])
    d.table(T3, L["t3"], L["t3n"], col_widths=[4.2, 2.6, 2.6, 3.6, 1.4, 1.4])
    d.save(out / "results.docx")
    print(f"[{lang}] wrote {out}")


def msd_(r, key):
    return f"{r[key]:.2f}" if abs(r[key]) < 10 else f"{r[key]:.1f}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=["zh", "en", "both"], default="both")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "outputs" / "pubstyle_demo"))
    a = ap.parse_args()
    for lg in (["zh", "en"] if a.lang == "both" else [a.lang]):
        run(lg, Path(a.out) / lg)
