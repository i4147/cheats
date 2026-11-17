#!/usr/bin/env python3
"""Download every topic in list.txt from cheat.sh into <topic>.txt files."""

import sys
import time
import random
from pathlib import Path
from multiprocessing import Pool, Value, Lock
from dh import runcmd
import re

WORKERS = 2
MIN_INTERVAL = 0.20  # seconds between request starts, GLOBAL across workers
JITTER = 0.05  # extra random delay [0, JITTER] — avoids synchronized bursts
_ANSI_RE = re.compile(
    r"\x1B"
    r"(?:"
    r"\[[0-?]*[ -/]*[@-~]"  # CSI:  \x1b[...m, \x1b[K, \x1b[2J, …
    r"|\][^\x07\x1B]*(?:\x07|\x1B\\)"  # OSC:  \x1b]0;title\x07
    r"|[PX^_][^\x1B]*\x1B\\"  # DCS / SOS / PM / APC
    r"|[@-Z\\-_]"  # single-char escapes
    r")"
)
_CTRL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_BACKSPACE_RE = re.compile(r"[^\n]\x08")


def clean_text(text: str) -> str:
    """Strip ANSI escapes, control chars, and \\r / backspace artifacts."""
    text = _ANSI_RE.sub("", text)
    prev = None
    while prev != text:
        prev = text
        text = _BACKSPACE_RE.sub("", text)
    text = text.replace("\x08", "")
    text = text.replace("\r\n", "\n")
    text = "\n".join(line.rsplit("\r", 1)[-1] for line in text.split("\n"))
    text = _CTRL_RE.sub("", text)
    text = "\n".join(ln.rstrip() for ln in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return text


BASE_URL = "https://cheat.sh/"  # trailing slash is required
LIST_FILE = "list"
# Shared rate-limiter state (populated in each worker via _init_worker)
_rate_last = None
_rate_lock = None


def _init_worker(last, lock):
    global _rate_last, _rate_lock
    _rate_last = last
    _rate_lock = lock


def _throttle():
    """Block until it's this worker's global turn to fire a request.
    Holding the lock during the sleep serialises request starts — that's
    exactly the rate limit we want. Effective rate ≈ 1 / MIN_INTERVAL req/s
    regardless of how many workers are running.
    """
    with _rate_lock:
        now = time.monotonic()
        wait = _rate_last.value + MIN_INTERVAL - now
        if wait > 0:
            time.sleep(wait)
        j = random.uniform(0, JITTER)
        if j > 0:
            time.sleep(j)
        _rate_last.value = time.monotonic()


def _fetch_one(args):
    """Worker: throttled download + save of a single topic."""
    i, total, line = args
    fname = line.replace("/", "_").replace(":", "_") + ".txt"
    if Path(fname).exists():
        return (i, line, "skip", fname)
    _throttle()
    try:
        url = BASE_URL + line
        # -f                : treat HTTP >=400 as failure (so 429/404 don't get saved as content)
        # --retry 3         : curl retries transient errors incl. 429 & 5xx
        # --retry-delay 2   : base delay between retries
        # --retry-all-errors: also retry connection resets/refused
        res, txt, _err = runcmd(
            ["curl", "-f", "-sS", "--retry", "3", "--retry-delay", "2", "--retry-all-errors", url],
            show_output=False,
        )
        if not res:
            # Leave a breadcrumb with whatever came back; do NOT save as .txt
            return (i, line, "fail", clean_text(txt)[:400])
        cleaned = clean_text(txt)
        Path(fname).write_text(cleaned, encoding="utf-8")
        return (i, line, "ok", fname)
    except Exception as e:
        return (i, line, "fail", repr(e))


def main() -> int:
    list_path = Path(LIST_FILE)
    if not list_path.exists():
        print(f"Error: {LIST_FILE} not found", file=sys.stderr)
        return 1
    topics = [
        line.strip()
        for line in list_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    # de-dup in case list has duplicates (avoids racing exist-check)
    topics = list(dict.fromkeys(topics))
    if not topics:
        print("list.txt is empty", file=sys.stderr)
        return 1
    rate = 1.0 / MIN_INTERVAL
    print(f"Downloading {len(topics)} topics from {BASE_URL}")
    print(f"  workers={WORKERS}, rate limit ≈ {rate:.1f} req/s " f"(MIN_INTERVAL={MIN_INTERVAL}s)\n", flush=True)
    tasks = [(i, len(topics), line) for i, line in enumerate(topics, 1)]
    last_ts = Value("d", 0.0)
    lock = Lock()
    ok = failed = skipped = 0
    with Pool(processes=WORKERS, initializer=_init_worker, initargs=(last_ts, lock)) as pool:
        for i, line, status, info in pool.imap_unordered(_fetch_one, tasks):
            if status == "ok":
                ok += 1
                print(f"[{i}/{len(topics)}] ok   {line}", flush=True)
            elif status == "skip":
                skipped += 1
                print(f"[{i}/{len(topics)}] skip {line}", flush=True)
            else:
                failed += 1
                print(f"[{i}/{len(topics)}] FAIL {line}: {info}", file=sys.stderr, flush=True)
    print(f"\nDone: {ok} saved, {skipped} skipped, {failed} failed " f"(of {len(topics)})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
