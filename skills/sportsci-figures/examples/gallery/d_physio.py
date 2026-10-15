# -*- coding: utf-8 -*-
"""D01 心肺分级运动与摄氧动力学 · D02 心率恢复与 HRV · D03 训练负荷监测 · D26 动态血压"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import curve_fit

from common import ddir, read, save, wilson, write_readme
from sportsci_figures.pubstyle.figures import *  # noqa: F401,F403   (all blocks, incl. figures_ext)
from sportsci_figures.pubstyle.style import tr as L, get_lang  # noqa: F401
from sportsci_figures.pubstyle import DOUBLE, panel_letter, arm_colors, fmt_p, condition_colors
from sportsci_figures.pubstyle import figures as pf
from sportsci_figures.pubstyle.style import C_AMBER, C_MAGENTA, C_SLATE, C_CORAL, C_GREY, C_INK, C_LIGHT, C_TEAL, C_PALE_SLATE2

POWER = np.array([100, 140, 180, 220, 260, 300])


# ============================================================================ D01
def sim_d01(seed=1):
    rng = np.random.default_rng(seed)
    rows, lt_rows, kin = [], [], []
    for i in range(24):
        grp = "HIIT" if i < 12 else "CON"
        T0 = rng.normal(185, 18)
        for tm in ("Pre", "Post"):
            shift = 0 if tm == "Pre" else (rng.normal(24, 8) if grp == "HIIT" else rng.normal(2, 8))
            T = T0 + shift
            lact = 0.9 + np.exp((POWER - T) / 60) * rng.lognormal(0, 0.06, 6)
            hr = 98 + 0.46 * (POWER - 100) - (0 if (tm == "Pre" or grp == "CON") else 4) + rng.normal(0, 2.5, 6)
            vo2 = 11 + 0.105 * POWER + rng.normal(0, 0.8, 6)
            for k in range(6):
                rows.append((f"G{i + 1:03d}", grp, tm, k + 1, POWER[k], round(hr[k], 1), round(vo2[k], 1), round(lact[k], 2)))
            gp = np.linspace(100, 300, 400)
            lt_rows.append((f"G{i + 1:03d}", grp, tm, round(float(np.interp(4.0, 0.9 + np.exp((gp - T) / 60), gp)), 1)))
            tau = rng.normal(40, 5) - (9 if (tm == "Post" and grp == "HIIT") else 0.5 * (tm == "Post"))
            t = np.arange(0, 361, 5.0)
            v = 700 + 1500 * (1 - np.exp(-np.maximum(t - 12, 0) / tau)) + 90 * (1 - np.exp(-np.maximum(t - 180, 0) / 100)) + rng.normal(0, 70, len(t))
            for a, b in zip(t, v):
                kin.append((f"G{i + 1:03d}", grp, tm, a, round(b, 1)))
    d = ddir("D01_心肺_分级运动")
    pd.DataFrame(rows, columns=["id", "group", "time", "stage", "power_w", "hr_bpm", "vo2_ml_kg_min", "lactate_mmol_l"]).to_csv(d / "gxt.csv", index=False)
    pd.DataFrame(lt_rows, columns=["id", "group", "time", "power_at_4mmol_w"]).to_csv(d / "lactate_threshold.csv", index=False)
    pd.DataFrame(kin, columns=["id", "group", "time", "t_s", "vo2_ml_min"]).to_csv(d / "vo2_kinetics.csv", index=False)
    write_readme("D01_心肺_分级运动", "分级运动试验与摄氧动力学（HIIT 前后）", "Graded exercise test and VO2 kinetics (pre/post HIIT)", "24 人（HIIT 12 / 对照 12），干预前后各一次分级试验与阶跃摄氧试验。",
                 {"gxt.csv": ("每人每时点 6 级功率的心率、摄氧、乳酸", "HR, VO2 and lactate at 6 stages", {"power_w": ("功率 W", "Power W"), "lactate_mmol_l": ("血乳酸", "Blood lactate")}),
                  "lactate_threshold.csv": ("4 mmol/L 乳酸对应功率", "Power at 4 mmol/L lactate", {"power_at_4mmol_w": ("功率 W", "Power W")}),
                  "vo2_kinetics.csv": ("阶跃运动 VO2（5 s 平均）", "Step-transition VO2 (5-s averages)", {"t_s": ("时间 s", "Time s"), "vo2_ml_min": ("VO2 mL/min", "VO2 mL/min")})})


def fig_d01(lang):
    d = "D01_心肺_分级运动"
    g = read(d, "gxt.csv"); lt = read(d, "lactate_threshold.csv"); kin = read(d, "vo2_kinetics.csv")
    col_t = {"Pre": C_SLATE, "Post": C_MAGENTA}
    tl = {"Pre": L("干预前", "Pre"), "Post": L("干预后", "Post")}
    fig = plt.figure(figsize=(DOUBLE, 3.2)); gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.1], wspace=0.42)
    for j, grp in enumerate(("HIIT", "CON")):
        ax = fig.add_subplot(gs[j]); ser = {}
        for tm in ("Pre", "Post"):
            w = g[(g["group"] == grp) & (g["time"] == tm)].pivot(index="id", columns="stage", values="lactate_mmol_l").values
            ser[tl[tm]] = (w.mean(0), w.std(0, ddof=1) / np.sqrt(len(w)))
        ax_bands(ax, POWER, ser, {tl["Pre"]: C_SLATE, tl["Post"]: C_MAGENTA if grp == "HIIT" else C_AMBER}, dashed=[tl["Pre"]])
        ax.axhline(4, color=C_GREY, lw=0.6, ls=":"); ax.text(100, 4.15, "4 mmol/L", fontsize=5.5, color=C_GREY, ha="left"); ax.set_ylim(0, 9.5)
        ax.set_xlabel(L("功率 (W)", "Power (W)")); ax.set_ylabel(L("血乳酸 (mmol/L)", "Blood lactate (mmol/L)"))
        ax.legend(loc="upper left", fontsize=6); ax.set_title(L("HIIT 组", "HIIT group") if grp == "HIIT" else L("对照组", "Control group"), loc="left", fontsize=7, pad=3)
        panel_letter(ax, "ab"[j], dx=-0.2, dy=1.06)
    ax = fig.add_subplot(gs[2])
    lt["group"] = lt["group"].map({"HIIT": L("HIIT 组", "HIIT"), "CON": L("对照组", "Control")}); lt["t"] = (lt["time"] == "Post").astype(int)
    gcol = {L("HIIT 组", "HIIT"): C_MAGENTA, L("对照组", "Control"): C_AMBER}
    w = lt.pivot_table(index=["id", "group"], columns="time", values="power_at_4mmol_w").reset_index(); w["d"] = w["Post"] - w["Pre"]
    a, c = w[w["group"] == L("HIIT 组", "HIIT")]["d"], w[w["group"] == L("对照组", "Control")]["d"]; tt = stats.ttest_ind(a, c)
    long = lt.rename(columns={"power_at_4mmol_w": "y"})
    pf.ax_prepost(ax, long, "id", "group", "t", "y", list(gcol), gcol, [L("前", "Pre"), L("后", "Post")], L("4 mmol/L 乳酸对应功率 (W)", "Power at 4 mmol/L lactate (W)"),
                  title=f"{L('组间变化差', 'Between-group Δ')} {a.mean() - c.mean():+.1f} W  {fmt_p(tt.pvalue)}")
    panel_letter(ax, "c", dx=-0.2, dy=1.12)
    save(fig, d, "fig1_gxt_lactate", lang)
    # ---------------- kinetics
    def mono(t, b, A, td, tau):
        return b + A * (1 - np.exp(-np.maximum(t - td, 0) / tau))
    fits = []
    for (i, grp, tm), s in kin.groupby(["id", "group", "time"]):
        p, _ = curve_fit(mono, s["t_s"], s["vo2_ml_min"], p0=[700, 1500, 10, 40], maxfev=5000)
        fits.append((i, grp, tm, p[3]))
    fit = pd.DataFrame(fits, columns=["id", "group", "time", "tau"])
    fig = plt.figure(figsize=(DOUBLE, 3.2)); gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 1, 1], wspace=0.45)
    ax = fig.add_subplot(gs[0]); ser = {}
    for tm in ("Pre", "Post"):
        w = kin[(kin["group"] == "HIIT") & (kin["time"] == tm)].pivot(index="id", columns="t_s", values="vo2_ml_min")
        ser[tl[tm]] = (w.mean().values, w.std().values / np.sqrt(len(w)))
        pm, _ = curve_fit(mono, w.columns.values, w.mean().values, p0=[700, 1500, 10, 40]); ax.plot(w.columns.values, mono(w.columns.values, *pm), color="k", lw=0.8, ls=":")
    ax_bands(ax, kin["t_s"].unique(), ser, {tl["Pre"]: C_SLATE, tl["Post"]: C_MAGENTA})
    ax.set_xlabel(L("阶跃开始后时间 (s)", "Time after step (s)")); ax.set_ylabel(L("摄氧量 (mL/min)", "VO₂ (mL/min)")); ax.legend(loc="lower right", fontsize=6)
    ax.text(0.03, 0.96, L("虚线：单指数拟合", "dotted: mono-exponential fit"), transform=ax.transAxes, fontsize=5.5, color=C_GREY, va="top"); panel_letter(ax, "a", dx=-0.17)
    ax = fig.add_subplot(gs[1])
    names = {("HIIT", "Pre"): L("HIIT 前", "HIIT pre"), ("HIIT", "Post"): L("HIIT 后", "HIIT post"), ("CON", "Pre"): L("对照 前", "Control pre"), ("CON", "Post"): L("对照 后", "Control post")}
    cols = {names[("HIIT", "Pre")]: C_SLATE, names[("HIIT", "Post")]: C_MAGENTA, names[("CON", "Pre")]: C_PALE_SLATE2, names[("CON", "Post")]: C_AMBER}
    ax_raincloud(ax, {names[k]: fit[(fit["group"] == k[0]) & (fit["time"] == k[1])]["tau"].values for k in names}, cols, L("时间常数 τ (s)", "Time constant τ (s)"))
    ax.set_xticklabels([n.replace(" ", "\n") for n in names.values()], fontsize=5.8); panel_letter(ax, "b", dx=-0.25)
    ax = fig.add_subplot(gs[2]); wf = fit.pivot_table(index=["id", "group"], columns="time", values="tau").reset_index(); wf["d"] = wf["Post"] - wf["Pre"]
    ax_raincloud(ax, {L("HIIT 组", "HIIT"): wf[wf["group"] == "HIIT"]["d"].values, L("对照组", "Control"): wf[wf["group"] == "CON"]["d"].values}, gcol, L("τ 变化 (s)", "Change in τ (s)"))
    ax.axhline(0, color=C_GREY, lw=0.6, ls=":"); panel_letter(ax, "c", dx=-0.25)
    save(fig, d, "fig2_vo2_kinetics", lang)


# ============================================================================ D02
def sim_d02(seed=2):
    rng = np.random.default_rng(seed)
    n = 20; t = np.arange(0, 301, 10.0); rows = []
    tau = {"Passive": 150, "Active": 100, "ColdWater": 82}
    for i in range(n):
        peak = rng.normal(178, 6); rest = rng.normal(63, 6)
        for c, ta in tau.items():
            hr = rest + (peak - rest) * np.exp(-t / (ta * rng.lognormal(0, 0.1))) + rng.normal(0, 1.8, len(t))
            for a, b in zip(t, hr):
                rows.append((f"R{i + 1:03d}", c, a, round(b, 1)))
    d = ddir("D02_HRV_心率恢复")
    pd.DataFrame(rows, columns=["id", "condition", "t_s", "hr_bpm"]).to_csv(d / "hr_recovery.csv", index=False)
    r = []
    for i in range(40):
        grp = "Training" if i < 20 else "Control"; base = rng.lognormal(np.log(42), 0.35)
        r += [(f"V{i + 1:03d}", grp, "Pre", round(base, 1)), (f"V{i + 1:03d}", grp, "Post", round(base * rng.lognormal(0.22 if grp == "Training" else 0.02, 0.18), 1))]
    pd.DataFrame(r, columns=["id", "group", "time", "rmssd_ms"]).to_csv(d / "hrv.csv", index=False)
    write_readme("D02_HRV_心率恢复", "心率恢复（三种恢复方式交叉）与 HRV", "Heart-rate recovery (3 recovery modes, crossover) and HRV", "20 人交叉；40 人 HRV 前后。",
                 {"hr_recovery.csv": ("极量运动后 5 分钟心率", "HR for 5 min after maximal exercise", {"condition": ("恢复方式", "Recovery mode")}), "hrv.csv": ("rMSSD 前后", "rMSSD pre/post", {"rmssd_ms": ("rMSSD ms（右偏）", "rMSSD ms (right-skewed)")})})


def fig_d02(lang):
    d = "D02_HRV_心率恢复"
    h = read(d, "hr_recovery.csv"); v = read(d, "hrv.csv")
    cn = {"Passive": L("被动恢复", "Passive"), "Active": L("主动恢复", "Active"), "ColdWater": L("冷水浸泡", "Cold-water")}
    col = {cn["Passive"]: C_AMBER, cn["Active"]: C_CORAL, cn["ColdWater"]: C_MAGENTA}
    fig = plt.figure(figsize=(DOUBLE, 3.2)); gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1, 1], wspace=0.45)
    ax = fig.add_subplot(gs[0]); ser = {}
    for c in cn:
        w = h[h["condition"] == c].pivot(index="id", columns="t_s", values="hr_bpm"); ser[cn[c]] = (w.mean().values, w.std().values / np.sqrt(len(w)))
    ax_bands(ax, np.sort(h["t_s"].unique()), ser, col, dashed=[cn["Passive"]]); ax.set_xlabel(L("运动结束后时间 (s)", "Time after exercise (s)")); ax.set_ylabel(L("心率 (次/分)", "Heart rate (bpm)"))
    ax.legend(loc="upper right", fontsize=6); panel_letter(ax, "a", dx=-0.17)
    ax = fig.add_subplot(gs[1])
    p = h[h["t_s"].isin([0, 60])].pivot_table(index=["id", "condition"], columns="t_s", values="hr_bpm").reset_index(); p["hrr60"] = p[0] - p[60]
    wide = p.pivot(index="id", columns="condition", values="hrr60").rename(columns=cn)
    est = {c: paired_ci(wide[c].values) for c in col}
    pf.ax_paired_estimate(ax, wide, list(col), col, est, L("60 s 心率下降 HRR60 (次/分)", "HRR60 (bpm)")); panel_letter(ax, "b", dx=-0.25)
    ax = fig.add_subplot(gs[2]); gm = {"Training": L("训练组", "Training"), "Control": L("对照组", "Control")}; v["g"] = v["group"].map(gm); v["t"] = (v["time"] == "Post").astype(int)
    pf.ax_prepost(ax, v.rename(columns={"rmssd_ms": "y"}), "id", "g", "t", "y", list(gm.values()), {gm["Training"]: C_MAGENTA, gm["Control"]: C_AMBER}, [L("前", "Pre"), L("后", "Post")], "rMSSD (ms)")
    ax.set_yscale("log"); ax.minorticks_off(); ax.set_yticks([20, 40, 80, 160]); ax.set_yticklabels(["20", "40", "80", "160"]); ax.text(0.97, 0.03, L("对数坐标", "log scale"), transform=ax.transAxes, ha="right", fontsize=5.5, color=C_GREY)
    panel_letter(ax, "c", dx=-0.25)
    save(fig, d, "fig1_hr_recovery_hrv", lang)


# ============================================================================ D03
def sim_d03(seed=3):
    rng = np.random.default_rng(seed)
    n, W = 30, 16
    base = rng.normal(2400, 350, n); rows = []
    for i in range(n):
        load = []
        for w in range(1, W + 1):
            ramp = 1 + 0.025 * min(w, 10) + (0.25 if w in (6, 11) else 0) * rng.random()
            load.append(max(600, base[i] * ramp * rng.lognormal(0, 0.30)))
        load = np.array(load)
        for w in range(1, W + 1):
            acute = load[w - 1]; chronic = load[max(0, w - 4):w].mean()
            acwr = acute / chronic if w >= 4 else np.nan
            risk = 0.012
            if np.isfinite(acwr):
                risk = 0.012 + (0.14 if acwr > 1.5 else 0.06 if acwr > 1.3 else 0.0 if acwr >= 0.8 else 0.045)
            rows.append((f"T{i + 1:03d}", w, round(load[w - 1]), round(acwr, 2) if np.isfinite(acwr) else "", int(rng.random() < risk)))
    d = ddir("D03_训练负荷监测")
    pd.DataFrame(rows, columns=["id", "week", "srpe_load_au", "acwr", "injury_next_week"]).to_csv(d / "load.csv", index=False)
    write_readme("D03_训练负荷监测", "球队训练负荷与损伤", "Team training load and injuries", "30 名运动员 16 周的 session-RPE 周负荷、急慢性负荷比（ACWR）与次周损伤。",
                 {"load.csv": ("每人每周一行", "One row per athlete-week", {"srpe_load_au": ("周负荷 AU", "Weekly load AU"), "acwr": ("急性:慢性负荷比（周 4 起）", "Acute:chronic workload ratio (from week 4)"), "injury_next_week": ("次周是否损伤", "Injury in the following week")})})


def fig_d03(lang):
    d = "D03_训练负荷监测"
    df = read(d, "load.csv")
    W = df.pivot(index="id", columns="week", values="srpe_load_au")
    fig = plt.figure(figsize=(DOUBLE, 4.9)); gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.1], width_ratios=[1.3, 1], hspace=0.5, wspace=0.34)
    ax = fig.add_subplot(gs[0, :])
    for _, r in W.iterrows():
        ax.plot(W.columns, r.values, color=C_LIGHT, lw=0.45, alpha=0.8)
    m = W.mean(); sd = W.std()
    ax.fill_between(W.columns, m - sd, m + sd, color=C_MAGENTA, alpha=0.14, lw=0); ax.plot(W.columns, m, color=C_MAGENTA, lw=1.8)
    ax.set_xlabel(L("周", "Week")); ax.set_ylabel(L("周负荷 (AU)", "Weekly load (AU)")); ax.text(0.99, 0.04, L("粗线：球队均值；阴影：±SD；细线：个体", "bold: team mean; band: ±SD; thin: individuals"), transform=ax.transAxes, ha="right", fontsize=5.5, color=C_GREY)
    panel_letter(ax, "a", dx=-0.05)
    ax = fig.add_subplot(gs[1, 0])
    z = (W.values - W.values.mean(1, keepdims=True)) / W.values.std(1, keepdims=True)
    im, order = ax_heatmap(ax, z, list(W.index), [str(c) for c in W.columns], cmap=SEQ, vmin=-2.5, vmax=2.5, cluster_rows=True)
    ax.set_yticks([]); ax.set_xlabel(L("周", "Week")); ax.set_ylabel(L("运动员（聚类排序）", "Athletes (clustered)"))
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02); cb.set_label(L("个人内 z 分数", "Within-athlete z-score"), fontsize=5.8); cb.ax.tick_params(labelsize=5); panel_letter(ax, "b", dx=-0.08)
    ax = fig.add_subplot(gs[1, 1])
    a = df[pd.to_numeric(df["acwr"], errors="coerce").notna()].copy(); a["acwr"] = a["acwr"].astype(float)
    bins = [0, 0.8, 1.3, 1.5, 9]; lab = ["<0.8", "0.8–1.3", "1.3–1.5", ">1.5"]; a["zone"] = pd.cut(a["acwr"], bins, labels=lab, right=False)
    cols = [C_SLATE, C_TEAL, C_AMBER, C_CORAL]
    for i, zn in enumerate(lab):
        s = a[a["zone"] == zn]; k, nn = int(s["injury_next_week"].sum()), len(s); p, lo, hi = wilson(k, nn)
        ax.bar(i, p * 100, color=cols[i], width=0.66, lw=0); ax.errorbar(i, p * 100, yerr=[[(p - lo) * 100], [(hi - p) * 100]], color=C_INK, capsize=2.5, lw=1); ax.text(i, hi * 100 + 0.6, f"n={nn}", ha="center", fontsize=5.4, color=C_GREY)
    ax.set_xticks(range(4)); ax.set_xticklabels(lab); ax.tick_params(axis="x", length=0); ax.set_xlabel("ACWR"); ax.set_ylabel(L("次周损伤发生率 (%)", "Next-week injury rate (%)")); hair_y(ax); panel_letter(ax, "c", dx=-0.25)
    save(fig, d, "fig1_training_load", lang)


# ============================================================================ D26
def sim_d26(seed=26):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(40):
        grp = "Intervention" if i < 20 else "Control"; mesor = rng.normal(122, 8); amp = rng.normal(11, 3) + (3 if grp == "Intervention" else 0)
        for h in range(24):
            sbp = mesor + amp * np.cos(2 * np.pi * (h - 15) / 24) + rng.normal(0, 3)
            rows.append((f"B{i + 1:03d}", grp, h, round(sbp, 1)))
    d = ddir("D26_动态血压_昼夜节律")
    pd.DataFrame(rows, columns=["id", "group", "hour", "sbp_mmhg"]).to_csv(d / "abpm.csv", index=False)
    write_readme("D26_动态血压_昼夜节律", "24 小时动态血压", "24-h ambulatory blood pressure", "40 人逐小时平均收缩压；干预组夜间下降更明显。", {"abpm.csv": ("每人每小时一行", "One row per person-hour", {"hour": ("钟点 0–23", "Clock hour 0–23"), "sbp_mmhg": ("收缩压 mmHg", "Systolic BP mmHg")})})


def fig_d26(lang):
    d = "D26_动态血压_昼夜节律"
    df = read(d, "abpm.csv"); gm = {"Control": L("对照组", "Control"), "Intervention": L("干预组", "Intervention")}; col = {gm["Control"]: C_AMBER, gm["Intervention"]: C_MAGENTA}
    fig = plt.figure(figsize=(DOUBLE, 3.0)); gs = fig.add_gridspec(1, 3, width_ratios=[1.4, 1, 0.9], wspace=0.45)
    ax = fig.add_subplot(gs[0]); ser = {}
    for k, v in gm.items():
        w = df[df["group"] == k].pivot(index="id", columns="hour", values="sbp_mmhg"); ser[v] = (w.mean().values, w.std().values / np.sqrt(len(w)))
    ax.axvspan(0, 6, color="#EDEDF5", lw=0); ax.axvspan(22, 23.5, color="#EDEDF5", lw=0); ax.text(3, 0.03, L("夜间", "Night"), transform=ax.get_xaxis_transform(), fontsize=5.5, color=C_GREY, ha="center")
    ax_bands(ax, np.arange(24), ser, col, dashed=[gm["Control"]]); ax.set_xlim(0, 23); ax.set_xticks([0, 6, 12, 18, 23]); ax.set_xlabel(L("钟点", "Clock hour")); ax.set_ylabel(L("收缩压 (mmHg)", "Systolic BP (mmHg)"))
    ax.legend(loc="upper left", fontsize=6); panel_letter(ax, "a", dx=-0.15)
    w = df.pivot_table(index=["id", "group"], columns="hour", values="sbp_mmhg").reset_index()
    day = w[list(range(8, 20))].mean(1); night = w[[0, 1, 2, 3, 4, 5]].mean(1); w["dip"] = (1 - night / day) * 100
    ax = fig.add_subplot(gs[1]); ax_raincloud(ax, {gm[k]: w[w["group"] == k]["dip"].values for k in gm}, col, L("夜间下降率 (%)", "Nocturnal dip (%)")); ax.axhline(10, color=C_GREY, lw=0.6, ls=":"); ax.axhline(0, color=C_GREY, lw=0.4, ls=":")
    panel_letter(ax, "b", dx=-0.25)
    ax = fig.add_subplot(gs[2]); cats = [(L("反勺型", "Reverse"), -99, 0), (L("非勺型", "Non-dipper"), 0, 10), (L("勺型", "Dipper"), 10, 20), (L("过度勺型", "Extreme dipper"), 20, 99)]; cc = [C_CORAL, C_AMBER, C_SLATE, C_MAGENTA]
    bars = []
    for k in gm:
        s = w[w["group"] == k]["dip"]; bars.append((gm[k], {c[0]: ((s >= c[1]) & (s < c[2])).mean() * 100 for c in cats}))
    ax_stacked_bars_mod(ax, bars, [c[0] for c in cats], dict(zip([c[0] for c in cats], cc)), L("受试者占比 (%)", "Participants (%)")); panel_letter(ax, "c", dx=-0.25)
    save(fig, d, "fig1_abpm", lang)


def ax_stacked_bars_mod(ax, bars, order, colors, ylabel):
    pf.ax_stacked_bars(ax, bars, order, colors, ylabel)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=colors[o]) for o in order], labels=order, loc="upper center", bbox_to_anchor=(0.5, 1.28), ncol=2, fontsize=5.4, handlelength=0.9, columnspacing=0.7)


DOMAINS = [("D01_心肺_分级运动", sim_d01, fig_d01), ("D02_HRV_心率恢复", sim_d02, fig_d02), ("D03_训练负荷监测", sim_d03, fig_d03), ("D26_动态血压_昼夜节律", sim_d26, fig_d26)]
