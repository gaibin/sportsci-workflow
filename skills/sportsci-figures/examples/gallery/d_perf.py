# -*- coding: utf-8 -*-
"""D10 力量训练多时点 · D11 重测信度 · D12 响应者分析 · D13 计时赛配速 · D14 DXA 体成分 · D19 咖啡因剂量反应"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

from common import ddir, read, save, wilson, write_readme
from sportsci_figures.pubstyle.figures import *  # noqa: F401,F403   (all blocks, incl. figures_ext)
from sportsci_figures.pubstyle.style import tr as L, get_lang  # noqa: F401
from sportsci_figures.pubstyle import DOUBLE, panel_letter, arm_colors, fmt_p, condition_colors, dose_colors
from sportsci_figures.pubstyle import figures as pf
from sportsci_figures.pubstyle.style import C_AMBER, C_MAGENTA, C_SLATE, C_CORAL, C_GREY, C_INK, C_LIGHT, C_TEAL


# ============================================================================ D10
def sim_d10(seed=10):
    rng = np.random.default_rng(seed)
    rows = []
    gains = {"Control": 0.012, "LowLoad": 0.145, "HighLoad": 0.205}
    for i in range(60):
        grp = ["Control", "LowLoad", "HighLoad"][i // 20]; b = rng.normal(100, 18); resp = rng.lognormal(0, 0.25)
        for w in (0, 4, 8, 12, 16):
            frac = (1 - np.exp(-w / 7)) / (1 - np.exp(-16 / 7)); v = b * (1 + gains[grp] * resp * frac) * rng.lognormal(0, 0.035)
            rows.append((f"S{i + 1:03d}", grp, w, round(v, 1)))
    pd.DataFrame(rows, columns=["id", "group", "week", "squat_1rm_kg"]).to_csv(ddir("D10_力量训练_多时点")/"strength.csv", index=False)
    write_readme("D10_力量训练_多时点", "力量训练（3 组 × 5 个时点）", "Strength training (3 groups × 5 time points)", "60 人，对照 / 低负荷 / 高负荷；0、4、8、12、16 周下蹲 1RM。", {"strength.csv": ("长表", "Long format", {"squat_1rm_kg": ("下蹲 1RM kg", "Back-squat 1RM kg")})})


def fig_d10(lang):
    d = "D10_力量训练_多时点"; df = read(d, "strength.csv")
    gn = {"Control": L("对照", "Control"), "LowLoad": L("低负荷", "Low load"), "HighLoad": L("高负荷", "High load")}; df["g"] = df["group"].map(gn)
    col = {gn["Control"]: C_AMBER, gn["LowLoad"]: C_CORAL, gn["HighLoad"]: C_MAGENTA}
    fig = plt.figure(figsize=(DOUBLE, 3.3)); gs = fig.add_gridspec(1, 3, width_ratios=[1.4, 1.0, 0.9], wspace=0.42)
    ax = fig.add_subplot(gs[0]); times = [0, 4, 8, 12, 16]
    out = ax_multitime(ax, df, "id", "g", "week", "squat_1rm_kg", list(gn.values()), col, times, [str(t_) for t_ in times], L("下蹲 1RM (kg)", "Back-squat 1RM (kg)"), dodge=0.1, indiv_alpha=0.1)
    ax.set_xlabel(L("训练周", "Training week")); ax.legend(loc="upper left", fontsize=6); panel_letter(ax, "a", dx=-0.17)
    w = df.pivot_table(index=["id", "g"], columns="week", values="squat_1rm_kg").reset_index()
    for t_ in times[1:]:
        w[f"p{t_}"] = (w[t_] / w[0] - 1) * 100
    ax = fig.add_subplot(gs[1])
    ctrl = w[w["g"] == gn["Control"]]
    ser = {}
    for k in ("LowLoad", "HighLoad"):
        s = w[w["g"] == gn[k]]; est, lo, hi = [], [], []
        for t_ in times[1:]:
            a, c = s[f"p{t_}"].values, ctrl[f"p{t_}"].values; dm = a.mean() - c.mean(); se = np.sqrt(a.var(ddof=1) / len(a) + c.var(ddof=1) / len(c)); tc = 1.99
            est.append(dm); lo.append(dm - tc * se); hi.append(dm + tc * se)
        ser[gn[k]] = (est, lo, hi)
    ax_timepoints(ax, [str(t_) for t_ in times[1:]], ser, col, dodge=0.12, ylabel=L("较对照的增幅差 (百分点)", "Gain vs control (percentage points)")); ax.axhline(0, color=C_AMBER, lw=1.1, ls=(0, (3, 2)))
    ax.set_xlabel(L("训练周", "Training week")); ax.legend(loc="upper left", fontsize=6); panel_letter(ax, "b", dx=-0.25)
    ax = fig.add_subplot(gs[2]); ax_raincloud(ax, {gn[k]: w[w["g"] == gn[k]]["p16"].values for k in gn}, col, L("16 周下蹲 1RM 增幅 (%)", "Change in 1RM at week 16 (%)")); ax.set_xticklabels(list(gn.values()), fontsize=5.8); ax.axhline(0, color=C_GREY, lw=0.5, ls=":")
    panel_letter(ax, "c", dx=-0.3)
    save(fig, d, "fig1_strength", lang)


# ============================================================================ D11
def sim_d11(seed=11):
    rng = np.random.default_rng(seed); n = 40
    tests = {"sprint20_s": (3.15, 0.18, 0.022), "cmj_cm": (36, 6.5, 1.9), "grip_kg": (40, 9, 1.6), "squat1rm_kg": (110, 26, 6), "vo2max": (52, 7, 2.4), "agility_s": (10.4, 0.7, 0.2)}
    rows = []
    for i in range(n):
        for k, (m, sd, te) in tests.items():
            true = rng.normal(m, sd); rows.append((f"R{i + 1:03d}", k, round(true + rng.normal(0, te), 3), round(true + rng.normal(0, te) + 0.01 * sd, 3)))
    pd.DataFrame(rows, columns=["id", "test", "trial1", "trial2"]).to_csv(ddir("D11_重测信度")/"retest.csv", index=False)
    write_readme("D11_重测信度", "6 项测试的重测信度", "Test–retest reliability of 6 tests", "40 人，两次测试。", {"retest.csv": ("长表", "Long format", {"test": ("测试名称", "Test"), "trial1": ("第一次", "Trial 1"), "trial2": ("第二次", "Trial 2")})})


def fig_d11(lang):
    d = "D11_重测信度"; df = read(d, "retest.csv")
    names = {"sprint20_s": L("20 m 冲刺 (s)", "20-m sprint (s)"), "cmj_cm": L("纵跳 (cm)", "CMJ height (cm)"), "grip_kg": L("握力 (kg)", "Grip (kg)"),
             "squat1rm_kg": L("下蹲 1RM (kg)", "Squat 1RM (kg)"), "vo2max": L("VO₂max (mL/kg/min)", "VO₂max (mL/kg/min)"), "agility_s": L("敏捷 T 测试 (s)", "Agility T-test (s)")}
    fig = plt.figure(figsize=(DOUBLE, 3.4)); gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.2], wspace=0.5)
    s = df[df["test"] == "cmj_cm"]
    ax = fig.add_subplot(gs[0]); ax_identity(ax, s["trial1"], s["trial2"], L("第一次纵跳 (cm)", "CMJ trial 1 (cm)"), L("第二次纵跳 (cm)", "CMJ trial 2 (cm)")); panel_letter(ax, "a", dx=-0.3, dy=1.03)
    ax = fig.add_subplot(gs[1]); ax_bland_altman(ax, s["trial2"], s["trial1"], L("两次均值 (cm)", "Mean of trials (cm)"), L("第二次 − 第一次 (cm)", "Trial 2 − trial 1 (cm)"), "cm"); panel_letter(ax, "b", dx=-0.3, dy=1.03)
    ax = fig.add_subplot(gs[2]); rng = np.random.default_rng(0); rows = []
    for k, nm in names.items():
        t = df[df["test"] == k]; a, b = t["trial1"].values, t["trial2"].values; icc = icc_2_1(a, b)
        bs = [icc_2_1(a[i], b[i]) for i in (rng.integers(0, len(a), len(a)) for _ in range(400))]; lo, hi = np.percentile(bs, [2.5, 97.5])
        cv = (np.std(a - b, ddof=1) / np.sqrt(2)) / np.mean((a + b) / 2) * 100; rows.append((nm, icc, lo, hi, cv))
    rows.sort(key=lambda r: r[1])
    ax.axvspan(0, 0.75, color="#FBEFEC", lw=0); ax.axvspan(0.75, 0.9, color="#F5F3FA", lw=0); ax.axvspan(0.9, 1.0, color="#ECEEF8", lw=0)
    for i, (nm, icc, lo, hi, cv) in enumerate(rows):
        ax.errorbar(icc, i, xerr=[[icc - lo], [hi - icc]], fmt="o", ms=5, color=C_MAGENTA, ecolor=C_MAGENTA, elinewidth=1.4, capsize=2.5, mec="white", mew=0.7)
        ax.text(1.005, i, f"CV {cv:.1f}%", fontsize=5.4, va="center", color=C_GREY)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows]); ax.tick_params(axis="y", length=0); ax.set_xlim(0.5, 1.0); ax.set_xlabel("ICC(2,1) (95% CI)")
    ax.text(0.62, len(rows) - 0.35, L("一般", "Moderate"), fontsize=5.3, color=C_GREY, ha="center"); ax.text(0.825, len(rows) - 0.35, L("良好", "Good"), fontsize=5.3, color=C_GREY, ha="center"); ax.text(0.95, len(rows) - 0.35, L("优秀", "Excellent"), fontsize=5.3, color=C_GREY, ha="center")
    ax.set_ylim(-0.6, len(rows) - 0.1); ax.spines["left"].set_visible(False); panel_letter(ax, "c", dx=-0.62, dy=1.03)
    save(fig, d, "fig1_reliability", lang)


# ============================================================================ D12
def sim_d12(seed=12):
    rng = np.random.default_rng(seed); rows = []
    for i in range(80):
        grp = "Intervention" if i < 40 else "Control"; base = rng.normal(34, 5); true = rng.normal(3.2 if grp == "Intervention" else 0.2, 2.3)
        te = 1.4; obs = true + rng.normal(0, te); rows.append((f"Q{i + 1:03d}", grp, round(base, 1), round(obs, 2), te, 0.8))
    pd.DataFrame(rows, columns=["id", "group", "baseline_cmj_cm", "change_cmj_cm", "typical_error_cm", "swc_cm"]).to_csv(ddir("D12_响应者分析")/"responders.csv", index=False)
    write_readme("D12_响应者分析", "个体响应：SWC 与典型误差", "Individual responses: SWC and typical error", "80 人（干预 40 / 对照 40）纵跳变化；TE=1.4 cm，SWC=0.8 cm。", {"responders.csv": ("每人一行", "One row per person", {"change_cmj_cm": ("变化量 cm", "Change cm"), "typical_error_cm": ("典型误差 cm", "Typical error cm"), "swc_cm": ("最小有意义变化 cm", "Smallest worthwhile change cm")})})


def fig_d12(lang):
    d = "D12_响应者分析"; df = read(d, "responders.csv"); te, swc = df["typical_error_cm"].iloc[0], df["swc_cm"].iloc[0]
    gn = {"Intervention": L("干预组", "Intervention"), "Control": L("对照组", "Control")}
    fig = plt.figure(figsize=(DOUBLE, 3.3)); gs = fig.add_gridspec(1, 3, width_ratios=[1.5, 0.9, 1.0], wspace=0.42)
    ax = fig.add_subplot(gs[0]); s = df[df["group"] == "Intervention"]
    cnt = ax_waterfall(ax, s["change_cmj_cm"].values, swc, te, unit_label=L("纵跳变化 (cm)", "CMJ change (cm)")); ax.set_title(L("干预组：个体变化（误差棒 = 90% 置信限）", "Intervention: individual change (whiskers = 90% limits)"), fontsize=6.3, loc="left", pad=3)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in (C_MAGENTA, C_SLATE, C_CORAL)], labels=[L("有益", "Beneficial"), L("无意义", "Trivial"), L("有害", "Harmful")], loc="upper right", fontsize=5.8, handlelength=1)
    panel_letter(ax, "a", dx=-0.1)
    ax = fig.add_subplot(gs[1]); colr = [C_MAGENTA, C_SLATE, C_CORAL]
    for i, k in enumerate(gn):
        c = df[df["group"] == k]["change_cmj_cm"].values; ci = 1.645 * te
        shares = [((c - ci) > swc).mean(), 1 - ((c - ci) > swc).mean() - ((c + ci) < -swc).mean(), ((c + ci) < -swc).mean()]
        b = 0
        for sh, cl in zip(shares, colr):
            ax.bar(i, sh * 100, bottom=b, color=cl, width=0.6, lw=0)
            if sh > 0.07: ax.text(i, b + sh * 50, f"{sh * 100:.0f}", ha="center", va="center", fontsize=5.8, color="white" if cl != C_SLATE else "white")
            b += sh * 100
    ax.set_xticks([0, 1]); ax.set_xticklabels(list(gn.values())); ax.tick_params(axis="x", length=0); ax.set_ylabel(L("受试者占比 (%)", "Participants (%)")); panel_letter(ax, "b", dx=-0.3)
    ax = fig.add_subplot(gs[2]); si = s
    ax.axhspan(-swc, swc, color=C_BAND, zorder=0); ax.axhline(0, color=C_GREY, lw=0.5)
    ax.scatter(si["baseline_cmj_cm"], si["change_cmj_cm"], s=14, color=C_MAGENTA, alpha=0.8, edgecolors="white", linewidths=0.4)
    sl, ic, r, p, _ = stats.linregress(si["baseline_cmj_cm"], si["change_cmj_cm"]); xs = np.linspace(si["baseline_cmj_cm"].min(), si["baseline_cmj_cm"].max(), 20); ax.plot(xs, ic + sl * xs, color=C_INK, lw=1)
    ax.set_xlabel(L("基线纵跳 (cm)", "Baseline CMJ (cm)")); ax.set_ylabel(L("变化 (cm)", "Change (cm)")); ax.text(0.04, 0.96, f"r = {r:.2f}, {fmt_p(p)}", transform=ax.transAxes, fontsize=6, va="top"); panel_letter(ax, "c", dx=-0.25)
    save(fig, d, "fig1_responders", lang)


# ============================================================================ D13
def sim_d13(seed=13):
    rng = np.random.default_rng(seed); dist = np.arange(0, 20.01, 0.5); rows = []
    for i in range(16):
        v0 = rng.normal(38.5, 2.2)
        for cond in ("Placebo", "Caffeine"):
            pace = v0 * (1 + 0.035 * np.exp(-dist / 1.5) - 0.045 * np.sin(np.pi * dist / 20) + 0.06 * np.exp(-((20 - dist) / 1.2)))
            if cond == "Caffeine":
                pace = pace * (1 + 0.012 * (1 - np.exp(-dist / 3)))
            pace = pace * rng.lognormal(0, 0.006, len(dist))
            for dd, vv in zip(dist, pace):
                rows.append((f"T{i + 1:03d}", cond, dd, round(vv, 2)))
    pd.DataFrame(rows, columns=["id", "condition", "distance_km", "speed_kmh"]).to_csv(ddir("D13_计时赛_配速")/"time_trial.csv", index=False)
    write_readme("D13_计时赛_配速", "20 km 计时赛配速（咖啡因 vs 安慰剂，交叉）", "20-km time trial pacing (caffeine vs placebo, crossover)", "16 人；每 0.5 km 的速度。", {"time_trial.csv": ("每人每条件一条配速曲线", "One pacing profile per person per condition", {"speed_kmh": ("速度 km/h", "Speed km/h")})})


def fig_d13(lang):
    d = "D13_计时赛_配速"; df = read(d, "time_trial.csv"); cn = {"Placebo": L("安慰剂", "Placebo"), "Caffeine": L("咖啡因", "Caffeine")}; col = {cn["Placebo"]: C_AMBER, cn["Caffeine"]: C_MAGENTA}
    A = {k: df[df["condition"] == k].pivot(index="id", columns="distance_km", values="speed_kmh") for k in cn}
    x = A["Placebo"].columns.values
    fig = plt.figure(figsize=(DOUBLE, 3.3)); gs = fig.add_gridspec(1, 3, width_ratios=[1.3, 1.1, 0.9], wspace=0.42)
    ax = fig.add_subplot(gs[0]); ax_bands(ax, x, {cn[k]: (A[k].mean().values, A[k].std().values / np.sqrt(len(A[k]))) for k in cn}, col, dashed=[cn["Placebo"]])
    ax.set_xlabel(L("距离 (km)", "Distance (km)")); ax.set_ylabel(L("速度 (km/h)", "Speed (km/h)")); ax.legend(loc="upper center", fontsize=6); panel_letter(ax, "a", dx=-0.17)
    ax = fig.add_subplot(gs[1]); mu, lo, hi = pointwise_diff_ci(A["Caffeine"].values, A["Placebo"].values); ax_diff_band(ax, x, {cn["Caffeine"]: (mu, lo, hi)}, col, ref_label=cn["Placebo"], mark_min=False)
    ax.set_xlabel(L("距离 (km)", "Distance (km)")); ax.set_ylabel(L("速度差 咖啡因 − 安慰剂 (km/h)", "Speed difference, caffeine − placebo (km/h)")); ax.text(0.04, 0.96, L("阴影：逐点 95% CI（未校正）", "band: pointwise 95% CI (unadjusted)"), transform=ax.transAxes, fontsize=5.4, color=C_GREY, va="top"); panel_letter(ax, "b", dx=-0.22)
    ft = pd.DataFrame({cn[k]: 20 / (A[k].mean(axis=1) if False else (1 / (A[k].values.mean(axis=1)))) * 0 + 20 / np.trapz(np.ones(len(x)), x) * (60 * 20 / A[k].values.mean(1)) / 20 for k in cn}, index=A["Placebo"].index)
    ft = pd.DataFrame({cn[k]: 60 * 20 / A[k].values.mean(1) for k in cn}, index=A["Placebo"].index)
    ax = fig.add_subplot(gs[2]); est = {c: paired_ci(ft[c].values) for c in col}; pf.ax_paired_estimate(ax, ft, list(col), col, est, L("完赛时间 (min)", "Finish time (min)"))
    dd = paired_ci(ft[cn["Caffeine"]].values, ft[cn["Placebo"]].values); ax.set_title(f"{dd[0]:+.2f} min ({dd[1]:.2f}, {dd[2]:.2f})", fontsize=6.3, loc="left", pad=3); panel_letter(ax, "c", dx=-0.25)
    save(fig, d, "fig1_time_trial", lang)


# ============================================================================ D14
def sim_d14(seed=14):
    rng = np.random.default_rng(seed); rows = []
    for i in range(40):
        grp = "Training" if i < 20 else "Control"; fat = rng.normal(21, 5); lean = rng.normal(52, 7); bone = rng.normal(3.0, 0.35); vol = rng.normal(14, 3.5) if grp == "Training" else np.nan
        dl = (0.9 + 0.11 * (vol - 14) + rng.normal(0, 0.55)) if grp == "Training" else rng.normal(0, 0.55); df_ = (-1.1 + rng.normal(0, 1.0)) if grp == "Training" else rng.normal(0.1, 1.0)
        rows.append((f"X{i + 1:03d}", grp, "Pre", round(fat, 2), round(lean, 2), round(bone, 3), vol)); rows.append((f"X{i + 1:03d}", grp, "Post", round(fat + df_, 2), round(lean + dl, 2), round(bone + rng.normal(0.01, 0.02), 3), vol))
    pd.DataFrame(rows, columns=["id", "group", "time", "fat_kg", "lean_kg", "bone_kg", "sets_per_week"]).to_csv(ddir("D14_体成分_DXA")/"dxa.csv", index=False)
    write_readme("D14_体成分_DXA", "DXA 体成分（训练 vs 对照）", "DXA body composition (training vs control)", "40 人，前后。", {"dxa.csv": ("长表", "Long format", {"fat_kg": ("脂肪量 kg", "Fat mass kg"), "lean_kg": ("瘦体重 kg", "Lean mass kg"), "bone_kg": ("骨矿物含量 kg", "Bone mineral kg"), "sets_per_week": ("每周训练组数（训练组）", "Weekly sets (training group)")})})


def fig_d14(lang):
    d = "D14_体成分_DXA"; df = read(d, "dxa.csv"); gn = {"Control": L("对照", "Control"), "Training": L("训练", "Training")}; gc = {gn["Control"]: C_AMBER, gn["Training"]: C_MAGENTA}
    parts = [("lean_kg", L("瘦体重", "Lean"), C_MAGENTA), ("fat_kg", L("脂肪", "Fat"), C_AMBER), ("bone_kg", L("骨", "Bone"), C_SLATE)]
    fig = plt.figure(figsize=(DOUBLE, 3.3)); gs = fig.add_gridspec(1, 3, width_ratios=[1.1, 1.0, 1.0], wspace=0.45)
    ax = fig.add_subplot(gs[0]); pos = 0; ticks = []; labels = []
    for gi, g in enumerate(("Control", "Training")):
        for tm in ("Pre", "Post"):
            s = df[(df["group"] == g) & (df["time"] == tm)]; b = 0
            for c, lab, cl in parts:
                v = s[c].mean(); ax.bar(pos, v, bottom=b, color=cl, width=0.7, lw=0); ax.text(pos, b + v / 2, f"{v:.1f}", ha="center", va="center", fontsize=5.5, color="white" if cl != C_AMBER else C_INK) if v > 3.5 else None; b += v
            ax.text(pos, b + 1.2, f"{b:.1f}", ha="center", fontsize=5.6); ticks.append(pos); labels.append(L("前", "Pre") if tm == "Pre" else L("后", "Post")); pos += 0.9
        pos += 0.5
    ax.set_xticks(ticks); ax.set_xticklabels(labels); ax.tick_params(axis="x", length=0); ax.set_ylabel(L("平均质量 (kg)", "Mean mass (kg)")); ax.set_ylim(0, 105)
    for xc, g in ((np.mean(ticks[:2]), "Control"), (np.mean(ticks[2:]), "Training")):
        ax.text(xc, -0.12, gn[g], transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=6.3, color=gc[gn[g]], fontweight="bold")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in parts], labels=[p[1] for p in parts], loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=3, fontsize=5.6, handlelength=0.9); panel_letter(ax, "a", dx=-0.2, dy=1.1)
    w = df.pivot_table(index=["id", "group", "sets_per_week"], columns="time", values=["lean_kg", "fat_kg"], dropna=False).reset_index() if False else None
    pv = df.pivot_table(index=["id", "group"], columns="time", values=["lean_kg", "fat_kg"]); pv.columns = [f"{a}_{b}" for a, b in pv.columns]; pv = pv.reset_index()
    pv["dlean"] = pv["lean_kg_Post"] - pv["lean_kg_Pre"]; pv["dfat"] = pv["fat_kg_Post"] - pv["fat_kg_Pre"]; vol = df.drop_duplicates("id").set_index("id")["sets_per_week"]; pv["vol"] = pv["id"].map(vol)
    ax = fig.add_subplot(gs[1]); t = pv[pv["group"] == "Training"]; r_, p_, n_ = ax_scatter_fit(ax, t["vol"], t["dlean"], C_MAGENTA, L("每周训练组数", "Weekly sets"), L("瘦体重变化 (kg)", "Change in lean mass (kg)")); panel_letter(ax, "b", dx=-0.25)
    ax = fig.add_subplot(gs[2]); ax_raincloud(ax, {gn[g]: pv[pv["group"] == g]["dfat"].values for g in gn}, gc, L("脂肪量变化 (kg)", "Change in fat mass (kg)")); ax.axhline(0, color=C_GREY, lw=0.5, ls=":"); panel_letter(ax, "c", dx=-0.3)
    save(fig, d, "fig1_dxa", lang)


# ============================================================================ D19
def sim_d19(seed=19):
    rng = np.random.default_rng(seed); doses = [0, 1, 3, 6, 9]; rows = []
    for i in range(24):
        a0 = rng.normal(0, 0.55); em = rng.normal(2.3, 0.6); ed = rng.lognormal(np.log(2.6), 0.25)
        for dsg in doses:
            rows.append((f"C{i + 1:03d}", dsg, round(a0 + em * dsg / (ed + dsg) + rng.normal(0, 0.55), 2)))
    pd.DataFrame(rows, columns=["id", "dose_mg_kg", "improvement_pct"]).to_csv(ddir("D19_营养_剂量反应")/"caffeine.csv", index=False)
    write_readme("D19_营养_剂量反应", "咖啡因剂量-反应（5 个剂量，交叉）", "Caffeine dose–response (5 doses, crossover)", "24 人，计时赛成绩改善 %（相对基线）。", {"caffeine.csv": ("长表", "Long format", {"dose_mg_kg": ("剂量 mg/kg", "Dose mg/kg"), "improvement_pct": ("成绩改善 %", "Performance improvement %")})})


def fig_d19(lang):
    d = "D19_营养_剂量反应"; df = read(d, "caffeine.csv"); doses = sorted(df["dose_mg_kg"].unique()); cols = dose_colors(len(doses))
    fig = plt.figure(figsize=(DOUBLE, 3.3)); gs = fig.add_gridspec(1, 2, width_ratios=[1.2, 1], wspace=0.32)
    ax = fig.add_subplot(gs[0])
    for _, s in df.groupby("id"):
        ax.plot(s["dose_mg_kg"], s["improvement_pct"], color=C_LIGHT, lw=0.4, alpha=0.8, zorder=1)
    for dsg, c in zip(doses, cols):
        s = df[df["dose_mg_kg"] == dsg]; rng = np.random.default_rng(int(dsg)); ax.scatter(dsg + rng.uniform(-0.15, 0.15, len(s)), s["improvement_pct"], s=8, color=c, alpha=0.55, lw=0, zorder=2)
    g, fit, lo, hi = fit_band(df["dose_mg_kg"].values, df["improvement_pct"].values, "emax"); ax_fit_band(ax, g, fit, lo, hi, C_MAGENTA)
    ax.axhline(0, color=C_AMBER, lw=1.1, ls=(0, (3, 2))); ax.set_xlabel(L("咖啡因剂量 (mg/kg)", "Caffeine dose (mg/kg)")); ax.set_ylabel(L("成绩改善 (%)", "Performance improvement (%)")); ax.set_xticks(doses)
    ax.text(0.97, 0.05, L("曲线：Emax 模型；阴影：bootstrap 95% 区间", "curve: Emax model; band: bootstrap 95% interval"), transform=ax.transAxes, ha="right", fontsize=5.4, color=C_GREY); panel_letter(ax, "a", dx=-0.13)
    ax = fig.add_subplot(gs[1]); wide = df.pivot(index="id", columns="dose_mg_kg", values="improvement_pct"); wide.columns = [f"{c:g}" for c in wide.columns]
    colmap = dict(zip(wide.columns, cols)); ax_raincloud(ax, {c: wide[c].values for c in wide.columns}, colmap, L("成绩改善 (%)", "Performance improvement (%)"), paired_lines=wide, point_s=5, width=0.3)
    ax.set_xlabel(L("剂量 (mg/kg)", "Dose (mg/kg)")); ax.axhline(0, color=C_GREY, lw=0.5, ls=":"); panel_letter(ax, "b", dx=-0.17)
    save(fig, d, "fig1_dose_response", lang)


DOMAINS = [("D10_力量训练_多时点", sim_d10, fig_d10), ("D11_重测信度", sim_d11, fig_d11), ("D12_响应者分析", sim_d12, fig_d12), ("D13_计时赛_配速", sim_d13, fig_d13),
           ("D14_体成分_DXA", sim_d14, fig_d14), ("D19_营养_剂量反应", sim_d19, fig_d19)]
