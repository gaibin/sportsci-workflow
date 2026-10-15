"""Field-safe editing of .docx files that already contain Zotero fields.

Why this module exists
----------------------
In a Word document a Zotero citation is not text but a FIELD made of several runs:

    fldChar(begin) -> instrText(" ADDIN ZOTERO_ITEM CSL_CITATION {json} ")   (often split over many runs)
    -> fldChar(separate) -> display run ("[12]") -> fldChar(end)

and the whole bibliography is one field (ADDIN ZOTERO_BIBL) spanning dozens of paragraphs. The classic way to edit such a paragraph —
"delete every run, append one run with the new text" — silently destroys every citation in it: no error, the text still looks right,
only the field counts reveal it. A paragraph of 70 runs typically has only 25 plain-text runs; the other 45 belong to fields.

Rules this module enforces
--------------------------
  * only runs OUTSIDE fields are ever edited; field runs and everything inside a field (including the bibliography paragraphs) are untouched
  * field depth is tracked across the whole document, so a bibliography paragraph is recognised as "inside a field" even though
    its begin / end markers sit in other paragraphs
  * text is matched inside one stretch of plain runs, never across a field: "trend" + [16] + "." can not be matched as "trend."
  * an anchor must be unique, otherwise the edit is refused (an ambiguous anchor silently lands in the wrong place)
  * every other part of the package is copied byte for byte; `save()` refuses to overwrite the source and refuses to write a document
    whose field counts changed (unless you say so explicitly)

Typical use
-----------
    from sportsci_refs.fieldedit import FieldDoc

    doc = FieldDoc("thesis_zotero.docx")
    doc.replace("下降趋势", "降低趋势")                       # plain text only, fields stay intact
    ok, msg = doc.insert_after_anchor(par_idx, "显著提高", group.elements)   # move a citation group
    doc.refresh_numbers()                                  # displayed numbers = order of first appearance
    doc.save("thesis_v2.docx")                             # then: sportsci-refs verify thesis_v2.docx
"""
from __future__ import annotations

import copy
import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from lxml import etree

from .docx_fields import compress, norm_disp

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
CIT_PREFIX = "ADDIN ZOTERO_ITEM"
_TRANSPARENT = {"pPr", "bookmarkStart", "bookmarkEnd", "proofErr", "permStart", "permEnd", "commentRangeStart", "commentRangeEnd"}


def q(tag: str) -> str:
    return "{%s}%s" % (W, tag)


def _local(el) -> str:
    return el.tag.split("}")[-1] if isinstance(el.tag, str) and "}" in el.tag else str(el.tag)


# ----------------------------------------------------------------------------- run helpers
def run_text(r) -> str:
    return "".join(t.text or "" for t in r.findall(q("t")))


def set_run_text(r, text: str) -> None:
    ts = r.findall(q("t"))
    if not ts:
        ts = [etree.SubElement(r, q("t"))]
    ts[0].text = text
    ts[0].set(XML_SPACE, "preserve")
    for extra in ts[1:]:
        r.remove(extra)


def _is_text_run(r) -> bool:
    kids = [k for k in r if _local(k) not in ("rPr", "lastRenderedPageBreak")]
    return bool(kids) and all(_local(k) == "t" for k in kids)


@dataclass
class Span:
    """One complete field inside a paragraph (begin ... end)."""
    elements: List[etree._Element]
    instr: str
    display: str

    @property
    def kind(self) -> str:
        s = self.instr.strip()
        if s.startswith(CIT_PREFIX):
            return "citation"
        if s.startswith("ADDIN ZOTERO_BIBL"):
            return "bibliography"
        return s.split(" ")[0].upper() if s else "field"

    @property
    def payload(self) -> Optional[dict]:
        if self.kind != "citation":
            return None
        i, j = self.instr.find("{"), self.instr.rfind("}")
        if i < 0 or j < i:
            return None
        try:
            return json.loads(self.instr[i:j + 1])
        except json.JSONDecodeError:
            return None

    @property
    def keys(self) -> List[str]:
        """Item identities (zotero URI, else numeric id) in citation order."""
        d = self.payload or {}
        out = []
        for ci in d.get("citationItems", []):
            uris = ci.get("uris") or ci.get("uri") or []
            out.append(uris[0] if uris else str(ci.get("id")))
        return out


