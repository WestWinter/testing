---
description: Equity research report on a stock, using LSEG data for prices, fundamentals and consensus
argument-hint: <TICKER or company name> [--detailed]
allowed-tools: mcp__LSEG__entity_search, mcp__LSEG__symbology_lookup, mcp__LSEG__historical_pricing_summaries, mcp__LSEG__qa_company_fundamentals, mcp__LSEG__qa_ibes_consensus, mcp__LSEG__qa_macroeconomic, WebSearch, WebFetch
---

<!-- Report layout inspired by quant-sentiment-ai/claude-equity-research (MIT). Data steps rewritten for the LSEG MCP. -->

Write an equity research report for: **$ARGUMENTS**

All numbers must come from LSEG tool results. Use WebSearch only for news, catalysts and qualitative context, and cite the source. Never fill a number from memory. If a tool returns nothing, write "n/a (no LSEG data)".

## Step 1: Resolve the security
- If given a company name, or a ticker you are unsure of, call `mcp__LSEG__entity_search` (entityType `organisation`) to get the PrimaryRIC and confirm it is a Public Company.
- Keep both the RIC (e.g. `AAPL.O`) and the plain ticker (e.g. `AAPL`). Fundamentals accept either; IBES takes the ticker.

## Step 2: Pull data (run independent calls in parallel)
1. **Price history**: `mcp__LSEG__historical_pricing_summaries` with the RIC, interval `P1D`, tenor `1Y`. From it compute: last close, 52-week high/low, 1M / 3M / 12M return, 50- and 200-day SMA, 14-day RSI, and average 20-day volume vs 3-month average volume. Do the arithmetic carefully and show the inputs.
2. **Benchmark**: the same call for `.SPX` (or the stock's home index) over `1Y`, for relative strength.
3. **Reported fundamentals**: `mcp__LSEG__qa_company_fundamentals`, freq `A`, the last 3 fiscal years (revenue, gross income, EPS, DPS), plus freq `C`, year `0` for the current P/E and trailing DPS.
4. **Consensus**: `mcp__LSEG__qa_ibes_consensus` with measures `Eps`, `Rev`, `Dps`, periodIndexStart `1`, periodIndexEnd `3`. Also `qa_ibes_actuals` with pIndex `0`, quarterly, to compare the last report with expectations.
5. **Peers**: pick 3-4 close competitors and pull their current P/E (freq `C`) and next-year consensus EPS.
6. **News and catalysts** (WebSearch): the latest earnings call, guidance, upcoming dates, regulatory or legal issues.
7. With `--detailed`, also check insider and institutional activity and options sentiment via WebSearch, and the macro backdrop (rates, GDP) via `mcp__LSEG__qa_macroeconomic`.

## Step 3: Write the report in this structure

# $ARGUMENTS — Equity Research (data: LSEG, as of <latest price date>)

## Executive summary
**BUY / HOLD / SELL**, 12-month price target $X (X% from the last close). Investment thesis in 1-2 sentences. Conviction: High / Medium / Low.

## Fundamentals
A table of revenue, gross margin, EPS and DPS for the last 3 fiscal years with YoY growth. Then the forward consensus for the next 3 years, and the latest actual vs consensus (beat or miss).

## Valuation
Current P/E, forward P/E (price ÷ next-year consensus EPS) and dividend yield, compared with the peer table. Bull / base / bear price targets with probabilities that sum to 100%, each derived from a stated multiple × an EPS figure.

## Technical picture
Price vs the 50/200-day SMAs (trend), RSI (overbought above 70, oversold below 30), position in the 52-week range, volume trend, and 12-month relative strength vs the benchmark. End with one line: **Technical signal: Bullish / Neutral / Bearish**, with the reason.

## Catalysts
Near-term (0-6 months) and medium-term (6-24 months), with dates where known.

## Risks
Company-specific and macro risks. A suggested position size (1-5% of a portfolio) and a stop-loss level tied to a technical level.

## Data notes
Which LSEG calls succeeded, what was missing, and the date of each data point.

---
*For research and education only. Not investment advice.*
