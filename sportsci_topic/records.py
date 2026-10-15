"""Literature records: read them from whatever the student has, never generate them.

Accepted inputs: CSV (CNKI / Wanfang / Web of Science / PubMed exports, Chinese or English headers), RIS (Zotero, EndNote),
JSON (CSL-JSON, or a list of {title, year, ...}), and TXT (one title or one GB/T 7714 entry per line).
Nothing is completed from memory: a missing year stays missing and is reported.
"""
from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

_YEAR = re.compile(r"(?<!\d)(19[5-9]\d|20[0-4]\d)(?!\d)")


@dataclass
class Record:
    title: str
    year: int = 0
    doi: str = ""
    journal: str = ""
    abstract: str = ""
    authors: str = ""
    keywords: str = ""
    source: str = ""

    @property
    def text(self) -> str:
        return " ".join([self.title, self.abstract, self.keywords]).lower()

    def key(self) -> str:
        if self.doi:
            return "doi:" + self.doi.lower()
        return "ti:" + re.sub(r"[^a-z0-9一-鿿]+", "", self.title.lower())

    def to_dict(self) -> Dict:
        return asdict(self)


def _year(v) -> int:
    m = _YEAR.search(str(v or ""))
    return int(m.group(1)) if m else 0


def _doi(v) -> str:
    v = (v or "").strip().lower()
    v = re.sub(r"^https?://(dx\.)?doi\.org/", "", v)
    v = re.sub(r"^doi:\s*", "", v)
    return v if v.startswith("10.") else ""


def dedupe(records: Iterable[Record]) -> List[Record]:
    out: Dict[str, Record] = {}
    for r in records:
        if not r.title.strip():
            continue
        k = r.key()
        if k not in out:
            out[k] = r
        else:  # keep the richer copy
            old = out[k]
            for f in ("year", "doi", "journal", "abstract", "authors", "keywords"):
                if not getattr(old, f) and getattr(r, f):
                    setattr(old, f, getattr(r, f))
    return list(out.values())


# ---------------------------------------------------------------------------------------------------------- CSV

_ALIASES = [  # canonical field -> header fragments (matched after lower-casing and removing spaces)
    ("doi", ("doi",)),
    ("title", ("title", "题名", "标题", "题目", "篇名")),
    ("abstract", ("abstract", "summary", "摘要")),
    ("keywords", ("keyword", "关键词", "关键字")),
    ("authors", ("author", "作者")),
    ("journal", ("journal", "source", "刊名", "期刊", "文献来源", "来源", "publication")),
    ("year", ("year", "年份", "出版年", "发表年", "发表时间", "date", "年")),
]


