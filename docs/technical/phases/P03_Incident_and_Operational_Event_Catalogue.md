# P03: Incident and Operational-Event Catalogue

| Field | Value |
|---|---|
| Phase ID | P03 |
| Depends on | P02 |
| Unlocks | P07 (operational events and capacity become curated tables), P13 (analogue finder and root-cause validation), P14/P15 (event replays) |
| Can run in parallel with | P04, P05, P06 |
| Estimated effort | 3–4 days (research-heavy) |
| Manual interventions | **MI-08** (user review and sign-off of mechanism labels and key dates) |
| Canonical references | Research Document §3 (mechanism taxonomy), §5 (incident record); System Specification §4.8 (`op_event`), §4.14 (families), §6.3 (`incident`, `operational_event`, `capacity`), §7 (`known_at`) |

## 1. Purpose

Create the curated, sourced, point-in-time-correct catalogue of (a) **incidents** (documented dislocation episodes and near-misses, each with a hand-assigned mechanism) and (b) **operational events** (creation suspensions, subscription halts, trading halts, overseas-cap stops, market closures) plus (c) a **capacity table** for US commodity pools (registered-share headroom).

**Why it matters:** the incidents are the ground truth for validating root-cause tags and the reference set for the analogue finder; operational events are a secondary evaluation target and a source of features (only via `known_at`); capacity rows feed the `CREATION_CONSTRAINT` family. **The mechanism labels must be assigned before any model exists** (this phase precedes P12–P13), so that root-cause validation is not contaminated by model output.

## 2. Scope

**In scope:** `reference/incidents.csv`, `reference/operational_events.csv`, `reference/capacity_us.csv`, the research protocol, the dating protocol, the double-review of mechanism labels, and `reports/catalogue/catalogue_report.md`.

**Out of scope:** computing price-based episodes (P09 does that objectively from data); linking incidents to data-detected episodes (P09/P13).

## 3. Prerequisites

- [ ] P02 `VERIFIED` (instrument IDs exist to reference).

## 4. Implementation specification

### T03.1 Research protocol

For every candidate row:

1. Find at least **one primary source** (SEC/EDGAR filing, issuer press release or notice, exchange circular, SEBI/AMFI document, AMC notice) **or two independent credible secondary sources**.
2. Record the exact URL, the publisher, the publication date and time if shown, and a short quote or paraphrase (≤ 30 words) supporting the key fact.
3. Assign an evidence grade using the Research Document scheme ([V], [R], [K]).
4. Save a copy of each source page as text or PDF under `data/raw/catalogue_sources/<row_id>/` (gitignored) and log it in `ingest_log.jsonl` with `source = catalogue`.

### T03.2 Dating protocol (`effective_at` vs `known_at`)

| Event type | `effective_at` | `known_at` |
|---|---|---|
| SEC filing (8-K, S-3, 10-Q) | Date the action takes effect as stated in the filing | **EDGAR acceptance timestamp** of the filing |
| Issuer press release / notice | Stated effective date | Publication timestamp; if only a date is known, 09:00 local on that date if published before the market opened is not provable → use **18:00 local** of the publication date (conservative) |
| Exchange circular | Stated effective date | Circular date, 18:00 local |
| AMC notice (India) | Stated effective date | Notice date, 18:00 IST; if only press coverage is found, the earliest article's date, 18:00 IST |
| Unscheduled market closure | First closed session | Announcement time if known; else the first closed session's date at 00:00 local (closure becomes known when the market fails to open) |

Never use `effective_at` as `known_at`. If a source gives only a month, the row is graded with `date_precision = month` and excluded from features (it may still be used for narrative).

### T03.3 Incident table (`reference/incidents.csv`)

Columns: `incident_id, name, market, instrument_ids (semicolon list), group, mechanisms (ordered list of M1–M8 codes, primary first), primary_family (CRE|STL|UND|LIQ|DEM|MKT), direction (PREMIUM|DISCOUNT|BOTH), approx_onset, peak_date, approx_end, peak_magnitude_text, near_miss (y/n), include_in_validation (y/n; n for ETNs and rows without usable data), in_dev_period (y/n), in_lockbox (y/n), first_public_known_at, analogue_anchor_date, grade, sources (semicolon URLs), notes, labelled_by, reviewed_by, review_status`.

**Minimum content (from Research Document §5; add others found while researching):**

