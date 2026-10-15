# -*- coding: utf-8 -*-
"""Scale-free axes-level blocks used by the results builder (estimate forests, meta-analysis forest, funnel, bubble plot).

The pubstyle blocks assume effect sizes of a given magnitude; these accept any scale (mmol/L, kg, SMD ...) and never hard-code x positions.
All text arrives as arguments so both language sets work.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon

from ..pubstyle.style import C_AMBER, C_BAND_COOL, C_GREY, C_INK, C_LIGHT, C_MAGENTA, C_SLATE, hair_y

C_BAND = C_BAND_COOL


def est_forest(ax, rows: Sequence[dict], xlabel: str, ref: float = 0.0, decimals: int = 2, text_x: float = 1.03, ref_label: Optional[str] = None, show_labels: bool = True) -> None:
    """rows: dict(label, est, lo, hi, color, hollow=False, text='' , header=False). Value text sits in a column right of the axes."""
    n = len(rows)
    ys = np.arange(n)[::-1].astype(float)
    ok = [r for r in rows if not r.get("header")]
    lo = min(r["lo"] for r in ok)
    hi = max(r["hi"] for r in ok)
    lo, hi = min(lo, ref), max(hi, ref)
    pad = 0.12 * (hi - lo or 1.0)
    for y, r in zip(ys, rows):
        if r.get("header"):
            ax.text(0, y, r["label"], transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=6.4, fontweight="bold", color=r.get("color", C_INK))
            continue
        c = r["color"]
        ax.errorbar(r["est"], y, xerr=[[r["est"] - r["lo"]], [r["hi"] - r["est"]]], fmt="D" if r.get("hollow") else "o", ms=5, mfc="white" if r.get("hollow") else c,
                    mec=c, mew=1.3, ecolor=c, elinewidth=1.5, capsize=2.5, zorder=3)
        txt = r.get("text") or f"{r['est']:.{decimals}f} ({r['lo']:.{decimals}f}, {r['hi']:.{decimals}f})"
        ax.text(text_x, y, txt, transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=5.6, color=C_INK, linespacing=1.15)
    ax.axvline(ref, color=C_GREY, lw=0.7)
    if ref_label:
        ax.text(ref, n - 0.35, ref_label, fontsize=5.3, color=C_GREY, ha="center", va="bottom")
    ax.set_xlim(lo - pad, hi + pad)
    ax.set_ylim(-0.8, n - 0.2)
    ax.set_yticks([y for y, r in zip(ys, rows) if not r.get("header")])
    ax.set_yticklabels([r["label"] for r in rows if not r.get("header")] if show_labels else [])
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel(xlabel)


def meta_forest(studies, pooled: Dict, xlabel: str, left_header: str, right_header: str, pooled_label: str, het_text: str, subs: Optional[List[Dict]] = None,
                sub_col: Optional[str] = None, sub_colors: Optional[Dict[str, str]] = None, favour: Optional[tuple] = None, decimals: int = 2, width: float = 7.2):
    """Forest plot: squares ∝ weight, diamonds = pooled (and subgroup pooled). studies: DataFrame(study, es, lo, hi, w[, sub_col])."""
    d = studies.copy()
    if sub_col and sub_col in d and subs:
        d["_s"] = d[sub_col].astype(str)
        order = [s["level"] for s in subs]
        d["_o"] = d["_s"].map({k: i for i, k in enumerate(order)})
        d = d.sort_values(["_o", "es"]).reset_index(drop=True)
    layout = []  # (kind, payload)
    if sub_col and sub_col in d and subs:
        for s in subs:
            layout.append(("head", s))
            for _, r in d[d["_s"] == s["level"]].iterrows():
                layout.append(("study", r))
            layout.append(("sub", s))
    else:
        layout = [("study", r) for _, r in d.iterrows()]
    k = len(layout)
    fig, ax = plt.subplots(figsize=(width, 0.19 * k + 1.9))
    fig.subplots_adjust(left=0.36, right=0.70)
    lo = min(d["lo"].min(), pooled["lo"])
    hi = max(d["hi"].max(), pooled["hi"])
    pad = 0.08 * (hi - lo)
    ax.set_xlim(lo - pad, hi + pad)
    tl = ax.get_yaxis_transform()
    y = k + 0.5
    ylist = []
    for kind, p in layout:
        y -= 1
        ylist.append(y)
        if kind == "head":
            ax.text(-0.62, y, f"{p['level']}", transform=tl, fontsize=6.2, fontweight="bold", color=(sub_colors or {}).get(p["level"], C_INK), va="center", ha="left")
        elif kind == "study":
            c = (sub_colors or {}).get(str(p.get(sub_col)), C_SLATE) if sub_col else C_SLATE
            ax.plot([p["lo"], p["hi"]], [y, y], color=c, lw=1.1, zorder=2)
            ax.scatter(p["es"], y, marker="s", s=14 + 2.2 * p["w"], color=c, zorder=3, lw=0)
            ax.text(-0.62, y, "   " + str(p["study"]), transform=tl, fontsize=6.0, va="center", ha="left")
            ax.text(1.03, y, f"{p['es']:.{decimals}f} ({p['lo']:.{decimals}f}, {p['hi']:.{decimals}f})", transform=tl, fontsize=5.7, va="center")
            ax.text(1.52, y, f"{p['w']:.1f}", transform=tl, fontsize=5.7, va="center", ha="right")
        else:
            c = (sub_colors or {}).get(p["level"], C_SLATE)
            ax.add_patch(Polygon([[p["lo"], y], [p["est"], y + 0.32], [p["hi"], y], [p["est"], y - 0.32]], closed=True, fc=c, ec="none", alpha=0.85, zorder=3))
            ax.text(-0.62, y, f"   {p['level']} (k = {p['k']})", transform=tl, fontsize=5.8, fontweight="bold", va="center")
            ax.text(1.03, y, f"{p['est']:.{decimals}f} ({p['lo']:.{decimals}f}, {p['hi']:.{decimals}f})", transform=tl, fontsize=5.7, va="center", fontweight="bold")
    yd = -0.9
    ax.add_patch(Polygon([[pooled["lo"], yd], [pooled["est"], yd + 0.42], [pooled["hi"], yd], [pooled["est"], yd - 0.42]], closed=True, fc=C_MAGENTA, ec="none", zorder=3))
    ax.text(-0.62, yd, pooled_label, transform=tl, fontsize=6.2, fontweight="bold", va="center")
    ax.text(1.03, yd, f"{pooled['est']:.{decimals}f} ({pooled['lo']:.{decimals}f}, {pooled['hi']:.{decimals}f})", transform=tl, fontsize=5.7, fontweight="bold", va="center")
    ax.text(-0.62, yd - 0.95, het_text, transform=tl, fontsize=5.5, color=C_GREY, va="center")
    ax.axvline(0, color=C_INK, lw=0.7)
    ax.text(-0.62, k + 0.55, left_header, transform=tl, fontsize=6.2, fontweight="bold")
    ax.text(1.03, k + 0.55, right_header, transform=tl, fontsize=6.2, fontweight="bold")
    ax.text(1.52, k + 0.55, "W%", transform=tl, fontsize=6.2, fontweight="bold", ha="right")
    ax.set_ylim(yd - 1.6, k + 1.2)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel(xlabel)
    if favour:
        yf = -0.62 / (0.77 * fig.get_figheight())
        ax.text(0.0, yf, favour[0] + " ", transform=ax.get_xaxis_transform(), ha="right", fontsize=5.6, color=C_GREY)
        ax.text(0.0, yf, " " + favour[1], transform=ax.get_xaxis_transform(), ha="left", fontsize=5.6, color=C_GREY)
    return fig


def funnel(ax, es: np.ndarray, se: np.ndarray, pooled: float, xlabel: str, ylabel: str, color: str = C_SLATE) -> None:
    ymax = se.max() * 1.08
    ax.fill([pooled - 1.96 * ymax, pooled, pooled + 1.96 * ymax], [ymax, 0, ymax], color=C_BAND, zorder=0)
    ax.plot([pooled, pooled - 1.96 * ymax], [0, ymax], color=C_LIGHT, lw=0.7)
    ax.plot([pooled, pooled + 1.96 * ymax], [0, ymax], color=C_LIGHT, lw=0.7)
    ax.axvline(pooled, color=C_MAGENTA, lw=1)
    ax.scatter(es, se, s=16, color=color, alpha=0.85, edgecolors="white", linewidths=0.5, zorder=3)
    ax.set_ylim(ymax, 0)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


def bubble_metareg(ax, x: np.ndarray, y: np.ndarray, w: np.ndarray, reg: Dict, xlabel: str, ylabel: str, color: str = C_SLATE) -> None:
    gx = np.linspace(x.min(), x.max(), 50)
    ax.axhline(0, color=C_AMBER, lw=1.1, ls=(0, (3, 2)))
    ax.plot(gx, reg["intercept"] + reg["slope"] * gx, color=C_MAGENTA, lw=1.4)
    ax.scatter(x, y, s=10 + 3.0 * w, color=color, alpha=0.6, edgecolors="white", linewidths=0.5, zorder=3)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    hair_y(ax)


def small_grid(n: int, ncols: int = 3, cell=(2.4, 2.3)):
    nrows = int(np.ceil(n / ncols))
    fig, axs = plt.subplots(nrows, ncols, figsize=(cell[0] * ncols, cell[1] * nrows), squeeze=False)
    flat = axs.ravel()
    for a in flat[n:]:
        a.axis("off")
    return fig, flat[:n]


def diff_estimate(ax, rows: Sequence[dict], ylabel: str, decimals: int = 2, ref: float = 0.0, ref_label: Optional[str] = None, width: float = 0.34) -> None:
    """Estimation panel for model contrasts: sampling distribution (t, df) of each difference as a half-violin, with the point
    estimate and its 95% CI and the numbers written above. rows: dict(label, est, lo, hi, color, df=None, text='')."""
    from scipy import stats
    tops = []
    for i, r in enumerate(rows):
        dfree = r.get("df") or 1e6
        tc = stats.t.ppf(0.975, dfree)
        se = (r["hi"] - r["lo"]) / (2 * tc) if r["hi"] > r["lo"] else 1e-9
        yy = np.linspace(r["est"] - 4 * se, r["est"] + 4 * se, 200)
        d = stats.t.pdf((yy - r["est"]) / se, dfree)
        d = d / d.max() * width
        inside = (yy >= r["lo"]) & (yy <= r["hi"])
        c = r["color"]
        ax.fill_betweenx(yy, i + 0.06, i + 0.06 + d, color=c, alpha=0.12, lw=0)
        ax.fill_betweenx(yy[inside], i + 0.06, i + 0.06 + d[inside], color=c, alpha=0.28, lw=0)
        ax.plot(i + 0.06 + d, yy, color=c, lw=0.7)
        ax.plot([i, i], [r["lo"], r["hi"]], color=c, lw=2.2, solid_capstyle="round", zorder=4)
        ax.plot(i, r["est"], "o", ms=6, color=c, mec="white", mew=1.0, zorder=5)
        txt = r.get("text") or f"{r['est']:.{decimals}f}\n[{r['lo']:.{decimals}f}, {r['hi']:.{decimals}f}]"
        ax.annotate(txt, xy=(i, r["est"] + 4 * se), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=5.7, color=C_INK, linespacing=1.2)
        tops.append(r["est"] + 4 * se)
    ax.axhline(ref, color=C_GREY, lw=0.7, ls=(0, (3, 2)), zorder=1)
    if ref_label:
        ax.text(len(rows) - 0.45, ref, ref_label, fontsize=5.4, color=C_GREY, ha="right", va="bottom")
    lo_all = min(min(r["est"] - 4 * ((r["hi"] - r["lo"]) / 3.92) for r in rows), ref)
    hi_all = max(max(tops), ref)
    pad = 0.28 * (hi_all - lo_all or 1.0)
    ax.set_ylim(lo_all - 0.05 * pad, hi_all + pad)
    ax.set_xlim(-0.45, len(rows) - 0.45)
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels([r["label"] for r in rows])
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel(ylabel)
    hair_y(ax)
