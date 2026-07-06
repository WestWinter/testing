#!/usr/bin/env python3
"""QA checks over one processed snapshot (+ tracker DB if present).

Checks:
  Q1  no duplicate req_id in requisitions.csv
  Q2  source-reported total vs unique requisitions (within tolerance)
  Q3  every requisition has >= 1 location row; primary location count == req count
  Q4  n_locations column matches location-table row counts (no double counting)
  Q5  every listed req has a detail payload (from normalize_stats)
  Q6  classification coverage: no empty theme/function/seniority/role_pool
  Q7  low-confidence (needs_review) rate below threshold, list flagged reqs
  Q8  every raw envelope carries source_url + captured_at
  Q9  tracker invariants: status values legal, first_seen <= last_seen,
      closed reqs have missing_streak >= CLOSE_AFTER

Writes reports/qa_report.md and exits nonzero on hard failures.
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sqlite3
from collections import Counter

def run(root: pathlib.Path, snapshot: str) -> tuple[list, list]:
    proc = root / "data/processed" / snapshot
    raw = root / "fixtures/raw" / snapshot
    if not raw.exists():
        raw = root / "data/raw" / snapshot
    results, failures = [], []

    def check(name, ok, detail=""):
        results.append((name, ok, detail))
        if not ok:
            failures.append(name)

    reqs = list(csv.DictReader((proc / "requisitions.csv").open()))
    locs = list(csv.DictReader((proc / "locations.csv").open()))
    cls = list(csv.DictReader((proc / "classified.csv").open()))
    nstats = json.loads((proc / "normalize_stats.json").read_text())

    ids = [r["req_id"] for r in reqs]
    dupes = [i for i, c in Counter(ids).items() if c > 1]
    check("Q1 unique req_id", not dupes, f"duplicates: {dupes}" if dupes else f"{len(ids)} unique")

    total = nstats.get("total_reported_by_source") or 0
    diff = abs(total - len(ids))
    check("Q2 total vs unique reqs", diff <= max(2, total // 50),
          f"source total {total}, unique {len(ids)} (diff {diff}; multi-posting collapse expected)")

    by_req = Counter(l["req_id"] for l in locs)
    primaries = sum(1 for l in locs if l["is_primary"] == "1")
    check("Q3 location coverage", all(by_req.get(i, 0) >= 1 for i in ids) and primaries == len(ids),
          f"{len(locs)} location rows, {primaries} primaries for {len(ids)} reqs")

    mismatch = [r["req_id"] for r in reqs if int(r["n_locations"]) != by_req.get(r["req_id"], 0)]
    check("Q4 n_locations consistency", not mismatch, f"mismatched: {mismatch}" if mismatch else "ok")

    missing = nstats.get("missing_detail_payloads", [])
    check("Q5 detail payload coverage", not missing,
          f"missing details for {missing}" if missing else "all listed reqs have details")

    empty = [c["req_id"] for c in cls
             if not all(c[k] for k in ("theme", "function", "seniority", "role_pool"))]
    check("Q6 classification coverage", not empty, f"empty labels: {empty}" if empty else "ok")

    flagged = [c["req_id"] for c in cls if c["needs_review"] == "1"]
    rate = len(flagged) / max(1, len(cls))
    check("Q7 low-confidence rate", rate <= 0.15,
          f"{len(flagged)}/{len(cls)} flagged ({rate:.0%}): {flagged}")

    bad_env = []
    for sub in ("search", "details"):
        for f in sorted((raw / sub).glob("*.json")):
            env = json.loads(f.read_text())
            if not env.get("source_url") or not env.get("captured_at"):
                bad_env.append(f.name)
    check("Q8 capture provenance", not bad_env, f"missing url/ts: {bad_env}" if bad_env else "ok")

    db = root / "data/state/tracker.sqlite"
    if db.exists():
        con = sqlite3.connect(db)
        bad = con.execute("""SELECT req_id FROM requisitions WHERE
            status NOT IN ('active','absent','closed') OR first_seen > last_seen
            OR (status='closed' AND missing_streak < 2)""").fetchall()
        con.close()
        check("Q9 tracker invariants", not bad, f"violations: {bad}" if bad else "ok")

    return results, failures

def write_report(root: pathlib.Path, snapshot: str, results, failures, synthetic: bool):
    out = root / "reports/qa_report.md"
    lines = [f"# QA report — snapshot `{snapshot}`", ""]
    if synthetic:
        lines += ["> ⚠️ **SYNTHETIC FIXTURE DATA** — pipeline verification only, not real NVIDIA postings.", ""]
    lines += ["| Check | Result | Detail |", "|---|---|---|"]
    for name, ok, detail in results:
        lines.append(f"| {name} | {'✅ pass' if ok else '❌ FAIL'} | {detail} |")
    lines += ["", f"**{len(results) - len(failures)}/{len(results)} checks passed.**"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--synthetic", action="store_true")
    a = ap.parse_args()
    root = pathlib.Path(__file__).resolve().parents[1]
    results, failures = run(root, a.snapshot)
    write_report(root, a.snapshot, results, failures, a.synthetic)
    for name, ok, detail in results:
        print(("PASS " if ok else "FAIL ") + name + " — " + detail)
    raise SystemExit(1 if failures else 0)
