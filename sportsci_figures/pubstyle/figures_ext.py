"""
pubstyle.figures_ext — figure blocks for the data types beyond time-courses and two-arm trials.

Distributions & agreement : ax_raincloud, ax_bland_altman, ax_identity (+ icc_2_1)
Questionnaires            : ax_likert, ax_corr_heatmap, ax_mediation, ax_radar
Repeated measures         : ax_timepoints, ax_multitime
Survival / diagnostics    : km_estimate, ax_km, at_risk_table, roc_points, auc_ci, ax_roc, ax_calibration
Evidence synthesis        : meta_random_effects, fig_meta_forest, ax_funnel
Curve fitting             : fit_band, ax_fit_band
Omics-style               : ax_volcano, ax_heatmap
Sport-science specific    : ax_waterfall (responders), ax_spm, ax_ellipse (COP), pitch_outline, ax_pitch_heat, ax_gantt
Helpers                   : paired_ci, mean_se_curves, category_colors

Same contract as figures.py: draw only on the ``ax`` you pass, take every text string from the caller or from
``style.tr(zh, en)`` so both language sets work, take colours from style.py, never invent data.
All names are re-exported from ``pubstyle.figures`` (``pf.ax_raincloud`` ...).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Ellipse, FancyBboxPatch, Polygon, Rectangle
from scipy import stats

from .style import (C_AMBER, C_BAND, C_CORAL, C_GOLD_DARK, C_GREY, C_HAIR, C_INK, C_LIGHT, C_MAGENTA, C_MID, C_PALE_CONTRAST, C_PALE_SLATE, C_SLATE, C_TEAL,
                    DIVERGING_CMAP, SEQ_CMAP, _P, fmt_p, hair_y, tr as L, wrap_label)

CAT = [C_MAGENTA, C_AMBER, C_CORAL, C_SLATE, C_TEAL, _P["blue"], _P["violet"], _P["brown"]]


def category_colors(n: int) -> List[str]:
    """Qualitative colours for n unordered categories (primary first, then control, contrast, slate, teal ...)."""
    return [CAT[i % len(CAT)] for i in range(n)]


DIVERGING = DIVERGING_CMAP     # contrast <-> paper <-> primary
SEQ = SEQ_CMAP                 # paper -> navy


# ============================================================================ distributions
def ax_raincloud(ax, groups: Dict[str, np.ndarray], colors: Dict[str, str], ylabel: str = "", show_ci: bool = True, point_s: float = 6,
                 width: float = 0.36, horizontal: bool = False, seed: int = 3, paired_lines: Optional[pd.DataFrame] = None) -> None:
    """Half violin (density) + jittered raw points + IQR box + mean ± 95% CI. Use for n up to a few hundred.

    paired_lines: optional DataFrame (rows = subjects, columns = group names) to join each subject's points.
    """
    rng = np.random.default_rng(seed)
    names = list(groups)
    for i, g in enumerate(names):
        v = np.asarray(groups[g], float)
        v = v[np.isfinite(v)]
        c = colors[g]
        if len(v) > 3 and np.ptp(v) > 0:
            kde = stats.gaussian_kde(v)
            bw = kde.factor * v.std(ddof=1)
            yy = np.linspace(v.min() - 1.5 * bw, v.max() + 1.5 * bw, 240)   # tails taper smoothly instead of a flat cut
            d = kde(yy)
            d = d / d.max() * width
            keep = d > 0.012 * width
            yy, d = yy[keep], d[keep]
            if horizontal:
                ax.fill_between(yy, i, i + d, color=c, alpha=0.22, lw=0)
                ax.plot(yy, i + d, color=c, lw=0.7, alpha=0.9)
            else:
                ax.fill_betweenx(yy, i + 0.07, i + 0.07 + d, color=c, alpha=0.22, lw=0)
                ax.plot(i + 0.07 + d, yy, color=c, lw=0.7, alpha=0.9)
        jx = rng.uniform(-0.17, -0.05, len(v))
        if horizontal:
            ax.scatter(v, i - jx - 0.1, s=point_s, color=c, alpha=0.6, lw=0, zorder=3)
        else:
            ax.scatter(i + jx, v, s=point_s, color=c, alpha=0.6, lw=0, zorder=3)
        q1, med, q3 = np.percentile(v, [25, 50, 75])
        if horizontal:
            ax.plot([q1, q3], [i, i], color=C_GREY, lw=0.9, solid_capstyle="butt", zorder=4)
            ax.plot([med], [i], "|", color=C_GREY, ms=5, mew=1.0, zorder=5)
        else:
            ax.plot([i + 0.0, i + 0.0], [q1, q3], color=C_GREY, lw=0.9, solid_capstyle="butt", zorder=4)
            ax.plot([i - 0.035, i + 0.035], [med, med], color=C_GREY, lw=1.0, zorder=5)
        if show_ci and len(v) > 2:
            m, se = v.mean(), v.std(ddof=1) / np.sqrt(len(v))
            tc = stats.t.ppf(0.975, len(v) - 1)
            if not horizontal:
                ax.plot([i + 0.02, i + 0.02], [m - tc * se, m + tc * se], color=c, lw=2.0, solid_capstyle="round", zorder=6)
                ax.plot(i + 0.02, m, "D", ms=4.4, color=c, mec="white", mew=0.7, zorder=7)
    if paired_lines is not None:
        for _, r in paired_lines[names].dropna().iterrows():
            ax.plot(range(len(names)), [r[g] for g in names], color=C_LIGHT, lw=0.35, alpha=0.7, zorder=1)
    if horizontal:
        ax.set_yticks(range(len(names))); ax.set_yticklabels(names); ax.set_xlabel(ylabel)
    else:
        ax.set_xticks(range(len(names))); ax.set_xticklabels([wrap_label(n) for n in names]); ax.set_ylabel(ylabel); ax.tick_params(axis="x", length=0)
    hair_y(ax)


# ============================================================================ agreement / reliability
def icc_2_1(a: np.ndarray, b: np.ndarray) -> float:
    """ICC(2,1): two-way random, absolute agreement, single measurement."""
    X = np.c_[a, b]
    n, k = X.shape
    gm = X.mean()
    msr = k * ((X.mean(1) - gm) ** 2).sum() / (n - 1)
    msc = n * ((X.mean(0) - gm) ** 2).sum() / (k - 1)
    sse = ((X - X.mean(1, keepdims=True) - X.mean(0, keepdims=True) + gm) ** 2).sum()
    mse = sse / ((n - 1) * (k - 1))
    return (msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n)


def ax_bland_altman(ax, a, b, xlabel: str, ylabel: str, unit: str = "", pct: bool = False) -> Tuple[float, float, float]:
    """Mean of methods (x) vs difference (y); bias line and 95% limits of agreement with 95% CI shading."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    m = (a + b) / 2
    d = (a - b) / m * 100 if pct else a - b
    bias, sd, n = d.mean(), d.std(ddof=1), len(d)
    lo, hi = bias - 1.96 * sd, bias + 1.96 * sd
    se_loa = sd * np.sqrt(1 / n + 1.96 ** 2 / (2 * (n - 1)))
    tc = stats.t.ppf(0.975, n - 1)
    ax.axhspan(hi - tc * se_loa, hi + tc * se_loa, color=C_AMBER, alpha=0.15, lw=0)
    ax.axhspan(lo - tc * se_loa, lo + tc * se_loa, color=C_AMBER, alpha=0.15, lw=0)
    ax.axhline(bias, color=C_MAGENTA, lw=1.3)
    ax.axhline(hi, color=C_AMBER, lw=1, ls=(0, (3, 2)))
    ax.axhline(lo, color=C_AMBER, lw=1, ls=(0, (3, 2)))
    ax.scatter(m, d, s=9, color=C_SLATE, alpha=0.7, lw=0, zorder=3)
    x0_, x1_ = ax.get_xlim(); ax.set_xlim(x0_, x1_ + 0.32 * (x1_ - x0_))      # room for the line labels
    x1 = ax.get_xlim()[1]
    u = "%" if pct else unit
    ax.text(x1, hi, f"+1.96 SD {hi:.2f}{u}", fontsize=5.5, color=C_GOLD_DARK, ha="right", va="bottom")
    ax.text(x1, lo, f"−1.96 SD {lo:.2f}{u}", fontsize=5.5, color=C_GOLD_DARK, ha="right", va="top")
    ax.text(x1, bias, f"{L('偏倚', 'Bias')} {bias:.2f}{u}", fontsize=5.5, color=C_MAGENTA, ha="right", va="bottom")
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    return bias, lo, hi


