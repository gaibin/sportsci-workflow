# -*- coding: utf-8 -*-
"""Methods explained + defence Q&A (方法讲解与答辩问答) — the teaching deliverable of every results run.

The student must be able to explain and defend each analytic choice; this file walks through them with the numbers of
THEIR analysis (taken from the same result objects as the tables). Written as questions an examiner is likely to ask,
each with the reasoning and where the evidence sits in the output. Deterministic: no LLM involved.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np

QA = List[Tuple[str, str]]


def _common(T) -> QA:
    return [
        (T("为什么报告效应量和 95% 置信区间，而不只是 P 值？", "Why report effect sizes and 95% CIs, not only P values?"),
         T("P 值只回答“差异是否可能为零”，不说明差异有多大、估计有多精确。效应量（如 Hedges g、d_z、偏 η²、β）给出实际大小，95% CI 给出精度；"
           "主流期刊和 CONSORT 都要求两者并报。不要只写“P < 0.05，差异显著”。",
           "A P value only addresses whether the difference could be zero; effect sizes give the magnitude and the 95% CI its precision. Journals and CONSORT require both.")),
        (T("为什么要做多重比较校正？主要结局为什么用 Holm、次要结局用 BH？", "Why adjust for multiplicity, and why Holm for primary but BH for secondary outcomes?"),
         T("检验越多，至少一个“假阳性”的概率越高。主要结局是事先确定的确证性结论，用控制族错误率的 Holm 法（比 Bonferroni 更有检验效能）；"
           "次要结局属探索性，用控制错误发现率的 Benjamini–Hochberg（q 值），在每个结局类别内校正。表注中写明了校正规则。",
           "More tests inflate the false-positive rate. The pre-specified primary outcome uses Holm (family-wise error), exploratory secondary outcomes use Benjamini–Hochberg (false discovery rate) within category.")),
        (T("“差异无统计学意义”能说明两者相等吗？", "Does “not significant” mean “no difference”?"),
         T("不能。它只说明本研究的数据不足以排除零差异；若置信区间较宽，真实差异可能仍有实际意义。要证明“等效”需要事先设定等效界值做等效性检验。文中因此只写“差异未达统计学意义”。",
           "No. It means the data cannot exclude zero; a wide CI may still include meaningful effects. Equivalence needs a pre-specified margin and an equivalence test.")),
    ]


def _parallel(T, r) -> QA:
    out = [(T("为什么用协方差分析（ANCOVA）而不是比较两组的后测或变化量？", "Why ANCOVA instead of comparing post-test values or change scores?"),
            T("以基线值为协变量的 ANCOVA 校正了随机化后残留的基线差异和均值回归，在随机对照设计中比后测 t 检验和变化量 t 检验都有更高的检验效能和更小的偏倚（Vickers & Altman, 2001）。"
              "变化量和 Hedges g 仍在表中列出，便于和以往研究比较。",
              "Baseline-adjusted ANCOVA corrects residual baseline imbalance and regression to the mean and is more powerful than post-only or change-score t tests in randomised trials (Vickers & Altman, 2001)."))]
    imb = [b["name"] for b in r.get("baseline", []) if any(np.isfinite(v) and abs(v) >= 0.5 for v in b.get("smd", {}).values())]
    out.append((T("基线均衡性为什么看 SMD，而不是 P 值？", "Why judge baseline balance by SMD rather than P values?"),
                T("随机化后的组间差异按定义是偶然产生的，检验其“显著性”没有意义，而且 P 值依赖样本量。标准化均数差 |SMD| ≥ 0.5 被用作提示不均衡的界值。"
                  + (f"本研究中 {'、'.join(imb)} 的 |SMD| ≥ 0.5，主分析已校正基线值。" if imb else "本研究各基线变量 |SMD| 均 < 0.5。"),
                  "Baseline differences after randomisation are chance by definition; their P values are not meaningful and depend on n. |SMD| ≥ 0.5 flags imbalance.")))
    return out


def _crossover(T, r) -> QA:
    return [(T("交叉设计为什么用线性混合模型？", "Why a linear mixed model for the crossover?"),
             T("同一受试者在各条件下重复测量，观测值不独立。随机截距模型把个体间差异作为随机效应，固定效应估计条件差异，并可同时校正阶段（period）效应；"
               "比重复测量方差分析更能处理个别缺失值。估计边际均值（EMM）及其 95% CI 即图中菱形所示。",
               "Repeated measures within a participant are not independent; a random-intercept model handles that, adjusts for period and tolerates missing cells.")),
            (T("如何回应“延滞效应（carryover）”的质疑？", "How do you answer concerns about carryover?"),
             T("延滞效应主要靠设计控制（足够的洗脱期、平衡的条件顺序），统计上难以可靠检验。答辩时说明洗脱期长度及其依据，并指出模型已校正阶段效应。",
               "Carryover is controlled by design (washout, balanced sequences); statistical tests for it are weak. State the washout and that period is adjusted for.")),
            (T("d_z 是什么？", "What is d_z?"), T("配对差值的均值除以其标准差，是重复测量设计的标准化效应量；它与独立样本的 d 不可直接比较。", "Mean paired difference divided by its SD; not directly comparable with between-group d."))]


def _multitime(T, r) -> QA:
    return [(T("多时点数据为什么用混合模型，补充表里又为什么有重复测量方差分析？", "Why a mixed model for several time points, plus a repeated-measures ANOVA table?"),
             T("线性混合模型可使用所有可得观测值（缺失随机假设下无偏），并能约束基线组间相等（随机化设计）；重复测量方差分析只能纳入数据完整者。"
               "补充表按 SPSS 口径给出组别 × 时间方差分析，方便导师对照，结论以混合模型为准。",
               "The LMM uses all available observations and can constrain baseline equality; RM-ANOVA uses complete cases only. The supplementary ANOVA is for comparison with SPSS output.")),
            (T("什么是球形假设？Greenhouse–Geisser 校正做了什么？", "What is sphericity and what does the Greenhouse–Geisser correction do?"),
             T("球形假设要求各时间点两两差值的方差相等。不满足时（Mauchly 检验 P < 0.05）F 检验偏宽松，GG 校正按 ε 缩小自由度，使 P 值更保守。表中带 † 的行已校正。",
               "Sphericity: equal variances of all pairwise differences. When violated, GG shrinks the degrees of freedom by ε."))]


def _single(T, r) -> QA:
    out = [(T("单组前后测能证明干预有效吗？", "Can a single-group pre/post design show that the intervention works?"),
            T("不能单独证明。没有对照组，变化可能来自时间、学习/练习效应、季节、测试熟悉度或均值回归。结果中只能写“训练后……升高”，讨论中必须说明这一局限，并尽可能引用有对照的研究。",
              "Not on its own: without a control arm, change may reflect time, practice, season or regression to the mean."))]
    k = len(r.get("times", []))
    if k == 2:
        shp = [o["name"] for o in r["outcomes"] if np.isfinite(o["change"].get("shapiro_p", np.nan)) and o["change"]["shapiro_p"] < 0.05]
        out.append((T("为什么用配对 t 检验？为什么还报告 Wilcoxon？", "Why a paired t test, and why also Wilcoxon?"),
                    T("同一受试者前后测量，差值才是分析对象。配对 t 检验要求差值近似正态；Wilcoxon 符号秩检验不依赖正态，作为敏感性分析。"
                      + (f"本研究中 {'、'.join(shp)} 的差值 Shapiro–Wilk P < 0.05，应以 Wilcoxon 结果为主要参考。" if shp else "本研究差值的 Shapiro–Wilk 检验均未拒绝正态性。"),
                      "Paired differences are analysed; the t test assumes approximately normal differences, Wilcoxon does not and serves as a sensitivity analysis.")))
    else:
        gg = [o["name"] for o in r["outcomes"] if o["test"].get("gg_applied")]
        out.append((T("为什么用重复测量方差分析，两两比较为什么用 Bonferroni？", "Why repeated-measures ANOVA, and why Bonferroni for pairwise tests?"),
                    T(f"{k} 个时间点的同一受试者数据，先用总体 F 检验判断时间效应，再做两两比较。Bonferroni 与 SPSS 默认一致、最易解释；它较保守，"
                      "因此当总体效应显著而两两比较不显著时，应如实报告。"
                      + (f"{'、'.join(gg)} 不满足球形假设，已用 Greenhouse–Geisser 校正。" if gg else "各结局均满足球形假设（Mauchly P ≥ 0.05）。"),
                      "Overall F test for time, then pairwise comparisons with Bonferroni (SPSS default, conservative).")))
    return out


def _survey(T, r) -> QA:
    out: QA = []
    al = "；".join(f"{s['name']} α = {s['alpha']:.3f}" for s in r.get("scales", []))
    out.append((T("Cronbach α 多少算合格？", "What Cronbach's α is acceptable?"),
                T(f"一般 ≥ 0.70 可接受，≥ 0.80 良好；α 随题目数增加而升高，题目很少的分量表 α 偏低属常见。本研究：{al}。“删除该题后 α”明显升高的题目要检查是否反向计分或表述有问题。",
                  f"≥ 0.70 acceptable, ≥ 0.80 good; α grows with the number of items. Here: {al}.")))
    if r.get("efa"):
        e = r["efa"]
        out.append((T("做了探索性因子分析，为什么还会被问验证性因子分析（CFA）？", "Why might examiners ask for CFA after EFA?"),
                    T(f"EFA（本研究 KMO = {e['kmo']:.3f}，提取 {e['n_factors']} 个因子，累计解释 {e['cum_pct'][-1]:.1f}%）用于探索结构；使用成熟量表时，审稿人更期待用 CFA 检验既定结构（χ²/df、CFI、TLI、RMSEA、SRMR），"
                      "且 EFA 与 CFA 应在不同样本中进行。CFA 需在 AMOS、Mplus 或 R 的 lavaan 中完成，本工具未自动执行。",
                      "EFA explores structure; established scales are usually tested with CFA (χ²/df, CFI, TLI, RMSEA, SRMR) in a separate sample, using AMOS/Mplus/lavaan.")))
    if r.get("harman"):
        out.append((T("Harman 单因素检验通过，就能说明没有共同方法偏差吗？", "Does passing Harman's test rule out common-method bias?"),
                    T(f"不能。它是最宽松的检验（本研究第一因子解释 {r['harman']['first_pct']:.1f}%），只能排除“严重”偏差。更有说服力的是程序控制（匿名作答、反向题、分时段测量），"
                      "必要时可补充控制潜在方法因子的 CFA。",
                      "No; it is a weak test that only rules out severe bias. Procedural remedies and latent method-factor CFA are stronger.")))
    if r.get("mediation"):
        out.append((T("中介效应为什么用 Bootstrap，而不用逐步法（Baron & Kenny）或 Sobel 检验？", "Why bootstrap the indirect effect instead of Baron & Kenny or Sobel?"),
                    T("间接效应 a × b 的抽样分布通常不对称，Sobel 检验假定正态、检验效能低；逐步法要求总效应显著，会漏掉真实的间接效应。百分位 Bootstrap 置信区间不含 0 即判定中介显著，是目前推荐做法（Hayes, 2022）。"
                      "注意：横断面数据无法确定 X → M → Y 的因果方向，答辩中要主动说明。",
                      "The sampling distribution of a·b is skewed; Sobel assumes normality and the causal-steps approach misses indirect effects. Percentile bootstrap CIs are recommended (Hayes, 2022). Cross-sectional data cannot establish causal order.")))
    if r.get("moderation"):
        out.append((T("调节效应为什么要中心化？简单斜率怎么解读？", "Why mean-centre for moderation, and how to read simple slopes?"),
                    T("中心化使主效应的系数可解释为“调节变量取均值时”的效应，并降低与交互项的共线性（不改变交互项的检验）。简单斜率给出调节变量低（−1 SD）、中、高（+1 SD）时 X 对 Y 的效应；只有交互项显著时才解读调节作用。",
                      "Centring makes main effects interpretable at the moderator mean and reduces collinearity; simple slopes are interpreted only if the interaction is significant.")))
    if r.get("group_compare"):
        out.append((T("人口学差异比较为什么用 Welch t 检验，q 值是什么？", "Why Welch t tests, and what is q?"),
                    T("Welch t 检验不要求两组方差相等，比 Student t 更稳健。人口学比较属探索性、数量多，用 BH 校正得到 q 值（错误发现率），q < 0.05 才写“有差异”。",
                      "Welch's test does not assume equal variances; many exploratory comparisons are BH-adjusted (q).")))
    return out


def _meta(T, r) -> QA:
    return [(T("为什么用随机效应模型和 Hartung–Knapp 校正？", "Why a random-effects model with the Hartung–Knapp adjustment?"),
             T("纳入研究的人群、方案不同，真实效应很可能不同，随机效应模型估计其平均效应；研究数较少时 DerSimonian–Laird 的置信区间偏窄，Hartung–Knapp 校正更稳健。",
               "Studies differ, so true effects vary; HK adjustment gives better coverage with few studies.")),
            (T("I² 和预测区间怎么解释？", "How to interpret I² and the prediction interval?"),
             T("I² 是异质性占总变异的比例；预测区间给出“下一项研究”的真实效应可能落在的范围，比 I² 更有临床意义。Egger 检验只在研究数 ≥ 10 时做。",
               "I² is the share of variability due to heterogeneity; the prediction interval shows where a new study's true effect may lie. Egger's test only with ≥ 10 studies."))]


def build_explain(res: Dict[str, Any], lang: str = "zh") -> str:
    T = (lambda zh, en: zh) if lang == "zh" else (lambda zh, en: en)
    d = res.get("design")
    spec = {"parallel_prepost": _parallel, "crossover": _crossover, "multitime": _multitime, "single_group": _single, "survey": _survey, "meta": _meta}.get(d, lambda *a: [])
    qa = spec(T, res) + _common(T)
    L = [T("# 方法讲解与答辩问答", "# Methods explained and defence Q&A"), "",
         T("> 本文件用于学习和答辩准备：逐条读懂每个分析选择的理由，并能用自己的话复述。论文正文请由作者本人撰写。",
           "> For learning and defence preparation: understand each analytic choice and be able to explain it in your own words. The thesis text must be written by its author."), ""]
    for i, (qq, aa) in enumerate(qa, 1):
        L += [f"**{T('问', 'Q')} {i}. {qq}**", "", aa, ""]
    L += [T("## 答辩前自查", "## Before the defence"), "",
          T("- 能说出主要结局是什么、何时确定的（必须在看数据前确定）", "- State the primary outcome and when it was fixed (before seeing data)"),
          T("- 能解释主要结果的效应量和置信区间的实际含义", "- Explain the effect size and CI of the main result in practical terms"),
          T("- 能说明缺失数据和异常值是如何处理的", "- Explain how missing data and outliers were handled"),
          T("- 能说出本研究设计最主要的局限，以及它如何影响结论", "- Name the main design limitation and how it affects the conclusions"), ""]
    return "\n".join(L)
