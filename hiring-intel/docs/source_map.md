# Step 1 — Public job source map: NVIDIA

*Prepared 2026-07-06. Endpoint shapes below are the standard Workday CXS contract; verify
against a live capture on first run (`collect.py --probe`) since tenants can rename sites.*

## Source of record

NVIDIA hosts its external careers site on **Workday Recruiting**:

| Item | Value |
|---|---|
| Public careers UI | `https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite` |
| Tenant | `nvidia` |
| Workday instance | `wd5` |
| Career site name | `NVIDIAExternalCareerSite` |
| Marketing entry point | `https://www.nvidia.com/en-us/about-nvidia/careers/` (links out to the Workday site) |

The visible page is a JavaScript SPA. **Do not scrape rendered HTML** — the SPA itself is fed
by a JSON API ("CXS"), which is the structured payload this project uses.

## Search endpoint

```
POST https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs
Content-Type: application/json
Accept: application/json

{"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}
```

Response shape (fields we rely on):

```json
{
  "total": 4000,
  "jobPostings": [
    {
      "title": "Senior ASIC Design Engineer",
      "externalPath": "/job/US-CA-Santa-Clara/Senior-ASIC-Design-Engineer_JR1990001",
      "locationsText": "US, CA, Santa Clara",
      "postedOn": "Posted 3 Days Ago",
      "bulletFields": ["JR1990001"]
    }
  ],
  "facets": [ { "facetParameter": "locationCountry", "values": [...] }, ... ]
}
```

- `facets` in the same response give official taxonomy counts (country, time type,
  job family group) — capture them each snapshot; they are a free cross-check on our
  own aggregations.

## Pagination logic

- `limit` is capped at **20** by the CXS API (larger values are silently clamped).
- Iterate `offset = 0, 20, 40, …` until `offset >= total`.
- **Consistency rule:** record `total` on the first page; if `total` drifts more than ~1%
  during the crawl (postings added/removed mid-crawl), finish the pass, then run one
  reconciliation pass. Store both passes; dedupe on requisition ID.
- Results are not guaranteed stable-ordered across pages; deduplication by requisition ID
  is mandatory (see QA checks).

## Job-detail endpoint

```
GET https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite{externalPath}
Accept: application/json
```

Returns `jobPostingInfo` with: `id`, `title`, `jobDescription` (HTML), `location`,
`additionalLocations[]`, `postedOn` / `startDate`, `timeType`, `jobReqId`,
`jobPostingId`, `country`, plus `hiringOrganization`. This is the authoritative
record for a posting.

## Stable identifier

- **`jobReqId`** (e.g. `JR1990001`) is the Workday requisition ID — stable for the life of
  a requisition, embedded in `bulletFields[0]` on search results, in the `externalPath`
  slug suffix, and in the detail payload. **This is the tracker's primary key.**
- `jobPostingId` / `id` are posting-level GUIDs; a requisition reposted to the site gets a
  new posting GUID but keeps its `jobReqId`. Never key on the GUID.
- One requisition may be posted with multiple locations (`additionalLocations`); it is
  still **one** requisition → one investor-counted role.

## Access-rule review (do this before every collection campaign)

1. `https://nvidia.wd5.myworkdayjobs.com/robots.txt` — confirm the CXS paths are not
   disallowed for generic crawlers.
2. Workday/NVIDIA site terms — collection must stay: public data only, no auth, no
   circumvention of technical controls, low request rate (default: 1 request/second,
   single connection), honest User-Agent with contact info.
3. If robots or terms disallow it, or the site starts answering 403/429, **stop** —
   the collector does this automatically (it aborts the campaign on 403 and backs off
   then aborts on repeated 429).

> **Status of this session:** live collection was NOT performed. This build environment's
> egress policy (organization-managed allowlist) returns 403 CONNECT for all non-GitHub
> hosts, including `nvidia.wd5.myworkdayjobs.com`. That is an access-rule stop condition
> for *this environment*, not a property of the public site. Run `collect.py` from a
> normally-connected machine after performing the review above.
