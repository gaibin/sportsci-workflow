"""Command line for sportsci-refs.

    status      is Zotero running and reachable (and which settings are configured)
    search      candidate literature from Crossref + Europe PMC + OpenAlex -> markdown for human screening
    check-doi   verify every DOI on Crossref and compare titles
    parse       typed GB/T 7714 reference list -> RIS + CSL-JSON (import into Zotero)
    format      CSL-JSON / RIS -> GB/T 7714-2015 numeric list (when Zotero is not used)
    match       reference list <-> items of a Zotero collection
    fieldify    plain "[n]" citations in a .docx -> live Zotero citation fields + bibliography field
    verify      machine check of the Zotero fields of a .docx (every count must be 0)
    compare     after an edit: only word/document.xml may change; field sequence intact
    edit        field-safe text replacement in a .docx that already has Zotero fields
    renumber    set displayed citation numbers to the order of first appearance
    frames      page-by-page check of a bordered text frame in an exported PDF
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

app = typer.Typer(help="sportsci-refs: literature search, DOI verification, GB/T 7714 and live Zotero citation fields in Word.", no_args_is_help=True)
console = Console()


def _cfg():
    from .config import load_config
    return load_config()


def _read_refs(path: str):
    """Load references from .ris, CSL .json, or a plain GB/T 7714 list (.txt / .md)."""
    from .ris import parse_gbt_list, parse_ris
    p = Path(path)
    txt = p.read_text(encoding="utf-8-sig")
    if p.suffix.lower() == ".ris":
        return parse_ris(txt)
    if p.suffix.lower() == ".json":
        d = json.loads(txt)
        return d if isinstance(d, list) else d.get("items", [])
    return parse_gbt_list(txt)


@app.command()
def status():
    """Is Zotero running and its local API reachable? Shows which settings are configured."""
    from .zotero import ZoteroLocal
    cfg = _cfg()
    st = ZoteroLocal(cfg).status()
    console.print(("[green]" if st["running"] else "[red]") + st["message"] + "[/]")
    console.print(f"local API: {cfg.zotero_api} | user ID: {cfg.zotero_user_id or '[yellow]not set[/yellow]'} | data dir: {cfg.zotero_data_dir or '[yellow]not set[/yellow]'}"
                  f" | contact e-mail: {'set' if cfg.contact_email else 'not set'}")


@app.command()
def search(query: str, n: int = typer.Option(15, "--n", help="Results per source"), year_from: int = typer.Option(0, "--year-from"),
           src: str = typer.Option("crossref,europepmc,openalex", "--src"), out: str = typer.Option("lit_candidates.md", "--out", "-o")):
    """Candidate search (Crossref + Europe PMC + OpenAlex) -> markdown list for human screening."""
    from .search import search as run_search, write_candidates
    res = run_search(query, [s.strip() for s in src.split(",")], n, year_from)
    p = write_candidates(res, out)
    console.print(f"{res['n_raw']} raw -> {len(res['dropped'])} removed -> [bold]{len(res['records'])}[/bold] candidates -> {p}")
    for s, e in res["errors"].items():
        console.print(f"[yellow]{s} failed: {e}[/yellow]")


@app.command("check-doi")
def check_doi(path: str = typer.Argument(..., help=".ris / CSL .json / GB/T list .txt, or a text file with one DOI per line"),
              out: str = typer.Option("doi_check.md", "--out", "-o")):
    """Verify every DOI on Crossref and compare titles (OK / EXISTS / MISMATCH / 404 / NODOI)."""
    from collections import Counter
    from .doi import check_dois, report_md
    lines = [x.strip() for x in Path(path).read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    if lines and all(x.lower().startswith("10.") for x in lines):
        refs = [dict(num=i + 1, doi=x, title="") for i, x in enumerate(lines)]
    else:
        refs = [dict(num=r.get("id") or i + 1, doi=r.get("DOI", ""), title=r.get("title", "")) for i, r in enumerate(_read_refs(path))]
    res = check_dois(refs)
    Path(out).write_text(report_md(res), encoding="utf-8")
    console.print(dict(Counter(r["status"] for r in res)), f"-> {out}")


@app.command()
def parse(path: str = typer.Argument(..., help="Plain GB/T 7714 reference list (.txt)"), out: str = typer.Option("references", "--out", "-o", help="Output stem")):
    """GB/T 7714 text list -> RIS + CSL-JSON (Zotero: File -> Import). Lists entries the parser was unsure about."""
    from .ris import parse_gbt_list, to_csl, to_ris
    recs = parse_gbt_list(Path(path).read_text(encoding="utf-8-sig"))
    Path(out + ".ris").write_text(to_ris(recs), encoding="utf-8")
    Path(out + ".json").write_text(json.dumps(to_csl(recs), ensure_ascii=False, indent=1), encoding="utf-8")
    warn = [r for r in recs if r["_warnings"]]
    console.print(f"{len(recs)} entries -> {out}.ris, {out}.json; [yellow]{len(warn)} need a manual look[/yellow]")
    for r in warn:
        console.print(f"  [{r['id']}] {'; '.join(r['_warnings'])}: {r['_raw'][:70]}", markup=False)


@app.command("format")
def format_cmd(path: str = typer.Argument(..., help=".ris or CSL .json"), out: Optional[str] = typer.Option(None, "--out", "-o"),
               upper: bool = typer.Option(False, "--upper-surname", help="Western surnames in capitals (some schools require it)")):
    """Render a GB/T 7714-2015 numeric reference list (when Zotero is not used)."""
    from .gbt7714 import format_list
    lines = format_list(_read_refs(path), upper_surname=upper)
    if out:
        Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
        console.print(f"{len(lines)} entries -> {out}")
    else:
        for x in lines:
            console.print(x, markup=False, highlight=False)


@app.command()
def match(path: str = typer.Argument(..., help="The document's reference list (.txt GB/T / .ris / .json)"),
          collection: str = typer.Option(..., "--collection", "-c", help="Zotero collection name or key"),
          out: str = typer.Option("zotero_match.json", "--out", "-o")):
    """Match the reference list to a Zotero collection (DOI, then title >= 0.90) and pull CSL for every match."""
    from .zotero import ZoteroLocal, match as run_match
    z = ZoteroLocal(_cfg())
    refs = _read_refs(path)
    m = run_match(refs, z.collection_items(collection))
    ids = z.item_ids([v["key"] for v in m["mapping"].values()])
    for v in m["mapping"].values():
        v["csl"] = z.csl(v["key"])
        if v["key"] in ids:
            v["itemID"] = ids[v["key"]]
    Path(out).write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    console.print(f"matched {len(m['mapping'])}/{len(refs)}; unmatched {m['unmatched']}; review (title < 0.97) {m['review']}; "
                  f"collection items not used {len(m['unused'])} -> {out}")


@app.command()
def fieldify(docx: str, match_file: str = typer.Option("zotero_match.json", "--match", "-m"), out: Optional[str] = typer.Option(None, "--out", "-o"),
             superscript: bool = typer.Option(False, "--superscript", help="Make citation display superscript"), dry_run: bool = typer.Option(False, "--dry-run")):
    r"""Plain \[n] citations -> live Zotero fields (+ one bibliography field). Writes a NEW file; verify it afterwards."""
    from .docx_fields import fieldify as run_fieldify
    cfg = _cfg()
    if not cfg.zotero_user_id:
        console.print("[red]ZOTERO_USER_ID not set (config/local.toml or env) — needed for the citation URIs.[/red]")
        raise typer.Exit(1)
    items = {int(k): v for k, v in json.loads(Path(match_file).read_text(encoding="utf-8"))["mapping"].items()}
    dst = out or str(Path(docx).with_name(Path(docx).stem + "_Zotero.docx"))
    rep = run_fieldify(docx, dst, items, cfg.zotero_user_id, superscript=superscript, dry_run=dry_run)
    console.print(f"converted {rep['converted']} citations; bibliography entries {rep['bib_entries']}; missing numbers {rep['missing']}")
    for t in rep["not_converted"]:
        console.print(f"[yellow]not converted (split runs / unknown number): {t}[/yellow]", markup=True)
    if not dry_run:
        console.print(f"-> {dst}\nNext: open in Word -> Zotero -> Document Preferences (pick the style) -> Refresh; then `sportsci-refs verify`.")


@app.command()
def verify(docx: str, out: Optional[str] = typer.Option(None, "--out", "-o", help="Write the markdown report here")):
    """Machine check of Zotero fields: structure, payloads, numbering order, punctuation, bibliography. All counts must be 0."""
    from .docx_fields import verify as run_verify, verify_md
    rep = run_verify(docx)
    if out:
        Path(out).write_text(verify_md(rep), encoding="utf-8")
    bad = {k: v for k, v in rep["summary"].items() if v}
    console.print(("[green]all checks passed[/green]" if rep["ok"] else f"[red]problems: {bad}[/red]") +
                  f"  ({rep['n_citation_fields']} citation fields, {rep['n_items_cited']} items, {rep['n_bib_entries']} bibliography entries)")
    if not rep["ok"]:
        raise typer.Exit(1)


@app.command()
def compare(before: str, after: str):
    """After an edit: only word/document.xml may change, and the field sequence must be intact."""
    from .docx_fields import compare_parts, field_diff
    cp, fd = compare_parts(before, after), field_diff(before, after)
    console.print(f"parts changed: {cp['changed']}; missing {cp['missing_in_new']}; added {cp['added_in_new']}")
    console.print(f"fields before {fd['counts_before']}\nfields after  {fd['counts_after']}\nfield sequence identical: {fd['identical']}"
                  + ("" if fd["identical"] else f" (first difference at field #{fd['first_difference']})"))


@app.command()
def edit(docx: str, replace: List[str] = typer.Option(..., "--replace", "-r", help='"old=>new"; repeat for several edits'),
         out: Optional[str] = typer.Option(None, "--out", "-o"), count: Optional[int] = typer.Option(None, "--count", help="Max replacements per rule (default: all)")):
    """Field-safe text replacement: only plain text outside fields changes; citations and the bibliography are never touched."""
    from .docx_fields import verify as run_verify
    from .fieldedit import FieldDoc
    doc = FieldDoc(docx)
    for rule in replace:
        if "=>" not in rule:
            console.print(f"[red]rule must look like old=>new: {rule!r}[/red]")
            raise typer.Exit(1)
        old, new = rule.split("=>", 1)
        n = doc.replace(old, new, count)
        console.print(f"{n} x  {old!r} -> {new!r}" + ("" if n else "  [yellow](not found in plain text)[/yellow]"))
    dst = out or str(Path(docx).with_name(Path(docx).stem + "_edited.docx"))
    doc.save(dst)
    rep = run_verify(dst)
    console.print(f"-> {dst}  | verify: " + ("[green]ok[/green]" if rep["ok"] else f"[yellow]{ {k: v for k, v in rep['summary'].items() if v} }[/yellow]"))


@app.command()
def renumber(docx: str, out: Optional[str] = typer.Option(None, "--out", "-o")):
    """Set the displayed citation numbers (and payloads) to the order of first appearance. The bibliography is left to Zotero -> Refresh."""
    from .fieldedit import FieldDoc
    doc = FieldDoc(docx)
    rep = doc.refresh_numbers()
    dst = out or str(Path(docx).with_name(Path(docx).stem + "_renumbered.docx"))
    doc.save(dst)
    console.print(f"{len(rep['changed'])} citations renumbered, {rep['unchanged']} already right, {len(rep['skipped'])} skipped -> {dst}")
    for c in rep["changed"][:15]:
        console.print(f"  paragraph {c['paragraph']}: {c['before']} -> {c['after']}", markup=False)
    if rep["changed"]:
        console.print("The bibliography order is NOT changed here: open the file in Word and press Zotero -> Refresh.")


@app.command()
def frames(pdf: str, bottom_margin: float = typer.Option(72.0, "--bottom-margin", help="Bottom page margin in points"),
           gap: float = typer.Option(60.0, "--gap", help="Gap above which a middle page is flagged (points)")):
    """Page-by-page check of a bordered text frame in an exported PDF (needs `pip install pymupdf`)."""
    from .pdf_frames import scan
    res = scan(pdf, bottom_margin, gap)
    for p in res["pages"]:
        console.print(f"page {p['page']:>3}  frame bottom {p['frame_bottom']}  gap {p['gap_to_body_bottom']}" + ("  <-- gap" if p["flag"] else ""), markup=False)
    console.print(f"pages with a premature frame end: {res['pages_with_gap'] or 'none'}")


if __name__ == "__main__":
    app()
