"""Page-by-page check of the bordered text frame some Chinese 开题报告 templates require (one box on every page).

Needs pymupdf (`pip install pymupdf`), imported lazily. Export the .docx to PDF first (Word: SaveAs2 format 17).

A frame is drawn as thin rectangles: wide-flat ones (w > 400 pt, h <= 2) are top/bottom borders. A middle page whose
frame bottom stops well above the BODY bottom (page height - bottom margin, NOT the page edge — measuring against
the edge flags every page) has a gap. Cover page without a frame and a short last page are normal.
Usual cause of a gap: an inline figure/table does not fit, Word pushes it to the next page. Fixing that is a layout
change — report it to the author, do not restructure the document without consent.
"""
from __future__ import annotations

from typing import Dict, List


def scan(pdf_path, bottom_margin_pt: float = 72.0, gap_threshold_pt: float = 60.0) -> Dict:
    try:
        import fitz  # pymupdf
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("pymupdf is required: pip install pymupdf") from e
    doc = fitz.open(pdf_path)
    pages: List[Dict] = []
    bad: List[int] = []
    for pno in range(doc.page_count):
        pg = doc[pno]
        body_bottom = pg.rect.height - bottom_margin_pt
        bot = None
        for d in pg.get_drawings():
            for item in d["items"]:
                if item[0] == "re":
                    r = item[1]
                    if r.width > 400 and r.height <= 2.0 and (bot is None or r.y1 > bot):
                        bot = r.y1
        gap = None if bot is None else round(body_bottom - bot, 1)
        flag = bot is not None and 0 < pno < doc.page_count - 1 and gap > gap_threshold_pt
        if flag:
            bad.append(pno + 1)
        pages.append(dict(page=pno + 1, frame_bottom=None if bot is None else round(bot, 1), gap_to_body_bottom=gap, flag=flag))
    doc.close()
    return dict(pages=pages, pages_with_gap=bad)
