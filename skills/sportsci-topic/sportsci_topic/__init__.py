"""sportsci_topic — topic selection and study planning for exercise / sport / health science students.

    brief        one TOML form: question (PICO + Chinese/English search terms), outcomes, constraints, effect-size source
    designmap    question type -> one of six designs, with what it permits and forbids
    records      read CNKI / PubMed / Zotero exports (csv, ris, json, txt); nothing is generated
    evidence     evidence map: counts of overlap by population / intervention / outcome, nearest studies, record-set gaps
    power        exact sample size, power at the n you can recruit, smallest detectable effect
    variants     change one axis at a time and recount the overlap
    feasibility  green / yellow / red checks, each with its written rule
    card         one-page topic card (zh / en) and a design.json draft for sportsci-figures

Command line:  sportsci-topic --help   (or `python cli.py --help` from a source checkout)
"""
from .brief import Brief, BriefError, from_dict, load_brief, validate
from .designmap import choose_design
from .evidence import build_evidence
from .feasibility import assess
from .power import plan_sample
from .records import Record, load_records
from .variants import build_variants

__version__ = "1.0.0"
__all__ = ["Brief", "BriefError", "Record", "assess", "build_evidence", "build_variants", "choose_design", "from_dict",
           "load_brief", "load_records", "plan_sample", "validate"]
