# -*- coding: utf-8 -*-
"""Results engine: (1) estimates recover known simulated truth, (2) multiplicity helpers, (3) end-to-end builds in both languages."""
import json
import re
from pathlib import Path

import numpy as np
import pytest

from sportsci_figures.pubstyle import has_cjk_font
from sportsci_figures.results import SpecError, analyze, load_spec, run_results, simulate, validate_spec
from sportsci_figures.results.util import bh, holm

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "config" / "design_templates"
CJK = re.compile(r"[㐀-鿿　-〿＀-￯]")


def tpl(name, **sim):
    d = json.loads((TPL / f"{name}.json").read_text(encoding="utf-8"))
    d["simulate"].update(sim)
    return d


def test_holm_bh_known_values():
    p = [0.01, 0.04, 0.03, 0.005]
    assert np.allclose(holm(p), [0.03, 0.06, 0.06, 0.02])
    assert np.allclose(bh(p), [0.02, 0.04, 0.04, 0.02])


def test_spec_validation_messages():
    errs = validate_spec({"design": "crossover", "columns": {"id": "id"}, "outcomes": [{"name": "a"}]})
    assert any("condition" in e for e in errs) and any("primary" in e for e in errs)
    with pytest.raises(SpecError):
        load_spec({"design": "nope"})


def test_parallel_recovers_truth():
    d = tpl("parallel_prepost", n={"CON": 300, "RT": 300}, dropout=0.0, seed=2)
    spec = load_spec(d)
    r = analyze(simulate(spec), spec)
    h = r["outcomes"][0]["contrasts"][0]
    assert abs(h["diff"] - (-0.50)) < 0.15 and h["lo"] < -0.50 < h["hi"] and h["p"] < 1e-6
    assert r["outcomes"][0]["contrasts"][0]["adj_method"] == "Holm"
    assert r["outcomes"][1]["contrasts"][0]["adj_method"] == "BH"


def test_parallel_null_is_not_significant():
    d = tpl("parallel_prepost", n={"CON": 60, "RT": 60}, dropout=0.0, seed=4)
    d["simulate"]["effects"]["hba1c"]["change"] = {"CON": 0.0, "RT": 0.0}
    spec = load_spec(d)
    c = analyze(simulate(spec), spec)["outcomes"][0]["contrasts"][0]
    assert c["lo"] < 0 < c["hi"]


def test_crossover_recovers_truth_and_trend():
    spec = load_spec(tpl("crossover", n=200, seed=3))
    r = analyze(simulate(spec), spec)
    o = r["outcomes"][0]
    truth = {"RT20": -3.6, "RT30": -4.4, "RT45": -4.6}
    for c in o["contrasts"]:
        assert c["lo"] < truth[c["arm"]] < c["hi"], c
    assert o["trend"]["est"] < 0 and o["model"] == "LMM" and r["period_adjusted"]
    assert o["pairs"][0]["a"] == "RT45"


def test_multitime_recovers_truth():
    d = tpl("multitime", n={"CON": 150, "INT": 150}, seed=8)
    spec = load_spec(d)
    r = analyze(simulate(spec), spec)
    o = r["outcomes"][0]
    last = [c for c in o["contrasts"] if c["time"] == "w16"][0]
    assert last["lo"] < 22 - 2 < last["hi"] and o["p_group_time"] < 1e-6 and last["at_primary"]


def test_meta_recovers_truth():
    d = tpl("meta", k=80, true=0.45, tau=0.15, seed=21, subgroups={}, moderator_slope=0.0)
    d["columns"].pop("subgroup")
    d["columns"].pop("moderator")
    spec = load_spec(d)
    r = analyze(simulate(spec), spec)
    P = r["pooled"]
    assert P["lo"] < 0.45 < P["hi"] and 0 < P["I2"] < 90 and r["egger"] is not None
    assert len(r["loo"]) == 80


@pytest.mark.parametrize("design", ["parallel_prepost", "crossover", "multitime", "meta"])
def test_end_to_end_english(tmp_path, design):
    out = run_results(TPL / f"{design}.json", None, tmp_path, lang="en", simulate_data=True)
    files = out["outputs"]["en"]
    assert files["docx"].exists() and files["xlsx"].exists()
    md = files["md"].read_text(encoding="utf-8")
    assert "Figure 1" in md and "Table 1" in md and "Simulated-data notice" in md
    assert not CJK.search(md), "English output must contain no CJK characters"
    pngs = list((tmp_path / "en" / "figures").glob("*.png"))
    assert pngs and (tmp_path / "analysis.json").exists()


@pytest.mark.skipif(not has_cjk_font(), reason="no CJK font installed")
@pytest.mark.parametrize("design", ["parallel_prepost", "crossover", "multitime", "meta"])
def test_end_to_end_chinese(tmp_path, design):
    out = run_results(TPL / f"{design}.json", None, tmp_path, lang="zh", simulate_data=True)
    md = out["outputs"]["zh"]["md"].read_text(encoding="utf-8")
    assert "图 1" in md and "表 1" in md and "模拟数据声明" in md


def test_real_data_not_tagged_simulated(tmp_path):
    spec = tpl("crossover", n=20)
    spec["simulated"] = False
    df = simulate(load_spec(spec))
    run_results(spec, df, tmp_path, lang="en")
    md = (tmp_path / "en" / "results.md").read_text(encoding="utf-8")
    assert "Simulated-data notice" not in md
