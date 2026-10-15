# -*- coding: utf-8 -*-
"""Generate test data from a design spec that carries a "simulate" block with known true effects.

Purpose: (1) test the results engine (recover the true effects), (2) rehearse a study before real data exist.
Everything produced is simulated; the results builder tags figures/tables accordingly when spec["simulated"] is true.
"""
from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


def simulate(spec: Dict[str, Any]) -> pd.DataFrame:
    sim = spec.get("simulate", {})
    rng = np.random.default_rng(sim.get("seed", 1))
    return {"parallel_prepost": _parallel, "crossover": _crossover, "multitime": _multitime, "meta": _meta,
            "single_group": _single, "survey": _survey}[spec["design"]](spec, sim, rng)


def _single(spec, sim, rng):
    """One group, k time points; per outcome: mean, sd, r (between-time correlation), change {time: shift vs first}."""
    c = spec["columns"]
    times = [str(x) for x in spec["times"]["order"]]
    n = int(sim["n"])
    out = pd.DataFrame({c["id"]: np.repeat([f"S{i + 1:02d}" for i in range(n)], len(times)), c["time"]: times * n})
    for o in spec["outcomes"]:
        e = sim["effects"][o["name"]]
        rho = e.get("r", 0.7)
        subj = rng.normal(0, e["sd"] * np.sqrt(rho), n)
        vals = []
        for i in range(n):
            for t in times:
                vals.append(e["mean"] + e.get("change", {}).get(t, 0.0) + subj[i] + rng.normal(0, e["sd"] * np.sqrt(1 - rho)))
        out[o["column"]] = np.round(vals, e.get("round", 2))
    return _drop(out, sim, rng, [o["column"] for o in spec["outcomes"]], c["id"])


def _survey(spec, sim, rng):
    """Latent scale scores linked by simulate.paths [[from, to, beta], ...]; items are Likert indicators (min..max)."""
    n = int(sim["n"])
    names = [sc["name"] for sc in spec["scales"]]
    paths = sim.get("paths", [])
    lat = {}
    pending = list(names)
    for _ in range(len(names) + 1):  # topological order: a scale is generated once all its parents exist
        for nm in list(pending):
            parents = [(a, b_) for a, t, b_ in paths if t == nm]
            if all(a in lat for a, _ in parents):
                mu = sum(b_ * lat[a] for a, b_ in parents) if parents else np.zeros(n)
                lat[nm] = mu + rng.normal(0, np.sqrt(max(0.2, 1 - sum(b_ ** 2 for _, b_ in parents))), n)
                pending.remove(nm)
    if pending:
        raise ValueError(f"simulate.paths contain a cycle or unknown scale: {pending}")
    demo = {}
    for v in spec.get("demographics", []):
        b = sim.get("demographics", {}).get(v["name"])
        if b is None:
            continue
        col = v.get("column", v["name"])
        if v.get("type", "cat") == "cont":
            demo[col] = rng.normal(b["mean"], b["sd"], n).round(b.get("round", 0))
        else:
            p = np.array(b["p"], float)
            demo[col] = rng.choice(b["levels"], n, p=p / p.sum())
    for var, eff in sim.get("group_effects", {}).items():
        col = next((v.get("column", v["name"]) for v in spec.get("demographics", []) if v["name"] == var), var)
        for scale, shifts in eff.items():
            lat[scale] = lat[scale] + np.array([shifts.get(str(x), 0.0) for x in demo[col]])
    load = sim.get("loading", 0.72)
    cols = {}
    for sc in spec["scales"]:
        lo, hi = int(sc.get("min", 1)), int(sc.get("max", 5))
        k = hi - lo + 1
        cuts = np.quantile(rng.normal(0, 1, 20000), np.linspace(0, 1, k + 1)[1:-1])
        z = (lat[sc["name"]] - lat[sc["name"]].mean()) / lat[sc["name"]].std()
        for it in sc["items"]:
            x = lo + np.searchsorted(cuts, load * z + np.sqrt(1 - load ** 2) * rng.normal(0, 1, n))
            cols[it] = (lo + hi - x) if it in sc.get("reverse", []) else x
    out = pd.DataFrame({spec["columns"].get("id", "id"): [f"R{i + 1:03d}" for i in range(n)], **demo, **cols})
    rate = sim.get("missing", 0.0)
    if rate > 0:
        items = [it for sc in spec["scales"] for it in sc["items"]]
        mask = rng.random((n, len(items))) < rate
        out[items] = out[items].astype(float).mask(mask)
    return out


def _baseline_vars(spec, sim, rng, n):
    out = {}
    for v in spec.get("baseline_vars", []):
        b = sim.get("baseline", {}).get(v["name"])
        if b is None:
            continue
        if v.get("type", "cont") == "cont":
            out[v.get("column", v["name"])] = rng.normal(b["mean"], b["sd"], n).round(b.get("round", 1))
        else:
            lv, p = list(b["levels"]), np.array(b["p"], float)
            out[v.get("column", v["name"])] = rng.choice(lv, n, p=p / p.sum())
    return out


def _drop(df, sim, rng, cols, idc):
    rate = sim.get("dropout", 0.0)
    if rate > 0:
        gone = rng.choice(df[idc].unique(), int(round(rate * df[idc].nunique())), replace=False)
        last = df.groupby(idc).cumcount() == df.groupby(idc)[idc].transform("size") - 1
        df.loc[df[idc].isin(gone) & last, cols] = np.nan
    return df


