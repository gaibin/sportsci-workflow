# -*- coding: utf-8 -*-
"""Data intake (数据体检): a raw CSV/Excel file -> de-identified copy, data-quality report, draft design.json.

    python cli.py intake 原始数据.xlsx -o projects/study01/intake
    from sportsci_figures.intake import run_intake

Steps
  1. read (csv / xlsx, first sheet unless `sheet` is given)
  2. de-identify: drop name / phone / ID-card / student-number columns, replace the participant ID by P001, P002 ...
     (the original -> pseudonym map is written to <out>/_private/ — keep it with the raw files, never in a deliverable)
  3. profile every column: type, missing, distinct values, range, outliers (|z| > 3 and outside 3 × IQR), Likert-like items
  4. recognise the layout and propose a design:
       Likert item blocks (PA1..PA5, SL1..)            -> survey
       long format (id repeats, time column)           -> single_group | parallel_prepost | multitime
       long format (id repeats, condition column)      -> crossover
       wide format (x_pre / x_post column pairs)       -> reshaped to long, then parallel_prepost or single_group
  5. write intake_report.md, data_clean.csv (+ data_long.csv when reshaped) and design_draft.json

The draft is a starting point, never a decision: the primary outcome, reference group, reverse-keyed items and the
analysis plan must be confirmed by the researcher (the report lists every open question as 「待确认」).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .privacy import pii_columns, scrub_frame
from .profiler import profile_dataframe

_TIME_HINTS = re.compile(r"^(time|times|timepoint|visit|wave|phase|session|测试时间|时间点|时间|阶段|测次|测试阶段)$", re.I)
_COND_HINTS = re.compile(r"^(condition|trial|treatment|session_type|条件|处理|实验条件|试次)$", re.I)
_GROUP_HINTS = re.compile(r"(group|arm|cohort|组别|分组|组)$", re.I)
_ID_HINTS = re.compile(r"^(id|subject|participant|subj|sid|编号|受试者编号|被试编号|序号|样本编号|受试者|被试)$", re.I)
_ITEM = re.compile(r"^([A-Za-z一-鿿]+?)[_\-.]?(\d{1,2})$")
_PRE = re.compile(r"(?:_pre|_before|_baseline|_t0|_前测|_干预前|前测|干预前)$", re.I)
_POST = re.compile(r"(?:_post|_after|_t1|_后测|_干预后|后测|干预后)$", re.I)


def load_table(path, sheet=None) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(p, sheet_name=sheet or 0)
    for enc in ("utf-8-sig", "gb18030"):  # Chinese Excel exports are often GBK
        try:
            return pd.read_csv(p, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"cannot decode {p} as UTF-8 or GB18030")


# ----------------------------------------------------------------------------- column profile
def column_profile(df: pd.DataFrame) -> List[Dict[str, Any]]:
    out = []
    for c in df.columns:
        s = df[c]
        num = pd.to_numeric(s, errors="coerce")
        is_num = num.notna().sum() >= 0.9 * s.notna().sum() and s.notna().any()
        r: Dict[str, Any] = dict(column=str(c), n=int(s.notna().sum()), missing=int(s.isna().sum()), missing_pct=float(100 * s.isna().mean()),
                                 distinct=int(s.nunique(dropna=True)), numeric=bool(is_num))
        if is_num:
            x = num.dropna()
            r.update(min=float(x.min()), max=float(x.max()), mean=float(x.mean()), sd=float(x.std(ddof=1)) if len(x) > 1 else float("nan"))
            q1, q3 = x.quantile([0.25, 0.75])
            iqr = q3 - q1
            z = (x - x.mean()) / x.std(ddof=1) if x.std(ddof=1) > 0 else x * 0
            flag = (z.abs() > 3) & ((x < q1 - 3 * iqr) | (x > q3 + 3 * iqr))
            r["outliers"] = [dict(row=int(i), value=float(x[i])) for i in x[flag].index[:10]]
            r["likert"] = bool(len(x) and (x == x.round()).all() and x.min() >= 0 and x.max() <= 10 and r["distinct"] <= 11)
            r["non_numeric_values"] = [str(v) for v in s[num.isna() & s.notna()].unique()[:5]]
        else:
            r["levels"] = {str(k): int(v) for k, v in s.value_counts().head(12).items()}
        out.append(r)
    return out


def item_blocks(prof: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Group Likert-like columns sharing a prefix (PA1, PA2 ... / 焦虑1, 焦虑2 ...) into candidate scales (>= 3 items)."""
    blocks: Dict[str, List[str]] = {}
    for r in prof:
        if not r.get("likert"):
            continue
        m = _ITEM.match(r["column"])
        if m:
            blocks.setdefault(m.group(1), []).append(r["column"])
    return {k: sorted(v, key=lambda c: int(_ITEM.match(c).group(2))) for k, v in blocks.items() if len(v) >= 3}


