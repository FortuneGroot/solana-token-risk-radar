# DigitalOcean deployment

After Windows dry-run testing succeeds, create an Ubuntu 24.04 Droplet, install Docker/Compose, upload the project with SFTP, create `.env` and `config.json`, then run:

```bash
docker compose build
docker compose up -d
docker compose logs -f fortune-radar
```

Use one container only with SQLite. Back up `./data`, restrict `.env`, use SSH keys/firewall/security updates, configure API usage limits, and keep dry run enabled during the first hosted scans.
