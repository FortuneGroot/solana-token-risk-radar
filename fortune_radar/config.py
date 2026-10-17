from __future__ import annotations
import json, os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    token:str; guild_id:int; command_channel:int; alerts_channel:int; dashboard_channel:int; admin_role:int
    alert_role:int|None; rpc_url:str; jupiter_key:str; rugcheck_url:str; database_url:str; config:dict; base_dir:Path


def load_settings(base_dir:Path|None=None)->Settings:
    from dotenv import load_dotenv
    base_dir=(base_dir or Path.cwd()).resolve(); load_dotenv(base_dir/".env")
    path=base_dir/os.getenv("RADAR_CONFIG","config.json")
    if not path.exists(): path=base_dir/"config.example.json"
    cfg=json.loads(path.read_text(encoding="utf-8")); validate_config(cfg)
    def required(name):
        value=os.getenv(name,"").strip()
        if not value: raise RuntimeError(f"{name} is required in .env")
        return value
    alert=os.getenv("ALERT_ROLE_ID","").strip()
    return Settings(required("DISCORD_BOT_TOKEN"),int(required("DISCORD_GUILD_ID")),int(required("COMMAND_CENTER_CHANNEL_ID")),int(required("RADAR_ALERTS_CHANNEL_ID")),int(required("TRENDING_BOARD_CHANNEL_ID")),int(required("ADMIN_ROLE_ID")),int(alert) if alert else None,os.getenv("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com"),os.getenv("JUPITER_API_KEY",""),os.getenv("RUGCHECK_API_URL","https://api.rugcheck.xyz/v1"),os.getenv("DATABASE_URL","sqlite:///data/fortune_radar.db"),cfg,base_dir)


def validate_config(c:dict)->None:
    positive=["scan_interval_seconds","minimum_age_minutes","maximum_discovery_age_days","minimum_liquidity_usd","minimum_volume_h1_usd","minimum_transactions_h1","alert_cooldown_hours","daily_alert_limit"]
    for key in positive:
        if float(c.get(key,0))<=0: raise ValueError(f"config.json: {key} must be greater than zero")
    for key in ("minimum_buy_ratio_percent","maximum_price_change_h1_percent","minimum_fortune_score"):
        if not 0<=float(c.get(key,-1))<=100 and key!="maximum_price_change_h1_percent": raise ValueError(f"config.json: invalid {key}")
    if c.get("minimum_confidence") not in {"LOW","MEDIUM","HIGH"}: raise ValueError("config.json: minimum_confidence must be LOW, MEDIUM, or HIGH")
