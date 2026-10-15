"""sportsci_figures.results — from a design spec + data to a publication-style Results section (zh / en).

    from sportsci_figures.results import run_results, load_spec, simulate
    run_results("design.json", "data.csv", "results_out", lang="both")

Designs: parallel_prepost | crossover | multitime | meta | single_group | survey.   Spec reference: reference/DESIGN_SPEC.md.
"""
from .analysis import analyze, load_data
from .build import run_results
from .simulate import simulate
from .spec import DESIGNS, SpecError, load_spec, validate_spec

__all__ = ["run_results", "analyze", "load_data", "simulate", "load_spec", "validate_spec", "DESIGNS", "SpecError"]