def _scan(p, depth: int = 0):
    """Classify the direct children of paragraph `p`, carrying the field depth in from the previous paragraph.

    Returns (info, spans, end_depth). info: list of (element, kind), kind in plain | marker | in_field | barrier | transparent.
    """
    info: List[Tuple[etree._Element, str]] = []
    spans: List[Span] = []
    start_idx: Optional[int] = None
    for el in p:
        if _local(el) != "r":
            info.append((el, "transparent" if _local(el) in _TRANSPARENT else "barrier"))
            continue
        fc = el.find(q("fldChar"))
        if fc is not None:
            t = fc.get(q("fldCharType"))
            if t == "begin":
                if depth == 0:
                    start_idx = len(info)
                depth += 1
            elif t == "end":
                depth = max(0, depth - 1)
                info.append((el, "marker"))
                if depth == 0 and start_idx is not None:
                    els = [e for e, _ in info[start_idx:]]
                    spans.append(Span(els, _instr_of(els), _display_of(els)))
                    start_idx = None
                continue
            info.append((el, "marker"))
            continue
        if depth > 0:
            info.append((el, "in_field"))
        else:
            info.append((el, "plain" if _is_text_run(el) else "barrier"))
    return info, spans, depth


def _instr_of(els) -> str:
    return "".join(t.text or "" for e in els if _local(e) == "r" for t in e.findall(q("instrText")))


def _display_of(els) -> str:
    phase, out = False, []
    for e in els:
        if _local(e) != "r":
            continue
        fc = e.find(q("fldChar"))
        if fc is not None:
            if fc.get(q("fldCharType")) == "separate":
                phase = True
            elif fc.get(q("fldCharType")) == "end":
                phase = False
            continue
        if phase:
            out.append(run_text(e))
    return "".join(out)


def segments(p, depth: int = 0) -> List[List[etree._Element]]:
    """Maximal stretches of consecutive plain-text runs (a field, a drawing, a tab ... ends a stretch)."""
    info, _, _ = _scan(p, depth)
    segs, cur = [], []
    for el, kind in info:
        if kind == "plain":
            cur.append(el)
        elif kind == "transparent":
            continue
        else:
            if cur:
                segs.append(cur)
            cur = []
    if cur:
        segs.append(cur)
    return segs


def plain_text(p, depth: int = 0) -> str:
    """Visible text outside fields (field results such as '[12]' are not included)."""
    return "".join(run_text(r) for seg in segments(p, depth) for r in seg)


# ----------------------------------------------------------------------------- text edits on one paragraph
def _spans_of(seg) -> Tuple[str, List[Tuple[etree._Element, int, int]]]:
    pos, out = 0, []
    for r in seg:
        t = run_text(r)
        out.append((r, pos, pos + len(t)))
        pos += len(t)
    return "".join(run_text(r) for r in seg), out


