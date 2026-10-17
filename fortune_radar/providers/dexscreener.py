from .base import BaseProvider
from ..models import PoolMarket


class DexScreenerProvider(BaseProvider):
    name="DEX Screener"; base="https://api.dexscreener.com"
    async def token_pools(self,contract): return self.parse_pairs(await self.get_json(f"{self.base}/token-pairs/v1/solana/{contract}"),contract)
    async def discover(self):
        # Latest token profiles are discovery candidates only; paid boosts never add score or qualification.
        rows=await self.get_json(f"{self.base}/token-profiles/latest/v1")
        return list(dict.fromkeys(str(x.get("tokenAddress")) for x in rows if x.get("chainId")=="solana" and x.get("tokenAddress")))
    @staticmethod
    def parse_pairs(payload,contract=""):
        rows=payload.get("pairs",[]) if isinstance(payload,dict) else payload if isinstance(payload,list) else []
        result=[]
        for p in rows:
            if p.get("chainId")!="solana": continue
            base=p.get("baseToken") or {}; tx=(p.get("txns") or {}).get("h1") or {}; vol=p.get("volume") or {}; ch=p.get("priceChange") or {}
            pump_text=" ".join([str(p.get("dexId","")),str(p.get("url",""))," ".join(p.get("labels") or [])]).lower()
            result.append(PoolMarket("DEX Screener",base.get("address") or contract,p.get("pairAddress","") ,base.get("name","Unknown"),base.get("symbol","UNKNOWN"),p.get("dexId",""),(p.get("quoteToken") or {}).get("symbol",""),_f(p.get("priceUsd")),_f((p.get("liquidity") or {}).get("usd")),_f(p.get("fdv")),_f(p.get("marketCap")),_f(vol.get("m5")),_f(vol.get("h1")),_f(vol.get("h6")),_f(vol.get("h24")),_i(tx.get("buys")),_i(tx.get("sells")),_f(ch.get("h1")),_i(p.get("pairCreatedAt")),p.get("url",""),"pump" in pump_text))
        return result

def _f(v):
    try:return float(v) if v is not None else None
    except:return None
def _i(v):
    try:return int(v) if v is not None else None
    except:return None
