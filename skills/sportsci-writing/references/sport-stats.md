# Sport science statistics: tests and how to report them

The most common designs and analyses in sport science, with the exact reporting formats expected by reviewers. The `scripts/stats.py` helper produces output in these formats automatically.

## Decision tree (which test to use)

```
Comparing two means
├─ Same participants measured twice (pre/post, condition A vs B in same person)
│   ├─ Normally distributed differences → paired t-test
│   └─ Not normal / ordinal → Wilcoxon signed-rank
└─ Different participants in each group
    ├─ Normally distributed, equal variance → independent t-test
    ├─ Normally distributed, unequal variance → Welch's t-test
    └─ Not normal / ordinal → Mann–Whitney U

Comparing 3+ means
├─ One factor, between-subjects → one-way ANOVA + Tukey/Bonferroni
├─ One factor, within-subjects (repeated measures) → RM-ANOVA + Bonferroni
├─ Two factors, mixed (one between, one within) → mixed ANOVA
└─ Non-parametric alternative → Kruskal-Wallis (between) / Friedman (within)

Relationship between two continuous variables
├─ Both normal, linear → Pearson's r
└─ Non-normal, ordinal, or non-linear monotonic → Spearman's ρ

Relationship with confounders / multiple predictors
└─ Multiple regression / mixed-effects model

Reliability
├─ Continuous, two raters or test-retest → ICC (specify form: 2,1 / 3,1 / etc.)
├─ Internal consistency of a scale → Cronbach's α
└─ Categorical agreement → Cohen's κ
```

## Effect sizes (always report)

Sport science journals now expect effect sizes alongside P-values. Without them, reviewers will request a revision.

| Test | Effect size | Interpretation |
|---|---|---|
| Independent / paired t-test | Cohen's *d* (or Hedges' *g* when n is small) | 0.2 small, 0.5 medium, 0.8 large |
| One-way / RM ANOVA | partial η² ($\eta_p^2$) | 0.01 small, 0.06 medium, 0.14 large |
| Pearson r | r itself | 0.1 small, 0.3 medium, 0.5 large |
| Chi-square | Cramér's V or φ | depends on df |
| Logistic regression | OR with 95% CI | depends on context |

For sport-specific outcomes, also consider reporting **smallest worthwhile change (SWC)** when known for the variable (e.g., 1% for endurance time-trial performance in trained athletes).

## Reporting formats

Use these templates verbatim (substitute the numbers). The phrasing is what reviewers expect. Deviations look careless.

### Descriptives

> Participants (n = 20, 12 men and 8 women) were 24.3 ± 3.1 years old, 175.2 ± 7.8 cm tall, and weighed 71.4 ± 9.2 kg.

For non-normal data:
> Median training experience was 4.5 years (IQR 3.0–7.5).

### Independent t-test

> VO2max was higher in the trained group (52.1 ± 4.3 mL·kg⁻¹·min⁻¹) than in the untrained group (41.7 ± 5.2 mL·kg⁻¹·min⁻¹), *t*(38) = 6.91, *P* < 0.001, *d* = 2.18 (95% CI 1.43 to 2.91).

### Paired t-test

> Vertical jump height increased from baseline (42.3 ± 5.1 cm) to post-training (45.8 ± 4.7 cm), *t*(19) = 4.52, *P* < 0.001, *d* = 0.71 (95% CI 0.34 to 1.07).

### One-way ANOVA + post-hoc

> A one-way ANOVA revealed a significant effect of training group on VO2max, *F*(2, 42) = 8.43, *P* < 0.001, $\eta_p^2$ = 0.29. Bonferroni-corrected post-hoc comparisons showed that the HIIT group had higher VO2max than the MICT group (*P* = 0.012, *d* = 0.92) and the control group (*P* < 0.001, *d* = 1.34). MICT and control did not differ (*P* = 0.187).

### Repeated-measures ANOVA

> A repeated-measures ANOVA showed a significant main effect of time on countermovement jump height, *F*(3, 57) = 12.6, *P* < 0.001, $\eta_p^2$ = 0.40. Mauchly's test indicated that sphericity was violated ($\chi^2$(5) = 14.2, *P* = 0.014), so degrees of freedom were corrected using the Greenhouse-Geisser estimate (ε = 0.78).

### Mixed (two-way) ANOVA

> A 2 (group) × 4 (time) mixed ANOVA revealed a significant group × time interaction for VO2max, *F*(3, 84) = 5.21, *P* = 0.002, $\eta_p^2$ = 0.16. Simple effects analysis showed that VO2max increased over time in the HIIT group (*P* < 0.001) but not in the control group (*P* = 0.218).

### Pearson correlation

> Training volume was positively associated with VO2max improvement (*r* = 0.62, *P* = 0.001, 95% CI 0.31 to 0.81).

### Reliability: ICC

> Test-retest reliability for peak power was excellent, ICC(3,1) = 0.94 (95% CI 0.86 to 0.98), with a typical error of 12 W (CV = 2.8%).

### Cronbach's α

> Internal consistency for the Athlete Burnout Questionnaire was acceptable, α = 0.84 (95% CI 0.79 to 0.88).

## Sample size justification (Methods section)

Reviewers now routinely require this. Two acceptable forms:

**A priori power analysis (preferred):**
> An a priori power analysis (G\*Power 3.1.9) for a 2 × 2 mixed ANOVA, assuming a medium interaction effect ($\eta_p^2$ = 0.06), α = 0.05, and power = 0.80, indicated a required total sample of 34. We recruited 40 to allow for ~15% dropout.

**Justification from prior literature:**
> Sample size was based on Smith et al. (2019), who reported a between-group difference of 8% in VO2max with SD of 5% (*d* ≈ 1.6). To detect this effect with α = 0.05 and power = 0.80, 8 participants per group would be needed. We recruited 12 per group as a conservative estimate.

## Multiplicity and correction

State the correction explicitly:
- Bonferroni: most common, conservative
- Holm-Bonferroni: slightly more powerful
- FDR (Benjamini-Hochberg): preferred when many comparisons (e.g., -omics)
- Tukey HSD: for all-pairs after ANOVA
- Dunnett: when comparing several groups to a single control

> Post-hoc comparisons were Bonferroni-corrected for the 3 pairwise contrasts (adjusted α = 0.017).

## Assumption checks (state them)

> Normality was assessed by the Shapiro-Wilk test and visual inspection of Q-Q plots. Homogeneity of variance was assessed by Levene's test. When assumptions were violated, [specify alternative].

For ANOVA: Mauchly's test for sphericity (and what correction was applied if violated).

## Common reviewer complaints: preempt them

1. **No effect sizes** → always include.
2. **No 95% CIs on the effect size** → include them.
3. **Vague "approached significance"** → never use this phrase. Report the exact P (`P = 0.067`).
4. **No correction for multiple comparisons** → state the correction or justify why none.
5. **Unequal n in groups but no Welch's correction** → use Welch's t-test by default for between-subjects comparisons (it's robust whether variances are equal or not).
6. **Inferential test reported without descriptives** → always show means ± SD (or median, IQR) before the test result.
7. **"Significant" without "statistically"** → say "statistically significant" or just give the P-value.
8. **Significant figure / decimal-place inconsistency** → P to 3 decimals (or `< 0.001`). Means and effect sizes to 2 decimals. Percentages to 1 decimal unless precision matters.
