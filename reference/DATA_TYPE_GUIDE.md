# Data-type guide — which figure for which data (26 data types, all with a runnable example)

The house style is **data-agnostic**: the same palette, geometry, typography, tables and statistics rules apply to every data type.
What changes is the *figure block*. `examples/gallery/` simulates 26 data types and draws 30 figures in both language sets
(`python examples/gallery/make_gallery.py` → `outputs/gallery/{data,figures}`; rendered copies in `assets/pubstyle_gallery/`).
Take the closest row, copy its function from `examples/gallery/d_*.py`, replace the simulated data.

## 1. Selection rules (follow in this order)

| Your data look like … | Use | Notes |
|---|---|---|
| A curve per participant over time / cycle / distance (CGM, HR, power, EMG envelope, joint angle, GRF, pacing) | `ax_bands` (mean ± SEM, or ± SD for waveform "clouds") + `ax_diff_band` for paired differences | State SEM vs SD. Waveforms on a normalised axis (% cycle, % stance). |
| Two waveforms compared point-by-point | `ax_bands` + `ax_spm` (permutation max-t threshold, shaded clusters) | Never report pointwise P without a field-wise correction. |
| One number per participant, 2 paired conditions | `ax_paired_estimate` (raw lines + estimate ± CI) | Lines only when the subject has every condition. |
| One number per participant, ≥3 conditions or unpaired groups | `ax_raincloud` (density + raw points + IQR + mean ± CI), `paired_lines=` for repeated measures | n up to a few hundred. |
| Same measure at ≥3 time points by group | `ax_multitime` (faint individuals + mean ± 95% CI, dodged) or `ax_timepoints` (any categorical time; `log=True` for fold-changes) | |
| Pre/post by arm | `ax_prepost` | add `ax.set_yscale('log')` + `minorticks_off()` for skewed outcomes. |
| Many outcomes, one effect size each | `fig_forest_effects` (Hedges g, BH-q filled markers, safety in grey) | |
| Method agreement / test–retest | `ax_identity` (ICC, r) + `ax_bland_altman` (bias, LoA with CI) + ICC forest with CV% | |
| Ordinal items (Likert, PHQ-9, RPE categories) | `ax_likert` (diverging stacked %) — never means ± SD of single items | |
| Several scales, structure | `ax_corr_heatmap` (lower triangle, bold P<0.05), `ax_radar` (profiles), `ax_mediation` (path + bootstrap) | |
| Time-to-event (injury, drop-out) | `km_estimate` + `ax_km` + `at_risk_table`, HR forest (log axis) | CI bands, censor ticks, numbers at risk. |
| Binary outcome, screening tool | `ax_roc` (AUC with bootstrap CI, Youden point), `ax_calibration`, `ax_raincloud` of predicted risk | Legend below the axes. |
| Evidence synthesis | `fig_meta_forest` (+ subgroup colours), `ax_funnel`, meta-regression with `fit_band` | |
| Dose–response | `fit_band` / `ax_fit_band` (linear, quadratic, Emax; bootstrap band) + raincloud per dose | |
| Responders / individual differences | `ax_waterfall` (SWC band, typical-error whiskers) | colours: beneficial primary (navy), trivial slate, harmful contrast (terracotta). |
| Composition (time-in-range, body composition, sleep stages) | `ax_stacked_bars` (`ylim=None` for absolute values, `legend=True`) | |
| High-dimensional (omics, biomarker panels) | `ax_volcano`, `ax_heatmap` (clustered rows, group strip), PCA scores with `ax_ellipse` | |
| Spatial (centre of pressure, pitch tracking) | `ax_ellipse` (95% ellipse), `ax_pitch_heat` | |
| Study design | `draw_flow` (participant flow), `ax_gantt` (schedule), bars + line (periodisation) | |

If nothing fits: compose from the primitives (`ax_bands`, scatter, bars, `ax_raincloud`), obey the rules in `SKILL.md` §3, then add the new
block to `figures_ext.py`, a demo to the gallery and a row here.

## 2. Gallery: 26 data types

