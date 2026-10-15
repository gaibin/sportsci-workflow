"""
pubstyle.tables — number formatting and Excel export for result tables.

Formatting rules (identical in both languages):
  * continuous variables  ->  mean ± SD   (SD, not SE, in descriptive tables)
  * estimates             ->  estimate (95% CI lower, upper)
  * P values              ->  "<0.001" or three decimals; never "0.000"
  * digits adapt to magnitude: |x| < 10 -> 2 dp, < 100 -> 1 dp, otherwise 0 dp (override with nd=)
  * missing values        ->  an em dash "—"
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd


def fmt_num(x, nd: Optional[int] = None) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    if nd is None:
        a = abs(x)
        nd = 2 if a < 10 else (1 if a < 100 else 0)
    return f"{x:.{nd}f}"


def fmt_msd(x, nd: Optional[int] = None) -> str:
    s = pd.Series(x).dropna()
    if len(s) == 0:
        return "—"
    return f"{fmt_num(s.mean(), nd)} ± {fmt_num(s.std(ddof=1), nd)}"


def fmt_ci(est, lo, hi, nd: Optional[int] = None) -> str:
    return f"{fmt_num(est, nd)} ({fmt_num(lo, nd)}, {fmt_num(hi, nd)})"


def fmt_p_table(p) -> str:
    if p is None or (isinstance(p, float) and not np.isfinite(p)):
        return "—"
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def fmt_n_pct(mask) -> str:
    m = pd.Series(mask).astype(bool)
    return f"{int(m.sum())} ({m.mean() * 100:.0f}%)"


def save_tables_xlsx(tables: Dict[str, pd.DataFrame], path: str | Path) -> Path:
    """One sheet per table (sheet names are cut to 31 characters), frozen header, sensible column widths."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        for name, df in tables.items():
            sheet = name[:31]
            df.to_excel(w, sheet_name=sheet, index=False)
            ws = w.sheets[sheet]
            ws.freeze_panes = "B2"
            for j, c in enumerate(df.columns, start=1):
                width = max(len(str(c)), *(len(str(v)) for v in df[c].head(50))) if len(df) else len(str(c))
                ws.column_dimensions[ws.cell(row=1, column=j).column_letter].width = min(40, max(10, width * 1.1))
    return path