def replace_in_paragraph(p, old: str, new: str, depth: int = 0, count: int = 1) -> int:
    """Replace `old` by `new` in plain text only.

    Only the part that really changes is rewritten: the common prefix and suffix of `old` and `new` stay exactly where (and in which run)
    they were, so a bold or italic word inside the matched phrase keeps its formatting. A match may span several adjacent plain runs.
    """
    if not old:
        raise ValueError("old text is empty")
    if old == new:
        return 0
    pre = 0
    while pre < min(len(old), len(new)) and old[pre] == new[pre]:
        pre += 1
    suf = 0
    while suf < min(len(old), len(new)) - pre and old[len(old) - 1 - suf] == new[len(new) - 1 - suf]:
        suf += 1
    mid_old, mid_new = old[pre:len(old) - suf], new[pre:len(new) - suf]
    done = 0
    for seg in segments(p, depth):
        start = 0
        while done < count:
            text, offs = _spans_of(seg)
            m = text.find(old, start)
            if m < 0:
                break
            i, j = m + pre, m + len(old) - suf
            if i == j:                                            # pure insertion: put it into the run that ends at i
                tgt = next((r for r, a, b in offs if a < i <= b), offs[0][0] if offs else None)
                a0 = next(a for r, a, b in offs if r is tgt)
                t = run_text(tgt)
                set_run_text(tgt, t[:i - a0] + mid_new + t[i - a0:])
            else:
                first = True
                for r, a, b in offs:
                    if b <= i or a >= j:
                        continue
                    t = run_text(r)
                    lo, hi = max(i, a) - a, min(j, b) - a
                    if first:
                        set_run_text(r, t[:lo] + mid_new + t[hi:])
                        first = False
                    else:
                        set_run_text(r, t[:lo] + t[hi:])
            for r, _, _ in offs:
                if r.getparent() is not None and not run_text(r) and _is_text_run(r) and len(r.findall(q("t"))) <= 1:
                    r.getparent().remove(r)
            seg[:] = [r for r in seg if r.getparent() is not None]
            start = m + len(new)
            done += 1
        if done >= count:
            break
    return done


def rewrite_plain_paragraph(p, text: str, depth: int = 0) -> None:
    """Replace the whole text of a paragraph that has NO fields. Refuses otherwise (use replace_in_paragraph)."""
    info, spans, d = _scan(p, depth)
    if spans or d or any(k in ("marker", "in_field") for _, k in info):
        raise ValueError("paragraph contains fields; rewrite refused (use replace_in_paragraph)")
    plain = [e for e, k in info if k == "plain"]
    if not plain:
        raise ValueError("paragraph has no plain text run to carry the new text")
    set_run_text(plain[0], text)
    for r in plain[1:]:
        p.remove(r)


def _locate(p, anchor: str, depth: int = 0, occurrence: Optional[int] = None):
    hits = []
    for seg in segments(p, depth):
        text, offs = _spans_of(seg)
        for m in re.finditer(re.escape(anchor), text):
            hits.append((offs, m.start(), m.end()))
    if occurrence is None:
        if len(hits) != 1:
            return None, f"anchor found {len(hits)} times (must be unique): {anchor!r}"
        return hits[0], ""
    if not 0 <= occurrence < len(hits):
        return None, f"occurrence {occurrence} out of range ({len(hits)} found): {anchor!r}"
    return hits[occurrence], ""


def _split_at(offs, pos: int) -> etree._Element:
    """Make `pos` fall on a run boundary; return the run that ends exactly at `pos`."""
    for r, a, b in offs:
        if a < pos < b:
            t = run_text(r)
            r2 = copy.deepcopy(r)
            set_run_text(r, t[:pos - a])
            set_run_text(r2, t[pos - a:])
            r.addnext(r2)
            return r
        if b == pos:
            return r
    raise ValueError("position not inside any run")


def insert_after_anchor(p, anchor: str, elements: Sequence[etree._Element], depth: int = 0, occurrence: Optional[int] = None) -> Tuple[bool, str]:
    """Insert `elements` (e.g. a citation group) right after the (unique) anchor text."""
    hit, msg = _locate(p, anchor, depth, occurrence)
    if hit is None:
        return False, msg
    offs, _, end = hit
    r = _split_at(offs, end)
    parent = r.getparent()
    idx = parent.index(r) + 1
    for k, el in enumerate(elements):
        parent.insert(idx + k, el)
    return True, ""