def reverse_candidates(df: pd.DataFrame, items: List[str]) -> List[str]:
    """Items correlating negatively with the rest of their block are probably reverse-keyed (to be confirmed with the questionnaire)."""
    X = df[items].apply(pd.to_numeric, errors="coerce").dropna()
    out = []
    if len(X) < 10:
        return out
    for c in items:
        rest = X.drop(columns=c).sum(axis=1)
        if X[c].std() > 0 and np.corrcoef(X[c], rest)[0, 1] < -0.1:
            out.append(c)
    return out


# ----------------------------------------------------------------------------- layout
def _find(df: pd.DataFrame, pat: re.Pattern, exclude=()) -> Optional[str]:
    return next((str(c) for c in df.columns if pat.search(str(c).strip()) and str(c) not in exclude), None)


def detect_layout(df: pd.DataFrame, prof: List[Dict[str, Any]]) -> Dict[str, Any]:
    idc = _find(df, _ID_HINTS)
    blocks = item_blocks(prof)
    lay: Dict[str, Any] = dict(id=idc, blocks=blocks)
    repeats = bool(idc) and df[idc].duplicated().any()
    tc = _find(df, _TIME_HINTS)
    cc = _find(df, _COND_HINTS)
    gc = _find(df, _GROUP_HINTS, exclude=(idc or "", tc or "", cc or ""))
    if gc is not None and not (2 <= df[gc].nunique() <= 8):
        gc = None
    lay.update(time=tc, condition=cc, group=gc)
    if repeats and tc:
        k = df[tc].nunique()
        lay["design"] = "single_group" if not gc else ("parallel_prepost" if k == 2 else "multitime")
        lay["format"] = "long"
    elif repeats and cc:
        lay["design"], lay["format"] = "crossover", "long"
    elif blocks and sum(len(v) for v in blocks.values()) >= 0.5 * sum(1 for r in prof if r["numeric"]):
        lay.update(format="wide", design="survey")  # questionnaire items dominate: never treat PA1/PA2 as a pre/post pair
    else:
        pre = [str(c) for c in df.columns if _PRE.search(str(c))]
        post = [str(c) for c in df.columns if _POST.search(str(c))]
        pairs = []
        for p in pre:
            root = _PRE.sub("", p)
            q = next((x for x in post if _POST.sub("", x) == root), None)
            if q:
                pairs.append((root, p, q))
        if not pairs and not blocks:
            prof_ = profile_dataframe(df)
            pairs = [(re.sub(r"[_\-]?(pre|1)$", "", a, flags=re.I) or a, a, b) for a, b in prof_.pre_post_pairs]
        if pairs:
            lay.update(format="wide_prepost", pairs=pairs, design="parallel_prepost" if gc else "single_group")
        elif len(blocks) >= 1:
            lay.update(format="wide", design="survey")
        else:
            lay.update(format="wide", design=None)
    return lay


