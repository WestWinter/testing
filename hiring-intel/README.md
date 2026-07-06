# NVIDIA hiring-intelligence tracker

Investor-oriented tracker of NVIDIA's public job postings (Workday careers site).
Public data only. Python 3.9+ stdlib — no dependencies.

> ⚠️ **Current data is SYNTHETIC.** This session's build environment has an
> organization-managed egress allowlist (GitHub + package registries only), so live
> collection from `nvidia.wd5.myworkdayjobs.com` was blocked with a proxy 403 —
> an access-rule stop condition (Step 2). Everything downstream was therefore built
> and verified against the synthetic fixture snapshots in `fixtures/raw/`, and every
> generated artifact carries a SYNTHETIC banner. Run the quickstart below from a
> normally-connected machine to produce the real dataset; no code changes needed.

## Quickstart (live)

```bash
cd src
python3 collect.py --probe --contact you@yourfirm.com   # sanity-check access first
python3 collect.py --contact you@yourfirm.com           # full snapshot (~1 req/s)
python3 pipeline.py                                     # normalize→classify→track→QA→report→dashboard
```

Demo on synthetic fixtures (works offline):

```bash
cd src && python3 make_fixtures.py && python3 pipeline.py --fixtures
```

## Pipeline (maps 1:1 to the six steps)

| Step | Module | Output |
|---|---|---|
| 1. Source map | `docs/source_map.md` | endpoint, pagination, stable ID (`jobReqId`), access-rule checklist |
| 2. Collect | `src/collect.py` | `data/raw/<snapshot>/search/page_*.json`, `details/<reqId>.json` — verbatim payloads wrapped in `{source_url, captured_at, payload}` |
| 3. Normalize | `src/normalize.py` | `data/processed/<snapshot>/requisitions.csv` (1 row = 1 requisition = 1 investor-counted role), `locations.csv` (1:N, `is_primary` flag — multi-location roles never double-counted) |
| 4. Classify | `src/classify.py` | `classified.csv` — role pool (core / support / evergreen / intern), function, seniority, investor theme + confidence; `needs_review=1` under 0.60 |
| 5. Readout | `src/report.py`, `src/dashboard.py` | `reports/hiring_report.md` (facts / inference / watchlist sections), `reports/watchlist.csv`, `reports/dashboard.html` |
| 6. Tracker | `src/tracker.py` | `data/state/tracker.sqlite` + `tracker_state.csv` — first_seen, last_seen, active/absent/closed, re-openings |
| QA | `src/qa.py` | `reports/qa_report.md` — 9 checks (dedupe, totals, location integrity, payload coverage, classification coverage, review rate, provenance, tracker invariants) |

## Classification method (Step 4)

Signal hierarchy: **title (0.90) > department/family (0.75) > description (0.55)**.
A theme derived *only* from the department is capped at 0.55 — below the 0.60 review
threshold — because a department narrows the function, not the investor theme.
Flagged requisitions land in `classify_stats.json` and the report for manual review.
Themes are NVIDIA-specific (data-center/AI infra, networking & optics, AI software &
inference, automotive, robotics, gaming, Omniverse, research, silicon engineering,
supply-chain capacity, quantum, GTM, G&A).

## Tracker semantics (Step 6)

- Keyed on **`jobReqId`** (requisition), never posting GUIDs.
- `active --miss 1--> absent --miss ≥2--> closed --seen--> active (reopen_count++)`.
  The `absent` state absorbs Workday's temporary blink-outs (edits/reposts) so a
  single missed capture is not misread as a closure.
- **The first snapshot is composition, not velocity.** Openings/closures per period
  are only reported once ≥ 2 snapshots exist. Suggested cadence: weekly, same
  weekday/hour (Workday reposts cluster on weekdays).
- A delisting means the posting left the site — it does **not** distinguish filled
  from withdrawn. The report says so explicitly.

## Interpretation contract (Step 5)

Facts and inference are kept in separate report sections. Counts, locations, and
presence/absence are facts from payloads. Theme labels, seniority buckets, and
watchlist scores are analyst inference with stated confidence. **Nothing in this
tracker proves strategy, approved budget, launch timing, or revenue impact** —
postings show where the company is recruiting, and are hypotheses to test against
filings, earnings calls, and channel checks.

## Collection ethics / access rules

Public, unauthenticated data only; 1 request/second on a single connection; honest
User-Agent with contact info; automatic stop on HTTP 403 and backoff-then-stop on
429. Re-check `robots.txt` and site terms before each campaign (checklist in
`docs/source_map.md`). Raw payloads are stored verbatim with source URL and UTC
capture timestamp for auditability.
