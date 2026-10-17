from __future__ import annotations
import asyncio,logging
from .scoring import merge_risks,score,select_best_pool

LOG=logging.getLogger(__name__)


class ResearchService:
    def __init__(self,dex,jupiter,solana,rugcheck,db,cfg): self.dex,self.jupiter,self.solana,self.rugcheck,self.db,self.cfg=dex,jupiter,solana,rugcheck,db,cfg
    async def research(self,contract):
        pools=await self.dex.token_pools(contract); market=select_best_pool(pools); risks=[]
        async def collect(provider):
            try: risks.append(await provider.risk(contract))
            except Exception: LOG.warning("%s risk unavailable for %s",provider.name,contract,exc_info=True)
            finally: self.db.save_health(provider.health)
        providers=[self.jupiter,self.solana]+([self.rugcheck] if self.rugcheck else [])
        await asyncio.gather(*(collect(p) for p in providers)); result=score(contract,market,merge_risks(risks),self.cfg); self.db.save_score(result); self.db.save_health(self.dex.health); return result
