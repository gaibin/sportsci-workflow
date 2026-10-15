# -*- coding: utf-8 -*-
"""Field-safe editing: edits never touch fields, counts are conserved, ambiguous anchors are refused, namespaces survive."""
import zipfile
from pathlib import Path

import pytest

docx = pytest.importorskip("docx")

from sportsci_refs import parse_gbt_list
from sportsci_refs.docx_fields import compare_parts, fieldify, verify
from sportsci_refs.fieldedit import FieldDoc, detach, plain_text, set_group_display

REFS = """[1] 张三, 李四. 抗阻训练对2型糖尿病患者血糖控制的影响[J]. 体育科学, 2021, 41(3): 45-53.
[2] Colberg S R, Sigal R J. Physical activity/exercise and diabetes[J]. Diabetes Care, 2016, 39(11): 2065-2079.
[3] 赵六. 青少年体质健康促进研究[D]. 北京: 北京体育大学, 2019.
[4] Smith J A. Muscle and glucose[J]. J Appl Physiol, 2018, 125: 1-9."""


@pytest.fixture()
def fielded(tmp_path):
    """A document with live citation fields, a bibliography field and an inline picture."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, _ = plt.subplots(figsize=(1, 1))
    fig.savefig(tmp_path / "x.png")
    plt.close(fig)
    d = docx.Document()
    p = d.add_paragraph("抗阻训练可改善血糖控制")
    r = p.add_run("[1]"); r.font.superscript = True
    p.add_run("，并提高肌肉质量")
    r = p.add_run("[2,3]"); r.font.superscript = True
    p.add_run("。")
    d.add_paragraph("也有研究报告了相似结果[3]，结论一致[4]。结论一致，仍需验证。")
    d.add_paragraph("没有任何引用的一句话，结论一致。")
    d.add_picture(str(tmp_path / "x.png"))
    d.add_paragraph("参考文献")
    for line in REFS.splitlines():
        d.add_paragraph(line)
    src = tmp_path / "plain.docx"
    d.save(src)
    recs = parse_gbt_list(REFS)
    items = {i + 1: {"key": f"KEY{i + 1:05d}", "csl": r} for i, r in enumerate(recs)}
    out = tmp_path / "fielded.docx"
    fieldify(src, out, items, user_id="1", superscript=True)
    return out


def test_replace_only_touches_plain_text(fielded, tmp_path):
    doc = FieldDoc(fielded)
    before = doc.field_counts()
    n = doc.replace("提高肌肉质量", "增加肌肉质量")
    assert n == 1
    assert doc.replace("参考文献中不存在的词", "x") == 0
    out = doc.save(tmp_path / "edited.docx")
    v = verify(out)
    assert v["counts"]["begin"] == v["counts"]["end"] == before["begin"]
    assert v["summary"]["json_errors"] == 0 and v["summary"]["plain_vs_display"] == 0
    assert "增加肌肉质量" in "".join(plain_text(p) for p in FieldDoc(out).paragraphs)


def test_bibliography_paragraphs_are_never_edited(fielded):
    doc = FieldDoc(fielded)
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
    entries = [k for k, p in enumerate(doc.paragraphs) if "".join(t.text or "" for t in p.iter(W)).startswith("[")]
    assert len(entries) == 4
    # begin sits in the first entry's own paragraph; the other entries are inside the field although begin is in another paragraph
    assert [doc.depth_at(k) > 0 for k in entries] == [False, True, True, True]
    assert all(doc.plain(k) == "" for k in entries)        # no plain text anywhere in the bibliography field
    assert doc.replace("抗阻训练对2型", "力量训练对2型") == 0  # field result text is Zotero's to rewrite, not ours
    assert doc.find("抗阻训练对2型") == []


def test_ambiguous_anchor_is_refused_and_unique_one_works(fielded, tmp_path):
    doc = FieldDoc(fielded)
    cits = doc.citations()
    i_src, grp = cits[0]                           # [1] in paragraph 0
    i_dst = next(k for k, p in enumerate(doc.paragraphs) if "没有任何引用" in doc.plain(k))
    ok, msg = doc.insert_after_anchor(i_dst, "结论一致", [])           # appears once in this paragraph? it appears once -> ok
    assert ok
    j = next(k for k, p in enumerate(doc.paragraphs) if "相似结果" in doc.plain(k))
    ok, msg = doc.insert_after_anchor(j, "结论一致", [])               # appears twice in that paragraph
    assert not ok and "2 times" in msg
    els = detach(grp)
    ok, msg = doc.insert_before_anchor(i_dst, "。", els)               # citation lands BEFORE the full stop
    assert ok, msg
    out = doc.save(tmp_path / "moved.docx")
    v = verify(out)
    assert v["counts"]["begin"] == v["counts"]["end"]
    assert v["summary"]["after_punctuation"] == 0
    assert v["summary"]["json_errors"] == 0


def test_move_changes_order_and_refresh_numbers_repairs_display(fielded, tmp_path):
    doc = FieldDoc(fielded)
    (i0, g1), (_, g23), (_, g3), (_, g4) = doc.citations()
    # move the first citation to the very end of the third paragraph: first-appearance order changes
    i_dst = next(k for k, p in enumerate(doc.paragraphs) if "没有任何引用" in doc.plain(k))
    detach(g1)
    ok, msg = doc.insert_before_anchor(i_dst, "。", g1.elements)
    assert ok, msg
    bad = tmp_path / "bad.docx"
    doc.save(bad)
    assert verify(bad)["summary"]["display_vs_first_order"] > 0        # the numbers are now out of order ...
    doc2 = FieldDoc(bad)
    rep = doc2.refresh_numbers()                                         # ... and refresh puts them back
    assert rep["changed"] and rep["items"] == 4
    good = doc2.save(tmp_path / "good.docx")
    s = verify(good)["summary"]
    assert s["display_vs_first_order"] == 0 and s["plain_vs_display"] == 0 and s["json_errors"] == 0


def test_set_group_display_updates_payload(fielded):
    doc = FieldDoc(fielded)
    _, grp = doc.citations()[0]
    set_group_display(grp, "[12–14]")
    assert grp.display == "[12–14]"
    pl = grp.payload["properties"]
    assert pl["plainCitation"] == "[12–14]"
    assert pl["formattedCitation"] == r"[12\uc0\u8211{}14]"               # en dash is stored the way Zotero stores it


def test_set_group_display_keeps_rtf_superscript_wrapper(fielded):
    import json
    from sportsci_refs.fieldedit import q
    doc = FieldDoc(fielded)
    _, grp = doc.citations()[0]
    its = [t for e in grp.elements for t in e.iter(q("instrText"))]
    d = grp.payload
    d["properties"]["formattedCitation"] = r"\super [1]\nosupersub{}"       # style that renders superscript through RTF
    its[0].text = " ADDIN ZOTERO_ITEM CSL_CITATION " + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + " "
    for t in its[1:]:
        t.text = ""
    grp.instr = its[0].text
    set_group_display(grp, "[12–14]")
    assert grp.payload["properties"]["formattedCitation"] == r"\super [12\uc0\u8211{}14]\nosupersub{}"


def test_save_guards(fielded, tmp_path):
    doc = FieldDoc(fielded)
    with pytest.raises(ValueError):
        doc.save(fielded)                           # never overwrite the original
    _, grp = doc.citations()[0]
    detach(grp)                                     # a citation disappears -> field counts change
    with pytest.raises(ValueError, match="field counts changed"):
        doc.save(tmp_path / "lost.docx")
    assert doc.save(tmp_path / "lost.docx", allow_field_change=True).exists()


def test_other_parts_and_namespaces_survive(fielded, tmp_path):
    doc = FieldDoc(fielded)
    doc.replace("血糖控制", "血糖管理")
    out = doc.save(tmp_path / "e.docx")
    cp = compare_parts(fielded, out)
    assert cp["only_document_changed"]
    xml = zipfile.ZipFile(out).read("word/document.xml").decode("utf-8")
    assert "xmlns:a=" in xml and "<w:drawing>" in xml        # the picture's own namespace declaration is still there
    docx.Document(out)                                         # python-docx can reopen it
    assert FieldDoc(out)._nsmap0 == FieldDoc(fielded)._nsmap0


def test_cross_run_replace_keeps_formatting(tmp_path):
    d = docx.Document()
    p = d.add_paragraph()
    p.add_run("训练效果")
    r = p.add_run("显著"); r.bold = True
    p.add_run("提高。")
    src = tmp_path / "s.docx"
    d.save(src)
    doc = FieldDoc(src)
    assert doc.replace("效果显著提高", "效果明显提高") == 1      # only "显著"→"明显" is rewritten, inside the bold run
    out = doc.save(tmp_path / "t.docx")
    paras = docx.Document(out).paragraphs
    assert paras[0].text == "训练效果明显提高。"
    assert any(r.bold for r in paras[0].runs)                 # the bold run survived


def test_insertion_and_deletion_via_replace(tmp_path):
    d = docx.Document()
    d.add_paragraph("训练后血糖下降。")
    src = tmp_path / "i.docx"
    d.save(src)
    doc = FieldDoc(src)
    assert doc.replace("血糖下降", "空腹血糖下降") == 1          # pure insertion
    assert doc.replace("训练后", "") == 1                          # pure deletion
    assert docx.Document(doc.save(tmp_path / "o.docx")).paragraphs[0].text == "空腹血糖下降。"
