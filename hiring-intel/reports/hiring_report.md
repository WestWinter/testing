# NVIDIA hiring-intelligence readout — snapshot `20260706T120000Z`

> ⚠️ **SYNTHETIC FIXTURE DATA.** This report was generated from the synthetic test snapshot in `fixtures/` to verify the pipeline end-to-end. Numbers below describe the fixtures, **not NVIDIA**. Live collection was blocked by this build environment's egress policy — see `docs/source_map.md`. Re-run the pipeline after `collect.py` succeeds to produce the real readout.

*Source: public Workday CXS payloads. Captured at 2026-07-06T12:00:00Z.*

## Section A — Facts (counted directly from payloads)

- Unique open requisitions: **41** (source-reported total: 41)
- Multi-location requisitions: 10 (counted once each; 51 location rows in `locations.csv`)
- Role pools: core 35, support 3, intern 2, evergreen_pipeline 1
- Corporate/technical ("core") requisitions used for the mix below: **35**

### Core role mix by investor theme *(theme labels are inference — see Section B)*

| Category | Roles | Share |
|---|---:|---:|
| AI software & inference stack | 6 | 17% |
| Silicon & hardware engineering | 5 | 14% |
| Data-center & AI infrastructure | 5 | 14% |
| Networking (NVLink / InfiniBand / Ethernet / optics) | 4 | 11% |
| Sales & go-to-market | 3 | 9% |
| Supply chain & manufacturing capacity | 3 | 9% |
| Automotive / DRIVE | 2 | 6% |
| Robotics & edge (Jetson / Isaac / humanoids) | 2 | 6% |
| Frontier research | 1 | 3% |
| Gaming & consumer (GeForce / RTX) | 1 | 3% |
| Omniverse / simulation / digital twins | 1 | 3% |
| Corporate / G&A | 1 | 3% |
| Quantum computing (CUDA-Q) | 1 | 3% |

### Core role mix by function

| Category | Roles | Share |
|---|---:|---:|
| sw_engineering | 14 | 40% |
| hw_engineering | 8 | 23% |
| sales_gtm | 4 | 11% |
| operations_supply_chain | 3 | 9% |
| ga | 3 | 9% |
| research | 2 | 6% |
| product | 1 | 3% |

### Core role mix by primary-location country

| Category | Roles | Share |
|---|---:|---:|
| US | 22 | 63% |
| TW | 4 | 11% |
| IN | 3 | 9% |
| DE | 2 | 6% |
| IL | 1 | 3% |
| JP | 1 | 3% |
| CN | 1 | 3% |
| SG | 1 | 3% |

### Core role mix by seniority

| Category | Roles | Share |
|---|---:|---:|
| senior | 14 | 40% |
| ic | 12 | 34% |
| manager | 4 | 11% |
| principal_distinguished | 3 | 9% |
| entry | 1 | 3% |
| director_plus | 1 | 3% |

### Velocity since prior snapshot (fact: presence/absence between captures)

- Newly observed requisitions: **7**
- No longer listed (marked closed): **0**
- Temporarily absent: 2; re-opened: 0
- *A delisting means the posting left the site; it does not distinguish filled vs. cancelled.*

## Section B — Inference (rule-based labels, with confidence)

Theme, function and seniority labels are assigned by `classify.py` rules (title strongest, department second, description supporting). They are analyst constructs, not NVIDIA's own categories.

- Low-confidence labels flagged for manual review: **3** (7%) — `JR90122` "Software Engineering Talent Community - Future Openings", `JR90131` "Member of Technical Staff", `JR90132` "Senior Engineer"

**What this data can and cannot say:** job postings indicate where NVIDIA is *recruiting*. They do **not** prove strategy, approved budgets, product launch timing, or revenue impact. Postings can be evergreen, reposted, aspirational, or withdrawn without explanation. Treat themes as hypotheses to test against filings, earnings calls, and supply-chain checks.

## Section C — Watchlist: highest-signal individual postings

Ranked by a transparent score (strategic theme +2, watch keyword +1 each, principal/director seniority +1). Read the source posting before citing.

| Score | Req ID | Title | Why it scores | Source |
|---:|---|---|---|---|
| 5 | `JR90023` | Data Center Power Architect | strategic theme: datacenter_ai_infra; keyword: 800v; keyword: megawatt; senior hire: principal_distinguished | [posting](https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/job/US--WA--Redmond/Data-Center-Power-Architect_JR90023) |
| 4 | `JR90022` | Solutions Architect, AI Factories | strategic theme: datacenter_ai_infra; keyword: sovereign; senior hire: principal_distinguished | [posting](https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/job/JP--Tokyo/Solutions-Architect--AI-Factories_JR90022) |
| 4 | `JR90051` | Robotics Software Engineer, Isaac Manipulation | strategic theme: robotics_edge; keyword: gr00t; keyword: humanoid | [posting](https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/job/US--CA--Santa-Clara/Robotics-Software-Engineer--Isaac-Manipulation_JR90051) |
| 4 | `JR90091` | Technical Program Manager, GPU Supply Chain | strategic theme: supply_chain_capacity; keyword: cowos; keyword: hbm | [posting](https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/job/TW--Taipei/Technical-Program-Manager--GPU-Supply-Chain_JR90091) |
| 4 | `JR90142` | Senior Silicon Photonics Engineer | strategic theme: networking; keyword: photonics; keyword: co-packaged | [posting](https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/job/US--CA--Santa-Clara/Senior-Silicon-Photonics-Engineer_JR90142) |
| 3 | `JR90011` | Senior Software Engineer, NVLink Fabric | strategic theme: networking; keyword: nvlink | [posting](https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/job/US--CA--Santa-Clara/Senior-Software-Engineer--NVLink-Fabric_JR90011) |
| 3 | `JR90013` | Senior Product Manager, Spectrum-X Ethernet | strategic theme: networking; keyword: spectrum-x | [posting](https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/job/US--CA--Santa-Clara/Senior-Product-Manager--Spectrum-X-Ethernet_JR90013) |
| 3 | `JR90141` | Quantum Algorithms Engineer, CUDA-Q | strategic theme: quantum; keyword: quantum | [posting](https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/job/US--CA--Santa-Clara/Quantum-Algorithms-Engineer--CUDA-Q_JR90141) |
| 2 | `JR90005` | Thermal Engineer, Data Center Systems | strategic theme: datacenter_ai_infra | [posting](https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/job/US--CA--Santa-Clara/Thermal-Engineer--Data-Center-Systems_JR90005) |
| 2 | `JR90012` | InfiniBand Firmware Engineer | strategic theme: networking | [posting](https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/job/IL--Yokneam/InfiniBand-Firmware-Engineer_JR90012) |
| 2 | `JR90021` | Senior Site Reliability Engineer, DGX Cloud | strategic theme: datacenter_ai_infra | [posting](https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/job/US--Remote/Senior-Site-Reliability-Engineer--DGX-Cloud_JR90021) |
| 2 | `JR90035` | Research Scientist, Physical AI and World Models | keyword: world model; keyword: cosmos | [posting](https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/job/US--WA--Seattle/Research-Scientist--Physical-AI-and-World-Models_JR90035) |
