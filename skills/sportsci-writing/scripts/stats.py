#!/usr/bin/env python3
"""
Sport science statistics helper.

Runs descriptive and inferential tests common in sport science and
prints results in journal-ready format (Chinese or English).

Usage examples
--------------
# Independent t-test from a CSV with columns 'group' and 'vo2max'
python stats.py ttest data.csv --dv vo2max --group group --lang en

# Paired t-test from two columns
python stats.py paired data.csv --pre baseline --post week8 --lang zh

# One-way ANOVA
python stats.py anova data.csv --dv jump --group condition --lang en

# Pearson correlation
python stats.py corr data.csv --x volume --y improvement --method pearson

# Just descriptives
python stats.py describe data.csv --by group

The script prints (a) descriptives, (b) test result, (c) effect size with
95% CI, and (d) a Results-section paragraph in the requested language.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(p)
    return pd.read_csv(p)


# ---------------------------------------------------------------------------
# Effect sizes and helpers
# ---------------------------------------------------------------------------

def cohens_d_independent(x, y):
    nx, ny = len(x), len(y)
    sx, sy = np.std(x, ddof=1), np.std(y, ddof=1)
    pooled = math.sqrt(((nx - 1) * sx ** 2 + (ny - 1) * sy ** 2) / (nx + ny - 2))
    return (np.mean(x) - np.mean(y)) / pooled if pooled > 0 else float("nan")


def cohens_d_paired(pre, post):
    diff = np.array(post) - np.array(pre)
    sd = np.std(diff, ddof=1)
    return np.mean(diff) / sd if sd > 0 else float("nan")


def hedges_g(d, n_total):
    j = 1 - 3 / (4 * n_total - 9)
    return d * j


def d_ci(d, n1, n2, alpha=0.05):
    se = math.sqrt((n1 + n2) / (n1 * n2) + d ** 2 / (2 * (n1 + n2)))
    z = stats.norm.ppf(1 - alpha / 2)
    return d - z * se, d + z * se


def d_ci_paired(d, n, alpha=0.05):
    se = math.sqrt(1 / n + d ** 2 / (2 * n))
    z = stats.norm.ppf(1 - alpha / 2)
    return d - z * se, d + z * se


def fmt_p(p):
    return "< 0.001" if p < 0.001 else f"= {p:.3f}"


def fmt_mean_sd(x):
    return f"{np.mean(x):.2f} ± {np.std(x, ddof=1):.2f}"


# ---------------------------------------------------------------------------
# Descriptives
# ---------------------------------------------------------------------------

def describe(df: pd.DataFrame, by: str | None = None) -> str:
    out = []
    if by is None:
        for col in df.select_dtypes(include=np.number).columns:
            x = df[col].dropna()
            out.append(
                f"{col}: n={len(x)}, mean={x.mean():.2f}, SD={x.std(ddof=1):.2f}, "
                f"median={x.median():.2f}, IQR={x.quantile(0.25):.2f}–{x.quantile(0.75):.2f}, "
                f"min={x.min():.2f}, max={x.max():.2f}"
            )
    else:
        for g, sub in df.groupby(by):
            out.append(f"\n[{by} = {g}]  n = {len(sub)}")
            for col in sub.select_dtypes(include=np.number).columns:
                x = sub[col].dropna()
                out.append(
                    f"  {col}: mean={x.mean():.2f}, SD={x.std(ddof=1):.2f}, "
                    f"median={x.median():.2f}"
                )
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def independent_ttest(df, dv, group, lang="en"):
    groups = df[group].dropna().unique()
    if len(groups) != 2:
        sys.exit(f"Independent t-test requires exactly 2 groups; found {len(groups)}.")
    a = df.loc[df[group] == groups[0], dv].dropna().values
    b = df.loc[df[group] == groups[1], dv].dropna().values

    # Normality
    sw_a = stats.shapiro(a) if len(a) >= 3 else (np.nan, np.nan)
    sw_b = stats.shapiro(b) if len(b) >= 3 else (np.nan, np.nan)
    # Levene
    lev = stats.levene(a, b)
    equal_var = lev.pvalue > 0.05
    t, p = stats.ttest_ind(a, b, equal_var=equal_var)
    df_resid = (len(a) + len(b) - 2) if equal_var else _welch_df(a, b)
    d = cohens_d_independent(a, b)
    g = hedges_g(d, len(a) + len(b))
    lo, hi = d_ci(d, len(a), len(b))
    test_name = "Independent t-test" if equal_var else "Welch's t-test"

    print(f"=== {test_name} ===")
    print(f"{groups[0]} (n={len(a)}): {fmt_mean_sd(a)}")
    print(f"{groups[1]} (n={len(b)}): {fmt_mean_sd(b)}")
    print(f"Shapiro-Wilk: {groups[0]} W={sw_a[0]:.3f} P={sw_a[1]:.3f}; "
          f"{groups[1]} W={sw_b[0]:.3f} P={sw_b[1]:.3f}")
    print(f"Levene's test: F={lev.statistic:.3f}, P={lev.pvalue:.3f} "
          f"({'equal variances assumed' if equal_var else 'Welch correction applied'})")
    print(f"t({df_resid:.1f}) = {t:.3f}, P {fmt_p(p)}")
    print(f"Cohen's d = {d:.2f} (95% CI {lo:.2f} to {hi:.2f}); Hedges' g = {g:.2f}")

    print("\n--- Draft Results paragraph ---")
    if lang == "zh":
        print(f"{groups[0]}组（n = {len(a)}）的{dv}为 {fmt_mean_sd(a)}，"
              f"{groups[1]}组（n = {len(b)}）为 {fmt_mean_sd(b)}。"
              f"{test_name}显示两组差异{'显著' if p < 0.05 else '无统计学意义'}，"
              f"t({df_resid:.1f}) = {t:.3f}, P {fmt_p(p)}, "
              f"Cohen's d = {d:.2f}（95% CI {lo:.2f}–{hi:.2f}）。")
    else:
        direction = "higher" if np.mean(a) > np.mean(b) else "lower"
        sig = "" if p < 0.05 else " not"
        print(f"{dv} was{sig} significantly {direction} in the {groups[0]} group "
              f"({fmt_mean_sd(a)}) than in the {groups[1]} group ({fmt_mean_sd(b)}), "
              f"t({df_resid:.1f}) = {t:.3f}, P {fmt_p(p)}, "
              f"d = {d:.2f} (95% CI {lo:.2f} to {hi:.2f}).")


def _welch_df(a, b):
    va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
    na, nb = len(a), len(b)
    num = (va / na + vb / nb) ** 2
    den = (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
    return num / den


def paired_ttest(df, pre, post, lang="en"):
    a = df[pre].dropna().values
    b = df[post].dropna().values
    if len(a) != len(b):
        sys.exit("Paired t-test requires equal-length pre and post columns.")
    diff = b - a
    sw = stats.shapiro(diff) if len(diff) >= 3 else (np.nan, np.nan)
    t, p = stats.ttest_rel(a, b)
    d = cohens_d_paired(a, b)
    lo, hi = d_ci_paired(d, len(a))

    print("=== Paired t-test ===")
    print(f"{pre} (n={len(a)}): {fmt_mean_sd(a)}")
    print(f"{post} (n={len(b)}): {fmt_mean_sd(b)}")
    print(f"Shapiro-Wilk on differences: W={sw[0]:.3f}, P={sw[1]:.3f}")
    print(f"t({len(a)-1}) = {t:.3f}, P {fmt_p(p)}")
    print(f"Cohen's d = {d:.2f} (95% CI {lo:.2f} to {hi:.2f})")

    print("\n--- Draft Results paragraph ---")
    if lang == "zh":
        print(f"{post}（{fmt_mean_sd(b)}）较 {pre}（{fmt_mean_sd(a)}）"
              f"{'显著' if p < 0.05 else '无显著'}变化，"
              f"t({len(a)-1}) = {t:.3f}, P {fmt_p(p)}, "
              f"Cohen's d = {d:.2f}（95% CI {lo:.2f}–{hi:.2f}）。")
    else:
        direction = "increased" if np.mean(b) > np.mean(a) else "decreased"
        sig = "" if p < 0.05 else " not"
        print(f"{dv_label(pre, post)}{sig} significantly {direction} from baseline "
              f"({fmt_mean_sd(a)}) to post ({fmt_mean_sd(b)}), "
              f"t({len(a)-1}) = {t:.3f}, P {fmt_p(p)}, "
              f"d = {d:.2f} (95% CI {lo:.2f} to {hi:.2f}).")


def dv_label(pre, post):
    return pre.replace("baseline_", "").replace("pre_", "").replace("_pre", "")


def one_way_anova(df, dv, group, lang="en"):
    groups = df[group].dropna().unique()
    samples = [df.loc[df[group] == g, dv].dropna().values for g in groups]
    if len(groups) < 3:
        sys.exit("Use ttest for 2 groups; ANOVA requires 3+.")
    f, p = stats.f_oneway(*samples)
    df_between = len(groups) - 1
    df_within = sum(len(s) for s in samples) - len(groups)
    ss_between = sum(len(s) * (np.mean(s) - np.mean(np.concatenate(samples))) ** 2 for s in samples)
    ss_within = sum(((s - np.mean(s)) ** 2).sum() for s in samples)
    eta_p2 = ss_between / (ss_between + ss_within)

    print("=== One-way ANOVA ===")
    for g, s in zip(groups, samples):
        print(f"{group} = {g} (n={len(s)}): {fmt_mean_sd(s)}")
    print(f"F({df_between}, {df_within}) = {f:.3f}, P {fmt_p(p)}, partial eta^2 = {eta_p2:.3f}")

    # Post-hoc (Bonferroni)
    print("\n--- Bonferroni-corrected pairwise comparisons ---")
    n_comp = len(groups) * (len(groups) - 1) // 2
    alpha_adj = 0.05 / n_comp
    print(f"(adjusted alpha = {alpha_adj:.4f})")
    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            t, pp = stats.ttest_ind(samples[i], samples[j])
            pp_adj = min(pp * n_comp, 1.0)
            d = cohens_d_independent(samples[i], samples[j])
            mark = " *" if pp_adj < 0.05 else ""
            print(f"  {groups[i]} vs {groups[j]}: t={t:.2f}, P_adj {fmt_p(pp_adj)}, d={d:.2f}{mark}")

    print("\n--- Draft Results paragraph ---")
    if lang == "zh":
        print(f"单因素方差分析显示 {group} 对 {dv} 有"
              f"{'显著' if p < 0.05 else '无显著'}主效应，"
              f"F({df_between}, {df_within}) = {f:.3f}, P {fmt_p(p)}, "
              f"偏 η² = {eta_p2:.3f}。")
    else:
        sig = "a" if p < 0.05 else "no"
        print(f"A one-way ANOVA revealed {sig} significant effect of {group} on {dv}, "
              f"F({df_between}, {df_within}) = {f:.3f}, P {fmt_p(p)}, "
              f"partial eta^2 = {eta_p2:.3f}.")


def correlation(df, x, y, method="pearson", lang="en"):
    a = df[[x, y]].dropna()
    if method == "pearson":
        r, p = stats.pearsonr(a[x], a[y])
        label = "Pearson's r"
    else:
        r, p = stats.spearmanr(a[x], a[y])
        label = "Spearman's rho"
    n = len(a)
    # Fisher z CI for Pearson
    if method == "pearson" and abs(r) < 1:
        z = math.atanh(r)
        se = 1 / math.sqrt(n - 3)
        zcrit = stats.norm.ppf(0.975)
        lo, hi = math.tanh(z - zcrit * se), math.tanh(z + zcrit * se)
    else:
        lo = hi = float("nan")

    print(f"=== {label} ===")
    print(f"n = {n}")
    print(f"{label} = {r:.3f}, P {fmt_p(p)}")
    if not math.isnan(lo):
        print(f"95% CI: {lo:.2f} to {hi:.2f}")

    print("\n--- Draft Results paragraph ---")
    if lang == "zh":
        direction = "正" if r > 0 else "负"
        print(f"{x} 与 {y} 之间存在{'显著' if p < 0.05 else '无显著'}{direction}相关，"
              f"r = {r:.2f}, P {fmt_p(p)}（95% CI {lo:.2f}–{hi:.2f}, n = {n}）。")
    else:
        direction = "positively" if r > 0 else "negatively"
        sig = "" if p < 0.05 else " not"
        print(f"{x} was{sig} significantly {direction} associated with {y} "
              f"(r = {r:.2f}, P {fmt_p(p)}, 95% CI {lo:.2f} to {hi:.2f}, n = {n}).")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_d = sub.add_parser("describe")
    p_d.add_argument("file")
    p_d.add_argument("--by", default=None)

    p_t = sub.add_parser("ttest")
    p_t.add_argument("file")
    p_t.add_argument("--dv", required=True)
    p_t.add_argument("--group", required=True)
    p_t.add_argument("--lang", default="en", choices=["en", "zh"])

    p_p = sub.add_parser("paired")
    p_p.add_argument("file")
    p_p.add_argument("--pre", required=True)
    p_p.add_argument("--post", required=True)
    p_p.add_argument("--lang", default="en", choices=["en", "zh"])

    p_a = sub.add_parser("anova")
    p_a.add_argument("file")
    p_a.add_argument("--dv", required=True)
    p_a.add_argument("--group", required=True)
    p_a.add_argument("--lang", default="en", choices=["en", "zh"])

    p_c = sub.add_parser("corr")
    p_c.add_argument("file")
    p_c.add_argument("--x", required=True)
    p_c.add_argument("--y", required=True)
    p_c.add_argument("--method", default="pearson", choices=["pearson", "spearman"])
    p_c.add_argument("--lang", default="en", choices=["en", "zh"])

    args = ap.parse_args()
    df = load(args.file)

    if args.cmd == "describe":
        print(describe(df, by=args.by))
    elif args.cmd == "ttest":
        independent_ttest(df, args.dv, args.group, args.lang)
    elif args.cmd == "paired":
        paired_ttest(df, args.pre, args.post, args.lang)
    elif args.cmd == "anova":
        one_way_anova(df, args.dv, args.group, args.lang)
    elif args.cmd == "corr":
        correlation(df, args.x, args.y, args.method, args.lang)


if __name__ == "__main__":
    main()
