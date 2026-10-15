# -*- coding: utf-8 -*-
"""D04 肌电 · D05 力-时间曲线 · D06 力-速度关系 · D07 SPM 关节曲线 · D08 冲击载荷 · D09 IMU 一致性 · D24 平衡 COP · D25 GPS 球场热图"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from scipy import stats
from scipy.signal import find_peaks

from common import ddir, read, save, write_readme
from sportsci_figures.pubstyle.figures import *  # noqa: F401,F403   (all blocks, incl. figures_ext)
from sportsci_figures.pubstyle.style import tr as L, get_lang  # noqa: F401
from sportsci_figures.pubstyle import DOUBLE, panel_letter, arm_colors, fmt_p, condition_colors, dose_colors
from sportsci_figures.pubstyle import figures as pf
from sportsci_figures.pubstyle.style import C_AMBER, C_MAGENTA, C_SLATE, C_CORAL, C_GREY, C_INK, C_LIGHT, C_TEAL


def gauss(x, mu, sd):
    return np.exp(-0.5 * ((x - mu) / sd) ** 2)


# ============================================================================ D04 sEMG
def sim_d04(seed=4):
    rng = np.random.default_rng(seed)
    n = 18; pct = np.arange(0, 101); g_rows = []
    for i in range(n):
        sc = rng.lognormal(0, 0.18)
        for cond, a in (("Rested", 1.0), ("Fatigued", 1.32)):
            w = sc * a * (gauss(pct, 14, 7) * 55 + gauss(pct, 64, 10) * 34) + rng.normal(0, 2.2, len(pct)) + 3
            for p_, v in zip(pct, np.clip(w, 0.5, None)):
                g_rows.append((f"E{i + 1:03d}", cond, p_, round(v, 2)))
    f_rows = []
    pt = np.arange(0, 101, 5)
    for i in range(n):
        s_rms, s_mdf = rng.normal(0.9, 0.25), rng.normal(-0.33, 0.1)
        for p_ in pt:
            rms = 100 * (1 + 0.012 * s_rms * p_ * (1 - 0.003 * p_)) + rng.normal(0, 3)
            mdf = 100 * (1 + 0.0031 * s_mdf / 0.33 * p_ * 0.9) + rng.normal(0, 1.6)
            f_rows.append((f"E{i + 1:03d}", p_, round(rms, 1), round(mdf, 1)))
    d = ddir("D04_肌电_sEMG")
    pd.DataFrame(g_rows, columns=["id", "condition", "pct_cycle", "rms_pct_mvc"]).to_csv(d / "semg_gait.csv", index=False)
    pd.DataFrame(f_rows, columns=["id", "pct_time", "rms_pct_baseline", "mdf_pct_baseline"]).to_csv(d / "semg_fatigue.csv", index=False)
    write_readme("D04_肌电_sEMG", "表面肌电：步态包络与疲劳过程", "Surface EMG: gait envelope and fatigue", "18 人；股外侧肌；休息 vs 疲劳后的步态 RMS 包络；等长疲劳过程的 RMS 与中位频率 MDF。",
                 {"semg_gait.csv": ("步态周期 0–100% 的 RMS 包络", "RMS envelope across the gait cycle", {"rms_pct_mvc": ("%MVC", "%MVC")}), "semg_fatigue.csv": ("疲劳过程 RMS、MDF（相对起始 %）", "RMS and MDF during fatigue (% of baseline)", {"pct_time": ("占力竭时间 %", "% of time to exhaustion")})})


def fig_d04(lang):
    d = "D04_肌电_sEMG"
    g = read(d, "semg_gait.csv"); f = read(d, "semg_fatigue.csv")
    cn = {"Rested": L("休息", "Rested"), "Fatigued": L("疲劳后", "Fatigued")}; col = {cn["Rested"]: C_AMBER, cn["Fatigued"]: C_MAGENTA}
    fig = plt.figure(figsize=(DOUBLE, 3.3)); gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 1.1, 0.9], wspace=0.45)
    ax = fig.add_subplot(gs[0]); ser = {}
    for k, v in cn.items():
        w = g[g["condition"] == k].pivot(index="id", columns="pct_cycle", values="rms_pct_mvc"); ser[v] = (w.mean().values, w.std().values / np.sqrt(len(w)))
    ax_bands(ax, np.arange(101), ser, col, dashed=[cn["Rested"]]); ax.set_xlabel(L("步态周期 (%)", "Gait cycle (%)")); ax.set_ylabel(L("RMS (% MVC)", "RMS (% MVC)")); ax.legend(loc="upper right", fontsize=6)
    panel_letter(ax, "a", dx=-0.17)
    ax = fig.add_subplot(gs[1]); x = np.arange(0, 101, 5)
    r = f.pivot(index="id", columns="pct_time", values="rms_pct_baseline"); m = f.pivot(index="id", columns="pct_time", values="mdf_pct_baseline")
    ax_bands(ax, x, {"RMS": (r.mean().values, r.std().values / np.sqrt(len(r))), "MDF": (m.mean().values, m.std().values / np.sqrt(len(m)))}, {"RMS": C_MAGENTA, "MDF": C_CORAL}, dashed=["MDF"])
    ax.axhline(100, color=C_GREY, lw=0.5, ls=":"); ax.set_xlabel(L("占力竭时间 (%)", "Time to exhaustion (%)")); ax.set_ylabel(L("相对起始值 (%)", "% of baseline")); ax.legend(loc="center right", fontsize=6)
    ax.text(0.04, 0.96, L("RMS 上升、MDF 下降：疲劳的经典解耦", "RMS rises while MDF falls"), transform=ax.transAxes, fontsize=5.5, color=C_GREY, va="top"); panel_letter(ax, "b", dx=-0.2)
    ax = fig.add_subplot(gs[2])
    slope = lambda df: np.array([stats.linregress(x, df.loc[i].values).slope for i in df.index])
    ax_raincloud(ax, {"RMS": slope(r), "MDF": slope(m)}, {"RMS": C_MAGENTA, "MDF": C_CORAL}, L("斜率（%/% 时间）", "Slope (% per % time)")); ax.axhline(0, color=C_GREY, lw=0.5, ls=":"); panel_letter(ax, "c", dx=-0.3)
    save(fig, d, "fig1_semg", lang)


# ============================================================================ D05
def sim_d05(seed=5):
    rng = np.random.default_rng(seed)
    n = 16; t = np.arange(0, 301, 5.0); rows = []
    mult = {"CON": (1.0, 90), "PAP-Light": (1.035, 82), "PAP-Heavy": (1.07, 74)}
    for i in range(n):
        F0 = rng.normal(2700, 380); tau0 = rng.normal(92, 10); bw = rng.normal(80, 8)
        for c, (fm, tm) in mult.items():
            tau = tau0 * tm / 90
            F = bw * 9.81 + (F0 * fm - bw * 9.81) * (1 - np.exp(-t / tau)) * (1 - 0.2 * np.exp(-t / 40)) + rng.normal(0, 12, len(t))
            for a, b in zip(t, F):
                rows.append((f"F{i + 1:03d}", c, a, round(b, 1)))
    pd.DataFrame(rows, columns=["id", "condition", "t_ms", "force_n"]).to_csv(ddir("D05_力时曲线_等长")/"isometric_force_time.csv", index=False)
    write_readme("D05_力时曲线_等长", "等长大腿中部拉（IMTP）力-时间曲线（增强后效应，交叉）", "Isometric mid-thigh pull force–time curves (PAP, crossover)", "16 人，3 个条件；0–300 ms 力-时间曲线。",
                 {"isometric_force_time.csv": ("每人每条件一条曲线", "One curve per person per condition", {"t_ms": ("起拉后 ms", "ms after onset"), "force_n": ("力 N", "Force N")})})


def fig_d05(lang):
    d = "D05_力时曲线_等长"
    f = read(d, "isometric_force_time.csv"); cn = {"CON": "CON", "PAP-Light": L("PAP 轻负荷", "PAP-light"), "PAP-Heavy": L("PAP 重负荷", "PAP-heavy")}
    col = {cn["CON"]: C_AMBER, cn["PAP-Light"]: C_CORAL, cn["PAP-Heavy"]: C_MAGENTA}
    fig = plt.figure(figsize=(DOUBLE, 3.3)); gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1, 1], wspace=0.45)
    ax = fig.add_subplot(gs[0]); ser = {}
    for k, v in cn.items():
        w = f[f["condition"] == k].pivot(index="id", columns="t_ms", values="force_n"); ser[v] = (w.mean().values, w.std().values / np.sqrt(len(w)))
    ax_bands(ax, np.sort(f["t_ms"].unique()), ser, col, dashed=[cn["CON"]]); ax.set_xlabel(L("起拉后时间 (ms)", "Time from onset (ms)")); ax.set_ylabel(L("力 (N)", "Force (N)")); ax.legend(loc="lower right", fontsize=6)
    panel_letter(ax, "a", dx=-0.17)
    rfd = f[f["t_ms"] == 100].pivot(index="id", columns="condition", values="force_n"); base = f[f["t_ms"] == 0].pivot(index="id", columns="condition", values="force_n")
    rfd = ((rfd - base) / 0.1).rename(columns=cn)
    ax = fig.add_subplot(gs[1]); est = {c: paired_ci(rfd[c].values) for c in col}
    pf.ax_paired_estimate(ax, rfd, list(col), col, est, L("RFD 0–100 ms (N/s)", "RFD 0–100 ms (N/s)")); panel_letter(ax, "b", dx=-0.25)
    pk = f[f["t_ms"] == 300].pivot(index="id", columns="condition", values="force_n").rename(columns=cn)
    ax = fig.add_subplot(gs[2]); ax_raincloud(ax, {c: pk[c].values for c in col}, col, L("300 ms 时的力 (N)", "Force at 300 ms (N)"), paired_lines=pk); ax.set_xticklabels([c.replace(" ", "\n") for c in col], fontsize=5.8)
    panel_letter(ax, "c", dx=-0.25)
    save(fig, d, "fig1_force_time", lang)


# ============================================================================ D06
def sim_d06(seed=6):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(14):
        grp = "Sprint" if i < 7 else "Heavy"
        F0 = rng.normal(29 if grp == "Sprint" else 36, 2.2); V0 = rng.normal(3.1 if grp == "Sprint" else 2.4, 0.2)
        for load in (0, 20, 40, 60, 80):
            v = V0 * (1 - (load / 100) ** 0.9 * 0.82) * rng.lognormal(0, 0.03)
            F = F0 * (1 - v / V0) + 0.0 + rng.normal(0, 0.6)
            F = max(F, 0.5) + 9.81 * (load / 100) * 0.4
            rows.append((f"V{i + 1:03d}", grp, load, round(v, 3), round(F, 2)))
    pd.DataFrame(rows, columns=["id", "group", "load_pct_bm", "velocity_m_s", "force_n_kg"]).to_csv(ddir("D06_力速关系")/"fv_profile.csv", index=False)
    write_readme("D06_力速关系", "力-速度-功率剖面（跳深/跳蹲）", "Force–velocity–power profiling", "14 名运动员，5 个负荷；速度与相对力。", {"fv_profile.csv": ("每人每负荷一行", "One row per athlete per load", {"velocity_m_s": ("平均速度 m/s", "Mean velocity m/s"), "force_n_kg": ("相对力 N/kg", "Relative force N/kg")})})


def fig_d06(lang):
    d = "D06_力速关系"; df = read(d, "fv_profile.csv")
    gn = {"Sprint": L("速度导向", "Speed-oriented"), "Heavy": L("力量导向", "Force-oriented")}; col = {gn["Sprint"]: C_AMBER, gn["Heavy"]: C_MAGENTA}
    fig = plt.figure(figsize=(DOUBLE, 3.3)); gs = fig.add_gridspec(1, 3, width_ratios=[1.1, 1.1, 0.9], wspace=0.45)
    ax = fig.add_subplot(gs[0]); params = []
    for k, v in gn.items():
        for i, s in df[df["group"] == k].groupby("id"):
            sl, ic, *_ = stats.linregress(s["velocity_m_s"], s["force_n_kg"]); V0 = -ic / sl; F0 = ic; params.append((k, i, F0, V0, F0 * V0 / 4))
            xs = np.linspace(0, V0, 20); ax.plot(xs, ic + sl * xs, color=col[v], lw=0.6, alpha=0.4)
            ax.scatter(s["velocity_m_s"], s["force_n_kg"], s=7, color=col[v], alpha=0.5, lw=0)
        pm = [p for p in params if p[0] == k]; F0m, V0m = np.mean([p[2] for p in pm]), np.mean([p[3] for p in pm]); ax.plot([0, V0m], [F0m, 0], color=col[v], lw=2.0, label=v)
    ax.set_xlabel(L("速度 (m/s)", "Velocity (m/s)")); ax.set_ylabel(L("相对力 (N/kg)", "Relative force (N/kg)")); ax.legend(loc="upper right", fontsize=6); panel_letter(ax, "a", dx=-0.17); ax.set_xlim(0, None); ax.set_ylim(0, None)
    P = pd.DataFrame(params, columns=["group", "id", "F0", "V0", "Pmax"])
    ax = fig.add_subplot(gs[1])
    for k, v in gn.items():
        pm = P[P["group"] == k]; F0m, V0m = pm["F0"].mean(), pm["V0"].mean(); xs = np.linspace(0, V0m, 60)
        arr = np.array([r.F0 * xs * (1 - xs / r.V0) for r in pm.itertuples()]); m, se = mean_se_curves(np.where(xs[None, :] <= pm["V0"].values[:, None], arr, np.nan))
        ax.fill_between(xs, m - se, m + se, color=col[v], alpha=0.16, lw=0); ax.plot(xs, m, color=col[v], lw=1.8)
    ax.set_xlabel(L("速度 (m/s)", "Velocity (m/s)")); ax.set_ylabel(L("相对功率 (W/kg)", "Relative power (W/kg)")); panel_letter(ax, "b", dx=-0.2)
    ax = fig.add_subplot(gs[2]); ax_raincloud(ax, {gn[k]: P[P["group"] == k]["Pmax"].values for k in gn}, col, L("最大功率 Pmax (W/kg)", "Pmax (W/kg)")); panel_letter(ax, "c", dx=-0.25)
    save(fig, d, "fig1_force_velocity", lang)


# ============================================================================ D07 SPM
def sim_d07(seed=7):
    rng = np.random.default_rng(seed)
    n = 20; pct = np.arange(0, 101); rows = []
    for i in range(n):
        amp = rng.normal(42, 4); shift = rng.normal(0, 2)
        subj = rng.normal(0, 3)
        for shoe, delta in (("Stiff", 0.0), ("Soft", -3.4)):
            curve = 8 + amp * gauss(pct, 38 + shift, 14) + delta * gauss(pct, 40, 9) + subj + rng.normal(0, 1.1, len(pct))
            for p_, v in zip(pct, curve):
                rows.append((f"K{i + 1:03d}", shoe, p_, round(v, 2)))
    pd.DataFrame(rows, columns=["id", "shoe", "pct_stance", "knee_flexion_deg"]).to_csv(ddir("D07_关节曲线_SPM")/"knee_angle.csv", index=False)
    write_readme("D07_关节曲线_SPM", "支撑期膝关节屈曲角曲线（两种鞋，配对）", "Stance-phase knee flexion curves (two shoes, paired)", "20 人，0–100% 支撑期。", {"knee_angle.csv": ("每人每鞋一条曲线", "One curve per person per shoe", {"pct_stance": ("支撑期 %", "% stance"), "knee_flexion_deg": ("膝屈曲 °", "Knee flexion °")})})


def fig_d07(lang):
    d = "D07_关节曲线_SPM"; df = read(d, "knee_angle.csv")
    cn = {"Stiff": L("硬底鞋", "Stiff"), "Soft": L("软底鞋", "Soft")}; col = {cn["Stiff"]: C_AMBER, cn["Soft"]: C_MAGENTA}
    A = {k: df[df["shoe"] == k].pivot(index="id", columns="pct_stance", values="knee_flexion_deg") for k in cn}
    x = np.arange(101); diff = A["Soft"].values - A["Stiff"].values; n = len(diff)
    tcurve = diff.mean(0) / (diff.std(0, ddof=1) / np.sqrt(n))
    rng = np.random.default_rng(0); mx = []
    for _ in range(2000):
        sg = rng.choice([-1, 1], n)[:, None]; dd = diff * sg; mx.append(np.max(np.abs(dd.mean(0) / (dd.std(0, ddof=1) / np.sqrt(n)))))
    thr = np.percentile(mx, 95)
    fig = plt.figure(figsize=(DOUBLE, 4.2)); gs = fig.add_gridspec(2, 2, height_ratios=[1.3, 1], hspace=0.5, wspace=0.32)
    ax = fig.add_subplot(gs[0, :]); ser = {cn[k]: (A[k].mean().values, A[k].std().values) for k in cn}
    ax_bands(ax, x, ser, col, dashed=[cn["Stiff"]]); ax.set_ylabel(L("膝屈曲角 (°)", "Knee flexion (°)")); ax.set_xlabel(L("支撑期 (%)", "Stance phase (%)")); ax.legend(loc="upper right", fontsize=6)
    ax.text(0.01, 0.96, L("均值 ± SD", "Mean ± SD"), transform=ax.transAxes, fontsize=5.5, color=C_GREY, va="top"); panel_letter(ax, "a", dx=-0.05)
    ax = fig.add_subplot(gs[1, 0]); cl = ax_spm(ax, x, tcurve, thr, "t"); ax.set_xlabel(L("支撑期 (%)", "Stance phase (%)"))
    ax.set_title(L("SPM{t}：软 − 硬（置换检验，α=0.05）", "SPM{t}: soft − stiff (permutation, α = 0.05)"), fontsize=6.3, loc="left", pad=3)
    for a_, b_ in cl:
        ax.text((a_ + b_) / 2, thr * 1.05, f"{a_:.0f}–{b_:.0f}%", fontsize=5.3, ha="center", color=C_MAGENTA)
    panel_letter(ax, "b", dx=-0.17)
    ax = fig.add_subplot(gs[1, 1]); pk = pd.DataFrame({cn[k]: A[k].max(1).values for k in cn}); est = {c: paired_ci(pk[c].values) for c in col}
    pf.ax_paired_estimate(ax, pk, list(col), col, est, L("峰值膝屈曲 (°)", "Peak knee flexion (°)")); dd = paired_ci(pk[cn["Soft"]].values, pk[cn["Stiff"]].values)
    ax.set_title(f"{L('差值', 'Difference')} {dd[0]:+.1f}° ({dd[1]:.1f}, {dd[2]:.1f})", fontsize=6.3, loc="left", pad=3); panel_letter(ax, "c", dx=-0.2)
    save(fig, d, "fig1_spm_knee", lang)


# ============================================================================ D08
def sim_d08(seed=8):
    rng = np.random.default_rng(seed)
    n = 20; pct = np.arange(0, 101); curves, strides = [], []
    for i in range(n):
        a_i = rng.normal(2.55, 0.18)
        for shoe, imp, lr in (("Soft", 1.95, 62), ("Hard", 2.30, 88)):
            base = imp * gauss(pct, 12, 3.6) + a_i * gauss(pct, 48, 15) * (1 + 0.0) + rng.normal(0, 0.03, 101) * 0
            for p_, v in zip(pct, base + rng.normal(0, 0.02, 101)):
                curves.append((f"L{i + 1:03d}", shoe, p_, round(v, 3)))
            lri = lr * rng.lognormal(0, 0.18)
            for s in range(30):
                strides.append((f"L{i + 1:03d}", shoe, s + 1, round(lri * rng.lognormal(0, 0.12), 1), round(imp * rng.normal(1, 0.05), 3)))
    d = ddir("D08_冲击载荷_VGRF")
    pd.DataFrame(curves, columns=["id", "shoe", "pct_stance", "vgrf_bw"]).to_csv(d / "vgrf_curve.csv", index=False)
    pd.DataFrame(strides, columns=["id", "shoe", "stride", "loading_rate_bw_s", "impact_peak_bw"]).to_csv(d / "vgrf_strides.csv", index=False)
    write_readme("D08_冲击载荷_VGRF", "跑步垂直地面反作用力与负荷率", "Running vertical GRF and loading rate", "20 人 × 2 种鞋 × 30 步。", {"vgrf_curve.csv": ("平均 VGRF 曲线（BW）", "Mean VGRF curve (BW)", {}) if False else ("平均 VGRF 曲线（BW）", "Mean VGRF curve (BW)", {"vgrf_bw": ("体重倍数", "Body weights")}),
                                                            "vgrf_strides.csv": ("逐步参数", "Stride-level metrics", {"loading_rate_bw_s": ("负荷率 BW/s", "Loading rate BW/s"), "impact_peak_bw": ("冲击峰 BW", "Impact peak BW")})})


def fig_d08(lang):
    d = "D08_冲击载荷_VGRF"; c = read(d, "vgrf_curve.csv"); s = read(d, "vgrf_strides.csv")
    cn = {"Soft": L("软底", "Soft"), "Hard": L("硬底", "Hard")}; col = {cn["Soft"]: C_MAGENTA, cn["Hard"]: C_AMBER}
    fig = plt.figure(figsize=(DOUBLE, 3.2)); gs = fig.add_gridspec(1, 3, width_ratios=[1.5, 1, 1], wspace=0.42)
    ax = fig.add_subplot(gs[0]); ser = {}
    for k, v in cn.items():
        w = c[c["shoe"] == k].pivot(index="id", columns="pct_stance", values="vgrf_bw"); ser[v] = (w.mean().values, w.std().values / np.sqrt(len(w)))
    ax_bands(ax, np.arange(101), ser, col, dashed=[cn["Hard"]]); ax.set_xlabel(L("支撑期 (%)", "Stance phase (%)")); ax.set_ylabel(L("垂直 GRF (BW)", "Vertical GRF (BW)")); ax.legend(loc="center right", fontsize=6)
    ins = inset_axes(ax, width="34%", height="32%", loc="upper right", borderpad=1.0)
    for k, v in cn.items():
        ins.hist(s[s["shoe"] == k]["impact_peak_bw"], bins=14, color=col[v], alpha=0.75, lw=0)
    ins.set_xticks([]); ins.set_yticks([]); ins.set_title(L("冲击峰分布（逐步）", "Impact-peak, all strides"), fontsize=5, pad=1.5)
    for sp in ("top", "right"):
        ins.spines[sp].set_visible(False)
    panel_letter(ax, "a", dx=-0.13)
    m = s.groupby(["id", "shoe"])["loading_rate_bw_s"].mean().unstack().rename(columns=cn)
    ax = fig.add_subplot(gs[1]); ax_raincloud(ax, {v: m[v].values for v in col}, col, L("负荷率 (BW/s)", "Loading rate (BW/s)"), paired_lines=m); panel_letter(ax, "b", dx=-0.25)
    ax = fig.add_subplot(gs[2]); est = {v: paired_ci(m[v].values) for v in col}
    dd = (m[cn["Hard"]] - m[cn["Soft"]]).values; mu, lo, hi = paired_ci(dd)
    ax.errorbar([0], [mu], yerr=[[mu - lo], [hi - mu]], fmt="o", ms=6, color=C_MAGENTA, ecolor=C_INK, capsize=3); ax.scatter(np.random.default_rng(1).normal(0, 0.05, len(dd)), dd, s=8, color=C_SLATE, alpha=0.6, lw=0)
    ax.axhline(0, color=C_GREY, lw=0.6, ls=":"); ax.set_xticks([0]); ax.set_xticklabels([L("硬 − 软", "Hard − soft")]); ax.set_xlim(-0.5, 0.5); ax.set_ylabel(L("负荷率差 (BW/s)", "Loading-rate difference (BW/s)"))
    ax.set_title(f"{mu:+.1f} ({lo:.1f}, {hi:.1f})", fontsize=6.3, loc="left", pad=3); panel_letter(ax, "c", dx=-0.3); hair_y(ax)
    save(fig, d, "fig1_vgrf", lang)


# ============================================================================ D09 IMU
def sim_d09(seed=9):
    rng = np.random.default_rng(seed)
    d = ddir("D09_IMU_一致性")
    t = np.arange(0, 8, 0.01); acc = 0.15 * rng.normal(size=len(t)) + 1.0; st = np.arange(0.4, 7.8, 0.52) + rng.normal(0, 0.01, len(np.arange(0.4, 7.8, 0.52)))
    for s0 in st:
        acc += 2.6 * np.exp(-0.5 * ((t - s0) / 0.025) ** 2) + 0.7 * np.exp(-0.5 * ((t - s0 - 0.12) / 0.06) ** 2)
    pd.DataFrame({"t_s": t.round(3), "acc_vertical_g": acc.round(3)}).to_csv(d / "acc_trace.csv", index=False)
    rows = []
    for i in range(20):
        for s in range(10):
            tru = rng.normal(1050, 60); rows.append((f"M{i + 1:03d}", s + 1, round(tru + rng.normal(4, 13), 1), round(tru, 1)))
    pd.DataFrame(rows, columns=["id", "stride", "imu_stride_ms", "forceplate_stride_ms"]).to_csv(d / "stride_time_agreement.csv", index=False)
    a = [(f"M{i + 1:03d}", "Healthy", round(abs(rng.normal(3.2, 1.6)), 2)) for i in range(25)] + [(f"M{i + 26:03d}", "Injured", round(abs(rng.normal(9.5, 4.2)), 2)) for i in range(25)]
    pd.DataFrame(a, columns=["id", "group", "asymmetry_index_pct"]).to_csv(d / "asymmetry.csv", index=False)
    write_readme("D09_IMU_一致性", "可穿戴 IMU：步态事件检测、与测力台一致性、对称性", "Wearable IMU: step detection, agreement with force plate, asymmetry", "原始加速度、逐步步时一致性（20 人×10 步）、对称性指数。",
                 {"acc_trace.csv": ("8 s 垂直加速度（100 Hz）", "8 s vertical acceleration at 100 Hz", {}), "stride_time_agreement.csv": ("IMU 与测力台步时", "IMU vs force-plate stride time", {}), "asymmetry.csv": ("对称性指数 %（健康 vs 受伤）", "Asymmetry index %", {})})


def fig_d09(lang):
    d = "D09_IMU_一致性"; tr = read(d, "acc_trace.csv"); ag = read(d, "stride_time_agreement.csv"); asy = read(d, "asymmetry.csv")
    fig = plt.figure(figsize=(DOUBLE, 5.0)); gs = fig.add_gridspec(2, 3, height_ratios=[0.8, 1.2], hspace=0.62, wspace=0.52)
    ax = fig.add_subplot(gs[0, :]); ax.plot(tr["t_s"], tr["acc_vertical_g"], color=C_SLATE, lw=0.8)
    pk, _ = find_peaks(tr["acc_vertical_g"].values, height=2.2, distance=30); ax.plot(tr["t_s"].values[pk], tr["acc_vertical_g"].values[pk], "v", color=C_MAGENTA, ms=4.5, label=L("检测到的触地", "Detected foot strikes"))
    ax.set_xlabel(L("时间 (s)", "Time (s)")); ax.set_ylabel(L("垂直加速度 (g)", "Vertical acceleration (g)")); ax.legend(loc="upper right", bbox_to_anchor=(1.0, 1.25), fontsize=6); ax.set_xlim(0, 8); panel_letter(ax, "a", dx=-0.04)
    ax = fig.add_subplot(gs[1, 0]); ax_identity(ax, ag["forceplate_stride_ms"], ag["imu_stride_ms"], L("测力台步时 (ms)", "Force-plate stride time (ms)"), L("IMU 步时 (ms)", "IMU stride time (ms)")); panel_letter(ax, "b", dx=-0.3)
    ax = fig.add_subplot(gs[1, 1]); ax_bland_altman(ax, ag["imu_stride_ms"], ag["forceplate_stride_ms"], L("两方法均值 (ms)", "Mean of methods (ms)"), L("IMU − 测力台 (ms)", "IMU − force plate (ms)"), "ms"); panel_letter(ax, "c", dx=-0.3)
    ax = fig.add_subplot(gs[1, 2]); gn = {"Healthy": L("健康", "Healthy"), "Injured": L("受伤", "Injured")}; col = {gn["Healthy"]: C_SLATE, gn["Injured"]: C_CORAL}
    ax_raincloud(ax, {gn[k]: asy[asy["group"] == k]["asymmetry_index_pct"].values for k in gn}, col, L("对称性指数 (%)", "Asymmetry index (%)")); ax.axhline(10, color=C_GREY, lw=0.7, ls=(0, (3, 2))); ax.text(-0.45, 10, L("10% 阈值", "10% cut-off"), fontsize=5.4, color=C_GREY, ha="left", va="bottom")
    panel_letter(ax, "d", dx=-0.3)
    save(fig, d, "fig1_imu", lang)


# ============================================================================ D24 COP
def sim_d24(seed=24):
    rng = np.random.default_rng(seed); rows = []
    for i in range(16):
        sub = rng.lognormal(0, 0.2)
        for cond, k in (("EyesOpen", 1.0), ("EyesClosed", 1.7)):
            x = y = 0.0; ax_ = ay = 0.0
            for s in range(600):
                ax_ = 0.97 * ax_ + rng.normal(0, 0.55 * k * sub); ay = 0.97 * ay + rng.normal(0, 0.8 * k * sub)
                x = 0.9 * x + ax_ * 0.3 + rng.normal(0, 0.25); y = 0.9 * y + ay * 0.3 + rng.normal(0, 0.3)
                rows.append((f"C{i + 1:03d}", cond, round(s / 20, 2), round(x, 2), round(y, 2)))
    pd.DataFrame(rows, columns=["id", "condition", "t_s", "cop_ml_mm", "cop_ap_mm"]).to_csv(ddir("D24_平衡_COP")/"cop.csv", index=False)
    write_readme("D24_平衡_COP", "静态站立压力中心（COP）摇摆", "Quiet-standing centre-of-pressure sway", "16 人 × 睁眼/闭眼 × 30 s（20 Hz）。", {"cop.csv": ("COP 轨迹", "COP trajectories", {"cop_ml_mm": ("内外侧 mm", "Medio-lateral mm"), "cop_ap_mm": ("前后侧 mm", "Antero-posterior mm")})})


def fig_d24(lang):
    d = "D24_平衡_COP"; df = read(d, "cop.csv"); cn = {"EyesOpen": L("睁眼", "Eyes open"), "EyesClosed": L("闭眼", "Eyes closed")}; col = {cn["EyesOpen"]: C_SLATE, cn["EyesClosed"]: C_MAGENTA}
    fig = plt.figure(figsize=(DOUBLE, 3.2)); gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.95], wspace=0.42)
    ax = fig.add_subplot(gs[0]); one = df[df["id"] == "C003"]
    for k, v in cn.items():
        s = one[one["condition"] == k]; ax.plot(s["cop_ml_mm"], s["cop_ap_mm"], color=col[v], lw=0.4, alpha=0.7); ax_ellipse(ax, s["cop_ml_mm"].values - 0, s["cop_ap_mm"].values, col[v], scatter=False, label=v)
    ax.set_aspect("equal", "datalim"); ax.set_xlabel(L("内外侧 (mm)", "Medio-lateral (mm)")); ax.set_ylabel(L("前后 (mm)", "Antero-posterior (mm)")); ax.legend(loc="upper right", fontsize=6); ax.set_title(L("单个受试者轨迹与 95% 椭圆", "One participant, 95% ellipse"), fontsize=6.3, loc="left", pad=3)
    panel_letter(ax, "a", dx=-0.2, dy=1.08)
    ax = fig.add_subplot(gs[1]); areas = {}
    for k, v in cn.items():
        s = df[df["condition"] == k]; xc = s["cop_ml_mm"] - s.groupby("id")["cop_ml_mm"].transform("mean"); yc = s["cop_ap_mm"] - s.groupby("id")["cop_ap_mm"].transform("mean")
        ax_ellipse(ax, xc.values, yc.values, col[v], scatter=False, label=v)
    ax.set_aspect("equal", "datalim"); ax.autoscale(); ax.set_xlabel(L("内外侧 (mm)", "Medio-lateral (mm)")); ax.set_ylabel(L("前后 (mm)", "Antero-posterior (mm)")); ax.set_title(L("全部受试者合并（去均值）", "All participants (mean-centred)"), fontsize=6.3, loc="left", pad=3)
    panel_letter(ax, "b", dx=-0.2, dy=1.08)
    ax = fig.add_subplot(gs[2]); rows = []
    for (i, k), s in df.groupby(["id", "condition"]):
        rows.append((i, cn[k], 0 if k == "EyesOpen" else 1, ax_ellipse(plt.figure().add_subplot(), s["cop_ml_mm"].values, s["cop_ap_mm"].values, "k", scatter=False)))
    plt.close("all")
    # re-apply style after the throw-away figures
    ar = pd.DataFrame(rows, columns=["id", "cond", "t", "y"]); gcol = {cn["EyesOpen"]: C_SLATE, cn["EyesClosed"]: C_MAGENTA}
    w = ar.pivot(index="id", columns="cond", values="y")
    ax_raincloud(ax, {k: w[k].values for k in gcol}, gcol, L("95% 椭圆面积 (mm²)", "95% ellipse area (mm²)"), paired_lines=w); panel_letter(ax, "c", dx=-0.25)
    save(fig, d, "fig1_cop", lang)


# ============================================================================ D25 GPS
def sim_d25(seed=25):
    rng = np.random.default_rng(seed)
    n = 5400; x = np.zeros(n); y = np.zeros(n); x[0], y[0] = 52, 34; vx = vy = 0
    for k in range(1, n):
        vx = 0.96 * vx + rng.normal(0, 0.35) + 0.01 * (58 - x[k - 1]); vy = 0.96 * vy + rng.normal(0, 0.35) + 0.015 * (34 - y[k - 1])
        x[k] = np.clip(x[k - 1] + vx, 2, 103); y[k] = np.clip(y[k - 1] + vy, 2, 66)
    d = ddir("D25_GPS_球场热图")
    pd.DataFrame({"x_m": x.round(2), "y_m": y.round(2)}).to_csv(d / "gps_positions.csv", index=False)
    rows = []
    for pos, base in (("DF", [2800, 3600, 2100, 560, 120]), ("MF", [2400, 3900, 2900, 880, 260]), ("FW", [2300, 3500, 2500, 780, 330])):
        for p in range(8):
            for m in range(1, 11):
                z = [max(0, b * rng.lognormal(0, 0.12)) for b in base]; rows.append((pos, f"{pos}{p + 1}", m, *[round(v) for v in z]))
    pd.DataFrame(rows, columns=["position", "player", "match", "z1_walk_m", "z2_jog_m", "z3_run_m", "z4_hsr_m", "z5_sprint_m"]).to_csv(d / "speed_zones.csv", index=False)
    write_readme("D25_GPS_球场热图", "GPS 追踪：位置热图与速度区间距离", "GPS tracking: position heat map and speed-zone distance", "一名中场球员的位置；3 个位置 × 8 名球员 × 10 场比赛的速度区间距离。", {"gps_positions.csv": ("位置 m（105×68 球场）", "Positions in metres (105 × 68 pitch)", {}), "speed_zones.csv": ("各速度区距离 m", "Distance per speed zone m", {})})


def fig_d25(lang):
    d = "D25_GPS_球场热图"; pos = read(d, "gps_positions.csv"); z = read(d, "speed_zones.csv")
    fig = plt.figure(figsize=(DOUBLE, 3.2)); gs = fig.add_gridspec(1, 3, width_ratios=[1.45, 1.1, 1.0], wspace=0.35)
    ax = fig.add_subplot(gs[0]); im = ax_pitch_heat(ax, pos["x_m"].values, pos["y_m"].values); ax.set_title(L("单场比赛位置密度", "Position density, one match"), fontsize=6.5, loc="left", pad=2)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.01, orientation="horizontal", aspect=30); cb.set_label(L("相对时间占比", "Relative time share"), fontsize=5.5); cb.ax.tick_params(labelsize=5); panel_letter(ax, "a", dx=-0.03, dy=1.12)
    ax = fig.add_subplot(gs[1]); cols = ["z1_walk_m", "z2_jog_m", "z3_run_m", "z4_hsr_m", "z5_sprint_m"]; zl = L(["步行", "慢跑", "跑动", "高速跑", "冲刺"], ["Walk", "Jog", "Run", "High-speed", "Sprint"]); zc = [C_LIGHT, C_SLATE, C_AMBER, C_CORAL, C_MAGENTA]
    pm = z.groupby("position")[cols].mean().loc[["DF", "MF", "FW"]]
    for i, (p_, r) in enumerate(pm.iterrows()):
        b = 0
        for c, cl in zip(cols, zc):
            ax.bar(i, r[c], bottom=b, color=cl, width=0.62, lw=0); b += r[c]
        ax.text(i, b + 120, f"{b / 1000:.1f} km", ha="center", fontsize=5.8)
    ax.set_xticks(range(3)); ax.set_xticklabels([L("后卫", "Defenders"), L("中场", "Midfielders"), L("前锋", "Forwards")], fontsize=6); ax.tick_params(axis="x", length=0); ax.set_ylabel(L("场均距离 (m)", "Distance per match (m)")); ax.set_ylim(0, 15000)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in zc[::-1]], labels=zl[::-1], loc="upper left", fontsize=5.3, ncol=1, handlelength=0.9); panel_letter(ax, "b", dx=-0.22)
    ax = fig.add_subplot(gs[2]); pc = {"DF": C_SLATE, "MF": C_MAGENTA, "FW": C_AMBER}; z["hs"] = z["z4_hsr_m"] + z["z5_sprint_m"]
    for p_ in ("DF", "MF", "FW"):
        w = z[z["position"] == p_].pivot_table(index="player", columns="match", values="hs"); m, se = w.mean().values, w.std().values / np.sqrt(len(w)); ax.fill_between(w.columns, m - se, m + se, color=pc[p_], alpha=0.16, lw=0); ax.plot(w.columns, m, color=pc[p_], lw=1.6, label=p_)
    ax.set_xlabel(L("比赛序号", "Match number")); ax.set_ylabel(L("高速跑 + 冲刺距离 (m)", "High-speed + sprint distance (m)")); ax.legend(fontsize=6, loc="upper right", ncol=3); panel_letter(ax, "c", dx=-0.25)
    save(fig, d, "fig1_gps", lang)


DOMAINS = [("D04_肌电_sEMG", sim_d04, fig_d04), ("D05_力时曲线_等长", sim_d05, fig_d05), ("D06_力速关系", sim_d06, fig_d06), ("D07_关节曲线_SPM", sim_d07, fig_d07),
           ("D08_冲击载荷_VGRF", sim_d08, fig_d08), ("D09_IMU_一致性", sim_d09, fig_d09), ("D24_平衡_COP", sim_d24, fig_d24), ("D25_GPS_球场热图", sim_d25, fig_d25)]
