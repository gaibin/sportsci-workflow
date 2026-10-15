"""
pubstyle — publication-grade figures and tables in two fixed language sets (Chinese / English), one navy palette.

    from sportsci_figures.pubstyle import apply_style, save_figure, ResultsDoc
    from sportsci_figures.pubstyle import figures as pf

Workflow:  apply_style(lang) -> build figures with pf.* blocks -> save_figure() -> ResultsDoc(lang).
See SKILL.md, reference/STYLE_SPEC_ZH.md, reference/STYLE_SPEC_EN.md and examples/pubstyle_demo.py.
"""
from . import figures  # noqa: F401
from .report import ResultsDoc
from .style import (C_AMBER, C_CONTRAST, C_CONTROL, C_CORAL, C_GREY, C_INK, C_LIGHT, C_MAGENTA, C_MID, C_PRIMARY, C_SLATE, C_TEAL, DOUBLE, LANGS, PALETTE, SINGLE, STRINGS, apply_style, arm_colors, tr,
                    condition_colors, dose_colors, fmt_p, font_chain, get_lang, has_cjk_font, hair_y, panel_letter, panel_title, save_figure, sim_tag, t, verify_language, wrap_label)
from .tables import fmt_ci, fmt_msd, fmt_n_pct, fmt_num, fmt_p_table, save_tables_xlsx

__all__ = [
    "figures", "ResultsDoc", "apply_style", "save_figure", "panel_letter", "panel_title", "wrap_label", "hair_y", "sim_tag", "fmt_p", "t", "get_lang", "verify_language",
    "dose_colors", "condition_colors", "arm_colors", "font_chain", "has_cjk_font", "LANGS", "PALETTE", "SINGLE", "DOUBLE", "STRINGS",
    "C_PRIMARY", "C_CONTROL", "C_CONTRAST", "C_MAGENTA", "C_AMBER", "C_CORAL", "C_SLATE", "C_MID", "C_TEAL", "C_INK", "C_GREY", "C_LIGHT",
    "tr", "fmt_num", "fmt_msd", "fmt_ci", "fmt_p_table", "fmt_n_pct", "save_tables_xlsx",
]
