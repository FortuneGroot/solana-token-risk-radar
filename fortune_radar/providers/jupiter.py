from .base import BaseProvider
from ..models import RiskData


class JupiterProvider(BaseProvider):
    name="Jupiter"; base="https://lite-api.jup.ag/tokens/v2"
    def __init__(self,*args,api_key="",**kwargs): super().__init__(*args,**kwargs); self.api_key=api_key
    async def risk(self,contract):
        headers={"x-api-key":self.api_key} if self.api_key else None
        rows=await self.get_json(f"{self.base}/search",params={"query":contract},headers=headers)
        return self.parse(rows,contract)
    @staticmethod
    def parse(payload,contract):
        rows=payload if isinstance(payload,list) else payload.get("tokens",[]) if isinstance(payload,dict) else []
        row=next((r for r in rows if r.get("id")==contract or r.get("address")==contract),rows[0] if rows else {})
        audit=row.get("audit") or {}; tags=row.get("tags") or []
        return RiskData(mint_authority=_authority(audit.get("mintAuthorityDisabled")),freeze_authority=_authority(audit.get("freezeAuthorityDisabled")),holder_count=_i(row.get("holderCount")),top10_percent=_f(audit.get("topHoldersPercentage")),verification="Verified" if "verified" in tags or row.get("isVerified") else "Unverified",organic_score=_f(row.get("organicScore")),suspicious=row.get("isSus") if "isSus" in row else None,sources=["Jupiter"])

def _authority(disabled): return None if disabled is None else not bool(disabled)
def _f(v):
    try:return float(v) if v is not None else None
    except:return None
def _i(v):
    try:return int(v) if v is not None else None
    except:return None