| ID | Data type | Figures | Blocks |
|---|---|---|---|
| D01 | Graded exercise test, VO₂ kinetics | lactate–power curves, 4 mmol/L power pre/post, τ raincloud | `ax_bands` `ax_prepost` `ax_raincloud` |
| D02 | Heart-rate recovery, HRV | HR recovery curves, HRR60, rMSSD (log) | `ax_bands` `ax_paired_estimate` `ax_prepost` |
| D03 | Training load, ACWR, injuries | weekly load, athlete × week heat map, injury rate by ACWR zone | `ax_heatmap`, Wilson-CI bars |
| D04 | Surface EMG | gait envelope, RMS/MDF decoupling, slopes | `ax_bands` `ax_raincloud` |
| D05 | Force–time curves (IMTP, PAP) | curves, RFD, force at 300 ms | `ax_bands` `ax_paired_estimate` `ax_raincloud` |
| D06 | Force–velocity–power profile | F–v lines, power curves, Pmax | scatter + lines, `ax_raincloud` |
| D07 | Joint-angle waveforms, SPM | mean ± SD, SPM{t}, peak flexion | `ax_bands` `ax_spm` `ax_paired_estimate` |
| D08 | Vertical GRF, loading rate | curves + inset histogram, loading-rate paired cloud | `ax_bands` `ax_raincloud` |
| D09 | Wearable IMU | raw trace + detected steps, identity, Bland–Altman, asymmetry | `ax_identity` `ax_bland_altman` `ax_raincloud` |
| D10 | Strength training, 3 groups × 5 times | trajectories, difference vs control, 16-wk gain | `ax_multitime` `ax_timepoints` `ax_raincloud` |
| D11 | Test–retest reliability | identity, Bland–Altman, ICC forest | `ax_identity` `ax_bland_altman` |
| D12 | Responder analysis | waterfall, classification, regression to the mean | `ax_waterfall` |
| D13 | Time-trial pacing | pacing bands, pointwise difference, finish time | `ax_bands` `ax_diff_band` `ax_paired_estimate` |
| D14 | DXA body composition | stacked masses, ΔLM vs volume, ΔFM | `ax_stacked_bars` `ax_scatter_fit` |
| D15 | Psychology questionnaires (RCT, 3 times) | trajectories, change raincloud, responders, PHQ-9 items, correlations, POMS radar, mediation | `ax_multitime` `ax_likert`-style bars `ax_corr_heatmap` `ax_radar` `ax_mediation` |
| D16 | Time-to-injury | KM + risk table, adjusted HR, injury rate | `ax_km` `at_risk_table` |
| D17 | Diagnostic accuracy | ROC, calibration, predicted-risk cloud | `ax_roc` `ax_calibration` |
| D18 | Meta-analysis | forest, funnel, subgroup, meta-regression | `fig_meta_forest` `ax_funnel` `fit_band` |
| D19 | Caffeine dose–response | Emax fit + band, per-dose clouds | `fit_band` `ax_raincloud` |
| D20 | Sleep & steps (wearables) | stage composition, nightly sleep, steps | `ax_stacked_bars` `ax_bands` |
| D21 | Blood biomarkers over time | fold-change (log) for 3 markers, 12-marker heat maps | `ax_timepoints` `ax_heatmap` |
| D22 | Proteomics / myokines | volcano, clustered heat map, PCA ellipses | `ax_volcano` `ax_heatmap` `ax_ellipse` |
| D23 | Study timeline & periodisation | Gantt, volume bars, intensity line | `ax_gantt` |
| D24 | Balance (centre of pressure) | trajectory + ellipse, group ellipses, sway area | `ax_ellipse` `ax_raincloud` |
| D25 | GPS tracking | pitch heat map, speed-zone distance, high-speed running | `ax_pitch_heat` |
| D26 | Ambulatory blood pressure | 24-h profile, dipping, dipper classes | `ax_bands` `ax_raincloud` `ax_stacked_bars` |

## 3. Colour conventions added for the extended blocks
- Likert / ordinal: contrast (negative) → light grey (neutral) → slate (positive); 4-level PHQ-style: slate, light slate, light contrast, contrast.
- Correlation / diverging heat maps: `DIVERGING` (terracotta ↔ paper ↔ navy). Sequential heat maps: `SEQ` (paper → navy).
- Volcano: up primary, down slate, n.s. light grey. Responders: beneficial primary, trivial slate, harmful contrast.
- ≥5 unordered categories: `category_colors(n)` (primary, control, contrast, slate, teal, blue, violet, brown).
