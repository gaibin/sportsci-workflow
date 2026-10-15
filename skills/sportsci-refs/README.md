# sportsci-refs

**Turn the typed `[12]` citations in a Word thesis into live Zotero fields — then edit, renumber and verify the document without ever breaking them.**

[中文说明](README.zh-CN.md)

![From a draft with typed [n] to citations Zotero can refresh](assets/pipeline_en.png)

Most reference tooling stops at "export a list". The hard part comes after: the Word file already has fields, you must change a sentence,
move a citation, or fix the numbering — and one careless "select the paragraph and retype it" silently destroys every citation in it.
`sportsci-refs` treats the Word citation field as the unit it is, and checks the result with machine tests instead of "looks fine".

- **Search and verify.** Candidate literature from Crossref, Europe PMC and OpenAlex (peer-review records stripped, de-duplicated),
  every DOI resolved on Crossref with a title comparison — a *real* DOI attached to the *wrong* paper is reported as `MISMATCH`.
- **Typed list → Zotero.** Parse a hand-typed GB/T 7714 reference list into RIS / CSL-JSON, import, and match it to a Zotero collection by DOI, then title.
- **`[n]` → live Zotero fields.** Plain-text citations become real `ADDIN ZOTERO_ITEM` fields and the list becomes one bibliography field.
- **Field-safe editing.** Replace text, move a citation in front of the full stop, renumber by first appearance — only plain text outside fields
  changes; the bibliography is recognised as "inside a field" even though its markers sit in other paragraphs.
- **13 machine checks** (`verify`): balanced markers, payload JSON, display = payload, numbering = order of first appearance,
  citation before punctuation, bibliography numbering / tabs / title match, cited-but-not-listed, listed-but-not-cited.
- **GB/T 7714-2015** numeric list generation when Zotero is not used; Chinese and English entries.

## Quick start

```bash
git clone https://github.com/gaibin/sportsci-refs.git
cd sportsci-refs
pip install -e .

sportsci-refs status                                    # Zotero reachable? (needs Zotero 7 running)
sportsci-refs parse refs.txt -o refs                    # typed GB/T 7714 list -> refs.ris + refs.json
sportsci-refs check-doi refs.ris -o doi.md              # OK / EXISTS / MISMATCH / 404 / NODOI
#   Zotero: select a new collection, File -> Import -> refs.ris
sportsci-refs match refs.txt -c "My thesis" -o zotero_match.json
sportsci-refs fieldify thesis.docx -m zotero_match.json --superscript -o thesis_Zotero.docx
#   Word: Zotero -> Document Preferences -> choose the style -> Refresh
sportsci-refs verify thesis_Zotero.docx -o report.md    # every count must be 0
```

Edit later, safely:

```bash
sportsci-refs edit thesis_Zotero.docx -r "下降趋势=>降低趋势" -r "decline=>decrease" -o v2.docx
sportsci-refs renumber v2.docx -o v3.docx               # then Word -> Zotero -> Refresh for the bibliography
sportsci-refs compare thesis_Zotero.docx v3.docx        # only word/document.xml may differ
```

```python
from sportsci_refs.fieldedit import FieldDoc, detach

doc = FieldDoc("thesis_Zotero.docx")
doc.replace("下降趋势", "降低趋势")                         # plain text only
_, group = doc.citations()[0]
ok, msg = doc.insert_before_anchor(paragraph_index, "。", detach(group))   # refuses ambiguous anchors
doc.refresh_numbers()
doc.save("v2.docx")        # refuses to overwrite the source, refuses to write a document whose field counts changed
```

Settings (Zotero user ID, data folder, contact e-mail) live in `config/local.toml` (copy `config/local.example.toml`; git-ignored) or environment variables.

## Why it is built this way

| What goes wrong | Consequence | What this tool does |
|---|---|---|
| A paragraph is rewritten as "delete all runs, append one" | Citations vanish silently — a 70-run paragraph typically has only 25 plain-text runs | Only runs outside fields are edited |
| `document.xml` is round-tripped through a parser that hoists inline namespace declarations | Word: "the file is corrupt" (pictures declare `xmlns:a` inline) | String splice or lxml; every other package part copied byte for byte |
| The bibliography is treated as ordinary text | Edits are overwritten at the next Refresh | Field depth is tracked across the whole document |
| The anchor text occurs twice | The citation lands in the wrong sentence, no error | Anchors must be unique, otherwise the edit is refused |
| A checker says "37 inconsistencies" | You fix 37 non-problems (en dash vs hyphen, split `instrText`, RTF-encoded dashes) | Those false alarms are normalised before comparing |
| `HTTP 502` from `127.0.0.1:23119` | Looks like a broken Zotero; actually a local proxy answering because Zotero is not running | Local calls bypass proxies, external APIs use them; `status` explains it |

Full playbook (Chinese, with Word COM checks and framed-template notes): [`reference/ZOTERO_PLAYBOOK.md`](reference/ZOTERO_PLAYBOOK.md).

## Use it as an AI agent skill

`SKILL.md` gives an agent the pipeline, the iron rules and the checks. Clone into your skills folder:

```bash
git clone https://github.com/gaibin/sportsci-refs.git ~/.claude/skills/sportsci-refs
pip install -e ~/.claude/skills/sportsci-refs
```

## Scope and limits

- Windows Word and Zotero 7 desktop are the tested environment; the document editing itself is plain OOXML and needs no Word.
- Zotero's local API is read-mostly (search, CSL, collections); it cannot delete or modify items — do deletions in the Zotero UI.
- The bibliography is reordered and re-tabbed by **Zotero → Refresh in Word**, not by this tool.
- DOI verification shows that a paper exists with matching metadata, **not** that it supports the sentence it is cited for.
- Citations that Word split across runs (`[`, `12`, `]`) are reported, not converted.

## Development

```bash
pip install -e ".[dev]"
python -m pytest -q          # offline: no network, no running Zotero
```

## License

MIT — see [LICENSE](LICENSE).
