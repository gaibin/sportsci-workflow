#!/usr/bin/env python3
"""Finalize a manuscript .docx before it is handed to anyone: human-style numbers and spaces, journal fonts, font
sizes and line spacing. Rules: references/docx-delivery.md.

    python docx_finalize.py in.docx                 # writes in place
    python docx_finalize.py in.docx -o out.docx
    python docx_finalize.py in.docx --check         # only report problems, change nothing
    python docx_finalize.py notes.md                # text-only fixes for .md / .txt

What it does
  text      4-digit numbers without separator (6045), 5+ digits with a thousands comma (33,987) in Chinese text,
            commas from 1,000 up in English text; no space between a Chinese character and a Latin letter, digit,
            or full-width punctuation; no space around < > = inside Chinese text; caption labels "表1　…" / "图1　…";
            heading numbers followed by one full-width space; no double spaces.
  layout    Chinese 宋体 + English Times New Roman; title 小三 黑体; level-1 heading 四号 黑体, level-2 小四 黑体,
            level-3 小四 宋体 bold; body 小四, 1.5 line spacing, 2-character first-line indent; figure paragraphs single
            spacing and centred (1.5 spacing would add half a picture height of white space); captions, table cells and
            table notes 五号 / 小五 single spacing, wide tables autofit to the page; references 小四 without indent.

Personal settings such as document metadata are not part of this script. If a git-ignored file
docx_metadata.local.py sits next to it, finalize() calls its apply(path) after the layout pass.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

CJK = r'一-鿿㐀-䶿'
FULLPUNCT = '，。、；：？！（）【】《》“”‘’…～'
ZH_FONT, EN_FONT, HEI = '宋体', 'Times New Roman', '黑体'
PT = {'小三': 15, '四号': 14, '小四': 12, '五号': 10.5, '小五': 9}


# ------------------------------------------------------------------ text
def is_zh(text: str) -> bool:
    letters = re.findall(rf'[{CJK}A-Za-z]', text)
    return bool(letters) and sum(bool(re.match(rf'[{CJK}]', c)) for c in letters) / len(letters) > 0.2


def _group(digits: str, zh: bool) -> str:
    if zh:
        return digits if len(digits) <= 4 else f'{int(digits):,}'
    return f'{int(digits):,}' if len(digits) >= 4 else digits


def fix_numbers(t: str, zh: bool) -> str:
    # space / thin space / nbsp separated groups:  6 045, 33 987
    t = re.sub(r'(?<![\d.,])(\d{1,3})((?:[    ]\d{3})+)(?![\d])',
               lambda m: _group(m.group(1) + re.sub(r'\D', '', m.group(2)), zh), t)
    # comma separated groups:  6,045  33,987
    t = re.sub(r'(?<![\d.,])\d{1,3}(?:,\d{3})+(?![\d,])', lambda m: _group(m.group(0).replace(',', ''), zh), t)
    if not zh:   # English: 4+ digit integers get a comma, except years and page-like numbers handled by caller
        pass
    return t


def fix_spaces_zh(t: str) -> str:
    t = re.sub(rf'(?<=[{CJK}])[  ]+(?=[A-Za-z0-9(\[<>=])', '', t)
    t = re.sub(rf'(?<=[A-Za-z0-9)\]%])[  ]+(?=[{CJK}])', '', t)
    t = re.sub(rf'[  ]+(?=[{FULLPUNCT}])', '', t)
    t = re.sub(rf'(?<=[{FULLPUNCT}])[  ]+', '', t)
    t = re.sub(r'(?<=[A-Za-z])\s*([<>=≤≥])\s*(?=[\d.−-])', r'\1', t)   # P < 0.05 -> P<0.05 (Chinese prose)
    t = re.sub(r' {2,}', ' ', t)
    return t


def fix_captions_headings(t: str) -> str:
    t = re.sub(r'^(表|图|附表|附图)\s*(S?\d+[a-z]?)\s*[ 　]*', lambda m: f'{m.group(1)}{m.group(2)}　', t)
    t = re.sub(rf'^(\d+(?:\.\d+){{0,3}})[ 　]+(?=[{CJK}])', lambda m: f'{m.group(1)}　', t)
    return t


def is_english(text: str) -> bool:
    """A paragraph written in English (abstract, keywords, English reference)."""
    return not re.search(rf'[{CJK}]', text) and len(re.findall(r'[A-Za-z]{3,}', text)) >= 4


def fix_text(t: str, zh: bool | None = None) -> str:
    if not t.strip():
        return t
    if zh is None:
        zh = not is_english(t)
    t = fix_numbers(t, zh)
    if zh:
        t = fix_captions_headings(t)
        t = fix_spaces_zh(t)
    else:
        t = re.sub(r' {2,}', ' ', t)
    return t


# ------------------------------------------------------------------ docx
def _set_run_font(run, size=None, bold=None, east=ZH_FONT):
    from docx.oxml.ns import qn
    from docx.shared import Pt
    run.font.name = EN_FONT
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = rpr.makeelement(qn('w:rFonts'), {}); rpr.insert(0, rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:cs'):
        rf.set(qn(a), EN_FONT)
    rf.set(qn('w:eastAsia'), east)
    if size: run.font.size = Pt(size)
    if bold is not None: run.font.bold = bold


def _spacing(p, line=1.5, before=0, after=0, indent_chars=None, align=None):
    from docx.shared import Pt
    from docx.enum.text import WD_LINE_SPACING
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE if line != 1 else WD_LINE_SPACING.SINGLE
    pf.line_spacing = line
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    if indent_chars is not None:
        from docx.oxml.ns import qn
        ppr = p._element.get_or_add_pPr()
        ind = ppr.find(qn('w:ind'))
        if ind is None:
            ind = ppr.makeelement(qn('w:ind'), {}); ppr.append(ind)
        for a in list(ind.attrib):
            ind.attrib.pop(a)
        if indent_chars:
            ind.set(qn('w:firstLineChars'), str(indent_chars * 100))
    if align is not None:
        p.alignment = align


def _replace_runs_text(p, doc_zh=True):
    """Fix text run by run with the paragraph's language, then the caption label split over two runs."""
    zh = doc_zh and not is_english(p.text)
    for r in p.runs:
        if r.text:
            r.text = fix_text(r.text, zh)
    full = p.text
    if len(p.runs) > 1 and zh and len(p.runs[0].text.strip()) <= 6 and re.match(r'^(表|图|附表|附图)\s*S?\d', full):
        lab = re.sub(r'[ 　]+$', '', p.runs[0].text)
        p.runs[0].text = re.sub(r'^(表|图|附表|附图)\s*(S?\d+[a-z]?)$', lambda m: f'{m.group(1)}{m.group(2)}　', lab)
        if len(p.runs) > 1:
            p.runs[1].text = p.runs[1].text.lstrip(' 　')
    elif len(p.runs) == 1 and fix_text(full, zh) != full:
        p.runs[0].text = fix_text(full, zh)


