"""
DataProfiler — automatic column-role identification for arbitrary datasets.

Makes the pipeline discipline-agnostic: whether the user uploads a sport
physiology spreadsheet, a psychology scale dataset, or a humanities survey,
the profiler figures out which columns are:
  - the participant ID column
  - the group/condition column
  - pre/post measurement pairs (before/after, _pre/_post, _1/_2 ...)
  - standalone post-intervention outcome columns
No column names are hard-coded; all heuristics are deterministic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pandas as pd

_ID_HINTS = ["subject", "participant", "id", "case", "编号", "受试者", "被试", "参与者", "样本编号"]
_GROUP_HINTS = ["group", "condition", "arm", "cohort", "treatment", "组", "分组", "干预", "条件", "处理"]
_PRE_SUFFIX = re.compile(r"^(.*?)(?:_pre|_before|_base|_t0|_前测|_干预前)$", re.IGNORECASE)
_POST_SUFFIX = re.compile(r"^(.*?)(?:_post|_after|_t1|_后测|_干预后)$", re.IGNORECASE)
_PRE_PREFIX = re.compile(r"^(?:pre|前测|干预前)[_-]?(.*)$", re.IGNORECASE)
_POST_PREFIX = re.compile(r"^(?:post|后测|干预后)[_-]?(.*)$", re.IGNORECASE)
_TIME_SUFFIX = re.compile(r"^(.*?)[-_]?(?:t\d+|time\d+|w\d+)$", re.IGNORECASE)


@dataclass
class DataProfile:
    id_col: Optional[str] = None
    group_col: Optional[str] = None
    pre_post_pairs: List[Tuple[str, str]] = field(default_factory=list)
    post_only_outcomes: List[str] = field(default_factory=list)
    baseline_cols: List[str] = field(default_factory=list)  # covariates (pre columns)
    all_numeric: List[str] = field(default_factory=list)

    def summary(self) -> Dict[str, object]:
        return {
            "id_col": self.id_col,
            "group_col": self.group_col,
            "pre_post_pairs": [[p, q] for p, q in self.pre_post_pairs],
            "post_only_outcomes": self.post_only_outcomes,
            "baseline_cols": self.baseline_cols,
            "n_numeric_cols": len(self.all_numeric),
        }


def profile_dataframe(df: pd.DataFrame) -> DataProfile:
    profile = DataProfile()
    cols = list(df.columns)
    numeric_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    profile.all_numeric = numeric_cols

    # ---- 1. ID column -----------------------------------------------------
    for c in cols:
        cl = str(c).lower()
        if any(h in cl for h in _ID_HINTS):
            try:
                if df[c].nunique(dropna=True) >= max(2, len(df) * 0.8):
                    profile.id_col = str(c)
                    break
            except TypeError:
                continue

    # ---- 2. Group column --------------------------------------------------
    candidates: List[Tuple[int, str]] = []
    for c in cols:
        if c == profile.id_col:
            continue
        if not pd.api.types.is_numeric_dtype(df[c]):
            n_unique = df[c].nunique(dropna=True)
            if 2 <= n_unique <= 6:
                priority = 0
                cl = str(c).lower()
                if any(h in cl for h in _GROUP_HINTS):
                    priority = 2
                elif n_unique == 2:
                    priority = 1
                candidates.append((priority, str(c)))
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        profile.group_col = candidates[0][1]

    # ---- 3. Pre/post pairs ------------------------------------------------
    remaining = [c for c in cols if c not in (profile.id_col, profile.group_col) and c in numeric_cols]

    def match(col: str) -> Optional[str]:
        cl = str(col)
        for pat in (_PRE_SUFFIX, _POST_SUFFIX, _PRE_PREFIX, _POST_PREFIX, _TIME_SUFFIX):
            m = pat.match(cl)
            if m:
                return m.group(1)
        return None

    root_of: Dict[str, str] = {}
    for c in remaining:
        root = match(c)
        if root:
            root_of.setdefault(root, c)
        root_of.setdefault(c, c)

    # pair by shared root with a time-direction suffix
    pre_map: Dict[str, str] = {}
    post_map: Dict[str, str] = {}
    for c in remaining:
        cl = str(c)
        if _PRE_SUFFIX.match(cl) or _PRE_PREFIX.match(cl) or re.match(r"^(?:前测|干预前|pre)", cl, re.IGNORECASE):
            pre_map[cl] = cl
        elif _POST_SUFFIX.match(cl) or _POST_PREFIX.match(cl) or re.match(r"^(?:后测|干预后|post)", cl, re.IGNORECASE):
            post_map[cl] = cl

    # root-based pairing (x_pre ↔ x_post)
    used: set = set()
    for root, pre in pre_map.items():
        root_name = match(pre) or root
        post = None
        for pc in post_map:
            if (match(pc) or pc) == root_name and pc not in used:
                post = pc
                break
        if post:
            profile.pre_post_pairs.append((pre, post))
            used.add(pre)
            used.add(post)

    # fallback: generic numbered pairs (_1/_2) on the same root
    if not profile.pre_post_pairs:
        roots: Dict[str, List[str]] = {}
        for c in remaining:
            cl = str(c)
            m = re.match(r"^(.*?)[-_]?([12])$", cl)
            base = m.group(1) if m else cl
            roots.setdefault(base, []).append(cl)
        for base, group in roots.items():
            if len(group) >= 2 and base not in profile.group_col and base not in (profile.id_col or ""):
                sorted_cols = sorted(group)
                profile.pre_post_pairs.append((sorted_cols[0], sorted_cols[-1]))

    paired_cols = {c for pair in profile.pre_post_pairs for c in pair}
    profile.baseline_cols = [pre for pre, _ in profile.pre_post_pairs]

    # ---- 4. Remaining numeric columns as standalone outcomes ---------------
    for c in remaining:
        if c not in paired_cols:
            profile.post_only_outcomes.append(c)

    return profile
