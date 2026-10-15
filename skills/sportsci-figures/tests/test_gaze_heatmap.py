"""Eye-tracking blocks: gaze_density, ax_gaze_heatmap, fig_gaze_heatmap_grid (pubstyle.figures_ext).

The contract under test is *universality*: the same fixations must give the same picture and the same numbers whatever the export
convention, the screen resolution, the weight unit, the company they keep, or who contributed how many fixations.
"""
import importlib.util
import sys
import warnings
from pathlib import Path

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sportsci_figures.pubstyle import apply_style, has_cjk_font, verify_language  # noqa: E402
from sportsci_figures.pubstyle import figures as pf  # noqa: E402

W, H = 1920, 1080


def _cloud(n=400, centre=(600, 400), sd=60, seed=0):
    rng = np.random.default_rng(seed)
    return rng.normal(centre[0], sd, n), rng.normal(centre[1], sd, n)


def _width_px(z, cx, cy):
    """Full width at half of the local peak along x through (cx, cy)."""
    gx, gy = z.shape[1], z.shape[0]
    ix, iy = int(cx / W * (gx - 1)), int(cy / H * (gy - 1))
    row = z[iy]
    pk = row[max(0, ix - 6): ix + 7].max()
    above = np.where(row >= pk / 2)[0]
    seg = above[(above > ix - 20) & (above < ix + 20)]
    return (seg.max() - seg.min() + 1) * W / gx


# ------------------------------------------------------------------------------------------------------- density

def test_density_peak_is_at_the_cluster_and_follows_weights():
    x, y = _cloud()
    z = pf.gaze_density(x, y)
    assert z.shape == (108, 192) and (z >= 0).all()
    iy, ix = np.unravel_index(np.argmax(z), z.shape)
    assert abs(ix * W / 191 - 600) < 120 and abs(iy * H / 107 - 400) < 120
    x2, y2 = np.r_[x, 1500.0], np.r_[y, 800.0]
    w = np.r_[np.ones_like(x), 5000.0 * np.ones(1)]
    z2 = pf.gaze_density(x2, y2, w)
    assert np.unravel_index(np.argmax(z2), z2.shape)[1] > ix


def test_too_few_points_gives_zeros_and_offscreen_or_nan_are_dropped_and_counted():
    assert not pf.gaze_density([10, 20], [10, 20]).any()
    x, y = _cloud()
    info = {}
    z_out = pf.gaze_density(np.r_[x, -50, 4000, np.nan], np.r_[y, 10, 10, 10], info=info)
    assert np.allclose(pf.gaze_density(x, y), z_out)
    assert info["n_offscreen"] == 2 and info["n_nonfinite"] == 1 and info["n_used"] == 400


def test_identical_points_give_one_smooth_blob_not_nothing():
    z = pf.gaze_density([500] * 4, [300] * 4)
    assert z.max() > 1 and abs(z.mean() - 1) < 1e-9


def test_density_is_relative_to_an_even_spread():
    x, y = _cloud()
    assert abs(pf.gaze_density(x, y).mean() - 1.0) < 1e-9
    rng = np.random.default_rng(3)
    z = pf.gaze_density(rng.uniform(0, W, 20000), rng.uniform(0, H, 20000))
    assert abs(np.median(z) - 1.0) < 0.1                       # an even spread is ~1 everywhere


def test_hot_spot_width_does_not_depend_on_the_rest_of_the_data():
    rng = np.random.default_rng(1)
    hot = np.c_[rng.normal(500, 60, 600), rng.normal(300, 60, 600)]
    alone = pf.gaze_density(hot[:, 0], hot[:, 1])
    noise = np.c_[rng.uniform(100, 1800, 3000), rng.uniform(100, 1000, 3000)]
    mixed = pf.gaze_density(np.r_[hot[:, 0], noise[:, 0]], np.r_[hot[:, 1], noise[:, 1]])
    assert abs(_width_px(alone, 500, 300) - _width_px(mixed, 500, 300)) <= 20


