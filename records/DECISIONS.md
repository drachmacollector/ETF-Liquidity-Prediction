# Decision Log

Format, scope and approval rules: [`docs/process/Documentation_Logging_and_Phase_Gates.md`](../docs/process/Documentation_Logging_and_Phase_Gates.md) §5. IDs are sequential (`D-000`, `D-001`, …) except the reserved pre-registration IDs `D-P11-PREREG-A`, `D-P12-PREREG-B`, `D-P13-PREREG-EXPL`.

**Reserved / pending IDs:** D-001 (environment tool, P00), D-003 (commit policy, MI-01, P00).

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
