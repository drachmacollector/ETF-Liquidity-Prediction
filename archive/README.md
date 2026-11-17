# Archive: superseded project documents

Nothing in this folder is current. **Do not use these files for building or as a source of facts unless the active documents point to them.** The active documentation starts at [`docs/00_INDEX.md`](../docs/00_INDEX.md).

| Folder | What it holds | Why it is superseded |
|---|---|---|
| `v1_gold_silver_premium_forecaster/` | The "final" v1 Research Document and Technical Master Specification (4–5 Nov 2026), the Masterclass notes, flowcharts, presentation notes (`points.md`), and the external review "Errors and inconsistencies…" | v1 forecast **next-day premium intervals for Indian gold/silver ETFs only**. The project changed direction in Nov 2026 (see `docs/source/`): it now forecasts **the onset of arbitrage breakdowns 1–5 days ahead**, is built and validated on US ETFs first, and is then tested for transfer to Indian ETFs. |
| `v0_early_drafts/old docs/` | Earlier drafts (v0/v2 master specs, deep-research report, early Mirae research) and Mirae logo files | Replaced by v1, then by the current set. |

## What was carried forward, and where

The v1 research was useful and parts of it were reused after re-checking:

- Indian regulatory facts (SEBI ETF price-band circular of 15 Jun 2026, market-maker and direct-transaction rules, overseas-investment caps): re-graded and summarised in the Research Document §6.
- The Oct 2025 silver and Jan–Feb 2026 crash chronologies: Research Document §5.
- Data traps for NSE bhavcopy and AMFI NAV: System Specification §6 and phase P05.
- Lessons from the external review (NAV vs iNAV mismatch, conservative circuit-lock classification, `known_at` vs `effective_at` on events, baselines must output probabilities, absolute-level monitor alongside the relative model): built into the System Specification and the phases P03, P07, P09, P11 and P16.

The other v1 design choices (next-day quantile regression, CQR intervals, India-only training, the R0/R1/R2 regime feature as the main structural-break device) were **reassessed rather than carried forward**. Research Document §11–§12 gives the reasons.
