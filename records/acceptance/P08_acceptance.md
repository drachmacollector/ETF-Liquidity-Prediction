# P08 Acceptance Report — Pricing Layer

| Field | Value |
|---|---|
| Phase | P08 · prepared and verified by Claude Code, 2026-11-19 (same session) |
| Overall result | **PASS** (one known fact explained, D-020) |

## Tests

`tests/unit/test_premium.py` (4), `test_layer1.py` (2), `test_lock_class.py` (3), `tests/acceptance/test_p08_known_facts.py` (6), `test_p08_acceptance.py` (4) pass; full suite passes.

## Criteria

| ID | Criterion | Result | Evidence |
|---|---|---|---|
| AC-08.1 | Panel for every included instrument; no premium on invalid rows | PASS | `data/derived/pricing/pricing_panel.parquet`: 315,012 rows, 106 instruments |
| AC-08.2 | Known facts reproduced or explained | PASS | USO 21 Apr 2020 +3,641 bps; 1 May +145; UNG max +1,904 (28 Aug 2009); LQD min −508; GLD median 26 bps; SPY 1.8; MAFANG Apr 2026 median +1,815; issuer agreement GREK 0.4, BKLN 4.7 bps. SILVERAG +200 < +300 expected → explained (D-020) |
| AC-08.3 | b, s, band strictly backward-looking | PASS | `test_baseline_uses_only_prior_rows`, band test |
| AC-08.4 | Layer 1 where inputs verified; null reasons recorded | PASS | 30,159 rows with Layer 1; null reasons `duty_unverified` 36,339, `no_domestic_spot` 357 |
| AC-08.5 | Lock classes; Feb 2026 lock days visible | PASS | `lock_class`: unconstrained 31,360, near_band 20, unknown 93,379 (unverified regimes, MI-09); 1 Feb 2026: 14 silver ETFs `inferred_locked` (D-019) |
| AC-08.6 | EDA, NAV-basis-break and cost reports | PASS | `reports/pricing/` |

## Checklist

- GLD premium shows daily timing noise; the correlation of ETF-minus-NAV return with the post-strike gold move is reported in the EDA.
- NAV-basis break supported: after 1 Apr 2026, corr(NAV return, domestic spot return) 0.96 (gold) / 0.95 (silver) vs 0.50 / 0.43 with import parity.
- Every known-fact value is recorded in `reports/pricing/known_facts.csv`.
