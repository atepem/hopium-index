"""Hopium Index v0 — candidate selector.

Pulls active Polymarket binary markets, keeps liquid + near-dated ones in the
longshot band (where the favorite-longshot bias -> hope-inflation is strongest),
and writes the top N by volume to candidates.json for the forecast step.

No funds move here: this is public read-only market data.
"""
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOW = datetime.now(timezone.utc)

# --- tunables ---------------------------------------------------------------
MIN_LIQUIDITY = 10_000     # USDC of resting liquidity -> can actually trade
MIN_VOLUME    = 15_000     # traded volume -> the crowd has actually priced it
YES_LOW, YES_HIGH = 0.03, 0.30   # longshot band: hope lives here
MIN_DAYS, MAX_DAYS = 3, 365      # near-dated, but not resolving tomorrow
N_CANDIDATES = 8
PAGES, PAGE = 6, 200       # scan up to 1200 markets by volume desc

# Hopium is about wishful/absurd markets, not doom. Drop the grim geopolitics,
# disaster, downside and horse-race-politics longshots so the shortlist reads
# on-theme: things people are rooting FOR.
EXCLUDE_TERMS = (
    "invade", "invasion", "war", "attack", "strike", "nuke", "nuclear",
    "pandemic", "virus", "outbreak", "die", "death", "dead", "killed",
    "kill", "assassinat", "regime", "coup", "recession", "depression",
    "crash", "bomb", "hostage", "genocide", "famine", "shooting", "shot",
    "leadership change", "out as president", "impeach", "indict", "arrest",
    "control the house", "control the senate", "shutdown", "default",
    "dip to", "fall to", "drop to", "below", "clash", "military", "out as",
)

# Things people are actively rooting for (or find delightfully absurd). Markets
# hitting one of these lead the shortlist so the thread reads on-theme.
HOPE_TERMS = (
    "alien", "mars", "moon", "space", "starship", "ufo", "nobel", "cure",
    "record", "win", "champion", "super bowl", "world cup", "all-time high",
    "all time high", "ath", "hit $", "reach $", "acquire", "greenland",
    "satoshi", "gpt-5", "agi", "fusion", "land on", "discover", "first",
)
# ---------------------------------------------------------------------------


def fetch_page(offset):
    url = (
        "https://gamma-api.polymarket.com/markets"
        f"?closed=false&active=true&limit={PAGE}&offset={offset}"
        "&order=volumeNum&ascending=false"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "hopium/0.1"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def days_out(end_iso):
    if not end_iso:
        return None
    try:
        end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
    except ValueError:
        return None
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return (end - NOW).total_seconds() / 86400.0


def parse(m):
    try:
        outcomes = json.loads(m.get("outcomes") or "[]")
        prices = [float(x) for x in json.loads(m.get("outcomePrices") or "[]")]
    except (json.JSONDecodeError, ValueError, TypeError):
        return None
    if [o.lower() for o in outcomes] != ["yes", "no"] or len(prices) != 2:
        return None
    return {
        "id": m.get("id"),
        "question": m.get("question"),
        "slug": m.get("slug"),
        "yes": prices[0],
        "volume": float(m.get("volumeNum") or 0),
        "liquidity": float(m.get("liquidityNum") or 0),
        "end": m.get("endDateIso") or m.get("endDate"),
        "days": days_out(m.get("endDateIso") or m.get("endDate")),
        "orderbook": bool(m.get("enableOrderBook")),
    }


def eligible(c):
    q = (c or {}).get("question", "").lower()
    return (
        c
        and c["orderbook"]
        and c["days"] is not None
        and MIN_DAYS <= c["days"] <= MAX_DAYS
        and c["liquidity"] >= MIN_LIQUIDITY
        and c["volume"] >= MIN_VOLUME
        and YES_LOW <= c["yes"] <= YES_HIGH
        and not any(term in q for term in EXCLUDE_TERMS)
    )


def main():
    seen, cands = set(), []
    for p in range(PAGES):
        for m in fetch_page(p * PAGE):
            c = parse(m)
            if eligible(c) and c["id"] not in seen:
                seen.add(c["id"])
                cands.append(c)
    def is_hope(c):
        return any(term in c["question"].lower() for term in HOPE_TERMS)

    # hope-themed first, then by volume within each tier
    cands.sort(key=lambda c: (is_hope(c), c["volume"]), reverse=True)
    top = cands[:N_CANDIDATES]
    (HERE / "candidates.json").write_text(json.dumps(top, indent=2))

    print(f"scanned ~{PAGES*PAGE} markets -> {len(cands)} in-band -> top {len(top)}:\n")
    print(f"{'YES':>6}  {'vol$':>10}  {'liq$':>9}  {'days':>4}  question")
    print("-" * 88)
    for c in top:
        print(
            f"{c['yes']*100:5.1f}%  {c['volume']:>10,.0f}  {c['liquidity']:>9,.0f}"
            f"  {c['days']:>4.0f}  {c['question'][:52]}"
        )


if __name__ == "__main__":
    main()
