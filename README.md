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

### Refresh from Gmail
Click the **"↻ Refresh from Gmail"** button in the header. It opens a modal with a copy-able prompt — paste it into Claude Code chat. Claude queries Gmail via Composio, regenerates the lead list, and pushes to GitHub. Pages redeploys ~30 sec later.
