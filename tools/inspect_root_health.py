#!/usr/bin/env python3
"""Classify the health of root counterparts of old/ files and bucket metadata.

Usage: python3 tools/inspect_root_health.py [--repo /path/to/repo]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="surrogateescape")


def classify(root: Path) -> str:
    if not root.is_file():
        return "missing"
    text = read_text(root)
    if not text.strip():
        return "empty"
    if "<html" in text.lower()[:400] or "Bad Request" in text[:400]:
        return "html_error"
    return "normal"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    rows = json.loads((repo / "tools" / "semantic_report.json").read_text())["rows"]

    health: Counter[str] = Counter()
    unhealthy: list[str] = []
    for r in rows:
        state = classify(repo / r["target"])
        health[state] += 1
        if state != "normal":
            unhealthy.append(f"{r['name']} -> {r['target']} [{state}]")
    print("root counterpart health:")
    for k, v in health.most_common():
        print(f"  {k:<12}: {v}")
    print("\nunhealthy counterparts:")
    for line in unhealthy[:60]:
        print("  " + line)

    meta_topics: Counter[str] = Counter()
    for r in rows:
        for m in r["extra_metadata"]:
            topic = m.split(":", 1)[0].strip() if ":" in m else "<description>"
            meta_topics[topic[:40]] += 1
    print("\nextra metadata topics (top 25):")
    for k, v in meta_topics.most_common(25):
        print(f"  {k:<42}: {v}")


if __name__ == "__main__":
    main()
