#!/usr/bin/env python3
"""Ad-hoc inspection snippets used while deciding the cleanup policy.

Reproduces the quick cross-tabs and sanity checks that were run inline during
the session. Reads the JSON reports written by the other tools/ scripts and
(optionally) the original files from git via `git show HEAD:<path>`.

Usage: python3 tools/explore_snippets.py [--repo /path/to/repo]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    repo = Path(ap.parse_args().repo).resolve()
    tools = repo / "tools"

    fmt_rows = json.loads((tools / "format_report.json").read_text())["rows"]
    literal = json.loads((tools / "old_comparison_report.json").read_text())
    semantic = json.loads((tools / "semantic_report.json").read_text())["rows"]

    print("== format x root section layout cross-tab ==")
    cross = Counter((r["format"], ",".join(r["sections"]) or "none")
                    for r in fmt_rows)
    for (fmt, layout), n in cross.most_common():
        print(f"  {fmt:<30} {layout:<35} {n}")

    print("\n== old names mapping to the same root page ==")
    by_target: dict[str, list[str]] = defaultdict(list)
    for r in semantic:
        by_target[r["target"]].append(r["name"])
    multi = {k: v for k, v in by_target.items() if len(v) > 1}
    print(f"  {len(multi)} targets have more than one old/ file")
    for k, v in list(multi.items())[:5]:
        print(f"    {k} <- {v}")

    print("\n== rendered old/ pages with literal extra lines ==")
    fmt_by_name = {r["name"]: r["format"] for r in fmt_rows}
    literal_by_name = {d["name"]: d for d in literal["details"]}
    for name, detail in literal_by_name.items():
        if fmt_by_name.get(name) == "rendered" and \
                detail["category"] not in {"identical", "duplicate", "missing_root"}:
            print(f"  {name:<34} {detail.get('missing_from_root')} lines")

    print("\n== rendered extra commands: sanity check ==")
    extras = [(r["name"], e["rendered"]) for r in semantic
              for e in r["extra_entries"]]
    bad = [x for x in extras if "{{" in x[1] or "}}" in x[1]]
    print(f"  {len(extras)} extra commands, {len(bad)} with leftover placeholders")
    for n, c in bad[:5]:
        print(f"    {n}: {c}")

    print("\n== root counterparts already in tldr source format ==")
    tldr_root = []
    for r in semantic:
        result = subprocess.run(["git", "show", f"HEAD:{r['target']}"],
                                cwd=repo, capture_output=True, text=True,
                                errors="surrogateescape")
        if result.returncode:
            continue
        head = result.stdout.splitlines()[:20]
        if any(line.startswith("> ") for line in head[:8]) and \
                any("{{" in line for line in head):
            tldr_root.append(r["name"])
    print(f"  {len(tldr_root)} old/ files have a tldr-source root counterpart")
    print(f"  sample: {tldr_root[:10]}")


if __name__ == "__main__":
    main()
