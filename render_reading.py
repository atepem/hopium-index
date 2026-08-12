"""Render a Hopium Index reading from a results_*.json file.

gap = market_yes - ai_yes.
  gap > 0  -> market pays MORE than the AI thinks it's worth  (hope/drama premium; fade YES / buy NO)
  gap < 0  -> market pays LESS than the AI thinks               (fear/apathy discount; buy YES)

Prints a terminal table and writes reading_<date>.md next to the json.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "results_2026-08-11.json"
data = json.loads(path.read_text())

rows = []
for f in data["forecasts"]:
    gap = f["market_yes"] - f["ai_yes"]
    # NO-side return if you fade an overpriced YES: buy NO at (1-yes), collect 1 on NO
    fade_ret = f["market_yes"] / (1 - f["market_yes"]) if gap > 0 else None
    rows.append({**f, "gap": gap, "fade_ret": fade_ret})

rows.sort(key=lambda r: r["gap"], reverse=True)

hdr = f"{'MARKET':>7}  {'AI':>6}  {'GAP':>7}  {'fade→NO':>8}  question"
line = "-" * 94
out = [f"HOPIUM INDEX — reading {data['date']}", "", hdr, line]
for r in rows:
    fr = f"+{r['fade_ret']*100:4.1f}%" if r["fade_ret"] else "   —  "
    tag = "overpriced" if r["gap"] > 0 else "UNDERpriced"
    out.append(
        f"{r['market_yes']*100:6.1f}%  {r['ai_yes']*100:5.1f}%  "
        f"{r['gap']*100:+6.1f}  {fr:>8}  {r['question'][:46]}"
    )
out += ["", "gap = market − AI.  + = market over-hopes (fade YES).  − = market under-rates (buy YES)."]
report = "\n".join(out)
print(report)

# markdown journal
md = [f"# Hopium Index — reading {data['date']}", "",
      f"Forecaster: `{data['tool']}` via Olas mech `{data['mech'][:10]}…` · paid in USDC from the service safe · ~$0.01/market",
      "", "| Market YES | AI p_yes | Gap (pts) | Signal | Fade→NO return | Question |",
      "|---:|---:|---:|:--|---:|:--|"]
for r in rows:
    fr = f"+{r['fade_ret']*100:.1f}%" if r["fade_ret"] else "—"
    sig = "market over-hopes" if r["gap"] > 0 else "market under-rates"
    md.append(f"| {r['market_yes']*100:.1f}% | {r['ai_yes']*100:.1f}% | {r['gap']*100:+.1f} | {sig} | {fr} | {r['question']} |")
md += ["", "**Reading:** `gap = market_yes − ai_yes`. Positive = the crowd pays more than the AI's",
       "calibrated estimate (hope/drama premium → fade YES / buy NO). Negative = the crowd",
       "under-rates it (fear/apathy discount → buy YES).", "",
       "_Forecasts are one AI's calibrated read, not ground truth. Grade on resolution._"]
(path.parent / f"reading_{data['date']}.md").write_text("\n".join(md), encoding="utf-8")
print(f"\nwrote reading_{data['date']}.md")