| ID | Incident | Primary family |
|---|---|---|
| INC-US-2008-BOND | 2008 credit crisis: bond ETF discounts (LQD, HYG, MUB, others) | STL |
| INC-US-2009-UNG | UNG registered-share exhaustion, Jul–Sep 2009 | CRE |
| INC-US-2011-EGPT | Egypt exchange closure, Jan–Mar 2011 | STL |
| INC-US-2012-TVIX | TVIX issuance suspension (ETN; analogue-only, `include_in_validation = n`) | CRE |
| INC-US-2013-TAPER | Taper tantrum bond-ETF discounts, Jun 2013 | STL |
| INC-US-2015-GREK | Athens exchange closure, Jun–Aug 2015 | STL |
| INC-US-2015-CHINA | A-share suspensions, Jul 2015 | STL |
| INC-US-2020-BOND | March 2020 bond-ETF discounts | STL |
| INC-US-2020-GOLD-EFP | March 2020 COMEX–London dislocation (GLD) — confirm in data | UND |
| INC-US-2020-USO | USO creation suspension, Apr 2020 | CRE |
| INC-US-2021-SLV | Silver squeeze, Feb 2021 (near-miss) | DEM |
| INC-US-2022-RUSSIA | RSX/ERUS sanctions and closure, Feb–Mar 2022 | CRE |
| INC-US-2025-SILVER | Oct 2025 London silver squeeze (confirm whether US ETFs dislocated; may be near-miss) | UND |
| INC-US-2026-METALS | Jan–Feb 2026 metals crash | MKT |
| INC-IN-2013-GOLD | 2013 import restrictions, domestic gold premium | UND |
| INC-IN-2020-COVID | March 2020 Indian ETF gaps (candidate; confirm in data) | LIQ |
| INC-IN-2022-INTL | Overseas-cap stop, Feb 2022, international ETF premiums | CRE |
| INC-IN-2024-INTL | Overseas-ETF inflow stop from 1 Apr 2024 | CRE |
| INC-IN-2025-SILVER | Silver ETF premiums and FoF suspensions, Oct 2025 | UND |
| INC-IN-2026-CRASH | Gold/silver ETF crash and band lock-ups, Feb 2026 | MKT (with M7) |
| INC-IN-2026-INTL | International ETF premiums ~20–33%, 2025–2026 | CRE |

Mark `in_dev_period` / `in_lockbox` from `approx_onset` relative to `DEV_END`; Indian incidents are all out-of-sample for the transfer test.

### T03.4 Operational-event table (`reference/operational_events.csv`)

Columns: `event_id, instrument_ids, scope (instrument|issuer|industry|market), type, effective_at, known_at, ended_at, ended_known_at, date_precision (day|month), source_url, grade, related_incident_id, notes`.

Allowed `type` values: `creation_suspended`, `creation_resumed`, `creation_limited`, `subscription_halt_fof`, `subscription_resume_fof`, `subscription_halt_etf_direct`, `industry_cap_stop`, `trading_halt`, `trading_resumed`, `market_closure_unscheduled`, `market_reopen`, `registration_effective`, `fund_liquidation_announced`, `prospectus_risk_warning`.