def test_same_picture_for_every_export_convention():
    rng = np.random.default_rng(2)
    x, y = rng.normal(700, 150, 500), rng.normal(450, 110, 500)
    ref = pf.gaze_density(x, y)
    assert np.allclose(pf.gaze_density(x / W, y / H, units="norm"), ref)
    assert np.allclose(pf.gaze_density(x, H - y, origin="bottomleft"), ref)
    assert np.allclose(pf.gaze_density(x - W / 2, H / 2 - y, origin="center"), ref)
    s = 1280 / 1920                                               # same viewing on a smaller screen
    z720 = pf.gaze_density(x * s, y * s, screen=(1280, 720))
    assert np.allclose(z720, ref, atol=1e-6)
    d = np.full(500, 250.0)                                       # ms vs s
    assert np.allclose(pf.gaze_density(x, y, d), pf.gaze_density(x, y, d / 1000.0))


def test_px_values_that_look_normalised_are_refused():
    x, y = _cloud()
    with pytest.raises(ValueError, match="normalised"):
        pf.gaze_density(x / W, y / H)
    with pytest.raises(ValueError):
        pf.gaze_density(x, y, units="cm")
    with pytest.raises(ValueError):
        pf.gaze_density(x, y, origin="topright")


def test_participants_carry_equal_weight():
    rng = np.random.default_rng(5)
    a = np.c_[rng.normal(400, 50, 2000), rng.normal(300, 50, 2000)]       # one participant, very long
    b = np.c_[rng.normal(1400, 50, 450), rng.normal(700, 50, 450)]        # nine participants
    x, y = np.r_[a[:, 0], b[:, 0]], np.r_[a[:, 1], b[:, 1]]
    pid = np.r_[np.zeros(2000, int), np.repeat(np.arange(1, 10), 50)]

    def share_near_a(z):
        c = (np.arange(z.shape[1]) + 0.5) / z.shape[1] * W
        return z[:, (c >= 250) & (c <= 550)].sum() / z.sum()

    assert share_near_a(pf.gaze_density(x, y)) > 0.7
    assert abs(share_near_a(pf.gaze_density(x, y, participant=pid)) - 0.10) < 0.02


# ---------------------------------------------------------------------------------------------------------- axes

def test_ax_returns_image_and_vmax_and_english_has_no_cjk():
    apply_style("en")
    x, y = _cloud()
    fig, ax = plt.subplots()
    bg = np.full((1080, 1920, 3), 0.5)
    im, vm = pf.ax_gaze_heatmap(ax, x, y, weights=np.full_like(x, 250.0), background=bg, label="Path", n_text="auto")
    assert vm > 0 and im.get_cmap().name == pf.GAZE_CMAP
    assert abs(im.get_alpha() - 0.45) < 1e-9
    assert verify_language(fig) == []
    texts = [t.get_text() for t in ax.texts]
    assert "400 fixations" in texts
    plt.close(fig)


def test_chinese_set_uses_chinese_labels_and_counts():
    if not has_cjk_font():
        pytest.skip("no CJK font")
    apply_style("zh")
    x, y = _cloud()
    pid = np.arange(400) % 8
    fig, ax = plt.subplots()
    pf.ax_gaze_heatmap(ax, x, y, participant=pid, n_text="auto")
    assert any("相对注视密度" in a.get_ylabel() for a in fig.axes)
    assert "8 名被试 · 400 个注视点" in [t.get_text() for t in ax.texts]
    plt.close(fig)


def test_too_few_fixations_says_so_instead_of_drawing_a_blank_scale():
    apply_style("en")
    fig, ax = plt.subplots()
    pf.ax_gaze_heatmap(ax, [10, 20], [10, 20])
    assert any("too few" in t.get_text() for t in ax.texts) and len(fig.axes) == 1     # no colour bar
    plt.close(fig)


