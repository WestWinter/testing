#!/usr/bin/env python3
"""Step 3 — Normalize raw snapshot payloads into tidy tables.

Rules enforced here:
  * one unique requisition (jobReqId) == one investor-counted role, regardless of how
    many locations or search pages it appears on
  * locations go to a separate table (requisitions x locations is 1:N)
  * multi-location roles are never double-counted: `n_locations` lives on the
    requisition row; the location table carries `is_primary`

Outputs (CSV, under data/processed/<snapshot>/):
  requisitions.csv  — req_id, title, family_group, time_type, posted_on, country,
                      n_locations, description_text, source_url, captured_at
  locations.csv     — req_id, location, is_primary

Usage: python3 normalize.py --raw <raw-root> --snapshot <id> --out <processed-root>
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import pathlib
import re
import sys

def strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()

def load_envelopes(d: pathlib.Path):
    for f in sorted(d.glob("*.json")):
        yield json.loads(f.read_text())

def normalize(raw_root: pathlib.Path, snapshot: str, out_root: pathlib.Path) -> dict:
    snap_dir = raw_root / snapshot
    manifest = json.loads((snap_dir / "manifest.json").read_text())

    # search results: fallback records + duplicate detection across pages
    listed: dict[str, dict] = {}
    dupes = 0
    for env in load_envelopes(snap_dir / "search"):
        for p in env["payload"].get("jobPostings", []):
            rid = (p.get("bulletFields") or [None])[0]
            if not rid:
                continue
            if rid in listed:
                dupes += 1
            listed[rid] = p

    rows, loc_rows = [], []
    seen = set()
    for env in load_envelopes(snap_dir / "details"):
        info = env["payload"].get("jobPostingInfo", {})
        rid = info.get("jobReqId")
        if not rid or rid in seen:
            continue
        seen.add(rid)
        locs = [info.get("location")] + list(info.get("additionalLocations") or [])
        locs = [l for l in locs if l]
        rows.append({
            "req_id": rid,
            "title": info.get("title", ""),
            "family_group": info.get("jobFamilyGroup", ""),
            "time_type": info.get("timeType", ""),
            "posted_on": info.get("postedOn", ""),
            "country": (info.get("country") or {}).get("descriptor", ""),
            "n_locations": len(locs),
            "description_text": strip_html(info.get("jobDescription", ""))[:4000],
            "source_url": env["source_url"],
            "captured_at": env["captured_at"],
        })
        for i, l in enumerate(locs):
            loc_rows.append({"req_id": rid, "location": l, "is_primary": int(i == 0)})

    # requisitions listed in search but missing a detail payload
    missing_detail = sorted(set(listed) - seen)

    out = out_root / snapshot
    out.mkdir(parents=True, exist_ok=True)
    for name, data, fields in [
        ("requisitions.csv", rows, list(rows[0].keys()) if rows else []),
        ("locations.csv", loc_rows, ["req_id", "location", "is_primary"]),
    ]:
        with (out / name).open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(data)

    stats = {
        "snapshot": snapshot, "synthetic": manifest.get("synthetic", False),
        "captured_at": manifest.get("captured_at"),
        "total_reported_by_source": manifest.get("total_reported"),
        "unique_requisitions": len(rows),
        "search_duplicates_collapsed": dupes,
        "location_rows": len(loc_rows),
        "multi_location_reqs": sum(1 for r in rows if r["n_locations"] > 1),
        "missing_detail_payloads": missing_detail,
    }
    (out / "normalize_stats.json").write_text(json.dumps(stats, indent=1))
    return stats

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    root = pathlib.Path(__file__).resolve().parents[1]
    ap.add_argument("--raw", default=str(root / "data/raw"))
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--out", default=str(root / "data/processed"))
    a = ap.parse_args()
    s = normalize(pathlib.Path(a.raw), a.snapshot, pathlib.Path(a.out))
    print(json.dumps(s, indent=1))
    if s["missing_detail_payloads"]:
        print(f"WARNING: {len(s['missing_detail_payloads'])} listed reqs lack detail payloads",
              file=sys.stderr)
