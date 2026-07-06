# QA report — snapshot `20260706T120000Z`

> ⚠️ **SYNTHETIC FIXTURE DATA** — pipeline verification only, not real NVIDIA postings.

| Check | Result | Detail |
|---|---|---|
| Q1 unique req_id | ✅ pass | 41 unique |
| Q2 total vs unique reqs | ✅ pass | source total 41, unique 41 (diff 0; multi-posting collapse expected) |
| Q3 location coverage | ✅ pass | 51 location rows, 41 primaries for 41 reqs |
| Q4 n_locations consistency | ✅ pass | ok |
| Q5 detail payload coverage | ✅ pass | all listed reqs have details |
| Q6 classification coverage | ✅ pass | ok |
| Q7 low-confidence rate | ✅ pass | 3/41 flagged (7%): ['JR90122', 'JR90131', 'JR90132'] |
| Q8 capture provenance | ✅ pass | ok |
| Q9 tracker invariants | ✅ pass | ok |

**9/9 checks passed.**
