"""Reference records: GB/T 7714 text  <->  CSL-JSON  <->  RIS.

CSL-JSON is the internal format (Zotero imports and exports it natively). Typical use: a thesis draft already has a
typed reference list -> `parse_gbt_list` -> RIS -> import into a Zotero collection -> `zotero.match` -> `docx_fields.fieldify`.

Supported GB/T 7714 document-type codes: [J] journal, [D] thesis, [M] book, [C] proceedings (with "//"), [EB/OL] web,
[R] report, [S] standard, [N] newspaper, [P] patent. Anything the parser cannot read is kept with `_warnings` set,
never silently dropped or completed by guesswork.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

TYPE_OF_CODE = {"J": "article-journal", "D": "thesis", "M": "book", "C": "paper-conference", "EB/OL": "webpage", "OL": "webpage",
                "R": "report", "S": "standard", "N": "article-newspaper", "P": "patent", "Z": "document", "A": "chapter", "G": "book"}
RIS_OF_TYPE = {"article-journal": "JOUR", "thesis": "THES", "book": "BOOK", "paper-conference": "CONF", "chapter": "CHAP", "webpage": "ELEC",
               "report": "RPRT", "standard": "STAND", "article-newspaper": "NEWS", "patent": "PAT", "document": "GEN"}
TYPE_OF_RIS = {v: k for k, v in RIS_OF_TYPE.items()} | {"JFULL": "article-journal", "EJOUR": "article-journal", "THESIS": "thesis"}

_CJK = re.compile(r"[一-鿿]")
_ORG = re.compile(r"(college|association|organi[sz]ation|society|institute|committee|ministry|federation|council|university|department|"
                  r"cent(er|re)|agency|board|group|consortium|foundation|office|administration)", re.I)
_CODE = re.compile(r"\[(EB/OL|[JDMCRSNPZAG](?:/OL)?)\]")


def is_cjk(s: str) -> bool:
    return bool(_CJK.search(s or ""))


# ----------------------------------------------------------------------------- names
def parse_name(a: str) -> Dict[str, str]:
    """'Smith J A' / 'SMITH JA' / 'Smith, John' -> {'family','given'}; Chinese names and organisations -> {'literal'}."""
    a = a.strip().strip(".").strip()
    if not a or is_cjk(a) or re.search(r"\d", a):
        return {"literal": a}
    if "," in a:
        fam, giv = [x.strip() for x in a.split(",", 1)]
        return {"family": fam, "given": giv}
    m = re.match(r"^(?P<fam>[A-Za-z][A-Za-z'\-\s]*?)\s+(?P<giv>[A-Z](?:[\s.]?[A-Z]){0,3})$", a)
    if m and not (m.group("fam").isupper() and len(m.group("fam").split()) > 2):
        return {"family": m.group("fam").strip(), "given": " ".join(re.sub(r"[\s.]", "", m.group("giv")))}
    parts = a.split()
    if len(parts) != 2 or a.isupper() or _ORG.search(a):
        return {"literal": a}  # organisation (WHO, American College of Sports Medicine ...) or unparseable
    return {"family": parts[-1], "given": parts[0]}  # "John Smith"


def name_str(n: Dict[str, str]) -> str:
    return n.get("literal") or f"{n.get('family', '')} {n.get('given', '')}".strip()


def split_authors(block: str) -> Tuple[List[Dict[str, str]], bool]:
    """Returns (authors, truncated_with_et_al)."""
    block = block.strip().rstrip(".")
    etal = bool(re.search(r"(,|，)?\s*(等|et\s*al\.?)\s*$", block, re.I))
    block = re.sub(r"(,|，)?\s*(等|et\s*al\.?)\s*$", "", block, flags=re.I).strip()
    raw = [x.strip() for x in re.split(r"[,，;；]", block) if x.strip()]
    return [parse_name(x) for x in raw], etal


# ----------------------------------------------------------------------------- GB/T text -> CSL
def parse_gbt_entry(text: str, num: Optional[int] = None) -> Dict:
    raw = re.sub(r"\s+", " ", text.strip())
    m0 = re.match(r"^\[(\d+)\]\s*(.*)$", raw)
    if m0:
        num, raw = int(m0.group(1)), m0.group(2)
    rec: Dict = {"id": str(num) if num is not None else None, "_raw": raw, "_warnings": []}
    doi = re.search(r"(?:DOI|doi)\s*[:：]\s*(10\.\S+?)\.?\s*$", raw)
    if doi:
        rec["DOI"] = doi.group(1).rstrip(".")
        raw = raw[:doi.start()].rstrip(" .")
    url = re.search(r"(https?://\S+?)\.?\s*$", raw)
    m = _CODE.search(raw)
    code = m.group(1) if m else "J"
    if not m:
        rec["_warnings"].append("未找到文献类型标识 [J]/[M]/[D]…，按期刊论文处理")
    rec["type"] = TYPE_OF_CODE.get(code.replace("/OL", "") if code != "EB/OL" else code, "article-journal")
    head = raw[:m.start()].rstrip(" .") if m else raw
    tail = raw[m.end():].strip(" .") if m else ""
    mh = re.match(r"^(?P<auth>.+?)\.\s+(?P<title>.+)$", head)
    if mh and len(mh.group("auth")) < 200:
        rec["author"], etal = split_authors(mh.group("auth"))
        if etal:
            rec["_etal"] = True
        rec["title"] = mh.group("title").strip()
    else:
        rec["author"], rec["title"] = [], head.strip()
        rec["_warnings"].append("未能拆分作者与题名")
    rec["language"] = "zh" if is_cjk(rec.get("title", "")) else "en"
    t = rec["type"]
    if t == "article-journal":
        mj = re.match(r"^(?P<jn>.+?)\s*[,，]\s*(?P<y>\d{4})\s*(?:[,，]\s*(?P<rest>.+))?$", tail)
        if mj:
            rec["container-title"], rec["issued"] = mj.group("jn").strip(), {"date-parts": [[int(mj.group("y"))]]}
            rest = (mj.group("rest") or "").strip()
            mv = re.match(r"^(?P<v>[^(:：]*?)\s*(?:\((?P<i>[^)]*)\))?\s*(?:[:：]\s*(?P<p>.+))?$", rest)
            if mv:
                if mv.group("v"):
                    rec["volume"] = mv.group("v").strip()
                if mv.group("i"):
                    rec["issue"] = mv.group("i").strip()
                if mv.group("p"):
                    rec["page"] = mv.group("p").strip().replace("–", "-")
        else:
            rec["_warnings"].append("期刊/年/卷期页格式未识别")
            y = re.search(r"(19|20)\d{2}", tail)
            if y:
                rec["issued"] = {"date-parts": [[int(y.group(0))]]}
    elif t in ("thesis", "book", "report", "standard"):
        mp = re.search(r"(?P<place>[^.:：]+)[:：]\s*(?P<pub>[^,，]+)[,，]\s*(?P<y>\d{4})(?:\s*[:：]\s*(?P<p>[\d\-–]+))?", tail)
        if mp:
            rec["publisher-place"], rec["publisher"] = mp.group("place").strip(), mp.group("pub").strip()
            rec["issued"] = {"date-parts": [[int(mp.group("y"))]]}
            if mp.group("p"):
                rec["page"] = mp.group("p")
            ed = re.match(r"^(\d+)\s*(?:st|nd|rd|th)?\s*(?:版|ed)", tail)
            if ed:
                rec["edition"] = ed.group(1)
        else:
            y = re.search(r"(19|20)\d{2}", tail)
            if y:
                rec["issued"] = {"date-parts": [[int(y.group(0))]]}
            rec["_warnings"].append("出版地/出版者/年未识别")
    elif t == "paper-conference":
        mc = re.match(r"^//\s*(?P<c>.+?)\.\s*(?P<place>[^.:：]+)[:：]\s*(?P<pub>[^,，]+)[,，]\s*(?P<y>\d{4})(?:\s*[:：]\s*(?P<p>[\d\-–]+))?", tail)
        if mc:
            rec["container-title"], rec["publisher-place"], rec["publisher"] = mc.group("c").strip(), mc.group("place").strip(), mc.group("pub").strip()
            rec["issued"] = {"date-parts": [[int(mc.group("y"))]]}
            if mc.group("p"):
                rec["page"] = mc.group("p")
        else:
            rec["_warnings"].append("会议录信息未识别")
    elif t == "webpage":
        if url:
            rec["URL"] = url.group(1)
        dates = re.findall(r"[\(\[]([\d\-]+)[\)\]]", tail)
        if dates:
            parts = [int(x) for x in dates[0].split("-") if x.isdigit()]
            if parts and parts[0] > 1900:
                rec["issued"] = {"date-parts": [parts[:3]]}
            if len(dates) > 1:
                rec["accessed"] = {"raw": dates[-1]}
    if not rec.get("author"):
        rec["_warnings"].append("缺作者")
    if not rec.get("issued"):
        rec["_warnings"].append("缺年份")
    return rec


def parse_gbt_list(text: str) -> List[Dict]:
    """Split a pasted reference list into entries (one per '[n]' or one per line) and parse each."""
    blocks = re.split(r"\n(?=\s*\[\d+\])", text.strip()) if re.search(r"^\s*\[\d+\]", text, re.M) else [x for x in text.splitlines() if x.strip()]
    out = []
    for i, b in enumerate(blocks, 1):
        r = parse_gbt_entry(b, i)
        out.append(r)
    return out


# ----------------------------------------------------------------------------- CSL <-> RIS
def _year(rec: Dict) -> str:
    try:
        return str(rec["issued"]["date-parts"][0][0])
    except (KeyError, IndexError, TypeError):
        return ""


def to_ris(records: List[Dict]) -> str:
    out = []
    for r in records:
        L = [f"TY  - {RIS_OF_TYPE.get(r.get('type'), 'GEN')}"]
        for a in r.get("author", []):
            L.append(f"AU  - {a['literal']}" if "literal" in a else f"AU  - {a.get('family', '')}, {a.get('given', '')}".rstrip(", "))
        for k, tag in (("title", "TI"), ("container-title", "T2"), ("volume", "VL"), ("issue", "IS"), ("DOI", "DO"), ("publisher", "PB"),
                       ("publisher-place", "CY"), ("URL", "UR"), ("language", "LA"), ("edition", "ET")):
            if r.get(k):
                L.append(f"{tag}  - {r[k]}")
        if _year(r):
            L.append(f"PY  - {_year(r)}")
        if r.get("page"):
            sp, _, ep = str(r["page"]).partition("-")
            L.append(f"SP  - {sp.strip()}")
            if ep:
                L.append(f"EP  - {ep.strip()}")
        L.append("ER  - ")
        out.append("\n".join(L))
    return "\n\n".join(out) + "\n"


def parse_ris(text: str) -> List[Dict]:
    recs, cur = [], None
    for line in text.splitlines():
        m = re.match(r"^([A-Z][A-Z0-9])\s{2}-\s?(.*)$", line)
        if not m:
            continue
        tag, val = m.group(1), m.group(2).strip()
        if tag == "TY":
            cur = {"type": TYPE_OF_RIS.get(val, "article-journal"), "author": []}
        elif cur is None:
            continue
        elif tag == "ER":
            if cur.get("_sp"):
                cur["page"] = cur.pop("_sp") + ("-" + cur.pop("_ep") if cur.get("_ep") else "")
            cur.pop("_ep", None)
            recs.append(cur)
            cur = None
        elif tag in ("AU", "A1"):
            cur["author"].append(parse_name(val) if "," not in val else dict(zip(("family", "given"), [x.strip() for x in val.split(",", 1)])))
        else:
            key = {"TI": "title", "T1": "title", "T2": "container-title", "JO": "container-title", "JF": "container-title", "VL": "volume", "IS": "issue",
                   "DO": "DOI", "PB": "publisher", "CY": "publisher-place", "UR": "URL", "LA": "language", "SP": "_sp", "EP": "_ep", "ET": "edition"}.get(tag)
            if key:
                cur.setdefault(key, val)
            elif tag in ("PY", "Y1", "DA"):
                y = re.search(r"\d{4}", val)
                if y:
                    cur["issued"] = {"date-parts": [[int(y.group(0))]]}
    for i, r in enumerate(recs, 1):
        r.setdefault("id", str(i))
    return recs


def to_csl(records: List[Dict]) -> List[Dict]:
    """Strip private keys (_raw, _warnings ...) so the list imports cleanly into Zotero."""
    return [{k: v for k, v in r.items() if not k.startswith("_")} for r in records]
