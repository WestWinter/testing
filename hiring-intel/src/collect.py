#!/usr/bin/env python3
"""Step 2 — Collect raw NVIDIA job-posting data from the public Workday CXS API.

Saves every raw search page and every raw job-detail payload verbatim, wrapped in a
capture envelope (source URL + UTC timestamp). Never parses-and-discards: raw first,
normalize later (normalize.py).

Politeness / stop conditions:
  * single connection, fixed delay between requests (default 1.0s)
  * honest User-Agent (set --contact)
  * aborts the campaign on HTTP 403 (access denied => collection inappropriate)
  * backs off on 429/5xx; aborts after repeated 429

Usage:
  python3 collect.py --out ../data/raw            # full snapshot
  python3 collect.py --probe                      # 1 search page + 1 detail, then exit
  python3 collect.py --max-details 50             # cap detail fetches (testing)

Stdlib only; runs on any Python 3.9+.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

BASE = "https://nvidia.wd5.myworkdayjobs.com"
CXS = f"{BASE}/wday/cxs/nvidia/NVIDIAExternalCareerSite"
SEARCH_URL = f"{CXS}/jobs"
PAGE_LIMIT = 20  # CXS hard cap

class AccessDenied(Exception):
    pass

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def snapshot_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

class Client:
    def __init__(self, delay: float, contact: str):
        self.delay = delay
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": f"hiring-intel-tracker/1.0 (public-data research; contact: {contact})",
        }
        self._429s = 0

    def _request(self, url: str, body: dict | None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers=self.headers,
                                     method="POST" if body is not None else "GET")
        for attempt in range(4):
            time.sleep(self.delay)
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    self._429s = 0
                    return json.loads(resp.read().decode())
            except urllib.error.HTTPError as e:
                if e.code == 403:
                    raise AccessDenied(f"403 from {url} — stopping campaign") from e
                if e.code == 429:
                    self._429s += 1
                    if self._429s >= 5:
                        raise AccessDenied("repeated 429 — stopping campaign") from e
                    time.sleep(30 * (attempt + 1))
                    continue
                if 500 <= e.code < 600 and attempt < 3:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise
            except urllib.error.URLError:
                if attempt < 3:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise
        raise RuntimeError(f"retries exhausted for {url}")

    def search_page(self, offset: int) -> dict:
        return self._request(SEARCH_URL, {"appliedFacets": {}, "limit": PAGE_LIMIT,
                                          "offset": offset, "searchText": ""})

    def detail(self, external_path: str) -> dict:
        return self._request(f"{CXS}{external_path}", None)

def envelope(url: str, payload: dict) -> dict:
    return {"source_url": url, "captured_at": now_iso(), "payload": payload}

def save(path: pathlib.Path, url: str, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(envelope(url, payload), ensure_ascii=False, indent=1))

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parents[1] / "data/raw"))
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--contact", default="set-me@example.com")
    ap.add_argument("--max-details", type=int, default=0, help="0 = all")
    ap.add_argument("--probe", action="store_true", help="fetch 1 page + 1 detail and exit")
    args = ap.parse_args()

    snap = snapshot_id()
    root = pathlib.Path(args.out) / snap
    client = Client(args.delay, args.contact)
    print(f"snapshot {snap} -> {root}")

    try:
        # ---- search pages -------------------------------------------------
        first = client.search_page(0)
        total = int(first.get("total", 0))
        save(root / "search" / "page_0000.json", SEARCH_URL, first)
        print(f"total postings reported: {total}")
        postings = list(first.get("jobPostings", []))
        offset, page_no = PAGE_LIMIT, 1
        while offset < total and not args.probe:
            page = client.search_page(offset)
            save(root / "search" / f"page_{page_no:04d}.json", SEARCH_URL, page)
            got = page.get("jobPostings", [])
            postings.extend(got)
            drift = abs(int(page.get("total", total)) - total)
            if drift > max(10, total // 100):
                print(f"WARNING: total drifted by {drift} mid-crawl; "
                      f"run a reconciliation pass after this one", file=sys.stderr)
            if not got:
                break
            offset += PAGE_LIMIT
            page_no += 1
        print(f"search pages saved: {page_no}; postings listed: {len(postings)}")

        # ---- detail payloads ---------------------------------------------
        seen: set[str] = set()
        fetched = 0
        for p in postings:
            path = p.get("externalPath")
            req_id = (p.get("bulletFields") or [None])[0] or path
            if not path or req_id in seen:
                continue
            seen.add(req_id)
            detail = client.detail(path)
            safe = str(req_id).replace("/", "_")
            save(root / "details" / f"{safe}.json", f"{CXS}{path}", detail)
            fetched += 1
            if fetched % 100 == 0:
                print(f"  details fetched: {fetched}/{len(seen)}")
            if args.probe or (args.max_details and fetched >= args.max_details):
                break
        print(f"details saved: {fetched}")

        manifest = {
            "snapshot": snap, "captured_at": now_iso(), "source": SEARCH_URL,
            "total_reported": total, "search_pages": page_no,
            "postings_listed": len(postings), "details_fetched": fetched,
            "probe": args.probe, "synthetic": False,
        }
        (root / "manifest.json").write_text(json.dumps(manifest, indent=1))
        print("done.")
        return 0
    except AccessDenied as e:
        print(f"STOPPED: {e}", file=sys.stderr)
        print("Access rules make collection inappropriate from this network. "
              "See docs/source_map.md — do not retry from here.", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
