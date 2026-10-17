from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import StrEnum
from typing import Any


class HealthStatus(StrEnum):
    HEALTHY="HEALTHY"; DEGRADED="DEGRADED"; RATE_LIMITED="RATE_LIMITED"; UNAVAILABLE="UNAVAILABLE"


class Confidence(StrEnum):
    LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"


@dataclass(slots=True)
class PoolMarket:
    source: str; contract: str; pair_address: str=""; name: str="Unknown"; symbol: str="UNKNOWN"
    dex: str=""; quote_symbol: str=""; price_usd: float|None=None; liquidity_usd: float|None=None
    fdv: float|None=None; market_cap: float|None=None; volume_m5: float|None=None; volume_h1: float|None=None
    volume_h6: float|None=None; volume_h24: float|None=None; buys_h1: int|None=None; sells_h1: int|None=None
    change_h1: float|None=None; pool_created_at_ms: int|None=None; url: str=""; graduated_pumpfun: bool=False


@dataclass(slots=True)
class RiskData:
    mint_authority: bool|None=None; freeze_authority: bool|None=None; transfer_restricted: bool|None=None
    honeypot: bool|None=None; holder_count: int|None=None; top10_percent: float|None=None
    adjusted_top10_percent: float|None=None; developer_percent: float|None=None; insider_percent: float|None=None
    bundled_percent: float|None=None; suspicious: bool|None=None; verification: str="Unavailable"
    organic_score: float|None=None; liquidity_locked_percent: float|None=None; developer_history: str="Unavailable"
    exclusions: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list); sources: list[str]=field(default_factory=list)


@dataclass(slots=True)
class TokenResearch:
    contract: str; market: PoolMarket|None=None; risk: RiskData=field(default_factory=RiskData)
    score: int=0; grade: str="F"; confidence: Confidence=Confidence.LOW; qualified: bool=False
    passed: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list)
    blockers: list[str]=field(default_factory=list); missing: list[str]=field(default_factory=list); analyzed_at: str=""
    provider_sources: list[str]=field(default_factory=list)

    def to_dict(self)->dict[str,Any]: return asdict(self)


@dataclass(slots=True)
class ProviderHealth:
    name: str; status: HealthStatus=HealthStatus.UNAVAILABLE; last_success: str|None=None; last_failure: str|None=None
    consecutive_failures: int=0; last_error: str=""; cache_age_seconds: int|None=None
