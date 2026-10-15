# `sportsci_figures.pubstyle` — API

```python
from sportsci_figures.pubstyle import (apply_style, save_figure, panel_letter, hair_y, fmt_p, t, verify_language,
                                     dose_colors, condition_colors, arm_colors, ResultsDoc,
                                     fmt_num, fmt_msd, fmt_ci, fmt_p_table, fmt_n_pct, save_tables_xlsx,
                                     DOUBLE, SINGLE, C_MAGENTA, C_AMBER, C_CORAL, C_SLATE, C_TEAL, C_INK, C_GREY, C_LIGHT)
from sportsci_figures.pubstyle import figures as pf
```

## style
| Function | Purpose |
|---|---|
| `apply_style(lang)` | `'zh'` or `'en'`. Sets rcParams, fonts (installed fonts only), unicode minus, 300 dpi, TrueType PDF. **Call first.** |
| `save_figure(fig, stem, simulated=True)` | writes `stem.png` (300 dpi) + `stem.pdf`, adds footer tag, closes the figure; raises `ValueError` if an English figure contains CJK |
| `panel_letter(ax, 'a', dx=-0.02, dy=1.04)` | bold lowercase panel label |
| `hair_y(ax)` | faint horizontal dotted grid (the only grid allowed) |
| `fmt_p(p)` | `'P < 0.001'` / `'P = 0.012'` / `'—'` |
| `t(key, lang=None)` | common phrases (`'baseline'`, `'control'`, `'simulated'`, `'disclaimer'`, …) in the active language |
| `dose_colors(n)` | n colours light periwinkle → navy, monotone lightness |
| `condition_colors(names)` | dict: control-like names (`CON`, `control`, `placebo`, `baseline`, …) → control colour; others → ramp in order given |
| `arm_colors(control, intervention)` | `{control: control colour (sand), intervention: primary (navy)}` |
| `verify_language(fig)` | list of CJK strings found in an English figure (empty = OK) |
| `has_cjk_font()` / `font_chain(lang)` | diagnostics |

## figures (axes-level, draw on a given `ax`)
| Function | Key arguments |
|---|---|
| `ax_bands(ax, x, series, colors, dashed=(), lw=1.4)` | `series = {name: (mean, se)}` |
| `shade_window(ax, x0, x1, text=None, text_y=None)` | highlighted exposure window |
| `mark_events(ax, [(x, label)], y, label_dy)` | triangles + labels (meals, doses) |
| `pointwise_diff_ci(a, b)` | subjects×time arrays → `(mean, lo, hi)` of a−b (uncorrected t CI) |
| `ax_diff_band(ax, x, {name: (mean, lo, hi)}, colors, ref_label=None)` | difference band, dashed zero line in the control colour, marks the minimum |
| `ax_paired_estimate(ax, wide_df, order, colors, est, ylabel, label_map=None)` | `est = {cond: (estimate, lo, hi)}`; returns n with all conditions |
| `ax_contrast_forest(ax, rows, xlabel, threshold=None, threshold_label=None)` | `rows=[dict(label, est, lo, hi, color, hollow, ptext)]` |
| `ax_dose_response(ax, doses, colors, xlabel, ylabel, trend=(slope, intercept), note=None, xtick_labels=None)` | `doses={label: dict(x, diffs, est, lo, hi)}` |
| `ax_prepost(ax, long_df, id_col, group_col, time_col, y_col, groups, colors, time_labels, ylabel, title=None)` | time ∈ {0,1} |
| `ax_stacked_bars(ax, bars, part_order, part_colors, ylabel, group_labels, positions)` | `bars=[(tick_label, {part: value})]` |
| `ax_scatter_fit(ax, x, y, color, xlabel, ylabel)` | OLS line, 95% CI band, r and P; returns `(r, p, n)` |
| `ax_agp(ax, x, q, color, label)` | `q` keys 5, 25, 50, 75, 95 |
| `fig_forest_effects(rows, categories, cat_colors, xlabel, footnote='', row_h=0.165)` | `rows=[dict(category, label, g, lo, hi, sig, neutral, text)]`, orientation already + = favourable; returns a figure |
| `draw_flow(ax, boxes, arrows, texts, xlim, ylim)` | boxes/arrows in data coordinates |

## tables / report
| Function | Purpose |
|---|---|
| `fmt_num(x, nd=None)` | adaptive decimals; `—` for missing |
| `fmt_msd(series)` | `mean ± SD` |
| `fmt_ci(est, lo, hi, nd=None)` | `est (lo, hi)` |
| `fmt_p_table(p)` | `<0.001` / `0.012` |
| `fmt_n_pct(bool_series)` | `n (%)` |
| `save_tables_xlsx({name: df}, path)` | one sheet per table |
| `ResultsDoc(lang)` | `.title .heading .para .notice .figure(png, caption, width_cm) .table(df, caption, note, font, col_widths) .save(path)`; automatic numbering "Figure N." / "图 N", "Table N." / "表 N" |

## Adding a new figure block
1. Draw only on the `ax` you receive; take colours from `style.py`; take every text string as an argument (so both languages work).
2. No hidden data: all numbers arrive via arguments.
3. Add a picture to `assets/pubstyle_examples/` by extending `examples/pubstyle_demo.py`, and list it in `reference/FIGURE_CATALOG.md`.
4. Extend `tests/test_pubstyle.py` if the block introduces a new text pattern.