def wide_to_long(df: pd.DataFrame, idc: str, pairs: List[Tuple[str, str, str]], keep: List[str]) -> pd.DataFrame:
    parts = []
    for t, k in (("pre", 1), ("post", 2)):
        d = df[[idc] + keep].copy()
        d["time"] = t
        for root, a, b in pairs:
            d[root] = df[a if k == 1 else b].values
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


# ----------------------------------------------------------------------------- draft spec
_CONTROL = re.compile(r"(对照|控制|安慰|常规|control|con$|ctrl|placebo|usual|sham)", re.I)


def _reference(levels: List[str]) -> Tuple[str, bool]:
    """Reference level: the one named like a control arm if any, else the first. Returns (level, matched_by_name)."""
    hit = next((x for x in levels if _CONTROL.search(x)), None)
    return (hit, True) if hit else (levels[0], False)


def _outcomes(names: List[str]) -> List[Dict[str, Any]]:
    return [dict(name=n, label={"zh": n, "en": n}, unit="", category="Outcomes", primary=(i == 0), direction="neutral") for i, n in enumerate(names)]


def draft_spec(df: pd.DataFrame, lay: Dict[str, Any], prof: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
    """Returns (design_draft, open_questions)."""
    todo: List[str] = []
    d = lay.get("design")
    idc = lay.get("id") or "id"
    spec: Dict[str, Any] = dict(design=d, title={"zh": "（待填写研究题目）", "en": "(title to be filled in)"}, language="zh", simulated=False)
    numeric = [r["column"] for r in prof if r["numeric"] and r["column"] not in (idc, lay.get("time"), lay.get("group"), lay.get("condition"))]
    if d == "survey":
        scales = []
        for pref, items in lay["blocks"].items():
            rev = reverse_candidates(df, items)
            lo = int(min(df[i].min() for i in items))
            hi = int(max(df[i].max() for i in items))
            scales.append(dict(name=pref, label={"zh": pref, "en": pref}, items=items, reverse=rev, min=lo, max=hi))
            if rev:
                todo.append(f"量表 {pref}：{', '.join(rev)} 与同量表其他题负相关，疑似反向计分题——请对照原问卷确认。")
        item_cols = {i for its in lay["blocks"].values() for i in its}
        demo = []
        for r in prof:
            c = r["column"]
            if c in item_cols or c == idc:
                continue
            if not r["numeric"] and 2 <= r["distinct"] <= 8:
                demo.append(dict(name=c, label={"zh": c, "en": c}, type="cat", levels=list(r["levels"].keys())))
            elif r["numeric"] and not r.get("likert"):
                demo.append(dict(name=c, label={"zh": c, "en": c}, type="cont"))
        spec.update(columns={"id": idc}, scales=scales, demographics=demo, common_method_bias=True, efa={"enabled": True, "n_factors": len(scales) if len(scales) > 1 else None},
                    group_compare=[v["name"] for v in demo if v["type"] == "cat"], regression=[], mediation=[], moderation=[])
        todo += ["确认各量表名称、计分方式（均分/总分）与题项范围。", "研究假设对应的回归、中介（x→m→y）、调节（x×w→y）模型需按开题报告填写到 regression / mediation / moderation。"]
        if len(scales) > 1:
            todo.append("EFA 因子数暂按量表数设定；若量表有多个维度，请按维度拆分 scales 或修改 efa.n_factors。")
    elif d in ("single_group", "parallel_prepost", "multitime", "crossover"):
        if lay.get("format") == "wide_prepost":
            outs = [root for root, _, _ in lay["pairs"]]
            times = ["pre", "post"]
            tc = "time"
        else:
            outs = numeric
            tc = lay.get("time")
            times = [str(x) for x in pd.unique(df[tc].dropna())] if tc else []
        spec["outcomes"] = _outcomes(outs)
        todo.append(f"主要结局暂设为「{outs[0] if outs else '?'}」——必须在看结果之前与研究者确认（预设主要结局）。")
        todo.append("补全各结局的中文/英文名称、单位（unit）、方向（higher_better / lower_better）与类别（category）。")
        if d == "crossover":
            cc = lay["condition"]
            levels = [str(x) for x in pd.unique(df[cc].dropna())]
            ref, _ = _reference(levels)
            spec.update(columns={"id": idc, "condition": cc}, conditions={"order": [ref] + [x for x in levels if x != ref], "control": ref, "labels": {}})
            todo.append(f"参照条件暂设为「{ref}」，请确认；如有阶段/顺序列，请填写 columns.period。")
        else:
            spec["columns"] = {"id": idc, "time": tc}
            spec["times"] = {"order": times, "labels": {}}
            if len(times) >= 2:
                todo.append(f"时间点顺序识别为 {times}，请确认先后顺序。")
            if d in ("parallel_prepost", "multitime"):
                gc = lay["group"]
                levels = [str(x) for x in pd.unique(df[gc].dropna())]
                spec["columns"]["group"] = gc
                ref, by_name = _reference(levels)
                spec["groups"] = {"order": [ref] + [x for x in levels if x != ref], "control": ref, "labels": {}}
                todo.append(f"对照组{'按名称识别为' if by_name else '暂设为'}「{ref}」，请确认。")
                base = [r["column"] for r in prof if r["column"] not in outs + [idc, tc, gc] and r["distinct"] >= 2]
                spec["baseline_vars"] = [dict(name=c, label={"zh": c, "en": c}, type="cont" if next(p for p in prof if p["column"] == c)["numeric"] else "cat") for c in base[:8]]
    else:
        todo.append("未能自动识别研究设计：请说明数据结构（谁在什么时间测了什么、是否分组），再手工编写 design.json（模板：python cli.py new-design）。")
    return spec, todo


# ----------------------------------------------------------------------------- report
def _report(src: str, df_raw: pd.DataFrame, removed: List[str], prof: List[Dict[str, Any]], lay: Dict[str, Any], spec: Dict[str, Any], todo: List[str], files: Dict[str, str]) -> str:
    L = ["# 数据体检报告（intake）", "", f"- 源文件：`{Path(src).name}`", f"- 行 × 列：{len(df_raw)} × {df_raw.shape[1]}"]
    L.append(f"- 已移除的个人身份信息列：{('、'.join(removed)) if removed else '无'}；受试者编号已替换为 P001… 形式（对照表在 `_private/`，不要随交付物外发）")
    names = {"survey": "问卷 / 横断面（survey）", "single_group": "单组前后测 / 重复测量（single_group）", "parallel_prepost": "平行组前后测（parallel_prepost）",
             "multitime": "平行组多时点（multitime）", "crossover": "交叉设计（crossover）", None: "未识别"}
    L += [f"- 识别的数据格式：{lay.get('format')}；建议的研究设计：**{names.get(lay.get('design'))}**", ""]
    L += ["## 生成的文件", ""] + [f"- `{v}`：{k}" for k, v in files.items()] + [""]
    L += ["## 待确认（请逐条与研究者核对后再分析）", ""] + [f"{i + 1}. {t}" for i, t in enumerate(todo)] + [""]
    miss = [r for r in prof if r["missing_pct"] > 0]
    L += ["## 缺失值", ""]
    if miss:
        L += ["| 列 | 缺失数 | 缺失率 |", "|---|---|---|"] + [f"| {r['column']} | {r['missing']} | {r['missing_pct']:.1f}% |" for r in sorted(miss, key=lambda r: -r["missing_pct"])]
        if any(r["missing_pct"] > 20 for r in miss):
            L.append("\n> 有列缺失率 > 20%：需说明缺失原因，并考虑敏感性分析（如多重插补）。")
    else:
        L.append("无缺失值。")
    out_rows = [(r["column"], o) for r in prof if r.get("outliers") for o in r["outliers"]]
    L += ["", "## 可疑异常值（|z| > 3 且超出 3 × IQR）", ""]
    L += (["| 列 | 行号（0 起） | 值 |", "|---|---|---|"] + [f"| {c} | {o['row']} | {o['value']:g} |" for c, o in out_rows]) if out_rows else ["未发现。"]
    L.append("\n> 异常值只标记、不删除：先核对原始记录（录入错误？测试失败？），确属错误再修正，并在方法部分写明处理规则。")
    bad = [r for r in prof if r.get("non_numeric_values")]
    if bad:
        L += ["", "## 数值列中混入的文本", ""] + [f"- {r['column']}：{', '.join(r['non_numeric_values'])}" for r in bad]
    if lay.get("blocks"):
        L += ["", "## 识别到的量表题项", ""] + [f"- {k}：{len(v)} 题（{', '.join(v)}）" for k, v in lay["blocks"].items()]
    L += ["", "## 各列概况", "", "| 列 | 类型 | 有效 n | 不同取值 | 范围 / 水平 |", "|---|---|---|---|---|"]
    for r in prof:
        rng = f"{r['min']:g}–{r['max']:g}" if r["numeric"] else "、".join(f"{k}({v})" for k, v in list(r.get("levels", {}).items())[:6])
        L.append(f"| {r['column']} | {'数值' if r['numeric'] else '文本'}{'（李克特）' if r.get('likert') else ''} | {r['n']} | {r['distinct']} | {rng} |")
    L += ["", "## 下一步", "", "1. 按「待确认」逐条修改 `design_draft.json`，另存为 `design.json`；",
          "2. `python cli.py check-design design.json -d <数据文件>`；", "3. `python cli.py results design.json -d <数据文件> -o results -l zh`（学位论文加 `--chapter 4`）。"]
    return "\n".join(L) + "\n"


def run_intake(path, out_dir, sheet=None) -> Dict[str, Any]:
    out = Path(out_dir)
    (out / "_private").mkdir(parents=True, exist_ok=True)
    raw = load_table(path, sheet)
    raw.columns = [str(c).strip() for c in raw.columns]
    idc = _find(raw, _ID_HINTS)
    removed = [c for c in pii_columns(raw) if c != idc]
    clean, mapping = scrub_frame(raw, idc)
    if mapping:
        pd.DataFrame({"original": list(mapping), "pseudonym": list(mapping.values())}).to_csv(out / "_private" / "id_map.csv", index=False, encoding="utf-8-sig")
    prof = column_profile(clean)
    lay = detect_layout(clean, prof)
    files = {"去标识化后的数据": "data_clean.csv"}
    clean.to_csv(out / "data_clean.csv", index=False, encoding="utf-8-sig")
    data_for_spec = clean
    if lay.get("format") == "wide_prepost":
        idc2 = lay.get("id")
        if not idc2:
            clean.insert(0, "id", [f"P{i + 1:03d}" for i in range(len(clean))])
            idc2 = lay["id"] = "id"
        keep = [c for c in ([lay.get("group")] if lay.get("group") else [])]
        used = {c for _, a, b in lay["pairs"] for c in (a, b)}
        keep += [c for c in clean.columns if c not in used and c not in keep and c != idc2]
        long_ = wide_to_long(clean, idc2, lay["pairs"], keep)
        long_.to_csv(out / "data_long.csv", index=False, encoding="utf-8-sig")
        files["转换为长格式的数据（分析用这个）"] = "data_long.csv"
        data_for_spec = long_
    spec, todo = draft_spec(data_for_spec if lay.get("format") != "wide_prepost" else clean, lay, prof)
    (out / "design_draft.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    files["研究设计草稿（确认后改名为 design.json）"] = "design_draft.json"
    files["本报告"] = "intake_report.md"
    if mapping:
        files["编号对照表（仅内部保存）"] = "_private/id_map.csv"
    (out / "intake_report.md").write_text(_report(str(path), raw, removed, prof, lay, spec, todo, files), encoding="utf-8")
    return dict(layout={k: v for k, v in lay.items() if k != "blocks"} | {"blocks": list(lay.get("blocks", {}))}, removed=removed, todo=todo,
                spec=spec, out_dir=out, report=out / "intake_report.md")
