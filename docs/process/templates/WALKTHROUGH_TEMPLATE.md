# PXX Walkthrough — <Phase title>

| Field | Value |
|---|---|
| Phase | PXX |
| Status at time of writing | IMPLEMENTED / VERIFIED / checkpoint |
| Period | <start date> → <end date> |
| Sessions | <n> (see PROGRESS_LOG entries dated …) |
| Author | <agent/session id or user> |
| Git commit at end | <hash> (or "uncommitted: D-003 policy") |

## 1. Entry conditions (checked at start)

- [x] Prerequisite 1 … (evidence)
- [ ] … (if any was waived: decision ID)

## 2. What was completed

Bullet list of tasks T-xx.y with one line each: done / partially done / not done.

## 3. Outputs produced (where they are)

| Output | Path | Size / rows / count | Notes |
|---|---|---|---|

## 4. Key results and findings

Numbers that matter for later phases (coverage, counts, metrics, verdicts), each with its run ID or file.

## 5. Decisions made

| ID | Decision | Why | Decided by |
|---|---|---|---|

## 6. Deviations from the plan

| Planned (doc section) | Actual | Reason | Impact on later phases | Decision ID |
|---|---|---|---|---|

## 7. Issues encountered

| ID | Issue | Status | Resolution / workaround |
|---|---|---|---|

## 8. Unresolved problems and open questions

What remains uncertain, who must resolve it, and by which phase.

## 9. Manual interventions

| MI | Status | Date | Notes |
|---|---|---|---|

## 10. Exact current state of the project

- Data present: …
- Code modules complete: …
- Tests: `pytest -q` → <n passed, n skipped>; acceptance test → PASS/FAIL
- Configuration: settings version/hash; pre-registration hash (if applicable)
- Anything half-done, and where

## 11. How to reproduce this phase's outputs

Exact commands, in order, from a clean checkout plus the raw data cache.

## 12. Handoff to the next phase

What the next phase can rely on; what it must watch out for; the first three things to do.
