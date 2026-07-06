#!/usr/bin/env python3
"""Generate a self-contained HTML dashboard (reports/dashboard.html) from one
processed snapshot + the tracker DB. No external assets; light/dark aware.

Design notes (dataviz method): every chart here is a single-series magnitude
comparison -> horizontal bars in one sequential hue (validated reference palette,
slot 1 blue), <=24px marks with 4px rounded data-ends, hairline grid, no legend
(single series), values labeled at bar tips, per-mark hover tooltip, and the
numbers repeated in accessible tables.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import pathlib
import sqlite3
from collections import Counter

LABELS = {
    "datacenter_ai_infra": "Data-center & AI infra", "networking": "Networking & optics",
    "ai_software_inference": "AI software & inference", "autonomous_vehicles": "Automotive / DRIVE",
    "robotics_edge": "Robotics & edge", "gaming_consumer": "Gaming & consumer",
    "omniverse_simulation": "Omniverse / digital twins", "research_frontier": "Frontier research",
    "silicon_engineering": "Silicon & hardware eng.", "supply_chain_capacity": "Supply chain & capacity",
    "quantum": "Quantum (CUDA-Q)", "sales_gtm_expansion": "Sales & GTM",
    "corporate_ga": "Corporate / G&A", "unclassified": "Unclassified",
    "hw_engineering": "Hardware engineering", "sw_engineering": "Software engineering",
    "research": "Research", "product": "Product", "sales_gtm": "Sales & GTM",
    "operations_supply_chain": "Ops & supply chain", "ga": "G&A", "support": "Support",
    "intern": "Intern", "entry": "Entry", "ic": "IC", "senior": "Senior",
    "principal_distinguished": "Principal / Distinguished", "manager": "Manager",
    "director_plus": "Director+",
}

def esc(s): return html.escape(str(s))

def bar_chart(title: str, counter: Counter, total: int) -> str:
    mx = max(counter.values()) if counter else 1
    rows = []
    for k, v in counter.most_common():
        name = LABELS.get(k, k)
        pct = v / total
        w = max(1.5, 100 * v / mx)
        rows.append(
            f'<div class="row" tabindex="0" data-tip="{esc(name)}: {v} roles ({pct:.0%} of core)">'
            f'<span class="cat">{esc(name)}</span>'
            f'<span class="track"><span class="bar" style="width:{w:.1f}%"></span></span>'
            f'<span class="val">{v}</span></div>')
    table = ('<details><summary>Table view</summary><table><tr><th>Category</th>'
             '<th>Roles</th><th>Share</th></tr>' +
             "".join(f"<tr><td>{esc(LABELS.get(k, k))}</td><td>{v}</td><td>{v/total:.0%}</td></tr>"
                     for k, v in counter.most_common()) + "</table></details>")
    return f'<section class="card"><h2>{esc(title)}</h2><div class="chart">{"".join(rows)}</div>{table}</section>'

def stat(label: str, value, note: str = "") -> str:
    return (f'<div class="tile"><div class="tlabel">{esc(label)}</div>'
            f'<div class="tvalue">{esc(value)}</div>'
            f'<div class="tnote">{esc(note)}</div></div>')

def build(root: pathlib.Path, snapshot: str) -> pathlib.Path:
    proc = root / "data/processed" / snapshot
    cls = list(csv.DictReader((proc / "classified.csv").open()))
    locs = list(csv.DictReader((proc / "locations.csv").open()))
    nstats = json.loads((proc / "normalize_stats.json").read_text())
    synthetic = nstats.get("synthetic", False)

    core = [r for r in cls if r["role_pool"] == "core"]
    core_ids = {r["req_id"] for r in core}
    themes = Counter(r["theme"] for r in core)
    funcs = Counter(r["function"] for r in core)
    sen = Counter(r["seniority"] for r in core)
    geo = Counter(l["location"].split(",")[0].strip()
                  for l in locs if l["is_primary"] == "1" and l["req_id"] in core_ids)
    flagged = sum(1 for r in cls if r["needs_review"] == "1")

    velocity = ""
    db = root / "data/state/tracker.sqlite"
    if db.exists():
        con = sqlite3.connect(db)
        n_snaps = con.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
        if n_snaps >= 2:
            ev = Counter(e for (e,) in con.execute(
                "SELECT event FROM events WHERE snapshot=?", (snapshot,)))
            velocity = (stat("New since prior capture", ev.get("opened", 0), "requisitions") +
                        stat("Delisted (marked closed)", ev.get("closed", 0), "filled or withdrawn — payloads don't say which") +
                        stat("Re-opened", ev.get("reopened", 0), "previously closed"))
        con.close()

    watch_rows = ""
    wl = root / "reports/watchlist.csv"
    if wl.exists():
        for r in list(csv.DictReader(wl.open()))[:10]:
            watch_rows += (f"<tr><td>{esc(r['score'])}</td><td><code>{esc(r['req_id'])}</code></td>"
                           f"<td>{esc(r['title'])}</td><td>{esc(LABELS.get(r['theme'], r['theme']))}</td></tr>")

    banner = ""
    if synthetic:
        banner = ('<div class="banner">⚠️ SYNTHETIC FIXTURE DATA — pipeline demo only. '
                  'These are not real NVIDIA postings. Re-run after a live <code>collect.py</code> '
                  'snapshot to see actual data.</div>')

    body = f"""<title>NVIDIA hiring-intelligence dashboard</title>
