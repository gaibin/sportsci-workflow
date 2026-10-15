---
name: sportsci-figures
description: Publication-grade figures, three-line tables and a Results document (.docx / .md) for sport, exercise, health and psychology studies, in an all-Chinese or all-English set with one navy palette. Runs the analysis from a design spec for RCT pre-post (ANCOVA), crossover and multi-timepoint (mixed models), single-group pre-post / repeated measures, questionnaire surveys (reliability, EFA, regression, bootstrap mediation, moderation) and meta-analysis, and offers figure blocks for 26 more data types (CGM, EMG, force, SPM, survival, ROC, omics, GPS). Also checks raw data files and writes a methods explanation. Use for 数据分析, 结果, 作图, 图表, 三线表, 问卷信效度, 中介/调节, 前后测, 学位论文结果章, or any results figure/table request.
---

# sportsci-figures

Figures, tables and the Results section, done the same way every time: one style, two language sets (`zh` all-Chinese, `en`
all-English), numbers that always come from code. **Follow this file; do not improvise a style.**

Three ways in — pick by what the user has:

| The user has … | Path | Section |
|---|---|---|
| a raw data file (Excel / CSV), design unclear | `python cli.py intake data.xlsx -o intake` → de-identified data, data-quality report, draft `design.json` | §2 |
| a standard design (RCT, crossover, multi-time, single group, questionnaire, meta-analysis) | write / edit `design.json`, `python cli.py results` | §2 |
| any other data shape (waveforms, survival, ROC, omics, tracking …) | compose figure blocks from `pubstyle.figures` | §3 |

---

## 0. Ten-line summary

1. Decide the language set once (`zh` or `en`). Never mix languages in one deliverable.
2. `from sportsci_figures.pubstyle import apply_style, save_figure, ResultsDoc, figures as pf`, then **`apply_style(lang)` before any figure**.
3. Standard designs: write a `design.json` and run `python cli.py results` — never hand-code those analyses.
4. Other data: compose figures from `pf` blocks (§3). No `plt.style.use`, seaborn themes, or matplotlib default colours.
5. Every panel: bold lowercase letter + short title (`panel_title(ax, "a", "Change from baseline")`); no overall figure title.
6. Show **individual data** when n < ~60 plus a **model estimate with 95% CI**; effect sizes and exact P in the figure/table, never stars.
7. Colours are roles: intervention = navy `#112378`, control = sand `#C9A66B` (dashed lines), contrast/harm = terracotta `#C4573F`; doses = `dose_colors(n)`.
8. `save_figure(fig, stem)` → 300-dpi PNG + vector PDF, stamped "Simulated data" unless `simulated=False` (real data only).
9. Tables are three-line (`ResultsDoc.table`); numbers in text come from analysis objects, wording ("differed" / "did not differ") is chosen by code from P / CI.
10. **Open every PNG you produce** and run the checklist in §7. English figures must contain zero Chinese characters (`save_figure` raises).

---

## 1. Language set

| Signal | Set |
|---|---|
| Chinese request, 中文论文 / 开题 / 学位论文 / 国内期刊 | `zh` |
| English request, SCI journal, international submission | `en` |
| both | run twice (`-l both` or `for lang in ("zh", "en")`) → `…/zh/`, `…/en/` |
| unclear | ask once; default to the language of the request |

Layout, colours, sizes and statistics are identical in both sets. Differences: labels and captions (`图 1  标题` below / `Figure 1. Title`),
fonts (Arial + CJK fallback; docx 宋体/黑体 vs Times New Roman), minus sign (`-` in zh, `−` in en), footer tag. Use `tr("中文", "English")` for every
label so one script produces both sets. Full text: `reference/STYLE_SPEC_ZH.md`, `reference/STYLE_SPEC_EN.md`.

---

## 2. Standard designs: `design.json` → Results package

```bash
python cli.py intake data.xlsx -o intake                         # optional: raw file -> data_clean.csv, intake_report.md, design_draft.json
python cli.py new-design -t survey -o design.json                # parallel_prepost | crossover | multitime | meta | single_group | survey
python cli.py check-design design.json -d data.csv               # spec valid + data run through the analysis
python cli.py results design.json -d data.csv -o results -l both # add --chapter 4 for degree-thesis numbering (图 4-1 / Figure 4.1)
python cli.py results design.json --simulate -o rehearsal        # no data yet: rehearse with the spec's "simulate" block (tagged simulated)
```

