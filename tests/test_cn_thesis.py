# -*- coding: utf-8 -*-
"""Chinese-thesis features: single-group and survey designs (against reference implementations), mixed ANOVA supplement,
thesis numbering, methods explanation, data intake, privacy."""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sportsci_figures.privacy import pii_columns, redact, scrub_frame
from sportsci_figures.results import analyze, load_spec, run_results, simulate, validate_spec
from sportsci_figures.results.analysis_single import rm_anova
from sportsci_figures.results.analysis_survey import cronbach_alpha, mediation, regression

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "config" / "design_templates"
CJK = re.compile(r"[㐀-鿿　-〿＀-￯]")


def tpl(name, **sim):
    d = json.loads((TPL / f"{name}.json").read_text(encoding="utf-8"))
    d["simulate"].update(sim)
    return d


# ----------------------------------------------------------------------------- statistics vs reference implementations
def test_rm_anova_matches_pingouin():
    pg = pytest.importorskip("pingouin")
    rng = np.random.default_rng(0)
    b = rng.normal(0, 2, 25)
    Y = np.column_stack([b + 10 + rng.normal(0, 1, 25), b + 10.8 + rng.normal(0, 2, 25), b + 11.5 + rng.normal(0, 3, 25), b + 11 + rng.normal(0, 1.2, 25)])
    a = rm_anova(Y)
    long = pd.DataFrame([(i, t, Y[i, t]) for i in range(25) for t in range(4)], columns=["id", "t", "y"])
    ref = pg.rm_anova(long, dv="y", within="t", subject="id", correction=True).iloc[0]
    assert a["F"] == pytest.approx(ref["F"], rel=1e-6)
    assert a["eps_gg"] == pytest.approx(ref["eps"], rel=1e-4)
    assert a["mauchly_W"] == pytest.approx(ref["W-spher"], rel=1e-4)
    assert a["p_gg"] == pytest.approx(ref["p-GG-corr"], rel=1e-4)


def test_cronbach_alpha_matches_pingouin():
    pg = pytest.importorskip("pingouin")
    rng = np.random.default_rng(1)
    z = rng.normal(size=200)
    X = pd.DataFrame({f"i{k}": np.clip(np.round(3 + z + rng.normal(0, 1, 200)), 1, 5) for k in range(5)})
    assert cronbach_alpha(X) == pytest.approx(pg.cronbach_alpha(X)[0], rel=1e-6)


def test_regression_matches_statsmodels():
    sm = pytest.importorskip("statsmodels.api")
    rng = np.random.default_rng(2)
    d = pd.DataFrame({"x1": rng.normal(size=150), "x2": rng.normal(size=150), "sex": rng.choice(["F", "M"], 150)})
    d["y"] = 0.5 * d.x1 - 0.3 * d.x2 + (d.sex == "M") * 0.4 + rng.normal(size=150)
    r = regression(d, "y", ["x1", "x2"], ["sex"])
    X = sm.add_constant(np.column_stack([d.x1, d.x2, (d.sex == "M").astype(float)]))
    ref = sm.OLS(d.y, X).fit()
    assert [c["B"] for c in r["coefs"]] == pytest.approx(list(ref.params.iloc[1:]), rel=1e-8)
    assert r["r2"] == pytest.approx(ref.rsquared, rel=1e-8)
    assert r["coefs"][0]["p"] == pytest.approx(ref.pvalues.iloc[1], rel=1e-6)


def test_mediation_detects_indirect_and_null():
    rng = np.random.default_rng(3)
    x = rng.normal(size=400)
    m = 0.5 * x + rng.normal(size=400)
    y = 0.4 * m + 0.1 * x + rng.normal(size=400)
    r = mediation(pd.DataFrame(dict(x=x, m=m, y=y)), "x", "m", "y", n_boot=800)
    assert 0.12 < r["indirect"]["est"] < 0.30 and r["indirect"]["lo"] > 0
    y0 = 0.1 * x + rng.normal(size=400)
    m0 = rng.normal(size=400)
    r0 = mediation(pd.DataFrame(dict(x=x, m=m0, y=y0)), "x", "m", "y", n_boot=800)
    assert r0["indirect"]["lo"] < 0 < r0["indirect"]["hi"]


def test_single_group_recovers_change_and_flags():
    spec = load_spec(tpl("single_group", n=400, seed=9))
    r = analyze(simulate(spec), spec)
    cmj = r["outcomes"][0]
    assert cmj["test"]["kind"] == "rm_anova" and cmj["main"]["adj_method"] == "Holm"
    assert abs(cmj["change"]["diff"] - 2.4) < 0.3
    two = tpl("single_group", n=40, seed=4)
    two["times"]["order"] = ["pre", "w8"]
    spec2 = load_spec(two)
    r2 = analyze(simulate(spec2), spec2)
    assert r2["outcomes"][0]["test"]["kind"] == "paired_t" and r2["outcomes"][0]["test"]["p"] < 0.05


