# MI-01 — Commit Policy and (Optional) Private GitHub Remote

| Field | Value |
|---|---|
| Needed by phase | P00 (decision recorded as D-003 before P01 completes) |
| Required or optional | **Decision: required.** GitHub remote: optional |
| Estimated user time | 5 minutes (decision only) / 15 minutes (with GitHub) |
| What you will need | A GitHub account (only for the optional part) |

## Why this needs you

Claude Code does not commit or push to your repository unless you allow it. The project's workflow (phase gates, forward-test log) works best with regular commits, so you decide once, up front, what is allowed.

## Step 1 — Choose a commit policy

Reply to the agent with one of these (copy the line):

- **A (recommended):** "Commit at the end of each verified phase and at the end of working sessions when the work is consistent. Never push without asking."
- **B:** "Commit at the end of each verified phase only. Never push."
- **C:** "Never commit; I will commit myself." (The agent will leave changes in the working tree and remind you at each phase gate.)
- **D:** As A, plus "push to the private GitHub remote after each verified phase" (requires Step 2).

The agent records your choice verbatim as decision D-003 in `records/DECISIONS.md`.

## Step 2 (optional) — Create a private GitHub repository

Why it helps: an off-machine backup, and (for the optional forward-test log in P16) commit timestamps on GitHub are independent evidence that predictions were made before outcomes.

1. Go to https://github.com/new while signed in.
2. Repository name: e.g., `etf-stress-ews`. **Visibility: Private.** Do **not** add a README, .gitignore or licence (the repository already has files).
3. Click **Create repository**. Copy the HTTPS URL shown (e.g., `https://github.com/<you>/etf-stress-ews.git`).
4. Make sure the GitHub CLI is logged in on your machine: open a terminal and run `gh auth status`. If it says you are not logged in, run `gh auth login`, choose **GitHub.com → HTTPS → Login with a web browser**, and follow the prompts.
5. Give the agent the repository URL (the URL is not a secret).

## How to check it worked (you)

- After the agent adds the remote and pushes (only under policy D), the repository page on GitHub shows the project files, and `data/raw/`, `.env` and `.venv/` are **not** there.

## What the agent does next

1. Records D-003.
2. If a remote was provided: `git remote add origin <url>`; confirms `.gitignore` excludes data and secrets; under policy D pushes `main` after the next verified phase.
3. Updates `records/MANUAL_ACTIONS.md` → VERIFIED.

## If something goes wrong

| Problem | What to do |
|---|---|
| `gh auth login` fails behind a proxy | Skip GitHub; choose policy A or B; the project works fully offline |
| You pushed a secret by mistake | Tell the agent immediately; rotate the key at the provider; the agent will help remove it from history |
