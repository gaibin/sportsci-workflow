"""Machine-specific settings (Zotero user ID, data folder, contact e-mail). Nothing personal is ever stored in code.

Priority: environment variables > config file > defaults. The config file is the first of

    $SPORTSCI_REFS_CONFIG            explicit path
    ./config/local.toml              current working folder
    <repository>/config/local.toml   source checkout / skill folder
    ~/.sportsci-refs.toml            per user

Template: config/local.example.toml (copy to config/local.toml; it is git-ignored).

    ZOTERO_API               local API base             (default http://127.0.0.1:23119)
    ZOTERO_USER_ID           numeric user ID used in citation URIs (zotero.org/settings/keys shows it)
    ZOTERO_DATA_DIR          Zotero data folder holding zotero.sqlite (for numeric itemIDs; read from a temporary copy)
    ZOTERO_CITATION_STYLE    CSL style name to remind you to select in Word
    SPORTSCI_CONTACT_EMAIL   sent as mailto in the User-Agent for Crossref / OpenAlex "polite pool" (optional)
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

try:
    import tomllib  # py >= 3.11
except ImportError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class RefConfig:
    zotero_api: str = "http://127.0.0.1:23119"
    zotero_user_id: str = ""
    zotero_data_dir: str = ""
    contact_email: str = ""
    citation_style: str = "china-national-standard-gb-t-7714-2015-numeric"

    @property
    def user_agent(self) -> str:
        return "sportsci-refs/1.0" + (f" (mailto:{self.contact_email})" if self.contact_email else "")


def config_candidates() -> List[Path]:
    out = []
    if os.environ.get("SPORTSCI_REFS_CONFIG"):
        out.append(Path(os.environ["SPORTSCI_REFS_CONFIG"]))
    out += [Path.cwd() / "config" / "local.toml", REPO_ROOT / "config" / "local.toml", Path.home() / ".sportsci-refs.toml"]
    return out


def load_config(path: Optional[Path] = None) -> RefConfig:
    cfg = RefConfig()
    files = [Path(path)] if path else config_candidates()
    for p in files:
        if p.exists() and tomllib:
            data = tomllib.loads(p.read_text(encoding="utf-8")).get("refs", {})
            for k, v in data.items():
                if hasattr(cfg, k):
                    setattr(cfg, k, str(v))
            break
    env = {"ZOTERO_API": "zotero_api", "ZOTERO_USER_ID": "zotero_user_id", "ZOTERO_DATA_DIR": "zotero_data_dir",
           "SPORTSCI_CONTACT_EMAIL": "contact_email", "ZOTERO_CITATION_STYLE": "citation_style"}
    for e, attr in env.items():
        if os.environ.get(e):
            setattr(cfg, attr, os.environ[e])
    cfg.zotero_api = cfg.zotero_api.rstrip("/")
    return cfg
