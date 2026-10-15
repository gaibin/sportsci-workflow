"""
pubstyle.style — one global style for publication figures, in two language sets.

    from sportsci_figures.pubstyle import apply_style
    apply_style("zh")     # Chinese labels / captions / tables
    apply_style("en")     # English-only labels / captions / tables

Call ``apply_style(lang)`` ONCE, BEFORE creating any figure. Everything else in
``pubstyle`` (figures, tables, docx) reads the active language from here.

Design rules implemented here (see reference/STYLE_SPEC_*.md for the full text):
  * no top/right spines, ticks outward, 0.75 pt axes, no grey default grid
  * fixed semantic colour roles on a single navy / sand / terracotta palette
  * Arial for Latin text; CJK glyphs fall back per character (zh set only)
  * 300 dpi PNG + vector PDF with embedded TrueType (fonttype 42)
  * every figure can carry a fixed "Simulated data" tag
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

import matplotlib

matplotlib.use("Agg", force=False)
import matplotlib.pyplot as plt
import numpy as np
from cycler import cycler
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, to_hex, to_rgb

LANGS = ("zh", "en")
_ACTIVE = {"lang": "en"}

# ----------------------------------------------------------------------------- palette
# ONE palette (navy). Colour *roles* are fixed: intervention = navy, control = sand (dashed for lines), contrast / harm = terracotta.
_P: Dict[str, str] = dict(
    primary="#112378", control="#C9A66B", contrast="#C4573F", slate="#8E98C6", mid="#3F4F9E", teal="#2F6F73",
    ink="#161A26", grey="#626778", light="#D5D2CA", hair="#E0DDD5", band="#EEEBE4", band_cool="#E3E6F3",
    dose_low="#9BA5D3", blue="#4F8FB0", violet="#6B5B8C", brown="#8C6D31", paper="#F6F5F1",
    pale_slate="#B3BAD6", pale_slate2="#C3CAE3", pale_contrast="#E5B6A8", gold_dark="#7A5F2B", gold_mid="#8F6F32")

C_PRIMARY = _P["primary"]      # intervention / highest dose / primary outcome
C_CONTROL = _P["control"]      # control / baseline / reference condition (dashed for lines)
C_CONTRAST = _P["contrast"]    # contrast category / harm
C_SLATE = _P["slate"]          # reference, baseline visit, neutral composition
C_MID = _P["mid"]              # middle dose
C_TEAL = _P["teal"]            # 4th category colour (e.g. function outcomes)
C_INK = _P["ink"]              # text and error bars
C_GREY = _P["grey"]            # annotations
C_LIGHT = _P["light"]          # individual-subject lines, hairline grid
C_HAIR = _P["hair"]            # separators
C_BAND = _P["band"]            # target-range shading
C_BAND_COOL = _P["band_cool"]  # cool band (results-engine plots)
C_DOSE_LOW = _P["dose_low"]    # lowest end of the ordered dose ramp
C_PALE_SLATE, C_PALE_SLATE2, C_PALE_CONTRAST = _P["pale_slate"], _P["pale_slate2"], _P["pale_contrast"]
C_GOLD_DARK, C_GOLD_MID = _P["gold_dark"], _P["gold_mid"]   # text colours that sit next to the control colour
C_PAPER = _P["paper"]          # neutral centre of the diverging scale
# Legacy names (kept so existing scripts keep working; they now mean the *role*, not a fixed hue)
C_MAGENTA, C_AMBER, C_CORAL = C_PRIMARY, C_CONTROL, C_CONTRAST

PALETTE = [C_PRIMARY, C_CONTROL, C_CONTRAST, C_SLATE, _P["blue"], C_TEAL, "#333333"]

_SEQ_COLORS = [_P["paper"], _P["pale_slate2"], "#6677BE", _P["primary"], "#0C1545"]


def make_cmaps():
    """(sequential, diverging) colour maps. Sequential is a ListedColormap, diverging a LinearSegmentedColormap
    (figures_ext.ax_heatmap relies on that difference to pick symmetric limits)."""
    seq = ListedColormap(LinearSegmentedColormap.from_list("seq", _SEQ_COLORS)(np.linspace(0, 1, 256)), name="navy_seq")
    div = LinearSegmentedColormap.from_list("navy_div", [_P["contrast"], _P["paper"], _P["primary"]])
    return seq, div


SEQ_CMAP, DIVERGING_CMAP = make_cmaps()
matplotlib.colormaps.register(SEQ_CMAP, name="navy_seq", force=True)        # so rcParams["image.cmap"] can name it
matplotlib.colormaps.register(DIVERGING_CMAP, name="navy_div", force=True)

SINGLE = 3.5   # inches, one Nature column (89 mm)
DOUBLE = 7.2   # inches, two columns (183 mm)

_CONTROL_HINTS = ("control", "对照", "placebo", "安慰剂", "sham", "假刺", "baseline", "基线", "waitlist", "等待", "con", "usual")


def dose_colors(n: int) -> List[str]:
    """Ordered colour ramp (light periwinkle -> deep navy) for n ordered doses/conditions (n >= 1).

    Lightness decreases monotonically, so the order survives grayscale printing
    and colour-vision deficiency.
    """
    if n == 1:
        return [C_PRIMARY]
    a, b = np.array(to_rgb(C_DOSE_LOW)), np.array(to_rgb(C_PRIMARY))
    return [to_hex(a + (b - a) * i / (n - 1)).upper() for i in range(n)]


def condition_colors(order: Sequence[str]) -> Dict[str, str]:
    """Semantic colours for an ordered list of conditions.

    Control-like names (CON, control, placebo, baseline, ...) -> control colour; the remaining
    conditions get the dose ramp in the order given (low -> high dose).
    """
    ctrl = [c for c in order if str(c).lower() in _CONTROL_HINTS or any(h in str(c).lower() for h in _CONTROL_HINTS[:7])]
    act = [c for c in order if c not in ctrl]
    ramp = dose_colors(max(len(act), 1))
    out = {c: C_CONTROL for c in ctrl}
    out.update({c: ramp[i] for i, c in enumerate(act)})
    return out


def arm_colors(control: str, intervention: str) -> Dict[str, str]:
    return {control: C_CONTROL, intervention: C_PRIMARY}


# ----------------------------------------------------------------------------- strings
STRINGS: Dict[str, Dict[str, str]] = {
    "zh": {
        "simulated": "模拟数据 · Simulated data", "baseline": "基线", "post": "干预后", "week": "第{n}周", "control": "对照组", "intervention": "干预组",
        "n": "n = {n}", "mean_sd": "均值 ± SD", "mean_sem": "均值 ± SEM", "ci95": "95% CI", "diff": "差值", "time": "时间", "hours": "h",
        "figure": "图", "table": "表", "p": "P", "q": "q", "effect_size": "标准化效应量", "better": "获益方向", "ctrl_better": "← 对照组更优", "int_better": "干预组更优 →",
        "indiv": "个体", "group_mean": "组均值", "target_range": "目标范围", "model_est": "模型估计", "unadjusted": "未校正", "adherence": "依从性 (%)",
        "variable": "变量", "total": "全体", "outcome": "结局", "estimate": "估计值", "compare": "对比", "sig_fill": "实心 = 校正后显著",
        "disclaimer": "【模拟数据声明】本节全部结果由模拟数据计算得到，用于检验研究流程与科研工具的可靠性，不代表任何真实受试者的观察结果，不得引用为研究证据。",
    },
    "en": {
        "simulated": "Simulated data", "baseline": "Baseline", "post": "Post", "week": "Week {n}", "control": "Control", "intervention": "Intervention",
        "n": "n = {n}", "mean_sd": "Mean ± SD", "mean_sem": "Mean ± SEM", "ci95": "95% CI", "diff": "Difference", "time": "Time", "hours": "h",
        "figure": "Figure", "table": "Table", "p": "P", "q": "q", "effect_size": "Standardised effect size", "better": "Favourable direction",
        "ctrl_better": "← Favours control", "int_better": "Favours intervention →",
        "indiv": "Individual", "group_mean": "Group mean", "target_range": "Target range", "model_est": "Model estimate", "unadjusted": "unadjusted", "adherence": "Adherence (%)",
        "variable": "Variable", "total": "All", "outcome": "Outcome", "estimate": "Estimate", "compare": "Contrast", "sig_fill": "Filled = significant after adjustment",
        "disclaimer": "[Simulated-data notice] All results in this section were computed from simulated data to test the research workflow and tooling. "
                      "They do not represent observations from real participants and must not be cited as evidence.",
    },
}


def t(key: str, lang: Optional[str] = None, **kw) -> str:
    lang = lang or _ACTIVE["lang"]
    s = STRINGS[lang].get(key, STRINGS["en"].get(key, key))
    return s.format(**kw) if kw else s


def get_lang() -> str:
    return _ACTIVE["lang"]


def tr(zh: str, en: str) -> str:
    """Pick the string of the active language set: tr("血糖", "Glucose"). Use for every label so one script serves both sets."""
    return zh if _ACTIVE["lang"] == "zh" else en


# ----------------------------------------------------------------------------- fonts / rcParams
_LATIN = {"zh": ["Arial", "Helvetica", "Liberation Sans"],
          "en": ["Arial", "Helvetica", "Liberation Sans", "Nimbus Sans", "DejaVu Sans"]}
_CJK = ["Microsoft YaHei", "SimHei", "PingFang SC", "Heiti SC", "Noto Sans CJK SC", "Source Han Sans SC", "WenQuanYi Micro Hei", "SimSun"]


def _installed() -> set:
    return {f.name for f in fm.fontManager.ttflist}


def font_chain(lang: str) -> List[str]:
    """Installed fonts only (matplotlib warns noisily about missing families)."""
    have = _installed()
    chain = [f for f in _LATIN[lang] if f in have]
    if lang == "zh":
        chain += [f for f in _CJK if f in have]
    chain.append("DejaVu Sans")      # ships with matplotlib: last-resort glyphs (subscripts ₀₁₂, Greek, arrows) missing from Arial / CJK fonts
    return chain


def has_cjk_font() -> bool:
    have = _installed()
    return any(f in have for f in _CJK)


def apply_style(lang: str = "zh") -> None:
    """Activate the publication style for ``lang`` ('zh' or 'en'). Call before creating figures."""
    if lang not in LANGS:
        raise ValueError(f"lang must be one of {LANGS}, got {lang!r}")
    _ACTIVE["lang"] = lang
    matplotlib.rcParams.update({
        # NOTE: a *list* in font.family gives per-glyph fallback (Latin -> Arial, Chinese -> CJK font).
        # Do NOT write family='sans-serif' + a long font.sans-serif list: Latin text would then use the CJK font.
        "font.family": font_chain(lang),
        "axes.unicode_minus": lang == "en",
        "mathtext.fontset": "dejavusans",
        "font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5,
        "axes.linewidth": 0.75, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
        "xtick.direction": "out", "ytick.direction": "out", "xtick.major.size": 3, "ytick.major.size": 3,
        "xtick.major.width": 0.75, "ytick.major.width": 0.75, "xtick.major.pad": 2, "ytick.major.pad": 2,
        "lines.linewidth": 1.2, "legend.frameon": False,
        "figure.dpi": 150, "savefig.dpi": 300, "savefig.pad_inches": 0.04,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        # safety net: even hand-written matplotlib code (no pubstyle block) comes out in the navy palette, never tab:blue / viridis
        "axes.prop_cycle": cycler(color=PALETTE), "image.cmap": "navy_seq",
        "text.color": C_INK, "axes.labelcolor": C_INK, "axes.edgecolor": C_INK, "xtick.color": C_INK, "ytick.color": C_INK, "axes.titlecolor": C_INK,
    })


# ----------------------------------------------------------------------------- small helpers
def panel_letter(ax, s: str, dx: float = -0.02, dy: float = 1.04) -> None:
    """Bold lowercase panel label (a, b, c ...) at the upper-left of the axes."""
    ax.text(dx, dy, s, transform=ax.transAxes, ha="left", va="bottom", fontsize=9, fontweight="bold", color="black")


def panel_title(ax, letter: str, title: str = "", dx: float = -0.02, dy: float = 1.04, size: float = 7.2) -> None:
    """Bold panel letter followed by a short panel title on the same baseline ("a  Individual trajectories").

    Keep titles to a few words; details belong in the caption. Without a title this equals ``panel_letter``.
    """
    panel_letter(ax, letter, dx, dy)
    if title:
        ax.annotate(title, xy=(dx, dy), xycoords="axes fraction", xytext=(10.5, 0.6), textcoords="offset points",
                    ha="left", va="bottom", fontsize=size, color=C_INK)


def wrap_label(s: str, width: int = 10, cjk_width: int = 5) -> str:
    """Break a long tick label onto two lines: CJK labels longer than ``cjk_width`` characters in the middle,
    Latin labels longer than ``width`` at the space nearest the middle."""
    s = str(s)
    if "\n" in s:
        return s
    if _CJK_RE.search(s):
        if len(s) <= cjk_width:
            return s
        k = (len(s) + 1) // 2
        return s[:k] + "\n" + s[k:]
    if len(s) <= width or " " not in s:
        return s
    mid = len(s) // 2
    cut = min((i for i, ch in enumerate(s) if ch == " "), key=lambda i: abs(i - mid))
    return s[:cut] + "\n" + s[cut + 1:]


def hair_y(ax) -> None:
    """The only grid allowed: faint dotted horizontal hairlines."""
    ax.grid(axis="y", linestyle=":", linewidth=0.5, color=C_LIGHT, alpha=0.9)
    ax.set_axisbelow(True)


def sim_tag(fig, y: float = -0.014) -> None:
    fig.text(0.995, y, t("simulated"), ha="right", va="bottom", fontsize=5, color="#9CA3AF", style="italic")


def fmt_p(p: Optional[float], with_label: bool = True) -> str:
    """'P < 0.001' or 'P = 0.012'. Never 'P = 0.000', never '= <'."""
    if p is None or not np.isfinite(p):
        return "—"
    body = "< 0.001" if p < 0.001 else f"= {p:.3f}"
    return f"P {body}" if with_label else body.replace("= ", "")


_CJK_RE = re.compile(r"[㐀-鿿　-〿＀-￯]")


def figure_texts(fig) -> List[str]:
    out = []
    for artist in fig.findobj(matplotlib.text.Text):
        s = artist.get_text()
        if s and s.strip():
            out.append(s)
    return out


def verify_language(fig, lang: Optional[str] = None) -> List[str]:
    """Return offending strings. For 'en': any CJK character is an error."""
    lang = lang or _ACTIVE["lang"]
    if lang != "en":
        return []
    return [s for s in figure_texts(fig) if _CJK_RE.search(s)]


def save_figure(fig, out_stem: str | Path, simulated: bool = True, formats: Iterable[str] = ("png", "pdf"), dpi: int = 300) -> List[Path]:
    """Save PNG (300 dpi) + vector PDF. Raises if an English figure contains CJK text."""
    bad = verify_language(fig)
    if bad:
        raise ValueError(f"English figure contains CJK text: {bad[:5]}")
    if simulated:
        sim_tag(fig)
    out_stem = Path(out_stem)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in formats:
        p = out_stem.with_suffix(f".{ext}")
        fig.savefig(p, dpi=dpi, bbox_inches="tight") if ext == "png" else fig.savefig(p, bbox_inches="tight")
        paths.append(p)
    plt.close(fig)
    return paths