def ax_identity(ax, x, y, xlabel: str, ylabel: str, color: str = C_MAGENTA) -> Tuple[float, float]:
    """Scatter with the line of identity (dashed), OLS line, ICC(2,1) and Pearson r."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    lim = [min(x.min(), y.min()), max(x.max(), y.max())]
    pad = 0.04 * (lim[1] - lim[0])
    lim = [lim[0] - pad, lim[1] + pad]
    ax.plot(lim, lim, color=C_GREY, lw=0.9, ls=(0, (3, 2)), zorder=1)
    sl, ic, r, p, _ = stats.linregress(x, y)
    ax.plot(lim, [ic + sl * lim[0], ic + sl * lim[1]], color=color, lw=1.4, zorder=2)
    ax.scatter(x, y, s=12, color=color, alpha=0.65, edgecolors="white", linewidths=0.4, zorder=3)
    icc = icc_2_1(x, y)
    ax.text(0.04, 0.96, f"ICC(2,1) = {icc:.2f}\nr = {r:.2f}, n = {len(x)}", transform=ax.transAxes, va="top", fontsize=6)
    ax.set_xlim(lim); ax.set_ylim(lim); ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    return icc, r


# ============================================================================ questionnaires
LIKERT5 = [C_CORAL, C_PALE_CONTRAST, C_HAIR, C_PALE_SLATE, C_SLATE]


def ax_likert(ax, items: Sequence[str], pct: np.ndarray, level_labels: Sequence[str], colors: Optional[Sequence[str]] = None, xlabel: str = "",
              show_legend: bool = True) -> None:
    """Diverging stacked bars. pct: items × levels (rows sum to 100). Neutral level (odd count) is centred."""
    pct = np.asarray(pct, float)
    k = pct.shape[1]
    colors = list(colors) if colors is not None else (LIKERT5 if k == 5 else [plt.cm.PuOr(0.1 + 0.8 * i / (k - 1)) for i in range(k)])
    mid = k // 2
    for i in range(len(items)):
        left = -(pct[i, :mid].sum() + (pct[i, mid] / 2 if k % 2 else 0))
        for j in range(k):
            ax.barh(i, pct[i, j], left=left, color=colors[j], height=0.68, lw=0)
            if pct[i, j] >= 9:
                ax.text(left + pct[i, j] / 2, i, f"{pct[i, j]:.0f}", ha="center", va="center", fontsize=5.3, color=C_INK)
            left += pct[i, j]
    ax.axvline(0, color=C_INK, lw=0.7)
    ax.set_yticks(range(len(items))); ax.set_yticklabels(items); ax.invert_yaxis()
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel(xlabel)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{abs(v):.0f}"))
    ax.spines["left"].set_visible(False)
    if show_legend:
        ax.legend(handles=[Rectangle((0, 0), 1, 1, color=c) for c in colors], labels=list(level_labels), ncol=k, loc="upper center", bbox_to_anchor=(0.5, 1.16),
                  fontsize=5.3, handlelength=0.9, columnspacing=0.7)


def ax_corr_heatmap(ax, corr: np.ndarray, labels: Sequence[str], pvals: Optional[np.ndarray] = None, fmt: str = "{:.2f}") -> object:
    """Lower-triangle correlation matrix in the contrast↔primary diverging scale; bold = P < 0.05 (if pvals given)."""
    n = len(labels)
    mask = np.triu(np.ones_like(corr, bool), 1)
    m = np.ma.array(corr, mask=mask)
    im = ax.imshow(m, cmap=DIVERGING, vmin=-1, vmax=1)
    for i in range(n):
        for j in range(i + 1):
            sig = pvals is not None and pvals[i, j] < 0.05 and i != j
            ax.text(j, i, fmt.format(corr[i, j]), ha="center", va="center", fontsize=5.4, fontweight="bold" if sig else "normal",
                    color="white" if abs(corr[i, j]) > 0.65 else C_INK)
    ax.set_xticks(range(n)); ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticks(range(n)); ax.set_yticklabels(labels)
    ax.tick_params(length=0)
    for s in ("left", "bottom"):
        ax.spines[s].set_visible(False)
    return im


def ax_mediation(ax, names: Tuple[str, str, str], a: str, b: str, c: str, cp: str, indirect: str) -> None:
    """Path diagram X → M → Y with coefficient labels (strings already formatted with CI / P)."""
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    X, M, Y = (0.17, 0.30), (0.50, 0.80), (0.83, 0.30)
    for (x, y), nm, col in ((X, names[0], C_AMBER), (M, names[1], C_SLATE), (Y, names[2], C_MAGENTA)):
        ax.add_patch(FancyBboxPatch((x - 0.15, y - 0.09), 0.30, 0.18, boxstyle="round,pad=0.005,rounding_size=0.02", lw=1.0, ec=col, fc=col, alpha=0.18, zorder=1))
        ax.text(x, y, nm, ha="center", va="center", fontsize=6.3, zorder=3)
    arr = dict(arrowstyle="-|>", color=C_GREY, lw=1.0, shrinkA=0, shrinkB=0)
    ax.annotate("", xy=(0.43, 0.71), xytext=(0.23, 0.39), arrowprops=arr)
    ax.annotate("", xy=(0.77, 0.39), xytext=(0.57, 0.71), arrowprops=arr)
    ax.annotate("", xy=(0.68, 0.30), xytext=(0.32, 0.30), arrowprops=arr)
    ax.text(0.15, 0.62, f"a = {a}", fontsize=5.8, ha="center", va="center")
    ax.text(0.85, 0.62, f"b = {b}", fontsize=5.8, ha="center", va="center")
    ax.text(0.50, 0.19, f"c′ = {cp}", fontsize=5.8, ha="center", va="top")
    ax.text(0.50, 0.05, f"c = {c}   |   {L('间接效应', 'Indirect effect')} = {indirect}", fontsize=5.8, ha="center", va="top", color=C_MAGENTA)


def ax_radar(ax, cats: Sequence[str], series: Dict[str, Sequence[float]], colors: Dict[str, str], rmax: float, rmin: float = 0, ring_step: Optional[float] = None) -> None:
    """ax must be a polar axes (fig.add_subplot(..., projection='polar'))."""
    k = len(cats)
    ang = np.linspace(0, 2 * np.pi, k, endpoint=False)
    ax.set_theta_offset(np.pi / 2); ax.set_theta_direction(-1)
    for name, vals in series.items():
        v = list(vals) + [vals[0]]
        ax.plot(list(ang) + [ang[0]], v, color=colors[name], lw=1.5, label=name)
        ax.fill(list(ang) + [ang[0]], v, color=colors[name], alpha=0.14)
    ax.set_ylim(rmin, rmax)
    ax.set_xticks(ang); ax.set_xticklabels(cats, fontsize=6)
    if ring_step:
        ax.set_yticks(np.arange(rmin + ring_step, rmax + 1e-9, ring_step))
    ax.tick_params(axis="y", labelsize=5, colors=C_GREY)
    ax.grid(color=C_HAIR, lw=0.6)
    ax.spines["polar"].set_visible(False)


# ============================================================================ multi-time / categorical-time
def ax_timepoints(ax, x_labels: Sequence[str], series: Dict[str, Tuple[Sequence[float], Sequence[float], Sequence[float]]], colors: Dict[str, str], dodge: float = 0.07,
                  log: bool = False, dashed: Sequence[str] = (), ylabel: str = "") -> None:
    """Point-range lines across categorical time points. series: name → (est, lo, hi)."""
    k = len(series)
    xs = np.arange(len(x_labels))
    for i, (name, (m, lo, hi)) in enumerate(series.items()):
        off = (i - (k - 1) / 2) * dodge
        m, lo, hi = np.asarray(m, float), np.asarray(lo, float), np.asarray(hi, float)
        ax.errorbar(xs + off, m, yerr=[m - lo, hi - m], fmt="o", ms=4.5, lw=1.4, color=colors[name], mec="white", mew=0.7, ecolor=colors[name], elinewidth=1.1, capsize=2,
                    ls=(0, (3, 2)) if name in dashed else "-", label=name, zorder=3)
    ax.set_xticks(xs); ax.set_xticklabels(x_labels)
    if log:
        ax.set_yscale("log")
    ax.set_ylabel(ylabel)
    hair_y(ax)


def ax_multitime(ax, long_df: pd.DataFrame, id_col: str, group_col: str, time_col: str, y_col: str, groups: Sequence[str], colors: Dict[str, str],
                 times: Sequence, time_labels: Sequence[str], ylabel: str, dodge: float = 0.07, indiv_alpha: float = 0.12, band: bool = False,
                 dashed: Sequence[str] = (), direct_labels: Optional[Dict[str, str]] = None) -> Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Group mean ± 95% CI at each of several time points with faint individual trajectories.

    band=True draws the CI as a shaded ribbon (no whiskers); dashed: groups drawn with dashed mean lines (control);
    direct_labels: {group: text} written at the end of each mean line instead of a legend.
    """
    xs = np.arange(len(times))
    out = {}
    k = len(groups)
    for gi, g in enumerate(groups):
        sub = long_df[long_df[group_col] == g]
        w = sub.pivot_table(index=id_col, columns=time_col, values=y_col)[list(times)]
        for _, r in w.iterrows():
            ax.plot(xs, r.values, color=colors[g], alpha=indiv_alpha, lw=0.4, zorder=1)
        m = w.mean().values
        se = w.std(ddof=1).values / np.sqrt(w.count().values)
        tc = stats.t.ppf(0.975, w.count().values - 1)
        off = 0.0 if band else (gi - (k - 1) / 2) * dodge
        ls = (0, (4, 2)) if g in dashed else "-"
        if band:
            ax.fill_between(xs, m - tc * se, m + tc * se, color=colors[g], alpha=0.16, lw=0, zorder=3)
            ax.plot(xs, m, color=colors[g], lw=1.9, ls=ls, zorder=4, label=g)
            ax.plot(xs, m, "o", ms=4.8, color=colors[g], mec="white", mew=0.8, zorder=5)
        else:
            ax.errorbar(xs + off, m, yerr=tc * se, fmt="-o", ms=5, lw=1.7, color=colors[g], mec="white", mew=0.8, ecolor=colors[g], elinewidth=1.2, capsize=2.5, zorder=4, label=g)
        out[g] = (m, m - tc * se, m + tc * se)
    if direct_labels:
        _direct_end_labels(ax, [(direct_labels[g], out[g][0][-1], colors[g]) for g in groups if g in direct_labels], xs[-1])
    ax.set_xticks(xs); ax.set_xticklabels(time_labels); ax.set_ylabel(ylabel); ax.tick_params(axis="x", length=0)
    hair_y(ax)
    return out