def _autofit(tb):
    """Let Word size columns to their content within the page width (fixed narrow first columns wrap every label)."""
    from docx.oxml.ns import qn
    tbl = tb._tbl
    tblPr = tbl.tblPr
    w = tblPr.find(qn('w:tblW'))
    if w is None:
        w = tblPr.makeelement(qn('w:tblW'), {}); tblPr.append(w)
    w.set(qn('w:type'), 'pct'); w.set(qn('w:w'), '5000')
    lay = tblPr.find(qn('w:tblLayout'))
    if lay is not None:
        tblPr.remove(lay)
    for tc in tbl.iter(qn('w:tc')):
        pr = tc.tcPr
        if pr is not None:
            for cw in pr.findall(qn('w:tcW')):
                cw.set(qn('w:type'), 'auto'); cw.set(qn('w:w'), '0')
    grid = tbl.find(qn('w:tblGrid'))
    if grid is not None:
        for gc in grid.findall(qn('w:gridCol')):
            gc.attrib.pop(qn('w:w'), None)


def layout(doc, doc_zh=True):
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    body = doc.element.body
    first = True
    after_table = False
    in_refs = False
    for el in body.iterchildren():
        if el.tag.endswith('}tbl'):
            from docx.table import Table
            tb = Table(el, doc)
            ncol = len(tb.columns)
            _autofit(tb)
            for row in tb.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        _replace_runs_text(p, doc_zh)
                        _spacing(p, 1, 0, 0, indent_chars=0)
                        for r in p.runs:
                            _set_run_font(r, PT['小五'] if ncol >= 6 else PT['五号'])
            after_table = True
            continue
        if not el.tag.endswith('}p'):
            continue
        from docx.text.paragraph import Paragraph
        p = Paragraph(el, doc)
        _replace_runs_text(p, doc_zh)
        t = p.text.strip()
        has_pic = bool(el.findall('.//' + qn('w:drawing')))
        if not t and not has_pic:
            after_table = False
            continue
        if has_pic:
            _spacing(p, 1, 6, 0, indent_chars=0, align=WD_ALIGN_PARAGRAPH.CENTER)
        elif first:
            _spacing(p, 1.5, 0, 12, indent_chars=0, align=WD_ALIGN_PARAGRAPH.CENTER)
            for r in p.runs: _set_run_font(r, PT['小三'], True, HEI)
            first = False
        elif re.match(r'^(表|图|附表|附图)S?\d+[a-z]?　', t):
            _spacing(p, 1, 6 if t.startswith(('表', '附表')) else 2, 6, indent_chars=0, align=WD_ALIGN_PARAGRAPH.CENTER)
            for i, r in enumerate(p.runs): _set_run_font(r, PT['五号'], True if i == 0 else None)
        elif after_table:
            _spacing(p, 1, 2, 6, indent_chars=0)
            for r in p.runs: _set_run_font(r, PT['小五'])
        elif re.match(r'^\d+　', t) and len(t) <= 20 or t in ('参考文献', '附录', '结论', '讨论', '摘要', '中文摘要', 'Abstract', '附录：补充表', '补充材料'):
            _spacing(p, 1.5, 12, 6, indent_chars=0)
            for r in p.runs: _set_run_font(r, PT['四号'], True, HEI)
            in_refs = t == '参考文献'
        elif re.match(r'^\d+\.\d+　', t) and len(t) <= 24:
            _spacing(p, 1.5, 6, 0, indent_chars=0)
            for r in p.runs: _set_run_font(r, PT['小四'], True, HEI)
        elif re.match(r'^\d+\.\d+\.\d+　', t) and len(t) <= 28:
            _spacing(p, 1.5, 6, 0, indent_chars=0)
            for r in p.runs: _set_run_font(r, PT['小四'], True)
        elif re.match(r'^\[\d+\]', t) or in_refs:
            _spacing(p, 1.5, 0, 0, indent_chars=0)
            for r in p.runs: _set_run_font(r, PT['小四'])
        elif not (doc_zh and not is_english(t)) and len(t) < 250 and not re.search(r'[.:;]$', t) and not re.match(r'^(Abstract|Keywords)', t):
            _spacing(p, 1.5, 6, 6, indent_chars=0, align=WD_ALIGN_PARAGRAPH.CENTER)
            for r in p.runs: _set_run_font(r, PT['小四'], True)
        elif re.match(r'^(摘\s*要|关键词|Abstract|Keywords|英文题目)', t):
            _spacing(p, 1.5, 0, 6, indent_chars=0)
            for r in p.runs: _set_run_font(r, PT['小四'])
        else:
            _spacing(p, 1.5, 0, 0, indent_chars=2)
            for r in p.runs: _set_run_font(r, PT['小四'])
        after_table = False
    # default style fonts so new text typed by the author also comes out right
    st = doc.styles['Normal']
    st.font.name = EN_FONT
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = rpr.makeelement(qn('w:rFonts'), {}); rpr.insert(0, rf)
    rf.set(qn('w:eastAsia'), ZH_FONT)


