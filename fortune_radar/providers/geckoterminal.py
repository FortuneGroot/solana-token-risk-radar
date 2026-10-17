from .base import BaseProvider


class GeckoTerminalProvider(BaseProvider):
    name="GeckoTerminal"; base="https://api.geckoterminal.com/api/v2"
    async def discover(self):
        contracts=[]
        for endpoint in ("trending_pools","new_pools"):
            data=await self.get_json(f"{self.base}/networks/solana/{endpoint}",params={"include":"base_token","page":"1"})
            contracts.extend(self.parse_contracts(data))
        return list(dict.fromkeys(contracts))
    @staticmethod
    def parse_contracts(payload):
        included={x.get("id"):x for x in payload.get("included",[]) if x.get("type")=="token"}
        result=[]
        for row in payload.get("data",[]):
            rel=((row.get("relationships") or {}).get("base_token") or {}).get("data") or {}; token=included.get(rel.get("id"),{})
            address=(token.get("attributes") or {}).get("address")
            if not address and isinstance(rel.get("id"),str): address=rel["id"].split("_",1)[-1]
            if address: result.append(address)
        return result
