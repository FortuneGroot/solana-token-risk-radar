"""Optional read-only provider connectivity probe. It never connects to wallets or Discord."""
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import aiohttp
from fortune_radar.providers.dexscreener import DexScreenerProvider
from fortune_radar.providers.geckoterminal import GeckoTerminalProvider
from fortune_radar.providers.jupiter import JupiterProvider
from fortune_radar.providers.solana import SolanaProvider
from fortune_radar.providers.rugcheck import RugCheckProvider

CONTRACT="So11111111111111111111111111111111111111112"
async def main():
    async with aiohttp.ClientSession() as session:
        providers=[DexScreenerProvider(session),GeckoTerminalProvider(session),JupiterProvider(session),SolanaProvider(session),RugCheckProvider(session)]
        checks=[("DEX Screener",lambda:providers[0].token_pools(CONTRACT)),("GeckoTerminal",providers[1].discover),("Jupiter",lambda:providers[2].risk(CONTRACT)),("Solana RPC",lambda:providers[3].risk(CONTRACT)),("RugCheck optional",lambda:providers[4].risk(CONTRACT))]
        for name,call in checks:
            try:
                value=await call();print(json.dumps({"provider":name,"status":"SUCCESS","result_count":len(value) if isinstance(value,list) else 1}))
            except Exception as exc:print(json.dumps({"provider":name,"status":"FAILED","error":str(exc)[:200]}))
if __name__=="__main__":asyncio.run(main())
