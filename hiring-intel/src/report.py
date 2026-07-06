#!/usr/bin/env python3
"""Step 5 — Investor readout: Markdown report + watchlist of high-signal postings.

Hard rules encoded here:
  * facts (counts from payloads) and inference (theme labels, signal scores) are
    reported in separate sections
  * no claims that postings prove strategy, budget, launch timing, or revenue impact
  * support / evergreen / intern pools are excluded from the corporate-technical mix
  * first snapshot => composition only; velocity section appears only from snapshot 2
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sqlite3
from collections import Counter

# themes whose postings are rare/strategic enough to be individually readable
WATCH_THEMES = {"quantum", "supply_chain_capacity", "networking", "datacenter_ai_infra",
                "robotics_edge", "omniverse_simulation"}
WATCH_KEYWORDS = ["photonics", "co-packaged", "800v", "megawatt", "cowos", "hbm",
                  "sovereign", "gr00t", "humanoid", "world model", "cosmos", "quantum",
                  "export", "spectrum-x", "nvlink"]

LABELS = {
    "datacenter_ai_infra": "Data-center & AI infrastructure",
    "networking": "Networking (NVLink / InfiniBand / Ethernet / optics)",
    "ai_software_inference": "AI software & inference stack",
    "autonomous_vehicles": "Automotive / DRIVE",
    "robotics_edge": "Robotics & edge (Jetson / Isaac / humanoids)",
    "gaming_consumer": "Gaming & consumer (GeForce / RTX)",
    "omniverse_simulation": "Omniverse / simulation / digital twins",
    "research_frontier": "Frontier research",
    "silicon_engineering": "Silicon & hardware engineering",
    "supply_chain_capacity": "Supply chain & manufacturing capacity",
    "quantum": "Quantum computing (CUDA-Q)",
    "sales_gtm_expansion": "Sales & go-to-market",
    "corporate_ga": "Corporate / G&A",
    "unclassified": "Unclassified",
}

def pct_table(counter: Counter, total: int, label_map=None) -> list[str]:
    rows = ["| Category | Roles | Share |", "|---|---:|---:|"]
    for k, v in counter.most_common():
        name = (label_map or {}).get(k, k)
        rows.append(f"| {name} | {v} | {v/total:.0%} |")
    return rows

def signal_score(row: dict) -> tuple[int, list[str]]:
    reasons = []
    text = (row["title"] + " " + row["description_text"]).lower()
    score = 0
    if row["theme"] in WATCH_THEMES:
        score += 2; reasons.append(f"strategic theme: {row['theme']}")
    hits = [k for k in WATCH_KEYWORDS if k in text]
    score += len(hits); reasons += [f"keyword: {k}" for k in hits]
    if row["seniority"] in ("principal_distinguished", "director_plus"):
        score += 1; reasons.append(f"senior hire: {row['seniority']}")
    return score, reasons

def build(root: pathlib.Path, snapshot: str) -> None:
    proc = root / "data/processed" / snapshot
    cls = list(csv.DictReader((proc / "classified.csv").open()))
    locs = list(csv.DictReader((proc / "locations.csv").open()))
    nstats = json.loads((proc / "normalize_stats.json").read_text())
    synthetic = nstats.get("synthetic", False)

    core = [r for r in cls if r["role_pool"] == "core"]
    pools = Counter(r["role_pool"] for r in cls)
    themes = Counter(r["theme"] for r in core)
    funcs = Counter(r["function"] for r in core)
    sen = Counter(r["seniority"] for r in core)
    core_ids = {r["req_id"] for r in core}
    geo = Counter(l["location"].split(",")[0].strip()
                  for l in locs if l["is_primary"] == "1" and l["req_id"] in core_ids)
    flagged = [r for r in cls if r["needs_review"] == "1"]

    L = []
    L.append(f"# NVIDIA hiring-intelligence readout — snapshot `{snapshot}`\n")
    if synthetic:
        L.append("> ⚠️ **SYNTHETIC FIXTURE DATA.** This report was generated from the synthetic "
                 "test snapshot in `fixtures/` to verify the pipeline end-to-end. Numbers below "
                 "describe the fixtures, **not NVIDIA**. Live collection was blocked by this "
                 "build environment's egress policy — see `docs/source_map.md`. Re-run the "
                 "pipeline after `collect.py` succeeds to produce the real readout.\n")
    L.append(f"*Source: public Workday CXS payloads. Captured at {nstats['captured_at']}.*\n")

    L.append("## Section A — Facts (counted directly from payloads)\n")
    L.append(f"- Unique open requisitions: **{len(cls)}** "
             f"(source-reported total: {nstats['total_reported_by_source']})")
    L.append(f"- Multi-location requisitions: {nstats['multi_location_reqs']} "
             f"(counted once each; {nstats['location_rows']} location rows in `locations.csv`)")
    L.append(f"- Role pools: " + ", ".join(f"{k} {v}" for k, v in pools.most_common()))
    L.append(f"- Corporate/technical (\"core\") requisitions used for the mix below: **{len(core)}**\n")

    L.append("### Core role mix by investor theme *(theme labels are inference — see Section B)*\n")
    L += pct_table(themes, len(core), LABELS)
    L.append("\n### Core role mix by function\n")
    L += pct_table(funcs, len(core))
    L.append("\n### Core role mix by primary-location country\n")
    L += pct_table(geo, len(core))
    L.append("\n### Core role mix by seniority\n")
    L += pct_table(sen, len(core))

    # ---- velocity (only if tracker has >= 2 snapshots) ----------------------
    db = root / "data/state/tracker.sqlite"
    if db.exists():
        con = sqlite3.connect(db)
        snaps = con.execute("SELECT snapshot, captured_at, unique_reqs FROM snapshots ORDER BY snapshot").fetchall()
        if len(snaps) >= 2:
            ev = Counter(e for (e,) in con.execute(
                "SELECT event FROM events WHERE snapshot=?", (snapshot,)))
            L.append("\n### Velocity since prior snapshot (fact: presence/absence between captures)\n")
            L.append(f"- Newly observed requisitions: **{ev.get('opened', 0)}**")
            L.append(f"- No longer listed (marked closed): **{ev.get('closed', 0)}**")
            L.append(f"- Temporarily absent: {ev.get('missed', 0)}; re-opened: {ev.get('reopened', 0)}")
            L.append("- *A delisting means the posting left the site; it does not distinguish "
                     "filled vs. cancelled.*")
        else:
            L.append("\n*This is the first snapshot: it establishes **composition** only. "
                     "No velocity claims until repeated captures exist.*")
        con.close()

    L.append("\n## Section B — Inference (rule-based labels, with confidence)\n")
    L.append("Theme, function and seniority labels are assigned by `classify.py` rules "
             "(title strongest, department second, description supporting). They are analyst "
             "constructs, not NVIDIA's own categories.\n")
    L.append(f"- Low-confidence labels flagged for manual review: **{len(flagged)}** "
             f"({len(flagged)/max(1,len(cls)):.0%}) — " +
             (", ".join(f"`{r['req_id']}` \"{r['title']}\"" for r in flagged) or "none"))
    L.append("\n**What this data can and cannot say:** job postings indicate where NVIDIA is "
             "*recruiting*. They do **not** prove strategy, approved budgets, product launch "
             "timing, or revenue impact. Postings can be evergreen, reposted, aspirational, or "
             "withdrawn without explanation. Treat themes as hypotheses to test against "
             "filings, earnings calls, and supply-chain checks.\n")

    L.append("## Section C — Watchlist: highest-signal individual postings\n")
    L.append("Ranked by a transparent score (strategic theme +2, watch keyword +1 each, "
             "principal/director seniority +1). Read the source posting before citing.\n")
    scored = sorted(((signal_score(r), r) for r in core), key=lambda t: -t[0][0])
    L.append("| Score | Req ID | Title | Why it scores | Source |")
    L.append("|---:|---|---|---|---|")
    watch_rows = []
    for (s, reasons), r in scored[:12]:
        if s < 2:
            break
        L.append(f"| {s} | `{r['req_id']}` | {r['title']} | {'; '.join(reasons[:4])} | "
                 f"[posting]({r['source_url']}) |")
        watch_rows.append({"req_id": r["req_id"], "title": r["title"], "score": s,
                           "reasons": "; ".join(reasons), "theme": r["theme"],
                           "source_url": r["source_url"]})

    out = root / "reports"
    out.mkdir(exist_ok=True)
    (out / "hiring_report.md").write_text("\n".join(L) + "\n")
    with (out / "watchlist.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["req_id", "title", "score", "theme", "reasons", "source_url"])
        w.writeheader(); w.writerows(watch_rows)
    print(f"wrote {out/'hiring_report.md'} and watchlist ({len(watch_rows)} entries)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    a = ap.parse_args()
    build(pathlib.Path(__file__).resolve().parents[1], a.snapshot)
