"""GB/T 7714-2015 numeric (顺序编码制) reference formatting from CSL-JSON.

For when the reference list is produced by code (results reports, quick drafts) rather than by Zotero. When the author
uses Zotero, let Zotero render the list with the CSL style their school requires (2015 or the newer edition) — the
style file is the authority, this module is a convenience that follows the 2015 rules:

    authors   up to 3, then "等" (Chinese) / "et al" (other languages); Western names surname first, initials without dots
    codes     [J] [M] [D] [C] [R] [S] [N] [P] [EB/OL]; contributions in proceedings use "//"
    journal   作者. 题名[J]. 刊名, 年, 卷(期): 起-止页. DOI:...
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .ris import is_cjk

CODE_OF_TYPE = {"article-journal": "J", "article": "J", "article-magazine": "J", "book": "M", "thesis": "D", "paper-conference": "C",
                "chapter": "M", "report": "R", "standard": "S", "article-newspaper": "N", "patent": "P", "webpage": "EB/OL",
                "post-weblog": "EB/OL", "dataset": "DS", "document": "Z"}


def _name(a: Dict, upper: bool) -> str:
    if a.get("literal"):
        return a["literal"]
    fam, giv = a.get("family", ""), a.get("given", "")
    if is_cjk(fam + giv):
        return f"{fam}{giv}"
    initials = " ".join(p[0].upper() for p in giv.replace(".", " ").replace("-", " ").split() if p)
    return f"{fam.upper() if upper else fam} {initials}".strip()


def authors_str(authors: List[Dict], zh: bool, upper: bool = False, etal: bool = False) -> str:
    if not authors:
        return ""
    names = [_name(a, upper) for a in authors[:3]]
    more = len(authors) > 3 or etal
    return ", ".join(names) + ((", 等" if zh else ", et al") if more else "")


def _ordinal(ed) -> str:
    s = str(ed)
    if not s.isdigit():
        return s
    n = int(s)
    return s + ("th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))


def _year(r: Dict) -> str:
    try:
        return str(r["issued"]["date-parts"][0][0])
    except (KeyError, IndexError, TypeError):
        return str(r.get("issued", {}).get("raw", "")) if isinstance(r.get("issued"), dict) else ""


def format_gbt(r: Dict, upper_surname: bool = False, with_doi: bool = True) -> str:
    zh = r.get("language", "").startswith("zh") or is_cjk(r.get("title", ""))
    code = CODE_OF_TYPE.get(r.get("type", ""), "J")
    au = authors_str(r.get("author", []), zh, upper_surname, bool(r.get("_etal")))
    title = (r.get("title") or "").strip().rstrip(".")
    y = _year(r)
    page = str(r.get("page", "")).replace("–", "-").replace("—", "-")
    head = (f"{au}. " if au else "") + f"{title}[{code}]"
    if code == "J":
        vi = (r.get("volume") or "") + (f"({r['issue']})" if r.get("issue") else "")
        body = f"{r.get('container-title', '')}, {y}" + (f", {vi}" if vi else "") + (f": {page}" if page else "")
    elif code in ("M", "R", "S"):
        if r.get("type") == "chapter" and r.get("container-title"):
            eds = authors_str(r.get("editor", []), zh, upper_surname)
            head += "//" + (f"{eds}. " if eds else "") + r["container-title"]
        ed = f"{r['edition']}版. " if r.get("edition") and zh else (f"{_ordinal(r['edition'])} ed. " if r.get("edition") else "")
        pub = ": ".join(x for x in (r.get("publisher-place"), r.get("publisher")) if x)
        body = ed + (f"{pub}, " if pub else "") + y + (f": {page}" if page else "")
    elif code == "D":
        pub = ": ".join(x for x in (r.get("publisher-place"), r.get("publisher")) if x)
        body = (f"{pub}, " if pub else "") + y
    elif code == "C":
        eds = authors_str(r.get("editor", []), zh, upper_surname)
        head += "//" + (f"{eds}. " if eds else "") + (r.get("container-title") or "")
        pub = ": ".join(x for x in (r.get("publisher-place"), r.get("publisher")) if x)
        body = (f"{pub}, " if pub else "") + y + (f": {page}" if page else "")
    elif code == "EB/OL":
        acc = r.get("accessed", {})
        acc = acc.get("raw") if isinstance(acc, dict) and acc.get("raw") else ("-".join(f"{x:02d}" if i else str(x) for i, x in enumerate(acc["date-parts"][0])) if isinstance(acc, dict) and acc.get("date-parts") else "")
        try:
            full = "-".join(f"{x:02d}" if i else str(x) for i, x in enumerate(r["issued"]["date-parts"][0]))
        except (KeyError, IndexError, TypeError):
            full = y
        body = (f"({full})" if full else "") + (f"[{acc}]" if acc else "") + (f". {r['URL']}" if r.get("URL") else "")
    else:
        body = ", ".join(x for x in (r.get("container-title"), r.get("publisher"), y) if x)
    s = f"{head}. {body}".rstrip(" .,") + "."
    if with_doi and r.get("DOI") and code in ("J", "C", "M", "D", "R"):
        s += f" DOI:{r['DOI']}."
    return s


def format_list(records: List[Dict], start: int = 1, upper_surname: bool = False, with_doi: bool = True) -> List[str]:
    return [f"[{i}] {format_gbt(r, upper_surname, with_doi)}" for i, r in enumerate(records, start)]
