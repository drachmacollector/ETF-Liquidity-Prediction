# MI-XX — <Short title>

| Field | Value |
|---|---|
| Needed by phase | PXX (blocks: <tasks>) |
| Required or optional | Required / Optional / Conditional (only if …) |
| Estimated user time | <minutes> |
| What you will need | <account, browser, institution login, …> |
| Status tracker | `records/MANUAL_ACTIONS.md` row MI-XX |

## Why this needs you

One or two sentences: why the agent cannot do it (account creation, licence acceptance, credentials, judgment call).

## Step-by-step

1. Go to <exact URL>.
2. Click <exact button/menu>; choose <exact option>.
3. …

## What to give the agent

- Files: put them in `<exact folder>` named `<exact pattern>`.
- Secrets: add `<VAR_NAME>=<value>` to the `.env` file in the repository root (never paste secrets in chat).
- Decisions: reply with <exact choice format>.

## How to check it worked (you)

- <observable result, e.g., "the file is ~200 KB and opens in Excel with a Date column starting in 2006">

## What the agent does next

1. Verification steps (commands, checks).
2. Status update in `records/MANUAL_ACTIONS.md` → VERIFIED.
3. Which task resumes.

## If something goes wrong

| Problem | What to do |
|---|---|