def test_survey_pipeline_and_validation():
    spec = load_spec(tpl("survey", n=300, seed=5))
    r = analyze(simulate(spec), spec)
    assert all(s["alpha"] > 0.7 for s in r["scales"])
    assert r["efa"]["n_factors"] == 4 and r["efa"]["kmo"] > 0.7
    assert r["harman"]["first_pct"] < 40
    assert r["mediation"][0]["indirect"]["hi"] < 0          # PA -> sleep -> anxiety, negative indirect effect
    assert {g["var"] for g in r["group_compare"]} == {"sex", "grade"}
    bad = {"design": "survey", "scales": [{"name": "A", "items": ["a1"], "reverse": ["a9"]}], "group_compare": ["sex"]}
    errs = validate_spec(bad)
    assert any(">= 2 item" in e for e in errs) and any("reverse" in e for e in errs) and any("demographics" in e for e in errs)


def test_multitime_has_mixed_anova_supplement():
    spec = load_spec(tpl("multitime"))
    r = analyze(simulate(spec), spec)
    ma = r["outcomes"][0]["mixed_anova"]
    assert [e["effect"] for e in ma["effects"]] == ["group", "time", "group_x_time"]


# ----------------------------------------------------------------------------- end to end
@pytest.mark.parametrize("design", ["single_group", "survey"])
def test_end_to_end_both_languages_thesis_layout(tmp_path, design):
    d = tpl(design)
    if design == "survey":
        d["simulate"]["n"] = 200
        d["mediation"][0]["n_boot"] = 300
    r = run_results(d, None, tmp_path, lang="both", simulate_data=True, thesis_chapter=4)
    import docx
    for lg in ("zh", "en"):
        out = r["outputs"][lg]
        assert out["docx"].exists() and out["explain"].exists()
        caps = [p.text for p in docx.Document(out["docx"]).paragraphs if p.text.startswith(("图 4-", "表 4-", "Figure 4.", "Table 4."))]
        assert caps, "thesis numbering missing"
        md = out["md"].read_text(encoding="utf-8")
        if lg == "en":
            assert not CJK.search(md), CJK.findall(md)[:10]
    assert (tmp_path / "zh" / "methods_explained.md").read_text(encoding="utf-8").startswith("# 方法讲解")


# ----------------------------------------------------------------------------- intake & privacy
def test_intake_survey_and_wide_prepost(tmp_path):
    from sportsci_figures.intake import run_intake
    spec = load_spec(tpl("survey", n=150))
    d = simulate(spec).rename(columns={"id": "编号"})
    d.insert(1, "姓名", [f"学生{i}" for i in range(len(d))])
    d.to_csv(tmp_path / "s.csv", index=False, encoding="gb18030")
    r = run_intake(tmp_path / "s.csv", tmp_path / "o1")
    assert r["layout"]["design"] == "survey" and r["removed"] == ["姓名"]
    draft = json.loads((tmp_path / "o1" / "design_draft.json").read_text(encoding="utf-8"))
    rev = {s["name"]: s["reverse"] for s in draft["scales"]}
    assert rev["SL"] == ["SL3"] and rev["AX"] == ["AX6"]
    clean = pd.read_csv(tmp_path / "o1" / "data_clean.csv")
    assert "姓名" not in clean.columns and clean["编号"].iloc[0] == "P001"
    assert (tmp_path / "o1" / "_private" / "id_map.csv").exists()

    rng = np.random.default_rng(0)
    w = pd.DataFrame({"受试者编号": [f"S{i}" for i in range(20)], "组别": ["实验组"] * 10 + ["对照组"] * 10,
                      "VO2max_前测": rng.normal(45, 5, 20), "VO2max_后测": rng.normal(48, 5, 20)})
    w.to_excel(tmp_path / "w.xlsx", index=False)
    r2 = run_intake(tmp_path / "w.xlsx", tmp_path / "o2")
    assert r2["layout"]["design"] == "parallel_prepost" and r2["spec"]["groups"]["control"] == "对照组"
    res = run_results(tmp_path / "o2" / "design_draft.json", tmp_path / "o2" / "data_long.csv", tmp_path / "res", lang="zh")
    assert res["outputs"]["zh"]["docx"].exists()


def test_redaction_and_pii_columns():
    s = redact("电话 13812345678，邮箱 a.b@c.com，身份证 110101199003071234，NRIC S1234567D，P = 0.91234567，学号 2023123456789")
    for raw in ("13812345678", "a.b@c.com", "110101199003071234", "S1234567D", "2023123456789"):
        assert raw not in s
    assert "0.91234567" in s                      # statistics are not mistaken for phone numbers
    df = pd.DataFrame({"id": ["a", "b"], "姓名": ["x", "y"], "Phone": [1, 2], "hotel_nights": [1, 2], "vo2max": [40, 50]})
    assert pii_columns(df) == ["姓名", "Phone"]
    clean, mp = scrub_frame(df, "id")
    assert list(clean.columns) == ["id", "hotel_nights", "vo2max"] and list(clean["id"]) == ["P001", "P002"] and mp == {"a": "P001", "b": "P002"}
