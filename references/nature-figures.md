# Nature-style figures for sport science

The defaults in `assets/matplotlibrc` and the helpers in `scripts/nature_plot.py` already enforce most of these rules. This document explains why each rule exists, so you can deviate intelligently when the data demands it.

## 1. Typography

- **Font family:** Helvetica (preferred) or Arial. Both are sans-serif, both render cleanly at small sizes, both are accepted by Nature, Science, Cell, JAMA, NEJM, MSSE. Never use Times New Roman in figures (it's for body text, not figure labels).
- **Sizes:**
  - Tick labels: 7 pt
  - Axis labels: 8 pt
  - Panel labels (a, b, c): 9 pt **bold**
  - In-figure annotations / significance markers: 7 pt
  - Legend: 7 pt
- All text in a figure should be the same size, except panel labels (slightly larger and bold).

## 2. Color

- **Use a limited palette.** Nature figures rarely use more than 5 colors per panel. Pick from one of:
  - Nature's recommended palette: `#E64B35`, `#4DBBD5`, `#00A087`, `#3C5488`, `#F39B7F`, `#8491B4`, `#91D1C2`, `#DC0000`
  - Colorblind-safe (Wong 2011): `#000000`, `#E69F00`, `#56B4E9`, `#009E73`, `#F0E442`, `#0072B2`, `#D55E00`, `#CC79A7`
  - Sequential data: `viridis`, `cividis`, `plasma` (perceptually uniform)
- **Never use the default matplotlib rainbow / `jet` colormap.** It is perceptually non-uniform and hostile to color-blind readers.
- **Do not encode information by color alone** when shape, hatch, or position can carry it. ~8% of male readers have red-green color blindness.
- For two-group comparisons, prefer **one chromatic color + one neutral** (e.g., `#4DBBD5` and `#888888`), not two saturated colors.

## 3. Axes and spines

- **Only left and bottom spines visible.** Top and right spines off. This is the single biggest visual difference between a default matplotlib plot and a journal figure.
- **Tick direction: outward.** Inward ticks overlap data points.
- **Tick length:** 3 pt. **Tick width:** 0.75 pt.
- **No gridlines.** If you absolutely need a reference line, use a thin (0.5 pt) light gray (`#DDDDDD`) horizontal line.
- **No background fill.** Plot area is white.
- **Axis line width:** 0.75 pt.

## 4. Data presentation

### Continuous data, group comparisons

For n ≤ 30 per group: **always** show individual data points. Options, in order of preference:

1. **Box plot + jittered individual points**: most informative, shows distribution shape and outliers
2. **Violin plot + jittered individual points**: better when distribution shape matters
3. **Bar with error + jittered points overlaid**: common in older sport science papers, acceptable but less informative

Plain bar charts with error bars and no individual points are increasingly rejected as hiding within-group variability. Avoid for n ≤ 30.

### Error bars: always specify what they are

In the figure caption, state explicitly: "Error bars represent SD" / "SEM" / "95% CI". A figure without this is a reviewer red flag.

- **SD**: when describing the spread of the sample
- **SEM**: when comparing means and showing precision of the estimate (most common in sport science)
- **95% CI**: preferred by modern statistical guidelines and recommended for new submissions

### Significance markers

- Use brackets connecting the compared groups, with `*`, `**`, `***`, or the actual P-value.
- `*` P < 0.05, `**` P < 0.01, `***` P < 0.001. State this in the caption.
- For ≤ 4 comparisons, prefer printing the actual P-value (e.g., `P = 0.032`).
- For multiple comparisons, state which correction was applied (Bonferroni, Holm, FDR).

### Lines (time-series, dose-response)

- Line width: 1.0–1.25 pt.
- Markers at data points: small (size 4), filled.
- Confidence band: shaded region at 20–30% alpha, same color as line.
- For multiple lines, **use direct labels** (text next to the line endpoint) instead of a legend box when ≤ 4 lines.

### Scatter plots

- Marker: filled circle, size 15–25 pt², edge color slightly darker than fill, edge width 0.4 pt.
- For dense data: use alpha 0.5 or hexbin/2D density.
- Add regression line with shaded 95% CI band.
- Print Pearson r (or Spearman ρ) and P-value in the corner of the panel.

## 5. Layout

- **Single column:** 89 mm wide (3.5 in)
- **1.5 column:** 120–136 mm (4.7–5.4 in)
- **Double column / full width:** 183 mm (7.2 in)
- **Aspect ratio:** typically 1:1 to 4:3. Never wider than 16:9 unless time-series demand it.

### Multi-panel figures

- Panel labels: lowercase bold, top-left of each panel: `a`, `b`, `c`.
- Panel labels positioned **outside** the plot area, not over the data.
- Panels separated by clear whitespace (5–10 mm gap), not lines.
- Share axes between panels when comparing equivalent measures (use `sharey=True`).

## 6. Export

Always export both:

- **PDF** (vector): for journal submission
- **PNG at 300 DPI**: for previews, slides, supplementary material

Use TIFF (LZW compression) only if the journal explicitly requires it.

```python
fig.savefig("figure_1.pdf", bbox_inches="tight", pad_inches=0.05)
fig.savefig("figure_1.png", dpi=300, bbox_inches="tight", pad_inches=0.05)
```

## 7. Captions

A Nature-quality caption has four parts in this order:

1. **One-sentence title** (bold or italic, depending on journal).
2. **Brief description** of what each panel shows.
3. **Sample sizes** (n per group).
4. **What the error bars mean and what statistical test produced any P-values.**

Example:
> **Figure 1 | HIIT improves VO2max more than MICT over 8 weeks.** (a) Individual VO2max trajectories for the HIIT group (n = 15). (b) Individual trajectories for the MICT group (n = 15). (c) Group means at week 8. Box plots show median, IQR, and range, with individual points overlaid. Error bars in panel (c) represent 95% CI. *** P < 0.001, two-way mixed ANOVA followed by Bonferroni-corrected post-hoc tests.

## 8. What to avoid (Nature-specific aesthetic)

- 3D bar charts, pie charts, exploded slices: never appropriate
- Drop shadows, gradients, beveled edges
- Colored backgrounds (light gray, light blue, etc.)
- Excel default styling
- Logos, watermarks, decorative borders
- More than one font family per figure
- Axis labels at 45° (use horizontal labels with shorter category names instead)

## 9. Forest plots (for meta-analysis)

- Effect estimate as filled square, sized in proportion to study weight.
- 95% CI as horizontal line through the square.
- Pooled estimate as diamond at bottom. Diamond width = CI.
- Vertical reference line at the null effect (1 for ratios, 0 for differences).
- Heterogeneity statistics ($I^2$, τ², Q with df and P) printed below.
- Subgroups separated by horizontal whitespace and a subtotal diamond per subgroup.
