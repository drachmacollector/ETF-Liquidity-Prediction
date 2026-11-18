# Decision Log

Format, scope and approval rules: [`docs/process/Documentation_Logging_and_Phase_Gates.md`](../docs/process/Documentation_Logging_and_Phase_Gates.md) §5. IDs are sequential (`D-000`, `D-001`, …) except the reserved pre-registration IDs `D-P11-PREREG-A`, `D-P12-PREREG-B`, `D-P13-PREREG-EXPL`.

**Reserved / pending IDs:** D-001 (environment tool, P00).

---

### D-000 — Adopt the revised project direction and this documentation set as the single source of truth
- Date: 2026-11-17 · Phase: pre-P00 · Decided by: user (request) / documentation author
- Context: The v1 project (next-day premium intervals for Indian gold/silver ETFs) was superseded by the revised direction in `docs/source/` (breakdown-onset early warning, US-first, India transfer test).
- Decision: Archive all v0/v1 material; adopt the Research Document, System Specification, phase documents, process protocol and MI guides as the governing documents. Key reassessments of the proposal are recorded in Research Document §12 (Rule 6c-11 scope; label uses `max(floor, k·scale)` not "either"; empirical no-arbitrage band instead of bottom-up excess premium; EDGE spread estimator instead of quoted spreads/depth; no historical iNAV; two model variants (full US vs transferable core) because India lacks creation data; two-layer gap and the 1 Apr 2026 Indian NAV-basis break).
- Consequences: All build work follows the phase order and gates in System Specification §13.
- Affects documents: all (initial versions 1.0)
- Reversible: yes, through a logged decision

### D-002 — Use the installed Python 3.11
- Date: 2026-11-17 · Phase: pre-P00 · Decided by: documentation author (within delegated scope)
- Context: Python 3.11 is installed on the user's machine; v1 assumed 3.12. All planned libraries support 3.11.
- Decision: Target Python ≥ 3.11; do not require a new installation.
- Consequences: `requires-python = ">=3.11"`.
- Reversible: yes

