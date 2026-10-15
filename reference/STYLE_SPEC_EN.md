# English set (`apply_style("en")`)

For English theses, protocols and journal manuscripts (MSSE, BJSM, JSAMS, Diabetes Care …). Layout, colours, geometry and statistics are **identical** to the Chinese set (`STYLE_SPEC_ZH.md`); only language and a few typographic conventions differ. **Every string in figures, tables, captions and notes must be English — `save_figure` raises an error if a CJK character appears in an English figure.**

## 1. Typography
| Object | Rule |
|---|---|
| Figure text | **Arial** (fallback Helvetica / Liberation Sans / DejaVu Sans). `apply_style("en")` configures it; do not override rcParams |
| Sizes | 7 pt body, 6.5 pt ticks, 5.5–6 pt annotations, 9 pt bold lowercase panel letters |
| Word body | Times New Roman 10.5 pt, line spacing 1.35, no first-line indent |
| Word headings | Times New Roman bold: 14 / 12 / 11 pt |
| Figure caption | Below the figure, 8.5 pt: `Figure 1. Title. a, …; b, ….` — the label "Figure 1." is bold |
| Table caption | Above the table, 9.5 pt: `Table 1. Title` — label bold |
| Table note | Below the table, 8 pt grey: model/test, adjustment, multiplicity, abbreviations, transformations (†) |
| Table font | 7–8 pt |
| Punctuation | en dash for ranges (`0–6 h`, `95% CI −6.3 to −3.0`), true minus `−` in figures, thin consistency in text; Oxford comma optional but consistent |
| Spelling | pick British *or* American once (`standardised`/`standardized`) |

## 2. Vocabulary used inside figures (English set)
| Concept | English |
|---|---|
| Baseline / follow-up | Baseline / Week 12 |
| Arms | Control / Intervention (say "waitlist control" in the caption if applicable) |
| Descriptive | Mean ± SD ; Mean ± SEM |
| Time axis | Time after start (h) — state what t = 0 is |
| Change | Change from baseline (unit) |
| Paired difference | Paired difference vs CON (mmol/L) |
| Forest arrows | ← Favours control / Favours intervention → |
| Individual data | "thin lines are individual participants" (caption) |
| Simulated data | `Simulated data` (auto footer, 5 pt grey italic) |

Axis label = **quantity (unit)**: `Glucose (mmol/L)`, `Skeletal muscle mass (kg)`, `14-d TIR (%)`, `0–6 h net iAUC (mmol·h/L)`. Sentence case, no trailing period.

## 3. Numbers and statistics
- Descriptive: `mean ± SD` (2 dp if |x| < 10, 1 dp if < 100, else integer); categorical `n (%)`.
- Estimates: `estimate (95% CI lower, upper)`; in text `−4.3 mmol·h/L (95% CI −6.3 to −2.3; P < 0.001)`.
- P: `P < 0.001` or `P = 0.012`; italic *P* in the final manuscript is applied by the journal template — keep plain text in generated files. Never `P = 0.000` or `P = <0.001`. In tables: `<0.001` / `0.012`.
- Effect sizes: Hedges *g* (between groups), paired *d*z (crossover); say which variable they refer to.
- Multiplicity: Holm for pre-specified contrasts (`Holm P`), Benjamini–Hochberg within outcome category for secondary outcomes (`BH q`), primary outcome unadjusted.
- State coverage thresholds (e.g. CGM ≥ 70% valid data), dropouts, sensitivity analyses.

## 4. Caption template
```
Figure N. {One-sentence title}. a, {content} ({what the band means}); b, {content}; c, {content}.
{Model, adjustment, multiplicity, n, abbreviations.}
```
Example:
```
Figure 3. Primary outcome, 0–6 h net iAUC. a, individual observations (light dots; grey lines join participants with all four conditions)
and linear-mixed-model estimated marginal means with 95% CI; b, differences between conditions with 95% CI (Holm-adjusted P for RT − CON;
dotted line, pre-specified 10% clinical threshold); c, dose–response against CON with linear trend.
```