def _direct_end_labels(ax, labels, x, min_gap_pt: float = 8.5) -> None:
    """Write line-end labels and push them apart vertically so they never overlap (at least ``min_gap_pt`` points)."""
    if not labels:
        return
    ax.figure.canvas.draw()
    to_pt = ax.transData.transform
    ys = sorted(((to_pt((x, y))[1] * 72 / ax.figure.dpi, i) for i, (_, y, _) in enumerate(labels)))
    placed = []
    for y, i in ys:
        y = max(y, placed[-1][0] + min_gap_pt) if placed else y
        placed.append((y, i))
    shift = (sum(p[0] for p in placed) - sum(y for y, _ in ys)) / len(placed)   # keep the group centred on the data
    for (y_new, i), (y_old, _) in zip(placed, ys):
        text, y_data, col = labels[i]
        ax.annotate(text, xy=(x, y_data), xytext=(6, y_new - shift - y_old), textcoords="offset points", fontsize=6.2, color=col, fontweight="bold", va="center")


# ============================================================================ survival / diagnostics / meta
def km_estimate(time: np.ndarray, event: np.ndarray) -> Dict[str, np.ndarray]:
    """Kaplan–Meier with Greenwood log–log 95% CI. Returns t, s, lo, hi, censor_t, censor_s."""
    time, event = np.asarray(time, float), np.asarray(event, int)
    ut = np.unique(time[event == 1])
    s, var_sum, ts, ss, lo, hi = 1.0, 0.0, [0.0], [1.0], [1.0], [1.0]
    for u in ut:
        n_at = (time >= u).sum()
        d = ((time == u) & (event == 1)).sum()
        s *= 1 - d / n_at
        var_sum += d / (n_at * (n_at - d)) if n_at > d else 0
        se = np.sqrt(var_sum) / abs(np.log(s)) if 0 < s < 1 else 0
        ci = (s ** np.exp(1.96 * se), s ** np.exp(-1.96 * se)) if 0 < s < 1 else (s, s)
        ts.append(u); ss.append(s); lo.append(ci[0]); hi.append(ci[1])
    cens = time[event == 0]
    cs = np.array([ss[max(np.searchsorted(ts, c, side="right") - 1, 0)] for c in cens])
    return dict(t=np.array(ts), s=np.array(ss), lo=np.array(lo), hi=np.array(hi), censor_t=cens, censor_s=cs)


