# -*- coding: utf-8 -*-
"""D20 睡眠与可穿戴 · D21 运动后生物标志物 · D22 组学（火山图/热图/PCA） · D23 研究时间线与周期化"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

from common import ddir, read, save, write_readme
from sportsci_figures.pubstyle.figures import *  # noqa: F401,F403   (all blocks, incl. figures_ext)
from sportsci_figures.pubstyle.style import tr as L, get_lang  # noqa: F401
from sportsci_figures.pubstyle import DOUBLE, panel_letter, arm_colors, fmt_p, condition_colors, dose_colors
from sportsci_figures.pubstyle import figures as pf
from sportsci_figures.pubstyle.style import C_AMBER, C_MAGENTA, C_SLATE, C_CORAL, C_GREY, C_INK, C_LIGHT, C_TEAL


# ============================================================================ D20
def sim_d20(seed=20):
    rng = np.random.default_rng(seed); rows, steps = [], []
    for i in range(40):
        grp = "Travel" if i < 20 else "Home"; base = rng.normal(0, 1)
        for n in range(1, 15):
            jet = (2.6 - 0.8 * n) if (grp == "Travel" and n <= 3) else 0
            deep = max(20, rng.normal(78, 14) - 14 * max(jet, 0)); rem = max(25, rng.normal(98, 16) - 9 * max(jet, 0)); awake = max(5, rng.normal(30, 10) + 11 * max(jet, 0))
            light = max(150, 480 - deep - rem - awake - rng.normal(40, 12) - 20 * max(jet, 0))
            rows.append((f"W{i + 1:03d}", grp, n, round(deep), round(rem), round(light), round(awake)))
            steps.append((f"W{i + 1:03d}", grp, n, int(rng.lognormal(np.log(9500 if grp == "Home" else 7800 if n <= 3 else 9200), 0.32))))
    d = ddir("D20_睡眠_可穿戴")
    pd.DataFrame(rows, columns=["id", "group", "night", "deep_min", "rem_min", "light_min", "awake_min"]).to_csv(d / "sleep.csv", index=False)
    pd.DataFrame(steps, columns=["id", "group", "day", "steps"]).to_csv(d / "steps.csv", index=False)
    write_readme("D20_睡眠_可穿戴", "可穿戴睡眠与步数（客场旅行 vs 主场）", "Wearable sleep and steps (travel vs home)", "40 人 14 晚。", {"sleep.csv": ("每晚睡眠分期", "Sleep stages per night", {"deep_min": ("深睡 min", "Deep min"), "rem_min": ("REM min", "REM min"), "light_min": ("浅睡 min", "Light min"), "awake_min": ("清醒 min", "Awake min")}), "steps.csv": ("每日步数", "Daily steps", {})})


def fig_d20(lang):
    d = "D20_睡眠_可穿戴"; s = read(d, "sleep.csv"); st = read(d, "steps.csv"); gn = {"Home": L("主场", "Home"), "Travel": L("旅行", "Travel")}; gc = {gn["Home"]: C_SLATE, gn["Travel"]: C_MAGENTA}
    s["total"] = s["deep_min"] + s["rem_min"] + s["light_min"]
    fig = plt.figure(figsize=(DOUBLE, 3.3)); gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.3, 1.0], wspace=0.45)
    ax = fig.add_subplot(gs[0]); parts = [("deep_min", L("深睡", "Deep"), C_MAGENTA), ("rem_min", "REM", C_CORAL), ("light_min", L("浅睡", "Light"), C_SLATE), ("awake_min", L("清醒", "Awake"), C_LIGHT)]; pos = 0; ticks, labs = [], []
    for g in ("Home", "Travel"):
        for lab, sel in ((L("1–3 晚", "Nights 1–3"), s["night"] <= 3), (L("4–14 晚", "Nights 4–14"), s["night"] > 3)):
            b = 0
            for c, nm, cl in parts:
                v = s[(s["group"] == g) & sel][c].mean(); ax.bar(pos, v, bottom=b, color=cl, width=0.7, lw=0); ax.text(pos, b + v / 2, f"{v:.0f}", ha="center", va="center", fontsize=5.4, color="white" if cl != C_LIGHT else C_INK) if v > 25 else None; b += v
            ticks.append(pos); labs.append(lab.replace(" ", "\n", 1)); pos += 0.85
        pos += 0.4
    ax.set_xticks(ticks); ax.set_xticklabels(labs, fontsize=5.4); ax.tick_params(axis="x", length=0); ax.set_ylabel(L("平均时长 (min)", "Mean duration (min)")); ax.set_ylim(0, 640)
    for xc, g in ((np.mean(ticks[:2]), "Home"), (np.mean(ticks[2:]), "Travel")):
        ax.text(xc, -0.2, gn[g], transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=6.3, color=gc[gn[g]], fontweight="bold")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in parts], labels=[p[1] for p in parts], loc="upper center", bbox_to_anchor=(0.5, 1.14), ncol=4, fontsize=5.3, handlelength=0.8, columnspacing=0.6)
    panel_letter(ax, "a", dx=-0.22, dy=1.1)
    ax = fig.add_subplot(gs[1]); ser = {}
    for g, v in gn.items():
        w = s[s["group"] == g].pivot(index="id", columns="night", values="total"); ser[v] = (w.mean().values, w.std().values / np.sqrt(len(w)))
    ax_bands(ax, np.arange(1, 15), ser, gc, dashed=[gn["Home"]]); ax.set_xlabel(L("夜序", "Night")); ax.set_ylabel(L("总睡眠时间 (min)", "Total sleep time (min)")); ax.legend(loc="lower right", fontsize=6); ax.set_xticks([1, 3, 5, 7, 9, 11, 13]); panel_letter(ax, "b", dx=-0.17)
    ax = fig.add_subplot(gs[2]); dm = st.groupby(["id", "group"])["steps"].mean().reset_index(); ax_raincloud(ax, {gn[g]: dm[dm["group"] == g]["steps"].values for g in gn}, gc, L("日均步数", "Mean daily steps")); panel_letter(ax, "c", dx=-0.3)
    save(fig, d, "fig1_sleep_steps", lang)


# ============================================================================ D21
MARKERS = ["CK", "LDH", "Myoglobin", "IL-6", "TNF-α", "IL-10", "CRP", "Cortisol", "Testosterone", "GH", "Irisin", "BDNF"]
RESP = {"CK": (3.2, 48), "LDH": (1.6, 36), "Myoglobin": (4.0, 12), "IL-6": (6.0, 2), "TNF-α": (1.4, 12), "IL-10": (2.2, 4), "CRP": (1.3, 30), "Cortisol": (1.7, 2), "Testosterone": (0.75, 2), "GH": (8.0, 0), "Irisin": (1.5, 2), "BDNF": (1.4, 2)}


def sim_d21(seed=21):
    rng = np.random.default_rng(seed); rows = []
    times = {"Pre": 0, "0h": 0, "2h": 2, "24h": 24, "48h": 48}
    for i in range(40):
        grp = "Intervention" if i < 20 else "Control"
        for m in MARKERS:
            base = rng.lognormal(np.log(10), 0.35); peak, tp = RESP[m]
            for tn, th in times.items():
                if tn == "Pre":
                    fc = 1.0
                else:
                    pk = peak if grp == "Control" else 1 + (peak - 1) * 0.65
                    t_peak = max(tp, 0.1); fc = 1 + (pk - 1) * np.exp(-0.5 * ((np.log1p(th) - np.log1p(t_peak)) / 0.9) ** 2)
                rows.append((f"B{i + 1:03d}", grp, m, tn, round(base * fc * rng.lognormal(0, 0.18), 3)))
    pd.DataFrame(rows, columns=["id", "group", "marker", "time", "value"]).to_csv(ddir("D21_生物标志物_时间过程")/"biomarkers.csv", index=False)
    write_readme("D21_生物标志物_时间过程", "运动后 12 种血液标志物（5 个时点）", "12 blood markers after exercise (5 time points)", "40 人；对数正态。干预组应答幅度较小。", {"biomarkers.csv": ("长表", "Long format", {"marker": ("标志物", "Marker"), "time": ("时点 Pre/0h/2h/24h/48h", "Time point"), "value": ("浓度（任意单位）", "Concentration (arbitrary units)")})})


def fig_d21(lang):
    d = "D21_生物标志物_时间过程"; df = read(d, "biomarkers.csv"); tl = ["Pre", "0h", "2h", "24h", "48h"]
    gn = {"Control": L("对照", "Control"), "Intervention": L("干预", "Intervention")}; gc = {gn["Control"]: C_AMBER, gn["Intervention"]: C_MAGENTA}
    fig = plt.figure(figsize=(DOUBLE, 5.0)); gs = fig.add_gridspec(2, 6, height_ratios=[1, 1.15], hspace=0.62, wspace=1.6)
    for j, mk in enumerate(["CK", "IL-6", "Cortisol"]):
        ax = fig.add_subplot(gs[0, 2 * j:2 * j + 2]); ser = {}
        for g, v in gn.items():
            w = df[(df["marker"] == mk) & (df["group"] == g)].pivot(index="id", columns="time", values="value")[tl]; lg = np.log(w.div(w["Pre"], axis=0)); m, se = lg.mean().values, lg.std().values / np.sqrt(len(w)); tc = 2.09
            ser[v] = (np.exp(m), np.exp(m - tc * se), np.exp(m + tc * se))
        ax_timepoints(ax, tl, ser, gc, dodge=0.1, log=True, ylabel=L("相对运动前倍数（几何均值）", "Fold change vs pre (geometric mean)") if j == 0 else ""); ax.axhline(1, color=C_GREY, lw=0.5, ls=":")
        ax.set_title(mk, fontsize=7, loc="left", pad=3); ax.minorticks_off(); tk = [t_ for t_ in (0.5, 1, 2, 4, 8, 16) if ax.get_ylim()[0] * 0.8 <= t_ <= ax.get_ylim()[1] * 1.2]; ax.set_yticks(tk); ax.set_yticklabels([f"{t_:g}" for t_ in tk])
        if j == 0:
            ax.legend(loc="upper right", fontsize=5.8)
        panel_letter(ax, "abc"[j], dx=-0.28, dy=1.1)
    mats = {}
    for g in gn:
        m = np.array([[np.log2(df[(df["marker"] == mk) & (df["group"] == g) & (df["time"] == t_)]["value"].mean() / df[(df["marker"] == mk) & (df["group"] == g) & (df["time"] == "Pre")]["value"].mean()) for t_ in tl[1:]] for mk in MARKERS]); mats[g] = m
    vmax = 3.0; order = None
    for k, g in enumerate(gn):
        ax = fig.add_subplot(gs[1, 3 * k:3 * k + 3])
        im, o = ax_heatmap(ax, mats[g] if order is None else mats[g][order], MARKERS if order is None else [MARKERS[i] for i in order], tl[1:], cmap=DIVERGING, vmin=-vmax, vmax=vmax, cluster_rows=(order is None), annotate=True, fmt="{:.1f}")
        if order is None:
            order = o
        ax.set_title(gn[g], fontsize=7, loc="left", pad=3, color=gc[gn[g]], fontweight="bold")
        if k == 0:
            panel_letter(ax, "d", dx=-0.3, dy=1.1)
    cb = fig.colorbar(im, ax=fig.axes[-2:], fraction=0.03, pad=0.02); cb.set_label("log₂ FC", fontsize=6); cb.ax.tick_params(labelsize=5)
    save(fig, d, "fig1_biomarkers", lang)


# ============================================================================ D22
def sim_d22(seed=22):
    rng = np.random.default_rng(seed); P, n = 600, 30; g = np.array([0] * 15 + [1] * 15)
    eff = np.zeros(P); idx = rng.choice(P, 70, replace=False); eff[idx] = rng.choice([-1, 1], 70) * rng.uniform(0.6, 1.8, 70)
    X = rng.normal(0, 1, (n, P)) * rng.uniform(0.4, 0.9, P) + np.outer(g, eff) + rng.normal(0, 0.5, (n, 1))
    names = [f"PROT{k:03d}" for k in range(1, P + 1)]
    names[:12] = ["IL6", "CKM", "MYH7", "TTN", "PGC1A", "FNDC5", "BDNF", "CXCL10", "SPP1", "COL1A1", "LDHA", "SOD2"]
    t = [stats.ttest_ind(X[g == 1, k], X[g == 0, k]) for k in range(P)]
    p = np.array([a.pvalue for a in t]); lfc = X[g == 1].mean(0) - X[g == 0].mean(0)
    o = np.argsort(p); q = np.empty(P); prev = 1.0
    for rank in range(P - 1, -1, -1):
        i = o[rank]; prev = min(prev, p[i] * P / (rank + 1)); q[i] = prev
    d = ddir("D22_组学_火山图")
    pd.DataFrame({"feature": names, "log2fc": lfc.round(3), "pvalue": p, "qvalue": q}).to_csv(d / "differential.csv", index=False)
    pd.DataFrame(X.round(3), columns=names).assign(sample=[f"M{i + 1:02d}" for i in range(n)], group=np.where(g == 1, "Intervention", "Control")).to_csv(d / "expression.csv", index=False)
    write_readme("D22_组学_火山图", "蛋白质组/肌因子差异表达（火山图、热图、PCA）", "Proteomics / myokine differential expression (volcano, heat map, PCA)", "30 个样本 × 600 个特征（log2 强度）；其中 70 个真实差异。", {"differential.csv": ("每个特征的 log2FC、P、BH q", "log2FC, P and BH q per feature", {}), "expression.csv": ("表达矩阵（样本 × 特征）", "Expression matrix", {})})


def fig_d22(lang):
    d = "D22_组学_火山图"; de = read(d, "differential.csv"); ex = read(d, "expression.csv"); gcol = ex["group"].values; X = ex.drop(columns=["sample", "group"])
    gn = {"Control": L("对照", "Control"), "Intervention": L("干预", "Intervention")}; gc = {"Control": C_AMBER, "Intervention": C_MAGENTA}
    fig = plt.figure(figsize=(DOUBLE, 3.4)); gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 1.1, 1.0], wspace=0.5)
    ax = fig.add_subplot(gs[0]); up, dn = ax_volcano(ax, de["log2fc"].values, de["pvalue"].values, de["feature"].tolist(), fc_thr=0.5, p_thr=0.05, n_label=7, q=de["qvalue"].values)
    ax.text(0.98, 0.97, f"{L('上调', 'Up')} {up} · {L('下调', 'Down')} {dn}\n(q<0.05, |log₂FC|≥0.5)", transform=ax.transAxes, fontsize=5.6, va="top", ha="right", color=C_GREY); panel_letter(ax, "a", dx=-0.2)
    ax = fig.add_subplot(gs[1]); top = de.sort_values("pvalue").head(25)["feature"].tolist(); M = X[top].values.T; Z = (M - M.mean(1, keepdims=True)) / M.std(1, keepdims=True)
    srt = np.argsort(gcol, kind="stable"); im, order = ax_heatmap(ax, Z[:, srt], top, [""] * len(srt), cmap=DIVERGING, vmin=-2.5, vmax=2.5, cluster_rows=True, col_colors=[gc[g] for g in gcol[srt]])
    ax.set_xticks([]); ax.tick_params(axis="y", labelsize=5.2); ax.set_xlabel(L("样本", "Samples"), labelpad=2)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03); cb.set_label("z", fontsize=6); cb.ax.tick_params(labelsize=5); panel_letter(ax, "b", dx=-0.4, dy=1.08)
    ax = fig.add_subplot(gs[2]); A = X.values - X.values.mean(0); U, S, Vt = np.linalg.svd(A, full_matrices=False); pc = U[:, :2] * S[:2]; ve = S ** 2 / (S ** 2).sum() * 100
    for g, v in gn.items():
        m = gcol == g; ax_ellipse(ax, pc[m, 0], pc[m, 1], gc[g], scatter=True, label=v, s=14)
    ax.set_xlabel(f"PC1 ({ve[0]:.1f}%)"); ax.set_ylabel(f"PC2 ({ve[1]:.1f}%)"); ax.legend(loc="best", fontsize=6); ax.axhline(0, color=C_LIGHT, lw=0.5); ax.axvline(0, color=C_LIGHT, lw=0.5); panel_letter(ax, "c", dx=-0.25)
    save(fig, d, "fig1_omics", lang)


# ============================================================================ D23
def sim_d23(seed=23):
    rng = np.random.default_rng(seed); d = ddir("D23_研究时间线_周期化")
    sched = [("Screening", -4, -3.2, "visit"), ("Familiarisation", -3, -2.2, "visit"), ("Baseline testing", -1.2, -0.2, "test"), ("Intervention (12 weeks)", 0, 12, "train"), ("Mid-point testing", 6, 6.6, "test"), ("Post testing", 12.2, 13, "test"), ("Follow-up", 20, 20.6, "test")]
    pd.DataFrame(sched, columns=["task", "start_week", "end_week", "type"]).to_csv(d / "study_schedule.csv", index=False)
    rows = []
    for w in range(1, 17):
        phase = "Accumulation" if w <= 6 else "Intensification" if w <= 12 else "Taper"
        vol = {"Accumulation": 14 + 0.9 * w, "Intensification": 18 - 0.4 * (w - 6), "Taper": 13 - 2.2 * (w - 12)}[phase]; inten = {"Accumulation": 62 + 1.2 * w, "Intensification": 70 + 2.0 * (w - 6), "Taper": 82 - 3.0 * (w - 12)}[phase]
        rows.append((w, phase, round(vol + rng.normal(0, 0.4), 1), round(inten + rng.normal(0, 0.8), 1), 4 if w % 4 == 0 else 0))
    pd.DataFrame(rows, columns=["week", "phase", "volume_sets", "intensity_pct_1rm", "deload"]).to_csv(d / "periodisation.csv", index=False)
    write_readme("D23_研究时间线_周期化", "研究时间线与训练周期化", "Study timeline and training periodisation", "研究流程甘特图；16 周周期化计划。", {"study_schedule.csv": ("研究流程", "Study schedule", {}), "periodisation.csv": ("周期化计划", "Periodisation plan", {})})


def fig_d23(lang):
    d = "D23_研究时间线_周期化"; sc = read(d, "study_schedule.csv"); pl = read(d, "periodisation.csv")
    tcol = {"visit": C_LIGHT, "test": C_SLATE, "train": C_MAGENTA}
    nm = {"Screening": L("筛查", "Screening"), "Familiarisation": L("熟悉期", "Familiarisation"), "Baseline testing": L("基线测试", "Baseline testing"), "Intervention (12 weeks)": L("干预（12 周）", "Intervention (12 weeks)"),
          "Mid-point testing": L("中期测试", "Mid-point testing"), "Post testing": L("干预后测试", "Post testing"), "Follow-up": L("随访", "Follow-up")}
    fig = plt.figure(figsize=(DOUBLE, 4.6)); gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.15], width_ratios=[1, 1], hspace=0.55, wspace=0.3)
    ax = fig.add_subplot(gs[0, :]); tasks = [(nm[r.task], r.start_week, r.end_week, tcol[r.type]) for r in sc.itertuples()]
    ax_gantt(ax, tasks, milestones=[(0, L("随机化", "Randomisation")), (12, L("干预结束", "End of intervention"))], xlabel=L("相对干预开始的周数", "Weeks relative to start of intervention")); ax.set_xlim(-8, 22)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in tcol.values()], labels=[L("访视", "Visit"), L("测试", "Testing"), L("训练", "Training")], loc="upper right", bbox_to_anchor=(1.0, 0.82), fontsize=6, ncol=1); panel_letter(ax, "a", dx=-0.04, dy=1.1)
    pc = {"Accumulation": C_SLATE, "Intensification": C_MAGENTA, "Taper": C_AMBER}; pn = {"Accumulation": L("积累期", "Accumulation"), "Intensification": L("强化期", "Intensification"), "Taper": L("减量期", "Taper")}
    ax = fig.add_subplot(gs[1, 0]); ax.bar(pl["week"], pl["volume_sets"], color=[pc[p] for p in pl["phase"]], width=0.74, lw=0)
    for w in pl[pl["deload"] > 0]["week"]: ax.plot(w, pl[pl["week"] == w]["volume_sets"].iloc[0] + 0.9, marker="v", color=C_INK, ms=3.5)
    ax.set_xticks([1, 4, 8, 12, 16]); ax.set_xlabel(L("周", "Week")); ax.set_ylabel(L("每周训练组数", "Weekly sets")); ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=pc[k]) for k in pc], labels=[pn[k] for k in pc], loc="upper center", bbox_to_anchor=(0.5, 1.2), ncol=3, fontsize=5.5, handlelength=0.9)
    ax.text(0.99, 0.03, L("▼ 减负荷周", "▼ deload week"), transform=ax.transAxes, fontsize=5.4, color=C_GREY, ha="right"); panel_letter(ax, "b", dx=-0.17, dy=1.1)
    ax = fig.add_subplot(gs[1, 1]); ax.plot(pl["week"], pl["intensity_pct_1rm"], color=C_INK, lw=1.2, zorder=1)
    ax.scatter(pl["week"], pl["intensity_pct_1rm"], s=22, c=[pc[p] for p in pl["phase"]], zorder=3, edgecolors="white", linewidths=0.6)
    ax.set_xticks([1, 4, 8, 12, 16]); ax.set_xlabel(L("周", "Week")); ax.set_ylabel(L("相对强度 (% 1RM)", "Relative intensity (% 1RM)")); hair_y(ax); panel_letter(ax, "c", dx=-0.2, dy=1.1)
    save(fig, d, "fig1_timeline_periodisation", lang)


DOMAINS = [("D20_睡眠_可穿戴", sim_d20, fig_d20), ("D21_生物标志物_时间过程", sim_d21, fig_d21), ("D22_组学_火山图", sim_d22, fig_d22), ("D23_研究时间线_周期化", sim_d23, fig_d23)]
