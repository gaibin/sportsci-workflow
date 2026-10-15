---
name: sportsci-refs
description: Reference management for Word documents (theses, proposals, papers) with Zotero. Searches literature (Crossref, Europe PMC, OpenAlex), verifies DOIs against Crossref, parses a typed GB/T 7714 list to RIS / CSL-JSON, matches it to a Zotero collection, turns plain "[n]" citations into live Zotero citation fields, edits and renumbers a document that already has fields without breaking them, and machine-verifies the result. Use for 参考文献, 引文, Zotero, 引文域, GB/T 7714, 文献表, 引用编号乱了, 检查引文, DOI 核验, 让 Zotero 管理这篇的参考文献, or "make the citations in this docx refresh automatically".
---

# sportsci-refs

One pipeline from "a draft with typed `[n]` citations" to "citations Zotero can refresh, a self-consistent bibliography, and a document
that still opens". Every step has a command and a check; nothing here is "be careful".

## First use (once)

The commands in this skill come from a Python package that ships in this folder. Before the first command, check it is installed:

```bash
sportsci-refs --help
```

If the shell says the command is not found, install it from this skill's folder (Python 3.10+):

```bash
python -m pip install -e <path to this skill folder>
```

From a source checkout, `python cli.py <command>` in this folder works once the dependencies are installed. Do this check once per machine, not before every command.

## Iron rules

1. **Never invent.** Authors, years, volume/pages, DOIs: if it is missing, ask the author or read the paper. A candidate list is not a reference list.
2. **Fields first.** In a paragraph with citation fields, edit only runs outside fields. Never rewrite or delete a paragraph that holds field markers.
3. **Back up, write a NEW file, verify.** Every command writes a new file and refuses to overwrite the source. After any write run `verify`; every count must be 0.

## Pipeline

| # | Goal | Command | Check |
|---|---|---|---|
| 0 | Is Zotero reachable? | `sportsci-refs status` | a 502 comes from a local proxy: Zotero is simply not running |
| 1 | Candidate literature | `sportsci-refs search "<keywords>" --n 15 --year-from 2015 -o candidates.md` | candidates only; the author reads and decides |
| 2 | Verify DOIs | `sportsci-refs check-doi list.txt -o doi.md` | `MISMATCH` = real DOI on the wrong paper; `EXISTS` = no title to compare; `NODOI` → check CNKI / Wanfang by hand |
| 3 | Typed list → Zotero | `sportsci-refs parse refs.txt -o refs` → import `refs.ris` in Zotero | entries the parser was unsure about are listed |
| 4 | List ↔ collection | `sportsci-refs match refs.txt -c "<collection>" -o zotero_match.json` | title matches below 0.97 go to manual review |
| 5 | `[n]` → live fields | `sportsci-refs fieldify thesis.docx -m zotero_match.json --superscript --dry-run`, then without `--dry-run` | split-run citations are reported, not touched |
| 6 | Word: style + Refresh | Zotero → Document Preferences → choose the required style → Refresh | rebuilds numbers, bibliography, tab characters |
| 7 | Edit text later | `sportsci-refs edit thesis.docx -r "old=>new" -o v2.docx` | only plain text outside fields changes |
| 8 | Numbers out of order | `sportsci-refs renumber v2.docx -o v3.docx`, then Word → Refresh | bibliography is reordered by Zotero, not by the tool |
| 9 | Verify before delivery | `sportsci-refs verify v3.docx -o report.md` and `sportsci-refs compare old.docx v3.docx` | all counts 0; only `word/document.xml` changed |
| – | No Zotero | `sportsci-refs format refs.ris` | GB/T 7714-2015 numeric list from CSL / RIS |
| – | Framed templates | `sportsci-refs frames thesis.pdf` | pages where the frame ends early |

Settings (Zotero user ID, data folder, e-mail) go in `config/local.toml` or environment variables — copy `config/local.example.toml`; never put
them in code or commit them. Full playbook with every pitfall: `reference/ZOTERO_PLAYBOOK.md`.

## What `verify` checks (all must be 0)

field markers balanced · payload JSON valid · citationID unique · display = payload · numbers = order of first appearance ·
citation before sentence-final punctuation · no two adjacent fields without text · bibliography numbered 1..N with a tab after each number ·
bibliography entry matches the cited title · cited-but-not-listed / listed-but-not-cited.
A freshly `fieldify`-ed file that Zotero has not refreshed yet will report missing tabs and title mismatches: expected until step 6.
**Checkers lie too**: en dash vs hyphen, `instrText` split over runs, RTF-encoded dashes in `formattedCitation`. Before reporting "N problems",
open the first one by hand.

## Python

```python
from sportsci_refs import parse_gbt_list, format_list, to_ris
from sportsci_refs.docx_fields import fieldify, verify
from sportsci_refs.fieldedit import FieldDoc

doc = FieldDoc("thesis_zotero.docx")
doc.replace("下降趋势", "降低趋势")                               # plain text only
i, grp = doc.citations()[0]
from sportsci_refs.fieldedit import detach
els = detach(grp)
ok, msg = doc.insert_before_anchor(j, "。", els)                # move a citation in front of the full stop; refuses ambiguous anchors
doc.refresh_numbers()
doc.save("thesis_v2.docx")                                      # refuses to overwrite, refuses to drop fields
```

## Pitfalls

- A Zotero field is 5+ runs; a 70-run paragraph often has only 25 plain-text runs. "Delete all runs and append one" silently destroys citations.
- Never serialise `document.xml` through a parser that moves inline namespace declarations (`xmlns:a` on pictures): Word reports a corrupt file.
  `fieldify` splices strings; `fieldedit` uses lxml which keeps declarations; all other package parts are copied byte for byte.
- Press Refresh only when the Zotero library is complete: missing items become `[?]` and numbering shifts. Sync before switching machines.
- Never write test items to a real library (the local API cannot delete: 501) and never touch `zotero.sqlite` directly; item IDs are read from a copy.
- Word re-saves change the package silently; re-check `docProps/custom.xml` (holds the Zotero style) and the field counts afterwards.
- A reference "verified" by DOI only exists with matching metadata; whether it supports the sentence is the author's job.

## Files

| Path | Purpose |
|---|---|
| `sportsci_refs/search.py`, `doi.py` | candidate search, DOI verification |
| `sportsci_refs/ris.py`, `gbt7714.py` | GB/T 7714 text ↔ CSL-JSON ↔ RIS; GB/T 7714-2015 formatter |
| `sportsci_refs/zotero.py`, `net.py`, `config.py` | local Zotero API (proxy-safe), item IDs from a database copy, settings |
| `sportsci_refs/docx_fields.py` | `fieldify`, `verify`, `compare_parts`, `field_diff`, `diagnose` |
| `sportsci_refs/fieldedit.py` | field-safe edits: replace, move, renumber (`FieldDoc`) |
| `sportsci_refs/pdf_frames.py` | page-by-page frame check |
| `reference/ZOTERO_PLAYBOOK.md` | full playbook (Chinese): environment, stages, pitfalls, delivery, framed templates |
| `tests/` | offline tests (no network, no running Zotero) |
