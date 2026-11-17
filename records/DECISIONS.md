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