def insert_before_anchor(p, anchor: str, elements: Sequence[etree._Element], depth: int = 0, occurrence: Optional[int] = None) -> Tuple[bool, str]:
    """Insert `elements` right before the (unique) anchor text — e.g. before the sentence-final '。' so the citation precedes the punctuation."""
    hit, msg = _locate(p, anchor, depth, occurrence)
    if hit is None:
        return False, msg
    offs, start, _ = hit
    run = next(r for r, a, b in offs if a <= start < b)
    if next(a for r, a, b in offs if r is run) == start:      # anchor starts exactly at a run boundary
        parent, idx = run.getparent(), run.getparent().index(run)
    else:
        left = _split_at(offs, start)                          # split inside the run; insert between the halves
        parent, idx = left.getparent(), left.getparent().index(left) + 1
    for k, el in enumerate(elements):
        parent.insert(idx + k, el)
    return True, ""


def detach(span: Span) -> List[etree._Element]:
    """Remove a field group from the tree and return its elements (to be re-inserted elsewhere)."""
    for el in span.elements:
        if el.getparent() is not None:
            el.getparent().remove(el)
    return span.elements


def append_text_run(p, text: str, depth: int = 0) -> etree._Element:
    """Append a new plain run at the END of the paragraph (after any field), cloning the formatting of the last plain run.

    Typical case: a REF cross-reference field sits after the sentence punctuation and a closing bracket has to be added.
    """
    info, _, _ = _scan(p, depth)
    plain = [e for e, k in info if k == "plain"]
    if not plain:
        raise ValueError("no plain run to take the formatting from")
    r = etree.SubElement(p, q("r"))
    rpr = plain[-1].find(q("rPr"))
    if rpr is not None:
        r.append(copy.deepcopy(rpr))
    set_run_text(r, text)
    return r


# ----------------------------------------------------------------------------- citation groups: display / payload
def _rtf(text: str) -> str:
    return text.replace("–", "\\uc0\\u8211{}").replace("—", "\\uc0\\u8212{}")


def set_group_display(span: Span, text: str, update_payload: bool = True) -> None:
    """Change the shown text of a citation field ('[3]' -> '[5]') and keep payload plainCitation / formattedCitation in step.

    Changing only the visible run is what makes verification report 'payload != display'; both places must change.
    """
    runs = [e for e in span.elements if _local(e) == "r"]
    phase, disp = False, []
    for r in runs:
        fc = r.find(q("fldChar"))
        if fc is not None:
            t = fc.get(q("fldCharType"))
            phase = True if t == "separate" else (False if t == "end" else phase)
            continue
        if phase and r.find(q("t")) is not None:
            disp.append(r)
    if not disp:
        raise ValueError("citation field has no display run")
    set_run_text(disp[0], text)
    for r in disp[1:]:
        r.getparent().remove(r)
        span.elements.remove(r)
    span.display = text
    d = span.payload
    if update_payload and d is not None:
        fc = d.get("properties", {}).get("formattedCitation", "")
        d.setdefault("properties", {})["plainCitation"] = text
        d["properties"]["formattedCitation"] = ("\\super " + _rtf(text) + "\\nosupersub{}") if fc.startswith("\\super") else _rtf(text)
        instr = " ADDIN ZOTERO_ITEM CSL_CITATION " + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + " "
        its = [t for r in runs for t in r.findall(q("instrText"))]
        its[0].text = instr
        its[0].set(XML_SPACE, "preserve")
        for t in its[1:]:
            t.text = ""
        span.instr = instr


