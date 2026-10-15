# Brief fields (`brief.toml`)

Generate a commented file with `sportsci-topic new`; check it with `sportsci-topic check`.

## `[topic]`

| Field | Values | Meaning |
|---|---|---|
| `working_title` | text | shown on the card; the student's own words |
| `language` | `zh` \| `en` | language of the card (`--lang` overrides) |
| `goal` | `thesis` \| `journal` \| `grant` \| `course` | context only |
| `question_type` | `effect` \| `acute` \| `course` \| `association` \| `synthesis` | programme effect · acute response · time course · questionnaire association · evidence synthesis |

## `[pico.population]`, `[pico.intervention]`, `[pico.comparator]`, `[pico.outcome]`

| Field | Meaning |
|---|---|
| `label` | short name shown on the card |
| `terms` | search vocabulary, **Chinese and English**; population, intervention and outcome need at least one term. Synonyms and abbreviations help; too few terms make a falsely empty map |

For association questions, `intervention` holds the exposure / predictor.

## `[[outcomes]]` (not needed for `association`; scales are used instead)

| Field | Meaning |
|---|---|
| `name` | column name in the future data file |
| `label`, `label_en`, `unit` | labels used in the design draft |
| `primary` | exactly one outcome must be `true` |
| `direction` | `higher_better` \| `lower_better` \| `neutral` |
| `decimals`, `category` | passed on to `design.json` |
| `needs` | instrument or test the measurement depends on; matched against `constraints.equipment` |

## `[[scales]]` (association questions)

`name`, `label`, `label_en`, `n_items`, `role` ∈ `x` predictor · `y` outcome · `m` mediator · `w` moderator · `covariate`.

## `[design]`

| Field | Meaning |
|---|---|
| `has_control` | a control or comparison group exists |
| `timepoints` | number of assessments (2 = baseline + post) |
| `groups`, `groups_en` | group names; the first is the control |
| `time_labels`, `time_labels_en` | assessment names |
| `conditions`, `conditions_en` | crossover conditions; the first is the control |

## `[constraints]`

| Field | Meaning |
|---|---|
| `accessible_n` | people you can really enrol (before dropout) |
| `dropout` | expected loss, 0–0.9 |
| `weeks_available` | weeks until the deadline |
| `intervention_weeks`, `recruit_weeks`, `test_weeks`, `writing_weeks` | the time budget |
| `ethics` | `approved` \| `pending` \| `not_started` \| `not_needed`; `ethics_weeks` overrides the default lead time |
| `vulnerable_population` | minors, patients … |
| `equipment` | instruments you can use (list) |
| `stats_comfort` | `basic` \| `intermediate` \| `advanced` |
| `supervisor_direction` | free text, printed on the card |

## `[effect]`

| Field | Meaning |
|---|---|
| `source` | where the effect size comes from (paper DOI + table, pilot, smallest effect of interest). **Empty = illustrative only** |
| `d` / `dz` | standardised difference (between groups / within participants) |
| `delta`, `sd`, `r_prepost` | raw difference, outcome SD and pre–post correlation for ANCOVA |
| `r`, `f`, `f2`, `predictors`, `groups` | for correlation, ANOVA, regression |
| `alpha`, `power`, `contrasts` | default 0.05, 0.80, 1 |

## `[[variants.<axis>]]`

`axis` ∈ `population` \| `intervention` \| `comparator` \| `outcome`. Each item: `label`, `terms`, optional `note`.
