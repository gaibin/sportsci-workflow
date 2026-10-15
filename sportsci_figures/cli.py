"""Command line for sportsci-figures.

    intake        raw data file -> de-identified copy, data-quality report, draft design.json
    new-design    write a design-spec template
    check-design  validate a spec (and that the data run through the analysis)
    results       spec + data -> figures, tables, Results .docx/.md, methods explanation (zh / en)
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

app = typer.Typer(help="sportsci-figures: publication-grade figures, three-line tables and Results documents (Chinese / English) from a design spec + data.",
                  no_args_is_help=True)
console = Console()


def _templates_dir() -> Path:
    """Packaged templates (wheel install) or the repository's config folder (skill / source checkout)."""
    here = Path(__file__).resolve().parent
    for cand in (here / "templates", here.parent / "config" / "design_templates"):
        if cand.is_dir():
            return cand
    raise FileNotFoundError("design templates not found")


@app.command()
def intake(data: str, out: str = typer.Option("intake", "--out", "-o", help="Output folder (keep raw data outside any shared repository)"),
           sheet: Optional[str] = typer.Option(None, "--sheet", help="Excel sheet name (default: first)")):
    """Data check of a raw file: de-identify, profile, detect the design, write intake_report.md + design_draft.json."""
    from .intake import run_intake
    r = run_intake(data, out, sheet)
    console.print(f"[green]Design guess:[/green] {r['layout'].get('design')}  (format {r['layout'].get('format')})")
    if r["removed"]:
        console.print(f"[yellow]Removed identifying columns:[/yellow] {', '.join(r['removed'])}  (ID map in {Path(out) / '_private'} — keep it private)")
    console.print(f"[bold]{len(r['todo'])} open questions[/bold] to confirm before analysis -> {r['report']}")


@app.command("new-design")
def new_design(type: str = typer.Option("parallel_prepost", "--type", "-t", help="parallel_prepost | crossover | multitime | meta | single_group | survey"),
               out: str = typer.Option("design.json", "--out", "-o", help="Where to write the design-spec template")):
    """Write a design-spec template (edit it before running results)."""
    from .results import DESIGNS
    if type not in DESIGNS:
        console.print(f"[red]type must be one of {DESIGNS}[/red]")
        raise typer.Exit(1)
    shutil.copy(_templates_dir() / f"{type}.json", out)
    console.print(f"[green]Template written to {out}[/green] (field reference: reference/DESIGN_SPEC.md)")


@app.command("check-design")
def check_design(spec: str, data: Optional[str] = typer.Option(None, "--data", "-d", help="Optional data file: also runs the analysis on it")):
    """Validate a design spec (and, if given, that the data file runs through the analysis)."""
    from .results import SpecError, analyze, load_data, load_spec
    try:
        sp = load_spec(spec)
        if data:
            analyze(load_data(data), sp)
    except (SpecError, KeyError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    console.print("[green]Design spec OK[/green]" + (" and the data run through the analysis." if data else "."))


@app.command("results")
def results(spec: str = typer.Argument(..., help="Design spec json"),
            data: Optional[str] = typer.Option(None, "--data", "-d", help="Data file (csv / xlsx)"),
            out: str = typer.Option("results_out", "--out", "-o", help="Output folder"),
            lang: str = typer.Option("both", "--lang", "-l", help="zh | en | both"),
            chapter: Optional[int] = typer.Option(None, "--chapter", help="Degree-thesis layout, numbered by chapter (图 4-1 / Figure 4.1)"),
            simulate: bool = typer.Option(False, "--simulate", help="Rehearse with data generated from the spec's 'simulate' block (tagged simulated)")):
    """Design spec + data -> analysis, figures, tables, Results text, .docx and methods_explained.md."""
    from .results import run_results
    r = run_results(spec, data, out, lang=lang, simulate_data=simulate, thesis_chapter=chapter)
    for lg, paths in r["outputs"].items():
        console.print(f"[bold]{lg}[/bold]: " + ", ".join(str(p) for p in paths.values()))


if __name__ == "__main__":
    app()
