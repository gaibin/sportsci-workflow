"""The topic card (one page of facts + open items) and the `design.json` draft for the results engine."""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Dict, List, Optional

from .brief import Brief, Facet, FACET_KEYS
from .designmap import DesignChoice
from .evidence import TIER_TEXT, Evidence
from .feasibility import GREEN, RED, YELLOW, weeks_needed
from .power import SamplePlan
from .variants import Variant

LIGHT = {GREEN: "🟢", YELLOW: "🟡", RED: "🔴"}
VERDICT = {
    "zh": {GREEN: "可以进入开题准备", YELLOW: "先处理下面列出的黄色项再定题", RED: "有红色项：调整选题或条件后再继续"},
    "en": {GREEN: "ready for proposal preparation", YELLOW: "resolve the yellow items before committing", RED: "red items: change the topic or the constraints first"},
}
FACET_NAME = {
    "zh": {"population": "人群 P", "intervention": "干预/暴露 I", "comparator": "对照 C", "outcome": "结局 O"},
    "en": {"population": "Population P", "intervention": "Intervention / exposure I", "comparator": "Comparator C", "outcome": "Outcome O"},
}


def _t(lang: str, zh: str, en: str) -> str:
    return zh if lang == "zh" else en


def _esc(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ")


# ---------------------------------------------------------------------------------------------------- design draft

def _codes(labels: List[str], prefix: str) -> List[str]:
    return [f"{prefix}{i + 1}" for i in range(len(labels))]


def build_design_draft(b: Brief, choice: DesignChoice) -> Dict:
    """A design.json the results engine accepts (`sportsci-figures check-design`). Primary outcome comes from the brief;
    nothing is simulated and `simulated` is false: the file describes a plan for real data."""
    d = choice.design
    title = {"zh": b.title, "en": b.title}
    spec: Dict = {"design": d, "title": title, "language": b.language, "simulated": False}
    outs = [{"name": o.name, "label": {"zh": o.label or o.name, "en": o.label_en or o.label or o.name}, "unit": o.unit,
             "category": o.category, "primary": o.primary, "direction": o.direction, "decimals": o.decimals} for o in b.outcomes]

    def labels(zh: List[str], en: List[str], codes: List[str]):
        return {c: {"zh": z, "en": (en[i] if i < len(en) else z)} for i, (c, z) in enumerate(zip(codes, zh))}

    if d == "survey":
        spec["columns"] = {"id": "id"}
        spec["demographics"] = [{"name": "sex", "label": {"zh": "性别", "en": "Sex"}, "type": "cat", "levels": ["男", "女"]},
                                {"name": "age", "label": {"zh": "年龄 (岁)", "en": "Age (years)"}, "type": "cont"}]
        spec["scales"] = [{"name": s.name, "label": {"zh": s.label or s.name, "en": s.label_en or s.label or s.name},
                           "items": [f"{s.name}{i}" for i in range(1, max(2, s.n_items) + 1)], "min": 1, "max": 5} for s in b.scales]
        spec["common_method_bias"] = True
        spec["efa"] = {"enabled": True, "n_factors": None}
        spec["group_compare"] = ["sex"]
        xs = [s.name for s in b.scales if s.role == "x"]
        ys = [s.name for s in b.scales if s.role == "y"]
        ms = [s.name for s in b.scales if s.role == "m"]
        ws = [s.name for s in b.scales if s.role == "w"]
        cov = ["sex", "age"]
        if ys and xs:
            spec["regression"] = [{"y": ys[0], "x": xs + ms + ws, "covariates": cov}]
        if ys and xs and ms:
            spec["mediation"] = [{"x": xs[0], "m": ms[0], "y": ys[0], "covariates": cov, "n_boot": 5000, "seed": 7}]
        if ys and xs and ws:
            spec["moderation"] = [{"x": xs[0], "w": ws[0], "y": ys[0], "covariates": cov}]
        return spec

    if d == "meta":
        spec["columns"] = {"study": "study", "n1": "n_int", "m1": "mean_int", "sd1": "sd_int", "n2": "n_ctl", "m2": "mean_ctl", "sd2": "sd_ctl"}
        prim = b.primary_outcome
        spec["meta"] = {"effect": "smd", "direction": prim.direction if prim and prim.direction != "neutral" else "higher_better", "hksj": True,
                        "outcome_label": {"zh": prim.label if prim else "", "en": prim.label_en if prim else ""}}
        return spec

    if d == "crossover":
        conds = b.design.conditions or ["对照条件", "干预条件"]
        codes = ["CON"] + [f"C{i}" for i in range(1, len(conds))]
        spec["columns"] = {"id": "id", "condition": "condition", "period": "period"}
        spec["conditions"] = {"order": codes, "control": codes[0], "labels": labels(conds, b.design.conditions_en, codes)}
    elif d == "single_group":
        times = b.design.time_labels or ["基线", "终测"]
        codes = ["pre"] + [f"t{i}" for i in range(1, len(times))]
        spec["columns"] = {"id": "id", "time": "time"}
        spec["times"] = {"order": codes, "labels": labels(times, b.design.time_labels_en, codes)}
    else:  # parallel_prepost | multitime
        groups = b.design.groups or ["对照组", "干预组"]
        gcodes = ["CON"] + [f"G{i}" for i in range(1, len(groups))]
        n_t = 2 if d == "parallel_prepost" else max(3, b.design.timepoints)
        times = list(b.design.time_labels)
        while len(times) < n_t:
            times.append(("基线" if not times else f"随访{len(times)}"))
        times = times[:n_t]
        tcodes = ["pre", "post"] if d == "parallel_prepost" else ["t0"] + [f"t{i}" for i in range(1, n_t)]
        spec["columns"] = {"id": "id", "group": "group", "time": "time"}
        spec["groups"] = {"order": gcodes, "control": gcodes[0], "labels": labels(groups, b.design.groups_en, gcodes)}
        spec["times"] = {"order": tcodes, "labels": labels(times, b.design.time_labels_en, tcodes)}
        if d == "multitime":
            spec["times"]["primary"] = tcodes[-1]
            spec["multitime"] = {"constrained_baseline": True}
        spec["baseline_vars"] = [{"name": "age", "label": {"zh": "年龄 (岁)", "en": "Age (years)"}, "type": "cont"},
                                 {"name": "sex", "label": {"zh": "性别", "en": "Sex"}, "type": "cat", "levels": ["F", "M"]}]
    spec["outcomes"] = outs
    cats = sorted({o["category"] for o in outs})
    spec["category_labels"] = {c: {"zh": c, "en": c} for c in cats}
    return spec


# ------------------------------------------------------------------------------------------------------- open items

def open_items(b: Brief, choice: DesignChoice, plan: SamplePlan, ev: Optional[Evidence], checks: List, lang: str) -> List[str]:
    items: List[str] = []
    if not (b.effect.source or "").strip() and plan.status != "not_applicable":
        items.append(_t(lang, "效应量没有来源：从最接近的 1–2 篇文献里读出效应量（写明 DOI 和表号），或说明是预实验 / 最小有意义差异",
                        "the effect size has no source: read it from the 1-2 closest papers (state DOI and table) or declare pilot / smallest effect of interest"))
    if ev is None or ev.n_records == 0:
        items.append(_t(lang, "还没有记录集：用 `sportsci-refs search` 检索，或从 CNKI / PubMed 导出题录后重新生成", "no record set yet: run `sportsci-refs search` or export from CNKI / PubMed and rebuild"))
    elif ev.coverage == "low":
        items.append(_t(lang, f"记录集只有 {ev.n_records} 条：补充中文（CNKI/万方）和英文检索后再判断撞题",
                        f"only {ev.n_records} records: extend Chinese (CNKI) and English searches before judging overlap"))
    if ev is not None and ev.nearest:
        items.append(_t(lang, "逐篇阅读「最接近的研究」表里的前 3–5 篇，并写一句话说明你的题目与它们的区别（这一句话必须由你自己写）",
                        "read the top 3-5 papers in the nearest-studies table and write one sentence on how your study differs (you write that sentence)"))
    for c in checks:
        if c.status == RED:
            items.append(_t(lang, f"红色：{c.title} — 需要调整", f"red: {c.title} - needs a change"))
    items.append(_t(lang, f"主要结局已固定为「{b.primary_outcome.label if b.primary_outcome else '—'}」，看数据前不得更改",
                    f"primary outcome is fixed as '{b.primary_outcome.label_en if b.primary_outcome else '-'}' and may not change after seeing data"))
    items.append(_t(lang, "把 design_draft.json 交给 `sportsci-figures check-design` 检查列名，再进入数据采集计划",
                    "run design_draft.json through `sportsci-figures check-design`, then plan data collection"))
    return items


# ------------------------------------------------------------------------------------------------------------ card

def render_card(b: Brief, choice: DesignChoice, plan: SamplePlan, ev: Optional[Evidence], assessment: Dict,
                variants: Optional[List[Variant]] = None, warnings: Optional[List[str]] = None, lang: Optional[str] = None,
                today: Optional[_dt.date] = None) -> str:
    lang = lang or b.language
    zh = lang == "zh"
    today = today or _dt.date.today()
    overall = assessment["overall"]
    L: List[str] = []
    L.append(f"# {_t(lang, '选题卡：', 'Topic card: ')}{b.title or _t(lang, '（未命名）', '(untitled)')}")
    L.append("")
    L.append(f"{LIGHT[overall]} **{VERDICT[lang][overall]}**  ·  {today.isoformat()}")
    L.append("")
    L.append(_t(lang, "> 这张卡只陈述事实和计算结果；题目取舍、与既有研究的区别、引言与讨论都是作者自己的工作。",
                "> This card states facts and computed results. Choosing the topic, saying how it differs from prior work, and writing the introduction and discussion are the author's job."))
    L.append("")

    L.append(f"## 1. {_t(lang, '研究问题', 'Research question')}")
    L.append("")
    L.append(f"| {_t(lang, '要素', 'Element')} | {_t(lang, '内容', 'Content')} | {_t(lang, '检索词', 'Search terms')} |")
    L.append("|---|---|---|")
    for k in FACET_KEYS:
        f = b.facets.get(k)
        if f and f.terms:
            L.append(f"| {FACET_NAME[lang][k]} | {_esc(f.label)} | {_esc(' · '.join(f.terms))} |")
    L.append("")
    if b.constraints.supervisor_direction:
        L.append(f"{_t(lang, '导师方向', 'Supervisor direction')}：{b.constraints.supervisor_direction}")
        L.append("")

    L.append(f"## 2. {_t(lang, '研究设计', 'Study design')}")
    L.append("")
    L.append(f"- **{choice.design}** — {choice.rule}")
    L.append(f"- {_t(lang, '可以说', 'May claim')}：{choice.permits}")
    L.append(f"- {_t(lang, '不能说', 'May not claim')}：{choice.forbids}")
    L.append(f"- {_t(lang, '计划分析', 'Planned analysis')}：{choice.analysis}")
    L.append(f"- {_t(lang, '备选分析', 'Fallback analysis')}：{choice.fallback}")
    for w in choice.warnings:
        L.append(f"- ⚠️ {w}")
    prim = b.primary_outcome
    if prim:
        L.append(f"- {_t(lang, '主要结局', 'Primary outcome')}：{prim.label if zh else prim.label_en}（{prim.unit or '—'}）")
        sec = [o for o in b.outcomes if not o.primary]
        if sec:
            L.append(f"- {_t(lang, '次要结局', 'Secondary outcomes')}：" + ("、" if zh else ", ").join(o.label if zh else o.label_en for o in sec))
    L.append("")

    L.append(f"## 3. {_t(lang, '证据地图', 'Evidence map')}")
    L.append("")
    if ev is None or ev.n_records == 0:
        L.append(_t(lang, "没有记录集：这一节不能下结论。", "No record set: this section cannot conclude anything."))
    else:
        lo, hi = ev.window
        L.append(_t(lang, f"记录集 **{ev.n_records}** 条（{ev.n_without_year} 条缺年份）；"
                          f"窗口 {lo}–{hi}；覆盖度：{'足够（≥30）' if ev.coverage == 'ok' else '**不足（<30，只是草图）**'}",
                    f"**{ev.n_records}** records ({ev.n_without_year} without a year); window {lo}-{hi}; coverage: "
                    f"{'adequate (>= 30)' if ev.coverage == 'ok' else '**thin (< 30, a sketch)**'}"))
        L.append("")
        L.append(f"| {_t(lang, '组合', 'Combination')} | {_t(lang, '全部年份', 'All years')} | {_t(lang, '近五年', 'Last 5 years')} |")
        L.append("|---|---|---|")
        for k, v in ev.combos_all.items():
            L.append(f"| {k} | {v} | {ev.combos_recent.get(k, 0)} |")
        L.append("")
        L.append(f"**{_t(lang, '撞题判断', 'Overlap')}**：{TIER_TEXT[lang][ev.tier]}（{_t(lang, '近五年直接重叠', 'direct overlaps, last 5 years')} {ev.direct_recent}）")
        L.append("")
        if ev.gaps:
            L.append(f"**{_t(lang, '关于记录集的事实陈述', 'Statements about the record set')}**")
            L.append("")
            for g in ev.gaps:
                L.append(f"- {g['text']}")
            L.append("")
            L.append(_t(lang, "> 这些是对**记录集**的陈述，不是对全部文献的结论；是否真是缺口，要读完最接近的研究后由你判断。",
                        "> These describe the **record set**, not the whole literature; whether it is a real gap is your judgement after reading the nearest studies."))
            L.append("")
        if ev.nearest:
            L.append(f"**{_t(lang, '最接近的研究', 'Nearest studies')}**")
            L.append("")
            L.append(f"| # | {_t(lang, '年', 'Year')} | {_t(lang, '命中', 'Hits')} | {_t(lang, '设计', 'Design')} | {_t(lang, '题名', 'Title')} | {_t(lang, '期刊', 'Journal')} | DOI |")
            L.append("|---|---|---|---|---|---|---|")
            for i, h in enumerate(ev.nearest, 1):
                r = h.record
                L.append(f"| {i} | {r.year or '—'} | {h.code()} | {h.design} | {_esc(r.title)} | {_esc(r.journal) or '—'} | {r.doi or '—'} |")
            L.append("")
        if ev.retrieval:
            L.append(f"**{_t(lang, '检索记录', 'Retrieval log')}**：" + "；".join(
                f"{_esc(str(x.get('source') or x.get('query')))} → {x.get('n', '?')}" for x in ev.retrieval))
            L.append("")

    L.append(f"## 4. {_t(lang, '样本量', 'Sample size')}")
    L.append("")
    if plan.status == "not_applicable":
        for r in plan.rules:
            L.append(f"- {r}")
    else:
        L.append(f"| {_t(lang, '项目', 'Item')} | {_t(lang, '值', 'Value')} |")
        L.append("|---|---|")
        L.append(f"| {_t(lang, '效应量', 'Effect size')} | {plan.effect_label or _t(lang, '未提供', 'not provided')} |")
        L.append(f"| {_t(lang, '效应量来源', 'Source')} | {_esc(plan.source) or _t(lang, '**未写明**', '**not stated**')} |")
        if plan.n_total:
            L.append(f"| {_t(lang, '需要分析的人数', 'Analysed participants needed')} | {plan.n_total}"
                     + (f"（{_t(lang, '每组', 'per group')} {plan.n_per_group}）" if plan.groups > 1 and plan.n_per_group else "") + " |")
            L.append(f"| {_t(lang, '含脱落需入组', 'Enrol (with dropout)')} | {plan.n_enrol_total} |")
        L.append(f"| {_t(lang, '可及人数（脱落后）', 'Accessible (after dropout)')} | {plan.accessible_enrol}（{plan.accessible_analysed}） |")
        if plan.power_at_accessible is not None:
            L.append(f"| {_t(lang, '该人数下的功效', 'Power at that n')} | {plan.power_at_accessible:.2f} |")
        if plan.mdes_at_accessible is not None:
            L.append(f"| {_t(lang, '80% 功效可检出的最小效应', 'Smallest effect detectable (80%)')} | {plan.mdes_label} ≈ {plan.mdes_at_accessible:.2f} |")
        if plan.assumptions:
            L.append(f"| {_t(lang, '假设', 'Assumptions')} | {_esc(plan.assumptions)} |")
        L.append("")
        for r in plan.rules:
            L.append(f"- {r}")
        if plan.sensitivity:
            L.append("")
            L.append(f"**{_t(lang, '敏感性示意（常规量级，不是你的效应量）', 'Sensitivity (conventional magnitudes, not your effect size)')}**")
            L.append("")
            L.append(f"| {_t(lang, '效应', 'Effect')} | {_t(lang, '需要人数', 'n needed')} | {_t(lang, '可及人数下的功效', 'Power at accessible n')} |")
            L.append("|---|---|---|")
            for s in plan.sensitivity:
                L.append(f"| {s['effect']} | {s['n']}{_t(lang, '（每组）', ' per group') if plan.groups > 1 else ''} | {s['power_at_accessible']:.2f} |")
    L.append("")

    L.append(f"## 5. {_t(lang, '可行性', 'Feasibility')}")
    L.append("")
    L.append(f"| | {_t(lang, '项目', 'Check')} | {_t(lang, '结果', 'Result')} | {_t(lang, '规则', 'Rule')} |")
    L.append("|---|---|---|---|")
    for c in assessment["checks"]:
        L.append(f"| {LIGHT[c.status]} | {c.title} | {_esc(c.detail)} | {_esc(c.rule)} |")
    L.append("")

    if variants and len(variants) > 1:
        L.append(f"## 6. {_t(lang, '变体矩阵', 'Variant matrix')}")
        L.append("")
        L.append(_t(lang, "每次只改一个轴，重新统计与记录集的直接重叠。「不可判断」= 该变体的检索词在记录集里一条都没出现，零不代表没人做过。",
                    "One axis changed at a time, direct overlap recounted. 'Not assessable' = the variant's terms occur nowhere in the record set; a zero then means nothing."))
        L.append("")
        L.append(f"| {_t(lang, '变体', 'Variant')} | {_t(lang, '近五年直接重叠', 'Direct overlap (5 y)')} | {_t(lang, '全部年份', 'All years')} | {_t(lang, '较基础题', 'vs base')} | {_t(lang, '判断', 'Status')} |")
        L.append("|---|---|---|---|---|")
        for v in variants:
            d = "—" if not v.axes else f"{v.delta_recent:+d}"
            status = _t(lang, "基础题", "base") if not v.axes else (_t(lang, "可判断", "assessable") if v.assessable else _t(lang, "不可判断", "not assessable"))
            L.append(f"| {_esc(v.name())} | {v.direct_recent} | {v.direct_all} | {d} | {status} |")
        L.append("")
        L.append(_t(lang, "> 换了变体后，可及人数、设备、伦理需要重新核对；这张表只回答「撞不撞题」。",
                    "> A variant changes who you can recruit, what you need and the ethics route; this table only answers 'does it overlap'."))
        L.append("")

    n = 7 if variants and len(variants) > 1 else 6
    L.append(f"## {n}. {_t(lang, '下一步', 'Next steps')}")
    L.append("")
    for i, it in enumerate(open_items(b, choice, plan, ev, assessment["checks"], lang), 1):
        L.append(f"{i}. {it}")
    L.append("")
    if warnings:
        L.append(f"## {_t(lang, '简报提示', 'Brief notes')}")
        L.append("")
        for w in warnings:
            L.append(f"- {w}")
        L.append("")
    return "\n".join(L).rstrip() + "\n"


def write_outputs(out_dir: str | Path, card_md: str, draft: Dict, ev: Optional[Evidence], plan: SamplePlan,
                  assessment: Dict, variants: Optional[List[Variant]] = None) -> Dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {"card": out / "topic_card.md", "design": out / "design_draft.json", "data": out / "topic_data.json"}
    paths["card"].write_text(card_md, encoding="utf-8")
    paths["design"].write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    data = {
        "overall": assessment["overall"],
        "checks": [c.to_dict() for c in assessment["checks"]],
        "sample": plan.to_dict(),
        "evidence": ev.to_dict() if ev else None,
        "variants": [v.to_dict() for v in variants] if variants else [],
    }
    paths["data"].write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return paths
