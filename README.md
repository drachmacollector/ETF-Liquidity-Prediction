# ETF Arbitrage-Stress Early Warning System

A research prototype that estimates, for each ETF and each trading day, **the probability that a material, persistent gap between its market price and its NAV begins within the next 1–5 trading days**, shows **which part of the arbitrage mechanism is under strain** (creation constraint, stale NAV, underlying squeeze, liquidity drain, demand surge, market-wide stress), and names **the closest past incident**. It is built and validated on two decades of US ETF data (UNG 2009, March 2020 bond ETFs, USO April 2020, Russia ETFs 2022 and more) and then tested, without retraining, on Indian ETFs (October 2025 silver premiums, international ETFs under the overseas-investment cap, the February 2026 crash), with Mirae Asset's products highlighted against peers.

> Model estimates for internal research and discussion. Not investment advice and not a trading system.

## Status

Planning complete; build not started. See [`records/STATUS.md`](records/STATUS.md).

## Where to start

| You want to… | Read |
|---|---|
| Understand the problem, the evidence and why the approach was chosen | [`docs/research/ETF_Stress_Research_Document.md`](docs/research/ETF_Stress_Research_Document.md) |
| Know the exact definitions, architecture and conventions | [`docs/technical/00_System_Specification.md`](docs/technical/00_System_Specification.md) |
| Build the next phase | [`docs/technical/phases/`](docs/technical/phases/) (P00 → P17) |
| See what has actually been done | [`records/`](records/) |
| Do something only you can do (API keys, downloads, sign-offs) | [`docs/manual/MI-00_Index.md`](docs/manual/MI-00_Index.md) |
| Run a Claude Code session on this repo | [`CLAUDE.md`](CLAUDE.md) |

Full document map: [`docs/00_INDEX.md`](docs/00_INDEX.md). Superseded material: [`archive/`](archive/README.md).
