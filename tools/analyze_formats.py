#!/usr/bin/env python3
"""Classify the format of old/ files and the section layout of root files.

old/ holds two kinds of snapshots of the same cheat sheets:
  * "rendered"    - plain cheat.sheets style: `# comment` + bare command lines
  * "tldr_source" - tldr markdown: `> description`, `- example:`, backticked
                    commands with `{{placeholders}}`
Root files are rendered pages, sometimes combined from several sources with
markers such as `cheat.sheets:name`, ` cheat:name`, ` tldr:name`.

Usage: python3 tools/analyze_formats.py [--repo /path/to/repo]
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

SECTION_RE = re.compile(r"^\s*(cheat\.sheets:|cheat:|tldr:)(\S+)\s*$")


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="surrogateescape").splitlines()


def old_format(lines: list[str]) -> str:
    if any(line.startswith("> ") or line.startswith("- ") for line in lines) \
            and any("{{" in line for line in lines):
        return "tldr_source"
    if any(line.startswith("> ") or line.startswith("- ") for line in lines):
        return "tldr_source_no_placeholders"
    if any(line.startswith("# ") for line in lines):
        return "rendered"
    return "other"


def root_sections(lines: list[str]) -> list[str]:
    return [m.group(1) for line in lines
            if (m := SECTION_RE.match(line.rstrip()))]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    old_dir = repo / "old"

    rows = []
    fmt_counter: Counter[str] = Counter()
    section_counter: Counter[str] = Counter()
    missing_map: list[str] = []
    for old_file in sorted(p for p in old_dir.iterdir() if p.is_file()):
        lines = read_lines(old_file)
        fmt = old_format(lines)
        fmt_counter[fmt] += 1
        target = old_file.name
        if target.endswith("_1"):
            target = target[:-2]
        root_file = repo / target
        sections = root_sections(read_lines(root_file)) if root_file.is_file() else []
        section_counter[",".join(sections) or "none"] += 1
        if not root_file.is_file():
            missing_map.append(old_file.name)
        rows.append({
            "name": old_file.name,
            "format": fmt,
            "target": target,
            "root_exists": root_file.is_file(),
            "sections": sections,
            "old_lines": len(lines),
            "root_lines": len(read_lines(root_file)) if root_file.is_file() else 0,
        })

    print("old/ formats:")
    for k, v in fmt_counter.most_common():
        print(f"  {k:<30}: {v}")
    print("\nroot section layouts (top 20):")
    for k, v in section_counter.most_common(20):
        print(f"  {k:<45}: {v}")
    print(f"\nold files whose (de-suffixed) root target is missing: {len(missing_map)}")
    for name in missing_map[:30]:
        print(f"  {name}")

    out = repo / "tools" / "format_report.json"
    out.write_text(json.dumps({"rows": rows}, indent=2) + "\n", encoding="utf-8")
    print(f"\nFull report: {out}")


if __name__ == "__main__":
    main()
