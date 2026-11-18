# P03 Walkthrough — Incident and Operational-Event Catalogue

| Field | Value |
|---|---|
| Phase | P03 |
| Status | VERIFIED_WITH_PENDING (MI-08) |
| Period | 2026-11-18 |
| Author | Claude Code |

## 1. What was built

- `reference/incidents.csv` (24), `reference/operational_events.csv` (48), `reference/capacity_us.csv` (596), assembled by `src/esw/reference/bootstrap_catalogue.py` (now hand-edited source of truth; do not rerun the builder after MI-08).
- `src/esw/ingest/edgar.py` (submissions with acceptance times, full-text search, document fetch); `src/esw/reference/catalogue.py` + `esw catalogue validate`; `src/esw/reporting/catalogue_report.py` → `reports/catalogue/catalogue_report.md`, `timeline.png`, `second_pass.csv`, `source_capture.csv`.

## 2. Counts

US 17 incidents (dev 9, lockbox 8), India 7; families CRE 10, STL 6, UND 4, MKT 2, DEM 1, LIQ 1; 6 near-misses; 19 usable for validation (EGPT, TVIX, RUSSIA, WEAT, UNG-Nov-2007 excluded: no data or before NAV coverage).

## 3. Added beyond the minimum, and why

- INC-US-2022-WEAT: Teucrium Wheat Fund ran out of registered shares on 7 Mar 2022 (two 8-Ks), resumed 9 Mar after accelerated registration — found by EDGAR full-text search for suspension language.
- INC-US-2009-UNG-MAY and INC-US-2007-UNG-NOV: UNG disclosed only 8.1m / 0.5m registered units left; new registrations went effective before exhaustion → capacity near-misses (the same precursor as July 2009 without a suspension).

## 4. Findings while researching

- EDGAR `acceptanceDateTime` in the submissions JSON is UTC (not Eastern) — verified from nightly EFFECT notices; the code converts accordingly.
- EGPT: VanEck suspended creations on 31 Jan 2011 (secondary) — an M1 component in the Egypt case.
- GREK: the issuer's own file shows premiums of 3-8% during the 2015 closure; press reports disagree on the sign.
- SLV's Feb 2021 warning is in an S-3ASR accepted 5 Feb 2021 22:51 UTC (press says 3 Feb).
- Oct 2025 Indian silver FoF halts dated per AMC (Kotak 10 Oct … ICICI resumption 28 Oct); Axis conflicting.
- May 2026 Indian duty rise is reported (duty table, MI-09).

## 5. Double review

Pass 1 (labels with reasons) then pass 2 (later re-read): 22/24 agree. Disagreements: INC-US-2022-RUSSIA (CRE vs STL — the premium needs both blocked creation and an unknowable NAV) and INC-IN-2020-COVID (LIQ vs MKT). Pass-1 labels stand; both are flagged for the user.

## 6. Decisions

D-016 (VERIFIED_WITH_PENDING; MI-08 gates P12).

## 7. Pending

MI-08 (user review). Until then, P07-P11 may use incident dates and events but not the mechanism labels.