def ax_km(ax, curves: Dict[str, Dict[str, np.ndarray]], colors: Dict[str, str], xlabel: str, ylabel: str, xmax: Optional[float] = None, ylim=(0.0, 1.02)) -> None:
    for name, c in curves.items():
        col = colors[name]
        ax.fill_between(c["t"], c["lo"], c["hi"], step="post", color=col, alpha=0.14, lw=0)
        ax.step(c["t"], c["s"], where="post", color=col, lw=1.6, label=name)
        ax.plot(c["censor_t"], c["censor_s"], "|", color=col, ms=4, mew=0.7, alpha=0.8)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); ax.set_ylim(*ylim)
    if xmax:
        ax.set_xlim(0, xmax)


def at_risk_table(ax, groups: Dict[str, Tuple[np.ndarray, np.ndarray]], colors: Dict[str, str], times: Sequence[float], xlabel: str = "") -> None:
    """Numbers at risk under a KM plot; groups: name → (time, event)."""
    ax.set_xlim(*ax.figure.axes[0].get_xlim()) if False else None
    ax.set_ylim(-0.6, len(groups) - 0.4)
    for i, (g, (tm, ev)) in enumerate(groups.items()):
        for u in times:
            ax.text(u, len(groups) - 1 - i, str((np.asarray(tm) >= u).sum()), ha="center", va="center", fontsize=6, color=colors[g])
    ax.set_yticks(range(len(groups))); ax.set_yticklabels(list(groups)[::-1])
    for lab, g in zip(ax.get_yticklabels(), list(groups)[::-1]):
        lab.set_color(colors[g])
    ax.tick_params(length=0); ax.set_xlabel(xlabel)
    for s in ("left", "bottom", "top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_xticks(times)


def roc_points(y: np.ndarray, score: np.ndarray):
    o = np.argsort(-score)
    y = y[o]
    tps = np.cumsum(y) / y.sum()
    fps = np.cumsum(1 - y) / (1 - y).sum()
    return np.r_[0, fps], np.r_[0, tps], score[o]


def auc_ci(y: np.ndarray, score: np.ndarray, n_boot: int = 400, seed: int = 0):
    fpr, tpr, _ = roc_points(y, score)
    auc = np.trapz(tpr, fpr)
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if y[i].sum() in (0, len(i)):
            continue
        f, tt, _ = roc_points(y[i], score[i])
        bs.append(np.trapz(tt, f))
    return auc, np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def ax_roc(ax, y: np.ndarray, scores: Dict[str, np.ndarray], colors: Dict[str, str], mark_youden: bool = True) -> Dict[str, Tuple[float, float, float]]:
    ax.plot([0, 1], [0, 1], color=C_GREY, lw=0.8, ls=(0, (3, 2)))
    res = {}
    for name, s in scores.items():
        fpr, tpr, thr = roc_points(y, s)
        auc, lo, hi = auc_ci(y, s)
        res[name] = (auc, lo, hi)
        ax.plot(fpr, tpr, color=colors[name], lw=1.6, label=f"{name}  AUC {auc:.2f} ({lo:.2f}–{hi:.2f})")
        if mark_youden:
            k = int(np.argmax(tpr - fpr))
            ax.plot(fpr[k], tpr[k], "o", color=colors[name], mec="white", mew=0.8, ms=5, zorder=4)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.0); ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(L("1 − 特异度", "1 − Specificity")); ax.set_ylabel(L("灵敏度", "Sensitivity"))
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), fontsize=5.6, handlelength=1.4)      # below the axes: never covers a curve
    return res


