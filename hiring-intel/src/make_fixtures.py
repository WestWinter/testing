#!/usr/bin/env python3
"""Generate a SYNTHETIC two-snapshot raw dataset in the exact on-disk format that
collect.py produces, so the full pipeline can be exercised without network access.

Every manifest is marked "synthetic": true and every downstream artifact built from it
carries a SYNTHETIC DATA banner. None of these postings are real NVIDIA requisitions.
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXROOT = ROOT / "fixtures" / "raw"

SNAP_A = "20260629T120000Z"  # first capture  -> composition
SNAP_B = "20260706T120000Z"  # second capture -> velocity

CXS = "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite"

# (req_id, title, family_group, primary_loc, extra_locs, time_type, seniority_hint,
#  desc_keywords, in_A, in_B)
JOBS = [
    ("JR90001", "Senior ASIC Design Engineer", "Hardware Engineering", "US, CA, Santa Clara", [], "Full time", "senior", "RTL design, SoC, GPU architecture, synthesis, timing closure", 1, 1),
    ("JR90002", "Principal Physical Design Engineer", "Hardware Engineering", "US, TX, Austin", ["US, CA, Santa Clara"], "Full time", "principal", "floorplanning, place and route, advanced process nodes, tapeout", 1, 1),
    ("JR90003", "ASIC Verification Engineer, New College Grad", "Hardware Engineering", "IN, Bangalore", [], "Full time", "entry", "UVM, SystemVerilog, functional verification of GPU units", 1, 1),
    ("JR90004", "Senior Signal Integrity Engineer", "Hardware Engineering", "TW, Taipei", [], "Full time", "senior", "high speed SerDes, PCB, HBM interfaces, power delivery", 1, 1),
    ("JR90005", "Thermal Engineer, Data Center Systems", "Hardware Engineering", "US, CA, Santa Clara", ["IL, Yokneam"], "Full time", "mid", "liquid cooling, rack scale thermal design for AI supercomputers", 0, 1),
    ("JR90011", "Senior Software Engineer, NVLink Fabric", "Software Engineering", "US, CA, Santa Clara", [], "Full time", "senior", "NVLink, NVSwitch, fabric manager, rack-scale GPU interconnect", 1, 1),
    ("JR90012", "InfiniBand Firmware Engineer", "Software Engineering", "IL, Yokneam", ["IL, Tel Aviv"], "Full time", "mid", "InfiniBand, RDMA, congestion control, NIC firmware", 1, 1),
    ("JR90013", "Senior Product Manager, Spectrum-X Ethernet", "Product", "US, CA, Santa Clara", [], "Full time", "senior", "Ethernet for AI, Spectrum-X, switch ASIC roadmap, hyperscaler customers", 1, 1),
    ("JR90014", "DPU Software Architect, BlueField", "Software Engineering", "IL, Tel Aviv", [], "Full time", "principal", "BlueField DPU, DOCA, zero-trust offload, storage acceleration", 1, 0),
    ("JR90021", "Senior Site Reliability Engineer, DGX Cloud", "Software Engineering", "US, Remote", ["PL, Warsaw"], "Full time", "senior", "Kubernetes, Slurm, large GPU cluster operations, DGX Cloud", 1, 1),
    ("JR90022", "Solutions Architect, AI Factories", "Sales", "JP, Tokyo", [], "Full time", "senior", "sovereign AI, data center reference architectures, customer deployments", 1, 1),
    ("JR90023", "Data Center Power Architect", "Hardware Engineering", "US, WA, Redmond", [], "Full time", "principal", "megawatt scale power architecture, 800V DC distribution, grid integration", 0, 1),
    ("JR90031", "Senior Deep Learning Software Engineer, Inference", "Software Engineering", "US, CA, Santa Clara", ["US, Remote"], "Full time", "senior", "TensorRT-LLM, NIM microservices, KV cache optimization, speculative decoding", 1, 1),
    ("JR90032", "CUDA Kernel Engineer, Attention Optimization", "Software Engineering", "US, Remote", [], "Full time", "mid", "CUDA C++, kernel fusion, FlashAttention, Blackwell tensor cores", 1, 1),
    ("JR90033", "AI Frameworks Engineer, NeMo Training", "Software Engineering", "DE, Munich", [], "Full time", "mid", "distributed training, Megatron, mixture of experts, PyTorch", 1, 1),
    ("JR90034", "Senior Research Scientist, Foundation Model Efficiency", "Research", "US, CA, Santa Clara", ["CA, Toronto"], "Full time", "senior", "model compression, quantization research, publications at NeurIPS", 1, 1),
    ("JR90035", "Research Scientist, Physical AI and World Models", "Research", "US, WA, Seattle", [], "Full time", "senior", "world foundation models, Cosmos, video generation, robotics pretraining", 0, 1),
    ("JR90041", "Senior Autonomous Driving Software Engineer, Planning", "Software Engineering", "US, CA, Santa Clara", ["DE, Berlin"], "Full time", "senior", "DRIVE AV stack, motion planning, safety cases, ISO 26262", 1, 1),
    ("JR90042", "System Software Engineer, DRIVE OS", "Software Engineering", "CN, Shanghai", [], "Full time", "mid", "DRIVE Orin, Thor, hypervisor, automotive safety island", 1, 1),
    ("JR90051", "Robotics Software Engineer, Isaac Manipulation", "Software Engineering", "US, CA, Santa Clara", [], "Full time", "mid", "Isaac Lab, GR00T humanoid foundation models, sim-to-real", 1, 1),
    ("JR90052", "Embedded Software Engineer, Jetson Platform", "Software Engineering", "IN, Pune", [], "Full time", "mid", "Jetson Orin, edge AI, L4T, camera pipelines", 1, 1),
    ("JR90061", "Senior Rendering Engineer, RTX Neural Graphics", "Software Engineering", "US, NC, Durham", [], "Full time", "senior", "DLSS, neural rendering, path tracing, game engine integration", 1, 1),
    ("JR90062", "GeForce NOW Streaming Infrastructure Engineer", "Software Engineering", "PL, Warsaw", [], "Full time", "mid", "cloud gaming, video streaming QoE, edge POPs", 1, 0),
    ("JR90071", "Senior Omniverse Solutions Engineer, Industrial Digital Twins", "Software Engineering", "DE, Munich", [], "Full time", "senior", "OpenUSD, Omniverse, factory digital twins, BMW-scale deployments", 1, 1),
    ("JR90081", "Enterprise Account Manager, Healthcare AI", "Sales", "US, MA, Boston", [], "Full time", "senior", "Clara, BioNeMo, pharma accounts, quota carrying", 1, 1),
    ("JR90082", "Developer Relations Manager, Generative AI", "Marketing", "SG, Singapore", [], "Full time", "senior", "developer ecosystem, hackathons, NIM adoption", 1, 1),
    ("JR90083", "Sales Operations Analyst", "Sales", "US, CA, Santa Clara", [], "Full time", "mid", "pipeline analytics, Salesforce, forecasting", 1, 1),
    ("JR90091", "Technical Program Manager, GPU Supply Chain", "Operations", "TW, Taipei", ["US, CA, Santa Clara"], "Full time", "senior", "CoWoS capacity planning, OSAT partners, HBM supply, foundry engagement", 1, 1),
    ("JR90092", "Manufacturing Test Engineer", "Operations", "TW, Hsinchu", [], "Full time", "mid", "system level test, board bring-up, yield analytics", 1, 1),
    ("JR90093", "Senior Demand Planner", "Operations", "US, CA, Santa Clara", [], "Full time", "senior", "S&OP, data center demand planning, allocation", 0, 1),
    ("JR90101", "Senior Financial Analyst, Data Center BU", "Finance", "US, CA, Santa Clara", [], "Full time", "senior", "revenue forecasting, BU P&L, FP&A", 1, 1),
    ("JR90102", "Director, Export Compliance", "Legal", "US, DC, Washington", [], "Full time", "director", "export controls, EAR, licensing strategy, government affairs", 1, 1),
    ("JR90103", "HR Business Partner", "Human Resources", "IN, Bangalore", [], "Full time", "mid", "org design, employee relations", 1, 1),
    ("JR90104", "IT Support Technician", "Information Technology", "US, TX, Austin", [], "Full time", "entry", "helpdesk, ticket queue, AV support", 1, 1),
    ("JR90111", "Customer Support Engineer, Enterprise GPU", "Support", "IN, Pune", [], "Full time", "mid", "L2 support, break-fix, enterprise customers", 1, 1),
    ("JR90112", "Technical Support Specialist, GeForce NOW", "Support", "US, Remote", [], "Full time", "entry", "consumer support, streaming troubleshooting", 1, 1),
    ("JR90121", "Hardware Engineering Intern, Summer 2027", "Hardware Engineering", "US, CA, Santa Clara", [], "Part time", "intern", "internship, undergraduate, VLSI coursework", 0, 1),
    ("JR90122", "Software Engineering Talent Community - Future Openings", "Software Engineering", "US, CA, Santa Clara", ["US, Remote"], "Full time", "pipeline", "evergreen requisition, join our talent community, future opportunities", 1, 1),
    ("JR90123", "PhD Research Intern, Networking", "Research", "US, CA, Santa Clara", [], "Part time", "intern", "internship, PhD, network transport research", 1, 1),
    ("JR90131", "Member of Technical Staff", "Software Engineering", "US, CA, Santa Clara", [], "Full time", "mid", "distributed systems experience, C++, ownership mindset", 1, 1),
    ("JR90132", "Senior Engineer", "Hardware Engineering", "TW, Taipei", [], "Full time", "senior", "cross functional execution, debug, bring-up", 1, 1),
    ("JR90141", "Quantum Algorithms Engineer, CUDA-Q", "Software Engineering", "US, CA, Santa Clara", [], "Full time", "mid", "CUDA-Q, quantum-classical hybrid workflows, GPU simulation of quantum circuits", 0, 1),
    ("JR90142", "Senior Silicon Photonics Engineer", "Hardware Engineering", "US, CA, Santa Clara", ["TW, Taipei"], "Full time", "senior", "co-packaged optics, photonic integrated circuits, optical interconnect for scale-up fabrics", 0, 1),
]

SENIORITY_TEXT = {
    "entry": "0-2 years of experience.", "mid": "3+ years of relevant experience.",
    "senior": "6+ years of relevant experience.", "principal": "12+ years; recognized technical leader.",
    "director": "10+ years including people leadership.", "intern": "Currently enrolled student.",
    "pipeline": "This is an evergreen posting for future openings.",
}

def slug(title: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in title).strip("-")

def posting_stub(req, snap_days):
    req_id, title, fam, loc, extra, tt, sen, kw, *_ = req
    path = f"/job/{slug(loc)}/{slug(title)}_{req_id}"
    return {
        "title": title, "externalPath": path,
        "locationsText": loc if not extra else f"{len(extra)+1} Locations",
        "postedOn": f"Posted {snap_days} Days Ago", "bulletFields": [req_id],
    }

def detail_payload(req, posted_date):
    req_id, title, fam, loc, extra, tt, sen, kw, *_ = req
    desc = (f"<p>NVIDIA is looking for a {title} on the {fam} team. "
            f"You will work on {kw}.</p><p>{SENIORITY_TEXT[sen]}</p>"
            f"<p>NVIDIA is an equal opportunity employer.</p>")
    return {
        "jobPostingInfo": {
            "id": f"guid-{req_id.lower()}", "title": title, "jobDescription": desc,
            "location": loc, "additionalLocations": extra, "postedOn": posted_date,
            "timeType": tt, "jobReqId": req_id, "jobPostingId": f"post-{req_id.lower()}",
            "country": {"descriptor": loc.split(",")[0].strip()},
            "jobFamilyGroup": fam,
        },
        "hiringOrganization": {"name": "NVIDIA", "url": "https://www.nvidia.com"},
    }

def write(path: pathlib.Path, url: str, payload: dict, captured: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"source_url": url, "captured_at": captured,
                                "payload": payload}, ensure_ascii=False, indent=1))

def build_snapshot(snap: str, flag_idx: int, posted_date: str, days_ago: int):
    jobs = [j for j in JOBS if j[8 + flag_idx] == 1]
    root = FIXROOT / snap
    captured = f"{snap[:4]}-{snap[4:6]}-{snap[6:8]}T12:00:00Z"
    pages = [jobs[i:i+20] for i in range(0, len(jobs), 20)]
    for n, page in enumerate(pages):
        payload = {"total": len(jobs),
                   "jobPostings": [posting_stub(j, days_ago) for j in page],
                   "facets": [{"facetParameter": "jobFamilyGroup",
                               "values": sorted({j[2] for j in jobs})}]}
        write(root / "search" / f"page_{n:04d}.json", f"{CXS}/jobs", payload, captured)
    for j in jobs:
        write(root / "details" / f"{j[0]}.json",
              f"{CXS}{posting_stub(j, days_ago)['externalPath']}",
              detail_payload(j, posted_date), captured)
    manifest = {"snapshot": snap, "captured_at": captured, "source": f"{CXS}/jobs",
                "total_reported": len(jobs), "search_pages": len(pages),
                "postings_listed": len(jobs), "details_fetched": len(jobs),
                "probe": False, "synthetic": True,
                "note": "SYNTHETIC fixture data generated by make_fixtures.py — not real NVIDIA postings."}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"{snap}: {len(jobs)} postings, {len(pages)} pages")

if __name__ == "__main__":
    build_snapshot(SNAP_A, 0, "2026-06-20-07:00", 9)
    build_snapshot(SNAP_B, 1, "2026-06-27-07:00", 9)