### D-003 — Commit policy: commit and push after every phase, with simple messages
- Date: 2026-11-17 · Phase: pre-P00 (MI-01) · Decided by: user
- User's words: "yes commit after every phase. also keep the commit messages simple and easy to understand. a repository has already been made https://github.com/drachmacollector/ETF-Liquidity-Prediction"
- Decision:
  1. Commit at the end of every phase, once it is VERIFIED (acceptance report and walkthrough written).
  2. Push to `origin` (https://github.com/drachmacollector/ETF-Liquidity-Prediction, branch `main`) after each phase commit.
  3. Commit messages are short, plain English, start with the phase ID, and say what was achieved, e.g. `P04: download US ETF prices and NAV history`. No jargon, no long bodies; one optional second line if something important needs saying (e.g., `Some files were downloaded by hand (MI-04).`). No attribution lines.
  4. Small record-keeping updates between phases (status, logs) may be committed with the same style, e.g. `Update project records`.
  5. Before every commit, check that no `.env`, `data/raw/`, `data/manual_drop/` or other gitignored paths are staged.
- Consequences: optional forward-test log (P16) can use GitHub commit timestamps.
- Reversible: yes

### D-004 — Data terms of use accepted for research use
- Date: 2026-11-17 · Phase: pre-P01 (MI-07) · Decided by: user
- User's words: "terms have been accepted."
- Decision: All planned sources (Research Document §9) may be used for non-commercial research and this demonstration. Raw vendor data are never committed or redistributed. If P01 finds a source whose terms prohibit automated access, it is switched to manual-only (MI-04/MI-05) and the user is told. SEC EDGAR requests use a generic project identifier only (no personal email) unless the user decides otherwise.
- Consequences: P01 still writes `reports/data/terms_of_use_summary.md` for the record; MI-07 does not block P04–P06.
- Reversible: yes

### D-001 — Use uv for the environment and lockfile
- Date: 2026-11-17 · Phase: P00 · Decided by: agent (within delegated scope)
- Context: P00 T00.1 prefers `uv` if it installs; fallback is venv + pip.
- Decision: `uv` 0.13.9 installed via pip. Environment: `.venv/` created by `uv sync --all-extras --python 3.11`; lockfile `uv.lock` (104 packages). Run commands with `.venv/Scripts/python.exe -m esw …` or `python -m uv run esw …`.
- Consequences: Recreate the environment with `python -m pip install uv` then `python -m uv sync --all-extras`.
- Reversible: yes

### D-005 — Indian NAV before 1 Apr 2026 included a notional delivery premium (correction)
- Date: 2026-11-17 · Phase: P01 · Decided by: agent (correction of a factual statement, evidence-based)
- Context: The Research Document assumed NAV = import parity before Apr 2026 (`LP_NAV ≈ 0`). SEBI's circular of 26 Feb 2026 (para 1) says the old valuation added transport, duty, taxes "and factoring notional premium or discount"; the Mirae Silver ETF SID describes it as "a notional premium that is usually charged for delivery of silver to the place where it is stored".
- Decision: `LP_NAV` before 2026-04-01 = a small, slow-moving notional delivery premium (estimated empirically in P08), not 0. Research Document → v1.1 (§4.1, §4.3); System Specification → v1.1 (§4.4).
- Consequences: P08 estimates the notional premium from NAV vs parity; the Oct 2025 interpretation (squeeze premium largely outside NAV) stands.
- Reversible: yes

### D-006 — Data source choices and fallbacks (from the P01 probes)
- Date: 2026-11-17 · Phase: P01 · Decided by: agent (within delegated scope; follows the D-004 access rules)
- Decision: US prices: Tiingo (primary, ≤ 45 requests/hour) → yfinance (fallback); Stooq dropped (browser check). US NAV: SPDR Gold archive, iShares and SSGA scripted; USCF, Invesco, Global X, Xtrackers, abrdn, Teucrium and Vanguard manual (MI-04); RSX/EGPT/ERUS unavailable unless CRSP (MI-06). India prices: NSE archive host (archives.nseindia.com) from 2016-01-01; before 2016 yfinance `.NS` or manual (MI-05); BSE dropped. India NAV: AMFI API (with upload timestamps) → mfapi.in. Domestic spot: manual (MI-05). India VIX: yfinance `^INDIAVIX`. Credit spread: FRED `BAA10Y` (ICE BofA OAS truncated). Futures curve: EIA to 2024-04-05, yfinance single contracts afterwards. No source is accessed by imitating a browser or bypassing bot protection.
- Consequences: Recorded in `config/settings.yaml: sources` and `reference/source_registry.csv`.
- Reversible: yes

### D-007 — Classify Indian ETFs by scheme name, not AMFI category
- Date: 2026-11-17 · Phase: P01 · Decided by: agent
- Context: AMFI files similar ETFs under inconsistent categories (GOLDBEES under "Other Scheme - Gold ETF"; ICICI Silver ETF under "Other ETFs"; ABSL Gold ETF under "Equity ETF").
- Decision: `esw.ingest.candidates.classify_india()` assigns IN_GOLD/IN_SILVER/IN_INTL/IN_DEBT from the scheme name, restricted to ETF categories and excluding FoFs and index funds. P02 hand-verifies the result.
- Reversible: yes

### D-008 — Indian NAV `known_at` = AMFI upload timestamp (IST)
- Date: 2026-11-17 · Phase: P01 · Decided by: agent
- Context: The AMFI API returns an upload time per NAV (labelled "Z" but it is IST wall-clock time). Most uploads are 22:00–23:00 IST; some are after midnight (02:00 observed).
- Decision: System Specification §7 updated: use the upload timestamp; fallback t 23:59 IST where unavailable. Decision time τ(t) = 08:00 IST on t+1 is unchanged and still after all observed uploads.
- Reversible: yes

### D-009 — Universe feasibility gate: PASS with manual dependencies
- Date: 2026-11-17 · Phase: P01 · Decided by: agent (gate rule in P01 T01.8)
- Decision: The gate passes when FEASIBLE_MANUAL instruments count, as T01.8 allows. The essential manual items (USCF: USO and UNG; Global X: GREK) become an **entry condition for completing P04**. If they cannot be obtained, the loss of coverage (capacity-type futures incidents; closure-type international incidents) goes to the user for a decision before P07.
- Reversible: yes

### D-010 — Automation first: browser-like clients allowed for public data files
- Date: 2026-11-17 · Phase: P02 (between P01 and P02) · Decided by: user
- User's words: "it is completely and absolutely okay for you to do this, anything that would lessen the manual steps and automate the implementation process is more than welcome."
- Context: In P01 the agent dropped a browser-like user-agent fallback and routed several sources to manual downloads (MI-04/MI-05).
- Decision: Automated download is tried first. A browser-like user agent and headers, session cookies and page-issued tokens may be used to fetch publicly downloadable files (`PoliteSession(browser=True)`). Rate limits and back-off still apply. SEC EDGAR keeps the declared generic project user agent (D-004). Manual interventions are raised only when automation fails.
- Consequences: CLAUDE.md, System Specification §11 (v1.2), `esw.ingest.http` and the MI-04 guide updated. Immediate gains in P02: the NSE archive host `nsearchives.nseindia.com` serves bhavcopies back to 2007 (P01 had 2016), and the BSE bhavcopy is downloadable. P04 retries the remaining MI-04 issuer files automatically.
- Reversible: yes

### D-011 — No CRSP (MI-06 declined: institution not registered with WRDS)
- Date: 2026-11-17 · Phase: P02 · Decided by: user (fact) / agent (consequence)
- Decision: Continue with free sources only. RSX, EGPT and ERUS stay `include = false` (I-005) and their incidents are catalogue-only in P03. USO/UNG shares outstanding stay missing (I-001); creation-activity features are missing-aware for these funds. The EDGE spread estimator is not validated against CRSP quotes (P10 assumption AS-04 stays an assumption).
- Reversible: yes (if CRSP access appears before P07)

### D-012 — P02 universe and identifier rules
- Date: 2026-11-17 · Phase: P02 · Decided by: agent (within P02 scope)
- Decision:
  1. US: every §5.2 candidate has a row. `FEASIBLE` and `FEASIBLE_MANUAL` rows are `include = true`; those whose NAV file has not arrived are marked "NAV pending" and flip to `false` in P04 if automation and MI-04 both fail. RSX, EGPT, ERUS are `false` (I-005).
  2. India: the instrument key is the **current** ISIN. A fund's NSE symbol and ISIN can change (AMC mergers, renames); P02 links them into one lineage from NSE bhavcopies and records every (symbol, ISIN) period in `symbol_history` (new column `isin`). Listing date = first bhavcopy appearance of the lineage, found by bisection of monthly samples.
  3. India controls: NIFTYBEES, SBINIFTY50 (formerly SETFNIF50), BANKBEES, JUNIORBEES, SENSEXIETF and Mirae NIFTYETF. Debt ETFs other than liquid/overnight are included (optional group). Gold/silver ETFs that were delisted or merged stay in the table as `include = false` for survivorship.
  4. Extra column `cik` in `instruments_us` (SEC registrant) for EDGAR work in P03/P04.
- Reversible: yes

### D-013 — Duty and price-band table conventions
- Date: 2026-11-17 · Phase: P02 · Decided by: agent
- Decision: (a) A duty change announced in a Budget speech is in force from the day after the speech (customs notifications issued on Budget day). (b) A row is `verified = y` only when the rate is in a primary document read by the agent (Budget speech or its annex, exchange circular); rates seen only in secondary reports stay `n` and are listed in MI-09. (c) Layer 1 is computed only for verified duty periods; lock class is `unknown` for unverified band rows (System Specification §4.4, §4.11). (d) The May 2026 duty increase (to 15%) is recorded as reported but unverified.
- Reversible: yes

### D-014 — Correction: USCF NAV download is not split-adjusted
- Date: 2026-11-17 · Phase: P02 · Decided by: agent (evidence)
- Context: P01 (OQ-04, primary_text_notes §5) quoted the USCF page saying NAV history is adjusted for the 2020 reverse split. The CSV received in MI-04 is raw: USO NAV jumps from 2.04 to 17.22 on 2020-04-29 and UNG shows four jumps (2011, 2012, 2018, 2024). BNO's NAV halves on 2013-08-28, one trading day before its price ex-date (2013-08-29).
- Decision: Treat the USCF file as unadjusted. All US splits are seeded in `reference/corporate_actions_manual.csv` with `applies_to` saying which raw series shows the jump (iShares NAV files are adjusted, so iShares splits apply to price only). OQ-04 amended.
- Reversible: yes

### D-015 — US NAV coverage after P04: accepted gaps and exclusions
- Date: 2026-11-18 · Phase: P04 · Decided by: agent (P04 AC-04.1/AC-04.3 allow exclusion or a logged explanation)
- Decision: (1) USO, UNG, UGA, USL start NAV on 2009-01-02 (USCF API and MI-04 files both start there): accepted; UNG 2009 and USO 2020 are covered, 2006-2008 USO is not. (2) DBC, DBA, DBO, BKLN, QQQ: Invesco's API gives NAV/TNA only from 2016-09-29: accepted (development-period rows before 2016 have no NAV and are not scored). (3) SPY/DIA NAV from 2003-12-01 (SSGA). (4) SIVR, PPLT, PALL, CORN, WEAT, SOYB, BND, VOO and ASHR set `include = false` (issuer NAV pages not automatable; optional MI-04 rows 6, 8-10). The P01 gate still passes (4/12/8/9/5 included per US group).
- Reversible: yes (re-include if MI-04 files arrive)

### D-016 — P03 closed as VERIFIED_WITH_PENDING (MI-08 label review becomes an entry condition of P12)
- Date: 2026-11-18 · Phase: P03 · Decided by: agent, under the user's instruction of 2026-11-18 ("go on implementing as many phases as possible ... I plan to do all the remaining manual tasks all together in one go")
- Context: P03 needs the user's review of mechanism labels (MI-08). Its purpose is that labels are fixed by people before any model exists. P07-P11 use incident dates and operational events, not the mechanism labels; labels are first used in P13 (root-cause validation), and models first exist in P12.
- Decision: P03 is `VERIFIED_WITH_PENDING`: every other P03 criterion is met; MI-08 is REQUESTED and is an **entry condition of P12**. Labels are not changed by the agent before MI-08; any change after MI-08 needs a logged decision. The user may reject this and ask to stop at P07 instead.
- Reversible: yes

### D-017 — No futures curve after 2024-04-05
- Date: 2026-11-18 · Phase: P06 · Decided by: agent
- Context: EIA stopped its NYMEX contract 1-4 series on 2024-04-05 (OQ-08). P01 assumed yfinance single contracts could continue the curve, but yfinance drops expired contracts: only still-live contracts (from Nov 2026) have history, and those were not the front months in the past.
- Decision: `wti_c1..c4`, `hh_c1..c4` end 2024-04-05; roll-yield/contango features (F6 `f6_roll_yield`) are missing after that date (missing-aware). Continuous front-month series (`CL=F`, `NG=F`) cover the whole span.
- Reversible: yes (if a free contract-level source is found)

### D-018 — India: AMFI monthly AUM and FBIL reference rate not acquired
- Date: 2026-11-18 · Phase: P05/P06 · Decided by: agent
- Decision: AMFI scheme-wise monthly AUM (JavaScript page, no stable file) and the FBIL/RBI INR reference rate are not acquired. No core feature depends on AUM; Layer 1 parity uses FRED DEXINUS / yfinance INR=X instead of the RBI rate (documented approximation).
- Reversible: yes