def ax_calibration(ax, pred: np.ndarray, obs: np.ndarray, color: str = C_MAGENTA, bins: int = 8) -> None:
    q = np.quantile(pred, np.linspace(0, 1, bins + 1))
    xs, ys, lo, hi = [], [], [], []
    for a, b in zip(q[:-1], q[1:]):
        m = (pred >= a) & (pred <= b)
        n, k = m.sum(), obs[m].sum()
        p = k / n
        z = 1.96
        den = 1 + z * z / n
        c = (p + z * z / (2 * n)) / den
        h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
        xs.append(pred[m].mean()); ys.append(p); lo.append(c - h); hi.append(c + h)
    ax.plot([0, 1], [0, 1], color=C_GREY, lw=0.8, ls=(0, (3, 2)))
    ax.errorbar(xs, ys, yerr=[np.array(ys) - np.array(lo), np.array(hi) - np.array(ys)], fmt="o-", color=color, ms=4.5, lw=1.3, mec="white", mew=0.7, ecolor=color, capsize=2)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(L("预测概率", "Predicted probability")); ax.set_ylabel(L("观察到的比例", "Observed proportion"))


def meta_random_effects(es: np.ndarray, se: np.ndarray) -> Dict[str, float]:
    """DerSimonian–Laird random-effects pooled estimate; also returns I², tau², Q p."""
    w = 1 / se ** 2
    fe = (w * es).sum() / w.sum()
    Q = (w * (es - fe) ** 2).sum()
    k = len(es)
    C = w.sum() - (w ** 2).sum() / w.sum()
    tau2 = max(0, (Q - (k - 1)) / C)
    wr = 1 / (se ** 2 + tau2)
    pooled = (wr * es).sum() / wr.sum()
    se_p = np.sqrt(1 / wr.sum())
    I2 = max(0, (Q - (k - 1)) / Q) * 100 if Q > 0 else 0
    return dict(est=pooled, se=se_p, lo=pooled - 1.96 * se_p, hi=pooled + 1.96 * se_p, I2=I2, tau2=tau2, Qp=1 - stats.chi2.cdf(Q, k - 1), w=wr / wr.sum() * 100)


