#!/usr/bin/env python3
"""Compute the /market-scan tables from LSEG data collected by the command.

Usage:
    python3 tools/market_scan.py <scan_data.json> [--universe tools/market_scan_universe.json]

scan_data.json layout (filled in by the /market-scan command from LSEG tool results):

{
  "as_of": "2026-11-06",
  "cape": {"value": 40.71, "period": "2026-10"},              # optional, mnemonic USSPRPER
  "prices": {
    "S&P 500": {"ric": ".SPX", "closes": [7376.86, 7580.07, ...]},     # weekly closes, NEWEST FIRST
    "KOSPI":   {"ric": ".dMIKR00000PUS", "substitute": "MSCI Korea",    # MSCI fallback was used
                "headers": [{"name": "DATE"}, {"name": "TRDPRC_1"}, ...], "data": [[...], ...]}
  },                                                           # either "closes" or raw LSEG headers/data
  "earnings": {
    "S&P 500": {"NVIDIA": [4.90, 9.30, 15.84], "Apple": [8.86, 9.42, 10.50], "Tesla": null}
  }                                                            # [last reported FY, FY+1, FY+2]; null = no data
}

Weights come from the universe file and are renormalised over the names that returned data.
Standard library only.
"""
import argparse
import json
import statistics

CAP = 100.0  # growth rates are capped at +/-100% before weighting so one outlier cannot dominate


def closes_of(entry):
    if "closes" in entry:
        c = [float(x) for x in entry["closes"] if x is not None]
    else:
        names = [h["name"] for h in entry["headers"]]
        i = names.index("TRDPRC_1")
        c = [float(r[i]) for r in entry["data"] if r[i] is not None]
    return c[::-1]  # oldest first


def rsi(c, p=14):
    gains = [max(b - a, 0) for a, b in zip(c, c[1:])]
    losses = [max(a - b, 0) for a, b in zip(c, c[1:])]
    if len(gains) < p:
        return None
    ag, al = sum(gains[:p]) / p, sum(losses[:p]) / p
    for g, l in zip(gains[p:], losses[p:]):
        ag, al = (ag * (p - 1) + g) / p, (al * (p - 1) + l) / p
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)


def technicals(c):
    last = c[-1]
    ret = lambda w: (last / c[-1 - w] - 1) * 100 if len(c) > w else None
    ma40 = sum(c[-40:]) / 40 if len(c) >= 40 else None
    r = rsi(c)
    vs = (last / ma40 - 1) * 100 if ma40 else None
    if r is not None and vs is not None:
        if r >= 70 or vs >= 10:
            state = "Overbought"
        elif r <= 30 or vs <= -8:
            state = "Oversold"
        elif r >= 62:
            state = "Stretched"
        elif r <= 40:
            state = "Weak"
        else:
            state = "Neutral"
    else:
        state = "n/a"
    return {"wk": ret(1), "4w": ret(4), "13w": ret(13), "52w": (last / c[0] - 1) * 100,
            "off_hi": (last / max(c) - 1) * 100, "vs40w": vs, "rsi": r, "state": state, "n": len(c)}


def growth(a, b):
    if a is None or b is None or a <= 0:
        return None
    return (b / a - 1) * 100


def earnings(group_spec, data):
    rows, w1, w2, s1, s2, hump_w = [], 0.0, 0.0, 0.0, 0.0, 0.0
    total_w = sum(x["w"] for x in group_spec)
    got_w = 0.0
    for x in group_spec:
        eps = data.get(x["name"])
        if not eps or len(eps) < 3 or any(v is None for v in eps[1:]):
            rows.append((x["name"], x["w"], None, None, "no data"))
            continue
        g1, g2 = growth(eps[0], eps[1]), growth(eps[1], eps[2])
        got_w += x["w"]
        note = ""
        if g1 is not None and g2 is not None and g1 > 30 and g2 < 0:
            note = "hump: possible one-off in FY+1"
            hump_w += x["w"]
        if eps[0] is not None and eps[0] <= 0:
            note = "loss base: FY0->1 excluded"
        if g1 is not None:
            w1 += x["w"]; s1 += x["w"] * max(-CAP, min(CAP, g1))
        if g2 is not None:
            w2 += x["w"]; s2 += x["w"] * max(-CAP, min(CAP, g2))
        rows.append((x["name"], x["w"], g1, g2, note))
    g2s = [r[3] for r in rows if r[3] is not None]
    return {
        "wtd_next": s1 / w1 if w1 else None,
        "wtd_after": s2 / w2 if w2 else None,
        "median_after": statistics.median(g2s) if g2s else None,
        "up": sum(g > 0 for g in g2s), "n": len(g2s),
        "coverage": got_w,               # % of index weight covered (weights are index weights in %)
        "hump_share": hump_w / got_w if got_w else 0.0,
        "listed": total_w,
        "rows": rows,
    }


