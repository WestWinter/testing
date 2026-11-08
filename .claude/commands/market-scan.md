---
description: Scan global indices and US sectors for overbought/oversold conditions and rising/falling earnings, using LSEG data
argument-hint: [optional: subset of indices/sectors, e.g. "Asia only"]
allowed-tools: mcp__LSEG__historical_pricing_summaries, mcp__LSEG__qa_ibes_consensus, mcp__LSEG__qa_macroeconomic, mcp__LSEG__entity_search, mcp__LSEG__symbology_lookup, Read, Write, Bash(python3 tools/market_scan.py:*), WebSearch
---

Run a market scan of global stock indices and US sectors. $ARGUMENTS

Every number comes from LSEG tool results or from `tools/market_scan.py`. Never fill a number from memory. Use WebSearch only to explain unusual moves, and cite the source.

## Step 0: Load the universe
Read `tools/market_scan_universe.json`. It lists:
- the indices and their MSCI fallbacks;
- the 11 S&P 500 sectors;
- for each earnings group, the largest companies with LSEG identifiers, expected EPS currency and approximate index weight.

If `$ARGUMENTS` names a subset, scan only that subset.

## Step 1: Prices (weekly bars, 1 year)
For each index and sector, call `mcp__LSEG__historical_pricing_summaries` with `universe` = the RIC, `interval` `P1W` and `tenor` `1Y`. Run the calls in parallel.
- **If a call returns an entitlement error ("User has no permission"), retry with the `fallback` RIC** (the MSCI equivalent) and record it as `"substitute": "<fallback_name>"`.
- If an index has no fallback listed and is blocked, find one: `mcp__LSEG__entity_search` with entityType `index` and query `"MSCI <country or region> Price Index USD"`. Prefer the `.dMI…PUS` RIC. Then retry. If nothing works, leave that index out and say so.

## Step 2: Earnings (bottom-up, weighted)
For every company in each earnings group, call `mcp__LSEG__qa_ibes_consensus` with dataType `qa_ibes_consensus` and:
- `ticker` = `id` and `tickerType` = `id_type`;
- `measures`: `["Eps"]`, or the company's `measure` field if it has one (`Ffops` for REITs);
- `periodType` `Year`, `periodIndexStart` 0, `periodIndexEnd` 2.

Rules for these calls:
- **Send one company per call**, with the calls in parallel. A single bad identifier fails the whole batch with a 404.
- Fetch a company only once, even when it appears in several groups.
- **Discard a result**, recording it as `null`, when:
  - the call returns 404;
  - the estimates come back in a currency other than the company's `ccy`;
  - the response contains more than one `estPermID`.

  The last two mean the identifier resolved to the wrong company. For example, ticker `ROG` returns Rogers Corp, not Roche.
- Record `[periodIndex 0, 1, 2]` EPS values in that order.

## Step 3: Valuation check
Call `mcp__LSEG__qa_macroeconomic` with `{"dataType": "series", "options": {"mnemonic": "USSPRPER", "limit": 1, "order": "desc"}}`. This is the S&P 500 CAPE. Index-level forward P/E and EPS aggregates are not available in this LSEG connection.

## Step 4: Compute
Write the data file to the scratchpad directory, using the layout documented at the top of `tools/market_scan.py`:
- `prices`: either `closes`, newest first, or the raw `headers` and `data` arrays;
- `earnings`: group → company name → `[eps0, eps1, eps2]` or `null`;
- `cape`.

Use the company names exactly as they appear in the universe file. Then run:

```
python3 tools/market_scan.py <scratchpad>/scan_data.json
```

Use its tables as they are. Do not recompute anything by hand.

## Step 5: Report
Write the report from the script output:

1. **Bottom line** (3–5 bullets): what is overbought, what is oversold, where earnings are rising and falling, and the best "oversold with rising earnings" setups.
2. **Indices table** and **sectors table**, from the script. Name every MSCI substitute in the Source column.
3. **Combined map**: a 3×3 grid of technical state (overbought / neutral / oversold) against earnings (rising / flat / falling).
4. **Notes on flagged items:**
   - Any `*` "check one-offs" flag: look at the per-company detail and explain in one line whether it's a real cycle peak (energy prices, for example) or an accounting one-off (investment gains, legal charges).
   - Any weekly move of ±8% or more in a broad index: give one WebSearch-sourced explanation, or say it's unexplained.
5. **Data notes:**
   - which indices were blocked and what replaced them;
   - which companies had no data or were discarded, and why;
   - coverage (% of index weight) for each group;
   - the caveat that weights are approximate and fiscal years differ;
   - groups with no earnings proxy (Russell 2000).

End with: *For research and education only. Not investment advice.*

## Maintenance
The universe weights are approximate. When a company's weight or membership changes noticeably, update `tools/market_scan_universe.json`. To add a company, check its identifier first with a single `qa_ibes_consensus` call. RICs containing lowercase letters (e.g. `SIEGn.DE`) are rejected by the tool; try the plain ticker instead and verify the currency.
