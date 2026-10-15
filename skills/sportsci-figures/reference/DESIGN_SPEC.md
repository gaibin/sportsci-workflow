# Design spec (`design.json`) — the contract between "design" and "results"

One json file describes the study; the engine needs nothing else besides the data file.
`python cli.py new-design -t <type> -o design.json` writes a runnable template; `python cli.py check-design design.json -d data.csv` validates spec + data;
`python cli.py results design.json -d data.csv -o results_out -l both` produces everything.

```python
from sportsci_figures.results import run_results
run_results("design.json", "data.csv", "results_out", lang="both")      # lang: zh | en | both
```

## Choosing the design

| Study | `design` | Data layout (long, one row per…) | Primary model |
|---|---|---|---|
| Parallel groups, baseline + one follow-up (RCT, quasi-experiment) | `parallel_prepost` | participant × time | ANCOVA (follow-up ~ group + baseline); Hedges g on change |
| Every participant does every condition (random order) | `crossover` | participant × condition | linear mixed model, participant random intercept, period adjusted |
| Parallel groups, ≥ 3 assessments | `multitime` | participant × time | constrained longitudinal LMM (baseline common) or full group × time |
| Pooling published studies | `meta` | study | DerSimonian–Laird + Hartung–Knapp; subgroup; leave-one-out; Egger (k ≥ 10); meta-regression |
| One group, 2 or more assessments (单组前后测 / 单组重复测量) | `single_group` | participant × time | paired t (+ Wilcoxon) / one-way RM-ANOVA, Mauchly + Greenhouse–Geisser, Bonferroni pairwise |
| Questionnaire / cross-sectional survey (问卷调查) | `survey` | respondent (wide: one column per item) | α, KMO/Bartlett, EFA, Harman, correlations, group differences, regression, bootstrap mediation, moderation |

Not sure which design fits a raw data file? `python cli.py intake data.xlsx -o projects/<name>/intake` profiles it and writes `design_draft.json`.

Anything else (waveforms, ROC, survival …): use the figure blocks directly (SKILL.md §4b); this engine is for the analyses where a
pre-registered model + multiplicity rule can be fixed in advance.

## Common fields

| Field | Meaning |
|---|---|
| `design` | one of the four above (required) |
| `title` | string or `{"zh":…, "en":…}` |
| `language` | default set when `--lang` is not given |
| `simulated` | `true` → every figure carries "Simulated data" and the docx opens with the disclaimer. **Set `false` only for real data** |
| `columns` | map of roles to data column names (below) |
| `outcomes` | list; **exactly the outcomes you pre-specified**; at least one `"primary": true` |
| `category_labels` | `{category: {"zh":…, "en":…}}` for grouping rows in tables/forests |
| `simulate` | optional block with true effects → `--simulate` generates test data (used by the tests: estimates must recover the truth) |
| `report` | optional `{"profile": "thesis", "chapter": 4}` → Chinese degree-thesis layout: 小四 body, 1.5 spacing, figures/tables numbered 图 4-1 / 表 4-1, headings 4.1, 4.2 … (same as `--chapter 4`) |

Outcome fields: `name` (id), `column` (default = name), `label` (string or zh/en dict), `unit`, `category`, `primary`, `direction` (`higher_better` | `lower_better` | `neutral`; used to orient forest plots so that **positive = favourable**), `decimals`.

Labels may be a plain string (same in both sets) or `{"zh": "...", "en": "..."}`. A label missing in one language falls back to the other — check the English output contains no Chinese (the test-suite does).

## parallel_prepost / multitime
```json
"columns": {"id": "id", "group": "group", "time": "time"},
"groups": {"order": ["CON", "RT"], "control": "CON", "labels": {"CON": {"zh": "对照组", "en": "Control"}, "RT": "RT"}},
"times":  {"order": ["pre", "post"], "primary": "post", "labels": {...}},       // multitime: >= 3 entries; "primary" = time that carries the confirmatory test
"multitime": {"constrained_baseline": true},
"baseline_vars": [{"name": "age", "label": {...}, "type": "cont"}, {"name": "sex", "type": "cat", "levels": ["F", "M"]}]
```
Data: one row per participant per time; outcomes are columns; baseline variables repeated (first row per id is used).

## crossover
```json
"columns": {"id": "id", "condition": "condition", "period": "period"},       // period optional (adjusted when present)
"conditions": {"order": ["CON","RT20","RT30","RT45"], "control": "CON",
               "dose": {"CON":0,"RT20":20,"RT30":30,"RT45":45}, "dose_unit": {"zh":"min","en":"min"},   // dose → linear trend test
               "pairs": [["RT45","RT20"]],                                                                 // pre-specified pairwise contrasts (Holm within outcome)
               "labels": {...}}
```

