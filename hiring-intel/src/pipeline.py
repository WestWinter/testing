#!/usr/bin/env python3
"""Orchestrate: normalize -> classify -> tracker ingest -> QA -> report -> dashboard
for every raw snapshot (chronological order), from either data/raw or fixtures/raw.

  python3 pipeline.py                # process data/raw (live captures)
  python3 pipeline.py --fixtures     # process fixtures/raw (synthetic demo)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

def sh(script: str, *args: str) -> int:
    cmd = [sys.executable, str(SRC / script), *args]
    print(f"\n== {script} {' '.join(args)}")
    return subprocess.call(cmd)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", action="store_true")
    a = ap.parse_args()
    raw = ROOT / ("fixtures/raw" if a.fixtures else "data/raw")
    snaps = sorted(p.name for p in raw.iterdir() if (p / "manifest.json").exists())
    if not snaps:
        print(f"no snapshots under {raw}", file=sys.stderr)
        return 1
    rc = 0
    for snap in snaps:
        man = json.loads((raw / snap / "manifest.json").read_text())
        syn = ["--synthetic"] if man.get("synthetic") else []
        rc |= sh("normalize.py", "--raw", str(raw), "--snapshot", snap)
        rc |= sh("classify.py", "--snapshot", snap)
        rc |= sh("tracker.py", "--raw", str(raw), "--snapshot", snap)
        rc |= sh("qa.py", "--snapshot", snap, *syn)
    latest = snaps[-1]
    rc |= sh("report.py", "--snapshot", latest)
    rc |= sh("dashboard.py", "--snapshot", latest)
    print(f"\npipeline {'FAILED' if rc else 'OK'}; report/dashboard built from {latest}")
    return rc

if __name__ == "__main__":
    raise SystemExit(main())
