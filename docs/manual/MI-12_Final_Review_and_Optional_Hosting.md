# MI-12 — Brief Wording Review, Final Report Sign-off, Optional Dashboard Hosting

| Field | Value |
|---|---|
| Needed by phase | P16 (brief wording, routing text); P17 (final report and summary sign-off) |
| Required or optional | Review: required. Hosting: optional |
| Estimated user time | 45–90 minutes (review); 20 minutes (hosting) |

## Part A — Brief wording review (P16)

1. Open the sample briefs in `outputs/samples/` (HTML in a browser).
2. Read them as a Mirae ETF product, sales or compliance reader would. Check: Is anything worded like advice ("buy", "sell", "avoid")? Is anything unclear? Is the Mirae products box correct?
3. Open `config/routing.yaml` and check the "who acts" texts.
4. Decide whether to show Mirae branding (logo files are archived in `archive/v0_early_drafts/old docs/`). Default: plain text only. Using the logo in anything shared outside Mirae is not advisable without permission.
5. Reply with "Wording approved" or a list of edits.

## Part B — Optional dashboard hosting

Hosting makes the dashboard viewable by link. It requires the repository on GitHub (MI-01, Step 2) and a free Streamlit Community Cloud account. **Hosted apps can expose data**; only host if the app runs on derived, non-redistributable-safe outputs (the agent prepares a "demo data" bundle of aggregated predictions without raw vendor data) and you are comfortable with the visibility settings.

1. Go to https://share.streamlit.io and sign in with GitHub.
2. Click **Create app** → choose the repository, branch `main`, main file `app/streamlit_app.py`.
3. Under advanced settings, set Python version 3.11 and keep the app **private** if the option is available for your account; otherwise do not share the link widely.
4. Deploy; share the URL with the agent so it can be added to the report.

## Part C — Final report and summary sign-off (P17)

1. Read `reports/final/ETF_Stress_EWS_Summary_2page.md` (the pitch artefact) and skim the technical report.
2. Check that the summary's claims match the report, that negative results are stated plainly, and that the tone suits the Mirae Asset audience.
3. Reply "Final report approved" or list edits.

## What the agent does next

Applies edits, re-runs the banned-word scan and traceability check, records approvals in `records/DECISIONS.md`, marks MI-12 VERIFIED, and completes the P17 readiness checklist.
