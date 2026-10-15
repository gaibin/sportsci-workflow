# -*- coding: utf-8 -*-
"""Command line, offline: parse / format / fieldify / verify / edit / renumber / compare on a synthetic document."""
import json
from pathlib import Path

import pytest

docx = pytest.importorskip("docx")
from typer.testing import CliRunner

from sportsci_refs.cli import app
from sportsci_refs.docx_fields import verify
from sportsci_refs.fieldedit import FieldDoc

REFS = """[1] 张三, 李四. 抗阻训练对2型糖尿病患者血糖控制的影响[J]. 体育科学, 2021, 41(3): 45-53.
[2] Colberg S R, Sigal R J. Physical activity/exercise and diabetes[J]. Diabetes Care, 2016, 39(11): 2065-2079.
[3] 赵六. 青少年体质健康促进研究[D]. 北京: 北京体育大学, 2019."""
run = CliRunner().invoke


def test_parse_then_format_roundtrip(tmp_path):
    (tmp_path / "refs.txt").write_text(REFS, encoding="utf-8")
    r = run(app, ["parse", str(tmp_path / "refs.txt"), "-o", str(tmp_path / "out")])
    assert r.exit_code == 0 and "3 entries" in r.output
    assert (tmp_path / "out.ris").exists() and json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))[0]["title"].startswith("抗阻训练")
    r = run(app, ["format", str(tmp_path / "out.json"), "-o", str(tmp_path / "list.txt")])
    assert r.exit_code == 0
    assert (tmp_path / "list.txt").read_text(encoding="utf-8").splitlines()[2].startswith("[3] 赵六. 青少年体质健康促进研究[D]. 北京: 北京体育大学, 2019")


def test_fieldify_edit_renumber_verify_chain(tmp_path, monkeypatch):
    d = docx.Document()
    d.add_paragraph("抗阻训练改善血糖控制[2]，同时提高肌肉质量[1]。")
    d.add_paragraph("相关研究提示结论一致[3]。")
    d.add_paragraph("参考文献")
    for line in REFS.splitlines():
        d.add_paragraph(line)
    src = tmp_path / "t.docx"
    d.save(src)
    from sportsci_refs import parse_gbt_list
    recs = parse_gbt_list(REFS)
    match = {"mapping": {str(i + 1): {"key": f"KEY{i + 1:05d}", "csl": r} for i, r in enumerate(recs)}}
    (tmp_path / "m.json").write_text(json.dumps(match, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv("ZOTERO_USER_ID", "42")

    r = run(app, ["fieldify", str(src), "-m", str(tmp_path / "m.json"), "-o", str(tmp_path / "f.docx")])
    assert r.exit_code == 0 and "converted 3 citations" in r.output
    r = run(app, ["edit", str(tmp_path / "f.docx"), "-r", "提高肌肉质量=>增加肌肉质量", "-r", "不存在的词=>x", "-o", str(tmp_path / "e.docx")])
    assert r.exit_code == 0 and "1 x" in r.output and "not found" in r.output
    assert "增加肌肉质量" in "".join(FieldDoc(tmp_path / "e.docx").plain(i) for i in range(len(FieldDoc(tmp_path / "e.docx").paragraphs)))
    # "[2]" appears before "[1]" in the text, so the typed numbers are not in order of first appearance: verify must say so ...
    assert verify(tmp_path / "e.docx")["summary"]["display_vs_first_order"] == 2
    r = run(app, ["renumber", str(tmp_path / "e.docx"), "-o", str(tmp_path / "n.docx")])
    assert r.exit_code == 0 and "citations renumbered" in r.output
    s = verify(tmp_path / "n.docx")["summary"]
    assert s["display_vs_first_order"] == 0 and s["plain_vs_display"] == 0 and s["json_errors"] == 0
    r = run(app, ["compare", str(tmp_path / "f.docx"), str(tmp_path / "n.docx")])
    assert r.exit_code == 0 and "word/document.xml" in r.output and "field sequence identical: True" in r.output


def test_status_without_zotero_is_a_clear_message(monkeypatch):
    monkeypatch.setenv("ZOTERO_API", "http://127.0.0.1:1")      # closed port: connection refused, not a proxy 502
    r = run(app, ["status"])
    assert r.exit_code == 0 and "Zotero" in r.output


def test_edit_rejects_malformed_rule(tmp_path):
    d = docx.Document()
    d.add_paragraph("x")
    d.save(tmp_path / "a.docx")
    r = run(app, ["edit", str(tmp_path / "a.docx"), "-r", "no-arrow"])
    assert r.exit_code == 1
