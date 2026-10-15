# -*- coding: utf-8 -*-
"""Offline tests: brief, design rules, record readers, evidence counts, power against published values,
variants, feasibility rubric, card, design draft."""
import copy
import datetime as dt
import json
from pathlib import Path

import pytest

from sportsci_topic import power as pw
from sportsci_topic.brief import BriefError, TEMPLATE, from_dict, load_brief, validate
from sportsci_topic.designmap import choose_design
from sportsci_topic.evidence import build_evidence, detect_design, term_regex
from sportsci_topic.feasibility import GREEN, RED, YELLOW, assess
from sportsci_topic.pipeline import run, search_queries
from sportsci_topic.records import Record, dedupe, load_records
from sportsci_topic.variants import build_variants, rank

TODAY = dt.date(2026, 10, 12)
YEAR = 2026


def R(title, year=2023, abstract="", doi=""):
    return Record(title=title, year=year, abstract=abstract, doi=doi)


# ------------------------------------------------------------------------------------------------------------ brief

def test_template_is_a_valid_brief(tmp_path):
    p = tmp_path / "b.toml"
    p.write_text(TEMPLATE, encoding="utf-8")
    errs, _ = validate(load_brief(p))
    assert errs == []


def test_exactly_one_primary_outcome_required(base_dict):
    d = base_dict
    d["outcomes"][1]["primary"] = True
    assert any("exactly one outcome" in e for e in validate(from_dict(d))[0])
    d["outcomes"][0]["primary"] = d["outcomes"][1]["primary"] = False
    assert any("exactly one outcome" in e for e in validate(from_dict(d))[0])


def test_missing_search_terms_and_language_warnings(base_dict):
    d = base_dict
    d["pico"]["outcome"]["terms"] = []
    d["pico"]["population"]["terms"] = ["university students"]
    errs, warns = validate(from_dict(d))
    assert any("pico.outcome.terms" in e for e in errs)
    assert any("no Chinese term" in w for w in warns)


def test_association_needs_scales_with_roles(base_dict):
    d = base_dict
    d["topic"]["question_type"] = "association"
    errs, _ = validate(from_dict(d))
    assert any("two scales" in e for e in errs)
    d["scales"] = [{"name": "PA", "label": "体育锻炼", "n_items": 5, "role": "x"}, {"name": "ANX", "label": "焦虑", "n_items": 6, "role": "y"}]
    assert validate(from_dict(d))[0] == []


def test_unknown_question_type_and_constraints(base_dict):
    d = base_dict
    d["topic"]["question_type"] = "magic"
    d["constraints"]["accessible_n"] = 0
    errs, _ = validate(from_dict(d))
    assert any("question_type" in e for e in errs) and any("accessible_n" in e for e in errs)


# ------------------------------------------------------------------------------------------------------- design rules

@pytest.mark.parametrize("qt,has_control,tp,expected", [
    ("effect", True, 2, "parallel_prepost"), ("effect", True, 4, "multitime"), ("effect", False, 2, "single_group"),
    ("acute", True, 2, "crossover"), ("course", True, 4, "multitime"), ("association", False, 1, "survey"), ("synthesis", False, 1, "meta"),
])
def test_design_rule_table(base_dict, qt, has_control, tp, expected):
    d = base_dict
    d["topic"]["question_type"] = qt
    d["design"]["has_control"], d["design"]["timepoints"] = has_control, tp
    assert choose_design(from_dict(d)).design == expected


def test_single_group_warns_about_attribution(base_dict):
    d = base_dict
    d["design"]["has_control"] = False
    ch = choose_design(from_dict(d), "zh")
    assert ch.design == "single_group" and ch.warnings and "对照" in ch.warnings[0]
    assert "归因" in ch.forbids


# ----------------------------------------------------------------------------------------------------- record readers

def test_csv_cnki_headers_utf8_and_gbk(tmp_path):
    rows = "Title-题名,Author-作者,Source-文献来源,Year-年,Summary-摘要,Keyword-关键词\n" \
           "功能性训练对大学生纵跳的影响,张三,体育科学,2021,摘要内容,功能性训练;纵跳\n"
    (tmp_path / "u.csv").write_bytes(rows.encode("utf-8-sig"))
    (tmp_path / "g.csv").write_bytes(rows.encode("gb18030"))
    for name in ("u.csv", "g.csv"):
        (r,) = load_records([tmp_path / name])
        assert r.title.startswith("功能性训练") and r.year == 2021 and r.journal == "体育科学" and "纵跳" in r.keywords


