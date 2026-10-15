# -*- coding: utf-8 -*-
"""One call from (design spec + data) to the Results section.

    from sportsci_figures.results import run_results
    run_results("design.json", "data.csv", "results_out", lang="both")

Output (per language):  results_out/<zh|en>/{figures/*.png|pdf, tables.xlsx, results.docx, results.md, methods_explained.md}
Shared:                 results_out/analysis.json (all numbers), results_out/design_used.json
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..pubstyle import ResultsDoc, apply_style, save_tables_xlsx
from .analysis import analyze, load_data
from .builders import BUILDERS, Ctx
from .explain import build_explain
from .simulate import simulate
from .spec import lab, load_spec


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, pd.DataFrame):
        return json.loads(o.to_json(orient="records"))
    return o


def _md_table(df: pd.DataFrame) -> str:
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)) + "\n"


def assemble(sections: List[Dict[str, Any]], spec: Dict[str, Any], lang: str, out: Path) -> Dict[str, Path]:
    """Write docx + markdown + xlsx from the section list (numbers in all three come from the same objects).

    spec["report"] = {"profile": "thesis", "chapter": 4} switches to the Chinese degree-thesis layout (图 4-1, 小四, 1.5 spacing).
    """
    rep = spec.get("report", {})
    doc = ResultsDoc(lang, profile=rep.get("profile", "journal"), chapter=rep.get("chapter"))
    md: List[str] = []
    tables: Dict[str, pd.DataFrame] = {}
    title = lab(spec.get("title"), lang, "")
    doc.title(("结果" if lang == "zh" else "Results") + (f"：{title}" if title and lang == "zh" else (f" — {title}" if title else "")))
    md.append(f"# {'结果' if lang == 'zh' else 'Results'}\n")
    if spec.get("simulated"):
        doc.notice()
        md.append("> " + ("【模拟数据声明】本节全部结果由模拟数据计算得到，不代表真实受试者观察结果。" if lang == "zh" else "[Simulated-data notice] All results were computed from simulated data and do not represent real participants.") + "\n")
    for i, sec in enumerate(sections, 1):
        num = f"{rep['chapter']}.{i}" if rep.get("chapter") is not None else str(i)
        doc.heading(f"{num}  {sec['heading']}", 2)
        md.append(f"\n## {num}  {sec['heading']}\n")
        for it in sec["items"]:
            if it[0] == "p":
                doc.para(it[1])
                md.append(it[1] + "\n")
            elif it[0] == "fig":
                n = doc.num_label(doc.figure(it[1], it[2]))
                md.append(f"![{'图' if lang == 'zh' else 'Figure'} {n}]({Path(it[1]).relative_to(out).as_posix()})\n\n**{'图' if lang == 'zh' else 'Figure'} {n}** {it[2]}\n")
            elif it[0] == "tab":
                n = doc.num_label(doc.table(it[1], it[2], it[3]))
                tables[f"{'表' if lang == 'zh' else 'Table'}{n}"] = it[1]
                md.append(f"\n**{'表' if lang == 'zh' else 'Table'} {n}** {it[2]}\n\n{_md_table(it[1])}\n{it[3]}\n")
    paths = {"docx": doc.save(out / "results.docx"), "xlsx": save_tables_xlsx(tables, out / "tables.xlsx")}
    (out / "results.md").write_text("\n".join(md), encoding="utf-8")
    paths["md"] = out / "results.md"
    return paths


def run_results(spec, data=None, out_dir="results_out", lang: Optional[str] = None, simulate_data: bool = False,
                thesis_chapter: Optional[int] = None) -> Dict[str, Any]:
    """spec: path or dict. data: csv/xlsx path or DataFrame (None + simulate_data=True -> generate from spec['simulate']).

    lang: 'zh' | 'en' | 'both' (default: spec['language']).
    thesis_chapter: number figures/tables/headings by chapter in degree-thesis layout (overrides spec['report']).
    """
    spec = load_spec(spec)
    if thesis_chapter is not None:
        spec["report"] = {"profile": "thesis", "chapter": int(thesis_chapter)}
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if data is None:
        if not simulate_data:
            raise ValueError("no data given; pass a data file, or simulate_data=True for a spec with a 'simulate' block")
        df = simulate(spec)
        df.to_csv(out / "simulated_data.csv", index=False, encoding="utf-8-sig")
        spec["simulated"] = True
    else:
        df = data if isinstance(data, pd.DataFrame) else load_data(data)
    res = analyze(df, spec)
    langs = ["zh", "en"] if lang == "both" else [lang or spec["language"]]
    outputs: Dict[str, Any] = {}
    for lg in langs:
        apply_style(lg)
        d = out / lg
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        cx = Ctx(spec, res, df, lg, d / "figures")
        secs = BUILDERS[spec["design"]](cx)
        outputs[lg] = assemble(secs, spec, lg, d)
        (d / "methods_explained.md").write_text(build_explain(res, lg), encoding="utf-8")
        outputs[lg]["explain"] = d / "methods_explained.md"
    (out / "analysis.json").write_text(json.dumps(_jsonable(res), ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "design_used.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    return dict(results=res, outputs=outputs, out_dir=out)
