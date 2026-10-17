# Solana Token Risk Radar

A read-only Discord research bot for **Solana tokens**. It discovers new and trending tokens, pulls market and safety data from several independent on-chain and DEX data providers, and computes an **explainable, conservative risk score** — showing exactly which checks passed, which failed, and which data was missing. It never connects to wallets or trades.

Built for the Fortune & Finance trading-education community.

## The problem it solves

Newly launched Solana tokens move fast, and many are traps: unlimited mint authority, freeze authority, honeypot transfer restrictions, a handful of wallets holding most of the supply, or bundled launches. Checking each token by hand across five websites takes minutes per coin. This bot automates that research and is honest about uncertainty: missing data lowers the score and confidence instead of being ignored, and any single hard blocker disqualifies a token regardless of its other numbers.

## Key features

- **Multi-provider data aggregation**
  - DEX Screener and GeckoTerminal for discovery, pools, liquidity, volume, and transactions
  - Jupiter for token metadata and risk flags
  - RugCheck (optional) for token risk reports
  - Solana JSON-RPC for on-chain holder data
- **Best-pool selection** by liquidity, volume, and activity.
- **Conservative risk merge** — if any provider reports a danger flag, it is kept.
- **Explainable 0–100 score with letter grade**: 17 checks covering age, liquidity, 1-hour volume and transactions, buy ratio, FDV/liquidity, price extension, mint/freeze authority, transfer restrictions, honeypot and suspicious flags, top-10 holder, developer, insider, and bundled-launch concentration.
- **Confidence rating** (LOW / MEDIUM / HIGH) based on data coverage and number of independent sources; missing data applies a score penalty.
- **Hard blockers** that always prevent an alert (e.g. mint authority enabled, extreme holder concentration).
- **Paid promotion is ignored**: paid boosts/profile visibility contribute nothing to the score.
- **Provider health tracking** with response caching, stale-cache fallback (marked degraded), and rate-limit detection.
- **Alert controls**: dry-run mode, idempotent alerts (no duplicates), per-token cooldown, daily alert budget, and a trending dashboard that edits one message in place.
- Slash commands: `/coin`, `/holders`, `/developer`, `/trending`, `/watch`, `/unwatch`, `/watchlist`, `/radar_status`, `/radar_scan`.

## Technologies

- **Python 3.11+**, `asyncio`
- **discord.py** (slash commands, embeds)
- **aiohttp** for REST and JSON-RPC providers
- **SQLite** (watchlist, alerts, score history, provider health, settings, audit; with migrations)
- Docker / docker-compose
- `unittest` test suite with recorded JSON fixtures for each provider

## How it works

```text
Discovery (DEX Screener, GeckoTerminal)
        │
        ▼
Pool selection ─► Risk enrichment (Jupiter, RugCheck, Solana RPC) ─► merge_risks()
        │
        ▼
score(): 17 checks → points, blockers, warnings, missing data
        │
        ▼
_finish(): missing-data penalty → score/grade → confidence → qualified?
        │
        ▼
Dry-run log  or  Discord alert (cooldown + daily budget + idempotency key)
```

```text
fortune_radar/
├─ providers/       base (cache, retries, health), dexscreener, geckoterminal, jupiter, rugcheck, solana
├─ scoring.py       best-pool selection, conservative risk merge, score/grade/confidence
├─ research.py      orchestrates providers for one token
├─ database.py      SQLite persistence and migrations
├─ presentation.py  Discord embeds within Discord size limits
├─ validation.py    contract address and config validation
└─ bot.py           slash commands, scheduled scans, dashboard
```

All scoring math lives in `fortune_radar/scoring.py` so it can be audited in one place.

## Local setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env              # Discord token, channel IDs, optional RPC/API keys
Copy-Item config.example.json config.json
python run.py
```

Start with `"dry_run": true` in `config.json`. Guides included: `DISCORD_SETUP.md`, `API_PROVIDER_SETUP.md`, `WINDOWS_INSTALL.md`, `DIGITALOCEAN_DEPLOYMENT.md`, `BACKUP_RESTORE.md`, `SECURITY.md`, `TROUBLESHOOTING.md`.

## Testing and current status

```powershell
python -m unittest discover -s tests -v
```

**Verified (October 2026):** 36 tests pass (Python 3.12). They cover every provider parser against recorded fixtures, each score filter and hard blocker, missing-data confidence, conservative risk merging, provider caching and rate-limit health, alert de-duplication, cooldown, daily budget, migrations, slash-command registration, and Discord embed size limits.

**Previously recorded (August 2026, see `LIVE_CONNECTIVITY_RESULTS.md`):** DEX Screener, GeckoTerminal, Jupiter, and RugCheck responded and parsed successfully; the public Solana RPC endpoint failed after retries, so a dedicated RPC URL is recommended. Live provider calls and a live Discord run were **not** re-executed during this review.

## Business application

- Automated due-diligence screening for crypto/Web3 communities, research teams, and token-listing reviews.
- Demonstrates a reusable pattern for **combining several unreliable third-party APIs** into one decision with explicit confidence — useful anywhere data quality varies by source (KYC, lead enrichment, vendor risk).

## Development approach

Built by George ([@FortuneGroot](https://github.com/FortuneGroot)) using AI-assisted development (OpenAI Codex and other AI coding tools). George specified the research checklist, which red flags are hard blockers, how missing data should be penalized, and the alert-safety rules, based on his experience in crypto trading communities. He directed the implementation and validated it with fixture-based tests and live connectivity probes. The AI tools generated much of the code under that direction.

## Disclaimer

Research aid only. A high score is not a recommendation to buy, and no automated check can detect every scam.

## License

Copyright © 2026 George (FortuneGroot). All rights reserved. This code is published for portfolio review; contact me before reusing it.
