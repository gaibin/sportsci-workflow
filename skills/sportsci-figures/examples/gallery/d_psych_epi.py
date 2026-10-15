# -*- coding: utf-8 -*-
"""D15 心理量表 · D16 损伤生存 · D17 诊断 ROC · D18 荟萃分析"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy import stats

from common import ddir, read, save, wilson, write_readme
from sportsci_figures.pubstyle.figures import *  # noqa: F401,F403   (all blocks, incl. figures_ext)
from sportsci_figures.pubstyle.style import tr as L, get_lang  # noqa: F401
from sportsci_figures.pubstyle import DOUBLE, panel_letter, arm_colors, fmt_p, condition_colors
from sportsci_figures.pubstyle import figures as pf
from sportsci_figures.pubstyle.style import C_AMBER, C_MAGENTA, C_SLATE, C_CORAL, C_GREY, C_INK, C_LIGHT, C_TEAL, C_PALE_SLATE, C_PALE_CONTRAST, get_lang

GRP = ("Control", "Intervention")


def gname():
    return {"Control": L("对照组", "Control"), "Intervention": L("干预组", "Intervention")}


# ============================================================================ D15 psychology
def sim_d15(seed=15):
    rng = np.random.default_rng(seed)
    n = 120
    ids = [f"P{i:03d}" for i in range(1, n + 1)]
    grp = np.array(["Control"] * 60 + ["Intervention"] * 60)
    g = (grp == "Intervention").astype(int)
    z = rng.normal(size=n)                                       # individual symptom trait
    se0 = np.clip(rng.normal(26, 5, n), 10, 40)                  # self-efficacy baseline
    d_se = 4.0 * g + rng.normal(0, 4.5, n)                       # intervention raises self-efficacy
    se1 = np.clip(se0 + d_se, 10, 40)
    gad0 = np.clip(np.round(11 + 3 * z + rng.normal(0, 1.5, n)), 0, 21)
    d_gad = -1.3 * g - 0.55 * d_se + 0.35 * z * 0 + rng.normal(0, 3.3, n) - 0.5          # b = -0.55 per SE point
    gad1 = np.clip(np.round(gad0 + d_gad), 0, 21)
    gad2 = np.clip(np.round(gad0 + 0.85 * d_gad + rng.normal(0, 2.0, n)), 0, 21)
    phq0 = np.clip(np.round(10 + 3.5 * z + rng.normal(0, 2, n)), 0, 27)
    phq1 = np.clip(np.round(phq0 - 3.4 * g - 1.0 + rng.normal(0, 3.4, n)), 0, 27)
    phq2 = np.clip(np.round(phq0 - 2.8 * g - 1.2 + rng.normal(0, 3.6, n)), 0, 27)
    res0 = np.clip(np.round(24 - 1.2 * z + rng.normal(0, 4, n)), 0, 40)
    res1 = np.clip(np.round(res0 + 4.5 * g + 1 + rng.normal(0, 3.5, n)), 0, 40)
    res2 = np.clip(np.round(res0 + 3.6 * g + 1 + rng.normal(0, 3.8, n)), 0, 40)
    sleep0 = np.clip(np.round(9 - 1.5 * z + rng.normal(0, 2.2, n)), 0, 21)       # PSQI-like (higher = worse)
    sleep1 = np.clip(np.round(sleep0 - 2.3 * g - 0.4 + rng.normal(0, 2.4, n)), 0, 21)
    sleep2 = np.clip(np.round(sleep0 - 1.8 * g - 0.4 + rng.normal(0, 2.6, n)), 0, 21)
    rows = []
    for i in range(n):
        for tm, a, b, c, d in (("Baseline", gad0, phq0, res0, sleep0), ("Post", gad1, phq1, res1, sleep1), ("FU3m", gad2, phq2, res2, sleep2)):
            rows.append((ids[i], grp[i], tm, a[i], b[i], c[i], d[i], (se0 if tm == "Baseline" else se1)[i] if tm != "FU3m" else se1[i] - 0.5))
    psych = pd.DataFrame(rows, columns=["id", "group", "time", "gad7", "phq9", "resilience", "psqi", "self_efficacy"])
    psych.to_csv(ddir("D15_心理量表") / "psych_scores.csv", index=False)
    # PHQ-9 items at post (0–3), latent from phq1
    thr = np.array([0.2, 0.3, 0.45, 0.5, 0.35, 0.4, 0.25, 0.2, 0.05])
    items = {}
    for k in range(9):
        lat = (phq1 / 27) * 3 + rng.normal(0, 0.55, n) - 0.15 + (thr[k] - 0.3) * 1.2
        items[f"item{k + 1}"] = np.clip(np.round(lat), 0, 3).astype(int)
    pd.concat([pd.DataFrame({"id": ids, "group": grp}), pd.DataFrame(items)], axis=1).to_csv(ddir("D15_心理量表") / "phq9_items_post.csv", index=False)
    # POMS T-scores
    poms_means = dict(Tension=(54, 48), Depression=(52, 47), Anger=(50, 46), Vigor=(50, 56), Fatigue=(53, 47), Confusion=(49, 45))
    pr = []
    for i in range(n):
        r = {"id": ids[i], "group": grp[i]}
        for k, (mc, mi) in poms_means.items():
            r[k.lower()] = round(rng.normal(mi if g[i] else mc, 8), 1)
        pr.append(r)
    pd.DataFrame(pr).to_csv(ddir("D15_心理量表") / "poms_post.csv", index=False)
    pd.DataFrame({"id": ids, "group": grp, "x_intervention": g, "m_delta_self_efficacy": (se1 - se0).round(2), "y_delta_gad7": (gad1 - gad0)}).to_csv(ddir("D15_心理量表") / "mediation.csv", index=False)
    write_readme("D15_心理量表", "心理问卷量表（RCT，三个时点）", "Psychological questionnaires (RCT, 3 time points)",
                 "120 名受试者，干预 vs 对照；基线 / 干预后 / 3 个月随访。含 GAD-7、PHQ-9、韧性、睡眠质量、自我效能；PHQ-9 逐题；POMS 六个分量表；中介分析数据。",
                 {"psych_scores.csv": ("每人每时点一行的量表总分（长表）", "Scale totals, one row per person per time point", {"id": ("受试者", "Participant"), "group": ("分组", "Group"), "time": ("时点", "Time point"), "gad7": ("焦虑 0–21", "Anxiety 0–21"), "phq9": ("抑郁 0–27", "Depression 0–27"), "resilience": ("韧性 0–40", "Resilience 0–40"), "psqi": ("睡眠问题 0–21（越高越差）", "Sleep problems 0–21 (higher = worse)"), "self_efficacy": ("自我效能 10–40", "Self-efficacy 10–40")}),
                  "phq9_items_post.csv": ("PHQ-9 九个条目（0–3），干预后", "PHQ-9 items (0–3) at post", {"item1..9": ("条目得分", "Item score")}),
                  "poms_post.csv": ("POMS 六个分量表 T 分，干预后", "POMS subscale T-scores at post", {"tension..confusion": ("T 分", "T-score")}),
                  "mediation.csv": ("中介分析：x=分组，m=自我效能变化，y=焦虑变化", "Mediation: x = group, m = change in self-efficacy, y = change in anxiety", {"x_intervention": ("0/1", "0/1"), "m_delta_self_efficacy": ("m", "m"), "y_delta_gad7": ("y", "y")})})


def fig_d15(lang):
    d = ddir("D15_心理量表")
    df = pd.read_csv(d / "psych_scores.csv")
    it = pd.read_csv(d / "phq9_items_post.csv"); po = pd.read_csv(d / "poms_post.csv"); me = pd.read_csv(d / "mediation.csv")
    gn = gname(); col = {gn[k]: v for k, v in arm_colors("Control", "Intervention").items()}
    cc = arm_colors(*[gn[k] for k in GRP])
    # ---------------- Fig 1: overview
    df["g"] = df["group"].map(gn)
    fig = plt.figure(figsize=(DOUBLE, 3.1))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1, 0.8], wspace=0.42)
    ax = fig.add_subplot(gs[0])
    tl = [L("基线", "Baseline"), L("干预后", "Post"), L("随访 3 个月", "3-mo follow-up")]
    ax_multitime(ax, df, "id", "g", "time", "gad7", list(gn.values()), cc, ["Baseline", "Post", "FU3m"], tl, L("焦虑 GAD-7 (0–21)", "Anxiety, GAD-7 (0–21)"))
    ax.legend(loc="upper right", fontsize=6); panel_letter(ax, "a", dx=-0.17)
    ax = fig.add_subplot(gs[1])
    w = df.pivot_table(index=["id", "g"], columns="time", values="gad7").reset_index()
    w["chg"] = w["Post"] - w["Baseline"]
    ax_raincloud(ax, {g_: w[w["g"] == g_]["chg"].values for g_ in gn.values()}, cc, L("GAD-7 变化 (基线→干预后)", "Change in GAD-7 (baseline → post)"))
    ax.axhline(0, color=C_GREY, lw=0.5, ls=":"); panel_letter(ax, "b", dx=-0.22)
    ax = fig.add_subplot(gs[2])
    for i, g_ in enumerate(gn.values()):
        s = w[w["g"] == g_]; k = int(((s["Baseline"] - s["Post"]) / s["Baseline"] >= 0.5).sum()); p, lo, hi = wilson(k, len(s))
        ax.bar(i, p * 100, width=0.62, color=cc[g_], alpha=0.9, lw=0)
        ax.errorbar(i, p * 100, yerr=[[p * 100 - lo * 100], [hi * 100 - p * 100]], color=C_INK, capsize=3, lw=1.1)
        ax.text(i, hi * 100 + 2, f"{k}/{len(s)}", ha="center", fontsize=6)
    ax.set_xticks([0, 1]); ax.set_xticklabels(list(gn.values())); ax.tick_params(axis="x", length=0)
    ax.set_ylabel(L("缓解率：GAD-7 降幅 ≥50% (%)", "Responders: GAD-7 reduction ≥50% (%)")); ax.set_ylim(0, 100); hair_y(ax); panel_letter(ax, "c", dx=-0.3)
    save(fig, "D15_心理量表", "fig1_scale_overview", lang)
    # ---------------- Fig 2: items + correlation + radar
    fig = plt.figure(figsize=(DOUBLE, 5.6))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.05, 1], width_ratios=[1, 1, 1.0], hspace=0.55, wspace=0.5)
    names9 = L(["兴趣减退", "情绪低落", "睡眠问题", "疲劳", "食欲改变", "自我否定", "注意力差", "迟滞或烦躁", "自伤念头"],
               ["Little interest", "Feeling down", "Sleep problems", "Tired", "Appetite", "Feeling bad about self", "Poor concentration", "Slowed/restless", "Self-harm thoughts"])
    lev = L(["完全没有", "几天", "一半以上天数", "几乎每天"], ["Not at all", "Several days", "More than half", "Nearly every day"])
    lik4 = [C_SLATE, C_PALE_SLATE, C_PALE_CONTRAST, C_CORAL]
    for j, gk in enumerate(GRP):
        ax = fig.add_subplot(gs[0, j])
        sub = it[it["group"] == gk]
        pct = np.array([[(sub[f"item{k + 1}"] == v).mean() * 100 for v in range(4)] for k in range(9)])
        for i in range(9):
            left = 0
            for v in range(4):
                ax.barh(i, pct[i, v], left=left, color=lik4[v], height=0.7, lw=0)
                if pct[i, v] >= 12:
                    ax.text(left + pct[i, v] / 2, i, f"{pct[i, v]:.0f}", ha="center", va="center", fontsize=5.2, color=C_INK)
                left += pct[i, v]
        ax.set_yticks(range(9)); ax.set_yticklabels(names9 if j == 0 else [""] * 9); ax.invert_yaxis(); ax.tick_params(axis="y", length=0)
        ax.set_xlim(0, 100); ax.set_xlabel(L("受试者占比 (%)", "Participants (%)")); ax.spines["left"].set_visible(False)
        ax.set_title(gn[gk], fontsize=7, loc="left", color=cc[gn[gk]], fontweight="bold")
        if j == 0:
            panel_letter(ax, "a", dx=-0.62, dy=1.1)
    axl = fig.add_subplot(gs[0, 2]); axl.axis("off")
    axl.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in lik4], labels=lev, loc="center left", fontsize=6, handlelength=1.0, title=L("PHQ-9 条目作答", "PHQ-9 response"), title_fontsize=6)
    base = df[df["time"] == "Post"][["gad7", "phq9", "resilience", "psqi", "self_efficacy"]]
    cn = L(["焦虑", "抑郁", "韧性", "睡眠问题", "自我效能"], ["Anxiety", "Depression", "Resilience", "Sleep problems", "Self-efficacy"])
    corr = base.corr().values
    pv = np.array([[stats.pearsonr(base.iloc[:, i], base.iloc[:, j])[1] if i != j else 0 for j in range(5)] for i in range(5)])
    ax = fig.add_subplot(gs[1, 0:2])
    im = ax_corr_heatmap(ax, corr, cn, pv); panel_letter(ax, "b", dx=-0.3, dy=1.05)
    cb = fig.colorbar(im, ax=ax, fraction=0.05, pad=0.03); cb.ax.tick_params(labelsize=5); cb.outline.set_linewidth(0.4)
    ax.set_title(L("干预后各量表相关（粗体 P<0.05）", "Correlations at post (bold P<0.05)"), fontsize=6, loc="left", pad=3)
    ax = fig.add_subplot(gs[1, 2], projection="polar")
    cats = ["tension", "depression", "anger", "vigor", "fatigue", "confusion"]
    cl = L(["紧张", "抑郁", "愤怒", "活力", "疲劳", "困惑"], ["Tension", "Depression", "Anger", "Vigor", "Fatigue", "Confusion"])
    ser = {gn[gk]: [po[po["group"] == gk][c].mean() for c in cats] for gk in GRP}
    ax_radar(ax, cl, ser, cc, rmax=70, rmin=30, ring_step=10)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=2, fontsize=6)
    ax.set_title(L("POMS 剖面（T 分，干预后）", "POMS profile (T-score, post)"), fontsize=7, loc="left", pad=16, x=-0.25)
    panel_letter(ax, "c", dx=-0.32, dy=1.12)
    save(fig, "D15_心理量表", "fig2_items_corr_profile", lang)
    # ---------------- Fig 3: mediation
    x, m, y = me["x_intervention"].values, me["m_delta_self_efficacy"].values, me["y_delta_gad7"].values
    def coefs(xx, mm, yy):
        a = sm.OLS(mm, sm.add_constant(xx)).fit().params[1]
        r2 = sm.OLS(yy, sm.add_constant(np.c_[xx, mm])).fit()
        c = sm.OLS(yy, sm.add_constant(xx)).fit().params[1]
        return a, r2.params[2], r2.params[1], c
    a, b, cp, c = coefs(x, m, y)
    rng = np.random.default_rng(0)
    bs = np.array([coefs(x[i], m[i], y[i])[0:2] for i in (rng.integers(0, len(x), len(x)) for _ in range(2000))])
    ind = bs[:, 0] * bs[:, 1]
    lo, hi = np.percentile(ind, [2.5, 97.5])
    ra = sm.OLS(m, sm.add_constant(x)).fit(); rb = sm.OLS(y, sm.add_constant(np.c_[x, m])).fit(); rc = sm.OLS(y, sm.add_constant(x)).fit()
    f = lambda v, r, k: f"{v:.2f} ({r.conf_int()[k][0]:.2f}, {r.conf_int()[k][1]:.2f})"
    fig = plt.figure(figsize=(DOUBLE, 2.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 1], wspace=0.25)
    ax = fig.add_subplot(gs[0])
    ax_mediation(ax, (L("干预", "Intervention"), L("自我效能变化", "Δ self-efficacy"), L("焦虑变化 (GAD-7)", "Δ anxiety (GAD-7)")), f(a, ra, 1), f(b, rb, 2), f(c, rc, 1), f(cp, rb, 1), f"{a * b:.2f} ({lo:.2f}, {hi:.2f})")
    panel_letter(ax, "a", dx=0.0, dy=1.0)
    ax = fig.add_subplot(gs[1])
    ax.hist(ind, bins=40, color=C_SLATE, alpha=0.8, lw=0)
    ax.axvline(a * b, color=C_MAGENTA, lw=1.4); ax.axvspan(lo, hi, color=C_MAGENTA, alpha=0.12, lw=0); ax.axvline(0, color=C_GREY, lw=0.6, ls=":")
    ax.set_xlabel(L("间接效应 a×b（bootstrap 2000 次）", "Indirect effect a×b (2000 bootstraps)")); ax.set_ylabel(L("频数", "Count")); panel_letter(ax, "b", dx=-0.2)
    save(fig, "D15_心理量表", "fig3_mediation", lang)


# ============================================================================ D16 survival
def sim_d16(seed=16):
    rng = np.random.default_rng(seed)
    n = 200
    prog = np.array(["Standard"] * 100 + ["Prehab"] * 100)
    age = rng.integers(18, 33, n); prior = (rng.random(n) < 0.35).astype(int)
    lam = 0.032 * np.exp(-0.55 * (prog == "Prehab") + 0.04 * (age - 24) + 0.5 * prior)
    t_ev = rng.exponential(1 / lam); t_cen = np.minimum(40, rng.exponential(60, n))
    time = np.minimum(t_ev, t_cen); event = (t_ev <= t_cen).astype(int)
    pd.DataFrame({"id": [f"A{i:03d}" for i in range(1, n + 1)], "program": prog, "age": age, "prior_injury": prior, "time_weeks": time.round(2), "injury": event}).to_csv(ddir("D16_损伤_生存") / "injury.csv", index=False)
    write_readme("D16_损伤_生存", "运动损伤时间-事件（生存分析）", "Time-to-injury (survival analysis)", "200 名运动员，两种预防方案，随访至首次损伤或 40 周删失。",
                 {"injury.csv": ("每人一行", "One row per athlete", {"program": ("方案 Standard/Prehab", "Programme"), "age": ("年龄", "Age"), "prior_injury": ("既往损伤 0/1", "Prior injury 0/1"), "time_weeks": ("随访周数", "Weeks followed"), "injury": ("事件 1=损伤 0=删失", "Event 1 = injury, 0 = censored")})})


def fig_d16(lang):
    from statsmodels.duration.hazard_regression import PHReg
    df = read("D16_损伤_生存", "injury.csv")
    gm = {"Standard": L("常规方案", "Standard"), "Prehab": L("预防方案", "Prehab")}
    cc = {gm["Standard"]: C_AMBER, gm["Prehab"]: C_MAGENTA}
    fig = plt.figure(figsize=(DOUBLE, 4.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[3.4, 1], width_ratios=[1.35, 1], hspace=0.38, wspace=0.34)
    ax = fig.add_subplot(gs[0, 0]); curves, grp = {}, {}
    for k, v in gm.items():
        s = df[df["program"] == k]; curves[v] = km_estimate(s["time_weeks"], s["injury"]); grp[v] = (s["time_weeks"].values, s["injury"].values)
    ax_km(ax, curves, cc, L("随访时间（周）", "Time since start (weeks)"), L("未发生损伤的概率", "Injury-free probability"), xmax=40, ylim=(0.2, 1.02))
    ax.legend(loc="lower left", fontsize=6.3); panel_letter(ax, "a", dx=-0.13)
    at = fig.add_subplot(gs[1, 0], sharex=ax); at_risk_table(at, grp, cc, [0, 10, 20, 30, 40], ""); at.tick_params(axis="x", labelbottom=False); at.tick_params(axis="y", pad=14)
    at.set_title(L("风险集人数", "Number at risk"), fontsize=6, loc="left", pad=1)
    X = pd.DataFrame({"prehab": (df["program"] == "Prehab").astype(int), "age5": (df["age"] - 24) / 5, "prior": df["prior_injury"]})
    m = PHReg(df["time_weeks"].values, X.values, status=df["injury"].values).fit()
    hr, ci = np.exp(m.params), np.exp(m.conf_int())
    ax = fig.add_subplot(gs[0, 1])
    labs = L(["预防方案 vs 常规", "年龄 每 +5 岁", "既往损伤 有 vs 无"], ["Prehab vs standard", "Age, per +5 years", "Prior injury, yes vs no"])
    cols = [C_MAGENTA, C_SLATE, C_CORAL]
    for i in range(3):
        y = 2 - i
        ax.errorbar(hr[i], y, xerr=[[hr[i] - ci[i, 0]], [ci[i, 1] - hr[i]]], fmt="o", ms=5, color=cols[i], ecolor=cols[i], elinewidth=1.5, capsize=2.5, mec="white", mew=0.7)
        ax.text(2.8, y, f"{hr[i]:.2f} ({ci[i, 0]:.2f}, {ci[i, 1]:.2f})\n{fmt_p(m.pvalues[i])}", fontsize=5.6, va="center", linespacing=1.15)
    ax.axvline(1, color=C_GREY, lw=0.7); ax.set_xscale("log"); ax.set_xlim(0.3, 8); ax.set_xticks([0.5, 1, 2]); ax.set_xticklabels(["0.5", "1", "2"])
    ax.set_yticks([2, 1, 0]); ax.set_yticklabels(labs); ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False); ax.set_ylim(-0.6, 2.6)
    ax.set_xlabel(L("校正后风险比 HR（95% CI）", "Adjusted hazard ratio (95% CI)")); panel_letter(ax, "b", dx=-0.62, dy=1.04)
    ax = fig.add_subplot(gs[1, 1])
    for i, (k, v) in enumerate(gm.items()):
        s = df[df["program"] == k]; ev, pt = int(s["injury"].sum()), s["time_weeks"].sum()
        r = ev / pt * 1000; lo = stats.chi2.ppf(0.025, 2 * ev) / 2 / pt * 1000; hi = stats.chi2.ppf(0.975, 2 * ev + 2) / 2 / pt * 1000
        ax.barh(i, r, color=cc[v], height=0.6, lw=0); ax.errorbar(r, i, xerr=[[r - lo], [hi - r]], color=C_INK, capsize=2.5, lw=1)
        ax.text(hi + 1, i, f"{ev}", fontsize=6, va="center")
    ax.set_yticks([0, 1]); ax.set_yticklabels(list(gm.values())); ax.tick_params(axis="y", length=0); ax.set_xlabel(L("损伤率（每 1000 人周）", "Injury rate (per 1000 athlete-weeks)")); ax.set_xlim(0, 60)
    panel_letter(ax, "c", dx=-0.62, dy=1.1)
    save(fig, "D16_损伤_生存", "fig1_survival", lang)


# ============================================================================ D17 diagnostics
def sim_d17(seed=17):
    rng = np.random.default_rng(seed)
    n = 300
    dz = (rng.random(n) < 0.26).astype(int)
    age = rng.normal(72, 6, n)
    grip = rng.normal(27, 7, n) - 7 * dz - 0.15 * (age - 72)
    sarcf = np.clip(np.round(rng.normal(2.2, 1.6, n) + 2.2 * dz), 0, 10)
    calf = rng.normal(34, 3, n) - 2.8 * dz
    gait = np.clip(rng.normal(1.1, 0.22, n) - 0.18 * dz, 0.3, 1.8)
    pd.DataFrame({"id": [f"S{i:03d}" for i in range(1, n + 1)], "sarcopenia": dz, "age": age.round(1), "grip_kg": grip.round(1), "sarcf": sarcf, "calf_cm": calf.round(1), "gait_speed": gait.round(2)}).to_csv(ddir("D17_诊断_ROC") / "screening.csv", index=False)
    write_readme("D17_诊断_ROC", "筛查工具诊断效能", "Diagnostic accuracy of screening tools", "300 名老年人，参考标准为肌少症（患病率约 26%）。",
                 {"screening.csv": ("每人一行", "One row per person", {"sarcopenia": ("参考标准 0/1", "Reference standard 0/1"), "grip_kg": ("握力", "Grip strength"), "sarcf": ("SARC-F 0–10", "SARC-F 0–10"), "calf_cm": ("小腿围", "Calf circumference"), "gait_speed": ("步速 m/s", "Gait speed m/s")})})


def fig_d17(lang):
    df = read("D17_诊断_ROC", "screening.csv")
    y = df["sarcopenia"].values
    X = np.c_[-df["grip_kg"], df["sarcf"], -df["calf_cm"], -df["gait_speed"]]
    lr = sm.Logit(y, sm.add_constant((X - X.mean(0)) / X.std(0))).fit(disp=0)
    comb = lr.predict()
    names = L(["握力", "SARC-F", "小腿围", "联合模型"], ["Grip strength", "SARC-F", "Calf circumference", "Combined model"])
    sc = {names[0]: X[:, 0], names[1]: X[:, 1], names[2]: X[:, 2], names[3]: comb}
    cols = dict(zip(names, [C_SLATE, C_AMBER, C_CORAL, C_MAGENTA]))
    fig = plt.figure(figsize=(DOUBLE, 2.95))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.1, 0.9, 1], wspace=0.5)
    ax = fig.add_subplot(gs[0]); ax_roc(ax, y, sc, cols); panel_letter(ax, "a", dx=-0.2, dy=1.03)
    ax = fig.add_subplot(gs[1]); ax_calibration(ax, comb, y); panel_letter(ax, "b", dx=-0.25, dy=1.03)
    ax = fig.add_subplot(gs[2])
    gn = {0: L("非肌少症", "No sarcopenia"), 1: L("肌少症", "Sarcopenia")}
    ax_raincloud(ax, {gn[k]: comb[y == k] for k in (0, 1)}, {gn[0]: C_SLATE, gn[1]: C_MAGENTA}, L("联合模型预测概率", "Predicted probability (combined)"))
    fpr, tpr, thr = roc_points(y, comb); k = int(np.argmax(tpr - fpr)); cut = thr[k - 1] if k > 0 else 0.5
    ax.axhline(cut, color=C_GREY, lw=0.8, ls=(0, (3, 2))); ax.text(1.45, cut, f"{L('截断值', 'Cut-off')} {cut:.2f}", fontsize=5.6, color=C_GREY, ha="right", va="bottom")
    ax.set_ylim(-0.02, 1.02); panel_letter(ax, "c", dx=-0.3, dy=1.03)
    save(fig, "D17_诊断_ROC", "fig1_roc_calibration", lang)


# ============================================================================ D18 meta-analysis
def sim_d18(seed=18):
    rng = np.random.default_rng(seed)
    k = 18
    mod = rng.choice(["Aerobic", "Resistance", "Combined"], k)
    dur = rng.integers(8, 29, k)
    true = np.where(mod == "Aerobic", -0.45, np.where(mod == "Resistance", -0.55, -0.80)) - 0.012 * (dur - 16)
    n = rng.integers(20, 110, k); se = np.sqrt(4 / n) * rng.uniform(0.9, 1.15, k)
    es = true + rng.normal(0, 0.18, k) + rng.normal(0, se)
    # small-study effect: favour larger effects for small trials
    es = es - 0.35 * (se - se.mean())
    names = [f"{nm} {yr}" for nm, yr in zip(rng.choice(["Chen", "Smith", "Garcia", "Kim", "Silva", "Müller", "Rossi", "Nakamura", "Ali", "Novak", "Lee", "Brown", "Wang", "Hansen", "Dubois", "Kowalski", "Singh", "Park"], k, replace=False), rng.integers(2005, 2025, k))]
    pd.DataFrame({"study": names, "modality": mod, "duration_weeks": dur, "n_total": n, "smd": es.round(3), "se": se.round(3)}).sort_values("study").to_csv(ddir("D18_荟萃分析") / "meta.csv", index=False)
    write_readme("D18_荟萃分析", "RCT 荟萃分析（运动对 HbA1c）", "Meta-analysis of RCTs (exercise on HbA1c)", "18 项研究的标准化均数差 SMD（负值=更有利）。",
                 {"meta.csv": ("每项研究一行", "One row per study", {"smd": ("SMD", "SMD"), "se": ("标准误", "SE"), "modality": ("运动类型", "Modality"), "duration_weeks": ("干预周数", "Duration (weeks)")})})


def fig_d18(lang):
    df = read("D18_荟萃分析", "meta.csv")
    pooled = meta_random_effects(df["smd"].values, df["se"].values)
    df = df.assign(es=df["smd"], lo=df["smd"] - 1.96 * df["se"], hi=df["smd"] + 1.96 * df["se"], w=pooled["w"]).sort_values("es")
    mname = {"Aerobic": L("有氧", "Aerobic"), "Resistance": L("抗阻", "Resistance"), "Combined": L("联合", "Combined")}
    mc = {"Aerobic": C_SLATE, "Resistance": C_CORAL, "Combined": C_MAGENTA}
    d2 = df.copy(); d2["subgroup"] = d2["modality"]
    fig = fig_meta_forest(d2, pooled, L("标准化均数差 SMD（95% CI）  ← 更有利", "Standardised mean difference (95% CI)  ← favours exercise"), L("研究", "Study"), "SMD (95% CI)", subgroup_col="subgroup", sub_colors=mc)
    ax = fig.axes[0]
    ax.legend(handles=[plt.Line2D([], [], marker="s", ls="", color=mc[k], ms=5) for k in mc], labels=[mname[k] for k in mc], loc="lower right", fontsize=5.8, bbox_to_anchor=(0.62, 0.0))
    save(fig, "D18_荟萃分析", "fig1_forest", lang)
    fig = plt.figure(figsize=(DOUBLE, 2.9)); gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.05], wspace=0.5)
    ax = fig.add_subplot(gs[0]); ax_funnel(ax, df["es"].values, df["se"].values, pooled["est"]); panel_letter(ax, "a", dx=-0.2)
    eg = stats.linregress(1 / df["se"].values, df["es"].values / df["se"].values); ax.text(0.03, 0.97, va="top", s=f"Egger {L('截距', 'intercept')} {eg.intercept:.2f}, {fmt_p(eg.intercept_stderr and 2 * (1 - stats.t.cdf(abs(eg.intercept / eg.intercept_stderr), len(df) - 2)))}", transform=ax.transAxes, fontsize=5.5, color=C_GREY)
    ax = fig.add_subplot(gs[1])
    for i, k in enumerate(["Aerobic", "Resistance", "Combined"][::-1]):
        s = df[df["modality"] == k]; r = meta_random_effects(s["es"].values, ((s["hi"] - s["lo"]) / 3.92).values)
        ax.errorbar(r["est"], i, xerr=[[r["est"] - r["lo"]], [r["hi"] - r["est"]]], fmt="D", ms=5.5, color=mc[k], ecolor=mc[k], elinewidth=1.5, capsize=2.5, mec="white", mew=0.7)
        ax.text(0.65, i, f"k = {len(s)}\n{r['est']:.2f} ({r['lo']:.2f}, {r['hi']:.2f})", fontsize=5.5, va="center", linespacing=1.15)
    ax.axvline(0, color=C_GREY, lw=0.6); ax.axvline(pooled["est"], color=C_MAGENTA, lw=0.8, ls=":")
    ax.set_yticks([0, 1, 2]); ax.set_yticklabels([mname[k] for k in ["Combined", "Resistance", "Aerobic"]]); ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
    ax.set_xlim(-1.5, 1.4); ax.set_ylim(-0.6, 2.6); ax.set_xlabel(L("亚组合并 SMD（95% CI）", "Subgroup pooled SMD (95% CI)")); panel_letter(ax, "b", dx=-0.35)
    ax = fig.add_subplot(gs[2])
    sz = 12 + 5 * df["w"].values
    for k in mc:
        s = df[df["modality"] == k]; ax.scatter(s["duration_weeks"], s["es"], s=12 + 5 * s["w"], color=mc[k], alpha=0.75, edgecolors="white", linewidths=0.5, label=mname[k])
    g, fit, lo, hi = fit_band(df["duration_weeks"].values, df["es"].values, "lin")
    ax_fit_band(ax, g, fit, lo, hi, C_INK); ax.axhline(0, color=C_GREY, lw=0.5, ls=":")
    ax.set_xlabel(L("干预时长（周）", "Intervention duration (weeks)")); ax.set_ylabel("SMD"); ax.legend(fontsize=5.6, loc="upper center", bbox_to_anchor=(0.5, 1.16), ncol=3, handletextpad=0.2, columnspacing=0.8); panel_letter(ax, "c", dx=-0.22, dy=1.1)
    save(fig, "D18_荟萃分析", "fig2_funnel_subgroup_metareg", lang)


DOMAINS = [("D15_心理量表", sim_d15, fig_d15), ("D16_损伤_生存", sim_d16, fig_d16), ("D17_诊断_ROC", sim_d17, fig_d17), ("D18_荟萃分析", sim_d18, fig_d18)]