def test_ris_json_txt_readers(tmp_path):
    (tmp_path / "a.ris").write_text("TY  - JOUR\nTI  - Functional training in students\nPY  - 2020/05/01\nDO  - https://doi.org/10.1000/ABC\nJO  - J Test\nER  - \n", encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps([{"title": ["Core training and jump"], "issued": {"date-parts": [[2019]]}, "DOI": "10.1000/xyz"}]), encoding="utf-8")
    (tmp_path / "c.txt").write_text("[1] 张三, 李四. 抗阻训练对血糖的影响[J]. 体育科学, 2021, 41(3): 45-53.\n2. Plain title only 2018\n", encoding="utf-8")
    recs = load_records([tmp_path / "a.ris", tmp_path / "b.json", tmp_path / "c.txt"])
    by = {r.title: r for r in recs}
    assert by["Functional training in students"].doi == "10.1000/abc" and by["Functional training in students"].year == 2020
    assert by["Core training and jump"].year == 2019
    assert "抗阻训练对血糖的影响" in by and by["抗阻训练对血糖的影响"].year == 2021
    assert by["Plain title only 2018"].year == 2018


def test_dedupe_by_doi_and_title_keeps_richer_copy():
    a = Record("Same Paper", 2020, doi="10.1/a")
    b = Record("same paper (copy)", 2020, doi="10.1/a", journal="J")
    c = Record("Another, paper!", 2019)
    d = Record("another paper", 2019, journal="K")
    out = dedupe([a, b, c, d])
    assert len(out) == 2 and {r.journal for r in out} == {"J", "K"}


def test_unsupported_file_type(tmp_path):
    (tmp_path / "x.docx").write_text("x")
    with pytest.raises(ValueError):
        load_records([tmp_path / "x.docx"])


# ---------------------------------------------------------------------------------------------------- evidence map

def test_term_matching_is_word_bounded_with_plurals_and_hyphens():
    rx = term_regex("rt")
    assert not rx.search("start of the season") and rx.search("rt and control")
    assert term_regex("university student").search("university students were recruited")
    assert term_regex("high intensity interval training").search("high-intensity interval training")
    assert term_regex("纵跳").search("纵跳高度提高")


def test_design_detection_precedence():
    assert detect_design("a systematic review of randomised trials") == "review"
    assert detect_design("random 分配的实验") == "rct"
    assert detect_design("某问卷调查") == "survey"
    assert detect_design("nothing relevant") == "other"


def _records_for_map():
    recs = []
    for i in range(5):
        recs.append(R(f"Functional training and balance in university students {i}", 2022))              # P+I
    for i in range(3):
        recs.append(R(f"Functional training and countermovement jump in older adults {i}", 2021))        # I+O
    recs.append(R("Plyometric training and vertical jump in university students", 2024))                 # P+O
    recs += [R(f"Unrelated nutrition study {i}", 2020) for i in range(25)]
    return recs


def test_combos_gap_statement_and_tier(base_dict):
    b = from_dict(base_dict)
    ev = build_evidence(_records_for_map(), b, this_year=YEAR)
    assert ev.n_records == 34 and ev.coverage == "ok"
    assert ev.combos_all["P+I"] == 5 and ev.combos_all["I+O"] == 3 and ev.combos_all["P+O"] == 1 and ev.combos_all["P+I+O"] == 0
    assert ev.tier == "none" and ev.direct_all == 0
    kinds = [g["kind"] for g in ev.gaps]
    assert "missing_outcome" in kinds and "missing_intervention" not in kinds  # P+O has 1 < 3 records
    assert all(g["counts"] for g in ev.gaps)


def test_direct_overlap_tiers_and_recent_window(base_dict):
    b = from_dict(base_dict)
    old = [R(f"Functional training and vertical jump in university students {i}", 2010) for i in range(12)]
    ev = build_evidence(old + [R("filler %d" % i) for i in range(30)], b, this_year=YEAR)
    assert ev.direct_all == 12 and ev.direct_recent == 0 and ev.tier == "none"
    new = [R(f"Functional training and vertical jump in university students {i}", 2024) for i in range(10)]
    ev = build_evidence(new + [R("filler %d" % i) for i in range(30)], b, this_year=YEAR)
    assert ev.direct_recent == 10 and ev.tier == "very_crowded"
    ev = build_evidence(new[:4] + [R("filler %d" % i) for i in range(30)], b, this_year=YEAR)
    assert ev.tier == "crowded"


