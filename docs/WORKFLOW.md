# The workflow, step by step

Each step writes new files. The "check" column is what must be true before the next step starts.

| Step | You bring | The skill produces | Check before moving on |
|---|---|---|---|
| **1 Topic** `sportsci-topic` | an idea, constraints (people, weeks, equipment, ethics), records exported from CNKI / PubMed / Zotero | `topic_card.md`, `design_draft.json`, `topic_data.json` | no red row you cannot explain; effect size has a source; the one sentence on how your study differs is written by you |
| **2 Data** `sportsci-figures` | `design.json` (start from the draft), the data file | `analysis.json`, figures (png + pdf), `tables.xlsx`, `results.docx`, `methods_explained.md` | `check-design` passes; open every figure; `simulated: false` only for real data |
| **3 Writing** `sportsci-writing` | your draft (Chinese or English), `analysis.json` for the numbers | revised text, `ai_trace_check.py` report | every number traceable to `analysis.json`; no invented citation; the checker's hits are fixed or consciously kept |
| **4 References** `sportsci-refs` | the Word file, the reference list, a Zotero collection | `*_Zotero.docx`, `verify` report, `compare` report | every `verify` count is 0; only `word/document.xml` changed; then Word → Zotero → Refresh |

## What passes between steps

```
brief.toml ─┐
records     ├─ topic_card.md
            └─ design_draft.json ──► design.json ──┐
                                      data.csv ────┴─► results.docx · figures · analysis.json
                                                                         │
                                       your own text ◄───────────────────┘ (numbers come from analysis.json)
                                            │
                                            ▼
                                  draft.docx ──► *_Zotero.docx  (live citation fields)
```

## Rules that hold across all four

1. Never invent data, references, effect sizes or results; ask, or say what is missing.
2. Fix the primary outcome before the data are seen.
3. Write a new file, verify it, keep the original.
4. Say which analyses are exploratory and which numbers are illustrative.
5. A heat map or a "gap" is a description of what you have, not a conclusion about the field.

## Using one skill alone

All four work on their own. The only soft dependencies: `sportsci-topic --fetch` uses `sportsci-refs search`, and the topic card's
`design_draft.json` is validated by `sportsci-figures check-design`.
