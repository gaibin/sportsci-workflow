# -*- coding: utf-8 -*-
"""Generate ALL simulated datasets and both language sets of figures (26 data types, 30 figures).

    python examples/gallery/make_gallery.py [--only D15,D16] [--lang zh,en] [--no-sim]

Output: outputs/gallery/data/<domain>/*.csv  and  outputs/gallery/figures/<lang>/<domain>/*.png|pdf
"""
import argparse
import importlib
import traceback

import common  # noqa  (adds the skill folder to sys.path)
from sportsci_figures.pubstyle import apply_style

MODULES = ["d_psych_epi", "d_physio", "d_neuromech", "d_perf", "d_bio"]

ap = argparse.ArgumentParser()
ap.add_argument("--only", default="")
ap.add_argument("--lang", default="zh,en")
ap.add_argument("--no-sim", action="store_true")
a = ap.parse_args()
only = [s for s in a.only.split(",") if s]
domains = []
for m in MODULES:
    try:
        domains += importlib.import_module(m).DOMAINS
    except ModuleNotFoundError as e:
        if e.name != m:
            raise
for code, sim, fig in domains:
    if only and not any(code.startswith(o) for o in only):
        continue
    if not a.no_sim:
        sim()
    for lang in a.lang.split(","):
        apply_style(lang)
        try:
            fig(lang)
        except Exception:
            print(f"!! {code} [{lang}] failed"); traceback.print_exc()
    print("ok", code)
