# -*- coding: utf-8 -*-
"""Reference management (sportsci_refs) — fully offline: no network, no running Zotero."""
import json
import zipfile
from pathlib import Path

import pytest

from sportsci_refs import format_list, parse_gbt_list, parse_ris, to_ris
from sportsci_refs.docx_fields import compare_parts, compress, expand, fieldify, field_diff, verify
from sportsci_refs.search import junk_reason, merge
from sportsci_refs.zotero import match

REFS = """[1] 张三, 李四, 王五, 等. 抗阻训练对2型糖尿病患者血糖控制的影响[J]. 体育科学, 2021, 41(3): 45-53.
[2] Colberg S R, Sigal R J, Yardley J E, et al. Physical activity/exercise and diabetes: a position statement of the American Diabetes Association[J]. Diabetes Care, 2016, 39(11): 2065-2079. DOI:10.2337/dc16-1728.
[3] 赵六. 青少年体质健康促进研究[D]. 北京: 北京体育大学, 2019.
[4] American College of Sports Medicine. ACSM's guidelines for exercise testing and prescription[M]. 11th ed. Philadelphia: Wolters Kluwer, 2021: 120-135.
[5] 国家体育总局. 全民健身计划（2021—2025年）[EB/OL]. (2021-08-03)[2024-05-01]. https://www.sport.gov.cn/n315/c23655706/content.html.
[6] SMITH J A, JONES B. Sprint performance in youth football[C]//Proceedings of the ECSS Congress. Cologne: ECSS, 2019: 112-113."""


def test_gbt_parse_format_roundtrip():
    recs = parse_gbt_list(REFS)
    assert [r["type"] for r in recs] == ["article-journal", "article-journal", "thesis", "book", "webpage", "paper-conference"]
    assert all(not r["_warnings"] for r in recs)
    assert recs[1]["DOI"] == "10.2337/dc16-1728" and recs[1]["page"] == "2065-2079"
    assert recs[3]["author"] == [{"literal": "American College of Sports Medicine"}] and recs[3]["edition"] == "11"
    out = format_list(recs)
    expected = [l.strip() for l in REFS.splitlines()]
    assert out[0] == expected[0] and out[1] == expected[1] and out[2] == expected[2] and out[4] == expected[4] and out[5] == expected[5]
    assert out[3] == expected[3]


def test_ris_roundtrip():
    recs = parse_gbt_list(REFS)
    back = parse_ris(to_ris(recs))
    assert len(back) == len(recs)
    assert back[1]["DOI"] == recs[1]["DOI"] and back[1]["page"] == "2065-2079" and back[1]["author"][0] == {"family": "Colberg", "given": "S R"}


def test_numbers_expand_compress():
    assert expand("1,3–5") == [1, 3, 4, 5] and expand("2-3") == [2, 3]
    assert compress([5, 3, 4, 1]) == "[1,3–5]" and compress([3, 4]) == "[3,4]"


def test_search_filters_and_dedupes():
    recs = {"crossref": [dict(doi="10.1/a", title="A study", author="x", year=2020, journal="J", cites=3, type="journal-article", source="Crossref"),
                         dict(doi="10.1/a/review1", title="Review for: A study", author="x", year=2020, journal="J", cites=0, type="peer-review", source="Crossref")],
            "openalex": [dict(doi="10.1/a", title="A study", author="x", year=2020, journal="J", cites=9, type="article", source="OpenAlex")]}
    kept, dropped = merge(recs)
    assert len(kept) == 1 and kept[0]["cites"] == 9 and kept[0]["also"] == ["OpenAlex"]
    assert len(dropped) == 1 and junk_reason(dropped[0][0])


def test_match_doi_then_title():
    refs = [dict(id="1", DOI="10.2337/DC16-1728", title="whatever"), dict(id="2", title="Muscle and glucose in older adults"), dict(id="3", title="Unrelated")]
    items = [dict(key="K1", doi="10.2337/dc16-1728", title="Physical activity", year="2016", journal="", type="journalArticle"),
             dict(key="K2", doi="", title="Muscle and glucose in older adults.", year="2018", journal="", type="journalArticle")]
    m = match(refs, items)
    assert m["mapping"]["1"]["key"] == "K1" and m["mapping"]["1"]["how"] == "DOI"
    assert m["mapping"]["2"]["key"] == "K2" and m["unmatched"] == ["3"]


