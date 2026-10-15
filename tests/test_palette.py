"""One navy palette: fixed role colours, ordered ramps that survive grayscale printing, no off-palette colours in the library."""
import sys
from pathlib import Path

import numpy as np
import pytest
from matplotlib.colors import LinearSegmentedColormap, to_rgb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sportsci_figures import pubstyle as ps  # noqa: E402
from sportsci_figures.pubstyle import figures as pf  # noqa: E402
from sportsci_figures.pubstyle import style as st  # noqa: E402

OFF_PALETTE = ("#A51E87", "#F0B41E", "#E1695A", "#7D82B8", "#C34370", "#0E6251", "#1F77B4", "#FF7F0E")   # magenta / amber / matplotlib defaults


def _lum(h):
    r, g, b = to_rgb(h)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def test_role_colours_are_navy_sand_terracotta():
    assert st.C_PRIMARY == "#112378" and st.C_CONTROL == "#C9A66B" and st.C_CONTRAST == "#C4573F"
    assert st.PALETTE[0] == st.C_PRIMARY and ps.C_MAGENTA == ps.C_PRIMARY          # legacy names are aliases of the roles


def test_dose_ramp_is_monotone_in_lightness():
    for n in (2, 3, 5):
        lum = [_lum(c) for c in ps.dose_colors(n)]
        assert all(a > b for a, b in zip(lum, lum[1:])), (n, lum)                    # survives grayscale printing
    assert ps.dose_colors(1) == [st.C_PRIMARY]


def test_colormaps_end_on_the_primary_colour():
    assert isinstance(pf.DIVERGING, LinearSegmentedColormap)
    assert np.allclose(to_rgb("#112378"), pf.DIVERGING(1.0)[:3], atol=0.01)
    assert not isinstance(pf.SEQ, LinearSegmentedColormap)                           # ax_heatmap keeps non-symmetric limits for sequential maps
    import inspect
    assert inspect.signature(pf.ax_heatmap).parameters["cmap"].default is pf.DIVERGING


def test_apply_style_sets_ink_colour():
    import matplotlib
    ps.apply_style("en")
    assert matplotlib.rcParams["text.color"] == "#161A26"


def test_no_off_palette_colour_in_library():
    """Hard-coded colours outside the navy palette must not appear in the library or the results engine."""
    hits = []
    for folder in ("sportsci_figures/pubstyle", "sportsci_figures/results"):
        for f in (ROOT / folder).rglob("*.py"):
            txt = f.read_text(encoding="utf-8").upper()
            hits += [(f.name, h) for h in OFF_PALETTE if h in txt]
    assert not hits, hits


def test_hand_written_matplotlib_also_comes_out_navy():
    """Safety net for data shapes without a pubstyle block: default colour cycle and colour map follow the palette."""
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_hex
    matplotlib.use("Agg")
    ps.apply_style("en")
    fig, ax = plt.subplots()
    l1, = ax.plot([0, 1], [0, 1])
    l2, = ax.plot([0, 1], [1, 0])
    im = ax.imshow(np.random.default_rng(0).random((3, 3)))
    assert to_hex(l1.get_color()).upper() == "#112378" and to_hex(l2.get_color()).upper() == "#C9A66B"
    assert im.get_cmap().name == "navy_seq"
    plt.close(fig)
