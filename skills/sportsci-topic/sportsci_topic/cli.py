"""Command line: sportsci-topic new | check | evidence | power | variants | card."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .brief import BriefError, load_brief, validate, write_template
from .card import LIGHT, VERDICT, write_outputs
from .designmap import choose_design
from . import power as pw
from .pipeline import run, search_queries

app = typer.Typer(add_completion=False, no_args_is_help=True,
                  help="sportsci-topic: choose a sport-science topic with evidence, a design, a sample size and a feasibility check.")
console = Console()
RECORDS = typer.Option(None, "--records", "-r", help="Records exported from CNKI / PubMed / Zotero (.csv .ris .json .txt); repeatable")


def _die(msg: str) -> None:
    console.print(f"[red]{msg}[/red]")
    raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def _root(version: bool = typer.Option(False, "--version", help="Show the version and exit")):
    if version:
        console.print(__version__)
        raise typer.Exit()


@app.command()
def new(out: Path = typer.Option("brief.toml", "--out", "-o", help="Where to write the commented brief template")):
    """Write a commented brief.toml to fill in."""
    if out.exists():
        _die(f"{out} exists; refusing to overwrite")
    write_template(out)
    console.print(f"wrote {out}  — fill it in, then: sportsci-topic check {out}")


@app.command()
def check(brief: Path):
    """Validate the brief and show the design it maps to."""
    try:
        b = load_brief(brief)
    except BriefError as e:
        _die(str(e))
    errs, warns = validate(b)
    for w in warns:
        console.print(f"[yellow]warning[/yellow] {w}")
    for e in errs:
        console.print(f"[red]error[/red]   {e}")
    if errs:
        raise typer.Exit(1)
    ch = choose_design(b, b.language)
    console.print(f"[green]ok[/green]  design = [bold]{ch.design}[/bold] — {ch.rule}")
    console.print(f"    queries: {' | '.join(search_queries(b))}")


@app.command()
def evidence(brief: Path, records: Optional[List[Path]] = RECORDS,
             fetch: bool = typer.Option(False, "--fetch", help="Also search via sportsci-refs (Crossref / Europe PMC / OpenAlex)"),
             n: int = typer.Option(25, "--n", help="Records per query when fetching"),
             year_from: int = typer.Option(0, "--year-from"),
             this_year: Optional[int] = typer.Option(None, "--this-year", help="Reference year for the 5-year window (default: today)"),
             lang: Optional[str] = typer.Option(None, "--lang"),
             out: Optional[Path] = typer.Option(None, "--out", "-o", help="Write evidence.json here")):
    """Evidence map: overlap counts, nearest studies, statements about the record set."""
    try:
        r = run(brief, records or [], fetch=fetch, fetch_n=n, year_from=year_from, this_year=this_year, lang=lang)
    except (BriefError, ValueError, RuntimeError) as e:
        _die(str(e))
    ev = r.evidence
    if ev is None:
        _die("no records: pass --records <file> or --fetch")
    t = Table(title=f"{ev.n_records} records · window {ev.window[0]}–{ev.window[1]} · coverage {ev.coverage}")
    for c in ("combination", "all years", "recent"):
        t.add_column(c)
    for k, v in ev.combos_all.items():
        t.add_row(k, str(v), str(ev.combos_recent.get(k, 0)))
    console.print(t)
    console.print(f"overlap: [bold]{ev.tier}[/bold] (direct, recent = {ev.direct_recent})")
    for g in ev.gaps:
        console.print(f"  • {g['text']}")
    if out:
        out.write_text(json.dumps(ev.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        console.print(f"wrote {out}")


@app.command()
def power(test: str = typer.Argument(..., help="two-sample | paired | ancova | correlation | anova | regression"),
          effect: Optional[float] = typer.Option(None, "--effect", "-e", help="d (two-sample), dz (paired), r (correlation), f (anova), f2 (regression)"),
          n: Optional[int] = typer.Option(None, "--n", help="Participants per group (total for paired/correlation/anova/regression): report power and MDES instead"),
          delta: Optional[float] = typer.Option(None, "--delta", help="ancova: raw between-group difference"),
          sd: Optional[float] = typer.Option(None, "--sd", help="ancova: outcome SD"),
          r_prepost: Optional[float] = typer.Option(None, "--r-prepost", help="ancova: pre-post correlation"),
          k: int = typer.Option(3, "--k", help="anova: number of groups"),
          predictors: int = typer.Option(3, "--predictors", help="regression: number of predictors"),
          alpha: float = typer.Option(0.05, "--alpha"), power_: float = typer.Option(0.80, "--power"),
          dropout: float = typer.Option(0.0, "--dropout", help="inflate the required n for expected loss"),
          ratio: float = typer.Option(1.0, "--ratio", help="two-sample: n2 / n1")):
    """Exact sample size (or power, or smallest detectable effect) for one test."""
    if test == "ancova":
        if not (delta and sd and r_prepost is not None) and effect is None:
            _die("ancova needs --delta --sd --r-prepost (or --effect as the adjusted d)")
        eff = effect if effect is not None else delta / (sd * (1 - r_prepost ** 2) ** 0.5)
        cov = 1
        test_fn = "two-sample"
    else:
        eff, cov, test_fn = effect, 0, test
    if n is None:
        if eff is None:
            _die("--effect is required unless --n is given")
        if test_fn == "two-sample":
            n1 = pw.n_two_sample(eff, alpha, power_, ratio, covariates=cov)
            msg = f"d = {eff:.3f}: n1 = {n1}, n2 = {int(-(-ratio * n1 // 1))}; enrol {pw.inflate(n1, dropout)} per arm at {dropout:.0%} dropout"
        elif test_fn == "paired":
            n1 = pw.n_paired(eff, alpha, power_)
            msg = f"dz = {eff:.3f}: n = {n1}; enrol {pw.inflate(n1, dropout)} at {dropout:.0%} dropout"
        elif test_fn == "correlation":
            n1 = pw.n_correlation(eff, alpha, power_)
            msg = f"r = {eff:.3f}: n = {n1}; enrol {pw.inflate(n1, dropout)} at {dropout:.0%} dropout"
        elif test_fn == "anova":
            n1 = pw.n_anova(eff, k, alpha, power_)
            msg = f"f = {eff:.3f}, k = {k}: N = {n1} (≈ {-(-n1 // k)} per group)"
        elif test_fn == "regression":
            n1 = pw.n_regression(eff, predictors, None, alpha, power_)
            msg = f"f² = {eff:.3f}, {predictors} predictors: N = {n1}"
        else:
            _die(f"unknown test {test!r}")
        console.print(msg + f"  [dim](α = {alpha}, power = {power_})[/dim]")
        return
    if test_fn == "two-sample":
        mdes = pw.mdes_two_sample(n, n, alpha, power_, cov)
        line = f"n = {n} per group: smallest detectable d = {mdes:.3f} at {power_:.0%} power"
        if eff is not None:
            line += f"; power for d = {eff:.2f}: {pw.power_two_sample(eff, n, n, alpha, True, cov):.3f}"
    elif test_fn == "paired":
        line = f"n = {n}: smallest detectable dz = {pw.mdes_paired(n, alpha, power_):.3f}"
        if eff is not None:
            line += f"; power for dz = {eff:.2f}: {pw.power_paired(eff, n, alpha):.3f}"
    elif test_fn == "correlation":
        line = f"n = {n}: smallest detectable r = {pw.mdes_correlation(n, alpha, power_):.3f}"
        if eff is not None:
            line += f"; power for r = {eff:.2f}: {pw.power_correlation(eff, n, alpha):.3f}"
    elif test_fn == "anova" and eff is not None:
        line = f"N = {n}, k = {k}: power for f = {eff:.2f}: {pw.power_anova(eff, n, k, alpha):.3f}"
    elif test_fn == "regression" and eff is not None:
        line = f"N = {n}, {predictors} predictors: power for f² = {eff:.2f}: {pw.power_regression(eff, n, predictors, None, alpha):.3f}"
    else:
        _die("give --effect for anova / regression power")
    console.print(line)


@app.command()
def variants(brief: Path, records: Optional[List[Path]] = RECORDS,
             this_year: Optional[int] = typer.Option(None, "--this-year"),
             two_axis: bool = typer.Option(False, "--two-axis", help="Also combine variants from two different axes"),
             lang: Optional[str] = typer.Option(None, "--lang")):
    """Variant matrix: overlap recounted with one axis changed at a time."""
    try:
        r = run(brief, records or [], this_year=this_year, lang=lang, two_axis=two_axis)
    except (BriefError, ValueError) as e:
        _die(str(e))
    if not r.variants:
        _die("need --records and at least one [[variants.<axis>]] in the brief")
    t = Table()
    for c in ("variant", "recent", "all", "vs base", "assessable"):
        t.add_column(c)
    for v in r.variants:
        t.add_row(v.name(), str(v.direct_recent), str(v.direct_all), "—" if not v.axes else f"{v.delta_recent:+d}", "yes" if v.assessable else "no")
    console.print(t)


@app.command()
def card(brief: Path, records: Optional[List[Path]] = RECORDS,
         out: Path = typer.Option("topic_out", "--out", "-o", help="Output folder"),
         fetch: bool = typer.Option(False, "--fetch"), n: int = typer.Option(25, "--n"),
         year_from: int = typer.Option(0, "--year-from"),
         this_year: Optional[int] = typer.Option(None, "--this-year"),
         two_axis: bool = typer.Option(False, "--two-axis"),
         lang: Optional[str] = typer.Option(None, "--lang", help="zh | en (default: the brief's language)")):
    """Everything: topic_card.md + design_draft.json + topic_data.json."""
    try:
        r = run(brief, records or [], fetch=fetch, fetch_n=n, year_from=year_from, this_year=this_year, lang=lang, two_axis=two_axis)
    except (BriefError, ValueError, RuntimeError) as e:
        _die(str(e))
    paths = write_outputs(out, r.card, r.draft, r.evidence, r.plan, r.assessment, r.variants)
    ov = r.assessment["overall"]
    console.print(f"{LIGHT[ov]} {VERDICT[r.lang][ov]}")
    for c in r.assessment["checks"]:
        console.print(f"  {LIGHT[c.status]} {c.title}: {c.detail}")
    for p in paths.values():
        console.print(f"wrote {p}")


if __name__ == "__main__":  # pragma: no cover
    app()
