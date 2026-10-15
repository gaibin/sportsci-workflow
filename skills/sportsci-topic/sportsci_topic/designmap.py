"""Question type -> study design, as an explicit rule table (no model, no scoring).

The six designs are the ones the results engine in `sportsci-figures` can analyse: parallel_prepost, crossover,
multitime, single_group, survey, meta. Each rule says what claim the design permits and what it does not.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .brief import Brief

COMFORT_RANK = {"basic": 0, "intermediate": 1, "advanced": 2}


def tr(lang: str, zh: str, en: str) -> str:
    return zh if lang == "zh" else en


@dataclass
class DesignChoice:
    design: str
    rule: str                      # the rule that fired, in plain words
    permits: str                   # what the design lets the author claim
    forbids: str                   # what it does not
    analysis: str                  # the planned primary analysis
    fallback: str                  # simpler analysis if the author cannot run the planned one
    comfort: str                   # statistical comfort the planned analysis needs
    warnings: List[str] = field(default_factory=list)


def choose_design(b: Brief, lang: str = "zh") -> DesignChoice:
    qt, d = b.question_type, b.design
    w: List[str] = []

    if qt == "synthesis":
        return DesignChoice(
            "meta",
            tr(lang, "问题类型是证据综合 → 系统综述 / 元分析", "question type is evidence synthesis -> systematic review / meta-analysis"),
            tr(lang, "合并既有研究的效应量，评估异质性与偏倚", "pool existing effect sizes; assess heterogeneity and bias"),
            tr(lang, "不产生新的实验数据；结论受纳入研究质量限制", "creates no new experimental data; conclusions are limited by included-study quality"),
            tr(lang, "随机效应模型（Hartung–Knapp 调整）；k≥10 才做漏斗图与元回归", "random-effects model (Hartung-Knapp); funnel plot and meta-regression only if k >= 10"),
            tr(lang, "固定效应 + 森林图；k<10 时只做描述性合并", "fixed-effect + forest plot; descriptive pooling if k < 10"),
            "advanced", w)

    if qt == "association":
        return DesignChoice(
            "survey",
            tr(lang, "问题类型是变量关联（问卷）→ 横断面问卷", "question type is association (questionnaire) -> cross-sectional survey"),
            tr(lang, "报告变量之间的关联与统计上的中介 / 调节", "report associations and statistical mediation / moderation"),
            tr(lang, "不能做因果推断；同源方法偏差需要检验", "no causal claim; common-method bias must be examined"),
            tr(lang, "信度（Cronbach α）、效度（KMO/EFA）、相关与回归，必要时 bootstrap 中介", "reliability (alpha), validity (KMO/EFA), correlation and regression; bootstrap mediation if needed"),
            tr(lang, "α + 相关 + 多元线性回归", "alpha + correlation + multiple linear regression"),
            "intermediate", w)

    if qt == "acute":
        if d.has_control and not d.conditions:
            w.append(tr(lang, "急性反应通常用受试者自身对照（交叉）；设计里没有写出条件顺序 [design].conditions",
                        "acute responses normally use a within-participant crossover; [design].conditions is empty"))
        return DesignChoice(
            "crossover",
            tr(lang, "问题类型是急性反应 → 受试者自身对照的交叉设计", "question type is acute response -> within-participant crossover"),
            tr(lang, "比较同一批人在不同条件下的即刻反应", "compare the same people across conditions"),
            tr(lang, "不能推断长期适应；需要洗脱期与随机顺序", "no inference about chronic adaptation; needs washout and randomised order"),
            tr(lang, "线性混合模型（条件、周期、个体随机截距），Holm 校正计划内比较", "linear mixed model (condition, period, random participant intercept); Holm for planned contrasts"),
            tr(lang, "配对 t 检验 / 重复测量方差分析", "paired t-test / repeated-measures ANOVA"),
            "advanced", w)

    if qt == "course":
        return DesignChoice(
            "multitime",
            tr(lang, "问题类型是时间进程 → 多时间点重复测量", "question type is time course -> repeated assessments over time"),
            tr(lang, "描述各时间点的变化轨迹及组间差异", "describe trajectories and group differences over time"),
            tr(lang, "没有对照组时不能把变化归因于干预", "without a control group change cannot be attributed to the intervention"),
            tr(lang, "线性混合模型（组 × 时间）；补充混合方差分析（GG 校正）", "linear mixed model (group x time); supplementary mixed ANOVA with GG correction"),
            tr(lang, "各时间点分别做 ANCOVA / t 检验（标注探索性）", "ANCOVA / t-test at each time point (label as exploratory)"),
            "advanced", w + ([] if d.timepoints >= 3 else [tr(
                lang, f"时间进程设计需要 ≥3 个测量点，简报里是 {d.timepoints}",
                f"a time-course design needs >= 3 assessments, the brief has {d.timepoints}")]))

    # qt == "effect"
    if not d.has_control:
        return DesignChoice(
            "single_group",
            tr(lang, "干预效果但没有对照组 → 单组前后测 / 重复测量", "intervention effect with no control group -> single-group pre-post / repeated measures"),
            tr(lang, "报告干预前后的变化及其置信区间", "report the change and its confidence interval"),
            tr(lang, "不能把变化归因于干预（成熟、学习效应、回归均值都可能）", "the change cannot be attributed to the intervention (maturation, learning, regression to the mean)"),
            tr(lang, "配对 t 检验 / 重复测量方差分析（Mauchly + GG 校正）", "paired t-test / repeated-measures ANOVA (Mauchly + GG)"),
            tr(lang, "配对 t 检验 + Wilcoxon 符号秩检验", "paired t-test + Wilcoxon signed-rank"),
            "basic", [tr(lang, "没有对照组：论文只能写前后变化。能否补一个对照组或等待名单对照？",
                         "no control group: the thesis can only report before/after change. Can a control or wait-list group be added?")])
    if d.timepoints >= 3:
        return DesignChoice(
            "multitime",
            tr(lang, "有对照组且测量点 ≥3 → 平行分组多时间点", "control group and >= 3 assessments -> parallel groups, repeated assessments"),
            tr(lang, "比较各组随时间的变化，估计干预效应及其持续性", "compare change over time between groups; estimate the intervention effect and its durability"),
            tr(lang, "时间点之间的多重比较需要说明校正方法", "multiple comparisons across time points need a stated correction"),
            tr(lang, "线性混合模型（组 × 时间）；补充混合方差分析（GG 校正）", "linear mixed model (group x time); supplementary mixed ANOVA with GG correction"),
            tr(lang, "只取终测做 ANCOVA（基线为协变量），其余时间点标注探索性", "ANCOVA at the final assessment (baseline covariate); other time points exploratory"),
            "advanced", w)
    return DesignChoice(
        "parallel_prepost",
        tr(lang, "有对照组且前后测各一次 → 平行分组前后测", "control group and one pre / one post assessment -> parallel-group pre-post"),
        tr(lang, "估计干预相对对照的效应（组间差及 95% CI），在随机分组时可作因果解释",
            "estimate the intervention effect against control (difference + 95% CI); causal reading if randomised"),
        tr(lang, "非随机分组时必须说明基线差异；不能写成"
                 "“证明了”", "if not randomised, baseline imbalance must be stated; do not write \"proved\""),
        tr(lang, "终测的 ANCOVA（基线为协变量）；报告组间差、95% CI、Hedges g", "ANCOVA on the post score with baseline as covariate; between-group difference, 95% CI, Hedges g"),
        tr(lang, "变化量（后−前）的独立样本 t 检验", "independent t-test on change scores (post - pre)"),
        "intermediate", w)


def comfort_gap(b: Brief, choice: DesignChoice) -> int:
    """How many levels the planned analysis is above the student's stated comfort (0 = fine)."""
    return max(0, COMFORT_RANK[choice.comfort] - COMFORT_RANK.get(b.constraints.stats_comfort, 1))