## 5. Table template
```
Table N. {Title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  thick rule
 Outcome | Intervention baseline | Intervention week 12 | … | Between-group difference (95% CI) | P | BH q
────────────────────────────────────────  thin rule under header
 …(no vertical rules, no shading)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  thick rule
{Note: Mean ± SD. Between-group difference is the time × group interaction …; BH q adjusted within category; † log-transformed.}
```
- Table 1 reports SMD and the test P value; variables with |SMD| ≥ 0.5 are named in the text and a baseline-adjusted sensitivity analysis is reported.

## 5b. Results sentence templates (English)
| Situation | Template |
|---|---|
| Primary between-group difference | `The intervention group improved {b:.1f} percentage points more than control (95% CI {lo:.1f} to {hi:.1f}; {P}; Hedges g = {g:.2f}); the difference {was / was not} statistically significant.` |
| Crossover main effect | `Across the three band conditions the mean 0–6 h net iAUC was {x:.1f} mmol·h/L lower than CON (95% CI {lo:.1f} to {hi:.1f}; {P}; d_z = {dz:.2f}).` |
| After multiplicity | `After Holm adjustment, RT20 ({b:.1f}; Holm {P}), RT30 (…) and RT45 (…) were each lower than CON.` — use "each" only if all adjusted P < 0.05; otherwise state them separately |
| No detected difference | `RT20 and RT45 differed by {d:+.1f} (95% CI {lo:.1f} to {hi:.1f}; {P}); no difference was detected.` — do **not** claim "equivalent" without an equivalence test |
| Exploratory | `These secondary outcomes were not adjusted for multiplicity and are exploratory.` |
| Baseline imbalance | `Using |SMD| ≥ 0.5, imbalances were present for …; a baseline-adjusted sensitivity analysis is reported.` |
| Safety | `{n} adverse events were recorded across both studies, {s} serious; the most frequent were ….` |

## 6. Do not
- overall figure titles, 3-D, rainbow maps, pie charts, framed legends, default grey grids, neon green / pure red / pure blue;
- Chinese (or any non-English) characters anywhere in an English deliverable, including the footer, table cells and docx;
- English figures made by hand-translating Chinese PNGs — regenerate with `apply_style("en")`.

## 7. Conventions by data type (apply to every data type; see `reference/DATA_TYPE_GUIDE.md`)
- **Waveforms / curves** (EMG, joint angle, GRF, pacing): normalised x-axis (% cycle, % stance); mean ± SEM (or ± SD, say which); compare two waveforms with SPM{t} using a permutation threshold, never uncorrected pointwise P values.
- **One value per participant**: paired designs use raw points + joining lines + estimate ± 95% CI; 3 or more groups, or unpaired data, use a raincloud (density, raw points, IQR, mean ± CI) with the density drawn over the observed range only.
- **Questionnaires / ordinal data**: single items as diverging stacked bars (Likert); totals as raincloud or multi-time mean ± 95% CI; correlation matrices as lower triangles with bold = P < 0.05; profiles as radar plots; mediation as a path diagram with a bootstrap interval for the indirect effect.
- **Survival**: Kaplan-Meier with 95% CI bands and censor ticks, a "number at risk" table underneath, hazard-ratio forest on a log axis.
- **Diagnostic / prediction**: ROC (AUC with bootstrap 95% CI, Youden point) and calibration; place the legend below the axes so it never covers a curve.
- **Agreement / reliability**: line of identity with ICC(2,1); Bland-Altman (bias and 95% limits of agreement with CIs); ICC forest annotated with CV%.
- **Meta-analysis**: forest (square area proportional to weight, diamond = pooled), funnel, bubble meta-regression.
- **Omics**: volcano (up primary, down slate), clustered heat map with a group colour strip, PCA scores with 95% ellipses.
- **Log axes**: plain-number ticks (0.5, 1, 2, 4), never 10^n; switch minor tick labels off.
- **Colour**: Likert and correlation matrices use the contrast / slate / primary diverging scale (`DIVERGING`); sequential heat maps use `SEQ` (paper → navy); 5 or more unordered categories use `category_colors(n)`.
