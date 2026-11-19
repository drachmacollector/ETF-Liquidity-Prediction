# Data dictionary (curated store, P07)

Every table carries `source`; time-stamped tables carry `known_at` (UTC) per System Specification §7; `ingested_at` comes from the ingest manifest.

## instrument

- Primary key: `instrument_id`; source: reference tables; `known_at`: known at all times; rows: 150

| Column | Type | Description |
|---|---|---|
| `instrument_id` | str | US:<ticker> or IN:<ISIN> |
| `market` | str |  |
| `ticker` | str |  |
| `isin` | str |  |
| `name` | str |  |
| `issuer` | str |  |
| `group` | str | Spec §5.1 group |
| `subgroup` | str |  |
| `underlying` | str |  |
| `legal_form` | str |  |
| `listing_date` | datetime64[us] | first trading day (India: first bhavcopy appearance or inception) |
| `delisting_date` | datetime64[ns] |  |
| `currency` | str |  |
| `is_mirae` | bool |  |
| `rule_6c11` | str |  |
| `include` | bool | in the modelling universe |
| `exclude_reason` | str |  |
| `nav_basis_default` | str | first nav_clock basis |
| `source` | str |  |

## calendar

- Primary key: `market, date`; source: exchange_calendars; India: NSE bhavcopy presence for past dates; `known_at`: scheduled: known at all times; rows: 80,563

| Column | Type | Description |
|---|---|---|
| `market` | str |  |
| `date` | datetime64[ns] |  |
| `is_trading` | bool | trading day |
| `session_type` | string | regular | half | special |
| `source` | str |  |

## px_daily

- Primary key: `instrument_id, date`; source: Tiingo (US), NSE bhavcopy (India); `known_at`: US t 16:15 New York; India t 18:00 IST; rows: 398,121

| Column | Type | Description |
|---|---|---|
| `instrument_id` | str |  |
| `date` | datetime64[us] |  |
| `open` | float64 |  |
| `high` | float64 |  |
| `low` | float64 |  |
| `close` | float64 | official close, unadjusted for dividends, on the current split basis |
| `volume` | float64 | units, current split basis |
| `traded_value` | float64 |  |
| `n_trades` | float64 |  |
| `split_factor_applied` | float64 | factor by which raw prices were divided |
| `price_source` | str |  |
| `mapped_by_symbol` | bool | India pre-2011 rows mapped by symbol |
| `known_at` | datetime64[us, UTC] |  |
| `source` | str |  |
| `ingested_at` | datetime64[us, UTC] |  |

## nav_daily

- Primary key: `instrument_id, date`; source: issuer files/APIs (US), AMFI then mfapi (India); `known_at`: US t 20:00 New York; India AMFI upload time (else t 23:59 IST); rows: 328,730

| Column | Type | Description |
|---|---|---|
| `instrument_id` | str |  |
| `date` | datetime64[us] |  |
| `nav` | float64 | NAV per unit, current split basis |
| `shares_out` | float64 | units outstanding (US issuers where published) |
| `total_net_assets` | float64 |  |
| `nav_source` | str | source used |
| `known_at` | datetime64[us, UTC] |  |
| `split_factor_applied` | float64 |  |
| `source` | str |  |
| `ingested_at` | datetime64[us, UTC] |  |

## issuer_premium

- Primary key: `instrument_id, date`; source: SPDR Gold, Invesco, Global X files; `known_at`: t 20:00 New York; rows: 15,785

| Column | Type | Description |
|---|---|---|
| `instrument_id` | str |  |
| `date` | datetime64[us] |  |
| `issuer_prem_bps` | float64 | issuer-published premium (their clock/midpoint) |
| `issuer_mid` | float64 |  |
| `issuer_close` | float64 |  |
| `source` | str |  |
| `known_at` | datetime64[us, UTC] |  |
| `ingested_at` | datetime64[us, UTC] |  |

## series_daily

- Primary key: `series_id, date`; source: FRED, EIA, yfinance, derived; `known_at`: t + catalogue lag (business days), 18:00 source local time; rows: 429,160

| Column | Type | Description |
|---|---|---|
| `series_id` | str |  |
| `date` | datetime64[us] |  |
| `value` | float64 | series value |
| `unit` | str |  |
| `known_at` | datetime64[us, UTC] |  |
| `source` | str |  |
| `ingested_at` | datetime64[us, UTC] |  |
| `ret` | float64 | log return with roll days nulled (continuous futures) |
| `roll_flag` | object | detected roll day |

## in_spot_polls

- Primary key: `metal, polled_at_ist`; source: MCX polled spot (MI-05); `known_at`: the poll time; rows: 22,744

| Column | Type | Description |
|---|---|---|
| `metal` | str |  |
| `date` | datetime64[us] |  |
| `polled_at_ist` | datetime64[us, Asia/Kolkata] |  |
| `spot_time_local` | str |  |
| `price_inr` | float64 | INR per 10 g (gold) or per kg (silver) |
| `unit` | str |  |
| `purity` | object |  |
| `location` | str |  |
| `dup_polls` | int64 |  |
| `conflicting_polls` | bool |  |
| `series_type` | str |  |
| `ingested_at` | datetime64[us, UTC] |  |
| `known_at` | datetime64[us, UTC] |  |
| `source` | str |  |

