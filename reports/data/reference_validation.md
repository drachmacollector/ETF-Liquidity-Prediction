# Reference validation

**Result:** reference validation: 0 error(s), 2 warning(s)

## Errors

- none

## Warnings

- duty_india: 11 row(s) verified = n (listed in MI-09)
- band_regimes_india: 10 row(s) verified = n (listed in MI-09)

## Checks run

- instruments_us: schema OK (50 rows)
- instruments_in: schema OK (100 rows)
- symbol_history: schema OK (293 rows)
- nav_clock: schema OK (158 rows)
- corporate_actions_manual: schema OK (45 rows)
- duty_india: schema OK (19 rows)
- band_regimes_india: schema OK (14 rows)
- series_catalogue: schema OK (54 rows)
- calendar_overrides_in: schema OK (29 rows)
- T02.11-1 nav_clock coverage of included instruments
- T02.11-2 one AMFI code and at least one NSE symbol per included Indian instrument
- T02.11-3 no shared NSE symbol on the same date
- T02.11-4 group codes are System Specification §5.1 codes
- gate US_COMM_PHYS: 4 included (min 3) PASS
- gate US_COMM_FUT: 12 included (min 4) PASS
- gate US_BOND: 8 included (min 4) PASS
- gate US_INTL: 9 included (min 4) PASS
- gate US_CTRL: 5 included (min 3) PASS
- gate IN_GOLD+IN_SILVER: 39 included (min 10) PASS
- gate IN_INTL: 6 included (min 3) PASS
- T02.11-5 feasibility gate
- T02.11-6 duty and band-regime periods contiguous and non-overlapping
