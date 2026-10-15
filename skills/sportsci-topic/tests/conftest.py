# -*- coding: utf-8 -*-
import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BASE = {
    "topic": {"working_title": "8周功能性训练对大学生下肢爆发力的影响", "language": "zh", "goal": "thesis", "question_type": "effect"},
    "pico": {
        "population": {"label": "大学生", "terms": ["大学生", "university students"]},
        "intervention": {"label": "功能性训练", "terms": ["功能性训练", "functional training"]},
        "comparator": {"label": "常规体育课", "terms": ["对照组", "control group"]},
        "outcome": {"label": "下肢爆发力", "terms": ["下肢爆发力", "countermovement jump", "vertical jump"]},
    },
    "outcomes": [
        {"name": "cmj", "label": "纵跳高度", "label_en": "CMJ height", "unit": "cm", "primary": True, "direction": "higher_better", "needs": "jump mat"},
        {"name": "sprint", "label": "30米冲刺", "label_en": "30-m sprint", "unit": "s", "direction": "lower_better", "needs": "timing gates"},
    ],
    "design": {"has_control": True, "timepoints": 2, "groups": ["对照组", "干预组"], "groups_en": ["Control", "Intervention"],
               "time_labels": ["基线", "第8周"], "time_labels_en": ["Baseline", "Week 8"]},
    "constraints": {"accessible_n": 80, "dropout": 0.15, "weeks_available": 40, "intervention_weeks": 8, "recruit_weeks": 2,
                    "test_weeks": 2, "writing_weeks": 6, "ethics": "approved", "equipment": ["jump mat", "timing gates"],
                    "stats_comfort": "intermediate"},
    "effect": {"source": "pilot, n = 12", "d": 0.7, "alpha": 0.05, "power": 0.8},
}


@pytest.fixture
def base_dict():
    return copy.deepcopy(BASE)


def to_toml(d) -> str:
    """Tiny TOML writer for the nested dicts the tests use (tables, arrays of tables, scalars, string lists)."""
    def val(v):
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return repr(v)
        if isinstance(v, list):
            return "[" + ", ".join(val(x) for x in v) + "]"
        return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'

    out = []

    def emit(prefix, tbl):
        scalars = {k: v for k, v in tbl.items() if not isinstance(v, dict) and not (isinstance(v, list) and v and isinstance(v[0], dict))}
        if prefix:
            out.append(f"[{prefix}]")
        for k, v in scalars.items():
            out.append(f"{k} = {val(v)}")
        out.append("")
        for k, v in tbl.items():
            if isinstance(v, dict):
                emit(f"{prefix}.{k}" if prefix else k, v)
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                for item in v:
                    out.append(f"[[{prefix}.{k}]]" if prefix else f"[[{k}]]")
                    for kk, vv in item.items():
                        out.append(f"{kk} = {val(vv)}")
                    out.append("")

    emit("", d)
    return "\n".join(out)


@pytest.fixture
def write_brief(tmp_path):
    def _w(d, name="brief.toml"):
        p = tmp_path / name
        p.write_text(to_toml(d), encoding="utf-8")
        return p
    return _w