def fig_meta_forest(df: pd.DataFrame, pooled: Dict[str, float], xlabel: str, left_header: str, right_header: str, width: float = 7.2, subgroup_col: Optional[str] = None,
                    sub_colors: Optional[Dict[str, str]] = None) -> plt.Figure:
    """df: columns study, es, lo, hi, w (weights %), optional subgroup. Square size ∝ weight; diamond = pooled."""
    k = len(df)
    fig, ax = plt.subplots(figsize=(width, 0.2 * k + 1.6))
    ys = np.arange(k, 0, -1)
    for y, (_, r) in zip(ys, df.iterrows()):
        c = (sub_colors or {}).get(r.get(subgroup_col), C_SLATE) if subgroup_col else C_SLATE
        ax.plot([r["lo"], r["hi"]], [y, y], color=c, lw=1.1)
        ax.scatter(r["es"], y, marker="s", s=14 + 2.2 * r["w"], color=c, zorder=3, lw=0)
        ax.text(-3.3, y, r["study"], fontsize=6.2, va="center")
        ax.text(2.0, y, f"{r['es']:.2f} ({r['lo']:.2f}, {r['hi']:.2f})", fontsize=5.8, va="center")
        ax.text(3.45, y, f"{r['w']:.1f}", fontsize=5.8, va="center", ha="right")
    yd = -0.9
    ax.add_patch(Polygon([[pooled["lo"], yd], [pooled["est"], yd + 0.45], [pooled["hi"], yd], [pooled["est"], yd - 0.45]], closed=True, fc=C_MAGENTA, ec="none"))
    ax.text(-3.3, yd, L("随机效应合计", "Random-effects pooled"), fontsize=6.2, fontweight="bold", va="center")
    ax.text(2.0, yd, f"{pooled['est']:.2f} ({pooled['lo']:.2f}, {pooled['hi']:.2f})", fontsize=5.8, va="center", fontweight="bold")
    ax.text(-3.3, yd - 1.0, f"I² = {pooled['I2']:.0f}%, τ² = {pooled['tau2']:.3f}, Q {fmt_p(pooled['Qp'])}", fontsize=5.5, color=C_GREY, va="center")
    ax.axvline(0, color=C_INK, lw=0.7)
    ax.text(-3.3, k + 0.9, left_header, fontsize=6.2, fontweight="bold"); ax.text(2.0, k + 0.9, right_header, fontsize=6.2, fontweight="bold"); ax.text(3.45, k + 0.9, "W%", fontsize=6.2, fontweight="bold", ha="right")
    ax.set_xlim(-3.4, 3.55); ax.set_ylim(yd - 1.6, k + 1.5)
    ax.set_yticks([]); ax.spines["left"].set_visible(False); ax.spines["bottom"].set_bounds(-1.5, 1.5)
    ax.set_xticks([-1.5, -1, -0.5, 0, 0.5, 1, 1.5]); ax.set_xlabel(xlabel)
    ax.xaxis.set_label_coords(0.5, -0.075 if k > 8 else -0.2)
    return fig


def ax_funnel(ax, es: np.ndarray, se: np.ndarray, pooled: float, color: str = C_SLATE) -> None:
    ymax = se.max() * 1.05
    ax.fill([pooled - 1.96 * ymax, pooled, pooled + 1.96 * ymax], [ymax, 0, ymax], color=C_BAND, zorder=0)
    ax.plot([pooled, pooled - 1.96 * ymax], [0, ymax], color=C_LIGHT, lw=0.7)
    ax.plot([pooled, pooled + 1.96 * ymax], [0, ymax], color=C_LIGHT, lw=0.7)
    ax.axvline(pooled, color=C_MAGENTA, lw=1)
    ax.scatter(es, se, s=16, color=color, alpha=0.8, edgecolors="white", linewidths=0.5, zorder=3)
    ax.set_ylim(ymax, 0)
    ax.set_xlabel(L("效应量 (SMD)", "Effect size (SMD)")); ax.set_ylabel(L("标准误", "Standard error"))


# ============================================================================ curve fitting / regression bands
def fit_band(x: np.ndarray, y: np.ndarray, kind: str = "quad", n_boot: int = 400, seed: int = 0, grid: int = 100):
    """Fit a curve and return grid, fit, lo, hi (bootstrap 95% band). kind: 'lin' | 'quad' | 'emax' (Emax: e0 + emax*x/(ed50+x))."""
    from scipy.optimize import curve_fit
    x, y = np.asarray(x, float), np.asarray(y, float)
    g = np.linspace(x.min(), x.max(), grid)

    def fitpred(xx, yy):
        if kind == "lin":
            return np.polyval(np.polyfit(xx, yy, 1), g)
        if kind == "quad":
            return np.polyval(np.polyfit(xx, yy, 2), g)
        f = lambda z, e0, em, ed: e0 + em * z / (ed + z)
        p, _ = curve_fit(f, xx, yy, p0=[yy.min(), np.ptp(yy), np.median(xx) + 1e-3], bounds=([-np.inf, -np.inf, 1e-3], [np.inf, np.inf, 1e3]), maxfev=5000)
        return f(g, *p)

    base = fitpred(x, y)
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(n_boot):
        i = rng.integers(0, len(x), len(x))
        try:
            bs.append(fitpred(x[i], y[i]))
        except Exception:
            pass
    bs = np.array(bs)
    return g, base, np.percentile(bs, 2.5, 0), np.percentile(bs, 97.5, 0)


def ax_fit_band(ax, g, fit, lo, hi, color: str = C_MAGENTA) -> None:
    ax.fill_between(g, lo, hi, color=color, alpha=0.15, lw=0)
    ax.plot(g, fit, color=color, lw=1.6)