def _parallel(spec, sim, rng):
    c = spec["columns"]
    times = [str(x) for x in spec["times"]["order"]]
    rows = []
    gi = 0
    for g in spec["groups"]["order"]:
        n = sim["n"][g]
        ids = [f"{g}{i + 1:02d}" for i in range(n)]
        bv = _baseline_vars(spec, sim, rng, n)
        cols = {o["column"]: None for o in spec["outcomes"]}
        for o in spec["outcomes"]:
            e = sim["effects"][o["name"]]
            pre = rng.normal(e["mean"], e["sd"], n)
            rho = e.get("r", 0.7)
            post = e["mean"] + rho * (pre - e["mean"]) + rng.normal(0, e["sd"] * np.sqrt(1 - rho ** 2), n) + e["change"][g]
            cols[o["column"]] = (pre.round(e.get("round", 2)), post.round(e.get("round", 2)))
        for ti, t in enumerate(times):
            d = {c["id"]: ids, c["group"]: g, c["time"]: t}
            d.update({k: v[ti] for k, v in cols.items()})
            d.update(bv)
            rows.append(pd.DataFrame(d))
        gi += 1
    df = pd.concat(rows, ignore_index=True)
    return _drop(df.sort_values([c["id"], c["time"]]).reset_index(drop=True), sim, rng, [o["column"] for o in spec["outcomes"]], c["id"])


def _crossover(spec, sim, rng):
    c = spec["columns"]
    conds = [str(x) for x in spec["conditions"]["order"]]
    n = sim["n"]
    ids = [f"P{i + 1:02d}" for i in range(n)]
    rows = []
    for i, pid in enumerate(ids):
        seq = list(rng.permutation(conds))
        for p, cond in enumerate(seq):
            rows.append({c["id"]: pid, c["condition"]: cond, c.get("period", "period"): p + 1})
    df = pd.DataFrame(rows)
    for o in spec["outcomes"]:
        e = sim["effects"][o["name"]]
        u = dict(zip(ids, rng.normal(0, e["sd_between"], n)))
        v = df[c["id"]].map(u).values + e["mean"] + df[c["condition"]].map(e["effect"]).values + rng.normal(0, e["sd_within"], len(df))
        v = v + (df[c.get("period", "period")].values - 1) * e.get("period_effect", 0.0)
        df[o["column"]] = v.round(e.get("round", 2))
    return df


def _multitime(spec, sim, rng):
    c = spec["columns"]
    times = [str(x) for x in spec["times"]["order"]]
    rows = []
    for g in spec["groups"]["order"]:
        n = sim["n"][g]
        ids = [f"{g}{i + 1:02d}" for i in range(n)]
        bv = _baseline_vars(spec, sim, rng, n)
        vals = {}
        for o in spec["outcomes"]:
            e = sim["effects"][o["name"]]
            u = rng.normal(0, e["sd"] * np.sqrt(e.get("r", 0.7)), n)
            vals[o["column"]] = [(e["mean"] + u + e["traj"][g][ti] + rng.normal(0, e["sd"] * np.sqrt(1 - e.get("r", 0.7)), n)).round(e.get("round", 2)) for ti in range(len(times))]
        for ti, t in enumerate(times):
            d = {c["id"]: ids, c["group"]: g, c["time"]: t}
            d.update({k: v[ti] for k, v in vals.items()})
            d.update(bv)
            rows.append(pd.DataFrame(d))
    df = pd.concat(rows, ignore_index=True)
    return df.sort_values([c["id"], c["time"]]).reset_index(drop=True)


def _meta(spec, sim, rng):
    c = spec["columns"]
    k = sim.get("k", 20)
    true, tau = sim.get("true", 0.4), sim.get("tau", 0.15)
    subs = sim.get("subgroups", {})
    rows = []
    for i in range(k):
        n = int(rng.integers(12, 60))
        sub = rng.choice(list(subs)) if subs else None
        mu = true + (subs[sub] if subs else 0.0) + rng.normal(0, tau)
        sd = rng.uniform(0.8, 1.4)
        mod = float(rng.integers(4, 24))
        mu = mu + sim.get("moderator_slope", 0.0) * (mod - 12)
        mu_c = rng.normal(10, 2)
        m2 = rng.normal(mu_c, sd / np.sqrt(n))
        flip = -1.0 if spec.get('meta', {}).get('direction') == 'lower_better' else 1.0
        x1 = rng.normal(mu_c + flip * mu * sd, sd / np.sqrt(n))
        row = {c["study"]: f"Author{chr(65 + i % 26)}{i // 26 or ''} {2008 + int(rng.integers(0, 16))}", c["n1"]: n, c["m1"]: round(x1, 2), c["sd1"]: round(sd, 2),
               c["n2"]: n, c["m2"]: round(m2, 2), c["sd2"]: round(sd * rng.uniform(0.9, 1.1), 2)}
        if c.get("subgroup"):
            row[c["subgroup"]] = sub
        if c.get("moderator"):
            row[c["moderator"]] = mod
        rows.append(row)
    return pd.DataFrame(rows)
