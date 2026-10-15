# Method: every rule and threshold

Nothing in `sportsci-topic` is a model or a learned score. Each output is either a count over the student's records, a closed-form or
numerically exact power calculation, or a rule written below. The thresholds are conventions, not laws; they are constants at the top of
`evidence.py` / `feasibility.py` so a supervisor can change them and see the effect on the card.

## 1. Evidence map (`evidence.py`)

**Matching.** Each facet (population P, intervention I, comparator C, outcome O) is a list of terms. A record (title + abstract + keywords,
lower-cased) matches a facet if any term occurs.

- Latin terms are word-bounded, tolerate a plural `s`/`es`, and treat space and hyphen alike (`high-intensity` = `high intensity`).
  So `rt` does not match `start`.
- Chinese terms are plain substrings.

**Counts.** For every combination of the core facets (P, I, O) the number of records matching all of them, over all years and over the
last five (`recent_years`, window ends at `this_year`). *Direct overlap* = P+I+O.

**Overlap tier** (direct overlap in the last 5 years):

| Count | Tier | Colour on the card |
|---|---|---|
| 0 | none | green |
| 1–3 | few | green — state the difference |
| 4–9 | crowded | yellow |
| ≥ 10 | very crowded | red |

**Coverage.** Fewer than 30 records = `low`: the map is a sketch and the evidence check can never be green on it.

**Record-set statements** (only when there is no direct overlap and a pair has ≥ 3 records):

- P+I ≥ 3 and no record has O → "the population/intervention has been studied, none measured this outcome"
- I+O ≥ 3 and none in P → "this intervention/outcome exists, not in this population"
- P+O ≥ 3 and none with I → "this population/outcome exists, not with this intervention"

With direct overlap, the statement is the count itself plus, for effect questions, whether any of those records looks randomised or
quasi-experimental by its title/abstract. All of these are statements about the *record set*, never about the literature.

**Design detection** (title/abstract keywords, first match wins): meta-analysis, review, randomised, crossover, quasi-experimental,
cohort/longitudinal, cross-sectional, survey/questionnaire, pilot, experiment/intervention/trial, other. It is a hint for reading order, not a classification of record quality.

## 2. Design rule table (`designmap.py`)

| Question type | Condition | Design |
|---|---|---|
| synthesis | – | `meta` |
| association | – | `survey` |
| acute | – | `crossover` |
| course | – | `multitime` (warns when fewer than 3 assessments) |
| effect | no control group | `single_group` (warns: change cannot be attributed to the intervention) |
| effect | control, ≥ 3 assessments | `multitime` |
| effect | control, 2 assessments | `parallel_prepost` |

Each rule carries what the design permits, what it forbids, the planned analysis, a simpler fallback, and the statistical comfort it needs
(`basic` < `intermediate` < `advanced`).

## 3. Sample size (`power.py`)

- t tests: exact noncentral-t power. `n_two_sample(d)` is per group; ANCOVA with one baseline covariate uses `d_adj = Δ / (SD·√(1−r²))` and one fewer degree of freedom.
- Paired / crossover / single group: paired t on `dz`. If only `d` is given for a within-subject design it is treated as `dz` (stated on the card).
- Correlation: Fisher z (within ±1 of the exact value). One-way ANOVA: noncentral F, total N rounded up to a multiple of k. Regression: fixed-model noncentral F, λ = f²·N.
- `mdes_*`: the smallest effect with 80 % power at the given n (root of the power function).
- Dropout: `n_enrol = ceil(n / (1 − dropout))`.
- Multiple planned contrasts: Bonferroni on α (`effect.contrasts`).
- Multi-time-point models: no closed form; ANCOVA at the final time point is used and labelled.
- Survey: rules of thumb printed as rules — EFA 5–10 respondents per item and ≥ 200; regression N ≥ 50 + 8·predictors (Green 1991); bootstrap mediation ≥ 200 and no formula.
  If `effect.r` or `effect.f2` is supplied the exact figure is also computed and the larger of the two is used.
- Meta-analysis: k ≥ 2 can be pooled, funnel plot and meta-regression need ≥ 10 studies (Cochrane Handbook). The "sample size" is the number of eligible studies.
- **Sensitivity table**: n for d (or dz, r) = 0.3 / 0.5 / 0.8 and the power at the accessible n. Labelled as conventional magnitudes, never as the student's effect size.

Values are checked in `tests/test_topic.py` against widely published G*Power results (d = 0.5 → 64 per group; dz = 0.5 → 34; f = 0.25, k = 3 → 159; f² = 0.15, 3 predictors → 77).

## 4. Feasibility rubric (`feasibility.py`)

| Check | Green | Yellow | Red |
|---|---|---|---|
| Sample | power at accessible n ≥ 0.80 and effect source stated | 0.60–0.80, or no effect source, or no effect size | < 0.60 |
| Time | slack ≥ 20 % of weeks needed | slack < 20 % (or no deadline given) | weeks needed > weeks available |
| Measures | every outcome with `needs` has the instrument | a secondary outcome lacks it | the primary outcome lacks it |
| Ethics | approved / not needed | pending / not started / minors or patients | not started *and* time check red |
| Analysis | planned analysis within stated comfort | one level above | two levels above (use the fallback) |
| Design | no warning | a design rule warned (e.g. no control group) | – |
| Overlap | tier none / few and coverage ok | crowded, or fewer than 30 records, or no records | very crowded |

**Weeks needed** = ethics (approved 0, pending 4, not started 8, overridable by `ethics_weeks`) + recruitment + intervention + testing + analysis and writing.

**Overall colour** = the worst row. There is deliberately no weighted score: a red is a red and the student sees which constraint it is.

## 5. Variants (`variants.py`)

One axis of the brief is replaced by a listed alternative, the direct overlap is recounted, and the difference to the base question is shown.
With `--two-axis`, alternatives from two different axes are combined (capped at 40 rows).
A variant is **not assessable** if its own terms match no record at all: a zero then reflects the record set, not the field.
Ranking: assessable variants with the fewest recent direct overlaps first, then all-years overlap, then the unassessable ones.
A variant changes who can be recruited, what is measured and the ethics route; the table says nothing about those.

## 6. What the tool cannot do

- It cannot tell that a topic is *important* or *interesting*. It tells whether it is crowded, possible and affordable.
- It does not read papers. A record that mentions all three facets in the abstract may still study something else.
- It cannot search CNKI automatically. Records from CNKI / Wanfang are exported by the student.
- It cannot replace the supervisor's or the ethics committee's judgement.
