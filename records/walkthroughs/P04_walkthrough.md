# P04 Walkthrough — US ETF Data Acquisition

| Field | Value |
|---|---|
| Phase | P04 · Status VERIFIED · 2026-11-18 · Claude Code |

## Sources used per instrument

| Source | Instruments | History |
|---|---|---|
| Tiingo daily (raw OHLCV, splitFactor, divCash), paced ≤ 45/hour | all 50 candidates | from listing; 252,589 rows |
| SPDR Gold archive | GLD, GLDM | inception; NAV, oz/share, shares, issuer premium at 4:15pm |
| iShares fund download | IAU, SLV, GSG, LQD, HYG, MUB, EMB, AGG, TLT, EWJ, EWH, EWZ, EWW, FXI, EEM, INDA, TUR, IVV, IWM | inception; NAV + daily shares (split-adjusted) |
| SSGA NAV history | SPY, DIA, JNK | 2003/2007 |
| **USCF page API** (ALPS marketing API with the page-issued token, D-010) | USO, UNG, BNO, UGA, USL, UNL, CPER, USCI | NAV from 2009 (raw, not split-adjusted) |
| **Invesco dng-api** (curl client: the CDN rejects Python's TLS fingerprint) | DBC, DBA, DBO, BKLN, QQQ | NAV + TNA from 2016-09-29 |
| Global X premium/discount (MI-04 manual) | GREK | 2015-04-13 |

Automation (D-010) replaced the manual MI-04 rows for UGA, USL, UNL, USCI and the five Invesco funds. Not automatable within the phase: abrdn (SIVR, PPLT, PALL — site moved), Teucrium (CORN, WEAT, SOYB — NAV page is script-rendered with no data endpoint found), Vanguard (BND, VOO), DWS (ASHR) → excluded (D-015), recoverable by optional MI-04.

## Manual files

USO, UNG, BNO, CPER (USCF, identical to the API series and kept as cross-check `us_iss_uscf_manual`), GREK (Global X).

## Parser quirks

USCF values are `$`-formatted strings, raw split basis; Invesco premiums are midpoint-based percentages; iShares XML spreadsheet; SPDR archive has "US Holiday" rows. Staged paths are POSIX-style.

## Coverage

See `reports/data/coverage_us.md`. All included ≥ 99.28% NAV and ≥ 99.81% price coverage of XNYS days.

## Decisions

D-015.
