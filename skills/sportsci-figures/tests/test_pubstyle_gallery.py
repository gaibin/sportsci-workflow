"""
Tests for the extended figure blocks (figures_ext) and the 26-data-type gallery.

  * numerical helpers behave (Kaplan-Meier, random-effects meta-analysis, ICC, AUC, bootstrap curve bands)
  * the whole gallery (30 figures, 26 data types) renders in the English set; the Chinese set renders when a CJK font exists
  * English figures never contain CJK text (save_figure raises); no missing-glyph warnings
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest

from sportsci_figures.pubstyle import apply_style, has_cjk_font
from sportsci_figures.pubstyle import figures as pf

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "examples" / "gallery" / "make_gallery.py"
OUT = ROOT / "outputs" / "gallery" / "figures"


def test_km_estimate_is_monotone_and_starts_at_one():
    rng = np.random.default_rng(0)
    t = rng.exponential(20, 100)
    e = (rng.random(100) < 0.7).astype(int)
    k = pf.km_estimate(t, e)
    assert k["s"][0] == 1.0 and np.all(np.diff(k["s"]) <= 1e-12)
    assert np.all(k["lo"] <= k["s"] + 1e-9) and np.all(k["hi"] >= k["s"] - 1e-9)


def test_meta_random_effects_pooled_inside_study_range():
    es = np.array([-0.9, -0.5, -0.7, -0.2, -0.6])
    se = np.array([0.2, 0.15, 0.25, 0.3, 0.2])
    r = pf.meta_random_effects(es, se)
    assert es.min() <= r["est"] <= es.max() and 0 <= r["I2"] <= 100 and abs(r["w"].sum() - 100) < 1e-6


def test_icc_and_auc_limits():
    x = np.linspace(10, 50, 40)
    assert pf.icc_2_1(x, x + 1e-9) > 0.999
    y = np.r_[np.zeros(30), np.ones(30)].astype(int)
    auc, lo, hi = pf.auc_ci(y, np.r_[np.linspace(0, 1, 30), np.linspace(2, 3, 30)], n_boot=50)
    assert auc == pytest.approx(1.0) and hi <= 1.0 + 1e-9


def test_fit_band_brackets_the_fit():
    rng = np.random.default_rng(1)
    x = np.repeat([0, 1, 3, 6, 9], 8).astype(float)
    y = 0.2 + 2 * x / (3 + x) + rng.normal(0, 0.3, len(x))
    g, fit, lo, hi = pf.fit_band(x, y, "emax", n_boot=100)
    assert len(g) == len(fit) == len(lo) == len(hi) and np.all(lo <= hi + 1e-9)


def test_raincloud_and_bland_altman_draw_without_error():
    apply_style("en")
    rng = np.random.default_rng(2)
    fig, axs = plt.subplots(1, 2)
    pf.ax_raincloud(axs[0], {"A": rng.normal(0, 1, 30), "B": rng.normal(1, 1, 30)}, {"A": "#F0B41E", "B": "#A51E87"}, "y")
    b, lo, hi = pf.ax_bland_altman(axs[1], rng.normal(50, 5, 40), rng.normal(50, 5, 40), "mean", "diff")
    assert lo < b < hi
    plt.close(fig)


def _run(args):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, str(GALLERY)] + args, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, cwd=str(ROOT), timeout=900)


@pytest.fixture(scope="module")
def gallery_en():
    r = _run(["--lang", "en"])
    return r


def test_gallery_english_runs_clean(gallery_en):
    assert gallery_en.returncode == 0, gallery_en.stderr[-800:]
    assert "failed" not in gallery_en.stdout, gallery_en.stdout[-800:]
    assert "missing from font" not in gallery_en.stderr


def test_gallery_covers_26_data_types_and_30_figures(gallery_en):
    domains = sorted(p.name for p in (OUT / "en").glob("D*"))
    pngs = list((OUT / "en").glob("D*/*.png"))
    pdfs = list((OUT / "en").glob("D*/*.pdf"))
    assert len(domains) == 26 and len(pngs) == 30 and len(pdfs) == 30


@pytest.mark.skipif(not has_cjk_font(), reason="no CJK font installed")
def test_gallery_chinese_runs_clean(gallery_en):
    r = _run(["--lang", "zh", "--no-sim"])
    assert r.returncode == 0 and "failed" not in r.stdout, (r.stdout + r.stderr)[-800:]
    assert "missing from font" not in r.stderr
    assert len(list((OUT / "zh").glob("D*/*.png"))) == 30


def test_questionnaire_blocks_draw():
    apply_style("en")
    fig = plt.figure()
    pf.ax_likert(fig.add_subplot(2, 2, 1), ["q1", "q2"], np.array([[5, 15, 20, 40, 20], [10, 10, 30, 30, 20]]), ["SD", "D", "N", "A", "SA"])
    pf.ax_corr_heatmap(fig.add_subplot(2, 2, 2), np.eye(3), ["a", "b", "c"])
    pf.ax_radar(fig.add_subplot(2, 2, 3, projection="polar"), ["x", "y", "z"], {"g": [1, 2, 3]}, {"g": "#A51E87"}, 4)
    pf.ax_mediation(fig.add_subplot(2, 2, 4), ("X", "M", "Y"), "1", "2", "3", "4", "5")
    plt.close(fig)
