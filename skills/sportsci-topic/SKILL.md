---
name: sportsci-topic
description: Topic selection and study planning for sport, exercise, health and PE research (theses, proposals, grant applications). Turns a vague interest into a defensible topic - a brief with Chinese and English search terms and real constraints, an evidence map from the student's own records (CNKI / PubMed / Zotero exports or sportsci-refs search) with overlap counts and nearest studies, a design chosen by an explicit rule table (parallel pre-post, crossover, multi-time, single group, survey, meta), exact sample size and the smallest effect the accessible n can detect, a green/yellow/red feasibility rubric with each rule printed, variant comparison, and a one-page topic card plus a design.json draft for sportsci-figures. Use for 选题, 选题可行性, 研究设计, 样本量, 功效分析, 撞题, 研究缺口, 这个题目能不能做, 选哪种设计, topic selection, research gap, power analysis, feasibility. Does not write the proposal text (use sportsci-writing).
---

# sportsci-topic

Counting and calculating, not brainstorming. A topic is acceptable when it is not already crowded, a design exists that can answer it,
the people and weeks are enough, and the instruments exist. Every one of those is a number or a rule here.

## First use (once)

The commands in this skill come from a Python package that ships in this folder. Before the first command, check it is installed:

```bash
sportsci-topic --help
```

If the shell says the command is not found, install it from this skill's folder (Python 3.10+):

```bash
python -m pip install -e <path to this skill folder>
```

If the package is installed but the command is still not found (common on Windows, where pip puts scripts in a folder that is not on PATH), use `python -m sportsci_topic.cli <command>` instead: it is the same program. From a source checkout, `python cli.py <command>` in this folder also works. Do this check once per machine, not before every command.

## Iron rules

1. **Never invent literature, effect sizes or "gaps".** Records come from files the student exports (or `sportsci-refs search`). A gap is a
   statement about the *record set* ("12 records cover P and I, none covers O"); say it that way. Whether it is a real gap is the author's judgement.
2. **The effect size needs a source** (paper DOI + table, pilot, or "smallest effect of interest"). No source = the sample size is only illustrative.
3. **Fix the primary outcome now.** Exactly one `primary = true`, before any data exist.
4. **Do not write the thesis.** The card ends with open items the author must do: read the nearest studies, write the one sentence on how the study differs.
5. **Every number comes from a command.** Never type a sample size, a count or a power into the answer from memory.

## What the agent does (and what the code does)

| Step | Who | How |
|---|---|---|
| Turn the idea into a brief: PICO + Chinese **and** English terms, outcomes with `needs`, constraints | agent + student | `sportsci-topic new` → fill `brief.toml` → `sportsci-topic check brief.toml` |
| Get records | student / `sportsci-refs` | export from CNKI / Wanfang / PubMed / Zotero (`.csv .ris .json .txt`), or `sportsci-refs search "<q>" -o c.md` and export; `--fetch` does it when sportsci-refs is installed |
| Evidence map | code | `sportsci-topic evidence brief.toml -r records.csv` |
| Design + sample size + feasibility + card | code | `sportsci-topic card brief.toml -r records.csv -o topic_out --lang zh` |
| Variants: change one axis, recount | code (agent proposes the alternatives) | add `[[variants.population]]` etc. to the brief → `sportsci-topic variants brief.toml -r records.csv` |
| Explain the card, name the next 3 actions | agent | read `topic_out/topic_card.md` and `topic_data.json`; do not add numbers that are not there |
| Hand over to analysis | code | `sportsci-figures check-design topic_out/design_draft.json` |

Search vocabulary is where the agent adds value: list synonyms, abbreviations, Chinese and English variants per facet. A thin vocabulary gives a falsely empty map.

## Commands

```bash
sportsci-topic new -o brief.toml                  # commented template
sportsci-topic check brief.toml                   # errors, warnings, design, the queries it would run
sportsci-topic evidence brief.toml -r cnki.csv -r pubmed.ris
sportsci-topic variants brief.toml -r cnki.csv [--two-axis]
sportsci-topic power two-sample -e 0.5            # n per group; add --dropout 0.15
sportsci-topic power two-sample --n 17            # smallest detectable d for 17 per group
sportsci-topic power ancova --delta 3 --sd 5 --r-prepost 0.6
sportsci-topic card brief.toml -r cnki.csv -o topic_out --lang zh   # topic_card.md + design_draft.json + topic_data.json
```

`power` tests: `two-sample` (d), `paired` (dz), `ancova`, `correlation` (r), `anova` (f, `--k`), `regression` (f², `--predictors`).

## How to read the card

- **Evidence map** — counts of records matching P+I, I+O, P+O, P+I+O, all years and last five. Fewer than 30 records = "a sketch": say so, ask for more records.
- **Overlap tier** — direct overlap in the last 5 years: 0 / 1–3 green, 4–9 yellow, ≥ 10 red. 1–3 neighbours is normal; the author must state the difference.
- **Sample size** — required n for the stated effect, power at the accessible n, and the smallest effect that n can detect (80 % power). If the accessible n can only
  detect d ≈ 1.0, the honest advice is a bigger effect (longer / stronger intervention), a within-subject design, or a different outcome — not a smaller n claim.
- **Variants** — a zero is only informative if the variant's own terms appear in the records; otherwise it is "not assessable".
- **Feasibility** — each row has its rule. Overall colour = the worst row. Do not average.

## Python

```python
from sportsci_topic.pipeline import run
r = run("brief.toml", ["cnki.csv", "pubmed.ris"], lang="zh")
r.assessment["overall"], r.evidence.direct_recent, r.plan.mdes_at_accessible, r.choice.design
open("topic_card.md", "w", encoding="utf-8").write(r.card)
```

## Pitfalls

- CNKI exports are often GBK/ANSI; the reader tries UTF-8 then GB18030. Headers like `Title-题名`, `Year-年`, `Summary-摘要` are recognised.
- A Chinese-only vocabulary matches nothing in PubMed records and vice versa — give both languages for every facet.
- `accessible_n` is people you can really enrol (before dropout). Do not enter the class size if only a third will volunteer.
- Multi-time-point mixed models have no closed-form power: the tool uses ANCOVA at the final time point (usually conservative) and says so.
- `ethics = "not_needed"` is a claim to confirm in writing with the department, not a default.
- The tool never says a topic is *good*; it says whether it is crowded, possible and affordable.

## Files

| Path | Purpose |
|---|---|
| `sportsci_topic/brief.py` | brief form, validation, template |
| `sportsci_topic/designmap.py` | question type → design rule table (what it permits / forbids) |
| `sportsci_topic/records.py` | CSV (CNKI/WoS/PubMed), RIS, JSON, TXT readers; de-duplication |
| `sportsci_topic/evidence.py` | facet matching, overlap counts, tiers, record-set gap statements |
| `sportsci_topic/power.py` | exact power (noncentral t/F), n, MDES, dropout, survey rules of thumb |
| `sportsci_topic/variants.py` | one-axis (and two-axis) variant recount |
| `sportsci_topic/feasibility.py` | the rubric: sample, time, measures, ethics, analysis, design, overlap |
| `sportsci_topic/card.py` | topic card (zh / en) and `design.json` draft |
| `reference/METHOD.md` | every threshold and rule, with the reason |
| `reference/BRIEF_FIELDS.md` | every brief field |
| `examples/` | demo brief, 30 *synthetic* records, generated output |