<style>
.viz-root {{
  --surface-1:#fcfcfb; --page:#f9f9f7; --ink-1:#0b0b0b; --ink-2:#52514e;
  --muted:#898781; --grid:#e1e0d9; --border:rgba(11,11,11,.10);
  --series-1:#2a78d6; --track:#cde2fb; --warn-bg:#fff7e0; --warn-ink:#6b4b00;
}}
@media (prefers-color-scheme: dark) {{ .viz-root {{
  --surface-1:#1a1a19; --page:#0d0d0d; --ink-1:#ffffff; --ink-2:#c3c2b7;
  --muted:#898781; --grid:#2c2c2a; --border:rgba(255,255,255,.10);
  --series-1:#3987e5; --track:#104281; --warn-bg:#3a2f00; --warn-ink:#fab219;
}} }}
:root[data-theme="dark"] .viz-root {{
  --surface-1:#1a1a19; --page:#0d0d0d; --ink-1:#ffffff; --ink-2:#c3c2b7;
  --grid:#2c2c2a; --border:rgba(255,255,255,.10);
  --series-1:#3987e5; --track:#104281; --warn-bg:#3a2f00; --warn-ink:#fab219;
}}
:root[data-theme="light"] .viz-root {{
  --surface-1:#fcfcfb; --page:#f9f9f7; --ink-1:#0b0b0b; --ink-2:#52514e;
  --grid:#e1e0d9; --border:rgba(11,11,11,.10);
  --series-1:#2a78d6; --track:#cde2fb; --warn-bg:#fff7e0; --warn-ink:#6b4b00;
}}
.viz-root {{ background:var(--page); color:var(--ink-1);
  font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif; padding:24px; min-height:100vh; }}
.viz-root h1 {{ font-size:1.35rem; margin:0 0 2px; }}
.viz-root .sub {{ color:var(--ink-2); margin:0 0 18px; font-size:.9rem; }}
.banner {{ background:var(--warn-bg); color:var(--warn-ink); border:1px solid var(--border);
  border-radius:8px; padding:10px 14px; margin-bottom:18px; font-weight:600; }}
.kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
  gap:12px; margin-bottom:20px; }}
.tile {{ background:var(--surface-1); border:1px solid var(--border); border-radius:10px;
  padding:12px 14px; }}
.tlabel {{ color:var(--ink-2); font-size:.8rem; }}
.tvalue {{ font-size:2rem; font-weight:600; }}
.tnote {{ color:var(--muted); font-size:.72rem; }}
.grid2 {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:16px; }}
.card {{ background:var(--surface-1); border:1px solid var(--border); border-radius:10px;
  padding:16px 18px; }}
.card h2 {{ font-size:.95rem; margin:0 0 12px; }}
.row {{ display:grid; grid-template-columns:minmax(120px,38%) 1fr 2.5em; align-items:center;
  gap:8px; padding:3px 0; position:relative; outline:none; }}
.cat {{ color:var(--ink-2); font-size:.8rem; white-space:nowrap; overflow:hidden;
  text-overflow:ellipsis; }}
.track {{ display:block; height:16px; border-left:1px solid var(--grid); }}
.bar {{ display:block; height:16px; max-height:24px; background:var(--series-1);
  border-radius:0 4px 4px 0; }}
.val {{ font-size:.8rem; color:var(--ink-1); font-variant-numeric:tabular-nums; text-align:right; }}
.row:hover .bar, .row:focus .bar {{ filter:brightness(1.12); }}
.row:hover::after, .row:focus::after {{ content:attr(data-tip); position:absolute; left:38%;
  top:-30px; background:var(--ink-1); color:var(--page); padding:3px 9px; border-radius:6px;
  font-size:.75rem; white-space:nowrap; z-index:2; pointer-events:none; }}
details {{ margin-top:8px; color:var(--ink-2); font-size:.8rem; }}
table {{ border-collapse:collapse; width:100%; margin-top:6px; }}
th,td {{ text-align:left; padding:4px 8px; border-bottom:1px solid var(--grid); font-size:.8rem; }}
td:nth-child(2), td:nth-child(3) {{ font-variant-numeric:tabular-nums; }}
.note {{ color:var(--muted); font-size:.75rem; margin-top:20px; max-width:70ch; }}
.wrap {{ overflow-x:auto; }}
</style>
<div class="viz-root">
{banner}
<h1>NVIDIA hiring-intelligence dashboard</h1>
<p class="sub">Snapshot <code>{esc(snapshot)}</code> · captured {esc(nstats['captured_at'])} ·
public Workday job-posting data · one requisition = one role</p>
<div class="kpis">
{stat("Open requisitions", len(cls), "unique jobReqIds")}
{stat("Core corporate/technical", len(core), "excl. support, interns, evergreen")}
{stat("Countries (primary loc.)", len(geo), "core roles")}
{stat("Flagged for manual review", flagged, "theme confidence < 0.60")}
{velocity}
</div>
<div class="grid2">
{bar_chart("Core roles by investor theme (inferred labels)", themes, len(core))}
{bar_chart("Core roles by function", funcs, len(core))}
{bar_chart("Core roles by primary-location country", geo, len(core))}
{bar_chart("Core roles by seniority", sen, len(core))}
</div>
<section class="card" style="margin-top:16px">
<h2>Watchlist — highest-signal postings (read the source before citing)</h2>
<div class="wrap"><table><tr><th>Score</th><th>Req ID</th><th>Title</th><th>Theme</th></tr>
{watch_rows or '<tr><td colspan="4">run report.py first</td></tr>'}
</table></div>
</section>
<p class="note">Counts are facts from public payloads; theme/function/seniority labels and
watchlist scores are analyst inference. Job postings show where the company is recruiting —
they do not prove strategy, budget, launch timing, or revenue impact. Delistings do not
distinguish filled from withdrawn.</p>
</div>
"""
    out = root / "reports/dashboard.html"
    out.write_text(body)
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    a = ap.parse_args()
    p = build(pathlib.Path(__file__).resolve().parents[1], a.snapshot)
    print(f"wrote {p}")
