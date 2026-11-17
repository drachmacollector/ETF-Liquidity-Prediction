# P09: Labels — Dislocation Episodes and Targets

| Field | Value |
|---|---|
| Phase ID | P09 |
| Depends on | P08 |
| Can run in parallel with | P10 (P10 must not use labels) |
| Unlocks | P11 |
| Estimated effort | 2–3 days |
| Manual interventions | None planned. If the event-count gate fails, a user decision is required (logged) |
| Canonical references | System Specification §4.5–4.8, §4.10, §4.13; Research Document §11.3 |

## 1. Purpose

Implement the label definitions exactly as specified, identify every dislocation episode in both markets, produce the primary target and the secondary labels, link episodes to catalogued incidents and operational events, and **count events** to confirm that the evaluation has enough statistical power before any model is trained.

## 2. Scope

**In scope:** `esw.labels` module (isolated); dislocation days; episodes with freeze and structural absorption; timing-suspect flags; primary target (H = 5) and sensitivity targets (H = 1, 3); secondary labels; label sensitivity variants needed later (the grid in System Specification §4.13); episode–incident linking; the label card; the event-count gate.

**Out of scope:** features; models.

## 3. Prerequisites

- [ ] P08 `VERIFIED`.

## 4. Implementation specification

### T09.1 Module isolation

- `src/esw/labels/` may import `esw.config`, `esw.paths`, `esw.runlog`, `esw.reference`, pandas/numpy. It reads `pricing_panel.parquet` columns `instrument_id, date, valid, prem_bps, close, nav` and the next-day NAV for the timing check.
- It **recomputes** baseline and scale itself with the episode-aware rules (System Specification §4.5–4.6). It must not import `esw.pricing.panel` functions for baseline/scale (copying formulas is intended; the duplication is a guard against coupling).
- An import-guard test (`tests/unit/test_import_guards.py`) fails if `esw.features` imports `esw.labels` or vice versa.

### T09.2 Algorithm (per instrument, chronological single pass)

```
state: frozen = None (or (b, s, freeze_start))
for t in trading days of instrument:
    if not valid[t]:  DD[t] = 0 (and mark invalid); continue   # invalid days neither start nor extend (but a single invalid day
                                                               # inside a run counts against GAP_BRIDGE)
    if frozen and (t − freeze_start) ≥ FREEZE_MAX:  mark current episode structural; frozen = None
    b, s = frozen[:2] if frozen else rolling_baseline_scale(eligible history strictly before t)
            # eligible history = valid rows not inside any (non-structural) episode window found so far
    if s undefined: DD[t] = 0; continue
    dev = prem[t] − b ; thr = max(ABS_FLOOR_BPS, K_MULT × s)
    DD[t] = |dev| ≥ thr ; sign[t] = sign(dev)
    run-tracking: extend/close candidate runs with GAP_BRIDGE and sign rules;
    when a candidate run reaches PERSIST_MIN DD days → it is an episode; set frozen = (b_at_onset, s_at_onset, onset)
       (b_at_onset, s_at_onset are the values computed for the onset day, i.e., from pre-onset data)
    when an episode ends (gap > GAP_BRIDGE or sign flip) → frozen = None; record episode
```

Implementation note: because an episode is only confirmed after `PERSIST_MIN` days, the freeze is applied retroactively from the onset for baseline purposes (the first `PERSIST_MIN − 1` days of a run already used the pre-onset baseline, so retroactive freezing changes nothing for them). Write the code so this equivalence is explicit and tested.

### T09.3 Outputs

1. `data/derived/labels/daily_labels.parquet`: `instrument_id, date, valid, b_lab_bps, s_lab_bps, dev_lab_bps, thr_bps, DD, sign, in_episode, episode_id, eligible, y, y_h1, y_h3, cooldown, label_window_complete`.
2. `data/derived/labels/episodes.parquet`: `episode_id, instrument_id, group, market, onset, end, n_days, n_dd_days, direction, peak_dev_bps, peak_prem_bps, peak_date, structural, timing_suspect, incident_id (linked), op_event_ids (linked), sec_trigger_date, sebi_trigger_date`.
3. `data/derived/labels/secondary_triggers.parquet`: `instrument_id, trigger_type (sec|sebi|noquote|op_event), trigger_date, related_episode_id`.
4. Sensitivity variants: `data/derived/labels/variants/<variant_id>/{daily_labels,episodes}.parquet` for each grid point in System Specification §4.13 (the grid is computed now so P14 can use it without touching label code again).

### T09.4 Timing-suspect check

For each episode: compute `fprem` (System Specification §4.10) for its DD days; `timing_suspect = true` if for ≥ 50% of DD days `|fprem − b_lab| < thr`. Report the share of timing-suspect episodes by group (expected high for GLD/SLV and international ETFs, low for USO 2020 and UNG 2009).

### T09.5 Linking to the catalogue