## corporate_action

- Primary key: `instrument_id, ex_date, type, applies_to`; source: reference; `known_at`: known at all times (historical, verified); rows: 60

| Column | Type | Description |
|---|---|---|
| `instrument_id` | str |  |
| `ex_date` | datetime64[us] |  |
| `type` | str |  |
| `ratio` | float64 | new units per old unit |
| `applies_to` | str |  |
| `verified` | str |  |
| `source_url` | str |  |
| `notes` | str |  |
| `source` | str |  |

## operational_event

- Primary key: `event_id`; source: reference (P03); `known_at`: event known_at (never effective_at); rows: 48

| Column | Type | Description |
|---|---|---|
| `event_id` | str |  |
| `instrument_ids` | str |  |
| `scope` | str |  |
| `type` | str |  |
| `effective_at` | datetime64[us] | date the action takes effect |
| `known_at` | datetime64[us, UTC] |  |
| `ended_at` | str |  |
| `ended_known_at` | datetime64[us, UTC] |  |
| `date_precision` | str |  |
| `source_url` | str |  |
| `grade` | str |  |
| `related_incident_id` | str |  |
| `notes` | str |  |
| `source` | str |  |

## incident

- Primary key: `incident_id`; source: reference (P03); `known_at`: first_public_known_at; rows: 24

| Column | Type | Description |
|---|---|---|
| `incident_id` | str |  |
| `name` | str |  |
| `market` | str |  |
| `instrument_ids` | str |  |
| `group` | str |  |
| `mechanisms` | str | M1-M8 (pass-1 labels, MI-08 pending) |
| `primary_family` | str |  |
| `direction` | str |  |
| `approx_onset` | str |  |
| `peak_date` | str |  |
| `approx_end` | str |  |
| `peak_magnitude_text` | str |  |
| `near_miss` | str |  |
| `include_in_validation` | str |  |
| `in_dev_period` | str |  |
| `in_lockbox` | str |  |
| `first_public_known_at` | str |  |
| `analogue_anchor_date` | str |  |
| `grade` | str |  |
| `sources` | str |  |
| `notes` | str |  |
| `labelled_by` | str |  |
| `reviewed_by` | str |  |
| `review_status` | str |  |
| `source` | str |  |

## capacity

- Primary key: `instrument_id, as_of, metric, known_at, value`; source: SEC filings; `known_at`: EDGAR acceptance time; rows: 596

| Column | Type | Description |
|---|---|---|
| `instrument_id` | str |  |
| `as_of` | str |  |
| `metric` | str | registered_shares_total | registered_shares_remaining | shares_outstanding_reported |
| `value` | str |  |
| `unit` | str |  |
| `known_at` | datetime64[us, UTC] |  |
| `source_url` | str |  |
| `notes` | str |  |
| `source` | str |  |

## duty

- Primary key: `metal, effective_from`; source: reference (Budget documents); `known_at`: known at all times; unverified rows unused; rows: 19

| Column | Type | Description |
|---|---|---|
| `metal` | str |  |
| `effective_from` | datetime64[us] |  |
| `effective_to` | datetime64[us] |  |
| `bcd_pct` | float64 |  |
| `aidc_pct` | float64 |  |
| `sws_pct` | float64 |  |
| `other_pct` | float64 |  |
| `total_pct` | float64 | effective import duty % |
| `verified` | str |  |
| `source_url` | str |  |
| `notes` | str |  |
| `source` | str |  |

## band_regime

- Primary key: `market, exchange, group, effective_from`; source: reference (exchange circulars); `known_at`: known at all times; rows: 16

| Column | Type | Description |
|---|---|---|
| `market` | str |  |
| `exchange` | str |  |
| `group` | str |  |
| `effective_from` | datetime64[us] |  |
| `effective_to` | datetime64[us] |  |
| `base_rule` | str |  |
| `band_init_pct` | float64 | initial band % |
| `flex_step_pct` | float64 |  |
| `flex_max` | float64 |  |
| `cooling_off_note` | str |  |
| `verified` | str |  |
| `source_url` | str |  |
| `notes` | str |  |
| `source` | str |  |

## nav_clock

- Primary key: `instrument_id, effective_from`; source: reference; `known_at`: known at all times; rows: 158

| Column | Type | Description |
|---|---|---|
| `instrument_id` | str |  |
| `effective_from` | datetime64[us] |  |
| `effective_to` | datetime64[us] |  |
| `nav_basis` | str | Spec §6.3 basis code |
| `valuation_time_local` | str |  |
| `valuation_tz` | str |  |
| `source_url` | str |  |
| `notes` | str |  |
| `source` | str |  |

## quality_flag

- Primary key: `table, key, check_id`; source: P07 checks; `known_at`: -; rows: 598

| Column | Type | Description |
|---|---|---|
| `table` | str |  |
| `key` | str |  |
| `instrument_id` | str |  |
| `date` | datetime64[us] |  |
| `check_id` | str |  |
| `severity` | str | info | warn | error |
| `detail` | str |  |
| `detected_at` | datetime64[us, UTC] |  |
