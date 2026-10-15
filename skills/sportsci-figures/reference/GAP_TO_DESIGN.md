# From research gap to `design.json` (the part an AI agent does *before* the results engine)

Goal of the whole chain: **(1)** find a real gap in the literature → **(2)** fix an experimental or meta-analytic design *before* seeing data →
**(3)** run the results engine on the data → **(4)** write Results/Discussion from `analysis.json`.

## 1. Find the gap (no invented references)
1. Search the literature with your usual tools (PubMed, Europe PMC, OpenAlex, Web of Science, CNKI). Read the papers yourself;
   never cite a study you have not read, and verify every DOI before it enters the reference list.
   Without network access, ask the user for PDFs/abstracts — never fabricate citations or effect sizes.
2. Write the gap as one sentence in PICO form: Population, Intervention (dose!), Comparator, Outcome(s). Record 3–5 supporting papers with DOIs.
3. State what result would be *informative either way* (the "so what"): e.g. "no difference between 20 and 45 min" is only a finding with an equivalence margin.

## 2. Pick the design
| Question | Design | Why |
|---|---|---|
| Acute response to several exercise doses/conditions, reversible outcome | `crossover` | each participant is own control; needs washout and randomised order |
| Chronic effect of a programme vs control | `parallel_prepost` | ANCOVA is the efficient, pre-specifiable analysis |
| Time course / durability / dose over weeks | `multitime` | ≥ 3 assessments; constrained baseline model |
| Is there enough evidence yet / how large is the effect across studies | `meta` | pool, explore heterogeneity, assess bias |
| Several phases | write one `design.json` per study (e.g. study 1 crossover, study 2 parallel) |

## 3. Fix the analysis plan in the spec (this *is* pre-registration)
- Exactly one primary outcome (or a small Holm family); everything else `primary: false` with a `category`.
- Orient every outcome with `direction`; set `decimals` and units.
- For crossover add `dose` and `pairs` only if you pre-specify them; for meta set `effect`, `direction`, planned `subgroup` and `moderator` (≤ 2).
- Sample size: compute with the primary contrast and write it in the Methods text (parallel ANCOVA ≈ two-sample t on the adjusted SD; crossover uses SD of the paired difference; meta needs only k).
- Commit `design.json` (and a hash/date in the lab notebook) before data lock.

## 4. Data checklist
- Long format, one row per participant × time (or × condition / per study). Column names exactly as in `columns`.
- `python cli.py check-design design.json -d data.csv` must pass.
- Meta: fill `config/meta_extraction_template.csv` from the papers (two independent extractors if possible); record where each number came from.

## 5. Rehearse before real data (optional but recommended)
Add a `simulate` block with the *plausible* true effects and run `python cli.py results design.json --simulate -l both`. This checks the whole chain,
shows what the paper will look like, and the recovery tests show the estimator is unbiased. Simulated output is stamped "Simulated data" and must never be
presented as evidence.

## 6. After the results
Use `analysis.json` for every number in Discussion/Abstract. Interpret by CI, not only by P; flag secondary outcomes as exploratory; for "no difference" claims
report the CI and, if the claim is equivalence, run an equivalence test against a pre-stated margin.
