# P06 Walkthrough — Underlying, Market-wide and FX Data

| Field | Value |
|---|---|
| Phase | P06 · Status VERIFIED · 2026-11-18 · Claude Code |

## Final series list

FRED (no key; the declared project agent — FRED stalls on browser agents): VIX, OVX, GVZ, BAA10Y, AAA10Y, DGS10, DGS2, TEDRATE (to 2022), DTWEXBGS (2006+), DTWEXM (to 2019), DEXINUS, DEXJPUS, DEXHKUS, DEXCHUS, DEXMXUS, DEXBZUS, DEXUSEU. EIA: WTI and Henry Hub contracts 1-4 to 2024-04-05. yfinance: TRY, RUB, EGP, INR (London close); gold, silver, platinum, palladium, copper, WTI, Brent, natural gas, RBOB front continuous; S&P 500, Nasdaq-100, NYSE FANG+, Nikkei, Hang Seng, Bovespa, IPC, BIST100, Athens composite, Nifty 50. Derived: `gold_usd_navimpl` (GLD NAV ÷ oz/share). India VIX staged in P05.

Market-open diagnostics: `data/staged/market_open/<MIC>.parquet` (scheduled vs index printed a new value) for XTKS, XHKG, BVMF, XMEX, XIST, XATH, XNSE, XNYS.

## Unavailable and affected features

silver NAV-implied (no oz/share in SLV file) → silver_usd_fut; RBI/FBIL rate (D-018) → DEXINUS/INR=X in Layer 1; post-2024 curve (D-017) → roll-yield missing after 2024-04-05; CSI300/HSTECH/EGX30/MOEX not served by yfinance (instruments excluded or proxied by Hang Seng).

## Roll handling

Front continuous futures carry `roll_flag`/`ret`; flagged returns nulled.

## Splices

None.
