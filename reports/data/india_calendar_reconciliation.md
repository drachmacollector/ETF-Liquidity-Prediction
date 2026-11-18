# India calendar reconciliation (P05 T05.6)

Rule: a date is an NSE trading day if a CM bhavcopy with ≥ 500 rows exists (all 4,918 files have ≥ 500 rows). Compared with the preliminary P02 calendar (exchange_calendars XBOM + 29 bhavcopy-checked overrides).

| Date | Library (XBOM) | Bhavcopy | Class |
|---|---|---|---|
| 2013-11-14 | holiday | trading | library error (Muharram holiday moved by NSE to 15 Nov 2013) |
| 2013-11-15 | trading | no file | library error (the moved Muharram holiday) |

Special sessions (Muhurat 2007–2026, Budget Saturdays/Sunday 2015, 2020, 2025, 2026, Saturday DR sessions 2024) were already added in P02 from bhavcopy presence and agree. P07 adopts the bhavcopy calendar for past dates (`esw curate`).