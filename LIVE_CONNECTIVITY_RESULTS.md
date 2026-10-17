# Read-only live connectivity results

Probe date: 2026-08-24. No wallet, Discord, transaction, or trading action was used.

- DEX Screener: SUCCESS — token-pair response parsed; 30 pools returned for the probe contract.
- GeckoTerminal: SUCCESS — trending/new discovery responses parsed; 40 unique contracts returned.
- Jupiter Tokens v2: SUCCESS — token search/risk metadata response parsed.
- RugCheck (optional): SUCCESS — report response parsed.
- Public Solana mainnet RPC: FAILED after bounded retries in this environment. This is commonly subject to public endpoint availability/rate limits, but this result does not diagnose the external cause. Configure and test a dedicated read-only production RPC URL before enabling alerts.

These checks establish endpoint reachability and response parsing at the probe time only. They do not guarantee future availability or data correctness. Provider health is monitored continuously by the bot.
