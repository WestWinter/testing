#!/usr/bin/env python3
"""Compute the technical indicators used by /equity-research.

Input: a JSON file holding the `headers` and `data` of an LSEG
historical_pricing_summaries response (daily bars, newest first, as LSEG
returns them). The fields used are DATE, TRDPRC_1, HIGH_1, LOW_1 and ACVOL_UNS.

    {"headers": [{"name": "DATE"}, {"name": "TRDPRC_1"}, ...],
     "data": [["2026-11-06", 342.37, ...], ...]}

Optional: --benchmark-return PCT, the benchmark's return over the same window,
used to report relative strength.

Usage: python3 tools/ta_indicators.py bars.json [--benchmark-return 7.7]
Standard library only.
"""
import argparse
import json
import statistics


def rsi(closes, period=14):
    """Wilder's RSI on closes ordered oldest first."""
    gains = [max(b - a, 0) for a, b in zip(closes, closes[1:])]
    losses = [max(a - b, 0) for a, b in zip(closes, closes[1:])]
    if len(gains) < period:
        return None
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for g, l in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
    if avg_loss == 0:
        return 100.0
    return 100 - 100 / (1 + avg_gain / avg_loss)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bars")
    ap.add_argument("--benchmark-return", type=float)
    args = ap.parse_args()

    with open(args.bars) as f:
        doc = json.load(f)
    names = [h["name"] for h in doc["headers"]]
    idx = {n: names.index(n) for n in ("DATE", "TRDPRC_1", "HIGH_1", "LOW_1", "ACVOL_UNS")}
    rows = [r for r in doc["data"] if r[idx["TRDPRC_1"]] is not None]
    rows.reverse()  # oldest first

    dates = [r[idx["DATE"]] for r in rows]
    close = [float(r[idx["TRDPRC_1"]]) for r in rows]
    high = [float(r[idx["HIGH_1"]] if r[idx["HIGH_1"]] is not None else r[idx["TRDPRC_1"]]) for r in rows]
    low = [float(r[idx["LOW_1"]] if r[idx["LOW_1"]] is not None else r[idx["TRDPRC_1"]]) for r in rows]
    vol = [float(r[idx["ACVOL_UNS"]] or 0) for r in rows]
    n, last = len(close), close[-1]

    def ret(k):
        return None if n <= k else (last / close[-1 - k] - 1) * 100

    def sma(p):
        return None if n < p else sum(close[-p:]) / p

    out = {
        "bars": n,
        "first_date": dates[0],
        "last_date": dates[-1],
        "last_close": last,
        "high_52w": max(high[-252:]),
        "low_52w": min(low[-252:]),
        "pct_below_52w_high": (1 - last / max(high[-252:])) * 100,
        "return_1m_pct": ret(21),
        "return_3m_pct": ret(63),
        "return_12m_pct": ret(min(n - 1, 252)),
        "sma50": sma(50),
        "sma200": sma(200),
        "rsi14": rsi(close),
        "avg_vol_20d": statistics.mean(vol[-20:]) if n >= 20 else None,
        "avg_vol_3m": statistics.mean(vol[-63:]) if n >= 63 else None,
    }
    if out["avg_vol_20d"] and out["avg_vol_3m"]:
        out["vol_20d_vs_3m"] = out["avg_vol_20d"] / out["avg_vol_3m"]
    if args.benchmark_return is not None and out["return_12m_pct"] is not None:
        out["relative_strength_12m_pct_pts"] = out["return_12m_pct"] - args.benchmark_return

    s50, s200 = out["sma50"], out["sma200"]
    if s50 and s200:
        if last > s50 > s200:
            trend = "uptrend (price > SMA50 > SMA200)"
        elif last < s50 < s200:
            trend = "downtrend (price < SMA50 < SMA200)"
        else:
            trend = "mixed"
        out["trend"] = trend

    for k, v in out.items():
        print(f"{k}: {round(v, 2) if isinstance(v, float) else v}")


if __name__ == "__main__":
    main()
