"""
Eye-tracking fixation heat map demo (SYNTHETIC data, tagged as simulated).

Shows the three eye-tracking blocks of pubstyle.figures_ext on a made-up "scene" with made-up fixations:
  * ``gaze_density``           duration-weighted, fixed-width Gaussian density relative to an even spread (1 = even)
  * ``ax_gaze_heatmap``        one panel: stimulus + turbo overlay + category chip + count tag + own colour bar
  * ``fig_gaze_heatmap_grid``  a grid of panels, last unused cell hidden (``shared_scale=True`` = one colour bar for all)

To use it on real data replace ``synth_panels`` with your own table: fixation x / y, duration (any unit), participant id and the stimulus
image of each panel (path, PIL image or array). State the export's convention once: ``units="px"|"norm"`` and
``origin="topleft"|"bottomleft"|"center"`` (and ``screen=(W, H)``). Passing ``participant`` gives every participant equal weight.
For one category of several images, pool all of its fixations and draw them on one representative image, and say so in the figure legend.

    python examples/gaze_heatmap_demo.py --lang zh --out ./out_gaze
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
from sportsci_figures.pubstyle import apply_style, save_figure, tr  # noqa: E402
from sportsci_figures.pubstyle import figures as pf  # noqa: E402
from sportsci_figures.pubstyle.figures_ext import category_colors  # noqa: E402

W, H = 1920, 1080


def synth_scene(seed: int) -> np.ndarray:
    """A neutral made-up stimulus: sky-to-ground gradient with a few blocks (not a real photograph)."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W]
    img = np.zeros((H, W, 3), float)
    img[..., 0] = 0.55 + 0.25 * yy / H
    img[..., 1] = 0.60 + 0.15 * yy / H
    img[..., 2] = 0.75 - 0.30 * yy / H
    for _ in range(6):
        x0, y0 = rng.integers(100, W - 500), rng.integers(300, H - 300)
        w, h = rng.integers(180, 420), rng.integers(150, 330)
        img[y0:y0 + h, x0:x0 + w] = rng.uniform(0.25, 0.55, 3)
    return img


def synth_panels(lang: str):
    rng = np.random.default_rng(11)
    names = ["节点", "区域", "标志物", "边界", "道路"] if lang == "zh" else ["Node", "District", "Landmark", "Edge", "Path"]
    cols = category_colors(len(names))
    panels = []
    for k, (nm, c) in enumerate(zip(names, cols)):
        n = int(rng.integers(1800, 3200))
        centres = rng.uniform([300, 250], [1600, 800], size=(3, 2))
        pick = rng.integers(0, 3, n)
        pts = centres[pick] + rng.normal(0, [170, 120], size=(n, 2))
        dur = rng.gamma(4.0, 60.0, n)
        pid = rng.integers(0, 45, n)                                    # 45 synthetic participants
        panels.append(dict(x=pts[:, 0], y=pts[:, 1], weights=dur, participant=pid, background=synth_scene(k), label=nm, label_color=c,
                           n_text="auto"))
    return panels


def run(lang: str, out: Path) -> Path:
    apply_style(lang)
    out.mkdir(parents=True, exist_ok=True)
    fig = pf.fig_gaze_heatmap_grid(synth_panels(lang), ncols=3)
    stem = out / "fig7_gaze_heatmap"
    save_figure(fig, stem, simulated=True)
    return stem.with_suffix(".png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=["zh", "en"], default="en")
    ap.add_argument("--out", default="out_gaze")
    a = ap.parse_args()
    print(run(a.lang, Path(a.out)))
