import asyncio,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
import discord
from fortune_radar.bot import RadarBot,upsert_dashboard
from fortune_radar.config import Settings
from fortune_radar.database import Database
from fortune_radar.models import PoolMarket,RiskData
from fortune_radar.presentation import dashboard_embed,research_embeds
from fortune_radar.scoring import score

ROOT=Path(__file__).parents[1]

class DiscordTests(unittest.TestCase):
    def settings(self):
        cfg=json.loads((ROOT/"config.example.json").read_text());return Settings("x",1,2,3,4,5,None,"rpc","","rug","sqlite:///:memory:",cfg,ROOT)
    def test_command_registration(self):
        bot=RadarBot(self.settings());names=[x.name for x in bot.tree.get_commands(guild=discord.Object(id=1))];self.assertEqual(names,["coin","holders","developer","trending","watch","unwatch","watchlist","radar_status","radar_scan"]);bot.db.close()
    def test_research_embeds_within_limits(self):
        c=json.loads((ROOT/"config.example.json").read_text());m=PoolMarket("DEX Screener","x",name="Coin",symbol="COIN",liquidity_usd=100000,volume_h1=100000,buys_h1=60,sells_h1=40,fdv=1000000,change_h1=10,pool_created_at_ms=1)
        r=score("x",m,RiskData(mint_authority=False,freeze_authority=False,transfer_restricted=False,honeypot=False,suspicious=False,top10_percent=10,sources=["A","B"]),c,now_ms=10_000_000)
        for embed in research_embeds(r):
            self.assertLessEqual(len(embed),6000);self.assertLessEqual(len(embed.fields),25);self.assertIn("educational",embed.footer.text)
    def test_dashboard_edit_in_place(self):
        class Message:
            id=99
            def __init__(self):self.edits=0
            async def edit(self,**kwargs):self.edits+=1
        class Channel:
            def __init__(self):self.msg=Message();self.sends=0
            async def fetch_message(self,id):self.asserted=id;return self.msg
            async def send(self,**kwargs):self.sends+=1;return self.msg
        db=Database("sqlite:///:memory:");ch=Channel();asyncio.run(upsert_dashboard(ch,db,dashboard_embed([],True),"99"));self.assertEqual(ch.msg.edits,1);self.assertEqual(ch.sends,0);db.close()
    def test_dashboard_embed_limits(self):
        e=dashboard_embed([],True);self.assertLessEqual(len(e),6000);self.assertIn("DRY RUN",e.description)

if __name__=="__main__":unittest.main()