def test_low_coverage_is_flagged(base_dict):
    ev = build_evidence([R("Functional training and vertical jump in university students")], from_dict(base_dict), this_year=YEAR)
    assert ev.coverage == "low" and ev.direct_all == 1


def test_design_gap_when_no_randomised_direct_overlap(base_dict):
    recs = [R("Functional training and vertical jump in university students: a cross-sectional study")] + [R("x %d" % i) for i in range(30)]
    ev = build_evidence(recs, from_dict(base_dict), this_year=YEAR)
    assert "design_gap" in [g["kind"] for g in ev.gaps]


def test_search_queries_cover_pairs_and_both_languages(base_dict):
    qs = search_queries(from_dict(base_dict))
    assert "university students functional training" in qs and "functional training countermovement jump" in qs
    assert any("大学生" in q and "下肢爆发力" in q for q in qs)


# ------------------------------------------------------------------------------------------------------------ power

def test_known_values():
    assert pw.n_two_sample(0.5) == 64                       # G*Power: 64 per group
    assert pw.n_paired(0.5) == 34                           # G*Power: 34
    assert pw.n_correlation(0.3) in (84, 85)                # exact 84, Fisher-z approximation 85
    assert pw.n_anova(0.25, 3) == 159                       # G*Power: 159 (158 rounded up to 3 equal groups)
    assert pw.n_regression(0.15, 3) == 77                   # G*Power: 77
    assert abs(pw.power_two_sample(0.5, 64) - 0.80) < 0.01
    assert abs(pw.mdes_two_sample(64) - 0.5) < 0.01


def test_power_is_monotone_and_mdes_inverts_it():
    ps = [pw.power_two_sample(0.5, n) for n in (10, 20, 40, 80)]
    assert ps == sorted(ps)
    d = pw.mdes_two_sample(25)
    assert abs(pw.power_two_sample(d, 25) - 0.80) < 0.005
    assert pw.n_two_sample(2.0) < pw.n_two_sample(0.5) < pw.n_two_sample(0.2)


def test_huge_effects_do_not_return_nan():
    assert pw.power_two_sample(30, 40) == 1.0
    assert pw.n_two_sample(5.0) >= 3


def test_dropout_inflation():
    assert pw.inflate(64, 0.15) == 76
    assert pw.inflate(64, 0.0) == 64


def test_ancova_uses_baseline_correlation(base_dict):
    d = base_dict
    d["effect"] = {"source": "paper", "delta": 3.0, "sd": 5.0, "r_prepost": 0.6, "alpha": 0.05, "power": 0.8}
    b = from_dict(d)
    plan = pw.plan_sample(b, choose_design(b))
    assert plan.test == "ancova" and abs(plan.effect_value - 3.0 / (5.0 * 0.8)) < 1e-9
    assert plan.n_per_group < pw.n_two_sample(3.0 / 5.0)


def test_plan_without_effect_gives_no_number(base_dict):
    d = base_dict
    d["effect"] = {}
    b = from_dict(d)
    plan = pw.plan_sample(b, choose_design(b))
    assert plan.status == "no_effect" and plan.n_total is None and plan.sensitivity and plan.mdes_at_accessible


def test_plan_survey_floor_and_meta(base_dict):
    d = base_dict
    d["topic"]["question_type"] = "association"
    d["scales"] = [{"name": "PA", "n_items": 8, "role": "x"}, {"name": "SE", "n_items": 10, "role": "m"}, {"name": "ANX", "n_items": 12, "role": "y"}]
    d["effect"] = {"source": "", "alpha": 0.05, "power": 0.8}
    b = from_dict(d)
    plan = pw.plan_sample(b, choose_design(b))
    assert plan.n_total >= 200 and any("因子分析" in r for r in plan.rules)
    d["topic"]["question_type"] = "synthesis"
    b = from_dict(d)
    assert pw.plan_sample(b, choose_design(b)).status == "not_applicable"


# ------------------------------------------------------------------------------------------------------- variants

