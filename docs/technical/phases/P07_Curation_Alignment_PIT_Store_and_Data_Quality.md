# P07: Curation, Alignment, Point-in-Time Store and Data Quality

| Field | Value |
|---|---|
| Phase ID | P07 |
| Depends on | P03, P04, P05, P06 (all VERIFIED) |
| Unlocks | P08 |
| Estimated effort | 3–5 days |
| Manual interventions | None planned. Conflicts that cannot be resolved from data are escalated as decisions (e.g., an unexplained NAV jump in a key ETF). |
| Canonical references | System Specification §4.1–4.2, §6 (layers, schemas, split consistency), §7 (point-in-time rules) |

## 1. Purpose

Turn staged, source-shaped data and hand-built reference tables into **validated, canonical, point-in-time-stamped curated tables** that every later phase reads. This is where data errors are caught: unit/split inconsistencies, NAV errors, mapping errors, calendar mismatches, cross-source disagreements. After this phase, the dataset is frozen at a `DATA_CUTOFF` for all research phases.

## 2. Scope

**In scope:** canonical tables `instrument`, `symbol_history`, `calendar` (reconciled), `px_daily`, `nav_daily`, `issuer_premium`, `series_daily`, `corporate_action`, `operational_event`, `incident`, `capacity`, `duty`, `band_regime`, `nav_clock`, `quality_flag`; source precedence; split reconciliation; NAV anomaly detection; calendar alignment; `known_at` stamping; quality report; rebuild determinism; data dictionary; setting `DATA_CUTOFF`.

**Out of scope:** any derived analytics (premium is computed in P08, though this phase uses price/NAV ratios internally for diagnostics).

## 3. Prerequisites

- [ ] P03, P04, P05, P06 `VERIFIED`.

## 4. Implementation specification

### T07.1 Source precedence

| Table | Precedence (first available wins; others kept for cross-checks) |
|---|---|
| US `px_daily` | Tiingo raw → CRSP (if present) → Stooq → yfinance |
| US `nav_daily` | Issuer file → CRSP → Wayback archive |
| India `px_daily` | NSE → BSE (flag `fallback_exchange = BSE`) |
| India `nav_daily` | AMFI history → mfapi (flag) |
| `series_daily` | As set in the catalogue |

Precedence is configuration (`config/settings.yaml: curation.precedence`), not code.

### T07.2 Identity and mapping

- Join India price rows to instruments by ISIN; where a legacy row lacks ISIN, map by symbol through `symbol_history` with date validity and flag `mapped_by_symbol = true`.
- Assert one `px_daily` row per `(instrument_id, date)` after precedence; duplicates are an error.

### T07.3 Calendar alignment

- **India:** adopt the reconciled calendar from P05 (bhavcopy presence is authoritative for past dates; official lists for future dates). Update `calendar.parquet`.
- **US:** XNYS calendar; dates with prices outside the calendar are flagged; calendar days without prices for a listed instrument are gaps (counted in quality).
- **NAV alignment:** a NAV is attached to the trading date it is struck for. Indian NAVs for non-trading days (AMFI sometimes publishes NAVs on exchange holidays for funds whose underlying traded) are kept in `nav_daily` but do not create `px_daily` rows; P08 uses only dates on the instrument's listing calendar.

### T07.4 Split and unit consistency (System Specification §6.5)

1. Apply verified rows of `corporate_actions_manual.csv` to bring price and NAV to a **common current-unit basis** (record `split_factor_applied`).
2. Detect candidate unrecorded splits: day-over-day price ratio `r_p` and NAV ratio `r_n`; flag days where `|log(r_p) − log(r_n)| > log(1.5)` and either ratio is within 2% of a simple fraction (k or 1/k for k = 2…20). Each candidate becomes a `quality_flag` with severity `error`.
3. Resolve every `error` flag for included instruments: add a verified row to `corporate_actions_manual.csv` (with source) or document why the jump is real (e.g., an actual extreme dislocation day). **USO April 2020 is the reference test case**: after reconciliation, USO's price/NAV ratio across the reverse split must be continuous apart from the documented premium spike.

### T07.5 NAV anomaly detection

- **Jump-and-reverse:** NAV return on day t and t+1 both exceed 5 robust standard deviations of the instrument's NAV returns with opposite signs, while the price did not do the same → `quality_flag` `nav_spike` (severity `warn`). Not auto-corrected; P08 excludes flagged days from baselines and labels (`valid = false`) and lists them.
- **Stale NAV runs:** NAV unchanged for ≥ 3 consecutive trading days while the price moves → `nav_stale_run` (`info`): this is often *signal* (closed underlying market), not error. Keep.
- **Cross-source NAV check:** where two NAV sources overlap, report agreement; disagreements > 0.1% → `warn`.

