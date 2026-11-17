# Issue Log

Format: [`docs/process/Documentation_Logging_and_Phase_Gates.md`](../docs/process/Documentation_Logging_and_Phase_Gates.md) §6. IDs `I-001`, `I-002`, … Severity: low | medium | high | blocker. A `blocker` sets the phase to `BLOCKED_ON_ISSUE` in `STATUS.md`.

## Open

### I-001 — USCF NAV download has no shares outstanding [OPEN]
- Found: 2026-11-17 · Phase: P01 · Severity: medium
- Symptom: USCF's "Download Historical NAV Performance" CSV contains only Date and NAV.
- Impact: Creation-activity features (F2) are missing for USO and UNG, the anchor capacity incidents (2009, 2020). Capacity headroom (F3, from SEC filings) is unaffected.
- Options: shares outstanding from 10-Q/10-K (quarterly, too coarse); CRSP (MI-06); accept missing-aware features for these funds and state it. Decide in P04/P10.

### I-002 — Tiingo free-tier rate limit (~50 requests/hour) [OPEN]
- Found: 2026-11-17 · Phase: P01 · Severity: low
- Symptom: HTTP 429 for DIA, IVV, IWM, QQQ and VOO metadata during probing.
- Plan: P04 paces Tiingo at ≤ 45 requests/hour (`sources.us_prices.tiingo_requests_per_hour`); yfinance fallback exists for all five.

### I-003 — Nippon "BeES" ETFs have NAV history only from 2016-11-07 under current AMFI codes [OPEN]
- Found: 2026-11-17 · Phase: P01 · Severity: low
- Symptom: GOLDBEES, NIFTYBEES, BANKBEES and JUNIORBEES start 2016-11-07 in mfapi and are absent from AMFI's 2010 snapshot (predecessor AMCs: Benchmark → Goldman Sachs → Reliance → Nippon).
- Impact: GOLDBEES, the largest gold ETF, lacks NAV before Nov 2016 unless predecessor codes are found. Nine other gold ETFs cover 2007–2011 onwards.
- Plan: P02 searches AMFI snapshots for predecessor scheme codes by name.

### I-004 — Unit splits in Indian gold ETFs [OPEN]
- Found: 2026-11-17 · Phase: P01 · Severity: medium
- Symptom: e.g., Kotak Gold ETF NAV ≈ ₹1,657 (Jan 2010) vs low hundreds now.
- Plan: P02 seeds corporate actions; P07 detects and reconciles (OQ-19).

### I-005 — RSX, EGPT and ERUS NAV history unavailable from free sources [OPEN]
- Found: 2026-11-17 · Phase: P01 · Severity: medium
- Impact: The Russia 2022 and Egypt 2011 incidents become catalogue-only (no model data) unless CRSP is available (MI-06). Prices exist on Tiingo.

## Resolved

_None yet._
