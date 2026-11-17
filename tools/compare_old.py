#!/usr/bin/env python3
"""Compare every file in old/ with its counterpart in the repository root.

Categories
----------
identical      : byte-for-byte equal to the root file (after trailing-newline normalization)
duplicate      : every non-blank line of the old file is present in the root file
                 (root is a superset; old/ copy is unnecessary)
extra          : the old file contains lines that are NOT in the root file
                 (content must be merged into the root file)
missing_root   : no file with that name exists in the root (must be moved there)

Writes a JSON report to ``tools/old_comparison_report.json`` (gitignored) and
prints a summary plus the first N names in each category.

Usage: python3 tools/compare_old.py [--repo /path/to/repo] [--show 40]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def read_lines(path: Path) -> list[str]:
    """Return logical lines, ignoring a missing final newline."""
    return path.read_text(encoding="utf-8", errors="surrogateescape").splitlines()


def normalize(line: str) -> str:
    """Comparison key: ignore trailing whitespace only (leading is meaningful here)."""
    return line.rstrip()


def compare(old_root: Path, repo_root: Path, show: int) -> dict:
    old_files = sorted(p for p in old_root.iterdir() if p.is_file())
    categories: dict[str, list[str]] = {
        "identical": [],
        "duplicate": [],
        "extra": [],
        "missing_root": [],
    }
    details: list[dict] = []

    for old_file in old_files:
        name = old_file.name
        root_file = repo_root / name
        old_lines = read_lines(old_file)
        old_norm = [normalize(x) for x in old_lines]
        old_nonblank = [x for x in old_norm if x.strip()]

        if not root_file.is_file():
            categories["missing_root"].append(name)
            details.append({
                "name": name,
                "category": "missing_root",
                "old_lines": len(old_lines),
                "old_nonblank": len(old_nonblank),
            })
            continue

        root_lines = read_lines(root_file)
        root_norm = [normalize(x) for x in root_lines]
        root_nonblank = [x for x in root_norm if x.strip()]

        if old_norm == root_norm:
            categories["identical"].append(name)
            details.append({
                "name": name,
                "category": "identical",
                "old_lines": len(old_lines),
                "root_lines": len(root_lines),
            })
            continue

        # multiset comparison, so repeated lines are accounted for
        root_counter = Counter(root_nonblank)
        old_counter = Counter(old_nonblank)
        missing = old_counter - root_counter          # lines only in old/
        added = root_counter - old_counter            # lines only in root
        missing_lines = sum(missing.values())
        added_lines = sum(added.values())

        # subsequence check: is old/ content a contiguous/ordered subset of root?
        try:
            it = iter(root_norm)
            ordered_subset = all(any(candidate == line for candidate in it)
                                 for line in old_norm)
        except (UnicodeError, ValueError):
            ordered_subset = False

        category = "duplicate" if missing_lines == 0 else "extra"
        categories[category].append(name)
        details.append({
            "name": name,
            "category": category,
            "old_lines": len(old_lines),
            "root_lines": len(root_lines),
            "old_nonblank": len(old_nonblank),
            "missing_from_root": missing_lines,
            "added_in_root": added_lines,
            "old_ordered_subset": ordered_subset,
            "missing_sample": [line for line in old_nonblank
                               if line in missing][:8],
        })

    report = {
        "old_file_count": len(old_files),
        "counts": {k: len(v) for k, v in categories.items()},
        "categories": categories,
        "details": details,
    }
    out = repo_root / "tools" / "old_comparison_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--show", type=int, default=40)
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    report = compare(repo / "old", repo, args.show)

    print(f"old/ files examined : {report['old_file_count']}")
    for key, count in report["counts"].items():
        print(f"  {key:<14}: {count}")
    for key, names in report["categories"].items():
        if not names:
            continue
        print(f"\n--- {key} ({len(names)}) ---")
        for name in names[:args.show]:
            print(f"  {name}")
        if len(names) > args.show:
            print(f"  ... and {len(names) - args.show} more")
    print(f"\nFull report: {repo / 'tools' / 'old_comparison_report.json'}")


if __name__ == "__main__":
    main()