### T07.6 Price sanity checks (pandera)

`high ≥ max(open, close)`, `low ≤ min(open, close)`, `low > 0`, `volume ≥ 0`; India `n_trades ≥ 0`; `|close/NAV − 1| > 25%` → `warn` flag for manual review (expected for Russia 2022, Indian international ETFs at times, USO 21 Apr 2020: review and annotate rather than delete). Cross-source close check (US): on 200 random instrument-dates, primary vs secondary vendor close agree within 0.5% on ≥ 99% of samples.

### T07.7 Point-in-time stamping

Add `known_at` (UTC) to every row of `px_daily`, `nav_daily`, `series_daily`, `operational_event`, `capacity`, `corporate_action` following System Specification §7 exactly. Implement in `esw.curate.pit` with unit tests for each rule (including the India late-evening NAV rule and the FRED lag rule).

### T07.8 Data cutoff

Set `DATA_CUTOFF` = the latest date for which both price and NAV are available for ≥ 90% of included instruments in **both** markets. Write it to `config/settings.yaml` and to `data/curated/DATA_CUTOFF.txt`. All research phases (P08–P15) filter to `date ≤ DATA_CUTOFF`. Later data are for the forward window in P16 only.

### T07.9 Quality report and coverage

`reports/data/quality_report.md` (+ CSV of flags): counts by check and severity per instrument; list of every `error` and its resolution; list of `warn` flags with annotations; final coverage per instrument after curation; summary of dates excluded from labels.

### T07.10 Rebuild determinism

`esw rebuild --curated` deletes and regenerates `data/curated/`. A test rebuilds twice and compares content hashes of every Parquet file (sort rows by primary key, fixed column order, no wall-clock timestamps in content: `ingested_at` comes from the manifest, not from `now()`).

### T07.11 Data dictionary

`reports/data/data_dictionary.md`, generated from the pandera schemas: table, column, type, unit, description, source, `known_at` rule.

## 5. Deliverables

| Path | Description |
|---|---|
| `src/esw/curate/{build,schemas,pit,checks,splits}.py`; CLI `esw curate`, `esw rebuild --curated` | Code |
| `data/curated/*.parquet`, `data/curated/DATA_CUTOFF.txt` | Curated store |
| `reports/data/quality_report.md`, `reports/data/quality_flags.csv`, `reports/data/data_dictionary.md` | Reports |
| Updated `reference/corporate_actions_manual.csv` | With all resolved splits |
| Tests: `tests/unit/test_pit_rules.py`, `tests/unit/test_split_detection.py`, `tests/integration/test_rebuild_determinism.py`, `tests/acceptance/test_p07_acceptance.py` | Passing |

## 6. Tests and validation

1. `pit` rule tests: one test per row of System Specification §7.
2. Split detection on a synthetic series with a 1:8 reverse split applied only to price detects it; after applying the corporate action, no flag.
3. Rebuild determinism (hash equality).
4. Acceptance: schema validation of every curated table; zero unresolved `error` flags for included instruments; USO continuity test; DATA_CUTOFF set.

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-07.1 | All curated tables exist and validate against their schemas |
| AC-07.2 | Zero unresolved `error` quality flags for included instruments (each resolved by a sourced corporate action, a documented annotation, or exclusion of the instrument) |
| AC-07.3 | USO price/NAV ratio is continuous across April 2020 except for the documented dislocation; same check passes for every other documented split |
| AC-07.4 | Every row in time-stamped tables has `known_at`, and the PIT rule tests pass |
| AC-07.5 | `DATA_CUTOFF` set and recorded |
| AC-07.6 | Rebuild determinism test passes |
| AC-07.7 | Quality report and data dictionary generated |

## 8. Verification checklist (orchestrator)

- [ ] Read the list of `warn` flags with `|close/NAV − 1| > 25%`; confirm each has an annotation (known incident or data issue).
- [ ] Confirm the reconciled India calendar contains 2026-02-01.
- [ ] Confirm `DATA_CUTOFF` is a recent trading day in both markets.

## 9. Risks and decision points

| Item | Handling |
|---|---|
| Unexplained jumps in a key instrument (GLD, SLV, USO, UNG, LQD, Mirae ETFs) | Do not exclude silently; raise a decision with evidence; the user may help by checking the issuer site |
| Large `warn` volume from international ETFs (timing) | Expected; annotate by mechanism (stale NAV) rather than flagging each day individually |

## 10. Walkthrough requirements

Record: precedence actually used; every resolved split; NAV anomalies found; instruments excluded at this stage; the chosen `DATA_CUTOFF`; any rule in System Specification §7 that proved impractical.

## 11. Handoff

P08 reads only `data/curated/` and `reference/`. From here, no phase reads `data/staged/` or `data/raw/`.
