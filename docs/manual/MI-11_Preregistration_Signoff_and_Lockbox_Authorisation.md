# MI-11 — Pre-Registration Sign-off and Lockbox Authorisation

| Field | Value |
|---|---|
| Needed by phase | End of P13; hard gate for P14 and P15 |
| Required or optional | Required |
| Estimated user time | 30–45 minutes |

## Why this needs you

The lockbox (US data from 1 Jan 2020 and all Indian data) can be used for evaluation only once. Your sign-off certifies that everything that will be judged was decided before anyone looked at those results. This is what makes the project's claims credible.

## Step-by-step

1. Open `records/acceptance/MI-11_lockbox_request.md`. It summarises what is frozen and lists the hashes.
2. Read `config/pre_registration.md`, focusing on:
   - **A6 Hypotheses and pass criteria** — are these the right questions, and are the bars fair (not too easy)?
   - **A4 Alert budgets** — acceptable for a desk?
   - **Part B thresholds** — note the WATCH/HIGH probabilities.
   - **A8 Commitments** — results are reported whatever they are.
3. Check that the development results (`reports/models/model_dev_report.md`) were produced **without** lockbox data: the report states the date ranges used.
4. If you want changes, say so now (changes after sign-off are not possible without invalidating the lockbox). The agent will revise, re-hash and ask again.
5. To authorise, reply exactly:
   ```
   MI-11: I have read the pre-registration (hash <first 12 characters>) and authorise opening the lockbox.
   ```

## What the agent does next

1. Records your sign-off verbatim in `records/DECISIONS.md` and `records/MANUAL_ACTIONS.md` (VERIFIED) and in the pre-registration's sign-off section (which is the last edit; the final hash is recomputed and recorded).
2. Commits the frozen state (if D-003 allows) or archives it with its hash.
3. Starts P14.

## If something goes wrong

If you are unsure about any hypothesis or criterion, ask the agent to explain it in plain language before signing. It is better to delay than to sign something you have not understood.