- An episode links to an incident if the instrument is in the incident's `instrument_ids` and the episode onset lies within `[approx_onset − 10, approx_end + 10]` trading days.
- An episode links to operational events of the same instrument (or issuer/industry scope) with `effective_at` within `[onset − 20, end + 5]` trading days.
- Report: incidents with no matching episode (why? e.g., no NAV data; not a dislocation by our definition; near-miss — expected for SLV 2021), episodes in incident windows, and the largest unlinked episodes (candidates for catalogue additions; adding them requires the P03 protocol and is logged).
- Refine `analogue_anchor_date` in `reference/incidents.csv` to `onset − 1` of the matched episode (logged change).

### T09.6 Event-count gate

Compute onset counts by period and group: development (US, onset ≤ `DEV_END`), lockbox (US, onset ≥ `LOCKBOX_START`), India (all). Also count *effective clusters* (onsets grouped by calendar month across instruments).

| Gate | Threshold |
|---|---|
| US development onsets | ≥ 40, from ≥ 3 groups and ≥ 6 distinct calendar years |
| US lockbox onsets | ≥ 20 |
| India onsets | Reported (no minimum; case studies cover the rest) |
| Positive rate of `y` (US dev eligible rows) | Reported; expected 0.2–3% |

**If the gate fails:** do not train anything. Prepare a decision memo with options: (a) widen the universe (return to P01/P04 for more instruments); (b) adopt a different pre-specified grid point (e.g., `ABS_FLOOR_BPS = 150`) — chosen **only** on counts, never on any predictive analysis; (c) accept lower power and say so. The user decides; the choice is logged and then frozen in P11.

### T09.7 Label card

`reports/labels/label_card.md`: definitions with parameter values; counts tables; distribution of episode length, peak size and direction by group; timing-suspect shares; structural episodes (expected: Indian international ETFs; RSX if data); top 20 episodes by peak; linkage results; known limitations.

### T09.8 Commands

`esw build labels [--variant default|all]`.

## 5. Deliverables

| Path | Description |
|---|---|
| `src/esw/labels/{episodes,targets,secondary,linking}.py` | Code |
| `data/derived/labels/*.parquet`, `data/derived/labels/variants/**` | Labels |
| `reports/labels/label_card.md` (+ figures), `reports/labels/event_counts.csv` | Reports |
| Tests: `tests/unit/test_episodes_synthetic.py`, `tests/unit/test_targets.py`, `tests/unit/test_import_guards.py`, `tests/acceptance/test_p09_acceptance.py` | Passing |

## 6. Tests and validation

Synthetic-path unit tests (each a tiny hand-made premium series with known answers):

1. A single spike of 1 day above threshold → no episode.
2. Three consecutive days above threshold → one episode, onset day 1.
3. Two days above, one day below, two days above (same sign) → one episode (gap bridged).
4. Same with a sign flip → no merged episode.
5. A level shift lasting 100 days → episode marked `structural`, ends after absorption; days after absorption are eligible again.
6. `y` = 1 on the five days before onset, null inside the episode and cooldown, 0 elsewhere when the window is complete.
7. Calm series with s = 2 bps (SPY-like): threshold = 200 bps floor, no episodes from noise.
8. Volatile series with s = 120 bps: threshold = 360 bps.
9. Timing-suspect: a premium that is fully explained by next-day NAV → `timing_suspect = true`.

Acceptance checks: the episodes for USO April 2020, UNG Jul–Sep 2009 and LQD March 2020 exist with onsets within the expected windows; event-count gate evaluated.

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-09.1 | All synthetic tests pass; import-guard test passes |
| AC-09.2 | Labels, episodes, secondary triggers and all sensitivity variants produced for both markets |
| AC-09.3 | USO 2020, UNG 2009 and LQD 2020 episodes detected (onset within ±10 trading days of the documented start) |
| AC-09.4 | Event-count gate evaluated; passed, or user decision recorded and the chosen alternative implemented |
| AC-09.5 | Linking report produced; unmatched incidents explained |
| AC-09.6 | Label card produced |

## 8. Verification checklist (orchestrator)

- [ ] Read the event-count table and confirm the gate decision.
- [ ] Inspect three random episodes from different groups on a premium plot; confirm the onset is the first threshold-crossing day of a persistent run.
- [ ] Confirm that no file in `esw/features` imports `esw.labels`.

## 9. Risks and decision points

| Item | Handling |
|---|---|
| Too many timing-suspect episodes in GLD/SLV | Expected; reported; robustness evaluation removes them in P14 |
| Structural episodes dominate India | Expected for international ETFs; absorption rule handles it; reported |
| Temptation to tune label parameters for "nicer" counts | Forbidden except through the T09.6 gate procedure |

## 10. Walkthrough requirements

Record: final counts; gate outcome; notable episodes found that were not in the catalogue; timing-suspect shares; any deviation from the algorithm and why.

## 11. Handoff

P11 uses `daily_labels.parquet` and `episodes.parquet` to build folds, baselines and the pre-registration.