Minimum content: every operational event mentioned in Research Document §5 (UNG 6–7 Jul 2009 suspension and 28 Sep 2009 resumption; USO April 2020 suspension and later registration; VanEck RSX creation suspension effective 3 Mar 2022 and Cboe halt 4 Mar 2022; SLV prospectus warning Feb 2021; Egypt and Athens closures and reopenings; Moscow Exchange closure; each Indian AMC's silver FoF halt and resumption in Oct 2025; SEBI/AMFI overseas stops of Feb 2022 and Apr 2024; Mirae international FoF/ETF subscription notices found). Search systematically for:

- EDGAR full-text search terms: "suspend the issuance of Creation Baskets", "suspend creation", "registered shares", for USCF funds, Teucrium, iPath/ETN issuers (ETNs analogue-only), and other commodity pools in the universe.
- Indian AMC notices for "suspension of lumpsum", "fund of fund" + "silver"/"gold"/"international".

### T03.5 Capacity table (`reference/capacity_us.csv`)

For US commodity pools/trusts in the universe that register a fixed number of shares (USCF funds, Teucrium, others identified): rows of `instrument_id, as_of, metric (registered_shares_total|registered_shares_remaining|shares_outstanding_reported), value, unit, known_at (EDGAR acceptance timestamp), source_url`. Sources: S-1/S-3 registration statements and amendments, 10-Q/10-K disclosures of shares registered and sold, 8-K notices. Grantor trusts with shelf registrations that rarely bind (GLD, SLV) get a single row noting the registration type.

**Purpose:** P10 computes "registered-share headroom as a percentage of shares outstanding", forward-filled from `known_at`. Where headroom is unknown, the feature is missing (never imputed).

### T03.6 Mechanism labelling and double review

1. The agent assigns `mechanisms` and `primary_family` using the taxonomy (Research Document §3) and records the reasoning in `notes` (one or two sentences).
2. The agent re-reviews every label in a **second pass** at least one working session later, without looking at the first-pass reasoning, and records disagreements.
3. The user reviews the table (MI-08) and either approves or edits. Edits are logged in `records/DECISIONS.md`.
4. Agreement statistics (first pass vs second pass; agent vs user) are reported in `catalogue_report.md`. They are evidence for assumption AS-06.

### T03.7 Pre-onset windows for the analogue finder

For each incident with `include_in_validation = y`, record `analogue_anchor_date` = the day before `approx_onset` (refined in P09 to the data-detected onset if one is matched). P13 builds signatures from features in the `[anchor − 9, anchor]` window. Only incidents with `known_at` of their first public report before a query date may be returned as analogues for that query date.

### T03.8 Catalogue report

`reports/catalogue/catalogue_report.md`: counts by market, family, period (dev/lockbox/India), near-miss count; timeline figure; list of rows with `date_precision = month`; double-review agreement; open questions arising.

### T03.9 Code

`esw.reference` gains schemas for the three tables; `esw catalogue validate` checks: unique IDs, allowed codes, `known_at ≥ effective_at` is **not** required (announcements can precede effect) but `known_at` must be present for `date_precision = day`; instrument IDs exist; URLs present; every incident has at least one source.

## 5. Deliverables

| Path | Description |
|---|---|
| `reference/incidents.csv`, `reference/operational_events.csv`, `reference/capacity_us.csv` | Catalogue tables |
| `reports/catalogue/catalogue_report.md` (+ `timeline.png`) | Summary |
| `src/esw/reference/catalogue.py`, CLI `esw catalogue validate` | Validation |
| `tests/unit/test_catalogue_schema.py`, `tests/acceptance/test_p03_acceptance.py` | Passing |

## 6. Tests and validation

- Schema tests (bad codes, missing `known_at`, unknown instrument) fail as expected.
- Acceptance test: minimum counts (AC-03.1), every row sourced, MI-08 status DONE.

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-03.1 | ≥ 18 incidents (≥ 12 US, ≥ 6 India), including every row listed in T03.3 (or a recorded reason for dropping one) |
| AC-03.2 | ≥ 30 operational events, each with `effective_at`, `known_at` (or `date_precision = month`), source URL and grade |
| AC-03.3 | Capacity rows exist for USO and UNG covering 2009 and 2020, with EDGAR `known_at` timestamps |
| AC-03.4 | Every incident has mechanism codes and a primary family; double-review agreement is reported |
| AC-03.5 | MI-08 completed: user approval recorded; edits logged |
| AC-03.6 | `esw catalogue validate` passes with zero errors |

## 8. Verification checklist (orchestrator)

- [ ] Spot-check five `known_at` values against the cited sources (EDGAR acceptance times in particular).
- [ ] Confirm no row uses `effective_at` as `known_at` without justification.
- [ ] Confirm near-misses are present (at least SLV 2021).

## 9. Risks and decision points

| Item | Handling |
|---|---|
| Sources paywalled (Bloomberg) | Use alternative sources; grade accordingly |
| Ambiguous mechanisms | Allow multiple mechanisms; the primary family must still be one code; flag ambiguity in notes |
| Hindsight bias in labelling | Labels describe causes documented in sources, not model behaviour; done before P12 |

## 10. Walkthrough requirements

Record: counts; incidents added beyond the minimum and why; rows dropped and why; disagreements in double review and how resolved; the user's edits.

## 11. Handoff

P07 turns the three tables into curated Parquet. P09 links data-detected episodes to incidents. P13 uses mechanisms for validation.
