# Provider setup

The default adapters use read-only endpoints:

- DEX Screener market/pair and profile discovery: no key configured.
- GeckoTerminal pool discovery: no key configured.
- Jupiter Tokens v2 search: the project uses the lite public base by default. If your access tier requires a key, create one through the official Jupiter developer portal and place it after `JUPITER_API_KEY=`.
- Solana RPC: the public mainnet URL works for light testing but is rate-limited. For production obtain a dedicated read-only RPC HTTPS URL from a reputable Solana RPC provider and replace `SOLANA_RPC_URL=`.
- RugCheck: optional because availability and public-access rules can change. Disable `optional_rugcheck_enabled` in `config.json` if unavailable. Never replace it with an undocumented scraper.

API availability and free tiers change. Verify the official provider documentation during installation. No provider needs wallet permissions. Never put a seed phrase or private key in `.env`.
