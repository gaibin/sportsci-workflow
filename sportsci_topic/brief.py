"""The topic brief: one small TOML file that holds everything the rest of the toolkit needs.

A brief is deliberately a form, not prose. Every field is either a fact the student knows (how many people they can
recruit, how many weeks they have) or a search vocabulary (Chinese and English terms for each part of the question).
Nothing in it is a research result.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

QUESTION_TYPES = ("effect", "acute", "course", "association", "synthesis")
GOALS = ("thesis", "journal", "grant", "course")
FACET_KEYS = ("population", "intervention", "comparator", "outcome")
FACET_CODE = {"population": "P", "intervention": "I", "comparator": "C", "outcome": "O"}
ETHICS = ("approved", "pending", "not_started", "not_needed")
COMFORT = ("basic", "intermediate", "advanced")
DIRECTIONS = ("higher_better", "lower_better", "neutral")


class BriefError(ValueError):
    """The brief cannot be used; the message lists every problem found."""


@dataclass
class Facet:
    label: str = ""
    terms: List[str] = field(default_factory=list)
    note: str = ""

    def has_cjk(self) -> bool:
        return any("一" <= ch <= "鿿" for t in self.terms for ch in t)

    def has_latin(self) -> bool:
        return any(any(ch.isascii() and ch.isalpha() for ch in t) for t in self.terms)


@dataclass
class Outcome:
    name: str
    label: str = ""
    label_en: str = ""
    unit: str = ""
    primary: bool = False
    direction: str = "neutral"
    decimals: int = 1
    category: str = "Outcomes"
    needs: str = ""  # instrument / test the measurement depends on, matched against constraints.equipment


@dataclass
class Scale:
    name: str
    label: str = ""
    label_en: str = ""
    n_items: int = 5
    role: str = "x"  # x | y | m | w | covariate


@dataclass
class DesignInfo:
    has_control: bool = True
    timepoints: int = 2
    groups: List[str] = field(default_factory=list)  # first = control
    groups_en: List[str] = field(default_factory=list)
    time_labels: List[str] = field(default_factory=list)
    time_labels_en: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)  # crossover; first = control
    conditions_en: List[str] = field(default_factory=list)


@dataclass
class Constraints:
    accessible_n: int = 0
    dropout: float = 0.15
    weeks_available: int = 0
    intervention_weeks: int = 0
    recruit_weeks: int = 2
    test_weeks: int = 2
    writing_weeks: int = 6
    ethics: str = "not_started"
    ethics_weeks: Optional[int] = None
    vulnerable_population: bool = False
    equipment: List[str] = field(default_factory=list)
    stats_comfort: str = "intermediate"
    supervisor_direction: str = ""


@dataclass
class Effect:
    source: str = ""
    kind: str = ""  # d | dz | ancova | r | f | f2 | "" (derive from design)
    d: Optional[float] = None
    dz: Optional[float] = None
    delta: Optional[float] = None
    sd: Optional[float] = None
    r_prepost: Optional[float] = None
    r: Optional[float] = None
    f: Optional[float] = None
    f2: Optional[float] = None
    predictors: int = 3
    groups: int = 3
    alpha: float = 0.05
    power: float = 0.80
    contrasts: int = 1


@dataclass
class Brief:
    title: str = ""
    language: str = "zh"
    goal: str = "thesis"
    question_type: str = "effect"
    facets: Dict[str, Facet] = field(default_factory=dict)
    outcomes: List[Outcome] = field(default_factory=list)
    scales: List[Scale] = field(default_factory=list)
    design: DesignInfo = field(default_factory=DesignInfo)
    constraints: Constraints = field(default_factory=Constraints)
    effect: Effect = field(default_factory=Effect)
    variants: Dict[str, List[Facet]] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)

    def facet(self, key: str) -> Facet:
        return self.facets.get(key) or Facet()

    @property
    def primary_outcome(self) -> Optional[Outcome]:
        for o in self.outcomes:
            if o.primary:
                return o
        return None


# ----------------------------------------------------------------------------------------------------------- loading

def _as_list(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [v] if v.strip() else []
    return [str(x).strip() for x in v if str(x).strip()]


def _facet(d: Any) -> Facet:
    if isinstance(d, str):
        return Facet(label=d, terms=[d])
    d = d or {}
    terms = _as_list(d.get("terms"))
    label = str(d.get("label") or (terms[0] if terms else ""))
    return Facet(label=label, terms=terms, note=str(d.get("note") or ""))


def _pick(d: Dict[str, Any], cls, **extra):
    names = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
    return cls(**{k: v for k, v in d.items() if k in names}, **extra)


def from_dict(raw: Dict[str, Any]) -> Brief:
    topic = raw.get("topic", {}) or {}
    b = Brief(
        title=str(topic.get("working_title") or topic.get("title") or ""),
        language=str(topic.get("language") or "zh"),
        goal=str(topic.get("goal") or "thesis"),
        question_type=str(topic.get("question_type") or "effect"),
        raw=raw,
    )
    pico = raw.get("pico", {}) or {}
    for k in FACET_KEYS:
        if k in pico:
            b.facets[k] = _facet(pico[k])
    for o in raw.get("outcomes", []) or []:
        if "name" not in o:
            continue
        o = dict(o)
        o["label_en"] = o.get("label_en") or o.get("label") or o["name"]
        o["label"] = o.get("label") or o["name"]
        b.outcomes.append(_pick(o, Outcome))
    for s in raw.get("scales", []) or []:
        if "name" not in s:
            continue
        s = dict(s)
        s["label_en"] = s.get("label_en") or s.get("label") or s["name"]
        s["label"] = s.get("label") or s["name"]
        b.scales.append(_pick(s, Scale))
    dz = dict(raw.get("design", {}) or {})
    for k in ("groups", "groups_en", "time_labels", "time_labels_en", "conditions", "conditions_en"):
        dz[k] = _as_list(dz.get(k))
    b.design = _pick(dz, DesignInfo)
    cz = dict(raw.get("constraints", {}) or {})
    cz["equipment"] = _as_list(cz.get("equipment"))
    b.constraints = _pick(cz, Constraints)
    b.effect = _pick(dict(raw.get("effect", {}) or {}), Effect)
    for axis, items in (raw.get("variants", {}) or {}).items():
        b.variants[axis] = [_facet(i) for i in (items or [])]
    return b


def load_brief(path: str | Path) -> Brief:
    p = Path(path)
    try:
        raw = tomllib.loads(p.read_text(encoding="utf-8-sig"))
    except tomllib.TOMLDecodeError as e:
        raise BriefError(f"{p.name}: not valid TOML — {e}") from e
    return from_dict(raw)


# -------------------------------------------------------------------------------------------------------- validation

def validate(b: Brief) -> Tuple[List[str], List[str]]:
    """(errors, warnings). Errors block the pipeline, warnings are listed on the card."""
    e: List[str] = []
    w: List[str] = []
    if b.question_type not in QUESTION_TYPES:
        e.append(f"topic.question_type must be one of {QUESTION_TYPES}, got {b.question_type!r}")
    if b.goal not in GOALS:
        w.append(f"topic.goal {b.goal!r} is not one of {GOALS}")
    if b.language not in ("zh", "en"):
        e.append("topic.language must be 'zh' or 'en'")
    if not b.title:
        w.append("topic.working_title is empty")

    need = ("population", "intervention", "outcome")
    for k in need:
        f = b.facets.get(k)
        if not f or not f.terms:
            e.append(f"pico.{k}.terms: list at least one search term (Chinese and English if you can)")
            continue
        if not f.has_latin():
            w.append(f"pico.{k}: no English term — international databases will not match it")
        if not f.has_cjk():
            w.append(f"pico.{k}: no Chinese term — CNKI / Wanfang results will not be matched")
    if "comparator" in b.facets and not b.facets["comparator"].terms:
        w.append("pico.comparator has no terms")

    seen = set()
    for o in b.outcomes:
        if o.name in seen:
            e.append(f"outcomes: duplicate name {o.name!r}")
        seen.add(o.name)
        if o.direction not in DIRECTIONS:
            e.append(f"outcomes[{o.name}].direction must be one of {DIRECTIONS}")
    if b.question_type != "association":
        if not b.outcomes:
            e.append("outcomes: list at least one outcome (name, label, unit, primary, direction)")
        else:
            n_primary = sum(1 for o in b.outcomes if o.primary)
            if n_primary != 1:
                e.append(f"outcomes: exactly one outcome must have primary = true (found {n_primary}); "
                         "the primary outcome is fixed before data are seen")
    else:
        if len(b.scales) < 2:
            e.append("scales: an association study needs at least two scales (name, label, n_items, role)")
        roles = [s.role for s in b.scales]
        if "y" not in roles:
            e.append("scales: one scale needs role = \"y\" (the outcome scale)")
        if "x" not in roles:
            e.append("scales: one scale needs role = \"x\" (the predictor scale)")

    c = b.constraints
    if b.question_type != "synthesis":
        if c.accessible_n <= 0:
            e.append("constraints.accessible_n: how many participants can you realistically recruit?")
        if c.weeks_available <= 0:
            e.append("constraints.weeks_available: how many weeks until the deadline?")
    if not 0 <= c.dropout < 0.9:
        e.append("constraints.dropout must be between 0 and 0.9")
    if c.ethics not in ETHICS:
        e.append(f"constraints.ethics must be one of {ETHICS}")
    if c.stats_comfort not in COMFORT:
        e.append(f"constraints.stats_comfort must be one of {COMFORT}")
    if b.question_type in ("effect", "acute", "course") and c.intervention_weeks <= 0 and b.question_type != "acute":
        w.append("constraints.intervention_weeks is 0 — the time budget will not include the intervention")
    ef = b.effect
    if not 0 < ef.alpha < 0.5 or not 0.5 <= ef.power < 1:
        e.append("effect.alpha must be in (0, 0.5) and effect.power in [0.5, 1)")
    for axis in b.variants:
        if axis not in FACET_KEYS:
            e.append(f"variants.{axis}: axis must be one of {FACET_KEYS}")
    return e, w


def require_valid(b: Brief) -> List[str]:
    errs, warns = validate(b)
    if errs:
        raise BriefError("\n  - ".join(["The brief has problems:"] + errs))
    return warns


# ---------------------------------------------------------------------------------------------------------- template

TEMPLATE = '''\
# sportsci-topic 选题简报 / topic brief
# 这是一张表，不是论文：只填你知道的事实和检索词，不要填"预期结果"。
# Fill facts and search vocabulary only. Nothing here is a result.

[topic]
working_title = "8周功能性训练对大学生下肢爆发力的影响"
language = "zh"                  # zh | en  — 选题卡的语言
goal = "thesis"                  # thesis | journal | grant | course
question_type = "effect"         # effect 干预效果 | acute 急性反应 | course 时间进程 | association 问卷关联 | synthesis 证据综合

# ---- 研究问题的四个部分。每部分写中英文检索词（同义词越全，证据地图越准）----
[pico.population]
label = "大学生"
terms = ["大学生", "高校学生", "university students", "college students"]

[pico.intervention]
label = "功能性训练"
terms = ["功能性训练", "功能训练", "functional training"]

[pico.comparator]
label = "常规体育课"
terms = ["常规体育课", "对照组", "control group"]

[pico.outcome]
label = "下肢爆发力"
terms = ["下肢爆发力", "纵跳", "countermovement jump", "vertical jump", "lower limb power"]

# ---- 测量指标：必须有且只有一个 primary = true（看数据前就定下来）----
[[outcomes]]
name = "cmj"
label = "纵跳高度"
label_en = "Countermovement jump height"
unit = "cm"
primary = true
direction = "higher_better"
needs = "jump mat"

[[outcomes]]
name = "sprint30"
label = "30 m 冲刺时间"
label_en = "30-m sprint time"
unit = "s"
direction = "lower_better"
needs = "timing gates"

# ---- 设计信息 ----
[design]
has_control = true               # 有没有对照组
timepoints = 2                   # 测几次（基线+终测 = 2）
groups = ["对照组", "干预组"]     # 第一个是对照
groups_en = ["Control", "Intervention"]
time_labels = ["基线", "第8周"]
time_labels_en = ["Baseline", "Week 8"]

# ---- 现实约束 ----
[constraints]
accessible_n = 40                # 你实际能招到多少人
dropout = 0.15                   # 预计脱落比例
weeks_available = 28             # 距离提交还有几周
intervention_weeks = 8
recruit_weeks = 2
test_weeks = 2                   # 基线+终测各占的周数合计
writing_weeks = 6                # 分析与写作预留
ethics = "pending"               # approved | pending | not_started | not_needed
vulnerable_population = false    # 未成年人 / 患者等
equipment = ["jump mat", "timing gates"]
stats_comfort = "intermediate"   # basic | intermediate | advanced
supervisor_direction = ""        # 导师的研究方向（只出现在选题卡里）

# ---- 样本量依据：效应量必须写来源（文献 DOI / 预实验 / 最小有意义差异）----
[effect]
source = ""                      # 例如 "Smith 2022 doi:10.xxxx Table 2" 或 "smallest effect of interest"
d = 0.7                          # 标准化组间差（d）；ANCOVA 可改填 delta / sd / r_prepost
alpha = 0.05
power = 0.80

# ---- 想比较的变体（可选）：每个轴给几个替代选项，由 variants 命令统计各自的重叠 ----
[[variants.population]]
label = "高中生"
terms = ["高中生", "high school students", "adolescents"]

[[variants.outcome]]
label = "变向能力"
terms = ["变向能力", "agility", "change of direction"]
'''


def write_template(path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(TEMPLATE, encoding="utf-8")
    return p