# ============================================================================ omics-style
def ax_volcano(ax, log2fc: np.ndarray, p: np.ndarray, names: Sequence[str], fc_thr: float = 1.0, p_thr: float = 0.05, n_label: int = 8, q: Optional[np.ndarray] = None) -> Tuple[int, int]:
    """Volcano: x = log2 fold change, y = −log10 P. Up = primary, down = slate, n.s. = light grey. Top features labelled."""
    nlp = -np.log10(np.clip(p, 1e-300, 1))
    sig = (q if q is not None else p) < p_thr
    up = sig & (log2fc >= fc_thr)
    dn = sig & (log2fc <= -fc_thr)
    ns = ~(up | dn)
    ax.scatter(log2fc[ns], nlp[ns], s=5, color=C_LIGHT, lw=0, alpha=0.8)
    ax.scatter(log2fc[dn], nlp[dn], s=8, color=C_SLATE, lw=0, alpha=0.9)
    ax.scatter(log2fc[up], nlp[up], s=8, color=C_MAGENTA, lw=0, alpha=0.9)
    ax.axvline(fc_thr, color=C_GREY, lw=0.5, ls=":"); ax.axvline(-fc_thr, color=C_GREY, lw=0.5, ls=":")
    ax.axhline(-np.log10(p_thr), color=C_GREY, lw=0.5, ls=":")
    idx = np.argsort(-(nlp * np.abs(log2fc)))[:n_label]
    for i in idx:
        ax.annotate(names[i], (log2fc[i], nlp[i]), xytext=(3, 3), textcoords="offset points", fontsize=5.3, color=C_INK)
    ax.set_xlabel(L("log₂ 倍数变化", "log₂ fold change")); ax.set_ylabel("−log₁₀ P")
    return int(up.sum()), int(dn.sum())


def ax_heatmap(ax, mat: np.ndarray, row_labels: Sequence[str], col_labels: Sequence[str], cmap=DIVERGING, vmin: Optional[float] = None, vmax: Optional[float] = None,
               cluster_rows: bool = False, annotate: bool = False, fmt: str = "{:.1f}", col_colors: Optional[Sequence[str]] = None):
    """Plain heatmap with optional hierarchical row ordering and a coloured annotation strip above the columns."""
    mat = np.asarray(mat, float)
    order = np.arange(mat.shape[0])
    if cluster_rows:
        from scipy.cluster.hierarchy import leaves_list, linkage
        order = leaves_list(linkage(mat, "average"))
    m = mat[order]
    if vmin is None:
        vmax = np.nanmax(np.abs(m)) if vmax is None else vmax
        vmin = -vmax if isinstance(cmap, LinearSegmentedColormap) else np.nanmin(m)
    im = ax.imshow(m, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(col_labels))); ax.set_xticklabels(col_labels, rotation=45, ha="right")
    ax.set_yticks(range(len(row_labels))); ax.set_yticklabels([row_labels[i] for i in order])
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    if annotate:
        for i in range(m.shape[0]):
            for j in range(m.shape[1]):
                ax.text(j, i, fmt.format(m[i, j]), ha="center", va="center", fontsize=5, color="white" if abs(m[i, j]) > 0.6 * vmax else C_INK)
    if col_colors is not None:
        for j, c in enumerate(col_colors):
            ax.add_patch(Rectangle((j - 0.5, -1.4), 1, 0.7, color=c, clip_on=False, lw=0))
    return im, order


# ============================================================================ sport-science specific
def ax_waterfall(ax, changes: np.ndarray, swc: float, te: float, colors: Optional[Dict[str, str]] = None, unit_label: str = "") -> Dict[str, int]:
    """Sorted individual changes, SWC band, typical-error whiskers (±1.64 TE ≈ 90% CI). Classification by CI vs SWC."""
    colors = colors or dict(pos=C_MAGENTA, triv=C_SLATE, neg=C_CORAL)
    o = np.argsort(changes)[::-1]
    ch = np.asarray(changes)[o]
    ci = 1.645 * te
    cls = np.where(ch - ci > swc, "pos", np.where(ch + ci < -swc, "neg", "triv"))
    ax.axhspan(-swc, swc, color=C_BAND, zorder=0)
    ax.axhline(0, color=C_INK, lw=0.6)
    ax.bar(range(len(ch)), ch, color=[colors[c] for c in cls], width=0.78, lw=0, zorder=2)
    ax.errorbar(range(len(ch)), ch, yerr=ci, fmt="none", ecolor=C_INK, elinewidth=0.6, capsize=0, zorder=3, alpha=0.8)
    ax.set_xticks([]); ax.set_xlabel(L("受试者（按变化量排序）", "Participants (sorted by change)")); ax.set_ylabel(unit_label)
    ax.set_xlim(-0.8, len(ch) + 7)                                          # room on the right for the SWC labels
    ax.text(len(ch) - 0.2, swc, f"SWC +{swc:.1f}", fontsize=5.4, color=C_GREY, ha="left", va="bottom")
    ax.text(len(ch) - 0.2, -swc, f"SWC −{swc:.1f}", fontsize=5.4, color=C_GREY, ha="left", va="top")
    return {k: int((cls == k).sum()) for k in ("pos", "triv", "neg")}


def ax_spm(ax, x: np.ndarray, tcurve: np.ndarray, thr: float, label: str = "t", merge_gap: int = 3) -> List[Tuple[float, float]]:
    """Statistical-parametric-mapping style t-curve with threshold lines; supra-threshold clusters shaded.

    Clusters separated by <= merge_gap samples are merged (avoids a ragged pair of near-identical clusters).
    """
    ax.plot(x, tcurve, color=C_INK, lw=1.2)
    ax.axhline(thr, color=C_MAGENTA, lw=0.9, ls=(0, (3, 2))); ax.axhline(-thr, color=C_MAGENTA, lw=0.9, ls=(0, (3, 2)))
    ax.axhline(0, color=C_GREY, lw=0.5)
    sup = np.abs(tcurve) > thr
    idx = np.where(sup)[0]
    clusters: List[Tuple[float, float]] = []
    if len(idx):
        start = prev = idx[0]
        for i in idx[1:]:
            if i - prev > merge_gap + 1:
                clusters.append((x[start], x[prev])); start = i
            prev = i
        clusters.append((x[start], x[prev]))
    for a, b in clusters:
        ax.axvspan(a, b, color=C_MAGENTA, alpha=0.18, lw=0)
    lo, hi = ax.get_ylim()
    ax.set_ylim(lo, max(hi, thr * 1.5))
    ax.text(x[-1], thr * 1.04, f"{label}* = {thr:.2f}", fontsize=5.4, color=C_MAGENTA, ha="right", va="bottom")
    ax.set_ylabel(label)
    return clusters


