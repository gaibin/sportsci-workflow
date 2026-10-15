# Figure catalogue — scenario → block → picture

All pictures are rendered by `examples/pubstyle_demo.py` (synthetic data) in both language sets:
`assets/pubstyle_examples/zh/*.png` and `assets/pubstyle_examples/en/*.png`.
For a complete, current-style result package run `python cli.py results config/design_templates/<design>.json --simulate`.

| # | Scenario | Picture | Blocks | Layout |
|---|---|---|---|---|
| 1 | Participant flow (CONSORT-like) with computed counts | `fig1_flow.png` | `draw_flow` | 7.2 × 3.2–5.2 in; boxes: slate border = flow, primary/control-colour border = analysed sample |
| 2 | Time-course by condition, zoom, paired difference | `fig2_timecourse.png` | `ax_bands` `shade_window` `mark_events` `pointwise_diff_ci` `ax_diff_band` | `gs(2,2)`, a spans the top row |
| 3 | Primary outcome of a crossover: raw + estimate, contrasts, dose–response | `fig3_paired_estimate.png` | `ax_paired_estimate` `ax_contrast_forest` `ax_dose_response` | `gs(1,3, ratios 1.25/1/.95)`, 7.2 × 3.35 in |
| 4 | Pre/post individual trajectories by arm (key outcomes) | `fig4_prepost.png` | `ax_prepost` | `subplots(2,3)`, 7.2 × 5.2 in, difference + P in each sub-title |
| 5 | All outcomes, standardised effects by category | `fig5_forest.png` | `fig_forest_effects` | tall single axes; filled = adjusted-significant, grey = safety |
| 6 | Composition bars + 24-h profile + dose–response scatter | `fig6_composition_profile_scatter.png` | `ax_stacked_bars` `ax_agp` `ax_scatter_fit` | `gs(1,3, ratios 1/1.2/1)`, 7.2 × 2.9 in |
| 7 | Eye tracking: fixation density by stimulus category | `fig7_gaze_heatmap.png` (from `examples/gaze_heatmap_demo.py`, not part of the 6-figure demo) | `fig_gaze_heatmap_grid` (`ax_gaze_heatmap`, `gaze_density`) | 2 × 3 grid, 7.2 in wide, one colour bar per panel (or `shared_scale=True`); pool the fixations of a category on one representative image and say so in the legend |

Real-project examples (zh): `图1_受试者流程`, `图2_干预日血糖曲线`, `图3_主要结局_net_iAUC`, `图4_次要结局_时间窗与24h指标`, `图5_研究二_CGM`, `图6_研究二_全部结局效应量森林图`, `图7_研究二_个体前后轨迹`, `图8_干预组依从性与改善幅度`.

## Recipes for common needs (what to call, in what order)

**A. Two-arm RCT, pre/post** → Table 1 (baseline, SMD, P) · Fig `ax_prepost` small multiples · Fig `fig_forest_effects` · Table of all outcomes (`pre/post by arm`, between-group difference (95% CI), P, BH q, Hedges g).

**B. Crossover with time-course outcome** → `fig2` (curves) · `fig3` (primary compound) · secondary panels with `ax_paired_estimate` (2×3 grid) · Table of estimated marginal means · Table of contrasts (difference (95% CI), P, Holm P, d_z).

**C. Continuous monitoring (CGM, HR, power) at group level** → `ax_agp` per arm/visit; composition bars for time-in-zone; individual change slope-graph for the primary metric.

**D. Dose adherence vs response** → `ax_scatter_fit` ×3, one row.

**E. Safety / adverse events** → table only (counts by event × arm); a figure is unnecessary.

## Layout numbers worth keeping
- Compound figure margins come from `bbox_inches="tight"`; do not call `tight_layout` together with `gridspec(hspace=…)`.
- Panel-letter offsets: `dx = −0.04 … −0.2` depending on y-label width; `dy = 1.04 … 1.22` when sub-titles are two lines.
- Legends inside the empty top of a time-course axes: use direct labels at `(x, y)` pairs, 2 columns, keeping ≥ 3 data-units between columns.
- Annotations in the lower-right of axes: `transform=ax.transAxes, ha="right", va="bottom", fontsize=5.5, color=C_GREY`.

## Extended gallery (v3): 26 data types

The six figures above come from `examples/pubstyle_demo.py`. `examples/gallery/` adds **26 more data types / 30 figures** (physiology, EMG, force
curves, SPM, GRF, IMU, strength, reliability, responders, pacing, DXA, psychology questionnaires, survival, diagnostics, meta-analysis, dose-response,
sleep, biomarkers, omics, timeline, balance, GPS, ambulatory BP). Pictures: `assets/pubstyle_gallery/{zh,en}/` and the contact sheets
`assets/pubstyle_gallery/montage_{zh,en}_NN.png`. The data-shape -> block rules and the table of all 26 are in `reference/DATA_TYPE_GUIDE.md`.
