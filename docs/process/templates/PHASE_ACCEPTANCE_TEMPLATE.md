# PXX Acceptance Report — <Phase title>

| Field | Value |
|---|---|
| Phase | PXX |
| Prepared by / date | <executing agent>, <date> |
| Verified by / date | <orchestrator or fresh session>, <date> |
| Git commit evaluated | <hash> |
| Overall result | PASS / PASS WITH WAIVERS / FAIL |

## 1. Test suite

| Command | Result | Evidence |
|---|---|---|
| `pytest -q` | <n passed, n skipped, 0 failed> | log excerpt |
| `pytest tests/acceptance/test_pXX_acceptance.py -q` | | |
| `ruff check .` / `ruff format --check .` | | |

## 2. Acceptance criteria

| ID | Criterion (from phase doc) | Result (PASS/FAIL/WAIVED) | Evidence (paths, numbers, run IDs) | Decision ID if waived |
|---|---|---|---|---|
| AC-XX.1 | | | | |

## 3. Deliverables present

| Deliverable (from phase doc §5) | Path | Present |
|---|---|---|

## 4. Global Definition of Done (System Specification §14)

- [ ] 1 Deliverables exist
- [ ] 2 Tests and lint pass
- [ ] 3 All criteria evaluated
- [ ] 4 Acceptance report and walkthrough written
- [ ] 5 Records updated (STATUS, PROGRESS_LOG, DECISIONS, ISSUES, OPEN_QUESTIONS, MANUAL_ACTIONS)
- [ ] 6 Required MIs DONE/VERIFIED
- [ ] 7 Committed under D-003 policy

## 5. Orchestrator verification checklist (from phase doc §8)

| Check | Result | Notes |
|---|---|---|

## 6. Defects found during verification

| Defect | Issue ID | Fixed? |
|---|---|---|

## 7. Sign-off

- Executing agent: <name/date>
- Orchestrator: <name/date>
- User (only where the phase requires it): <name/date>
