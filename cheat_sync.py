#!/usr/bin/env python3
"""cheat-sync — mirror cheat.sh into ~/.cheats for offline use.
Resumable: non-empty cached files are skipped. Parallel: ThreadPoolExecutor
with a global token-bucket rate limit. Atomic: temp file + os.replace.
"""

from __future__ import annotations
import argparse
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

BASE = "https://cheat.sh"
UA = "cheat-sync/1.0 (+https://github.com/cheat/cheat)"
UNSAFE = re.compile(r"[^A-Za-z0-9._+-]")


# ---------- helpers ---------------------------------------------------------
def safe_name(topic: str) -> str:
    return UNSAFE.sub("_", topic)


def url_for(topic: str) -> str:
    # Match shell version: spaces → '+', keep '/', '+', '-', '.', '_'
    return f"{BASE}/{quote(topic.replace(' ', '+'), safe='+/-._~')}"


def http_get(url: str, timeout: float, retries: int) -> bytes:
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
            if attempt < retries:
                time.sleep(0.5 * 2**attempt)
    raise last  # type: ignore[misc]


class RateLimiter:
    """Serialize dispatch so the *global* request rate stays ≤ per_sec."""

    def __init__(self, per_sec: float) -> None:
        self._interval = 1.0 / per_sec if per_sec > 0 else 0.0
        self._lock = threading.Lock()
        self._next = 0.0

    def wait(self) -> None:
        if self._interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            sleep_for = max(0.0, self._next - now)
            self._next = max(now, self._next) + self._interval
        if sleep_for > 0:
            time.sleep(sleep_for)


# ---------- core ------------------------------------------------------------
def fetch_list(timeout: float, retries: int) -> list[str]:
    data = http_get(f"{BASE}/:list", timeout, retries).decode("utf-8", "replace")
    seen: set[str] = set()
    topics: list[str] = []
    for line in data.splitlines():
        t = line.strip()
        if not t or t.startswith(":"):  # skip meta topics (:learn, :list, …)
            continue
        if t not in seen:
            seen.add(t)
            topics.append(t)
    return topics


def fetch_one(
    topic: str, cache_dir: Path, timeout: float, retries: int, limiter: RateLimiter, use_cache: bool
) -> tuple[str, str]:
    """Returns (topic, status) where status ∈ {'new', 'cached', 'failed'}."""
    out = cache_dir / safe_name(topic)
    if use_cache and out.exists() and out.stat().st_size > 0:
        return topic, "cached"
    limiter.wait()
    try:
        body = http_get(url_for(topic), timeout, retries)
    except Exception:
        return topic, "failed"
    if not body:
        return topic, "failed"
    tmp = cache_dir / f".{safe_name(topic)}.{os.getpid()}.{threading.get_ident()}.part"
    try:
        with open(tmp, "wb") as f:
            f.write(body)
        os.replace(tmp, out)  # atomic on POSIX & NTFS
    except OSError:
        try:
            tmp.unlink()
        except OSError:
            pass
        return topic, "failed"
    return topic, "new"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cheat-sync", description="Mirror cheat.sh into a local cache.")
    ap.add_argument(
        "-d",
        "--dir",
        default=os.environ.get("CHEAT_DIR") or str(Path.home() / ".cheats"),
        help="cache directory (default: ~/.cheats or $CHEAT_DIR)",
    )
    ap.add_argument("-j", "--workers", type=int, default=1, help="parallel workers (default: 1)")
    ap.add_argument(
        "-r",
        "--rate",
        type=float,
        default=10.0,
        help="global requests/sec across all workers (default: 10, 0=unlimited)",
    )
    ap.add_argument("--timeout", type=float, default=20.0, help="per-request timeout seconds")
    ap.add_argument("--retries", type=int, default=2, help="retries per topic")
    ap.add_argument("--refresh", action="store_true", help="re-download even if a cached file already exists")
    args = ap.parse_args(argv)
    cache_dir = Path(args.dir).expanduser()
    cache_dir.mkdir(parents=True, exist_ok=True)
    print("Fetching topic list… ", end="", flush=True)
    try:
        topics = fetch_list(args.timeout, args.retries)
    except Exception as e:
        print(f"FAILED ({e})", file=sys.stderr)
        return 1
    print(f"{len(topics)} topics  →  {cache_dir}")
    limiter = RateLimiter(args.rate)
    counts = {"new": 0, "cached": 0, "failed": 0}
    failed: list[str] = []
    done = 0
    lock = threading.Lock()
    use_cache = not args.refresh
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futures = {
            ex.submit(fetch_one, t, cache_dir, args.timeout, args.retries, limiter, use_cache): t for t in topics
        }
        try:
            for fut in as_completed(futures):
                topic, status = fut.result()
                with lock:
                    counts[status] += 1
                    done += 1
                    if status == "failed":
                        failed.append(topic)
                    if done % 200 == 0 or done == len(topics):
                        print(
                            f"  [{done}/{len(topics)}]  "
                            f"new={counts['new']}  cached={counts['cached']}  "
                            f"failed={counts['failed']}",
                            flush=True,
                        )
        except KeyboardInterrupt:
            print("\nInterrupted — cancelling pending fetches…", file=sys.stderr)
            for f in futures:
                f.cancel()
            return 130
    print(f"Done: new={counts['new']}  cached={counts['cached']}  failed={counts['failed']}")
    if failed:
        preview = ", ".join(failed[:20])
        print(f"Failed topics ({len(failed)}): {preview}" f"{' …' if len(failed) > 20 else ''}", file=sys.stderr)
        print("Re-run to retry — cached entries are skipped.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
