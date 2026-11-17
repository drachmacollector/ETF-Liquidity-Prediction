# P04: US ETF Data Acquisition (prices, NAV, shares outstanding)

| Field | Value |
|---|---|
| Phase ID | P04 |
| Depends on | P02 (and MI-07 accepted for the sources used) |
| Can run in parallel with | P03, P05, P06 |
| Unlocks | P07 |
| Estimated effort | 3–4 days (more if many manual downloads) |
| Manual interventions | **MI-02** (Tiingo key, required unless a fallback is chosen), **MI-04** (manual issuer downloads for `MANUAL_ONLY` sources), **MI-06** (CRSP, only if chosen in P01) |
| Canonical references | System Specification §6.1–6.3 (`px_daily`, `nav_daily`, `issuer_premium`), §7 (`known_at`), §11 (polite access); P01 probe matrix |

## 1. Purpose

Acquire, for every included US instrument and its full listing history, the unadjusted daily OHLCV prices, the official daily NAV, and (where published) shares outstanding and issuer-reported premium/midpoint data, into immutable raw files and source-shaped staged Parquet tables, with complete manifests and coverage reports.

## 2. Scope

**In scope:** ingestion adapters per source family; backfill from listing date to today; manual-drop parsers for files the user downloads; idempotent re-runs; coverage reporting.

**Out of scope:** reconciliation across sources, split adjustment, calendar alignment and point-in-time stamping (P07); computing premiums (P08).

## 3. Prerequisites

- [ ] P02 `VERIFIED`; `reference/instruments_us.csv` has `px_source_id`, `nav_source_id`, `shares_source_id` filled for every included instrument.
- [ ] MI-07 DONE for the sources to be used.
- [ ] MI-02 DONE if Tiingo is the primary price source; otherwise the fallback decision is logged.

## 4. Implementation specification

### T04.1 Adapter interface

`src/esw/ingest/base.py` defines:

```python
class SourceAdapter(Protocol):
    source_id: str

    def plan(self, instruments: pd.DataFrame, start: date, end: date) -> list[FetchTask]: ...
    def fetch(self, task: FetchTask) -> RawFile: ...  # writes to data/raw/<source_id>/..., logs manifest
    def parse(self, raw: RawFile) -> pd.DataFrame: ...  # returns source-shaped typed frame
```

Shared behaviour (in a base class): rate limiting per host, retries with exponential back-off and jitter (429/5xx; max 5), user agent from settings, skip if a complete raw file for the same task already exists (unless `--refresh`), SHA-256 checksum, manifest line per file, structured error capture (an adapter failure for one instrument must not stop the batch; it is logged with `status = failed`).

### T04.2 Price adapters

- `us_px_tiingo`: daily endpoint for each ticker from listing date. Store the raw JSON. Parse **raw** (unadjusted) `open, high, low, close, volume` and the vendor's split/dividend fields if present (keep `adjClose` etc. as separate columns for audit, never as the price used for premium).
- `us_px_stooq` and `us_px_yf` (fallbacks): same output columns; used only for instruments where Tiingo is missing or as a cross-check sample (P07 compares closes on a random sample of dates).
- Staged output: `data/staged/us_px/<source_id>.parquet` with columns `ticker, date, open, high, low, close, volume, vendor_split_factor, vendor_div_cash, source_id, raw_path, ingested_at`.

### T04.3 Issuer NAV and shares adapters

One adapter per issuer family found feasible in P01 (`us_iss_spdr_gold`, `us_iss_ishares`, `us_iss_ssga`, `us_iss_uscf`, `us_iss_invesco`, `us_iss_vaneck`, `us_iss_globalx`, `us_iss_xtrackers`, `us_iss_abrdn`, `us_iss_teucrium`, `us_iss_vanguard`, `us_wayback`). Each parses into:

`ticker, date, nav, shares_out, total_net_assets, issuer_close, issuer_mid, issuer_prem_bps, extra_json, source_id, raw_path, ingested_at`

