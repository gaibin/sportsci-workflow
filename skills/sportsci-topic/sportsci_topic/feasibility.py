"""Feasibility checks: a visible rubric, every rule written next to its verdict.

Each check returns green / yellow / red, the numbers it rests on and the rule that produced the colour. There is no
weighted total and no composite score: a single red is a single red, and the student sees which constraint it is.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from .brief import Brief
from .designmap import DesignChoice, comfort_gap
from .evidence import Evidence
from .power import SamplePlan

GREEN, YELLOW, RED = "green", "yellow", "red"
RANK = {GREEN: 0, YELLOW: 1, RED: 2}
POWER_GREEN, POWER_YELLOW = 0.80, 0.60
SLACK_GREEN = 0.20          # weeks of slack as a share of weeks needed
ETHICS_DEFAULT_WEEKS = {"approved": 0, "not_needed": 0, "pending": 4, "not_started": 8}


@dataclass
class Check:
    id: str
    status: str
    title: str
    detail: str
    rule: str
    numbers: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


def _t(lang: str, zh: str, en: str) -> str:
    return zh if lang == "zh" else en


def check_sample(b: Brief, plan: SamplePlan, lang: str) -> Check:
    rule = _t(lang, "绿：可及人数下的功效 ≥ 0.80；黄：0.60–0.80，或没有效应量来源；红：< 0.60",
              "green: power at accessible n >= 0.80; yellow: 0.60-0.80 or no stated effect-size source; red: < 0.60")
    nums = {"accessible_enrol": plan.accessible_enrol, "accessible_analysed": plan.accessible_analysed, "dropout": b.constraints.dropout,
            "required_total_analysed": plan.n_total, "required_total_enrol": plan.n_enrol_total, "power_at_accessible": plan.power_at_accessible,
            "mdes": plan.mdes_at_accessible, "mdes_label": plan.mdes_label}
    title = _t(lang, "样本量", "Sample size")
    if plan.status == "not_applicable":
        return Check("sample", GREEN, title, _t(lang, "元分析：样本量问题改为「能检索到多少项合格研究」", "meta-analysis: the question becomes how many eligible studies exist"), rule, nums)
    if plan.status == "no_effect" and plan.test != "correlation":
        return Check("sample", YELLOW, title,
                     _t(lang, f"没有效应量，无法判断。可及 {plan.accessible_enrol} 人（脱落后约 {plan.accessible_analysed}），"
                              f"能以 80% 功效检出的最小效应约为 {plan.mdes_label} = {plan.mdes_at_accessible:.2f}。",
                        f"no effect size, so no verdict. {plan.accessible_enrol} accessible ({plan.accessible_analysed} after dropout) can detect "
                        f"{plan.mdes_label} = {plan.mdes_at_accessible:.2f} at 80% power."), rule, nums)
    pw = plan.power_at_accessible
    if plan.test == "correlation" and plan.status == "no_effect":
        floor_n = plan.n_total or 0
        st = GREEN if plan.accessible_analysed >= floor_n else YELLOW if plan.accessible_analysed >= 0.75 * floor_n else RED
        return Check("sample", st, title,
                     _t(lang, f"经验规则下限 {floor_n} 人；可及 {plan.accessible_enrol} 人，脱落后约 {plan.accessible_analysed} 人。",
                        f"rule-of-thumb floor {floor_n}; {plan.accessible_enrol} accessible, about {plan.accessible_analysed} after dropout."), rule, nums)
    st = GREEN if pw is not None and pw >= POWER_GREEN else YELLOW if pw is not None and pw >= POWER_YELLOW else RED
    mdes_zh = f"；该人数能以 80% 功效检出的最小效应 {plan.mdes_label} ≈ {plan.mdes_at_accessible:.2f}" if plan.mdes_at_accessible is not None else ""
    mdes_en = f"; that n detects {plan.mdes_label} ≈ {plan.mdes_at_accessible:.2f} at 80% power" if plan.mdes_at_accessible is not None else ""
    detail = _t(lang,
                f"{plan.effect_label}：需要分析 {plan.n_total} 人（含脱落约入组 {plan.n_enrol_total}）；可及 {plan.accessible_enrol} 人，"
                f"脱落后约 {plan.accessible_analysed}，功效 {pw:.2f}{mdes_zh}。",
                f"{plan.effect_label}: needs {plan.n_total} analysed ({plan.n_enrol_total} enrolled with dropout); {plan.accessible_enrol} accessible, "
                f"about {plan.accessible_analysed} analysed, power {pw:.2f}{mdes_en}.")
    if not plan.source and st == GREEN:
        st = YELLOW
        detail += _t(lang, "（效应量没有来源，降为黄）", " (no effect-size source: downgraded to yellow)")
    return Check("sample", st, title, detail, rule, nums)


def weeks_needed(b: Brief) -> Dict[str, int]:
    c = b.constraints
    ethics = c.ethics_weeks if c.ethics_weeks is not None else ETHICS_DEFAULT_WEEKS.get(c.ethics, 4)
    parts = {"ethics": ethics, "recruit": c.recruit_weeks, "intervention": c.intervention_weeks, "testing": c.test_weeks, "writing": c.writing_weeks}
    parts["total"] = sum(parts.values())
    return parts


def check_time(b: Brief, lang: str) -> Check:
    rule = _t(lang, "绿：可用周数 − 所需周数 ≥ 所需的 20%；黄：有余量但不足 20%；红：所需周数超过可用周数",
              "green: slack >= 20% of weeks needed; yellow: slack under 20%; red: weeks needed exceed weeks available")
    w = weeks_needed(b)
    avail = b.constraints.weeks_available
    slack = avail - w["total"]
    if avail <= 0:
        st = YELLOW
    elif slack < 0:
        st = RED
    elif slack >= SLACK_GREEN * w["total"]:
        st = GREEN
    else:
        st = YELLOW
    detail = _t(lang,
                f"需要 {w['total']} 周（伦理 {w['ethics']} + 招募 {w['recruit']} + 干预 {w['intervention']} + 测试 {w['testing']} + 分析写作 {w['writing']}），"
                f"可用 {avail} 周，余量 {slack} 周。",
                f"needs {w['total']} weeks (ethics {w['ethics']} + recruitment {w['recruit']} + intervention {w['intervention']} + testing {w['testing']} "
                f"+ analysis/writing {w['writing']}); {avail} available; slack {slack}.")
    return Check("time", st, _t(lang, "时间", "Time"), detail, rule, {**w, "available": avail, "slack": slack})


def check_measures(b: Brief, lang: str) -> Check:
    rule = _t(lang, "主要结局缺设备 = 红；次要结局缺设备 = 黄；没有写 needs 的指标不检查",
              "primary outcome without its instrument = red; secondary = yellow; outcomes without `needs` are not checked")
    have = [e.lower() for e in b.constraints.equipment]
    missing_primary, missing_other, unchecked = [], [], []
    for o in b.outcomes:
        if not o.needs:
            unchecked.append(o.name)
            continue
        ok = any(o.needs.lower() in h or h in o.needs.lower() for h in have)
        if not ok:
            (missing_primary if o.primary else missing_other).append(f"{o.label or o.name}（{o.needs}）")
    st = RED if missing_primary else YELLOW if missing_other else GREEN
    bits = []
    if missing_primary:
        bits.append(_t(lang, "主要结局缺设备：", "primary outcome lacks: ") + "、".join(missing_primary))
    if missing_other:
        bits.append(_t(lang, "次要结局缺设备：", "secondary outcomes lack: ") + "、".join(missing_other))
    if not bits:
        bits.append(_t(lang, "已列出的测量都有设备", "every listed measurement has its instrument"))
    if unchecked:
        bits.append(_t(lang, f"未检查（没写 needs）：{', '.join(unchecked)}", f"not checked (no `needs`): {', '.join(unchecked)}"))
    return Check("measures", st, _t(lang, "测量与设备", "Measures and equipment"), "；".join(bits) if lang == "zh" else "; ".join(bits), rule,
                 {"missing_primary": missing_primary, "missing_other": missing_other, "unchecked": unchecked})


def check_ethics(b: Brief, lang: str) -> Check:
    rule = _t(lang, "已批准/无需 = 绿；审批中 = 黄；尚未开始 = 黄（红，若时间检查为红）；涉及未成年人或患者 = 至少黄",
              "approved / not needed = green; pending = yellow; not started = yellow (red if the time check is red); minors or patients = at least yellow")
    c = b.constraints
    st = GREEN if c.ethics in ("approved", "not_needed") else YELLOW
    note = {"approved": _t(lang, "伦理已批准", "ethics approved"),
            "not_needed": _t(lang, "无需伦理审查（请向学院确认：只用已脱敏的既有数据或匿名问卷常见，但要书面确认）",
                             "ethics review not needed (confirm in writing with the department)"),
            "pending": _t(lang, "伦理审批中：批准前不能招募或收集数据", "ethics pending: no recruitment or data collection before approval"),
            "not_started": _t(lang, "伦理尚未开始：先与学院确认流程与周期", "ethics not started: confirm the process and lead time first")}[c.ethics]
    if c.vulnerable_population:
        st = YELLOW if st == GREEN else st
        note += _t(lang, "；涉及未成年人/患者，需要监护人同意或医疗机构配合", "; minors/patients involved: guardian consent or clinical cooperation needed")
    return Check("ethics", st, _t(lang, "伦理", "Ethics"), note, rule, {"ethics": c.ethics, "vulnerable": c.vulnerable_population})


def check_stats(b: Brief, choice: DesignChoice, lang: str) -> Check:
    rule = _t(lang, "绿：计划分析所需的统计水平 ≤ 你自评的水平；黄：高一级；红：高两级（改用备选分析）",
              "green: required level <= your stated level; yellow: one level above; red: two levels above (use the fallback analysis)")
    gap = comfort_gap(b, choice)
    st = [GREEN, YELLOW, RED][min(gap, 2)]
    if gap:
        detail = _t(lang, f"计划分析「{choice.analysis}」需要 {choice.comfort} 水平，你自评 {b.constraints.stats_comfort}。备选：{choice.fallback}",
                    f"planned analysis '{choice.analysis}' needs {choice.comfort}, you stated {b.constraints.stats_comfort}. Fallback: {choice.fallback}")
    else:
        detail = _t(lang, f"计划分析：{choice.analysis}", f"planned analysis: {choice.analysis}")
    return Check("stats", st, _t(lang, "统计分析", "Analysis"), detail, rule, {"required": choice.comfort, "stated": b.constraints.stats_comfort})


def check_design(choice: DesignChoice, lang: str) -> Optional[Check]:
    if not choice.warnings:
        return None
    return Check("design", YELLOW, _t(lang, "设计", "Design"), "；".join(choice.warnings) if lang == "zh" else "; ".join(choice.warnings),
                 _t(lang, "设计规则触发了警告（见设计映射表）", "a design rule raised a warning (see the design table)"), {})


def check_evidence(ev: Optional[Evidence], lang: str) -> Check:
    rule = _t(lang, "直接重叠（人群+干预+结局，近五年）：0 = 绿；1–3 = 绿（需说明差异）；4–9 = 黄；≥10 = 红；记录集 < 30 条 = 黄（只是草图）",
              "direct overlap (population + intervention + outcome, last 5 years): 0 = green; 1-3 = green (state the difference); 4-9 = yellow; >= 10 = red; < 30 records = yellow (a sketch)")
    title = _t(lang, "撞题", "Overlap with existing work")
    if ev is None or ev.n_records == 0:
        return Check("evidence", YELLOW, title, _t(lang, "没有记录集：先检索（或导出 CNKI / PubMed 结果）再判断", "no record set: search (or export CNKI / PubMed results) first"), rule, {})
    st = {"none": GREEN, "few": GREEN, "crowded": YELLOW, "very_crowded": RED}[ev.tier]
    if ev.coverage == "low" and st == GREEN:
        st = YELLOW
    detail = _t(lang, f"{ev.n_records} 条记录；近 {ev.window[1] - ev.window[0] + 1} 年直接重叠 {ev.direct_recent} 条（全部年份 {ev.direct_all}）。",
                f"{ev.n_records} records; direct overlap in the last {ev.window[1] - ev.window[0] + 1} years: {ev.direct_recent} ({ev.direct_all} in all years).")
    if ev.coverage == "low":
        detail += _t(lang, f"记录集不足 {30} 条，只是草图。", " Fewer than 30 records: a sketch only.")
    return Check("evidence", st, title, detail, rule, {"direct_recent": ev.direct_recent, "direct_all": ev.direct_all, "n_records": ev.n_records, "coverage": ev.coverage})


def assess(b: Brief, choice: DesignChoice, plan: SamplePlan, ev: Optional[Evidence], lang: str = "zh") -> Dict:
    checks = [check_sample(b, plan, lang), check_time(b, lang), check_measures(b, lang), check_ethics(b, lang), check_stats(b, choice, lang)]
    dchk = check_design(choice, lang)
    if dchk:
        checks.append(dchk)
    checks.append(check_evidence(ev, lang))
    # ethics not started + red time = red (the rule written on the check)
    t = next(c for c in checks if c.id == "time")
    e = next(c for c in checks if c.id == "ethics")
    if b.constraints.ethics == "not_started" and t.status == RED:
        e.status = RED
    overall = max((c.status for c in checks), key=lambda s: RANK[s])
    return {"overall": overall, "checks": checks}