## figures_ext (re-exported as `pf.<name>`)

| Function | Purpose / key arguments |
|---|---|
| `ax_raincloud(ax, groups, colors, ylabel, show_ci=True, horizontal=False, paired_lines=None)` | half-violin (observed range only) + jittered points + IQR bar + mean +/- 95% CI |
| `ax_bland_altman(ax, a, b, xlabel, ylabel, unit='', pct=False)` | bias, 95% limits of agreement with CI shading; returns `(bias, lo, hi)` |
| `ax_identity(ax, x, y, xlabel, ylabel)` / `icc_2_1(a, b)` | line of identity + OLS + ICC(2,1); returns `(icc, r)` |
| `ax_likert(ax, items, pct, level_labels, colors=None, xlabel='')` | diverging stacked % bars (pct = items x levels, rows sum to 100) |
| `ax_corr_heatmap(ax, corr, labels, pvals=None)` | lower-triangle correlation matrix, contrast↔primary diverging scale; bold = P<0.05 |
| `ax_mediation(ax, names, a, b, c, cp, indirect)` | X->M->Y path diagram; coefficient strings already formatted |
| `ax_radar(ax_polar, cats, series, colors, rmax, rmin=0, ring_step=None)` | profile radar (ax must be polar) |
| `ax_timepoints(ax, x_labels, {name: (est, lo, hi)}, colors, dodge, log, dashed, ylabel)` | point-range lines across categorical time |
| `ax_multitime(ax, long_df, id_col, group_col, time_col, y_col, groups, colors, times, time_labels, ylabel)` | faint individuals + mean +/- 95% CI per time |
| `km_estimate(time, event)` / `ax_km(ax, curves, colors, xlabel, ylabel)` / `at_risk_table(ax, {name: (time, event)}, colors, times)` | Kaplan-Meier with Greenwood log-log CI, censor ticks, numbers at risk |
| `roc_points` `auc_ci` `ax_roc(ax, y, {name: score}, colors)` `ax_calibration(ax, pred, obs)` | ROC with bootstrap AUC CI and Youden point; decile calibration with Wilson CI |
| `meta_random_effects(es, se)` / `fig_meta_forest(df, pooled, xlabel, left_header, right_header, subgroup_col=None)` / `ax_funnel` | DerSimonian-Laird pooling, forest with weights, funnel plot |
| `fit_band(x, y, kind)` / `ax_fit_band(ax, g, fit, lo, hi)` | kind = lin, quad or emax; bootstrap 95% band around the fitted curve |
| `ax_volcano(ax, log2fc, p, names, fc_thr, p_thr, n_label, q=None)` / `ax_heatmap(ax, mat, row_labels, col_labels, cluster_rows, col_colors, annotate)` | omics-style plots |
| `ax_waterfall(ax, changes, swc, te)` | sorted individual changes with SWC band and 90% typical-error whiskers; returns class counts |
| `ax_spm(ax, x, tcurve, thr, label='t')` | SPM{t} with threshold lines and merged supra-threshold clusters |
| `ax_ellipse(ax, x, y, color, level=0.95)` | confidence ellipse (COP, PCA scores); returns area |
| `pitch_outline` / `ax_pitch_heat(ax, x, y)` | football pitch outline, smoothed position density |
| `gaze_density(x, y, weights=None, screen=(1920, 1080), sigma=0.02, grid=(192, 108), units="px", origin="topleft", participant=None, min_points=3, info=None)` | fixed-kernel Gaussian density **relative to an even spread** (mean over the screen = 1); rows top to bottom; zeros if < `min_points` usable fixations; `info` receives n_total / n_used / n_offscreen / n_nonfinite / n_participants |
| `to_screen_px(x, y, screen, units="px", origin="topleft")` | any export convention -> screen pixels, origin top-left (`units` px / norm, `origin` topleft / bottomleft / center); refuses 0-1 values declared as px |
| `ax_gaze_heatmap(ax, x, y, weights=None, background=None, screen, sigma=0.02, cmap=GAZE_CMAP, alpha=0.45, vmax=None, vmax_pct=99, brighten=1.10, label=None, label_color, n_text=None, colorbar=True, units="px", origin="topleft", participant=None, stimulus_box=None)` | fixation heat map over the stimulus (path, PIL image or array); `n_text="auto"` writes participant / fixation counts from the data; `stimulus_box=(x0, y0, x1, y1)` for images smaller than the screen; warns when > 5 % of fixations are off screen; returns `(image, vmax)` |
| `fig_gaze_heatmap_grid(panels, ncols=3, width=DOUBLE, screen, panel_aspect=None, shared_scale=False, **kw)` | grid of `ax_gaze_heatmap`; `panels = [dict(x, y, weights, participant, background, label, label_color, n_text, units, origin, stimulus_box)]`; `shared_scale=True` = one colour scale and one colour bar; unused cells hidden; returns a figure |
| `ax_gantt(ax, tasks, milestones, xlabel)` | study schedule |
| `paired_ci(a, b=None)` / `mean_se_curves(arr, sd=False)` / `category_colors(n)` | helpers |

`ax_stacked_bars(..., ylim=(0, 100), legend=False, total_labels=False)` now also draws absolute-value stacks (`ylim=None`).
`tr(zh, en)` (in `pubstyle`) selects the string of the active language set; use it for every label.