def test_variants_count_and_flag_unassessable(base_dict):
    d = base_dict
    d["variants"] = {"population": [{"label": "高中生", "terms": ["high school students"]}, {"label": "老年人", "terms": ["older adults"]}],
                     "outcome": [{"label": "平衡", "terms": ["balance"]}]}
    b = from_dict(d)
    recs = _records_for_map() + [R("Functional training and vertical jump in university students", 2024)]
    vs = rank(build_variants(recs, b, this_year=YEAR))
    base = vs[0]
    assert not base.axes and base.direct_recent == 1
    by = {v.name(): v for v in vs}
    hs = by["population=高中生"]
    assert not hs.assessable and hs.direct_recent == 0     # a zero that means nothing
    older = by["population=老年人"]
    assert older.assessable and older.direct_all == 3 and older.direct_recent == 0 and older.delta_recent == -1  # three 2021 records, outside the window
    # unassessable variants are ranked after assessable ones
    names = [v.name() for v in vs[1:]]
    assert names.index("population=高中生") > names.index("population=老年人")


def test_two_axis_variants(base_dict):
    d = base_dict
    d["variants"] = {"population": [{"label": "A", "terms": ["older adults"]}], "outcome": [{"label": "B", "terms": ["balance"]}]}
    vs = build_variants(_records_for_map(), from_dict(d), this_year=YEAR, two_axis=True)
    assert any(len(v.axes) == 2 for v in vs)


# --------------------------------------------------------------------------------------------------- feasibility

def _assess(d, recs=None, lang="zh"):
    b = from_dict(d)
    ch = choose_design(b, lang)
    plan = pw.plan_sample(b, ch, lang)
    ev = build_evidence(recs, b, this_year=YEAR) if recs else None
    return assess(b, ch, plan, ev, lang)


def status(a, cid):
    return next(c.status for c in a["checks"] if c.id == cid)


def test_time_check_levels(base_dict):
    d = base_dict
    assert status(_assess(d), "time") == GREEN
    d["constraints"]["weeks_available"] = 21            # needs 18 weeks: slack 3 < 20%
    assert status(_assess(d), "time") == YELLOW
    d["constraints"]["weeks_available"] = 12
    assert status(_assess(d), "time") == RED


def test_sample_check_levels_follow_power(base_dict):
    d = base_dict                                        # 80 accessible, d = 0.7 -> 34/group needed, 34 analysed/group
    assert status(_assess(d), "sample") == GREEN
    d["constraints"]["accessible_n"] = 56                # about 24 per group: power ~0.67
    assert status(_assess(d), "sample") == YELLOW
    d["constraints"]["accessible_n"] = 30
    assert status(_assess(d), "sample") == RED


def test_sample_without_source_never_green(base_dict):
    d = base_dict
    d["effect"]["source"] = ""
    assert status(_assess(d), "sample") == YELLOW


def test_missing_primary_instrument_is_red_secondary_yellow(base_dict):
    d = base_dict
    d["constraints"]["equipment"] = ["timing gates"]
    a = _assess(d)
    assert status(a, "measures") == RED and a["overall"] == RED
    d["constraints"]["equipment"] = ["jump mat"]
    assert status(_assess(d), "measures") == YELLOW


def test_ethics_and_vulnerable(base_dict):
    d = base_dict
    d["constraints"]["ethics"] = "pending"
    assert status(_assess(d), "ethics") == YELLOW
    d["constraints"]["ethics"] = "approved"
    d["constraints"]["vulnerable_population"] = True
    assert status(_assess(d), "ethics") == YELLOW
    d["constraints"]["vulnerable_population"] = False
    d["constraints"]["ethics"] = "not_started"
    d["constraints"]["weeks_available"] = 10
    assert status(_assess(d), "ethics") == RED


def test_stats_comfort_gap(base_dict):
    d = base_dict
    d["topic"]["question_type"] = "course"
    d["design"]["timepoints"] = 4
    d["constraints"]["stats_comfort"] = "basic"
    assert status(_assess(d), "stats") == RED            # mixed model is two levels above 'basic'
    d["constraints"]["stats_comfort"] = "advanced"
    assert status(_assess(d), "stats") == GREEN


def test_evidence_check_levels_and_thin_set(base_dict):
    d = base_dict
    filler = [R("filler %d" % i) for i in range(30)]
    near = lambda n: [R(f"Functional training and vertical jump in university students {i}", 2024) for i in range(n)]
    assert status(_assess(d, filler), "evidence") == GREEN
    assert status(_assess(d, filler + near(2)), "evidence") == GREEN
    assert status(_assess(d, filler + near(5)), "evidence") == YELLOW
    assert status(_assess(d, filler + near(12)), "evidence") == RED
    assert status(_assess(d, near(1)), "evidence") == YELLOW      # 1 record: a sketch
    assert status(_assess(d, None), "evidence") == YELLOW


