# ASAP Pressure Clean — Lead & Campaign CRM

Single-file HTML CRM for tracking email outreach campaigns from `asappressurecleaning@gmail.com`.

**Live URL:** https://joshuaabbottr.github.io/asap-crm/

## Features
- 182 leads seeded from Gmail outreach (Apr 21–22, 2026)
- 2 campaigns, pipeline funnel, KPI cards
- Bounces, auto-replies, and real replies tracked
- All data persists in the browser via `localStorage`
- Export/Import JSON for backups and cross-device sync

## Updating

### Manual edit
Edit `index.html` locally, commit, and push to `main` — GitHub Pages auto-rebuilds.

### One-click refresh from Gmail
The "Refresh from Gmail" button in the UI opens the **Refresh CRM from Gmail** workflow on GitHub Actions. Click "Run workflow" → "Run workflow". The workflow:

1. Calls Composio's API to query the `asappressurecleaning@gmail.com` sent folder + inbox
2. Reconciles bounces, replies, and auto-replies against the sent leads
3. Regenerates the lead array inside `index.html`
4. Commits the change — Pages redeploys ~30 sec later

**One-time setup (required before the workflow can run):**

1. Get your Composio API key from [app.composio.dev/settings](https://app.composio.dev/settings)
2. In this repo, go to **Settings → Secrets and variables → Actions → New repository secret**
3. Add:
   - `COMPOSIO_API_KEY` — value: your API key
   - `COMPOSIO_GMAIL_ACCOUNT_ID` — value: `gmail_anat-leon` (the connected-account ID for the ASAP mailbox)

To enable a daily auto-refresh, uncomment the `schedule:` block in `.github/workflows/refresh.yml`.
