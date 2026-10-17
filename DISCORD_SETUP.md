# Discord setup

1. Create category `⛓️｜ON-CHAIN RADAR`.
2. Inside it create `🔎｜onchain-command-center`, `🚨｜onchain-radar-alerts`, and `📊｜onchain-trending-board`.
3. In the [Discord Developer Portal](https://discord.com/developers/applications), create an application named Fortune On-Chain Radar, open Bot, create/reset its token, and keep it private.
4. No privileged intents are required. Leave Message Content and Server Members intents off.
5. OAuth2 → URL Generator: select `bot` and `applications.commands`. Bot permissions: View Channels, Send Messages, Embed Links, Read Message History. Do not grant Administrator, Manage Server, or Mention Everyone.
6. Invite it. Give the bot those permissions in the three new channels only.
7. Enable Discord Developer Mode. Right-click the server and each new channel → Copy ID. Right-click your administrator role → Copy ID.
8. Paste IDs into the matching `.env` lines. The optional alert role is blank by default and the bot never uses `@everyone`.