- Keep any additional columns (e.g., GLD's ounces per share, LBMA price) in `extra_json` and also as typed columns where useful (`oz_per_share`, `benchmark_price`).
- If history must be assembled from several downloads (e.g., yearly files or rolling windows), the adapter deduplicates by date and records overlaps; conflicting overlapping values become a `quality_flag` candidate (passed to P07).
- **Manual drops:** for `MANUAL_ONLY` sources, the adapter reads files from `data/manual_drop/<source_id>/` following the naming convention in MI-04 (`<TICKER>_<anything>.<ext>`), logs each with `status = manual`, and parses them identically.

### T04.4 Optional CRSP adapter

Only if MI-06 succeeded: `us_crsp` reads the user's WRDS export (CSV) from `data/manual_drop/crsp/` with daily price, bid, ask, shares outstanding and, for funds in the CRSP mutual-fund database, daily NAV. Output columns as above plus `bid, ask`. CRSP bid/ask closes enable a direct check of the EDGE spread estimator (P10, AS-04).

### T04.5 Backfill and refresh commands

- `esw ingest us-prices [--tickers …] [--start …] [--end …] [--refresh]`
- `esw ingest us-nav [--tickers …] [--refresh]`
- `esw ingest us-all` (both, in order).
- All commands run inside `RunContext(phase="P04", purpose="ingest")`.

### T04.6 Coverage report

`reports/data/coverage_us.md` and `data/manifests/coverage_us.csv`, one row per instrument: `ticker, px_first, px_last, px_days, px_expected_days (XNYS between first and last), px_coverage_pct, nav_first, nav_last, nav_days, nav_coverage_pct, shares_days, issuer_prem_days, sources_used, manual_files, notes`. Expected days are counted on the US calendar between the later of listing date and source start, and the earlier of delisting date and today.

## 5. Deliverables

| Path | Description |
|---|---|
| `src/esw/ingest/{base,us_prices,us_issuers}.py` (+ `us_crsp.py` if used) | Adapters |
| `data/raw/us_*/**` (gitignored) and `data/manifests/ingest_log.jsonl` entries | Raw files and manifest |
| `data/staged/us_px/*.parquet`, `data/staged/us_nav/*.parquet` | Staged tables |
| `reports/data/coverage_us.md`, `data/manifests/coverage_us.csv` | Coverage |
| Tests: `tests/unit/test_us_parsers.py` (golden fixtures from P01), `tests/integration/test_us_ingest_idempotent.py`, `tests/acceptance/test_p04_acceptance.py` | Passing |

## 6. Tests and validation

1. **Golden-file parsing:** every adapter parses its P01 fixture to the expected columns, dtypes and row count.
2. **Idempotency:** running the same ingest twice creates no new raw files (status `skipped_cached`) and identical staged Parquet (content hash).
3. **Failure isolation:** a mocked HTTP 500 for one ticker yields `status = failed` for that ticker and success for the others.
4. **Unadjusted check:** for SPY, the staged close on an ex-dividend date equals the vendor raw close (not adjusted close).

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-04.1 | Every included instrument has staged price and NAV data; instruments that could not be obtained are switched to `include = false` in `instruments_us.csv` with a reason, and the P01 feasibility gate still passes |
| AC-04.2 | Price coverage ≥ 98% and NAV coverage ≥ 95% of expected trading days for every included instrument, or the shortfall is explained per instrument in the coverage report |
| AC-04.3 | GLD, SLV, USO, UNG and LQD NAV histories start within 30 calendar days of their listing dates (or the gap is explained and accepted by a logged decision) |
| AC-04.4 | Every raw file is listed in `ingest_log.jsonl` with a checksum; no raw file was modified after creation (checksums re-verified) |
| AC-04.5 | Idempotency and parser tests pass; `pytest -q` passes |
| AC-04.6 | Manual drops (if any) are logged with `status = manual` and the MI-04 checklist is DONE |

## 8. Verification checklist (orchestrator)

- [ ] Open the coverage report; check that no included instrument has a long unexplained gap (> 10 consecutive expected days).
- [ ] Look at USO staged price and NAV across April 2020: both series visible, split jump visible in at least one (reconciliation happens in P07).
- [ ] Confirm the staged UNG NAV includes July–September 2009.
- [ ] Re-run one ingest command and confirm `skipped_cached`.

## 9. Risks and decision points

| Item | Handling |
|---|---|
| Free-tier limits on Tiingo | Batch across days; cache; prioritise instruments; fallback adapters |
| Issuer file format changes mid-phase | Parser versioning (`parser_version` column); fixtures updated with a new golden file; old parser kept |
| NAV history shorter than listing (website truncation) | Wayback/CRSP/manual; else accept and document |
| Shares outstanding absent | Allowed (missing-aware features); record per instrument |

## 10. Walkthrough requirements

Record: sources actually used per instrument; manual files received; coverage summary table; instruments dropped; any parser quirks (date formats, thousand separators, split-adjusted NAV files).

## 11. Handoff

P07 consumes `data/staged/us_px` and `data/staged/us_nav`, reconciles sources, applies split consistency and stamps `known_at`.