# ----------------------------------------------------------------------------- the document
class FieldDoc:
    """A .docx opened for field-safe edits. Nothing is written until `save()`; the source file is never modified."""

    def __init__(self, path):
        self.path = Path(path)
        with zipfile.ZipFile(self.path) as z:
            raw = z.read("word/document.xml")
        self.root = etree.fromstring(raw, etree.XMLParser(resolve_entities=False, huge_tree=True))
        self.paragraphs: List[etree._Element] = list(self.root.iter(q("p")))
        self._depth: List[int] = []
        d = 0
        for p in self.paragraphs:
            self._depth.append(d)
            d = _scan(p, d)[2]
        self._counts0 = self.field_counts()
        self._nsmap0 = dict(self.root.nsmap)

    # -- queries
    def field_counts(self) -> Dict[str, int]:
        c = {"begin": 0, "separate": 0, "end": 0}
        for fc in self.root.iter(q("fldChar")):
            t = fc.get(q("fldCharType"))
            if t in c:
                c[t] += 1
        return c

    def depth_at(self, i: int) -> int:
        return self._depth[i]

    def plain(self, i: int) -> str:
        return plain_text(self.paragraphs[i], self._depth[i])

    def find(self, text: str) -> List[int]:
        """Indexes of paragraphs whose plain text (outside fields) contains `text`."""
        return [i for i in range(len(self.paragraphs)) if text in self.plain(i)]

    def citations(self) -> List[Tuple[int, Span]]:
        out = []
        for i, p in enumerate(self.paragraphs):
            for sp in _scan(p, self._depth[i])[1]:
                if sp.kind == "citation":
                    out.append((i, sp))
        return out

    # -- edits
    def replace(self, old: str, new: str, count: Optional[int] = None) -> int:
        """Replace `old` by `new` everywhere in plain text (all occurrences unless `count`)."""
        total, limit = 0, count if count is not None else 10 ** 9
        for i, p in enumerate(self.paragraphs):
            if total >= limit:
                break
            total += replace_in_paragraph(p, old, new, self._depth[i], limit - total)
        return total

    def replace_in(self, i: int, old: str, new: str, count: int = 1) -> int:
        return replace_in_paragraph(self.paragraphs[i], old, new, self._depth[i], count)

    def insert_after_anchor(self, i: int, anchor: str, elements, occurrence: Optional[int] = None) -> Tuple[bool, str]:
        return insert_after_anchor(self.paragraphs[i], anchor, elements, self._depth[i], occurrence)

    def insert_before_anchor(self, i: int, anchor: str, elements, occurrence: Optional[int] = None) -> Tuple[bool, str]:
        return insert_before_anchor(self.paragraphs[i], anchor, elements, self._depth[i], occurrence)

    def refresh_numbers(self) -> Dict:
        """Set every numeric citation display to the order of FIRST appearance of its items (what Zotero's Refresh does for the text).

        Payloads are kept in step. Bibliography paragraphs are not touched: renumber and reorder them with Zotero → Refresh in Word.
        """
        order: Dict[str, int] = {}
        changed, skipped, same = [], [], 0
        for i, sp in self.citations():
            nums = []
            for k in sp.keys:
                if k not in order:
                    order[k] = len(order) + 1
                nums.append(order[k])
            cur = sp.display.strip()
            if not re.fullmatch(r"\[[\d,\s–—-]+\]", cur):
                skipped.append(dict(paragraph=i, display=cur, reason="non-numeric style"))
                continue
            want = compress(nums)
            if norm_disp(want) == norm_disp(cur):
                same += 1
                continue
            set_group_display(sp, want)
            changed.append(dict(paragraph=i, before=cur, after=want))
        return dict(changed=changed, unchanged=same, skipped=skipped, items=len(order))

    # -- output
    def save(self, dst, allow_field_change: bool = False) -> Path:
        dst = Path(dst)
        if dst.resolve() == self.path.resolve():
            raise ValueError("write to a NEW file; keep the original as the backup")
        now = self.field_counts()
        if not allow_field_change and (now["begin"], now["separate"], now["end"]) != (self._counts0["begin"], self._counts0["separate"], self._counts0["end"]):
            raise ValueError(f"field counts changed {self._counts0} -> {now}; refusing to write (allow_field_change=True if intended)")
        if now["begin"] != now["separate"] or now["separate"] != now["end"]:
            raise ValueError(f"unbalanced field markers {now}; refusing to write")
        xml = etree.tostring(self.root, xml_declaration=True, encoding="UTF-8", standalone=True)
        with zipfile.ZipFile(self.path) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                zout.writestr(item, xml if item.filename == "word/document.xml" else zin.read(item.filename))
        return dst
