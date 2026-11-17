#!/usr/bin/env python3
"""Find content in old/ that is genuinely missing from the root cheat sheets.

old/ contains two formats of the same cheat sheets:
  * rendered pages (identical style to root)  -> literal line comparison
  * tldr markdown source (``> description`` / ``- example:`` / ```cmd {{x}}` ``)
    -> each command is matched against the command lines of the root page;
       unmatched entries are "extra" content worth merging.

Matching is deliberately layered, because cheat.sh renders tldr source in
several different ways (`{{[-t|--type]}} {{ruby}}` can become `--type=ruby`,
`--type ruby`, or `-t ruby`):

  1. tolerant regex: every `{{placeholder}}` matches any rendered value;
  2. fingerprint: command words + option flags (with `=value` stripped);
  3. fuzzy similarity of the normalized command strings.

An entry is only reported as extra when all three fail, which keeps precision
high and avoids adding near-duplicate examples back to the root pages.

Output: tools/semantic_report.json plus a summary on stdout.

Usage: python3 tools/semantic_compare.py [--repo /path/to/repo] [--show 25]
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
from collections import Counter
from pathlib import Path

SECTION_RE = re.compile(r"^\s*(cheat\.sheets:|cheat:|tldr:)\S+\s*$")
PLACEHOLDER_RE = re.compile(r"\{\{(?:(?!\}\}).)*\}\}")
BACKTICK_CMD_RE = re.compile(r"^`(.*)`\s*$")
VALUE_WORDS = {
    "path", "file", "url", "string", "pattern", "example", "device", "value",
    "integer", "number", "code", "text", "directory", "file_or_directory",
}


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="surrogateescape").splitlines()


def is_root_command(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if s.startswith("#"):
        return False
    if SECTION_RE.match(s):
        return False
    if s in {"---"} or s.startswith("tags:") or s.startswith("---"):
        return False
    return True


def placeholder_choices(inner: str) -> list[str]:
    """Return readable alternatives for the contents of a `{{...}}` group."""
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    choices = [c.strip() for c in inner.split("|") if c.strip()]
    return choices or [""]


def command_variants(cmd: str) -> list[str]:
    """Expand tldr `{{a|b}}` alternatives into concrete candidate commands."""
    matches = list(PLACEHOLDER_RE.finditer(cmd))
    if not matches:
        return [cmd]
    variants = [""]
    pos = 0
    for m in matches:
        literal = cmd[pos:m.start()]
        choices = placeholder_choices(m.group(0)[2:-2])
        variants = [v + literal + c for v in variants for c in choices[:4]]
        variants = variants[:24]
        pos = m.end()
    tail = cmd[pos:]
    return [v + tail for v in variants]


def command_regex(cmd: str) -> re.Pattern[str]:
    """Regex where every `{{placeholder}}` is a wildcard."""
    parts: list[str] = []
    pos = 0
    for m in PLACEHOLDER_RE.finditer(cmd):
        parts.append(re.escape(cmd[pos:m.start()]))
        parts.append(r".*?")
        pos = m.end()
    parts.append(re.escape(cmd[pos:]))
    return re.compile(r"^\s*" + "".join(parts) + r"\s*$", re.DOTALL)


def normalize_tokens(cmd: str) -> list[str]:
    """Tokens kept for loose comparison: words + option flags, values -> '*'."""
    cmd = PLACEHOLDER_RE.sub(" * ", cmd)
    cmd = cmd.replace("`", " ").replace('"', " ").replace("'", " ")
    tokens: list[str] = []
    for raw in cmd.split():
        tok = raw.strip("(),;")
        if not tok:
            continue
        # `--type=noruby` -> `--type`
        if tok.startswith("-") and "=" in tok:
            tok = tok.split("=", 1)[0]
        if tok.startswith("-") and len(tok) > 1:
            tokens.append(tok.lower())
        elif tok == "*" or re.search(r"[<>/{}*:@]|^\d+$|[0-9]", tok) \
                or tok.lower() in VALUE_WORDS:
            tokens.append("*")
        else:
            tokens.append(tok.lower())
    return tokens


def fingerprint(cmd: str) -> tuple[str, frozenset[str]]:
    """Loose fingerprint: leading command words + set of option flags."""
    toks = normalize_tokens(cmd)
    words = [t for t in toks if not t.startswith("-") and t != "*"]
    flags = frozenset(t for t in toks if t.startswith("-"))
    return (words[0] if words else "", flags | frozenset(words[1:3]))


def compact(cmd: str) -> str:
    """Alphanumeric skeleton: ignores punctuation/spacing and tldr placeholders.

    Catches renderings such as `--type=noruby` vs `--type no{{ruby}}`.
    """
    cmd = PLACEHOLDER_RE.sub("", cmd)
    return re.sub(r"[^a-z0-9]", "", cmd.lower())


def parse_tldr_source(lines: list[str]) -> dict:
    """Return entries and metadata lines in source order."""
    entries: list[dict] = []
    desc: str | None = None
    for line in lines:
        s = line.strip()
        if s.startswith("- "):
            desc = s[2:].rstrip()
        elif (m := BACKTICK_CMD_RE.match(s)):
            entries.append({"description": desc, "command": m.group(1), "raw": s})
        elif s.startswith("`") and s.endswith("`") and len(s) > 2:
            entries.append({"description": desc, "command": s[1:-1], "raw": s})
    metadata = [s for line in lines if (s := line.strip()).startswith("> ")]
    return {"entries": entries, "metadata": metadata}


def render_command(cmd: str) -> str:
    """Render a tldr source command into the plain style used by root pages."""
    def sub(m: re.Match[str]) -> str:
        inner = m.group(0)[2:-2]
        choices = placeholder_choices(inner)
        # prefer the long option, it is the most readable plain rendering
        long = [c for c in choices if c.startswith("--")]
        return (long[0] if long else choices[0])
    return PLACEHOLDER_RE.sub(sub, cmd)


def render_metadata(text: str) -> str:
    return "# " + text


def is_new_topic_metadata(text: str, root_lines: list[str]) -> bool:
    """Keep only metadata that introduces information absent from the root page.

    Skip bare description rewrites and `More information` URL updates; keep
    `See also`, `Note`, `Warning`, `Error codes`, ... when the root page has no
    line with that same lead-in.
    """
    text = text.strip()
    if ":" not in text:
        return False
    topic = text.split(":", 1)[0].strip()
    if topic.lower() in {"more information", "see <https", "upload code to <https"}:
        return False
    if len(topic.split()) > 4:
        return False
    prefix = "# " + topic.lower() + ":"
    return not any(line.strip().lower().startswith(prefix) for line in root_lines)


def compare_file(old_file: Path, root_file: Path) -> dict:
    old_lines = read_lines(old_file)
    has_tldr_markers = any(line.lstrip().startswith(("> ", "- ")) for line in old_lines)
    root_lines = read_lines(root_file) if root_file.is_file() else []
    root_norm = [x.rstrip() for x in root_lines]
    root_cmds = [x.strip() for x in root_norm if is_root_command(x)]
    root_norms = [" ".join(normalize_tokens(c)) for c in root_cmds]
    root_prints = [fingerprint(c) for c in root_cmds]
    root_compacts = [compact(c) for c in root_cmds]
    root_text = "\n".join(root_norm)

    if not has_tldr_markers:
        extra = [x for x in old_lines if x.rstrip() and x.rstrip() not in root_norm]
        return {
            "format": "rendered",
            "entries": len([x for x in old_lines if x.strip() and not x.startswith("#")]),
            "extra_lines": extra,
            "extra_entries": [],
            "extra_metadata": [],
        }

    parsed = parse_tldr_source(old_lines)
    extra_entries: list[dict] = []
    for entry in parsed["entries"]:
        cmd = entry["command"]
        regex = command_regex(cmd)
        variants = command_variants(cmd)
        matched = False
        for variant in variants:
            if regex.match(cmd) and any(regex.match(c) for c in root_cmds):
                matched = True
                break
            fp = fingerprint(variant)
            if fp in root_prints:
                matched = True
                break
            vt = " ".join(normalize_tokens(variant))
            vc = compact(variant)
            for rt, rc in zip(root_norms, root_compacts):
                if vt and difflib.SequenceMatcher(None, vt, rt).ratio() >= 0.88:
                    matched = True
                    break
                if vc and difflib.SequenceMatcher(None, vc, rc).ratio() >= 0.92:
                    matched = True
                    break
            if matched:
                break
        if not matched:
            extra_entries.append({
                "description": entry["description"],
                "command": cmd,
                "rendered": render_command(cmd),
            })

    extra_metadata: list[str] = []
    for meta in parsed["metadata"]:
        text = meta[2:].strip()
        core = re.sub(r"^#\s*", "", text)
        if core and core not in root_text and text not in root_text \
                and is_new_topic_metadata(text, root_norm):
            extra_metadata.append(text)

    return {
        "format": "tldr_source",
        "entries": len(parsed["entries"]),
        "extra_lines": [],
        "extra_entries": extra_entries,
        "extra_metadata": extra_metadata,
    }


def target_name(name: str, repo: Path) -> str:
    """Map `foo_1` / `foo.1` tldr source duplicates to their root page `foo`."""
    if name.endswith("_1") and (repo / name[:-2]).is_file():
        return name[:-2]
    if name.endswith(".1") and (repo / name[:-2]).is_file():
        return name[:-2]
    return name


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--show", type=int, default=25)
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    old_dir = repo / "old"

    rows = []
    for old_file in sorted(p for p in old_dir.iterdir() if p.is_file()):
        target = target_name(old_file.name, repo)
        root_file = repo / target
        info = compare_file(old_file, root_file)
        info.update({
            "name": old_file.name,
            "target": target,
            "root_exists": root_file.is_file(),
            "root_bytes": root_file.stat().st_size if root_file.is_file() else 0,
        })
        rows.append(info)

    total_entries = sum(r["entries"] for r in rows)
    total_extra_entries = sum(len(r["extra_entries"]) for r in rows)
    total_extra_lines = sum(len(r["extra_lines"]) for r in rows)
    total_extra_meta = sum(len(r["extra_metadata"]) for r in rows)
    affected = [r for r in rows if r["extra_entries"] or r["extra_lines"] or r["extra_metadata"]]
    clean = len(rows) - len(affected)

    print(f"old files analyzed            : {len(rows)}")
    print(f"old command entries           : {total_entries}")
    print(f"clean (fully duplicated)      : {clean}")
    print(f"files with extra content      : {len(affected)}")
    print(f"  extra rendered lines        : {total_extra_lines}")
    print(f"  extra tldr example commands : {total_extra_entries}")
    print(f"  extra new-topic metadata    : {total_extra_meta}")

    dist = Counter(min(len(r["extra_entries"]), 20) for r in rows)
    print("\nextra-commands-per-file distribution (capped at 20):")
    for k in sorted(dist):
        print(f"  {k:>2}: {dist[k]} files")

    print("\nsample files with extras:")
    for r in sorted(affected, key=lambda x: -len(x["extra_entries"]))[:args.show]:
        print(f"  {r['name']:<28} target={r['target']:<24} "
              f"extras={len(r['extra_entries']):<3} lines={len(r['extra_lines']):<3} "
              f"meta={len(r['extra_metadata'])}")

    print("\nsample extra entries:")
    shown = 0
    for r in affected:
        for e in r["extra_entries"]:
            print(f"  [{r['name']}] - {e['description']}  =>  {e['rendered']}")
            shown += 1
            if shown >= args.show:
                break
        if shown >= args.show:
            break

    out = repo / "tools" / "semantic_report.json"
    out.write_text(json.dumps({"rows": rows}, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"\nFull report: {out}")


if __name__ == "__main__":
    main()
