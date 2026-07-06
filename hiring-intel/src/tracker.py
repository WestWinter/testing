#!/usr/bin/env python3
"""Step 6 — Longitudinal requisition tracker.

State machine per requisition (keyed by jobReqId):

    (new) --seen--> ACTIVE --missed 1 snapshot--> ABSENT --missed >= CLOSE_AFTER--> CLOSED
      ACTIVE/ABSENT/CLOSED --seen again--> ACTIVE  (from CLOSED this increments reopen_count)

ABSENT exists because Workday postings blink out temporarily (edits, reposts); a single
missed snapshot is not evidence of closure. Default CLOSE_AFTER = 2 consecutive misses.

Interpretation contract:
  * the FIRST snapshot only establishes composition — no velocity claims from it
  * velocity (openings/closures per week) only exists once >= 2 snapshots are ingested

Tables:
  requisitions(req_id PK, title, theme, function, seniority, role_pool,
               first_seen, last_seen, status, missing_streak, reopen_count)
  events(req_id, event, snapshot, at)   -- opened / missed / closed / reopened
  snapshots(snapshot PK, captured_at, unique_reqs, synthetic)
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sqlite3

CLOSE_AFTER = 2

SCHEMA = """
CREATE TABLE IF NOT EXISTS requisitions(
  req_id TEXT PRIMARY KEY, title TEXT, theme TEXT, function TEXT,
  seniority TEXT, role_pool TEXT, first_seen TEXT, last_seen TEXT,
  status TEXT CHECK(status IN ('active','absent','closed')),
  missing_streak INTEGER DEFAULT 0, reopen_count INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS events(
  req_id TEXT, event TEXT, snapshot TEXT, at TEXT);
CREATE TABLE IF NOT EXISTS snapshots(
  snapshot TEXT PRIMARY KEY, captured_at TEXT, unique_reqs INTEGER, synthetic INTEGER);
"""

def ingest(db_path: pathlib.Path, classified_csv: pathlib.Path, snapshot: str,
           captured_at: str, synthetic: bool) -> dict:
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    cur = con.cursor()
    if cur.execute("SELECT 1 FROM snapshots WHERE snapshot=?", (snapshot,)).fetchone():
        con.close()
        return {"snapshot": snapshot, "skipped": "already ingested"}

    rows = {r["req_id"]: r for r in csv.DictReader(classified_csv.open())}
    known = {r[0]: r for r in cur.execute(
        "SELECT req_id,status,missing_streak,reopen_count FROM requisitions")}
    ev = lambda rid, e: cur.execute(
        "INSERT INTO events VALUES (?,?,?,?)", (rid, e, snapshot, captured_at))
    counts = {"opened": 0, "still_active": 0, "reopened": 0, "went_absent": 0, "closed": 0}

    for rid, r in rows.items():
        if rid not in known:
            cur.execute("""INSERT INTO requisitions VALUES (?,?,?,?,?,?,?,?, 'active',0,0)""",
                        (rid, r["title"], r["theme"], r["function"], r["seniority"],
                         r["role_pool"], captured_at, captured_at))
            ev(rid, "opened")
            counts["opened"] += 1
        else:
            status = known[rid][1]
            reopen = known[rid][3] + (1 if status == "closed" else 0)
            if status == "closed":
                ev(rid, "reopened")
                counts["reopened"] += 1
            else:
                counts["still_active"] += 1
            cur.execute("""UPDATE requisitions SET last_seen=?, status='active',
                           missing_streak=0, reopen_count=?, title=?, theme=? WHERE req_id=?""",
                        (captured_at, reopen, r["title"], r["theme"], rid))

    for rid, (_, status, streak, _) in known.items():
        if rid in rows or status == "closed":
            continue
        streak += 1
        new_status = "closed" if streak >= CLOSE_AFTER else "absent"
        cur.execute("UPDATE requisitions SET status=?, missing_streak=? WHERE req_id=?",
                    (new_status, streak, rid))
        ev(rid, "missed" if new_status == "absent" else "closed")
        counts["went_absent" if new_status == "absent" else "closed"] += 1

    cur.execute("INSERT INTO snapshots VALUES (?,?,?,?)",
                (snapshot, captured_at, len(rows), int(synthetic)))
    con.commit()
    n_snaps = cur.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
    con.close()
    mode = "composition (first snapshot — no velocity claims)" if n_snaps == 1 else "velocity"
    return {"snapshot": snapshot, "mode": mode, **counts}

def export_state(db_path: pathlib.Path, out_csv: pathlib.Path) -> None:
    con = sqlite3.connect(db_path)
    cur = con.execute("""SELECT req_id,title,theme,function,seniority,role_pool,
                         first_seen,last_seen,status,missing_streak,reopen_count
                         FROM requisitions ORDER BY req_id""")
    with out_csv.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([d[0] for d in cur.description])
        w.writerows(cur.fetchall())
    con.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    root = pathlib.Path(__file__).resolve().parents[1]
    ap.add_argument("--db", default=str(root / "data/state/tracker.sqlite"))
    ap.add_argument("--processed", default=str(root / "data/processed"))
    ap.add_argument("--raw", default=str(root / "data/raw"))
    ap.add_argument("--snapshot", required=True)
    a = ap.parse_args()
    man = json.loads((pathlib.Path(a.raw) / a.snapshot / "manifest.json").read_text())
    dbp = pathlib.Path(a.db); dbp.parent.mkdir(parents=True, exist_ok=True)
    res = ingest(dbp, pathlib.Path(a.processed) / a.snapshot / "classified.csv",
                 a.snapshot, man["captured_at"], man.get("synthetic", False))
    export_state(dbp, dbp.parent / "tracker_state.csv")
    print(json.dumps(res, indent=1))
