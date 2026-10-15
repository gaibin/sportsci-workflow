#!/usr/bin/env python3
"""
Nature-style plotting for sport science data.

Loads sane defaults from ../assets/matplotlibrc, exposes one-call helpers
for the figure types most common in sport science papers, and exports both
PDF (vector) and PNG (300 DPI) by default.

Usage as a CLI
--------------
# Box + jitter, group comparison
python nature_plot.py box data.csv --y vo2max --x group --out figure_1

# Scatter with regression line and 95% CI band
python nature_plot.py scatter data.csv --x volume --y improvement --out figure_2

# Lines with shaded SEM band, time-series
python nature_plot.py line data.csv --time week --y power --group condition --out figure_3

Use as a module
---------------
from nature_plot import box_jitter, scatter_reg, line_band
fig, ax = box_jitter(df, x='group', y='vo2max')
fig.savefig('figure.pdf')
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# Load the bundled matplotlibrc
_HERE = Path(__file__).resolve().parent
_RC = _HERE.parent / "assets" / "matplotlibrc"
if _RC.exists():
    matplotlib.rc_file(str(_RC), use_default_template=False)

# Colorblind-safe palette (Wong 2011)
PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#F0E442", "#56B4E9", "#E69F00", "#000000"]
# Nature-inspired alternative
PALETTE_NATURE = ["#E64B35", "#4DBBD5", "#00A087", "#3C5488", "#F39B7F", "#8491B4", "#91D1C2", "#DC0000"]

# Single-column figure size in inches (89 mm)
SINGLE_COL = (3.5, 2.8)
DOUBLE_COL = (7.2, 3.2)


def load(path):
    p = Path(path)
    if p.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(p)
    return pd.read_csv(p)


# ---------------------------------------------------------------------------
# Figure helpers
# ---------------------------------------------------------------------------

def _strip_spines(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(direction="out", length=3, width=0.75)
    for s in ("left", "bottom"):
        ax.spines[s].set_linewidth(0.75)


def box_jitter(df, x, y, palette=None, figsize=SINGLE_COL, ax=None):
    """Box plot with individual data points jittered on top."""
    palette = palette or PALETTE
    groups = list(df[x].dropna().unique())
    data = [df.loc[df[x] == g, y].dropna().values for g in groups]

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    bp = ax.boxplot(
        data,
        positions=range(len(groups)),
        widths=0.55,
        showfliers=False,
        patch_artist=True,
        medianprops={"color": "black", "linewidth": 1.0},
        boxprops={"linewidth": 0.75},
        whiskerprops={"linewidth": 0.75},
        capprops={"linewidth": 0.75},
    )
    for patch, color in zip(bp["boxes"], palette):
        patch.set_facecolor(color)
        patch.set_alpha(0.35)
        patch.set_edgecolor(color)

    rng = np.random.default_rng(seed=0)
    for i, vals in enumerate(data):
        jitter = rng.uniform(-0.12, 0.12, size=len(vals))
        ax.scatter(
            np.full_like(vals, i, dtype=float) + jitter,
            vals,
            s=14,
            color=palette[i % len(palette)],
            edgecolor="white",
            linewidth=0.4,
            zorder=3,
        )

    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    _strip_spines(ax)
    fig.tight_layout()
    return fig, ax


def scatter_reg(df, x, y, color=None, figsize=SINGLE_COL, ax=None):
    """Scatter with linear regression line and 95% CI band; prints r and P in corner."""
    color = color or PALETTE[0]
    a = df[[x, y]].dropna()

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    ax.scatter(a[x], a[y], s=20, color=color, alpha=0.7, edgecolor="white", linewidth=0.4)

    slope, intercept, r, p, se = stats.linregress(a[x], a[y])
    xs = np.linspace(a[x].min(), a[x].max(), 100)
    ys = slope * xs + intercept
    ax.plot(xs, ys, color=color, linewidth=1.0)

    # 95% CI band via bootstrap
    n_boot = 500
    rng = np.random.default_rng(seed=0)
    boot_lines = np.empty((n_boot, len(xs)))
    for i in range(n_boot):
        idx = rng.integers(0, len(a), len(a))
        sl, ic, *_ = stats.linregress(a[x].values[idx], a[y].values[idx])
        boot_lines[i] = sl * xs + ic
    lo = np.percentile(boot_lines, 2.5, axis=0)
    hi = np.percentile(boot_lines, 97.5, axis=0)
    ax.fill_between(xs, lo, hi, color=color, alpha=0.15, linewidth=0)

    p_str = "< 0.001" if p < 0.001 else f"= {p:.3f}"
    ax.text(0.04, 0.96, f"r = {r:.2f}\nP {p_str}\nn = {len(a)}",
            transform=ax.transAxes, va="top", ha="left", fontsize=7)

    ax.set_xlabel(x)
    ax.set_ylabel(y)
    _strip_spines(ax)
    fig.tight_layout()
    return fig, ax


def line_band(df, time, y, group=None, palette=None, figsize=SINGLE_COL, ax=None,
              error="sem"):
    """Line plot over time with shaded error band (SEM, SD, or 95% CI)."""
    palette = palette or PALETTE
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    if group is None:
        agg = df.groupby(time)[y].agg(["mean", "std", "count"]).reset_index()
        err = _err(agg, error)
        ax.plot(agg[time], agg["mean"], color=palette[0], linewidth=1.25, marker="o", markersize=4)
        ax.fill_between(agg[time], agg["mean"] - err, agg["mean"] + err,
                        color=palette[0], alpha=0.2, linewidth=0)
    else:
        for i, (g, sub) in enumerate(df.groupby(group)):
            agg = sub.groupby(time)[y].agg(["mean", "std", "count"]).reset_index()
            err = _err(agg, error)
            c = palette[i % len(palette)]
            ax.plot(agg[time], agg["mean"], color=c, linewidth=1.25, marker="o",
                    markersize=4, label=str(g))
            ax.fill_between(agg[time], agg["mean"] - err, agg["mean"] + err,
                            color=c, alpha=0.2, linewidth=0)
        ax.legend(frameon=False, fontsize=7, loc="best")

    ax.set_xlabel(time)
    ax.set_ylabel(y)
    _strip_spines(ax)
    fig.tight_layout()
    return fig, ax


def _err(agg, kind):
    if kind == "sd":
        return agg["std"]
    if kind == "sem":
        return agg["std"] / np.sqrt(agg["count"])
    if kind == "ci":
        return 1.96 * agg["std"] / np.sqrt(agg["count"])
    raise ValueError(f"Unknown error kind: {kind}")


def save(fig, stem):
    """Save as both vector PDF and 300-DPI PNG."""
    fig.savefig(f"{stem}.pdf", bbox_inches="tight", pad_inches=0.05)
    fig.savefig(f"{stem}.png", dpi=300, bbox_inches="tight", pad_inches=0.05)
    print(f"Wrote {stem}.pdf and {stem}.png")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_b = sub.add_parser("box")
    p_b.add_argument("file")
    p_b.add_argument("--x", required=True)
    p_b.add_argument("--y", required=True)
    p_b.add_argument("--out", required=True, help="output stem (no extension)")

    p_s = sub.add_parser("scatter")
    p_s.add_argument("file")
    p_s.add_argument("--x", required=True)
    p_s.add_argument("--y", required=True)
    p_s.add_argument("--out", required=True)

    p_l = sub.add_parser("line")
    p_l.add_argument("file")
    p_l.add_argument("--time", required=True)
    p_l.add_argument("--y", required=True)
    p_l.add_argument("--group", default=None)
    p_l.add_argument("--error", default="sem", choices=["sd", "sem", "ci"])
    p_l.add_argument("--out", required=True)

    args = ap.parse_args()
    df = load(args.file)

    if args.cmd == "box":
        fig, _ = box_jitter(df, args.x, args.y)
    elif args.cmd == "scatter":
        fig, _ = scatter_reg(df, args.x, args.y)
    elif args.cmd == "line":
        fig, _ = line_band(df, args.time, args.y, group=args.group, error=args.error)

    save(fig, args.out)


if __name__ == "__main__":
    main()
