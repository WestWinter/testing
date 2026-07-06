# Government AI Equity-Stake Screen

Deliverables for the "front-run the next US government stake" analysis (built 2026-07-06):

- `REPORT.md` — full report: doctrine memo, 9-factor framework, back-cast validation, ranked scorecards, 13 deep dives, trading playbook, bear case, monitoring checklist.
- `gov_ai_stake_screen.xlsx` — workbook: Next-Name Ranking, Full Scorecard (102 names), By Subsector, Factor Definitions, Deal Precedents, Notes.
- `build_screen.py` — scoring engine + Excel builder. All scores/rationales live here; run `python3 build_screen.py` (needs `openpyxl`) to regenerate the xlsx and `scorecard_tables.md`.

## Weekly refresh procedure (automated routine)

1. Re-scan primary sources for the past week: Commerce/NIST/DoW/DOE/EXIM releases, "is said to seek a stake" wire leaks, White House actions, officials' interviews. Checklist in REPORT.md §9.
2. Update `build_screen.py`: adjust factor scores/penalties/status for new facts; add new deals to `DEALS`; add newly relevant tickers.
3. Rerun the script; re-splice `scorecard_tables.md` into REPORT.md §10; refresh approximate market caps for the top-15 names.
4. Append a dated entry to the REPORT.md Changelog describing score changes and why.
5. Commit and push to `claude/gov-ai-equity-screening-wkipey`.