def f(v, nd=1, pct=True):
    if v is None:
        return "n/a"
    return f"{v:+.{nd}f}%" if pct else f"{v:.{nd}f}"


def earn_state(e):
    if e is None or e["wtd_after"] is None:
        return "n/a"
    g = e["wtd_after"]
    return "Rising" if g >= 8 else "Flat" if g >= 0 else "Falling"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scan")
    ap.add_argument("--universe", default="tools/market_scan_universe.json")
    a = ap.parse_args()
    U = json.load(open(a.universe))
    D = json.load(open(a.scan))
    groups = U["earnings_groups"]
    E = {g: earnings(groups[g], D.get("earnings", {}).get(g, {})) for g in groups if g in D.get("earnings", {})}

    print(f"# Market scan: data as of {D.get('as_of', '?')}\n")
    for title, items in (("Indices", U["indices"]), ("US sectors", U["sectors"])):
        print(f"## {title}: technicals and earnings\n")
        print("| | Source | 1 wk | 4 wk | 13 wk | 52 wk | From 52-wk high | vs 40-wk avg | Weekly RSI | Signal | EPS FY+1 (wtd) | EPS FY+2 (wtd) | Breadth | Coverage | Earnings | Combined |")
        print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for it in items:
            p = D.get("prices", {}).get(it["name"])
            if not p:
                print(f"| {it['name']} | not available | " + " | ".join(["n/a"] * 14) + " |")
                continue
            t = technicals(closes_of(p))
            src = p.get("ric", it["ric"]) + (f" ({p['substitute']})" if p.get("substitute") else "")
            e = E.get(it.get("earnings"))
            es = earn_state(e)
            combo = {("Oversold", "Rising"): "Opportunity", ("Weak", "Rising"): "Watch for entry",
                     ("Overbought", "Rising"): "Strong but stretched", ("Stretched", "Rising"): "Strong but stretched",
                     ("Overbought", "Falling"): "Avoid", ("Stretched", "Falling"): "Avoid",
                     ("Neutral", "Falling"): "Avoid", ("Weak", "Falling"): "Avoid", ("Oversold", "Falling"): "Value trap risk",
                     ("Oversold", "Flat"): "Cheap, no catalyst", ("Weak", "Flat"): "Cheap, no catalyst",
                     ("Neutral", "Rising"): "Healthy"}.get((t["state"], es), "-")
            if e and e["hump_share"] >= 0.2:
                # >=20% of covered weight shows a spike-then-drop EPS path: could be a real cycle peak
                # (e.g. oil) or a one-off gain (e.g. investment mark-ups). Flag it for a manual check.
                es += "*"
                combo += " (check one-offs*)"
            ecols = ["n/a"] * 4 if not e else [f(e["wtd_next"]), f(e["wtd_after"]), f"{e['up']}/{e['n']} up",
                                                 f"{e['coverage']:.0f}% of index"]
            print(f"| {it['name']} | {src} | {f(t['wk'])} | {f(t['4w'])} | {f(t['13w'])} | {f(t['52w'])} | "
                  f"{f(t['off_hi'])} | {f(t['vs40w'])} | {f(t['rsi'], 1, False)} | {t['state']} | "
                  + " | ".join(ecols) + f" | {es} | {combo} |")
        print()

    if D.get("cape"):
        c = D["cape"]
        print(f"**S&P 500 CAPE (Shiller P/E10):** {c['value']:.1f} ({c.get('period', '')}). The long-run average is about 17.\n")

    print("## Earnings detail (consensus EPS growth per company)\n")
    for g, e in E.items():
        parts = []
        for name, w, g1, g2, note in e["rows"]:
            s = f"{name} ({w}%): {f(g1, 0)} / {f(g2, 0)}" if g2 is not None else f"{name} ({w}%): no data"
            if note:
                s += f" [{note}]"
            parts.append(s)
        print(f"- **{g}**: weighted FY+1 {f(e['wtd_next'])}, FY+2 {f(e['wtd_after'])}, median FY+2 {f(e['median_after'])}, "
              f"coverage {e['coverage']:.0f}% of index. " + "; ".join(parts))
    print("\n*Growth rates are capped at ±100% before weighting. Weights are approximate index weights from the universe "
          "file, renormalised over companies with data. Fiscal years differ by company. An asterisk on Earnings means 20% "
          "or more of the covered weight shows a spike-then-drop EPS path (FY+1 up >30%, FY+2 down): either a genuine "
          "cycle peak or a one-off gain in FY+1, which needs a manual check.*")


if __name__ == "__main__":
    main()
