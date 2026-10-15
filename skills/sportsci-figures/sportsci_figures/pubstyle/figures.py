"""
pubstyle.figures — axes-level building blocks that reproduce the house figure style.

Every function draws on a caller-supplied ``ax`` (except ``fig_forest_effects`` which makes
its own figure) so that figures are *composed*: create the grid, call the blocks, add panel
letters, save with ``save_figure``. All numbers shown must come from data — nothing here
invents values. Text defaults come from ``style.t(key)`` and follow the active language.

Block catalogue (see reference/FIGURE_CATALOG.md for a picture of each):
    ax_bands              group time-courses, mean ± SEM bands, dashed control
    shade_window          highlight an intervention / exposure window
    mark_events           small triangles + labels for meals, doses, events
    ax_diff_band          paired difference vs reference with pointwise CI band
    ax_paired_estimate    raw individual data (+ lines) with model estimate ± 95% CI
    ax_contrast_forest    estimation plot: contrasts with CI, threshold line, text column
    ax_dose_response      per-dose individual differences + estimate + trend line
    ax_prepost            pre/post spaghetti by arm with mean ± SEM
    ax_stacked_bars       composition bars (e.g. time in ranges)
    ax_scatter_fit        scatter + OLS line + 95% CI band + r, P
    ax_agp                ambulatory-glucose-profile style median / IQR / 5-95 bands
    fig_forest_effects    grouped forest plot of standardised effects
    draw_flow             CONSORT-style flow diagram from a box/arrow specification
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch
from scipy import stats

from .style import (C_AMBER, C_BAND, C_GOLD_DARK, C_GOLD_MID, C_GREY, C_HAIR, C_INK, C_LIGHT, C_MAGENTA, C_SLATE, DOUBLE, fmt_p, hair_y, t, wrap_label)


# ----------------------------------------------------------------------------- time-courses
def ax_bands(ax, x, series: Dict[str, Tuple[np.ndarray, np.ndarray]], colors: Dict[str, str], dashed: Sequence[str] = (),
             lw: float = 1.4, band_alpha: float = 0.16) -> None:
    """series: name -> (mean, se). Control-like series should be listed in ``dashed``."""
    for name, (mu, se) in series.items():
        c = colors[name]
        ax.fill_between(x, mu - se, mu + se, color=c, alpha=band_alpha, lw=0, zorder=2)
        ax.plot(x, mu, color=c, lw=lw, ls=(0, (3, 2)) if name in dashed else "-", zorder=3, solid_capstyle="round", label=name)


def shade_window(ax, x0: float, x1: float, color: str = C_AMBER, alpha: float = 0.18, text: Optional[str] = None, text_y: Optional[float] = None) -> None:
    ax.axvspan(x0, x1, color=color, alpha=alpha, lw=0, zorder=0)
    if text:
        ax.text(x0 + 0.15, text_y if text_y is not None else ax.get_ylim()[0], text, rotation=90, ha="left", va="bottom", fontsize=5.5, color=C_GOLD_DARK)


def mark_events(ax, events: Sequence[Tuple[float, str]], y: float, label_dy: float = 0.3) -> None:
    for x, lab in events:
        ax.plot([x], [y], marker="v", ms=3.5, color=C_INK, clip_on=False)
        ax.text(x, y + label_dy, lab, ha="center", va="bottom", fontsize=5.5, color=C_GREY)


def ax_diff_band(ax, x, diffs: Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]], colors: Dict[str, str], ref_label: Optional[str] = None,
                 mark_min: bool = True) -> None:
    """diffs: name -> (mean_diff, ci_lo, ci_hi) on the common x grid; reference line at 0 uses the control colour, dashed."""
    for name, (mu, lo, hi) in diffs.items():
        ax.fill_between(x, lo, hi, color=colors[name], alpha=0.13, lw=0)
        ax.plot(x, mu, color=colors[name], lw=1.4)
        if mark_min:
            k = int(np.nanargmin(mu))
            ax.plot(x[k], mu[k], "o", ms=3, color=colors[name], mec="white", mew=0.5, zorder=4)
    ax.axhline(0, color=C_AMBER, lw=1.2, ls=(0, (3, 2)))
    if ref_label:
        ax.text(x[-1], 0.0, ref_label, color=C_GOLD_MID, fontsize=6, ha="right", va="bottom")


def pointwise_diff_ci(a: np.ndarray, b: np.ndarray, level: float = 0.95):
    """a, b: subjects x time arrays (paired). Returns mean, lo, hi of (a-b) per time point (uncorrected t CI)."""
    d = a - b
    n = np.isfinite(d).sum(0)
    mu = np.nanmean(d, 0)
    se = np.nanstd(d, 0, ddof=1) / np.sqrt(n)
    tc = stats.t.ppf(0.5 + level / 2, np.maximum(n - 1, 1))
    return mu, mu - tc * se, mu + tc * se


# ----------------------------------------------------------------------------- paired raw + estimate
def ax_paired_estimate(ax, wide: pd.DataFrame, order: Sequence[str], colors: Dict[str, str], est: Dict[str, Tuple[float, float, float]],
                       ylabel: str, label_map: Optional[Dict[str, str]] = None, seed: int = 7) -> None:
    """Raw observations (jittered points; grey lines join subjects with every condition) + estimate ± CI.

    wide: rows = subjects, columns = conditions. est: condition -> (estimate, lo, hi) from the statistical model.
    """
    x = {c: i for i, c in enumerate(order)}
    full = wide[list(order)].dropna()
    for _, r in full.iterrows():
        ax.plot([x[c] for c in order], [r[c] for c in order], color=C_LIGHT, lw=0.4, alpha=0.8, zorder=1)
    for c in order:
        v = wide[c].dropna()
        rng = np.random.default_rng(seed + x[c])
        ax.scatter(x[c] + rng.uniform(-0.1, 0.1, len(v)), v, s=6.5, color=colors[c], alpha=0.55, lw=0, zorder=2)
    for c in order:
        e, lo, hi = est[c]
        ax.plot([x[c] + 0.22, x[c] + 0.22], [lo, hi], color=colors[c], lw=1.8, solid_capstyle="round", zorder=5)
        ax.plot(x[c] + 0.22, e, "o", ms=5.6, color=colors[c], mec="white", mew=0.9, zorder=6)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([wrap_label((label_map or {}).get(c, c), cjk_width=4 if len(order) >= 4 else 5) for c in order])
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel(ylabel)
    hair_y(ax)
    return full.shape[0]


def ax_contrast_forest(ax, rows: Sequence[dict], xlabel: str, threshold: Optional[float] = None, threshold_label: Optional[str] = None,
                       text_pad: float = 0.6, decimals: int = 1) -> None:
    """rows: dict(label, est, lo, hi, color, hollow=False, ptext='')  drawn top to bottom.

    A text column (estimate (CI) + P) is printed to the right of the data range.
    """
    n = len(rows)
    ys = [n - 1 - i for i in range(n)]
    xmin = min(min(r["lo"] for r in rows) - 1.0, (threshold or 0) - 2)
    xmax = max(max(r["hi"] for r in rows) + 1.0, 3)
    for y, r in zip(ys, rows):
        hollow = r.get("hollow", False)
        col = r["color"]
        ax.errorbar(r["est"], y, xerr=[[r["est"] - r["lo"]], [r["hi"] - r["est"]]], fmt="D" if hollow else "o", ms=5, mfc="white" if hollow else col,
                    mec=col, mew=1.3, ecolor=col, elinewidth=1.5, capsize=2.5, zorder=3)
        ax.text(xmax + text_pad, y, f"{r['est']:.{decimals}f} ({r['lo']:.{decimals}f}, {r['hi']:.{decimals}f})\n{r.get('ptext', '')}", ha="left", va="center", fontsize=5.6,
                color=C_INK, linespacing=1.15)
    ax.axvline(0, color=C_GREY, lw=0.6)
    if threshold is not None:
        ax.axvline(threshold, color=C_MAGENTA, lw=0.7, ls=":")
        if threshold_label:
            ax.text(threshold - 0.15, n - 0.3, threshold_label, fontsize=5.3, color=C_MAGENTA, ha="right", va="top")
    ax.set_xlim(xmin, xmax + 9.5)
    ax.set_ylim(-0.8, n - 0.2)
    ax.set_yticks(ys)
    ax.set_yticklabels([r["label"] for r in rows])
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel(xlabel)


def ax_dose_response(ax, doses: Dict[str, dict], colors: Dict[str, str], xlabel: str, ylabel: str, trend: Optional[Tuple[float, float]] = None,
                     note: Optional[str] = None, xtick_labels: Optional[Dict[str, str]] = None) -> None:
    """doses: label -> dict(x, diffs=array of individual differences vs reference, est, lo, hi).

    trend = (slope per x-unit, intercept at x=0) draws a dashed linear trend line.
    """
    for lab, d in doses.items():
        rng = np.random.default_rng(int(d["x"]))
        ax.scatter(d["x"] + rng.uniform(-0.9, 0.9, len(d["diffs"])), d["diffs"], s=6, color=colors[lab], alpha=0.35, lw=0, zorder=1)
    xs = [d["x"] for d in doses.values()]
    if trend is not None:
        gx = np.linspace(min(xs) - 1, max(xs) + 1, 50)
        ax.plot(gx, trend[1] + trend[0] * gx, color=C_INK, lw=1, ls=(0, (2, 2)), zorder=2)
    for lab, d in doses.items():
        ax.plot([d["x"], d["x"]], [d["lo"], d["hi"]], color=colors[lab], lw=2.0, solid_capstyle="round", zorder=4)
        ax.plot(d["x"], d["est"], "o", ms=5.8, color=colors[lab], mec="white", mew=0.9, zorder=5)
    ax.axhline(0, color=C_AMBER, lw=1.2, ls=(0, (3, 2)))
    ax.set_xticks(xs)
    ax.set_xticklabels([(xtick_labels or {}).get(k, str(d["x"])) for k, d in doses.items()])
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if note:
        lo, hi = ax.get_ylim()
        ax.set_ylim(lo, hi + 0.14 * (hi - lo))          # head-room so the note never overlaps the data
        ax.text(0.97, 0.98, note, transform=ax.transAxes, ha="right", va="top", fontsize=5.6, color=C_GREY)
    hair_y(ax)


# ----------------------------------------------------------------------------- pre/post
def ax_prepost(ax, long_df: pd.DataFrame, id_col: str, group_col: str, time_col: str, y_col: str, groups: Sequence[str],
               colors: Dict[str, str], time_labels: Sequence[str], ylabel: str, title: Optional[str] = None, group_label_y: float = -0.1,
               gap: float = 1.1) -> None:
    """Spaghetti plot: thin individual lines, thick group mean ± SEM, groups side by side.

    long_df has one row per subject per time (time in {0, 1}).
    """
    w = long_df.pivot_table(index=id_col, columns=time_col, values=y_col).dropna()
    gmap = long_df.drop_duplicates(id_col).set_index(id_col)[group_col]
    w["_g"] = w.index.map(gmap)
    ticks, tlabs = [], []
    for gi, g in enumerate(groups):
        x0, x1 = gi * (1 + gap), gi * (1 + gap) + 0.9
        s = w[w["_g"] == g]
        c = colors[g]
        for _, r in s.iterrows():
            ax.plot([x0, x1], [r[0], r[1]], color=c, alpha=0.22, lw=0.55, zorder=1)
        ax.scatter(np.full(len(s), x0), s[0], s=5, color=c, alpha=0.55, lw=0, zorder=2)
        ax.scatter(np.full(len(s), x1), s[1], s=5, color=c, alpha=0.55, lw=0, zorder=2)
        m = [s[0].mean(), s[1].mean()]
        se = [s[0].std(ddof=1) / np.sqrt(len(s)), s[1].std(ddof=1) / np.sqrt(len(s))]
        ax.plot([x0, x1], m, color="white", lw=3.6, zorder=3, solid_capstyle="round")   # halo separates the mean line from the spaghetti
        ax.errorbar([x0, x1], m, yerr=se, fmt="-o", ms=5, lw=2.0, color=c, mec="white", mew=0.9, ecolor=c, elinewidth=1.6, capsize=0, zorder=4)
        ticks += [x0, x1]
        tlabs += list(time_labels)
        ax.text((x0 + x1) / 2, group_label_y, g, transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=6, color=c, fontweight="bold")
    ax.set_xticks(ticks)
    ax.set_xticklabels(tlabs, fontsize=5.8)
    ax.tick_params(axis="x", length=0)
    ax.set_xlim(-0.4, (len(groups) - 1) * (1 + gap) + 1.3)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title, fontsize=5.9, loc="left", pad=3, linespacing=1.3)


# ----------------------------------------------------------------------------- composition / association / profile
def ax_stacked_bars(ax, bars: Sequence[Tuple[str, Dict[str, float]]], part_order: Sequence[str], part_colors: Dict[str, str], ylabel: str,
                    group_labels: Optional[Sequence[Tuple[float, str, str]]] = None, positions: Optional[Sequence[float]] = None, min_label: float = 4,
                    ylim: Optional[Tuple[float, float]] = (0, 100), legend: bool = False, value_fmt: str = "{:.0f}", total_labels: bool = False) -> None:
    """bars: [(tick label, {part: value})]; parts stacked from the first of part_order (bottom).

    ylim=(0, 100) for percentage composition; pass ylim=None for absolute values (autoscale). legend=True adds a
    frameless legend above the axes; total_labels=True prints each bar's total above it.
    """
    pos = list(positions) if positions is not None else list(range(len(bars)))
    for p, (lab, vals) in zip(pos, bars):
        bottom = 0.0
        for part in part_order:
            ax.bar(p, vals[part], bottom=bottom, width=0.72, color=part_colors[part], lw=0)
            if vals[part] > min_label:
                ax.text(p, bottom + vals[part] / 2, value_fmt.format(vals[part]), ha="center", va="center", fontsize=5.8,
                        color="white" if part_colors[part] in (C_SLATE, C_MAGENTA) else C_INK)
            bottom += vals[part]
        if total_labels:
            ax.text(p, bottom, value_fmt.format(bottom), ha="center", va="bottom", fontsize=5.6)
    ax.set_xticks(pos)
    ax.set_xticklabels([b[0] for b in bars], fontsize=5.8)
    ax.tick_params(axis="x", length=0)
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.set_ylabel(ylabel)
    for x, lab, col in (group_labels or []):
        ax.text(x, -0.2, lab, transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=6.5, color=col, fontweight="bold")
    if legend:
        ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=part_colors[o]) for o in part_order], labels=list(part_order), loc="upper center", bbox_to_anchor=(0.5, 1.18),
                  ncol=min(len(part_order), 4), fontsize=5.4, handlelength=0.9, columnspacing=0.7)


def ax_scatter_fit(ax, x, y, color: str = C_MAGENTA, xlabel: str = "", ylabel: str = "", show_stats: bool = True) -> Tuple[float, float, int]:
    import statsmodels.api as sm
    x = np.asarray(x, float); y = np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    res = sm.OLS(y, sm.add_constant(x)).fit()
    gx = np.linspace(x.min(), x.max(), 60)
    pr = res.get_prediction(sm.add_constant(gx)).summary_frame(alpha=0.05)
    ax.fill_between(gx, pr["mean_ci_lower"], pr["mean_ci_upper"], color=color, alpha=0.15, lw=0)
    ax.plot(gx, pr["mean"], color=color, lw=1.5)
    ax.scatter(x, y, s=16, color=color, alpha=0.8, edgecolors="white", linewidths=0.5, zorder=3)
    ax.axhline(0, color=C_GREY, lw=0.5, ls=":")
    r, p = stats.pearsonr(x, y)
    if show_stats:
        ax.text(0.04, 0.96, f"r = {r:.2f}, {fmt_p(p)}\nn = {len(x)}", transform=ax.transAxes, ha="left", va="top", fontsize=6.2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    return r, p, len(x)


def ax_agp(ax, x, q: Dict[int, np.ndarray], color: str, label: str, band_alpha: float = 0.2) -> None:
    """q has keys 5, 25, 50, 75, 95 (percentile curves on the 24-h clock). Call twice (baseline then follow-up)."""
    ax.fill_between(x, q[5], q[95], color=color, alpha=0.06, lw=0)
    ax.fill_between(x, q[25], q[75], color=color, alpha=band_alpha, lw=0)
    ax.plot(x, q[50], color=color, lw=1.5, label=label, zorder=3)


# ----------------------------------------------------------------------------- grouped forest plot
def fig_forest_effects(rows: Sequence[dict], categories: Sequence[str], cat_colors: Dict[str, str], xlabel: str, footnote: str = "",
                       left_ratio: float = 0.0, width: float = DOUBLE, row_h: float = 0.165) -> plt.Figure:
    """Grouped forest plot of standardised effects.

    rows: dict(category, label, g, lo, hi, sig(bool), neutral(bool), text)   g/lo/hi already oriented so that + = favourable.
    Filled marker = significant after the stated multiplicity correction; grey = safety / neutral outcome.
    """
    from matplotlib.patches import Rectangle
    from matplotlib.transforms import blended_transform_factory
    items = []
    for cat in categories:
        items.append(("H", cat))
        items += [("R", r) for r in rows if r["category"] == cat]
    n_rows = sum(1 for k, _ in items if k == "R")
    height = max(2.2, 0.205 * len(items) + 0.95)
    fig = plt.figure(figsize=(width, height))
    bottom, top = 0.62 / height, 1 - 0.42 / height
    ax = fig.add_axes([0.36, bottom, 0.38, top - bottom])
    # symmetric x range from the data (at least ±1, at most ±3), ticks every 0.5 or 1
    span = max(1.0, min(3.0, np.ceil(max(max(abs(r["lo"]), abs(r["hi"])) for r in rows) * 2 + 0.2) / 2)) if rows else 2.0
    step = 0.5 if span <= 1.5 else 1.0
    y, placed = 0.0, []
    for kind, r in items[::-1]:
        placed.append((y, kind, r))
        y += 1.0 if kind == "R" else 1.25
    ymax = y - 0.4
    fx = blended_transform_factory(fig.transFigure, ax.transData)
    ri = 0
    for yy, kind, r in placed[::-1]:
        if kind == "H":
            col = cat_colors[r]
            ax.add_patch(Rectangle((0.015, yy - 0.28), 0.006, 0.56, transform=fx, color=col, clip_on=False, lw=0))
            ax.text(0.03, yy, r, transform=fx, fontsize=6.8, fontweight="bold", color=col, va="center", ha="left")
            continue
        if ri % 2 == 0:                                           # zebra rows across the whole figure width
            ax.add_patch(Rectangle((0.01, yy - 0.5), 0.98, 1.0, transform=fx, color=C_BAND, alpha=0.55, clip_on=False, lw=0, zorder=0))
        ri += 1
        col = C_GREY if r.get("neutral") else cat_colors[r["category"]]
        ax.plot([r["lo"], r["hi"]], [yy, yy], color=col, lw=1.4, solid_capstyle="round", zorder=3)
        ax.plot(r["g"], yy, "o", ms=5, mfc=col if r["sig"] else "white", mec=col, mew=1.2, zorder=4)
        ax.text(0.045, yy, r["label"], transform=fx, fontsize=6.3, va="center", ha="left", color=C_INK)
        ax.text(1.04, yy, r.get("text", ""), transform=ax.get_yaxis_transform(), fontsize=6.0, va="center", ha="left",
                color=C_INK if r["sig"] else C_GREY, fontweight="bold" if r["sig"] else "normal")
    ax.axvline(0, color=C_INK, lw=0.75, zorder=2)
    for v in np.arange(-span, span + 1e-9, step):
        if abs(v) > 1e-9:
            ax.axvline(v, color=C_HAIR, lw=0.5, ls=":", zorder=1)
    ax.set_xlim(-span * 1.08, span * 1.08)
    ax.set_ylim(-0.6, ymax + 0.9)
    ax.set_xticks(np.arange(-span, span + 1e-9, step))
    ax.spines["left"].set_visible(False)
    ax.set_yticks([])
    ax.set_xlabel(xlabel)
    ax.text(0.0, ymax + 0.55, "← " + t("ctrl_better").replace("←", "").strip(), transform=ax.get_yaxis_transform(), fontsize=5.8, color=C_GREY, ha="left", va="center")
    ax.text(1.0, ymax + 0.55, t("int_better").replace("→", "").strip() + " →", transform=ax.get_yaxis_transform(), fontsize=5.8, color=C_GREY, ha="right", va="center")
    ax.text(1.04, ymax + 0.55, xlabel.split("（")[0].split(" (")[0] + " (95% CI)", transform=ax.get_yaxis_transform(), fontsize=6.0, fontweight="bold",
            color=C_INK, ha="left", va="center")
    if footnote:
        fig.text(0.03, 0.12 / height, "●  " + footnote, fontsize=5.6, color=C_GREY, ha="left", va="bottom")
    return fig


# ----------------------------------------------------------------------------- flow diagram
def draw_flow(ax, boxes: Sequence[dict], arrows: Sequence[Tuple[float, float, float, float]] = (), texts: Sequence[dict] = (), xlim=(0, 1), ylim=(0, 1)) -> None:
    """boxes: dict(x, y, w, h, text, ec=C_SLATE, fc='white', fs=5.9, bold=False, lw=0.9) in axes data coordinates.

    texts: dict(x, y, s, fs=5, color=C_GREY, ha='center', va='top', bold=False).
    """
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.axis("off")
    for b in boxes:
        ax.add_patch(FancyBboxPatch((b["x"] - b["w"] / 2, b["y"] - b["h"] / 2), b["w"], b["h"], boxstyle="round,pad=0.004,rounding_size=0.012",
                                    lw=b.get("lw", 0.9), ec=b.get("ec", C_SLATE), fc=b.get("fc", "white"), zorder=2))
        ax.text(b["x"], b["y"], b["text"], ha="center", va="center", fontsize=b.get("fs", 5.9), color=C_INK, fontweight="bold" if b.get("bold") else "normal",
                linespacing=1.35, zorder=3)
    for x0, y0, x1, y1 in arrows:
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color=C_GREY, lw=0.8, shrinkA=0, shrinkB=0), zorder=1)
    for s in texts:
        ax.text(s["x"], s["y"], s["s"], fontsize=s.get("fs", 5), color=s.get("color", C_GREY), ha=s.get("ha", "center"), va=s.get("va", "top"),
                fontweight="bold" if s.get("bold") else "normal", linespacing=1.3)


# ---- extended blocks (questionnaires, survival, diagnostics, meta-analysis, omics, sport-specific) ----
from .figures_ext import *  # noqa: E402,F401,F403
