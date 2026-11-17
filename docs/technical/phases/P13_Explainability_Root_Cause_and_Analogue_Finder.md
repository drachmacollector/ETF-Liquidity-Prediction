# P13: Explainability — Root-Cause Tags, Reason Codes and Analogue Finder

| Field | Value |
|---|---|
| Phase ID | P13 |
| Depends on | P12 (frozen models), P03 (catalogue) |
| Unlocks | P14 (after MI-11), P16 |
| Estimated effort | 3–4 days |
| Manual interventions | **MI-11** (pre-registration sign-off and lockbox authorisation) is requested at the end of this phase |
| Canonical references | System Specification §4.14 (families), §10.1 (output columns); Research Document §3, §11.5 |

## 1. Purpose

Turn model outputs into explanations a product, sales or compliance team can act on: a **root-cause tag** (which part of the arbitrage pipe is under strain), up to three **reason codes** in plain language with the underlying values, and the **closest past incident**. Validate tags and analogues against the hand-labelled catalogue on development-period incidents, then freeze the rules so they can be tested out of sample in P14/P15.

## 2. Scope

**In scope:** TreeSHAP computation; family aggregation; tag rule; reason templates; analogue library and retrieval; development-period validation; freezing rules into Part B (appendix); MI-11 request.

**Out of scope:** any lockbox or India evaluation (P14/P15).

## 3. Prerequisites

- [ ] P12 `VERIFIED`; Part B hash recorded.
- [ ] `reference/incidents.csv` reviewed (MI-08 DONE).

## 4. Implementation specification

### T13.1 SHAP computation

- TreeSHAP (`shap.TreeExplainer`) on each fold's **uncalibrated** booster, output in log-odds. Calibration is monotone, so the ordering of contributions is preserved; the explanation describes the raw score.
- Computed for every eligible prediction row in the development OOF set (and later for lockbox/India/daily rows with the corresponding fold model).
- Stored as `data/derived/explain/shap_<model>_<period>.parquet` (feature-level) and `family_shap_<model>_<period>.parquet` (summed by family: `GAP, CRE, STL, UND, LIQ, DEM, MKT, CAL, CTX`).

### T13.2 Root-cause tag rule (frozen at the end of this phase)

For a prediction row:

1. Consider mechanism families `M = {CRE, STL, UND, LIQ, DEM, MKT}` (not `GAP`, `CAL`, `CTX`).
2. Positive contributions only: `c_f = max(0, family_shap_f)`.
3. If `Σ c_f = 0` → tag `UNSPECIFIED`.
4. Else `root_cause_tag = argmax_f c_f`; `root_cause_share = c_max / Σ c_f`; `secondary_tag` = second-largest family if its share ≥ 0.25.
5. `gap_share` = `max(0, GAP) / (max(0, GAP) + Σ c_f)` is shown separately ("of which gap already building: x%").

The tag for an **episode** (used in validation) is the tag of the eligible prediction with the highest `p` in `[onset − H, onset − 1]`; if no eligible prediction exists in that window, the episode is "untaggable" and reported separately.

### T13.3 Reason codes

- A template per feature ID in `src/esw/explain/templates.yaml`, e.g.:
  - `f2_so_chg20_z`: "Units outstanding grew {f2_so_chg20:.1%} in 20 days, {value:.1f} standard deviations above normal"
  - `f2_prem_no_creation5`: "On {value:.0f} of the last 5 days the ETF traded above its normal band without new units being created"
  - `f6_lp_med5`: "Domestic {metal} is {value:.0f} bps above import parity (5-day median)"
  - `f5_unsched_closure_active`: "The underlying market has been closed since {event_date}"
  - `f4_edge_spread21_z`: "Estimated bid–ask spread is {value:.1f} standard deviations above its one-year norm"
  - `f7_peer_share_absz_gt2`: "{value:.0%} of same-category peers are also trading unusually far from NAV"
- Top 3 features by positive SHAP, excluding `CTX` and `CAL`, become `top_reasons` (JSON list of `{feature_id, family, text, value, shap}`).
- Language rules: descriptive only; no advice verbs. A test scans all templates for banned words (`buy`, `sell`, `recommend`, `should invest`, `guarantee`, `profit`, `target`).

### T13.4 Analogue library and retrieval