def _read_text(p: Path) -> str:
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _map_headers(headers: Sequence[str]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    norm = [re.sub(r"\s+", "", (h or "").lower()) for h in headers]
    for field_, frags in _ALIASES:
        for i, h in enumerate(norm):
            if i in out.values():
                continue
            if any(f in h for f in frags):
                out[field_] = i
                break
    return out


def read_csv(path: Path) -> List[Record]:
    text = _read_text(path)
    dialect = csv.excel_tab if text.count("\t") > text.count(",") else csv.excel
    rows = list(csv.reader(io.StringIO(text), dialect))
    if not rows:
        return []
    hmap = _map_headers(rows[0])
    if "title" not in hmap:
        raise ValueError(f"{path.name}: no title column found (looked for Title / 题名 / 标题 …); header is {rows[0][:8]}")
    out = []
    for row in rows[1:]:
        def cell(f):
            i = hmap.get(f)
            return row[i].strip() if i is not None and i < len(row) else ""
        out.append(Record(title=cell("title"), year=_year(cell("year")), doi=_doi(cell("doi")), journal=cell("journal"),
                          abstract=cell("abstract"), authors=cell("authors"), keywords=cell("keywords"), source=path.name))
    return out


# ---------------------------------------------------------------------------------------------------------- RIS

def read_ris(path: Path) -> List[Record]:
    recs: List[Record] = []
    cur: Dict[str, List[str]] = {}

    def flush():
        if cur:
            g = lambda *tags: next((" ".join(cur[t]) for t in tags if t in cur), "")
            recs.append(Record(title=g("TI", "T1"), year=_year(g("PY", "Y1", "DA")), doi=_doi(g("DO")), journal=g("JO", "JF", "T2", "JA"),
                               abstract=g("AB", "N2"), authors="; ".join(cur.get("AU", []) + cur.get("A1", [])),
                               keywords="; ".join(cur.get("KW", [])), source=path.name))
        cur.clear()

    for line in _read_text(path).splitlines():
        m = re.match(r"^([A-Z][A-Z0-9])\s{2}-\s?(.*)$", line)
        if not m:
            continue
        tag, val = m.group(1), m.group(2).strip()
        if tag == "TY":
            flush()
        elif tag == "ER":
            flush()
        else:
            cur.setdefault(tag, []).append(val)
    flush()
    return recs


# ---------------------------------------------------------------------------------------------------------- JSON

def read_json(path: Path) -> List[Record]:
    data = json.loads(_read_text(path))
    if isinstance(data, dict):
        data = data.get("records") or data.get("items") or []
    out = []
    for it in data:
        if not isinstance(it, dict):
            continue
        title = it.get("title") or ""
        if isinstance(title, list):
            title = title[0] if title else ""
        year = it.get("year")
        if not year and isinstance(it.get("issued"), dict):
            try:
                year = it["issued"]["date-parts"][0][0]
            except (KeyError, IndexError, TypeError):
                year = 0
        au = it.get("authors") or it.get("author") or ""
        if isinstance(au, list):
            au = "; ".join(a.get("family", "") + " " + a.get("given", "") if isinstance(a, dict) else str(a) for a in au)
        jr = it.get("journal") or it.get("container-title") or ""
        if isinstance(jr, list):
            jr = jr[0] if jr else ""
        out.append(Record(title=str(title), year=_year(year), doi=_doi(it.get("doi") or it.get("DOI")), journal=str(jr),
                          abstract=str(it.get("abstract") or ""), authors=str(au), keywords=str(it.get("keywords") or ""),
                          source=str(it.get("source") or path.name)))
    return out


# ---------------------------------------------------------------------------------------------------------- TXT

_TYPE_MARK = re.compile(r"\[[A-Z]{1,2}(?:/[A-Z]{2})?\]")


def read_txt(path: Path) -> List[Record]:
    out = []
    for line in _read_text(path).splitlines():
        s = re.sub(r"^\s*(\[\d+\]|\d+[.、)])\s*", "", line).strip()
        if not s:
            continue
        m = _TYPE_MARK.search(s)
        if m:  # GB/T 7714 entry: "Authors. Title[J]. Journal, 2021, ..."
            head = s[: m.start()]
            title = head.split(". ")[-1].strip() if ". " in head else head.strip()
            out.append(Record(title=title, year=_year(s[m.end():]), source=path.name))
        else:
            out.append(Record(title=s, year=_year(s), source=path.name))
    return out


READERS = {".csv": read_csv, ".tsv": read_csv, ".ris": read_ris, ".json": read_json, ".txt": read_txt, ".md": read_txt}


def load_records(paths: Sequence[str | Path]) -> List[Record]:
    allrecs: List[Record] = []
    for p in paths:
        p = Path(p)
        fn = READERS.get(p.suffix.lower())
        if fn is None:
            raise ValueError(f"{p.name}: unsupported record file type {p.suffix!r} (use .csv .ris .json .txt)")
        allrecs += fn(p)
    return dedupe(allrecs)


def from_search_dicts(items: Iterable[Dict], source: str = "") -> List[Record]:
    """Convert records returned by sportsci_refs.search (title, year, doi, journal, author, source …)."""
    out = []
    for it in items:
        out.append(Record(title=it.get("title", ""), year=_year(it.get("year")), doi=_doi(it.get("doi")), journal=it.get("journal", ""),
                          abstract=it.get("abstract", ""), authors=it.get("author", ""), source=it.get("source") or source))
    return out
