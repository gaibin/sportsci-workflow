"""Sample size and achievable power, computed — never read from a template.

Exact noncentral-t / noncentral-F power for the tests the six designs use. Two directions are offered because the
student's real constraint is the second one:

    required_n(effect)      how many people does this effect need?
    achieved(n)             with the people I can actually recruit, what power do I have, and what is the smallest
                            effect I could detect (MDES)?
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from scipy import optimize, stats

from .brief import Brief
from .designmap import DesignChoice

MAX_N = 200_000


# -------------------------------------------------------------------------------------------------- power functions

def _power_nct(ncp: float, df: float, alpha: float, two_sided: bool = True) -> float:
    if df < 1:
        return 0.0
    if ncp > 35:  # scipy's nct.cdf returns NaN far in the tail; power is 1 to machine precision there
        return 1.0
    if two_sided:
        tc = stats.t.ppf(1 - alpha / 2, df)
        p = float(1 - stats.nct.cdf(tc, df, ncp) + stats.nct.cdf(-tc, df, ncp))
    else:
        tc = stats.t.ppf(1 - alpha, df)
        p = float(1 - stats.nct.cdf(tc, df, ncp))
    return p if math.isfinite(p) else (1.0 if ncp > 10 else 0.0)


def power_two_sample(d: float, n1: int, n2: Optional[int] = None, alpha: float = 0.05, two_sided: bool = True, covariates: int = 0) -> float:
    n2 = n2 or n1
    return _power_nct(abs(d) * math.sqrt(n1 * n2 / (n1 + n2)), n1 + n2 - 2 - covariates, alpha, two_sided)


def power_paired(dz: float, n: int, alpha: float = 0.05, two_sided: bool = True) -> float:
    return _power_nct(abs(dz) * math.sqrt(n), n - 1, alpha, two_sided)


def power_correlation(r: float, n: int, alpha: float = 0.05) -> float:
    if n <= 3:
        return 0.0
    z = math.atanh(abs(r)) * math.sqrt(n - 3)
    zc = stats.norm.ppf(1 - alpha / 2)
    return float(stats.norm.cdf(z - zc) + stats.norm.cdf(-z - zc))


def power_anova(f: float, n_total: int, k: int, alpha: float = 0.05) -> float:
    df1, df2 = k - 1, n_total - k
    if df2 < 1:
        return 0.0
    fc = stats.f.ppf(1 - alpha, df1, df2)
    return float(1 - stats.ncf.cdf(fc, df1, df2, f * f * n_total))


def power_regression(f2: float, n_total: int, predictors: int, tested: Optional[int] = None, alpha: float = 0.05) -> float:
    u = tested or predictors
    df2 = n_total - predictors - 1
    if df2 < 1:
        return 0.0
    fc = stats.f.ppf(1 - alpha, u, df2)
    return float(1 - stats.ncf.cdf(fc, u, df2, f2 * n_total))


def _smallest_n(power_fn, target: float, lo: int = 3) -> int:
    """Smallest integer n >= lo with power_fn(n) >= target (power is monotone in n)."""
    if power_fn(lo) >= target:
        return lo
    hi = max(lo * 2, 8)
    while power_fn(hi) < target:
        hi *= 2
        if hi > MAX_N:
            return MAX_N
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if power_fn(mid) >= target:
            hi = mid
        else:
            lo = mid
    return hi


def n_two_sample(d: float, alpha: float = 0.05, power: float = 0.8, ratio: float = 1.0, two_sided: bool = True, covariates: int = 0) -> int:
    """Participants in group 1 (group 2 = ceil(ratio * n1))."""
    return _smallest_n(lambda n: power_two_sample(d, n, math.ceil(ratio * n), alpha, two_sided, covariates), power)


def n_paired(dz: float, alpha: float = 0.05, power: float = 0.8, two_sided: bool = True) -> int:
    return _smallest_n(lambda n: power_paired(dz, n, alpha, two_sided), power)


def n_correlation(r: float, alpha: float = 0.05, power: float = 0.8) -> int:
    return _smallest_n(lambda n: power_correlation(r, n, alpha), power, lo=5)


def n_anova(f: float, k: int, alpha: float = 0.05, power: float = 0.8) -> int:
    """Total N for k equal groups (rounded up to a multiple of k, as G*Power reports it)."""
    n = _smallest_n(lambda n: power_anova(f, n, k, alpha), power, lo=k + 2)
    return int(math.ceil(n / k) * k)


def n_regression(f2: float, predictors: int, tested: Optional[int] = None, alpha: float = 0.05, power: float = 0.8) -> int:
    return _smallest_n(lambda n: power_regression(f2, n, predictors, tested, alpha), power, lo=predictors + 3)


def _solve_effect(power_of_effect, target: float, lo: float = 1e-3, hi: float = 6.0) -> float:
    if power_of_effect(hi) < target:
        return float("inf")
    return float(optimize.brentq(lambda e: power_of_effect(e) - target, lo, hi, xtol=1e-4))


def mdes_two_sample(n1: int, n2: Optional[int] = None, alpha: float = 0.05, power: float = 0.8, covariates: int = 0) -> float:
    return _solve_effect(lambda d: power_two_sample(d, n1, n2, alpha, True, covariates), power)


def mdes_paired(n: int, alpha: float = 0.05, power: float = 0.8) -> float:
    return _solve_effect(lambda d: power_paired(d, n, alpha), power)


def mdes_correlation(n: int, alpha: float = 0.05, power: float = 0.8) -> float:
    return _solve_effect(lambda r: power_correlation(r, n, alpha), power, hi=0.99)


def inflate(n: int, dropout: float) -> int:
    return int(math.ceil(n / (1.0 - dropout))) if dropout > 0 else int(n)


# -------------------------------------------------------------------------------------------------- planning layer

@dataclass
class SamplePlan:
    test: str                              # two_sample | ancova | paired | correlation | none
    effect_label: str                      # e.g. "d = 0.70"
    effect_value: Optional[float]
    source: str
    n_per_group: Optional[int] = None      # analysed participants per group (or total for single-sample tests)
    n_total: Optional[int] = None
    n_enrol_total: Optional[int] = None
    groups: int = 1
    accessible_enrol: int = 0
    accessible_analysed: int = 0
    power_at_accessible: Optional[float] = None
    mdes_at_accessible: Optional[float] = None
    mdes_label: str = ""
    sensitivity: List[Dict] = field(default_factory=list)
    rules: List[str] = field(default_factory=list)
    status: str = "ok"                     # ok | no_effect | not_applicable
    assumptions: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


def _groups(b: Brief, choice: DesignChoice) -> int:
    if choice.design in ("parallel_prepost", "multitime"):
        return max(2, len(b.design.groups))
    return 1


def plan_sample(b: Brief, choice: DesignChoice, lang: str = "zh") -> SamplePlan:
    zh = lang == "zh"
    ef, c = b.effect, b.constraints
    drop = c.dropout
    alpha = ef.alpha / max(1, ef.contrasts)
    design = choice.design
    src = (ef.source or "").strip()
    acc_enrol = c.accessible_n
    acc_an = int(math.floor(acc_enrol * (1 - drop)))

    if design == "meta":
        return SamplePlan("none", "", None, src, status="not_applicable", rules=[
            "k ≥ 2 即可合并，但 k < 5 时随机效应的异质性估计不可靠；漏斗图与元回归至少需要 10 项研究（Cochrane 手册建议）。" if zh else
            "k >= 2 can be pooled, but heterogeneity is unreliable with k < 5; funnel plots and meta-regression need at least 10 studies (Cochrane Handbook).",
            "样本量的问题变成「能检索到多少项合格研究」：先做检索与筛选再决定。" if zh else
            "The sample-size question becomes 'how many eligible studies exist': search and screen first."])

    if design == "survey":
        n_items = sum(s.n_items for s in b.scales)
        n_pred = max(1, sum(1 for s in b.scales if s.role in ("x", "m", "w", "covariate")))
        rules = [
            (f"探索性因子分析：常用经验规则为每个题项 5–10 人且不少于 200 人 → {max(200, 5 * n_items)}–{max(200, 10 * n_items)}（{n_items} 题）" if zh else
             f"EFA rule of thumb: 5-10 respondents per item and at least 200 -> {max(200, 5 * n_items)}-{max(200, 10 * n_items)} ({n_items} items)"),
            (f"多元回归：N ≥ 50 + 8 × 预测变量数 → {50 + 8 * n_pred}（Green 1991 的经验规则；效应量已知时用下面的精确计算）" if zh else
             f"multiple regression: N >= 50 + 8 x predictors -> {50 + 8 * n_pred} (Green 1991 rule; use the exact calculation when an effect size is known)"),
            ("bootstrap 中介：没有简单公式，建议 N ≥ 200，并在效应量依据里写明预期路径系数" if zh else
             "bootstrap mediation has no closed-form power: aim for N >= 200 and state the expected path coefficients"),
        ]
        plan = SamplePlan("correlation", "", None, src, groups=1, accessible_enrol=acc_enrol, accessible_analysed=acc_an,
                          rules=rules, status="ok" if ef.r or ef.f2 else "no_effect")
        floor_n = max(200, 5 * n_items, 50 + 8 * n_pred)
        plan.n_total = floor_n
        plan.n_enrol_total = inflate(floor_n, drop)
        plan.assumptions = "rule-of-thumb floor" if not zh else "经验规则下限"
        if ef.r and ef.kind in ("", "r"):
            plan.effect_label, plan.effect_value = f"r = {ef.r:.2f}", ef.r
            n = n_correlation(ef.r, alpha, ef.power)
            plan.n_total = max(n, floor_n)
            plan.n_enrol_total = inflate(plan.n_total, drop)
            plan.mdes_at_accessible = mdes_correlation(max(acc_an, 5), alpha, ef.power)
            plan.power_at_accessible = power_correlation(ef.r, max(acc_an, 4), alpha)
            plan.mdes_label = "r"
            plan.assumptions = f"two-sided α = {alpha:.3g}, power = {ef.power:.2f}; the larger of exact n and the rule-of-thumb floor"
        elif ef.f2:
            tested = max(1, sum(1 for s in b.scales if s.role == "x"))
            n = n_regression(ef.f2, n_pred, tested, alpha, ef.power)
            plan.effect_label, plan.effect_value = f"f² = {ef.f2:.2f}", ef.f2
            plan.n_total = max(n, floor_n)
            plan.n_enrol_total = inflate(plan.n_total, drop)
            plan.power_at_accessible = power_regression(ef.f2, max(acc_an, n_pred + 2), n_pred, tested, alpha)
            plan.assumptions = f"fixed-model regression, {n_pred} predictors, α = {alpha:.3g}, power = {ef.power:.2f}"
        plan.sensitivity = [{"effect": f"r = {r}", "n": n_correlation(r, alpha, ef.power),
                             "power_at_accessible": power_correlation(r, max(acc_an, 4), alpha)} for r in (0.1, 0.2, 0.3, 0.5)]
        return plan

    # experimental designs ------------------------------------------------------------------------------------------
    g = _groups(b, choice)
    kind = ef.kind
    if not kind:
        if design in ("crossover", "single_group"):
            kind = "dz"
        elif ef.delta and ef.sd and ef.r_prepost is not None:
            kind = "ancova"
        else:
            kind = "d"

    d_eff: Optional[float] = None
    label = ""
    test = "two_sample"
    if kind == "ancova" and ef.delta and ef.sd and ef.r_prepost is not None:
        d_eff = ef.delta / (ef.sd * math.sqrt(max(1e-9, 1 - ef.r_prepost ** 2)))
        label = f"Δ = {ef.delta:g}, SD = {ef.sd:g}, r(pre,post) = {ef.r_prepost:.2f} → d_adj = {d_eff:.2f}"
        test = "ancova"
    elif kind in ("d", "ancova") and ef.d:
        d_eff, label, test = ef.d, f"d = {ef.d:.2f}", "two_sample"
    elif kind == "dz" and ef.dz:
        d_eff, label, test = ef.dz, f"dz = {ef.dz:.2f}", "paired"
    elif design in ("crossover", "single_group") and ef.d:
        d_eff, label, test = ef.d, f"dz ≈ d = {ef.d:.2f} (treated as paired)", "paired"
    elif design in ("crossover", "single_group") and ef.delta and ef.sd:
        d_eff, label, test = ef.delta / ef.sd, f"Δ = {ef.delta:g}, SD(diff) = {ef.sd:g} → dz = {ef.delta / ef.sd:.2f}", "paired"

    paired = design in ("crossover", "single_group")
    if paired:
        test = "paired"
    mdes_fn_label = "dz" if paired else "d"

    plan = SamplePlan(test if d_eff else ("paired" if paired else "two_sample"), label, d_eff, src, groups=g,
                      accessible_enrol=acc_enrol, accessible_analysed=acc_an)

    # sensitivity table: conventional magnitudes, labelled as such
    def need(e: float) -> int:
        return n_paired(e, alpha, ef.power) if paired else n_two_sample(e, alpha, ef.power, covariates=1 if design in ("parallel_prepost", "multitime") else 0)

    def pw(e: float) -> float:
        if paired:
            return power_paired(e, max(acc_an, 2), alpha)
        per = max(2, acc_an // g)
        return power_two_sample(e, per, per, alpha, True, 1 if design in ("parallel_prepost", "multitime") else 0)

    plan.sensitivity = [{"effect": f"{mdes_fn_label} = {e}", "n": need(e), "power_at_accessible": pw(e)} for e in (0.3, 0.5, 0.8)]

    per_acc = max(2, acc_an // g)
    if paired:
        plan.mdes_at_accessible = mdes_paired(max(acc_an, 3), alpha, ef.power)
    else:
        plan.mdes_at_accessible = mdes_two_sample(per_acc, per_acc, alpha, ef.power, 1 if design in ("parallel_prepost", "multitime") else 0)
    plan.mdes_label = mdes_fn_label

    if d_eff is None:
        plan.status = "no_effect"
        plan.rules.append("没有可用的效应量：不能给出样本量。下表只是常规量级的敏感性示意。" if zh else
                          "No usable effect size: a sample size cannot be stated. The table is a sensitivity illustration only.")
        return plan

    if not src:
        plan.rules.append("效应量没有写明来源（文献 DOI / 预实验 / 最小有意义差异）：样本量只作示意，不能写进开题。" if zh else
                          "The effect size has no stated source (paper DOI / pilot / smallest effect of interest): the sample size is illustrative only.")

    cov = 1 if design in ("parallel_prepost", "multitime") else 0
    if cov and not paired:
        plan.test = "ancova"
    if paired:
        n = n_paired(d_eff, alpha, ef.power)
        plan.n_per_group = n
        plan.n_total = n
        plan.power_at_accessible = power_paired(d_eff, max(acc_an, 2), alpha)
        plan.assumptions = f"paired t, two-sided α = {alpha:.3g}, power = {ef.power:.2f}"
    else:
        n = n_two_sample(d_eff, alpha, ef.power, covariates=cov)
        plan.n_per_group = n
        plan.n_total = n * g
        plan.power_at_accessible = power_two_sample(d_eff, per_acc, per_acc, alpha, True, cov)
        plan.assumptions = (f"{'ANCOVA (baseline as covariate; df - 1)' if cov else 'independent t'}, {g} equal groups, "
                            f"two-sided α = {alpha:.3g}, power = {ef.power:.2f}")
    plan.n_enrol_total = inflate(plan.n_total or 0, drop)
    if ef.contrasts > 1:
        plan.rules.append(f"α 已按 {ef.contrasts} 个计划内比较做 Bonferroni 调整（{ef.alpha:g} → {alpha:.3g}）" if zh else
                          f"alpha is Bonferroni-adjusted for {ef.contrasts} planned contrasts ({ef.alpha:g} -> {alpha:.3g})")
    if design == "multitime":
        plan.rules.append("多时间点混合模型没有闭式功效公式：这里按终测时点的 ANCOVA 估计，通常偏保守。" if zh else
                          "A repeated-measures mixed model has no closed-form power: this uses ANCOVA at the final time point, usually conservative.")
    return plan
