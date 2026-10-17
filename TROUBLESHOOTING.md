# Troubleshooting

- Commands missing: verify guild ID and `applications.commands`, then restart.
- Wrong channel: correct the three channel IDs in `.env`.
- Forbidden/Missing Access: give View, Send, Embed, and History in the new channels; never solve it with Administrator.
- Provider degraded: wait for a rate limit, check `/radar_status`, RPC quota, and official provider status. The bot continues with other providers and lowers confidence.
- No alerts: dry run may be enabled, filters may fail, confidence may be insufficient, cooldown active, or daily budget exhausted. This is expected conservative behavior.
- Database locked: stop duplicate bot processes.
- Import error: rerun `SETUP_WINDOWS.bat`.
- RugCheck failure: disable its optional setting rather than scraping undocumented pages.

Never paste `.env` or secret-bearing logs into Discord or chat.
