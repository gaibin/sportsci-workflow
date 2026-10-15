"""sportsci_refs — literature and reference management, Zotero-first, for Word documents (theses, proposals, papers).

    search      candidate literature (Crossref / Europe PMC / OpenAlex), peer-review records removed, de-duplicated
    doi         verify DOIs on Crossref and compare titles
    ris         typed GB/T 7714 list <-> CSL-JSON <-> RIS
    gbt7714     CSL-JSON -> GB/T 7714-2015 numeric list
    zotero      local Zotero API: collections, CSL, item IDs, matching
    docx_fields plain "[n]" -> live Zotero fields; verify; compare
    fieldedit   field-safe edits of documents that already contain Zotero fields
    pdf_frames  page-by-page check of a bordered text frame in an exported PDF

Command line:  sportsci-refs --help   (or `python cli.py --help` from a source checkout)
"""
from .config import RefConfig, load_config
from .gbt7714 import format_gbt, format_list
from .ris import parse_gbt_list, parse_ris, to_csl, to_ris

__version__ = "1.0.0"
__all__ = ["RefConfig", "load_config", "format_gbt", "format_list", "parse_gbt_list", "parse_ris", "to_ris", "to_csl"]