def _make_docx(path, png=None):
    docx = pytest.importorskip("docx")
    d = docx.Document()
    p = d.add_paragraph("抗阻训练可改善血糖控制")
    r = p.add_run("[1]"); r.font.superscript = True
    p.add_run("，并提高肌肉质量")
    r = p.add_run("[2,3]"); r.font.superscript = True
    p.add_run("。")
    d.add_paragraph("也有研究报告了相似结果[3]，结论一致[4]。")
    p = d.add_paragraph("跨 run 的引用")
    p.add_run("[")
    p.add_run("4")
    p.add_run("]。")
    if png:
        d.add_picture(str(png))
    d.add_paragraph("参考文献")
    for line in REFS.splitlines()[:4]:
        d.add_paragraph(line)
    d.save(path)


def test_fieldify_verify_compare(tmp_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(1, 1)); fig.savefig(tmp_path / "x.png"); plt.close(fig)
    src, dst = tmp_path / "a.docx", tmp_path / "a_z.docx"
    _make_docx(src, tmp_path / "x.png")
    recs = parse_gbt_list(REFS)
    items = {i + 1: {"key": f"KEY{i + 1:05d}", "csl": r} for i, r in enumerate(recs[:4])}
    rep = fieldify(src, dst, items, user_id="1", superscript=True)
    assert rep["converted"] == 4 and rep["bib_entries"] == 4
    assert rep["not_converted"] == ["跨 run 的引用[4]。"]            # split runs are reported, never touched
    cp = compare_parts(src, dst)
    assert cp["only_document_changed"]
    xml = zipfile.ZipFile(dst).read("word/document.xml").decode("utf-8")
    assert "xmlns:a=" in xml and "<w:drawing>" in xml               # inline namespace of the picture survives
    v = verify(dst)
    assert v["counts"]["begin"] == v["counts"]["end"] == 5 and v["counts"]["ZOTERO_BIBL"] == 1
    s = v["summary"]
    assert s["json_errors"] == s["plain_vs_display"] == s["display_vs_first_order"] == s["cited_not_listed"] == 0
    assert s["bib_missing_tab"] == 4                                 # typed list: Zotero Refresh adds the tabs
    assert s["after_punctuation"] == 0 and s["adjacent_fields"] == 0
    assert field_diff(dst, dst)["identical"]
    with pytest.raises(ValueError):
        fieldify(dst, tmp_path / "again.docx", items, user_id="1")  # never double-convert
    with pytest.raises(ValueError):
        fieldify(src, src, items, user_id="1")                     # never overwrite the original


def test_verify_flags_wrong_order_and_punctuation(tmp_path):
    docx = pytest.importorskip("docx")
    src, dst = tmp_path / "b.docx", tmp_path / "b_z.docx"
    d = docx.Document()
    d.add_paragraph("先引用第二篇。[2]后引用第一篇[1]。")
    d.add_paragraph("参考文献")
    for line in REFS.splitlines()[:2]:
        d.add_paragraph(line)
    d.save(src)
    recs = parse_gbt_list(REFS)
    fieldify(src, dst, {1: {"key": "K1", "csl": recs[0]}, 2: {"key": "K2", "csl": recs[1]}}, user_id="1")
    s = verify(dst)["summary"]
    assert s["display_vs_first_order"] == 2 and s["after_punctuation"] == 1 and s["bib_title_mismatch"] == 2


def test_config_from_env(monkeypatch):
    from sportsci_refs.config import load_config
    monkeypatch.setenv("ZOTERO_USER_ID", "42")
    monkeypatch.setenv("SPORTSCI_CONTACT_EMAIL", "me@example.org")
    c = load_config(Path("does-not-exist.toml"))
    assert c.zotero_user_id == "42" and "mailto:me@example.org" in c.user_agent