def test_overall_is_the_worst_check_and_every_check_states_its_rule(base_dict):
    a = _assess(base_dict, [R("filler %d" % i) for i in range(30)])
    assert a["overall"] == max((c.status for c in a["checks"]), key=[GREEN, YELLOW, RED].index)
    assert all(c.rule and c.detail for c in a["checks"])


# ----------------------------------------------------------------------------------------- card and design draft

def _run(write_brief, d, recs, tmp_path, lang=None):
    rp = tmp_path / "records.csv"
    rows = ["Title,Year,Abstract"] + [f'"{r.title}",{r.year},"{r.abstract}"' for r in recs]
    rp.write_text("\n".join(rows), encoding="utf-8")
    return run(write_brief(d), [rp], this_year=YEAR, lang=lang, today=TODAY)


def test_card_is_deterministic_and_complete(write_brief, base_dict, tmp_path):
    base_dict["variants"] = {"outcome": [{"label": "平衡", "terms": ["balance"]}]}
    recs = _records_for_map()
    r1 = _run(write_brief, base_dict, recs, tmp_path)
    r2 = _run(write_brief, base_dict, recs, tmp_path)
    assert r1.card == r2.card
    for section in ("## 1.", "## 2.", "## 3.", "## 4.", "## 5.", "## 6.", "## 7."):
        assert section in r1.card
    assert "功能性训练" in r1.card and "最接近的研究" in r1.card and "规则" in r1.card
    assert "{" not in r1.card.replace("{}", "")            # no unfilled placeholders


def test_card_english_has_no_chinese_headers(write_brief, base_dict, tmp_path):
    r = _run(write_brief, base_dict, _records_for_map(), tmp_path, lang="en")
    heads = [ln for ln in r.card.splitlines() if ln.startswith("#")][1:]      # the working title is the author's own text
    assert heads and not any("一" <= ch <= "鿿" for h in heads for ch in h)
    assert "Topic card" in r.card and "Sample size" in r.card


def test_card_without_records_says_it_cannot_conclude(write_brief, base_dict):
    r = run(write_brief(base_dict), [], today=TODAY)
    assert r.evidence is None and "不能下结论" in r.card
    assert status(r.assessment, "evidence") == YELLOW


def test_brief_errors_stop_the_run(write_brief, base_dict):
    base_dict["outcomes"][0]["primary"] = False
    with pytest.raises(BriefError):
        run(write_brief(base_dict), [])


@pytest.mark.parametrize("qt,tp,has_control", [("effect", 2, True), ("effect", 4, True), ("effect", 2, False), ("acute", 2, True), ("course", 4, True)])
def test_design_drafts_pass_the_results_engine_validator(base_dict, write_brief, qt, tp, has_control):
    figures = Path(__file__).resolve().parents[2] / "sportsci-figures"
    try:
        import sportsci_figures.results.spec as spec  # type: ignore
    except ImportError:
        import sys
        if not figures.exists():
            pytest.skip("sportsci-figures not available")
        sys.path.insert(0, str(figures))
        import sportsci_figures.results.spec as spec  # type: ignore
    d = base_dict
    d["topic"]["question_type"], d["design"]["timepoints"], d["design"]["has_control"] = qt, tp, has_control
    d["design"]["conditions"] = ["无运动", "运动"]
    r = run(write_brief(d), [], today=TODAY)
    assert spec.validate_spec(r.draft) == []
    assert r.draft["simulated"] is False
    assert sum(1 for o in r.draft["outcomes"] if o["primary"]) == 1


def test_survey_draft_passes_validator(base_dict, write_brief):
    figures = Path(__file__).resolve().parents[2] / "sportsci-figures"
    if not figures.exists():
        pytest.skip("sportsci-figures not available")
    import sys
    sys.path.insert(0, str(figures))
    import sportsci_figures.results.spec as spec  # type: ignore
    d = base_dict
    d["topic"]["question_type"] = "association"
    d["scales"] = [{"name": "PA", "label": "体育锻炼", "n_items": 5, "role": "x"}, {"name": "SLP", "label": "睡眠", "n_items": 5, "role": "m"},
                   {"name": "ANX", "label": "焦虑", "n_items": 6, "role": "y"}]
    r = run(write_brief(d), [], today=TODAY)
    assert r.choice.design == "survey" and spec.validate_spec(r.draft) == []
    assert r.draft["mediation"][0]["m"] == "SLP"
