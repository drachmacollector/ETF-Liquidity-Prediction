# Manual Interventions: Index

Most of the project runs autonomously. These are the steps that need **you**: creating accounts, accepting terms, downloading files a website will not serve to scripts, or making decisions that are yours to make. Each has a dedicated step-by-step guide. Live status is tracked in [`records/MANUAL_ACTIONS.md`](../../records/MANUAL_ACTIONS.md); the agent will tell you in the session when one is needed.

**Two rules that apply to all of them**

1. **Never paste passwords or API keys into the chat.** Put keys in the `.env` file in the repository root (the agent will create it from `.env.example` in P00). The agent only checks that the key is set and works.
2. **Files you download go into `data/manual_drop/<folder named in the guide>/`**, with the file names the guide asks for. The agent finds and logs them from there.

| ID | What | When (phase) | Required? | Your time |
|---|---|---|---|---|
| [MI-01](MI-01_Commit_Policy_and_GitHub_Remote.md) | Decide the commit policy; optionally create a private GitHub repository | P00 | Decision required; GitHub optional | 5–15 min |
| [MI-02](MI-02_Tiingo_API_Key.md) | Create a free Tiingo account and add the API key | P01 (before P04) | Required unless you choose a fallback price source | 10 min |
| [MI-03](MI-03_FRED_API_Key.md) | Create a free FRED API key | P01/P06 | Optional (CSV downloads work without it) | 5 min |
| [MI-04](MI-04_Manual_US_Issuer_Downloads.md) | Download US ETF NAV/shares history files from issuer websites | P01/P04 | Conditional: only for sources that block scripts | 15–60 min |
| [MI-05](MI-05_Manual_India_Data_Downloads.md) | Download Indian domestic gold/silver spot history (and NSE files if blocked) | P01/P05 | Conditional (likely for MCX/IBJA) | 20–60 min |
| [MI-06](MI-06_WRDS_CRSP_Access_Check.md) | Check whether your institution offers WRDS/CRSP | P01 | Optional (upgrade) | 15 min + library response time |
| [MI-07](MI-07_Data_Terms_of_Use_Acceptance.md) | Read the terms-of-use summary and accept research-only use | P01 | Required | 15–20 min |
| [MI-08](MI-08_Incident_Catalogue_Review.md) | Review the incident catalogue's mechanism labels and key dates | P03 | Required | 45–90 min |
| [MI-09](MI-09_India_Duty_and_Regulatory_Fact_Verification.md) | Verify India import-duty rows and band-regime facts the agent could not confirm | P02 | Required for rows the agent flags | 20–60 min |
| [MI-10](MI-10_Stakeholder_Validation_Conversation.md) | Optional conversation with the Mirae Asset ETF team on lead time and alert budget | P11 | Optional, recommended | 30 min call + 15 min notes |
| [MI-11](MI-11_Preregistration_Signoff_and_Lockbox_Authorisation.md) | Read and sign the pre-registration; authorise opening the lockbox | End of P13 | Required | 30–45 min |
| [MI-12](MI-12_Final_Review_and_Optional_Hosting.md) | Review the brief wording and final report; optionally host the dashboard | P16/P17 | Review required; hosting optional | 45–90 min |

If the agent discovers a new manual step during the build, it writes a new guide from [`docs/process/templates/MANUAL_INTERVENTION_TEMPLATE.md`](../process/templates/MANUAL_INTERVENTION_TEMPLATE.md) and adds it here with the next free number.