def _local_hook():
    """Personal settings (document metadata) live in a git-ignored file next to this script, if present."""
    import importlib.util
    f = Path(__file__).with_name('docx_metadata.local.py')
    if not f.is_file():
        return None
    spec = importlib.util.spec_from_file_location('docx_metadata_local', f)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def finalize(src: Path, out: Path | None = None, do_layout: bool = True, **local_kw) -> Path:
    import docx
    out = out or src
    if out != src:
        shutil.copy(src, out)
    d = docx.Document(str(out))
    doc_zh = sum(bool(re.search(rf'[{CJK}]', p.text)) for p in d.paragraphs[:40]) > 3
    if do_layout:
        layout(d, doc_zh)
    else:
        for p in d.paragraphs:
            _replace_runs_text(p, doc_zh)
    d.save(str(out))
    hook = _local_hook()
    if hook is not None:
        hook.apply(out, **local_kw)
    return out


def check(path: Path) -> list[str]:
    """Report leftover problems in a .docx or text file."""
    probs = []
    if path.suffix.lower() == '.docx':
        import docx
        d = docx.Document(str(path))
        texts = [p.text for p in d.paragraphs] + [c.text for t in d.tables for r in t.rows for c in r.cells]
        hook = _local_hook()
        if hook is not None and hasattr(hook, 'check'):
            probs += hook.check(path)
    else:
        texts = path.read_text(encoding='utf-8').splitlines()
    pats = [(r'(?<![\d.,])\d{1,3}[    ]\d{3}(?!\d)', 'space inside a number'),
            (rf'[{CJK}][  ][A-Za-z0-9]|[A-Za-z0-9%)][  ][{CJK}]', 'space between Chinese and Latin/digit'),
            (r'(表|图) \d', 'space between 表/图 and its number'),
            (r'  ', 'double space')]
    for t in texts:
        for pat, lab in pats:
            if lab == 'space between Chinese and Latin/digit' and not is_zh(t):
                continue
            for m in re.finditer(pat, t):
                if lab == 'space between Chinese and Latin/digit' and re.match(r'^\d+(\.\d+)*\s', t) and m.start() < 8:
                    continue
                probs.append(f'{lab}: …{t[max(0, m.start() - 8):m.end() + 8]}…')
        if is_zh(t):
            for m in re.finditer(r'(?<![\d.,])\d{1,3},\d{3}(?![\d,])', t):
                if len(m.group(0).replace(',', '')) == 4:
                    probs.append(f'comma in a 4-digit number: …{t[max(0, m.start() - 8):m.end() + 8]}…')
    return probs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('file')
    ap.add_argument('-o', '--out')
    ap.add_argument('--no-layout', action='store_true', help='fix text and metadata only, keep fonts and spacing')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv)
    src = Path(a.file)
    if a.check:
        probs = check(src)
        print('\n'.join(probs) if probs else 'clean')
        return 1 if probs else 0
    if src.suffix.lower() == '.docx':
        out = finalize(src, Path(a.out) if a.out else None, do_layout=not a.no_layout)
    else:
        out = Path(a.out) if a.out else src
        out.write_text('\n'.join(fix_text(l) for l in src.read_text(encoding='utf-8').splitlines()) + '\n', encoding='utf-8')
    probs = check(out)
    print(f'{out}: ' + ('clean' if not probs else f'{len(probs)} issue(s)\n' + '\n'.join(probs)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
