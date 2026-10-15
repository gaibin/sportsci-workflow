# -*- coding: utf-8 -*-
"""Command line, offline: new -> check -> evidence -> variants -> card, and power."""
import json
from pathlib import Path

from typer.testing import CliRunner

from sportsci_topic.cli import app

run = CliRunner().invoke
ROOT = Path(__file__).resolve().parents[1]


def test_new_check_card_chain(tmp_path):
    brief = tmp_path / "brief.toml"
    r = run(app, ["new", "-o", str(brief)])
    assert r.exit_code == 0 and brief.exists()
    assert run(app, ["new", "-o", str(brief)]).exit_code == 1            # never overwrites
    r = run(app, ["check", str(brief)])
    assert r.exit_code == 0 and "parallel_prepost" in r.output
    recs = ROOT / "examples" / "demo_records.csv"
    out = tmp_path / "out"
    r = run(app, ["card", str(brief), "-r", str(recs), "-o", str(out), "--this-year", "2025"])
    assert r.exit_code == 0, r.output
    card = (out / "topic_card.md").read_text(encoding="utf-8")
    assert "## 3." in card and "synthetic example" in card
    draft = json.loads((out / "design_draft.json").read_text(encoding="utf-8"))
    assert draft["design"] == "parallel_prepost" and draft["simulated"] is False
    data = json.loads((out / "topic_data.json").read_text(encoding="utf-8"))
    assert data["overall"] in ("green", "yellow", "red") and data["evidence"]["n_records"] > 0


def test_check_reports_every_error(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text('[topic]\nquestion_type = "effect"\n[pico.population]\nterms = []\n', encoding="utf-8")
    r = run(app, ["check", str(bad)])
    assert r.exit_code == 1 and "pico.population.terms" in r.output and "primary" in r.output


def test_check_rejects_invalid_toml(tmp_path):
    p = tmp_path / "x.toml"
    p.write_text("this is = = not toml", encoding="utf-8")
    r = run(app, ["check", str(p)])
    assert r.exit_code == 1 and "not valid TOML" in r.output


def test_evidence_without_records_is_an_error(tmp_path):
    brief = tmp_path / "b.toml"
    run(app, ["new", "-o", str(brief)])
    r = run(app, ["evidence", str(brief)])
    assert r.exit_code == 1 and "no records" in r.output


def test_power_command_values():
    r = run(app, ["power", "two-sample", "-e", "0.5"])
    assert r.exit_code == 0 and "n1 = 64" in r.output
    r = run(app, ["power", "paired", "-e", "0.5", "--dropout", "0.2"])
    assert "n = 34" in r.output and "enrol 43" in r.output
    r = run(app, ["power", "two-sample", "--n", "20"])
    assert "smallest detectable d" in r.output
    r = run(app, ["power", "ancova", "--delta", "3", "--sd", "5", "--r-prepost", "0.6"])
    assert r.exit_code == 0 and "n1 =" in r.output
    r = run(app, ["power", "two-sample"])
    assert r.exit_code == 1


def test_variants_requires_axis_and_records(tmp_path):
    brief = tmp_path / "b.toml"
    run(app, ["new", "-o", str(brief)])
    recs = ROOT / "examples" / "demo_records.csv"
    r = run(app, ["variants", str(brief), "-r", str(recs), "--this-year", "2025"])
    assert r.exit_code == 0 and "base" in r.output
