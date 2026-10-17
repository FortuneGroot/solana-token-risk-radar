import asyncio,random
from .base import BaseProvider,ProviderError
from ..models import RiskData


class SolanaProvider(BaseProvider):
    name="Solana RPC"
    def __init__(self,*args,rpc_url="https://api.mainnet-beta.solana.com",**kwargs): super().__init__(*args,**kwargs); self.rpc_url=rpc_url; self.counter=0
    async def _rpc(self,method,params):
        error=None
        for attempt in range(self.retries):
            try:
                self.counter+=1; payload={"jsonrpc":"2.0","id":self.counter,"method":method,"params":params}
                async with self.session.post(self.rpc_url,json=payload,timeout=self.timeout) as response:
                    response.raise_for_status(); data=await response.json(content_type=None)
                if data.get("error"): raise RuntimeError(str(data["error"]))
                self._success(); return data.get("result")
            except asyncio.CancelledError: raise
            except Exception as exc:
                error=exc; self._failure(exc)
                if attempt+1<self.retries: await asyncio.sleep(min(8,(2**attempt)+random.random()))
        raise ProviderError("Solana RPC unavailable after retries") from error
    async def risk(self,contract):
        largest=await self._rpc("getTokenLargestAccounts",[contract]); supply=await self._rpc("getTokenSupply",[contract]); account=await self._rpc("getAccountInfo",[contract,{"encoding":"jsonParsed"}])
        return self.parse(largest,supply,account)
    @staticmethod
    def parse(largest,supply,account):
        total=float(((supply or {}).get("value") or {}).get("uiAmount") or 0); rows=(largest or {}).get("value") or []
        top=sum(float(x.get("uiAmount") or 0) for x in rows[:10]); pct=(top/total*100) if total else None
        info=((((account or {}).get("value") or {}).get("data") or {}).get("parsed") or {}).get("info") or {}
        return RiskData(mint_authority=bool(info.get("mintAuthority")) if "mintAuthority" in info else None,freeze_authority=bool(info.get("freezeAuthority")) if "freezeAuthority" in info else None,top10_percent=pct,holder_count=None,sources=["Solana RPC"])
