from .base import BaseProvider
from ..models import RiskData


class RugCheckProvider(BaseProvider):
    name="RugCheck"
    def __init__(self,*args,base_url="https://api.rugcheck.xyz/v1",**kwargs): super().__init__(*args,**kwargs); self.base_url=base_url.rstrip("/")
    async def risk(self,contract): return self.parse(await self.get_json(f"{self.base_url}/tokens/{contract}/report"))
    @staticmethod
    def parse(row):
        risks=row.get("risks") or []; names=" ".join(str(x.get("name","")).lower() for x in risks); top=row.get("topHolders") or []
        return RiskData(mint_authority=bool(row.get("mintAuthority")) if "mintAuthority" in row else None,freeze_authority=bool(row.get("freezeAuthority")) if "freezeAuthority" in row else None,top10_percent=sum(float(x.get("pct",0)) for x in top[:10]) if top else None,holder_count=len(top) or None,suspicious=bool(risks) if risks else False,warnings=[x.get("name","Risk warning") for x in risks[:8]],sources=["RugCheck"],transfer_restricted=True if "transfer" in names else None,honeypot=True if "honeypot" in names else None)
