# -*- coding: utf-8 -*-
"""Gallery infrastructure: paths, data dictionaries, one save() for both language sets."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Tuple

SKILL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL))

import numpy as np
import pandas as pd

from sportsci_figures.pubstyle.style import apply_style, save_figure

# Default: <skill>/outputs/gallery/{data/<domain>/*.csv, figures/<lang>/<domain>/*.png|pdf}.
# Override (e.g. to write into a project folder with other directory names) with environment variables:
#   GALLERY_OUT=<root>  GALLERY_DATA_DIR=<name>  GALLERY_FIG_DIR=<name>  GALLERY_LANG_DIRS=<zh-name>,<en-name>
ROOT = Path(os.environ.get("GALLERY_OUT", SKILL / "outputs" / "gallery"))
DATA = ROOT / os.environ.get("GALLERY_DATA_DIR", "data")
RES = ROOT / os.environ.get("GALLERY_FIG_DIR", "figures")
_zh, _en = os.environ.get("GALLERY_LANG_DIRS", "zh,en").split(",")
LANG_DIR = {"zh": _zh, "en": _en}
DATA.mkdir(exist_ok=True, parents=True)


def ddir(code: str) -> Path:
    p = DATA / code
    p.mkdir(exist_ok=True, parents=True)
    return p


def read(code: str, name: str, **kw) -> pd.DataFrame:
    return pd.read_csv(DATA / code / name, **kw)


def save(fig, code: str, name: str, lang: str) -> None:
    save_figure(fig, RES / LANG_DIR[lang] / code / name)


def write_readme(code: str, title_zh: str, title_en: str, desc: str, files: Dict[str, Tuple[str, str, Dict[str, Tuple[str, str]]]]) -> None:
    """files: filename -> (zh description, en description, {column: (zh, en)})"""
    lines = [f"# {code}  {title_zh} / {title_en}", "", desc, "", "> Simulated data (simulated data), for testing figure/analysis workflows only.", ""]
    for fn, (zh, en, cols) in files.items():
        lines += [f"## {fn}", f"{zh}  ", f"{en}", "", "| Column | zh | en |", "|---|---|---|"]
        lines += [f"| `{c}` | {a} | {b} |" for c, (a, b) in cols.items()]
        lines.append("")
    (ddir(code) / "README.md").write_text("\n".join(lines), encoding="utf-8")


def wilson(k: int, n: int, z: float = 1.96) -> Tuple[float, float, float]:
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, c - h, c + h
