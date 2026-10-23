#!/usr/bin/env python3
"""Install the sportsci workflow: the three Python packages (editable) and the four skills (copied).

    python install.py                       # pip install -e the packages, copy skills to ~/.claude/skills
    python install.py --dry-run             # print what would happen
    python install.py --no-pip              # only copy the skills
    python install.py --skills-dir DIR      # another skills folder (default: ~/.claude/skills)
    python install.py --no-skills           # only pip install

Standard library only. Existing skill folders are moved to <skills-dir>/../skills-backup/<skill>-<time> first
(never inside the skills folder, where a backup would be loaded as a second copy of the skill).
"""
from __future__ import annotations

import argparse
import datetime
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILLS = ROOT / "skills"
PACKAGES = ["sportsci-topic", "sportsci-figures", "sportsci-refs"]
ALL_SKILLS = ["sportsci-topic", "sportsci-figures", "sportsci-writing", "sportsci-refs"]
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "*.egg-info", ".git")


def plan(args) -> list[str]:
    steps: list[str] = []
    if not args.no_pip:
        for p in PACKAGES:
            steps.append(f"pip install -e {SKILLS / p}")
    if not args.no_skills:
        target = Path(args.skills_dir).expanduser()
        for s in ALL_SKILLS:
            steps.append(f"copy {SKILLS / s} -> {target / s}")
    return steps


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-pip", action="store_true")
    ap.add_argument("--no-skills", action="store_true")
    ap.add_argument("--skills-dir", default="~/.claude/skills")
    args = ap.parse_args(argv)

    missing = [s for s in ALL_SKILLS if not (SKILLS / s / "SKILL.md").is_file()]
    if missing:
        print("missing skill folders:", ", ".join(missing), file=sys.stderr)
        return 2

    for step in plan(args):
        print(("[dry-run] " if args.dry_run else "") + step)
    if args.dry_run:
        return 0

    if not args.no_pip:
        cmd = [sys.executable, "-m", "pip", "install"]
        for p in PACKAGES:
            cmd += ["-e", str(SKILLS / p)]
        rc = subprocess.call(cmd)
        if rc:
            print("pip install failed (exit %d); skills were not copied" % rc, file=sys.stderr)
            return rc

    if not args.no_skills:
        target = Path(args.skills_dir).expanduser()
        target.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = target.parent / "skills-backup"
        for s in ALL_SKILLS:
            dst = target / s
            if dst.exists() or dst.is_symlink():
                backup.mkdir(parents=True, exist_ok=True)
                bak = backup / f"{s}-{stamp}"
                dst.rename(bak)
                print(f"  existing {dst.name} moved to {bak}")
            shutil.copytree(SKILLS / s, dst, ignore=IGNORE)
        print(f"copied {len(ALL_SKILLS)} skills to {target}")

    if not args.no_pip:
        missing = [p for p in PACKAGES if shutil.which(p) is None]
        if missing:
            print("\nThe commands are installed but not on PATH. Either add pip's scripts folder to PATH, or run them as:")
            for p in missing:
                print(f"  python -m {p.replace('-', '_')}.cli --help")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