## meta
```json
"columns": {"study": "study", "n1": "n_int", "m1": "mean_int", "sd1": "sd_int", "n2": "n_ctl", "m2": "mean_ctl", "sd2": "sd_ctl",
            "subgroup": "duration_cat", "moderator": "weeks"},                 // subgroup / moderator optional
"meta": {"effect": "smd",            // smd = Hedges g | md = mean difference | generic = give columns.es and columns.se (or lo + hi)
         "direction": "lower_better",// flips sign so positive = favourable
         "hksj": true, "outcome_label": {...}, "subgroup_label": {...}, "moderator_label": {...}}
```
Extraction template: `config/meta_extraction_template.csv`. For change-score or adjusted effects use `effect: "generic"` with `es` and `se`.

## single_group
```json
"columns": {"id": "id", "time": "time"},
"times": {"order": ["pre", "w4", "w8"], "labels": {...}},       // >= 2 entries
"outcomes": [...]                                              // as above; one "primary": true
```
2 time points: paired t test, mean change (95% CI), d_z, Wilcoxon signed-rank as sensitivity, Shapiro–Wilk on the changes.
≥ 3 time points: one-way repeated-measures ANOVA on complete cases; Mauchly's test; Greenhouse–Geisser-corrected df and P reported whenever
sphericity is rejected (marked †); all pairwise paired t tests with Bonferroni (SPSS default); d_z for last vs first.
The Results text and every table note state that a single-group design cannot attribute change to the intervention alone.

## survey
```json
"columns": {"id": "id"},
"demographics": [{"name": "sex", "label": {...}, "type": "cat", "levels": ["男", "女"], "level_labels": {"男": {"zh": "男", "en": "Male"}}},
                 {"name": "age", "type": "cont"}],
"scales": [{"name": "ANX", "label": {"zh": "焦虑", "en": "Anxiety"}, "items": ["AX1", "AX2", "AX3"], "reverse": ["AX3"], "min": 1, "max": 5, "score": "mean"}],
"common_method_bias": true,                                     // Harman single-factor test
"efa": {"enabled": true, "n_factors": null},                    // null: number of scales (if > 1) else Kaiser
"group_compare": ["sex", "grade"],                              // must be declared in demographics; Welch t / one-way ANOVA, BH q across all
"regression": [{"y": "ANX", "x": ["PA", "SLP"], "covariates": ["sex", "age"]}],
"mediation":  [{"x": "PA", "m": "SLP", "y": "ANX", "covariates": [], "n_boot": 5000, "seed": 7}],   // Hayes model 4, percentile bootstrap
"moderation": [{"x": "PA", "w": "SE", "y": "ANX", "covariates": []}]                                 // Hayes model 1, mean-centred, simple slopes
```
Data: one row per respondent; one column per item (raw answers — reverse-keyed items are recoded by the engine, do not recode them in the file).
Scale scores are added as columns named after the scale, so scale names must not clash with existing columns. Categorical predictors/covariates
are dummy-coded automatically (first level = reference). CFA/SEM are not run (lavaan / AMOS / Mplus); the Results text says so.

## Statistical rules built in (stated in every table note)
- Primary outcome(s): Holm across the contrasts of the primary outcome(s). Secondary outcomes: Benjamini–Hochberg within `category`.
- Between-group effect sizes: Hedges g (parallel; on change scores), paired d_z (crossover). P values: `P < 0.001` / `P = 0.012`.
- Wording ("significant", "was not statistically significant") is chosen by code from the *adjusted* P; non-significance is never written as "equivalent".
- Meta-analysis: τ² DerSimonian–Laird; Hartung–Knapp CI (t, k−1); 95% prediction interval k ≥ 3; Egger only for k ≥ 10 (otherwise stated as not performed).
- Missing data: available-case in ANCOVA; likelihood-based (all available data) in the mixed models.

## Outputs
Every run also writes `<lang>/methods_explained.md`: the defence-style Q&A that explains each analytic choice with the numbers of this analysis
(for learning and defence preparation). `multitime` adds a supplementary group × time mixed ANOVA (SPSS convention).
```
results_out/analysis.json            every estimate (use it to write the Discussion; do not retype numbers)
results_out/design_used.json         the spec as executed
results_out/<zh|en>/figures/*.png|pdf   300 dpi + vector
results_out/<zh|en>/tables.xlsx
results_out/<zh|en>/results.docx     three-line tables, numbered captions
results_out/<zh|en>/results.md       same text/tables, for pasting into other tools
```