Output per language: `figures/*.png|pdf`, `tables.xlsx`, `results.docx`, `results.md`, `methods_explained.md` (each analytic choice explained
with this study's numbers), plus `analysis.json` (every estimate) and `design_used.json`. Text, tables and figures come from the same objects,
so they cannot disagree.

| Study | `design` | Engine reports |
|---|---|---|
| parallel groups, baseline + follow-up | `parallel_prepost` | ANCOVA (baseline covariate), change scores, Hedges g, estimation panel |
| every participant in every condition | `crossover` | random-intercept LMM, EMMs, contrasts (Holm), dose trend, d_z |
| parallel groups, ≥ 3 visits | `multitime` | constrained longitudinal LMM + supplementary group × time mixed ANOVA (GG-corrected) |
| one group, 2+ visits | `single_group` | paired t + Wilcoxon / RM-ANOVA (Mauchly, Greenhouse–Geisser, Bonferroni pairwise); states the no-control limitation |
| questionnaire | `survey` | α, item–total r, KMO/Bartlett, EFA (PAF + varimax), Harman, correlations, group differences (BH q), regression (B, β, VIF), bootstrap mediation, moderation |
| pooling studies | `meta` | DerSimonian–Laird + Hartung–Knapp, subgroups, leave-one-out, Egger (k ≥ 10), meta-regression |

Multiplicity: primary outcome Holm, secondary outcomes Benjamini–Hochberg within category; significance wording follows the adjusted P.
Spec fields and data layouts: `reference/DESIGN_SPEC.md`. From research question to spec: `reference/GAP_TO_DESIGN.md`.
`intake` only *guesses* the design, control group, primary outcome and reverse-keyed items — confirm every "open question" before `results`.

---

## 3. Any other data: pick the block by the *shape* of the data

| Data shape | Block (`pf.<name>`) |
|---|---|
| curve per participant (time, cycle, distance) | `ax_bands`, `ax_diff_band`, `ax_spm` |
| 1 number per participant, paired conditions | `ax_paired_estimate` |
| 1 number per participant, groups / ≥ 3 conditions | `ax_raincloud` |
| ≥ 3 time points by group | `ax_multitime(..., band=True)`, `ax_timepoints` |
| pre/post by arm | `ax_prepost` |
| many outcomes | `fig_forest_effects` |
| agreement / reliability | `ax_identity`, `ax_bland_altman` |
| ordinal items / scales | `ax_likert`, `ax_corr_heatmap`, `ax_radar`, `ax_mediation` |
| time-to-event | `km_estimate`, `ax_km`, `at_risk_table` |
| binary prediction | `ax_roc`, `ax_calibration` |
| evidence synthesis | `fig_meta_forest`, `ax_funnel` |
| dose–response | `ax_dose_response`, `fit_band` + `ax_fit_band` |
| individual response | `ax_waterfall` |
| composition | `ax_stacked_bars` |
| omics | `ax_volcano`, `ax_heatmap`, `ax_ellipse` |
| spatial | `ax_ellipse`, `ax_pitch_heat` |
| eye tracking (fixations on a stimulus) | `ax_gaze_heatmap`, `fig_gaze_heatmap_grid`, `gaze_density`, `to_screen_px` (see *Eye tracking* below) |
| design / flow | `draw_flow`, `ax_gantt` |

All 26 data types have a runnable example in `examples/gallery/` (pictures in `assets/pubstyle_gallery/`); selection rules and colour
conventions in `reference/DATA_TYPE_GUIDE.md`; signatures in `reference/API.md`; scenario → picture in `reference/FIGURE_CATALOG.md`.
If no block fits, plain matplotlib after `apply_style` still uses the navy palette (default colour cycle and colour map are set) — but add
panel titles, direct labels and CIs by hand to match §5.

```python
from sportsci_figures.pubstyle import apply_style, save_figure, condition_colors, panel_title, DOUBLE, ResultsDoc, figures as pf
import matplotlib.pyplot as plt

apply_style("en")                                          # or "zh" — BEFORE any figure
col = condition_colors(["CON", "RT20", "RT30", "RT45"])    # CON sand; doses light periwinkle -> navy
fig, ax = plt.subplots(figsize=(DOUBLE, 3.4))
pf.ax_bands(ax, x, {"CON": (mu0, se0), "RT20": (mu1, se1)}, col, dashed=["CON"])
ax.set_xlabel("Time after start (h)"); ax.set_ylabel("Glucose (mmol/L)")
panel_title(ax, "a", "Glucose time course")
save_figure(fig, "out/fig2_timecourse")                    # -> .png (300 dpi) + .pdf, tagged "Simulated data"

d = ResultsDoc("en")                                       # profile="thesis", chapter=4 for 小四 / 1.5 spacing / Figure 4.1
d.title("3  Results"); d.notice()                          # notice() only when data are simulated
d.para(f"{n} participants were included …")                # numbers from variables, never typed
d.figure("out/fig2_timecourse.png", "Glucose time course. a, …")
d.table(df, "Baseline characteristics", note="Mean ± SD …")
d.save("out/results.docx")
```
Complete two-language reference script: `examples/pubstyle_demo.py`.

### Eye tracking: one input contract, one look

Fixation heat maps look the same for every user and every data set because nothing in them is estimated from the data or left to taste.

| Fixed by the function | Set by you (state it once) |
|---|---|
| Gaussian kernel of fixed width `sigma = 0.02` of the screen width (about 1°), not data-driven | `screen=(W, H)` of the display, in pixels |
| Value = density **relative to an even spread** (1 = even): independent of resolution, fixation count and the unit of the weights | `units`: `"px"` or `"norm"` (0-1) |
| One colour map (`GAZE_CMAP`), alpha 0.45, scale 0 to the 99th percentile of the panel | `origin`: `"topleft"` (EyeLink, SMI, Tobii px), `"bottomleft"`, `"center"` (PsychoPy pix) |
| Equal weight per participant when `participant=` is given | `weights` (durations), `participant` (ids), `stimulus_box` for an image smaller than the screen |

Rules: pass `participant` for every group map (otherwise one long viewer dominates); use `n_text="auto"` so the counts come from the data;
a panel with fewer than 3 usable fixations says so instead of drawing a blank scale; a warning means more than 5 % of fixations fall off the
screen, so check `screen` / `units` / `origin` before trusting the picture. Colour bars are per panel by default; use
`fig_gaze_heatmap_grid(..., shared_scale=True)` when colours must be compared between panels. A heat map is descriptive: report AOI
statistics (dwell time, first fixation) in a table for any claim.

---

## 4. Hard rules

**Integrity.** Every number in a figure, table or sentence is computed from the data. Simulated data: `ResultsDoc.notice()` plus the footer
tag on every figure, and say so in Methods. Conceptual drawings say "conceptual schematic (not data)". Never write "significant" for P ≥ 0.05;
never write "equivalent" for a non-significant difference; label unadjusted secondary analyses exploratory.

**Figure anatomy.** Width 7.2 in (two columns) or 3.5 in (one); compound heights 2.7–5.3 in. Fonts 7 pt, ticks 6.5 pt, annotations 5.5–6 pt,
panel letters 9 pt bold, nothing below 5 pt. No top/right spines; the only grid is faint dotted horizontal hairlines (`hair_y`). Axis label =
quantity + unit (`Glucose (mmol/L)`); time axes say what t = 0 is. Legends frameless, direct labels preferred. Say whether bands are SEM or 95% CI.

**Colours (fixed roles, `pubstyle/style.py`).** primary navy `#112378` · control sand `#C9A66B` · contrast terracotta `#C4573F` · middle dose
`#3F4F9E` · slate `#8E98C6` · teal `#2F6F73` · ink `#161A26` · annotation grey `#626778`. Diverging maps terracotta–paper–navy (`DIVERGING`),
sequential paper→navy (`SEQ`). Never rainbow maps, pure red/green/blue, `viridis`/`magma`, or other palettes —
with **one named exception**: eye-tracking fixation heat maps use the rainbow-type `turbo` map, because that is the field's convention and
hot spots must read on photographs. It is the default of the gaze blocks only (`GAZE_CMAP`, overridable with `cmap=`); everything else, including
other heat maps drawn on a stimulus or a pitch, stays navy.

**Tables.** Three-line only (thick top and bottom rules, thin header rule, no vertical lines, no shading); first column left, others centred.
`mean ± SD`, `n (%)`, `estimate (95% CI)`, P as `<0.001` or three decimals (never `0.000`). Table 1 reports SMD, not only P. A footnote states
the model/test, adjustment, multiplicity rule and abbreviations. Export the same tables to Excel (`save_tables_xlsx`).

**Statistics (defaults).** Pre–post with control: ANCOVA on follow-up with baseline covariate, Hedges g. Crossover: LMM with participant random
intercept and period, EMMs, Holm-adjusted contrasts, d_z. Skewed outcomes: log-transform (ratios, mark `†`) or non-parametric. Report missing
data, exclusions and sensitivity analyses.

---

## 5. Finish rules (polished, not merely correct)

- CI bars and whiskers in the **group colour**, no caps, white-edged mean markers — never black error bars over coloured data.
- Time courses: mean line + **shaded 95% CI ribbon**, control dashed, **direct labels** at line ends (collision-free) instead of a legend.
- A single model contrast is an **estimation panel** (`results.plots.diff_estimate`: sampling distribution + estimate + CI + numbers), not a one-row forest.
- Densities taper smoothly (`ax_raincloud`); long tick labels wrap (`wrap_label`); panel widths follow content, `wspace` ≈ 0.35–0.45.
- Forest plots: category colour bars, zebra rows, value column next to the axis, "favours" labels on top.

Design rationale and the palette: `docs/STYLE_GUIDE.md`.

---

## 6. Workflow for an AI agent

1. Raw file? Run `intake` first and work on `data_clean.csv`; never copy the `_private/` ID map into outputs or prompts.
2. Identify design and outcomes by role (primary / secondary / safety); decide the language set (§1).
3. Standard design → `design.json` + `results`. Otherwise do the statistics with statsmodels / scipy / pingouin and keep tidy DataFrames.
4. Build figures with blocks, one script for both languages (`tr`). Save with `save_figure`; open each PNG; run §7.
5. Tables as DataFrames of strings (`fmt_msd`, `fmt_ci`, `fmt_p_table`) → `ResultsDoc.table` + `save_tables_xlsx`.
6. Results text with f-strings and conditional wording; number figures/tables in order of first mention; `ResultsDoc.save`.
7. Run `python -m pytest -q` after changing library code.
8. Report what was produced and where, the language set, exploratory/unadjusted analyses and limits (e.g. simulated data). Hand over
   `methods_explained.md`: whoever presents the work must be able to explain every analytic choice.

---

## 7. Self-check before handing over

Figures (open the PNG): language consistent (en has no Chinese) · no tofu boxes, minus and Greek render · nothing overlaps or is clipped ·
panel letters + titles aligned · units on every axis, t = 0 defined, n shown · raw data + estimate ± CI, band type stated · colours per §4,
control dashed, dose order readable in greyscale · "Simulated data" tag when applicable · PNG + PDF exist.
Tables: three-line, header bold, first column left · number formats per §4 · footnote with model, adjustment, multiplicity.
Text: every number traceable to a variable · conditional wording · exploratory analyses flagged · numbering follows first mention.

## 8. Known pitfalls

- `font.family` must stay a **list** (`['Arial', 'Microsoft YaHei']`) for per-character fallback; `apply_style` sets it — do not override rcParams afterwards.
- Figures created before `apply_style` keep the old fonts and colours.
- No CJK font installed → `has_cjk_font()` is False and zh figures show boxes: install Noto Sans CJK SC or Microsoft YaHei first.
- Windows console: set `PYTHONIOENCODING=utf-8` to print Chinese.
- Survey scale names become columns and must not clash with existing column names; feed raw item answers (reverse items are recoded by the engine).

## 9. Files

| Path | Purpose |
|---|---|
| `sportsci_figures/pubstyle/` | style (`style.py`), figure blocks (`figures.py`, `figures_ext.py`), tables (`tables.py`), Word document (`report.py`) |
| `sportsci_figures/results/` | design-spec engine: `spec.py`, `analysis*.py`, `builders*.py`, `plots.py`, `explain.py`, `simulate.py`, `build.py` (`run_results`) |
| `sportsci_figures/intake.py`, `privacy.py`, `profiler.py` | raw-file check, de-identification, layout detection |
| `sportsci_figures/cli.py`, `cli.py` | command line |
| `config/design_templates/` | runnable templates for the six designs; `config/meta_extraction_template.csv` |
| `reference/` | `DESIGN_SPEC`, `GAP_TO_DESIGN`, `DATA_TYPE_GUIDE`, `FIGURE_CATALOG`, `API`, `STYLE_SPEC_ZH`, `STYLE_SPEC_EN` |
| `docs/STYLE_GUIDE.md` | design rationale, palette, finish rules |
| `examples/pubstyle_demo.py`, `examples/gallery/` | two-language reference script; 26 data types (`python examples/gallery/make_gallery.py`) |
| `assets/` | rendered gallery and examples — the look to match |
| `tests/` | estimates recover simulated truth, reference implementations agree, both languages end to end, palette guard |
