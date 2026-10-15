"""Zotero citation fields inside .docx files: create, verify, compare. Field-safe by construction.

A Zotero citation in Word is a FIELD, not text:
    fldChar(begin) -> instrText(" ADDIN ZOTERO_ITEM CSL_CITATION {json} ", often split over many runs)
    -> fldChar(separate) -> display run ("[12]") -> fldChar(end)
The bibliography is ONE field (ADDIN ZOTERO_BIBL) spanning many paragraphs.

Rules this module follows (each one was learnt by breaking a real document):
  1. never rewrite a whole paragraph that contains fldChar / instrText — edit runs outside fields only
  2. never delete a paragraph that holds field markers (the bibliography end marker is easy to lose)
  3. never round-trip document.xml through ElementTree for writing: it hoists inline namespace declarations
     (Word declares xmlns:a, xmlns:pic ... on <a:graphic>) and drops unused ones -> "file is corrupt".
     Writes here are string-level splices of single runs; every other byte of the package is copied unchanged.
  4. display number = order of FIRST appearance in the text; numbers in one citation ascending; ranges with en dash
  5. citation sits BEFORE the sentence-final punctuation: "……呈下降趋势[16]。"
  6. after any write: verify() and compare_parts() (only word/document.xml may change)

Known false alarms of checkers (normalise before comparing): en dash vs hyphen in ranges; instrText split over
runs (join before searching); formattedCitation stores en dash as RTF "\\uc0\\u8211{}" (never compare that field).
"""
from __future__ import annotations

import hashlib
import html
import json
import random
import re
import string
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CSL_SCHEMA = "https://github.com/citation-style-language/schema/raw/master/csl-citation.json"
CITE_RE = re.compile(r"\[(\d+(?:\s*[-–—,，]\s*\d+)*)\]")
RUN_RE = re.compile(r"<w:r(?:\s[^>]*)?>.*?</w:r>", re.S)
PARA_RE = re.compile(r"<w:p(?:\s[^>]*)?>.*?</w:p>|<w:p(?:\s[^>]*)?/>", re.S)
BIB_HEAD = re.compile(r"^\s*(参考文献|參考文獻|references|bibliography|literature cited)\s*[:：]?\s*$", re.I)
END_PUNCT = "。．.！？!?；;"


def q(tag: str) -> str:
    return "{%s}%s" % (W, tag)


def read_document(path) -> str:
    with zipfile.ZipFile(path) as z:
        return z.read("word/document.xml").decode("utf-8")


def write_document(src, dst, new_xml: str) -> Path:
    """Copy every part byte-for-byte except word/document.xml."""
    src, dst = Path(src), Path(dst)
    if src.resolve() == dst.resolve():
        raise ValueError("write to a NEW file; keep the original as the backup")
    ET.fromstring(new_xml.encode("utf-8"))  # refuse to write malformed XML
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = new_xml.encode("utf-8") if item.filename == "word/document.xml" else zin.read(item.filename)
            zout.writestr(item, data)
    return dst


