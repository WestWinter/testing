#!/usr/bin/env python3
"""Step 4 — Classify normalized requisitions.

Signal hierarchy (weights):
  title match        0.90   (strongest)
  family/department  0.75
  description text   0.55   (supporting only)

Each requisition gets:
  role_pool     core | support | evergreen_pipeline | intern
                (support/evergreen/intern are excluded from the corporate/technical
                 role mix, per Step 3/5)
  function      hw_engineering, sw_engineering, research, product, sales_gtm,
                operations_supply_chain, ga, support
  seniority     intern, entry, ic, senior, principal_distinguished, manager,
                director_plus
  theme         investor theme (below) + confidence in [0,1]
  needs_review  True when confidence < 0.60 → manual review queue

Investor themes (NVIDIA-specific):
  datacenter_ai_infra, networking, ai_software_inference, autonomous_vehicles,
  robotics_edge, gaming_consumer, omniverse_simulation, research_frontier,
  silicon_engineering, supply_chain_capacity, quantum, sales_gtm_expansion,
  corporate_ga, unclassified
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re

W_TITLE, W_FAMILY, W_DESC = 0.90, 0.75, 0.55
REVIEW_THRESHOLD = 0.60

THEME_RULES = [
    # (theme, title/desc regexes) — first title match wins ties
    ("networking", r"nvlink|nvswitch|infiniband|ethernet|spectrum-?x|\bdpu\b|bluefield|\bnic\b|rdma|photonics|co-?packaged optics|optical interconnect|network"),
    ("supply_chain_capacity", r"supply chain|foundry|cowos|osat|\bhbm supply\b|demand plan|manufacturing|s&op|allocation|yield"),
    ("autonomous_vehicles", r"autonomous driving|drive os|drive av|self-driving|automotive|iso 26262|\borin\b|\bthor\b"),
    ("robotics_edge", r"robotic|isaac|jetson|humanoid|gr00t|embedded.*edge|edge ai|manipulation"),
    ("omniverse_simulation", r"omniverse|openusd|digital twin|simulation platform"),
    ("quantum", r"quantum|cuda-?q"),
    ("gaming_consumer", r"geforce|dlss|rtx|gaming|game engine|neural graphics|streaming.*(game|now)|cloud gaming"),
    ("datacenter_ai_infra", r"dgx|hgx|data center|datacenter|ai factor|supercomput|rack.?scale|liquid cooling|cluster|slurm|sovereign ai|megawatt|800v|grid"),
    ("ai_software_inference", r"tensorrt|\bnim\b|inference|triton|nemo|cuda|deep learning|llm|generative ai|foundation model|kernel|pytorch|megatron|attention"),
    ("research_frontier", r"research scientist|research intern|nvidia research|world model|publications"),
    ("silicon_engineering", r"asic|vlsi|rtl|physical design|verification|tapeout|signal integrity|silicon|soc\b|synthesis|timing closure|serdes|thermal|power (architect|delivery)|board"),
    ("sales_gtm_expansion", r"account manager|sales|solutions architect|developer relations|business development|go.?to.?market|partner|customer|marketing"),
    ("corporate_ga", r"financial|finance|legal|compliance|\bhr\b|human resources|accountant|internal audit|it support|workplace|recruiter|payroll|export"),
]

FAMILY_THEME = {
    "hardware engineering": "silicon_engineering",
    "software engineering": "ai_software_inference",
    "research": "research_frontier",
    "sales": "sales_gtm_expansion",
    "marketing": "sales_gtm_expansion",
    "product": "ai_software_inference",
    "operations": "supply_chain_capacity",
    "finance": "corporate_ga", "legal": "corporate_ga",
    "human resources": "corporate_ga", "information technology": "corporate_ga",
    "support": "corporate_ga",
}

FUNCTION_RULES = [
    ("support", r"customer support|technical support|support engineer|support specialist|helpdesk|it support"),
    ("research", r"research scientist|research intern"),
    ("sales_gtm", r"account manager|sales|solutions architect|developer relations|marketing|business development"),
    ("operations_supply_chain", r"supply chain|manufacturing|demand plan|logistics|program manager.*supply"),
    ("ga", r"financial|finance|legal|compliance|\bhr\b|human resources|recruiter|workplace"),
    ("product", r"product manager|product line"),
    ("hw_engineering", r"asic|vlsi|rtl|physical design|hardware|signal integrity|thermal|silicon|photonics|verification|board|power architect|test engineer"),
    # deliberately no bare "engineer"/"architect" — too generic; family decides those
    ("sw_engineering", r"software|developer|\bsre\b|reliability|devops|kernel|firmware"),
]
FAMILY_FUNCTION = {
    "hardware engineering": "hw_engineering", "software engineering": "sw_engineering",
    "research": "research", "sales": "sales_gtm", "marketing": "sales_gtm",
    "product": "product", "operations": "operations_supply_chain",
    "finance": "ga", "legal": "ga", "human resources": "ga",
    "information technology": "ga", "support": "support",
}

SENIORITY_RULES = [
    ("intern", r"\bintern\b|internship"),
    ("director_plus", r"\bdirector\b|\bvp\b|vice president"),
    ("manager", r"\bmanager\b(?!.*account)|head of"),
    ("principal_distinguished", r"principal|distinguished|\bfellow\b|architect"),
    ("senior", r"\bsenior\b|\bsr\.?\b|staff"),
    ("entry", r"new college grad|new grad|graduate|early career|associate\b"),
]

POOL_RULES = [
    ("intern", r"\bintern\b|internship"),
    ("evergreen_pipeline", r"talent community|evergreen|future openings|pipeline requisition|general interest"),
    ("support", r"customer support|technical support|support specialist|helpdesk|it support technician"),
]

def _match(rules, *texts_with_weights):
    """Return (label, confidence) using the highest-weight text that matches."""
    best = ("", 0.0)
    for label, pat in rules:
        rx = re.compile(pat, re.I)
        for text, weight in texts_with_weights:
            if text and rx.search(text):
                if weight > best[1]:
                    best = (label, weight)
                break  # a rule scores once, at its best available weight
    return best

def classify_row(r: dict) -> dict:
    title, fam, desc = r["title"], r["family_group"].lower(), r["description_text"]

    pool, _ = _match(POOL_RULES, (title, W_TITLE), (desc, W_DESC))
    pool = pool or "core"

    theme, conf = _match(THEME_RULES, (title, W_TITLE), (desc, W_DESC))
    if theme:
        # independent family agreement bumps a rule match; title matches stay as-is
        if fam and FAMILY_THEME.get(fam) == theme and conf < W_TITLE:
            conf = min(0.85, conf + 0.10)
    elif fam in FAMILY_THEME:
        # department alone narrows the function, not the investor theme — keep it
        # below the review threshold so a human confirms the strategic label
        theme, conf = FAMILY_THEME[fam], 0.55
    else:
        theme, conf = "unclassified", 0.0

    func, fconf = _match(FUNCTION_RULES, (title, W_TITLE), (desc, W_DESC))
    if fam in FAMILY_FUNCTION and (not func or fconf < W_FAMILY):
        func = FAMILY_FUNCTION[fam] if not func else func
    func = func or "sw_engineering"

    sen, sconf = _match(SENIORITY_RULES, (title, W_TITLE), (desc, W_DESC))
    sen = sen or "ic"

    return {**r,
            "role_pool": pool, "function": func, "seniority": sen,
            "theme": theme, "theme_confidence": round(conf, 2),
            "needs_review": int(conf < REVIEW_THRESHOLD)}

def classify(processed_root: pathlib.Path, snapshot: str) -> dict:
    src = processed_root / snapshot / "requisitions.csv"
    rows = list(csv.DictReader(src.open()))
    out_rows = [classify_row(r) for r in rows]
    dst = processed_root / snapshot / "classified.csv"
    with dst.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    review = [r["req_id"] for r in out_rows if r["needs_review"]]
    stats = {"snapshot": snapshot, "classified": len(out_rows),
             "needs_review": review, "review_rate": round(len(review) / max(1, len(out_rows)), 3)}
    (processed_root / snapshot / "classify_stats.json").write_text(json.dumps(stats, indent=1))
    return stats

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    root = pathlib.Path(__file__).resolve().parents[1]
    ap.add_argument("--processed", default=str(root / "data/processed"))
    ap.add_argument("--snapshot", required=True)
    a = ap.parse_args()
    print(json.dumps(classify(pathlib.Path(a.processed), a.snapshot), indent=1))
