# `old/` cleanup helpers

Scripts used to audit `old/`, merge its extra content into the root cheat
sheets, and remove the duplicates. Run them from the repository root (or pass
`--repo /path/to/repo`).

## Pipeline

```bash
./tools/cleanup_old.sh            # analyse + dry run, changes nothing
./tools/cleanup_old.sh --apply    # merge, delete old/, verify
```

| Script | Purpose |
| --- | --- |
| `compare_old.py` | Literal byte/line comparison of each `old/` file with its root counterpart. Writes `old_comparison_report.json`. |
| `analyze_formats.py` | Classifies `old/` pages as tldr markdown source vs. rendered cheat sheets, and lists the section markers of each root page. Writes `format_report.json`. |
| `semantic_compare.py` | The real dedup logic. Matches tldr-source examples against root command lines with a layered matcher (placeholder regex, option-flag fingerprint, fuzzy/compact string similarity). Reports only genuinely missing examples and new-topic metadata. Writes `semantic_report.json`. |
| `inspect_root_health.py` | Finds root counterparts that are missing, empty, or HTML error pages. |
| `merge_old.py` | Dry-run by default; `--apply` appends the extra examples to healthy root pages, rebuilds the 15 broken/missing root pages from `old/`, and deletes `old/`. Idempotent. |
| `verify_cleanup.py` | Verifies against `git show HEAD:<path>` that no original root line was lost, every reported extra example landed in its root page, no tldr placeholders were introduced, and `old/` is gone. |
| `explore_snippets.py` | The ad-hoc cross-tabs / sanity checks used while deciding the policy. |
| `cleanup_old.sh` | Bash driver for the whole pipeline. |

Generated `*_report.json` files are deliberately gitignored; they are
reproducible from `old/` while it still exists, and are kept in `tools/` only
as a local audit trail of the original run.

## What was found

`old/` held 2,321 files in two formats:

* 155 rendered cheat.sheets pages (same plain style as the root);
* 2,166 tldr markdown **source** pages (`> description`, `- example:`,
  `` `command {{placeholder}}` ``), including 101 `*_1` extra snapshots of
  pages that combine several sources in the root.

A literal diff is therefore misleading: the tldr source and the root's
rendered version are the same content in different syntax. After layered
semantic matching, 1,805 of the 2,321 files were fully duplicated by their
root page. The remainder contributed:

* 813 tldr examples absent from the root (newer upstream examples);
* 139 literal lines belonging to root pages that were empty or missing;
* 207 new-topic metadata lines (`See also:`, `Note:`, `Warning:`, ...).

Root page health: 2,305 normal, 12 empty, 1 HTML `400 Bad Request` page, and
2 targets with no root file at all.

## What was done

* 15 root pages rebuilt from `old/` (12 empty, 1 HTML error, 2 new: `ccze`,
  `cpp`). tldr markdown was rendered to the root's plain `# description` +
  `command` style.
* 501 healthy root pages received the extra examples/metadata (791 example
  commands + 791 descriptions + 206 metadata lines = 1,788 appended lines).
  The other 22 missing examples were already covered by the 15 full-page
  restores, so they were not appended a second time.
* The remaining 1,710 root targets were left untouched.
* All 2,321 `old/` files were deleted (31,882 lines / ~9 MB).

Final diff: 514 root pages modified, 2 new root pages, 1,963 root lines added,
7 root lines removed (the HTML error page), 2,321 files deleted.
Verification: `OK: cleanup verified`.
