# -*- coding: utf-8 -*-
"""Design specification: the machine-readable contract between "study design" and "results".

An AI agent (or a person) writes ONE json file after the design step (gap search -> design). The results engine needs nothing else
besides the data file. Templates: `python cli.py new-design --type parallel_prepost|crossover|multitime|meta`.
Field reference: reference/DESIGN_SPEC.md.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

DESIGNS = ("parallel_prepost", "crossover", "multitime", "meta", "single_group", "survey")


class SpecError(ValueError):
    pass


def lab(obj: Any, lang: str, default: str = "") -> str:
    """Label that may be a plain string or {'zh':..., 'en':...}."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return str(obj.get(lang) or obj.get("en") or obj.get("zh") or default)
    return str(obj)


def load_spec(path_or_dict) -> Dict[str, Any]:
    if isinstance(path_or_dict, dict):
        spec = json.loads(json.dumps(path_or_dict))
    else:
        p = Path(path_or_dict)
        txt = p.read_text(encoding="utf-8-sig")
        if p.suffix.lower() in (".yml", ".yaml"):
            import yaml  # optional dependency
            spec = yaml.safe_load(txt)
        else:
            spec = json.loads(txt)
    errs = validate_spec(spec)
    if errs:
        raise SpecError("Invalid design spec:\n  - " + "\n  - ".join(errs))
    return _defaults(spec)


def validate_spec(s: Dict[str, Any]) -> List[str]:
    e: List[str] = []
    d = s.get("design")
    if d not in DESIGNS:
        return [f"'design' must be one of {DESIGNS}, got {d!r}"]
    c = s.get("columns", {})
    if d == "survey":
        return _validate_survey(s)
    if d == "single_group":
        for k in ("id", "time"):
            if not c.get(k):
                e.append(f"columns.{k} is required")
        if len(s.get("times", {}).get("order", [])) < 2:
            e.append("times.order must list >= 2 time points")
        e += _validate_outcomes(s)
        return e
    if d == "meta":
        if not c.get("study"):
            e.append("columns.study is required for meta-analysis")
        mode = s.get("meta", {}).get("effect", "smd")
        if mode in ("smd", "md"):
            for k in ("n1", "m1", "sd1", "n2", "m2", "sd2"):
                if not c.get(k):
                    e.append(f"columns.{k} is required for meta.effect='{mode}'")
        elif mode == "generic":
            if not c.get("es") or not (c.get("se") or (c.get("lo") and c.get("hi"))):
                e.append("meta.effect='generic' needs columns.es and (columns.se or columns.lo + columns.hi)")
        else:
            e.append("meta.effect must be smd | md | generic")
        return e
    keyc = "condition" if d == "crossover" else "group"
    for k in ("id", keyc):
        if not c.get(k):
            e.append(f"columns.{k} is required")
    if d in ("parallel_prepost", "multitime") and not c.get("time"):
        e.append("columns.time is required")
    if d == "parallel_prepost" and len(s.get("times", {}).get("order", [])) != 2:
        e.append("times.order must list exactly 2 time points [baseline, post]")
    if d == "multitime" and len(s.get("times", {}).get("order", [])) < 3:
        e.append("times.order must list >= 3 time points")
    if d == "crossover":
        if not s.get("conditions", {}).get("order"):
            e.append("conditions.order is required")
        if not s.get("conditions", {}).get("control"):
            e.append("conditions.control is required (reference condition)")
    else:
        if not s.get("groups", {}).get("order"):
            e.append("groups.order is required")
        if not s.get("groups", {}).get("control"):
            e.append("groups.control is required (reference arm)")
    e += _validate_outcomes(s)
    return e


def _validate_outcomes(s: Dict[str, Any]) -> List[str]:
    e: List[str] = []
    if not s.get("outcomes"):
        e.append("outcomes must list at least one outcome")
    for i, o in enumerate(s.get("outcomes", [])):
        if not o.get("name"):
            e.append(f"outcomes[{i}].name is required")
    if s.get("outcomes") and not any(o.get("primary") for o in s["outcomes"]):
        e.append('mark at least one outcome with "primary": true (declare the primary outcome before analysis)')
    return e


def _validate_survey(s: Dict[str, Any]) -> List[str]:
    e: List[str] = []
    scales = s.get("scales", [])
    if not scales:
        return ["scales must list at least one scale: {name, items: [...], reverse?: [...], min?, max?}"]
    for i, sc in enumerate(scales):
        if not sc.get("name"):
            e.append(f"scales[{i}].name is required")
        if len(sc.get("items", [])) < 2:
            e.append(f"scales[{i}].items must list >= 2 item columns")
        bad = set(sc.get("reverse", [])) - set(sc.get("items", []))
        if bad:
            e.append(f"scales[{i}].reverse has items not in items: {sorted(bad)}")
    demo = {v.get("name") for v in s.get("demographics", [])}
    for var in s.get("group_compare", []):
        if var not in demo:
            e.append(f"group_compare '{var}' must also be declared in demographics")
    for kind, keys in (("mediation", ("x", "m", "y")), ("moderation", ("x", "w", "y"))):
        for i, m in enumerate(s.get(kind, [])):
            for k in keys:
                if not m.get(k):
                    e.append(f"{kind}[{i}].{k} is required")
    for i, r in enumerate(s.get("regression", [])):
        if not r.get("y") or not r.get("x"):
            e.append(f"regression[{i}] needs y and x (list)")
    return e


def _defaults(s: Dict[str, Any]) -> Dict[str, Any]:
    s.setdefault("language", "zh")
    s.setdefault("simulated", False)
    s.setdefault("title", "")
    s.setdefault("baseline_vars", [])
    s.setdefault("columns", {})
    for sc in s.get("scales", []):
        sc.setdefault("label", sc["name"])
        sc.setdefault("reverse", [])
    for o in s.get("outcomes", []):
        o.setdefault("column", o["name"])
        o.setdefault("label", o["name"])
        o.setdefault("unit", "")
        o.setdefault("category", "Outcomes")
        o.setdefault("primary", False)
        o.setdefault("direction", "neutral")  # higher_better | lower_better | neutral
    return s


def orient(o: Dict[str, Any]) -> int:
    """+1 if an increase is favourable (or neutral), -1 if a decrease is favourable."""
    return -1 if o.get("direction") == "lower_better" else 1
