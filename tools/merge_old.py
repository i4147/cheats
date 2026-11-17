#!/usr/bin/env python3
"""Merge the extra content of old/ into the root cheat sheets, then remove old/.

Rules
-----
* healthy root page   -> append only the extra examples / metadata found by
                         semantic_compare.py, rendered in the root's plain
                         `# description` + `command` style.
* empty / missing / HTML-error root page -> rebuild the page from the old/
                         file (tldr markdown is rendered to the plain style).
* everything else in old/ is a semantic duplicate and is simply discarded.

The tldr source files are rendered to plain cheat-sheet style: `> text` and
`- example:` become `# text` / `# example:`, and `{{placeholders}}` are
resolved to their most readable option (the long flag when there is a choice).

Idempotent: re-running it will not append the same lines twice.

Usage:
    python3 tools/merge_old.py            # dry run, prints planned changes
    python3 tools/merge_old.py --apply    # write root pages and delete old/
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"\{\{(?:(?!\}\}).)*\}\}")
BACKTICK_CMD_RE = re.compile(r"^`(.*)`\s*$")


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="surrogateescape").splitlines()


def placeholder_choices(inner: str) -> list[str]:
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    return [c.strip() for c in inner.split("|") if c.strip()] or [""]


def render_command(cmd: str) -> str:
    def sub(m: re.Match[str]) -> str:
        choices = placeholder_choices(m.group(0)[2:-2])
        long = [c for c in choices if c.startswith("--")]
        return long[0] if long else choices[0]
    return PLACEHOLDER_RE.sub(sub, cmd)


def render_tldr_page(lines: list[str], name: str) -> list[str]:
    """Convert a tldr markdown page into the plain style used by root pages."""
    out: list[str] = []
    for line in lines:
        s = line.strip()
        if s.startswith("# "):
            out.append(s)
        elif s.startswith("> "):
            out.append("# " + s[2:].strip())
        elif s.startswith("- "):
            out.append("# " + s[2:].strip())
        elif (m := BACKTICK_CMD_RE.match(s)):
            out.append(render_command(m.group(1)))
        elif s.startswith("`") and s.endswith("`") and len(s) > 2:
            out.append(render_command(s[1:-1]))
        elif not s:
            out.append("")
    if not out or not out[0].startswith("# "):
        out.insert(0, "# " + name)
    # collapse repeated blank lines
    cleaned: list[str] = []
    for line in out:
        if line == "" and cleaned and cleaned[-1] == "":
            continue
        cleaned.append(line)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()
    return cleaned


def root_health(path: Path) -> str:
    if not path.is_file():
        return "missing"
    text = path.read_text(encoding="utf-8", errors="surrogateescape")
    if not text.strip():
        return "empty"
    if "<html" in text.lower()[:400] or "Bad Request" in text[:400]:
        return "html_error"
    return "normal"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    report = json.loads((repo / "tools" / "semantic_report.json").read_text())
    rows = report["rows"]

    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[row["target"]].append(row)

    stats = {
        "targets": len(groups),
        "restored": 0,
        "appended_files": 0,
        "appended_commands": 0,
        "appended_metadata": 0,
        "appended_lines": 0,
        "unchanged": 0,
        "old_files_removed": 0,
    }
    plan: list[str] = []

    for target, contributions in sorted(groups.items()):
        root_file = repo / target
        health = root_health(root_file)
        existing = read_lines(root_file) if root_file.is_file() else []
        existing_stripped = {x.strip() for x in existing}

        if health in {"missing", "empty", "html_error"}:
            # Pick the richest old/ source for this page. Prefer a rendered
            # page (already in root style), otherwise render the tldr source.
            rendered = [r for r in contributions if r["format"] == "rendered"]
            source = (rendered or contributions)[0]
            old_file = repo / "old" / source["name"]
            old_lines = read_lines(old_file)
            if source["format"] == "rendered":
                content = old_lines
            else:
                content = render_tldr_page(old_lines, target)
            new_text = "\n".join(content) + "\n"
            if root_file.is_file() and root_file.read_text(
                    encoding="utf-8", errors="surrogateescape") == new_text:
                stats["unchanged"] += 1
                continue
            stats["restored"] += 1
            plan.append(f"RESTORE {target:<32} from old/{source['name']} "
                        f"[{health}, {len(content)} lines]")
            if args.apply:
                root_file.write_text(new_text, encoding="utf-8",
                                     errors="surrogateescape")
            continue

        additions: list[str] = []
        seen: set[str] = set()

        def add(line: str, dedupe_existing: bool = True) -> bool:
            key = line.strip()
            if not key or key in seen or (dedupe_existing and key in existing_stripped):
                return False
            seen.add(key)
            additions.append(line)
            return True

        for r in contributions:
            for meta in r["extra_metadata"]:
                if add("# " + meta.strip()):
                    stats["appended_metadata"] += 1
            for entry in r["extra_entries"]:
                cmd = entry["rendered"].strip()
                # Skip the whole entry when the command is already present.
                # This makes re-running the merge a no-op.
                if not cmd or cmd in existing_stripped or cmd in seen:
                    continue
                desc = entry["description"]
                # keep every description, even if a similar comment already
                # exists, so each merged command keeps its own explanation
                if desc and add("# " + desc.strip(), dedupe_existing=False):
                    stats["appended_lines"] += 1
                if add(cmd):
                    stats["appended_commands"] += 1
            for line in r["extra_lines"]:
                if add(line.rstrip()):
                    stats["appended_lines"] += 1

        if not additions:
            stats["unchanged"] += 1
            continue

        block = additions
        base = "\n".join(existing).rstrip("\n")
        new_text = base + "\n" + "\n".join(block) + "\n"
        stats["appended_files"] += 1
        plan.append(f"APPEND  {target:<32} +{len(block)} lines "
                    f"({sum(1 for r in contributions for _ in r['extra_entries'])} "
                    f"extra examples)")
        if args.apply:
            root_file.write_text(new_text, encoding="utf-8",
                                 errors="surrogateescape")

    if args.apply:
        old_dir = repo / "old"
        old_files = [p for p in old_dir.iterdir() if p.is_file()] if old_dir.exists() else []
        stats["old_files_removed"] = len(old_files)
        for p in old_files:
            p.unlink()
        if old_dir.exists():
            old_dir.rmdir()

    print("\n".join(plan[:40]))
    if len(plan) > 40:
        print(f"... and {len(plan) - 40} more changes")
    print("\nSTATS")
    for k, v in stats.items():
        print(f"  {k:<22}: {v}")
    print("mode:", "APPLIED" if args.apply else "DRY RUN (use --apply)")


if __name__ == "__main__":
    main()
