"""De-identification for participant data (used by `intake`).

  `pii_columns(df)`   finds identifying columns (name, phone, ID-card / passport / NRIC, student number, e-mail, address ...)
  `scrub_frame(df)`   drops them and replaces the participant ID with a stable pseudonym (P001, P002 ...)
  `redact(text)`      masks direct identifiers in free text (Chinese ID card / phone, Singapore NRIC/FIN, e-mail, long digit strings)

Keep the original -> pseudonym map with the raw files, never inside a deliverable. Disable `redact` only for debugging:
SPORTSCI_NO_REDACT=1.
"""
from __future__ import annotations

import os
import re
from typing import Dict, List, Tuple

import pandas as pd

# order matters: specific patterns first
_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("[身份证号]", re.compile(r"(?<![\d.])[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)")),
    ("[NRIC]", re.compile(r"\b[STFGM]\d{7}[A-Z]\b")),
    ("[邮箱]", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("[手机号]", re.compile(r"(?<![\d.])(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)")),
    ("[电话]", re.compile(r"(?<![\d.])(?:\+?65[- ]?)?[689]\d{3}[- ]?\d{4}(?!\d)")),
    ("[编号]", re.compile(r"(?<![\d.])\d{10,}(?![\d.])")),
]

# column-name fragments that identify a person (lower-cased match)
_PII_COL = re.compile(
    r"(姓名|名字|学生姓名|受试者姓名|^name$|full.?name|first.?name|last.?name|surname|"
    r"电话|手机|联系方式|phone|mobile|^tel$|telephone|"
    r"身份证|证件|id.?card|nric|passport|护照|"
    r"学号|工号|student.?(no|id|number)|"
    r"邮箱|e-?mail|住址|地址|address|微信|wechat|^qq)",
    re.I,
)


def redaction_enabled() -> bool:
    return os.environ.get("SPORTSCI_NO_REDACT") != "1"


def redact(text: str) -> str:
    """Mask direct identifiers in free text. Idempotent."""
    if not text or not redaction_enabled():
        return text
    for tag, pat in _PATTERNS:
        text = pat.sub(tag, text)
    return text


def pii_columns(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if _PII_COL.search(str(c).strip())]


def scrub_frame(df: pd.DataFrame, id_col: str | None = None) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Drop identifying columns; pseudonymise `id_col` (if given). Returns (clean frame, original->pseudonym map).

    Keep the map with the raw files, never inside a shared output.
    """
    out = df.drop(columns=[c for c in pii_columns(df) if c != id_col])
    mapping: Dict[str, str] = {}
    if id_col and id_col in out.columns:
        uniq = list(dict.fromkeys(out[id_col].astype(str)))
        mapping = {u: f"P{i + 1:03d}" for i, u in enumerate(uniq)}
        out[id_col] = out[id_col].astype(str).map(mapping)
    return out, mapping

