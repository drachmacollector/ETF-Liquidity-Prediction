# P08 Walkthrough — Pricing Layer

| Field | Value |
|---|---|
| Phase | P08 · Status VERIFIED · 2026-11-19 · Claude Code |

## Built

`src/esw/pricing/{panel,band,layer1,locks,diagnostics}.py`; `esw build pricing`. Panel columns per T08.1 plus `lock_class_inferred`.

## Known-fact values

USO 21 Apr 2020 +3,641; 1 May 2020 +145; UNG Aug–Sep 2009 max +1,904 (28 Aug); LQD 9–23 Mar 2020 min −508; GLD median |prem| 2010–19 = 26; SPY = 1.8; SILVERAG 9–16 Oct 2025 max +200 (expected ≥ 300, D-020); MAFANG Apr 2026 median +1,815; issuer premium agreement GREK 0.4, BKLN 4.7 bps.

## Definition clarifications

- Layer 1: G = previous US close of COMEX futures, FX = previous yfinance INR=X, D = last MCX poll at or before 15:30 IST; gold per 10 g at 995, silver per kg at 999. `LP_NAV` before 1 Apr 2026 (the notional premium) is not identifiable without grams per unit, so `tg_bps` is computed only from 1 Apr 2026.
- Lock class follows the specification; `lock_class_inferred` adds data-based locks where regimes are unverified (D-019).

## Layer 1 coverage

30,159 gold/silver ETF-days; unverified duty periods are null (pre-Mar-2012, the 2013 steps, 2013–2019, 2022–2024, after 13 May 2026).

## Lock classes

Specified classes: unconstrained 31,360, near_band 20, confirmed_locked 0, unknown 93,379. Inferred locks: 1,144 (1,119 international ETFs at the upper band; 14 silver ETFs on 1 Feb 2026).

## NAV-basis break

Supported by the numbers (`reports/pricing/india_nav_basis_break.md`).

## Findings

- The NSE band rule is visible in prices: T-2 NAV ±20% binds repeatedly 2020–2026; on 1 Feb 2026 silver ETFs locked against T-1 NAV while gold ETFs touched the T-2 limit (D-019).
- October 2025 silver was first a Layer-1 event (+2,047 bps domestic premium on 13 Oct); ETF premiums against the official NAV were modest for Mirae and large for some peers (D-020).