def test_offscreen_share_raises_a_warning_with_the_likely_causes():
    apply_style("en")
    x, y = _cloud(n=300)
    fig, ax = plt.subplots()
    with pytest.warns(UserWarning, match="screen, units and origin"):
        pf.ax_gaze_heatmap(ax, x + 3000, y)
    plt.close(fig)
    fig, ax = plt.subplots()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        pf.ax_gaze_heatmap(ax, x, y)                              # nothing off screen: silent
    plt.close(fig)


def test_stimulus_box_crops_to_the_displayed_image_and_keeps_its_proportions():
    apply_style("en")
    rng = np.random.default_rng(4)
    box = (240, 0, 1680, 1080)                                    # 4:3 image centred on a 16:9 screen
    x, y = rng.normal(960, 120, 500), rng.normal(540, 90, 500)
    fig, ax = plt.subplots()
    pf.ax_gaze_heatmap(ax, x, y, background=np.full((960, 1280, 3), 0.4), stimulus_box=box, n_text="auto")
    assert ax.get_xlim() == (0.0, 1440.0) and ax.get_ylim() == (1080.0, 0.0)
    assert "500 fixations" in [t.get_text() for t in ax.texts]
    plt.close(fig)


# --------------------------------------------------------------------------------------------------------- grid

def test_grid_hides_unused_cells_and_demo_renders_in_both_sets(tmp_path):
    apply_style("en")
    panels = [dict(x=_cloud(seed=i)[0], y=_cloud(seed=i)[1], label=f"P{i}") for i in range(5)]
    fig = pf.fig_gaze_heatmap_grid(panels, ncols=3)
    assert len([ax for ax in fig.axes if ax.get_visible() and ax.images]) == 5
    plt.close(fig)
    spec = importlib.util.spec_from_file_location("gaze_heatmap_demo", ROOT / "examples" / "gaze_heatmap_demo.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for lang in (["zh", "en"] if has_cjk_font() else ["en"]):
        png = mod.run(lang, tmp_path / lang)
        assert png.exists() and png.with_suffix(".pdf").exists() and png.stat().st_size > 20000


def test_shared_scale_uses_one_vmax_and_one_colour_bar():
    apply_style("en")
    panels = [dict(x=_cloud(seed=0, sd=40)[0], y=_cloud(seed=0, sd=40)[1]), dict(x=_cloud(seed=1, sd=250)[0], y=_cloud(seed=1, sd=250)[1])]
    fig = pf.fig_gaze_heatmap_grid(panels, ncols=2, shared_scale=True)
    ims = [im for ax in fig.axes for im in ax.images if im.get_cmap().name == pf.GAZE_CMAP]
    assert len({round(im.get_clim()[1], 6) for im in ims}) == 1
    assert len(fig.axes) == 3                                      # two panels + ONE colour bar
    plt.close(fig)
    fig = pf.fig_gaze_heatmap_grid(panels, ncols=2)
    assert len(fig.axes) == 4                                      # default: a colour bar per panel
    plt.close(fig)


def test_same_data_same_picture_regardless_of_other_panels():
    apply_style("en")
    a = dict(x=_cloud(seed=0)[0], y=_cloud(seed=0)[1])
    f1 = pf.fig_gaze_heatmap_grid([a], ncols=1)
    f2 = pf.fig_gaze_heatmap_grid([a, dict(x=_cloud(seed=9, sd=300)[0], y=_cloud(seed=9, sd=300)[1])], ncols=2)
    i1 = [im for im in f1.axes[0].images if im.get_cmap().name == pf.GAZE_CMAP][0]
    i2 = [im for im in f2.axes[0].images if im.get_cmap().name == pf.GAZE_CMAP][0]
    assert np.allclose(i1.get_array(), i2.get_array()) and i1.get_clim() == i2.get_clim()
    plt.close("all")
