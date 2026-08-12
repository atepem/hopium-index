# hopium index

prediction markets don't just price odds — they price *feelings*. long shots
people are rooting for (aliens confirmed, satoshi waking up, the chargers
winning it all) trade richer than a cold forecaster says they're worth.

this repo measures that.

```
hopium = market price − ai probability
```

positive gap → the crowd is paying for the story, not the odds.

## how it works

1. **scan** — `scan_candidates.py` sweeps ~1200 live Polymarket markets
   (public Gamma API, no key needed) and keeps the wishful long shots:
   priced 3–30%, real liquidity, real volume, resolves within the year.
   hope-themed markets rank first.
2. **forecast** — each candidate gets an independent AI probability from an
   [Olas mech](https://olas.network/services/ai-mechs): a brier-calibrated
   superforecaster (`superforcaster-polymarket-v4`, GPT-4.1 + live web
   search), ~$0.01 per forecast, paid on-chain by the agent's own wallet.
   this step runs through [Pearl](https://olas.network/pearl)'s connect
   signing service — the agent composes transactions but never holds a key.
3. **read** — `render_reading.py` computes the gaps and writes a journal
   entry. every reading is logged; every call gets graded when the market
   resolves.

## run the scanner

```
python scan_candidates.py
```

pure stdlib, python 3.10+. writes `candidates.json` and prints the shortlist.

## honest caveats

- the AI forecast is one model's calibrated read, not ground truth. the
  whole point of grading on resolution is to find out if it's actually
  better than the crowd.
- a wide gap is a *hypothesis*, not free money: longshot fades have ugly
  payoff asymmetry, spreads eat edges, and capital gets locked until
  resolution.
- nothing here is financial advice. it's an experiment, run in the open.

## journal

readings live in `readings/` as dated markdown files, written by the agent
as it goes. entry 001: an AI paid one cent to price humanity's mars dream
at 0.5%.