- **Library entries:** for each catalogue incident with `include_in_validation = y` and a matched data episode (P09), the signature at `analogue_anchor_date`: the mean of standardised family-SHAP vectors over `[anchor − 4, anchor]` for families `GAP, CRE, STL, UND, LIQ, DEM, MKT` (standardisation: divide by each family's standard deviation of SHAP over the development OOF set), plus `direction` (+1 premium, −1 discount) and `asset_class`.
- **Query signature:** the same construction for the current `(i, t)` over `[t − 4, t]`.
- **Distance:** cosine distance between family vectors + 0.5 if directions differ + 0.25 if asset classes differ.
- **Point-in-time constraint:** a library entry is eligible for a query at `t` only if the incident's `first_public_known_at < τ(t)` and its anchor date < `t`, and it is not the same instrument's episode overlapping `t`.
- **Output:** nearest eligible entry → `analogue_incident_id`, `analogue_name`, `analogue_distance`; plus the second-nearest for the dashboard.
- Library signatures are computed with the model of the fold that covers the anchor date (development folds for dev incidents; lockbox folds in P14).

### T13.5 Development-period validation

On development incidents (`in_dev_period = y`, `include_in_validation = y`, matched episode exists):

1. **Tag agreement:** top-1 agreement between episode tag and catalogue `primary_family`; confusion matrix; compare with (a) majority-class rate, (b) a rule-based tagger baseline (assigns the family whose own key indicator has the largest z-score: CRE ← `f2_so_chg20_z` or `f3_constraint_active`, STL ← `f5_absdiv_mean5_z`, UND ← `f6_und_rv20_z`/`f6_lp_z`, LIQ ← `f4_edge_spread21_z`, DEM ← `f7_turnover_surge5` z, MKT ← `f8_global_vix_z`). One-sided binomial test vs majority class.
2. **Analogue agreement:** leave-one-incident-out retrieval among earlier incidents (point-in-time constraint applied); share whose analogue has the same primary family; compare with a random-retrieval baseline (expected agreement given the family mix of eligible earlier incidents).
3. **Qualitative review:** for 5 well-known dev incidents (UNG 2009, EGPT 2011, GREK 2015, taper 2013, a 2008 bond case), a table of the tag, reasons and analogue at the anchor date, with a short critique.

Report in `reports/explain/explain_dev_report.md`. With few development incidents the tests will have low power; report counts and do not over-interpret.

### T13.6 Freeze and MI-11 request

1. Append an "Explainability rules" appendix to `config/pre_registration.md` (tag rule, thresholds 0.25/0.5/0.25 above, templates file hash, library construction) and record the new hash (D-P13-PREREG-EXPL).
2. Prepare `records/acceptance/MI-11_lockbox_request.md`: summary of Part A, Part B, the explainability appendix, hashes, and a checklist for the user (MI-11 guide).
3. Set P14 status to `BLOCKED_ON_USER` until MI-11 is DONE.

## 5. Deliverables

| Path | Description |
|---|---|
| `src/esw/explain/{shap_calc,families,tags,reasons,analogues,validate}.py`, `templates.yaml` | Code |
| `data/derived/explain/*.parquet` | SHAP outputs (dev) |
| `reference/analogue_library_dev.parquet` (generated; not hand-edited) | Library |
| `reports/explain/explain_dev_report.md` | Validation |
| Updated `config/pre_registration.md` + hash | Freeze |
| `records/acceptance/MI-11_lockbox_request.md` | Request to the user |
| Tests: `tests/unit/test_tags.py`, `tests/unit/test_reasons_templates.py`, `tests/unit/test_analogue_pit.py`, `tests/acceptance/test_p13_acceptance.py` | Passing |

## 6. Tests and validation

- Tag rule on synthetic SHAP vectors (ties, all negative, secondary threshold).
- Templates render for every feature they reference; banned-word scan.
- Analogue point-in-time test: an incident first known after `τ(t)` is never returned.
- SHAP additivity check: sum of SHAP + expected value equals the raw score (tolerance 1e-6) on a sample.

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-13.1 | SHAP, tags, reasons and analogues produced for all development OOF eligible rows |
| AC-13.2 | Development validation report with agreement rates, baselines, counts and qualitative review |
| AC-13.3 | Rules frozen into the pre-registration appendix; hash recorded |
| AC-13.4 | Tests pass (including point-in-time analogue test and banned-word scan) |
| AC-13.5 | MI-11 request prepared and the user notified; P14 marked `BLOCKED_ON_USER` |

## 8. Verification checklist (orchestrator)

- [ ] Read the qualitative review; check that explanations are understandable without technical knowledge.
- [ ] Confirm that tags were compared with catalogue labels made in P03 (not edited afterwards; check git history of `incidents.csv`).

## 9. Risks and decision points

| Item | Handling |
|---|---|
| Tags dominated by one family (e.g., MKT) | Report; consider in limitations; do not change rules after freezing |
| Few dev incidents | Low-power validation stated; out-of-sample test in P14/P15 is the real test |

## 10. Walkthrough requirements

Record: tag distribution; agreement results; analogue examples; template changes; the frozen-rule hash; MI-11 request date.

## 11. Handoff

After MI-11 is DONE, P14 runs the frozen pipeline on the lockbox. P16 can start building the brief and dashboard in parallel using development outputs as sample data.
