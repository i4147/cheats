#!/usr/bin/env bash
# Reproduce the old/ -> root cleanup pipeline.
#
#   ./tools/cleanup_old.sh            # analyse + dry-run merge (no changes)
#   ./tools/cleanup_old.sh --apply   # merge, remove old/, verify
#
# The first three analysis scripts need old/ to exist; run them before --apply.
set -euo pipefail

cd "$(dirname "$0")/.."
REPO="$PWD"
APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1

echo "== 1/6 literal line comparison =="
if [[ -d old ]]; then
    python3 tools/compare_old.py --repo "$REPO" --show 0
else
    echo "  skipped: old/ already removed (see tools/old_comparison_report.json)"
fi

echo "== 2/6 format classification =="
if [[ -d old ]]; then
    python3 tools/analyze_formats.py --repo "$REPO"
else
    echo "  skipped: old/ already removed (see tools/format_report.json)"
fi

echo "== 3/6 semantic comparison =="
if [[ -d old ]]; then
    python3 tools/semantic_compare.py --repo "$REPO" --show 0
else
    echo "  using saved tools/semantic_report.json from the original run"
fi

echo "== 4/6 root page health =="
python3 tools/inspect_root_health.py --repo "$REPO"

echo "== 5/6 merge extra content into root =="
if [[ "$APPLY" -eq 1 ]]; then
    python3 tools/merge_old.py --repo "$REPO" --apply
else
    python3 tools/merge_old.py --repo "$REPO"
fi

echo "== 6/6 verify =="
if [[ "$APPLY" -eq 1 ]]; then
    python3 tools/verify_cleanup.py --repo "$REPO"
else
    echo "  skipped: nothing was applied"
fi
