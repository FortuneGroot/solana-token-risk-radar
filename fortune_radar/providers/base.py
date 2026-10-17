from __future__ import annotations
import asyncio, logging, random, time
from datetime import UTC, datetime
import aiohttp
from ..models import HealthStatus, ProviderHealth

LOG=logging.getLogger(__name__)


class ProviderError(RuntimeError): pass
class RateLimited(ProviderError): pass


class BaseProvider:
    name="provider"
    def __init__(self,session:aiohttp.ClientSession,timeout:int=15,retries:int=3,cache_seconds:int=120):
        self.session=session; self.timeout=timeout; self.retries=retries; self.cache_seconds=cache_seconds; self.cache={}; self.health=ProviderHealth(self.name)

    async def get_json(self,url:str,*,params=None,headers=None):
        key=(url,tuple(sorted((params or {}).items()))); cached=self.cache.get(key)
        if cached and time.monotonic()-cached[0]<self.cache_seconds:
            self.health.cache_age_seconds=int(time.monotonic()-cached[0]); return cached[1]
        error=None
        for attempt in range(self.retries):
            try:
                async with self.session.get(url,params=params,headers=headers,timeout=self.timeout) as response:
                    if response.status==429: raise RateLimited("Provider rate limited the request")
                    response.raise_for_status(); data=await response.json(content_type=None); self.cache[key]=(time.monotonic(),data); self._success(); return data
            except asyncio.CancelledError: raise
            except Exception as exc:
                error=exc; self._failure(exc)
                if attempt+1<self.retries: await asyncio.sleep(min(8,(2**attempt)+random.random()))
        if cached:
            self.health.status=HealthStatus.DEGRADED; self.health.cache_age_seconds=int(time.monotonic()-cached[0]); return cached[1]
        raise ProviderError(f"{self.name} unavailable after retries") from error

    def _success(self): self.health.status=HealthStatus.HEALTHY; self.health.last_success=datetime.now(UTC).isoformat(); self.health.consecutive_failures=0; self.health.last_error=""
    def _failure(self,exc):
        self.health.status=HealthStatus.RATE_LIMITED if isinstance(exc,RateLimited) else HealthStatus.DEGRADED
        self.health.last_failure=datetime.now(UTC).isoformat(); self.health.consecutive_failures+=1; self.health.last_error=str(exc)[:250]