# ----------------------------------------------------------------------------- numbers
def expand(spec: str) -> List[int]:
    """'1,3–5' -> [1, 3, 4, 5]"""
    out: List[int] = []
    for part in re.split(r"\s*[,，]\s*", spec.strip()):
        m = re.match(r"^(\d+)\s*[-–—]\s*(\d+)$", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            out += list(range(a, b + 1)) if a <= b else [a, b]
        elif part.isdigit():
            out.append(int(part))
    return out


def compress(nums: Sequence[int]) -> str:
    """[1, 3, 4, 5] -> '[1,3–5]' (Zotero numeric style: ranges of >= 3 with en dash)."""
    ns = sorted(set(nums))
    parts, i = [], 0
    while i < len(ns):
        j = i
        while j + 1 < len(ns) and ns[j + 1] == ns[j] + 1:
            j += 1
        parts.append(f"{ns[i]}–{ns[j]}" if j - i >= 2 else ",".join(str(x) for x in ns[i:j + 1]))
        i = j + 1
    return "[" + ",".join(parts) + "]"


def norm_disp(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").replace("—", "–").replace("-", "–").replace("，", ","))


# ----------------------------------------------------------------------------- field construction
def _rand_id(k: int = 8) -> str:
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(k))


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _with_superscript(rpr: str) -> str:
    if "w:vertAlign" in rpr:
        return re.sub(r'<w:vertAlign w:val="[^"]*"/>', '<w:vertAlign w:val="superscript"/>', rpr)
    tag = '<w:vertAlign w:val="superscript"/>'
    if not rpr:
        return f"<w:rPr>{tag}</w:rPr>"
    for later in ("<w:rtl", "<w:cs/", "<w:cs ", "<w:em ", "<w:lang", "<w:eastAsianLayout", "<w:specVanish", "<w:oMath"):  # keep schema order
        k = rpr.find(later)
        if k >= 0:
            return rpr[:k] + tag + rpr[k:]
    return rpr.replace("</w:rPr>", tag + "</w:rPr>")


def citation_payload(nums: Sequence[int], display: str, items: Dict[int, Dict], user_id: str) -> Dict:
    cits = []
    for n in nums:
        it = items[n]
        data = {k: v for k, v in it["csl"].items() if not k.startswith("_")}
        iid = it.get("itemID") or (900000 + n)
        data["id"] = iid
        cits.append({"id": iid, "uris": [f"http://zotero.org/users/{user_id}/items/{it['key']}"], "itemData": data})
    return {"citationID": _rand_id(), "properties": {"formattedCitation": display, "plainCitation": display, "noteIndex": 0},
            "citationItems": cits, "schema": CSL_SCHEMA}


def citation_field_xml(payload: Dict, display: str, rpr: str) -> str:
    instr = " ADDIN ZOTERO_ITEM CSL_CITATION " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + " "
    return (f'<w:r>{rpr}<w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r>{rpr}<w:instrText xml:space="preserve">{_esc(instr)}</w:instrText></w:r>'
            f'<w:r>{rpr}<w:fldChar w:fldCharType="separate"/></w:r>'
            f'<w:r>{rpr}<w:t xml:space="preserve">{_esc(display)}</w:t></w:r>'
            f'<w:r>{rpr}<w:fldChar w:fldCharType="end"/></w:r>')


BIBL_BEGIN = ('<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> ADDIN ZOTERO_BIBL '
              '{&quot;uncited&quot;:[],&quot;omitted&quot;:[],&quot;custom&quot;:[]} CSL_BIBLIOGRAPHY </w:instrText></w:r>'
              '<w:r><w:fldChar w:fldCharType="separate"/></w:r>')
BIBL_END = '<w:r><w:fldChar w:fldCharType="end"/></w:r>'


def _para_text(pxml: str) -> str:
    return html.unescape("".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", pxml)))


def fieldify(src, dst, items: Dict[int, Dict], user_id: str, superscript: bool = False, dry_run: bool = False) -> Dict:
    """Turn plain-text citations "[n]", "[n,m]", "[n–m]" into Zotero citation fields and wrap the reference list
    (paragraphs starting with "[n]" after a 参考文献 / References heading) in one ZOTERO_BIBL field.

    items: {n: {"key": Zotero item key, "csl": CSL-JSON dict, "itemID": optional numeric id}} for every n in the list.
    Citations split across runs ("[", "12", "]") cannot be converted safely and are reported, not touched.
    """
    xml = read_document(src)
    if "ADDIN ZOTERO_ITEM" in xml or "ADDIN ZOTERO_BIBL" in xml:
        raise ValueError("document already contains Zotero fields; fieldify only converts plain-text citations")
    paras = [(m.start(), m.end(), m.group(0)) for m in PARA_RE.finditer(xml)]
    head = next((i for i, (_, _, p) in enumerate(paras) if BIB_HEAD.match(_para_text(p))), None)
    bib_start = paras[head][1] if head is not None else len(xml)
    entries: List[int] = []
    if head is not None:
        for i in range(head + 1, len(paras)):
            t = _para_text(paras[i][2]).strip()
            if re.match(r"^\[\d+\]", t):
                entries.append(i)
            elif t and entries:
                break
    report = dict(converted=0, citations=[], missing=[], not_converted=[], skipped_runs=[], bib_entries=len(entries), bib_heading=head is not None)
    # ---- citations (string splice per run, back to front so offsets stay valid)
    ops: List[Tuple[int, int, str]] = []
    ncit: Dict[int, int] = {}
    depth = 0
    for m in RUN_RE.finditer(xml, 0, bib_start):
        r = m.group(0)
        for t in re.findall(r'w:fldCharType="(begin|end)"', r):
            depth += 1 if t == "begin" else -1
        if depth > 0 or "<w:fldChar" in r or "<w:instrText" in r:
            continue
        ts = re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", r)
        text = "".join(ts)
        if not CITE_RE.search(html.unescape(text)):
            continue
        body = re.sub(r"<w:rPr>.*?</w:rPr>", "", r[r.index(">") + 1:-len("</w:r>")], flags=re.S)
        if len(ts) != 1 or re.sub(r"<w:t(?:\s[^>]*)?>[^<]*</w:t>", "", body).strip():
            report["skipped_runs"].append(html.unescape(text)[:60])
            continue
        rpr_m = re.search(r"<w:rPr>.*?</w:rPr>", r, re.S)
        rpr = rpr_m.group(0) if rpr_m else ""
        frpr = _with_superscript(rpr) if superscript else rpr
        open_tag = r[:r.index(">") + 1]
        out, pos, raw = [], 0, ts[0]
        for cm in CITE_RE.finditer(raw):
            nums = expand(cm.group(1))
            miss = [n for n in nums if n not in items]
            if miss:
                report["missing"] += miss
                continue
            disp = html.unescape(cm.group(0))
            if raw[pos:cm.start()]:
                out.append(f'{open_tag}{rpr}<w:t xml:space="preserve">{raw[pos:cm.start()]}</w:t></w:r>')
            out.append(citation_field_xml(citation_payload(nums, disp, items, user_id), disp, frpr))
            report["citations"].append(dict(display=disp, numbers=nums))
            pos = cm.end()
        if pos == 0:
            continue
        if raw[pos:]:
            out.append(f'{open_tag}{rpr}<w:t xml:space="preserve">{raw[pos:]}</w:t></w:r>')
        ops.append((m.start(), m.end(), "".join(out)))
        ncit[m.start()] = sum(1 for x in out if "ZOTERO_ITEM" in x)
    # citations visible in the paragraph text but not converted (split over runs, unknown number, mixed run)
    for s, e, p in paras:
        if s >= bib_start:
            break
        n_txt = len(CITE_RE.findall(_para_text(p)))
        if n_txt > sum(v for a, v in ncit.items() if s <= a < e):
            report["not_converted"].append(_para_text(p)[:80])
    # ---- bibliography wrapper
    if entries:
        fs, fe, fp = paras[entries[0]]
        k = fp.find("</w:pPr>")
        ins = fs + (k + len("</w:pPr>") if k >= 0 else fp.index(">") + 1)
        ls, le, lp = paras[entries[-1]]
        ops.append((ins, ins, BIBL_BEGIN))
        ops.append((le - len("</w:p>"), le - len("</w:p>"), BIBL_END))
    report["converted"] = len(report["citations"])
    report["missing"] = sorted(set(report["missing"]))
    if dry_run:
        return report
    new = xml
    for a, b, rep in sorted(ops, key=lambda o: (o[0], o[1]), reverse=True):
        new = new[:a] + rep + new[b:]
    write_document(src, dst, new)
    report["output"] = str(dst)
    return report


# ----------------------------------------------------------------------------- reading fields
def _tokens(xml: str) -> List[Dict]:
    """Document-order token stream per paragraph: text pieces and complete fields (instr + display)."""
    root = ET.fromstring(xml.encode("utf-8"))
    out = []
    for pi, p in enumerate(root.iter(q("p"))):
        depth, instr, disp, phase = 0, "", "", None
        toks: List[Dict] = []
        for el in p.iter():
            if el.tag == q("fldChar"):
                t = el.get(q("fldCharType"))
                if t == "begin":
                    depth += 1
                    if depth == 1:
                        instr, disp, phase = "", "", "instr"
                elif t == "separate" and depth == 1:
                    phase = "disp"
                elif t == "end":
                    if depth == 1:
                        toks.append(dict(kind="field", instr=instr.strip(), display=disp))
                        phase = None
                    depth = max(0, depth - 1)
            elif el.tag == q("instrText") and depth >= 1 and phase == "instr":
                instr += el.text or ""
            elif el.tag == q("t"):
                if depth >= 1 and phase == "disp":
                    disp += el.text or ""
                elif depth == 0:
                    toks.append(dict(kind="text", text=el.text or ""))
            elif el.tag == q("tab") and depth == 0:
                toks.append(dict(kind="text", text="\t"))
        out.append(dict(index=pi, tokens=toks, open_depth=depth))
    return out


def field_counts(xml: str) -> Dict[str, int]:
    c = lambda pat: len(re.findall(pat, xml))
    return dict(begin=c(r'w:fldCharType="begin"'), separate=c(r'w:fldCharType="separate"'), end=c(r'w:fldCharType="end"'),
                instrText=c(r"<w:instrText"), ZOTERO_ITEM=c(r"ADDIN ZOTERO_ITEM"), ZOTERO_BIBL=c(r"ADDIN ZOTERO_BIBL"))


def verify(path) -> Dict:
    """Full machine check of Zotero fields. Every count in `problems` must be 0 before delivery."""
    xml = read_document(path)
    cnt = field_counts(xml)
    paras = _tokens(xml)
    probs: Dict[str, List] = {k: [] for k in ("unbalanced_fields", "json_errors", "duplicate_citation_id", "plain_vs_display", "display_vs_first_order",
                                               "after_punctuation", "adjacent_fields", "empty_display", "bib_numbering", "bib_missing_tab",
                                               "bib_title_mismatch", "cited_not_listed", "listed_not_cited")}
    if not (cnt["begin"] == cnt["separate"] == cnt["end"]):
        probs["unbalanced_fields"].append(cnt)
    order: Dict[str, int] = {}
    titles: Dict[str, str] = {}
    ids: List[str] = []
    n_cit = 0
    for p in paras:
        toks = p["tokens"]
        for k, t in enumerate(toks):
            if t["kind"] != "field" or not t["instr"].startswith("ADDIN ZOTERO_ITEM"):
                continue
            n_cit += 1
            raw = t["instr"][len("ADDIN ZOTERO_ITEM"):].strip()
            raw = raw[len("CSL_CITATION"):].strip() if raw.startswith("CSL_CITATION") else raw
            try:
                d = json.loads(raw)
            except json.JSONDecodeError as e:
                probs["json_errors"].append(dict(paragraph=p["index"], error=str(e)[:80]))
                continue
            ids.append(d.get("citationID"))
            if not t["display"].strip():
                probs["empty_display"].append(p["index"])
            plain = d.get("properties", {}).get("plainCitation", "")
            if norm_disp(plain) != norm_disp(t["display"]):
                probs["plain_vs_display"].append(dict(paragraph=p["index"], plain=plain, display=t["display"]))
            nums = []
            for ci in d.get("citationItems", []):
                u = (ci.get("uris") or ci.get("uri") or [str(ci.get("id"))])[0]
                if u not in order:
                    order[u] = len(order) + 1
                    titles[u] = (ci.get("itemData") or {}).get("title", "")
                nums.append(order[u])
            if nums and norm_disp(compress(nums)) != norm_disp(t["display"]):
                probs["display_vs_first_order"].append(dict(paragraph=p["index"], display=t["display"], expected=compress(nums)))
            before = "".join(x.get("text", "") for x in toks[:k] if x["kind"] == "text").rstrip()
            if before and before[-1] in END_PUNCT and not re.search(r"(et al|e\.g|i\.e|etc)\.$", before):
                probs["after_punctuation"].append(dict(paragraph=p["index"], context=before[-20:] + t["display"]))
            if k > 0 and toks[k - 1]["kind"] == "field" and toks[k - 1]["instr"].startswith("ADDIN ZOTERO_ITEM"):
                probs["adjacent_fields"].append(dict(paragraph=p["index"], displays=[toks[k - 1]["display"], t["display"]]))
    dup = [k for k, v in Counter(ids).items() if v > 1]
    if dup:
        probs["duplicate_citation_id"] = dup
    # bibliography: text of paragraphs inside the BIBL field
    bib = _bib_entries(xml)
    nums_b = [b["num"] for b in bib if b["num"] is not None]
    if bib:
        if nums_b != list(range(1, len(nums_b) + 1)):
            probs["bib_numbering"].append(nums_b[:200])
        probs["bib_missing_tab"] = [b["num"] for b in bib if not b["tab"]]
        by_num = {v: u for u, v in order.items()}
        for b in bib:
            u = by_num.get(b["num"])
            if u and titles.get(u):
                tt = re.sub(r"\W+", "", titles[u].lower())[:24]
                if tt and tt not in re.sub(r"\W+", "", b["text"].lower()):
                    probs["bib_title_mismatch"].append(dict(num=b["num"], expected_title=titles[u][:60], entry=b["text"][:80]))
        probs["cited_not_listed"] = [n for n in range(1, len(order) + 1) if n not in nums_b]
        probs["listed_not_cited"] = [n for n in nums_b if n > len(order)]
    summary = {k: len(v) if isinstance(v, list) else v for k, v in probs.items()}
    return dict(file=str(path), counts=cnt, n_citation_fields=n_cit, n_items_cited=len(order), n_bib_entries=len(bib),
                ok=all(v == 0 for v in summary.values()), summary=summary, problems=probs)


def _bib_entries(xml: str) -> List[Dict]:
    k = xml.find("ADDIN ZOTERO_BIBL")
    if k < 0:
        return []
    # the BIBL field ends at the first fldChar end at depth 0 after its begin
    begin = xml.rfind('w:fldCharType="begin"', 0, k)
    depth, pos, end = 0, begin, len(xml)
    for m in re.finditer(r'w:fldCharType="(begin|end)"', xml[begin:]):
        depth += 1 if m.group(1) == "begin" else -1
        if depth == 0:
            end = begin + m.end()
            break
    seg = xml[xml.rfind("<w:p", 0, begin):end]
    out = []
    for p in PARA_RE.finditer(seg + "</w:p>"):
        t = _para_text(p.group(0)).strip()
        if not t:
            continue
        m = re.match(r"^\[(\d+)\]", t)
        out.append(dict(num=int(m.group(1)) if m else None, text=t, tab=bool(re.search(r"\](?:</w:t>)(?:(?!<w:t[ >]).)*?<w:tab/>", p.group(0), re.S))))
    return out


def verify_md(rep: Dict) -> str:
    names = {"unbalanced_fields": "fldChar begin/separate/end 不相等", "json_errors": "载荷 JSON 解析失败", "duplicate_citation_id": "citationID 重复",
             "plain_vs_display": "plainCitation ≠ 屏幕显示", "display_vs_first_order": "显示编号 ≠ 首次出现顺序", "after_punctuation": "引文在句末标点之后",
             "adjacent_fields": "同段相邻两个引文域之间无正文", "empty_display": "域显示为空", "bib_numbering": "文献表编号不连续",
             "bib_missing_tab": "文献表编号后缺制表符", "bib_title_mismatch": "文献表条目与引文题名错位", "cited_not_listed": "引而未列",
             "listed_not_cited": "列而未引"}
    L = [f"# 引文域校验：{Path(rep['file']).name}", "", f"- 域计数：{rep['counts']}", f"- 引文域 {rep['n_citation_fields']} 个，引用文献 {rep['n_items_cited']} 篇，文献表 {rep['n_bib_entries']} 条",
         f"- 结论：{'全部通过 ✔' if rep['ok'] else '存在问题 ✘（任何一项不为 0 都要就地修）'}", "", "| 检查项 | 问题数 |", "|---|---|"]
    L += [f"| {names[k]} | {v} |" for k, v in rep["summary"].items()]
    for k, v in rep["problems"].items():
        if v:
            L += ["", f"## {names[k]}", "", "```", json.dumps(v[:20] if isinstance(v, list) else v, ensure_ascii=False, indent=1), "```"]
    L += ["", "> 报告“N 处不一致”之前，先人工展开第一条核对：校验脚本也会误报（en dash、instrText 被拆分等）。"]
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------------------- comparisons
def compare_parts(a, b) -> Dict:
    """Which package parts differ between two .docx files (normally only word/document.xml may change)."""
    with zipfile.ZipFile(a) as za, zipfile.ZipFile(b) as zb:
        na, nb = set(za.namelist()), set(zb.namelist())
        changed = sorted(n for n in na & nb if za.read(n) != zb.read(n))
    return dict(missing_in_new=sorted(na - nb), added_in_new=sorted(nb - na), changed=changed,
                only_document_changed=not (na ^ nb) and set(changed) <= {"word/document.xml"})


def field_diff(a, b) -> Dict:
    """Field structure before/after an edit: counts and the ordered list of field instructions must match
    (unless fields were added on purpose)."""
    xa, xb = read_document(a), read_document(b)
    fa = [t["instr"][:40] for p in _tokens(xa) for t in p["tokens"] if t["kind"] == "field"]
    fb = [t["instr"][:40] for p in _tokens(xb) for t in p["tokens"] if t["kind"] == "field"]
    first = next((i for i, (x, y) in enumerate(zip(fa, fb)) if x != y), None if len(fa) == len(fb) else min(len(fa), len(fb)))
    return dict(counts_before=field_counts(xa), counts_after=field_counts(xb), identical=fa == fb, first_difference=first)


def diagnose(path) -> Dict:
    xml = read_document(path)
    with zipfile.ZipFile(path) as z:
        parts = {n: z.getinfo(n).file_size for n in z.namelist()}
    i = xml.find("<w:document")
    head = xml[i:xml.index(">", i) + 1] if i >= 0 else ""
    return dict(counts=field_counts(xml), paragraphs=len(re.findall(r"<w:p[ >]", xml)), tables=len(re.findall(r"<w:tbl[ >]", xml)),
                vml_pictures=len(re.findall(r"<w:pict\b", xml)), drawings=len(re.findall(r"<w:drawing\b", xml)),
                root_tag_len=len(head), root_xmlns=len(re.findall(r"xmlns:", head)), mc_ignorable=bool(re.search(r"mc:Ignorable=", head)),
                md5=hashlib.md5(Path(path).read_bytes()).hexdigest(), parts=parts)
