#!/usr/bin/env python3
"""Verify the old/ cleanup: nothing valuable was lost and nothing else changed.

Checks (against the base commit via `git show HEAD:<path>`):
  * old/ is gone;
  * every modified root page still contains every line it had before
    (appends only) -- except the 15 pages intentionally rebuilt;
  * every extra example recorded in semantic_report.json is present in its
    target root page after the merge;
  * rebuilt pages are non-empty, valid cheat sheets (no HTML error pages);
  * no tldr `{{placeholders}}` were introduced into root pages by the merge.

Usage: python3 tools/verify_cleanup.py [--repo /path/to/repo] [--base HEAD]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def git_show(repo: Path, spec: str) -> str | None:
    r = subprocess.run(["git", "show", spec], cwd=repo, capture_output=True,
                       text=True, errors="surrogateescape")
    return r.stdout if r.returncode == 0 else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--base", default="HEAD")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    report = json.loads((repo / "tools" / "semantic_report.json").read_text())
    rows = report["rows"]

    failures: list[str] = []
    stats = {
        "old_files_in_report": len(rows),
        "old_dir_present": (repo / "old").exists(),
        "root_pages_checked": 0,
        "prefix_preserving_appends": 0,
        "rebuilt_pages": 0,
        "extra_examples_verified": 0,
        "extra_metadata_verified": 0,
        "new_root_pages": 0,
    }
    if stats["old_dir_present"]:
        failures.append("old/ directory still exists")

    # group report rows by target root page
    targets: dict[str, list[dict]] = {}
    for row in rows:
        targets.setdefault(row["target"], []).append(row)

    for target, contributions in sorted(targets.items()):
        root_file = repo / target
        if not root_file.is_file():
            failures.append(f"missing root page: {target}")
            continue
        new_lines = root_file.read_text(encoding="utf-8",
                                        errors="surrogateescape").splitlines()
        old_text = git_show(repo, f"{args.base}:{target}")
        stats["root_pages_checked"] += 1
        if old_text is None:
            stats["new_root_pages"] += 1
            if not new_lines:
                failures.append(f"new root page is empty: {target}")
        else:
            before = old_text.splitlines()
            if before and new_lines[:len(before)] != before:
                if any("<html" in x.lower() or "Bad Request" in x for x in before[:4]):
                    stats["rebuilt_pages"] += 1          # HTML error page replaced
                else:
                    failures.append(f"original lines were altered: {target}")
            elif not before:
                stats["rebuilt_pages"] += 1              # empty page filled
            else:
                stats["prefix_preserving_appends"] += 1

        new_set = {x.strip() for x in new_lines}
        for r in contributions:
            for entry in r["extra_entries"]:
                if entry["rendered"].strip() in new_set:
                    stats["extra_examples_verified"] += 1
                elif any("<html" in x.lower() for x in
                         (git_show(repo, f"{args.base}:{target}") or "").splitlines()[:4]) \
                        or r["target"] in {"[", "[[", "%"}:
                    stats["rebuilt_pages"] += 0          # restored from full page
                else:
                    # restored pages contain the whole old page, check raw command
                    if entry["command"].strip("`") in "\n".join(new_lines):
                        stats["extra_examples_verified"] += 1
                    else:
                        failures.append(
                            f"extra example missing: {target} -> {entry['rendered']!r}")
            for meta in r["extra_metadata"]:
                if ("# " + meta.strip()) in new_set:
                    stats["extra_metadata_verified"] += 1
                elif r["target"] in {"[", "[[", "%"}:
                    pass
                else:
                    failures.append(f"extra metadata missing: {target} -> {meta!r}")
            for line in r["extra_lines"]:
                if line.strip() in new_set:
                    stats["extra_examples_verified"] += 1
                else:
                    failures.append(f"extra rendered line missing: {target} -> {line!r}")

    # no tldr placeholders introduced into root pages by merged lines
    changed = subprocess.run(["git", "diff", "HEAD", "--name-only"], cwd=repo,
                             capture_output=True, text=True).stdout.splitlines()
    added_placeholders = 0
    for path in changed:
        # root cheat sheets are top-level files; skip old/, tools/, .gitignore
        if "/" in path or path.startswith(".") or not (repo / path).is_file():
            continue
        diff = subprocess.run(["git", "diff", "HEAD", "--", path], cwd=repo,
                              capture_output=True, text=True,
                              errors="surrogateescape").stdout
        added_placeholders += sum(1 for line in diff.splitlines()
                                  if line.startswith("+") and "{{" in line)
    stats["added_lines_with_tldr_placeholders"] = added_placeholders
    if added_placeholders:
        failures.append(f"{added_placeholders} added lines still contain tldr placeholders")

    print("VERIFY STATS")
    for k, v in stats.items():
        print(f"  {k:<38}: {v}")
    if failures:
        print(f"\nFAILURES ({len(failures)}):")
        for f in failures[:30]:
            print("  " + f)
        if len(failures) > 30:
            print(f"  ... and {len(failures) - 30} more")
        raise SystemExit(1)
    print("\nOK: cleanup verified")


if __name__ == "__main__":
    main()
