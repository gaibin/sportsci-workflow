# -*- coding: utf-8 -*-
"""把某一语言的全部图拼成总览图（方便人工审阅）。  python make_montage.py [en|zh] [每页张数]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

import common

lang = sys.argv[1] if len(sys.argv) > 1 else "en"
per = int(sys.argv[2]) if len(sys.argv) > 2 else 4
root = common.RES / common.LANG_DIR[lang]
files = sorted(p for p in root.glob("D*/*.png"))
out = common.RES / "montage"
out.mkdir(exist_ok=True, parents=True)
W = 1100
try:
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
except Exception:
    font = ImageFont.load_default()
sheets = [files[i:i + per] for i in range(0, len(files), per)]
for k, fs in enumerate(sheets, 1):
    ims = []
    for f in fs:
        im = Image.open(f).convert("RGB")
        im = im.resize((W, int(im.height * W / im.width)))
        ims.append((f, im))
    cols = 2
    rows = (len(ims) + 1) // 2
    hs = [max(im.height for _, im in ims[r * 2:r * 2 + 2]) + 34 for r in range(rows)]
    sheet = Image.new("RGB", (W * cols + 10, sum(hs)), "white")
    y = 0
    for r in range(rows):
        for c, (f, im) in enumerate(ims[r * 2:r * 2 + 2]):
            d = ImageDraw.Draw(sheet); d.text((c * W + 12, y + 4), f"{f.parent.name} / {f.name}", fill=(60, 60, 60), font=font)
            sheet.paste(im, (c * W, y + 30))
        y += hs[r]
    sheet.save(out / f"montage_{lang}_{k:02d}.png")
print(len(files), "figures ->", len(sheets), "sheets")
