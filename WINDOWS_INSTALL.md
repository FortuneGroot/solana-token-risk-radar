# Windows installation

1. Install 64-bit Python 3.12 from python.org and check **Add Python to PATH**.
2. Extract the ZIP to `C:\FortuneOnChainRadar`.
3. Double-click `SETUP_WINDOWS.bat` and wait for “Setup complete.”
4. Open `.env` in Notepad. Replace `paste_discord_token_here`, then replace every required `0` with the IDs from `DISCORD_SETUP.md`. Do not add quotes. Leave `ALERT_ROLE_ID` and `JUPITER_API_KEY` blank initially.
5. Save `.env`. Open `config.json` and confirm `"dry_run": true`.
6. Double-click `START_BOT.bat`. Keep the window open.
7. In command center run `/radar_status`, `/coin` using a known Solana token contract, then `/radar_scan` as an administrator.
8. Confirm the dashboard edits one message and no public alerts appear in dry run.
9. Review provider health and tune production RPC/API access before considering `dry_run: false`.

Do not enable live alerts until repeated dry-run results look correct. This bot researches tokens; it cannot establish that any coin is safe.