def ax_ellipse(ax, x: np.ndarray, y: np.ndarray, color: str, level: float = 0.95, scatter: bool = True, label: Optional[str] = None, s: float = 3) -> float:
    """Confidence ellipse (bivariate normal); returns its area."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    cov = np.cov(x, y)
    vals, vecs = np.linalg.eigh(cov)
    o = vals.argsort()[::-1]
    vals, vecs = vals[o], vecs[:, o]
    k = stats.chi2.ppf(level, 2)
    w, h = 2 * np.sqrt(k * vals)
    ang = np.degrees(np.arctan2(*vecs[:, 0][::-1]))
    ax.add_patch(Ellipse((x.mean(), y.mean()), w, h, angle=ang, fc=color, ec=color, alpha=0.16, lw=0))
    ax.add_patch(Ellipse((x.mean(), y.mean()), w, h, angle=ang, fc="none", ec=color, lw=1.3, label=label))
    if scatter:
        ax.scatter(x, y, s=s, color=color, alpha=0.35, lw=0)
    ax.plot(x.mean(), y.mean(), "+", color=color, ms=6, mew=1.2)
    return float(np.pi * w * h / 4)


def pitch_outline(ax, length: float = 105, width: float = 68, color: str = "#9CA3AF") -> None:
    lw = 0.7
    ax.add_patch(Rectangle((0, 0), length, width, fill=False, ec=color, lw=lw))
    ax.plot([length / 2] * 2, [0, width], color=color, lw=lw)
    ax.add_patch(Ellipse((length / 2, width / 2), 18.3, 18.3, fill=False, ec=color, lw=lw))
    for x0, sgn in ((0, 1), (length, -1)):
        ax.add_patch(Rectangle((x0 if sgn == 1 else x0 - 16.5, width / 2 - 20.15), 16.5, 40.3, fill=False, ec=color, lw=lw))
        ax.add_patch(Rectangle((x0 if sgn == 1 else x0 - 5.5, width / 2 - 9.16), 5.5, 18.32, fill=False, ec=color, lw=lw))
    ax.set_xlim(-2, length + 2); ax.set_ylim(-2, width + 2); ax.set_aspect("equal"); ax.axis("off")


def ax_pitch_heat(ax, x: np.ndarray, y: np.ndarray, length: float = 105, width: float = 68, bins: int = 28):
    h, xe, ye = np.histogram2d(x, y, bins=[int(bins * length / width), bins], range=[[0, length], [0, width]])
    from scipy.ndimage import gaussian_filter
    h = gaussian_filter(h, 1.0)
    im = ax.imshow(h.T / h.max(), origin="lower", extent=[0, length, 0, width], cmap=SEQ, alpha=0.9, vmin=0, vmax=1, zorder=0)
    pitch_outline(ax, length, width)
    return im


def ax_gantt(ax, tasks: Sequence[Tuple[str, float, float, str]], milestones: Sequence[Tuple[float, str]] = (), xlabel: str = "", row_h: float = 0.58) -> None:
    """tasks: (label, start, end, colour). Milestones: diamonds with labels above the first row."""
    n = len(tasks)
    for i, (lab, a, b, c) in enumerate(tasks):
        y = n - 1 - i
        ax.barh(y, b - a, left=a, height=row_h, color=c, alpha=0.9, lw=0)
        ax.text(a - 0.2, y, lab, ha="right", va="center", fontsize=6)
    for x, lab in milestones:
        ax.plot([x], [n - 0.1], marker="D", ms=4, color=C_INK, clip_on=False)
        ax.text(x, n + 0.25, lab, ha="center", va="bottom", fontsize=5.5, color=C_GREY)
    ax.set_yticks([]); ax.spines["left"].set_visible(False)
    ax.set_xlabel(xlabel); ax.set_ylim(-0.6, n + 0.2)
    ax.grid(axis="x", linestyle=":", linewidth=0.5, color=C_LIGHT); ax.set_axisbelow(True)


def paired_ci(a: np.ndarray, b: Optional[np.ndarray] = None) -> Tuple[float, float, float]:
    """Mean (or mean difference a−b for paired data) with 95% t CI."""
    v = np.asarray(a, float) - (np.asarray(b, float) if b is not None else 0)
    v = v[np.isfinite(v)]
    se = v.std(ddof=1) / np.sqrt(len(v))
    tc = stats.t.ppf(0.975, len(v) - 1)
    return v.mean(), v.mean() - tc * se, v.mean() + tc * se


def mean_se_curves(arr: np.ndarray, sd: bool = False) -> Tuple[np.ndarray, np.ndarray]:
    """subjects×points → mean, se (or SD)."""
    n = np.isfinite(arr).sum(0)
    m = np.nanmean(arr, 0)
    s = np.nanstd(arr, 0, ddof=1)
    return m, (s if sd else s / np.sqrt(n))
