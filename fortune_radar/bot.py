from __future__ import annotations
import asyncio,hashlib,logging
from datetime import UTC,datetime
import aiohttp,discord
from discord import app_commands
from discord.ext import commands,tasks
from .database import Database
from .presentation import dashboard_embed,research_embeds
from .providers.dexscreener import DexScreenerProvider
from .providers.geckoterminal import GeckoTerminalProvider
from .providers.jupiter import JupiterProvider
from .providers.rugcheck import RugCheckProvider
from .providers.solana import SolanaProvider
from .research import ResearchService
from .validation import validate_contract

LOG=logging.getLogger(__name__)


class RadarBot(commands.Bot):
    def __init__(self,settings):
        intents=discord.Intents.none(); intents.guilds=True
        super().__init__(command_prefix=commands.when_mentioned,intents=intents,allowed_mentions=discord.AllowedMentions.none())
        self.settings=settings; self.db=Database(settings.database_url); self.session=None; self.providers={}; self.researcher=None; self.scan_lock=asyncio.Lock(); register_commands(self)
    async def setup_hook(self):
        cfg=self.settings.config; self.session=aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=cfg["request_timeout_seconds"]))
        common=(self.session,cfg["request_timeout_seconds"],cfg["provider_retries"],cfg["provider_cache_seconds"])
        dex=DexScreenerProvider(*common); gecko=GeckoTerminalProvider(*common); jupiter=JupiterProvider(*common,api_key=self.settings.jupiter_key); solana=SolanaProvider(*common,rpc_url=self.settings.rpc_url)
        rug=RugCheckProvider(*common,base_url=self.settings.rugcheck_url) if cfg["optional_rugcheck_enabled"] else None
        self.providers={p.name:p for p in (dex,gecko,jupiter,solana,rug) if p}; self.dex,self.gecko=dex,gecko; self.researcher=ResearchService(dex,jupiter,solana,rug,self.db,cfg)
        self.db.set_setting("config_version","1"); await self.tree.sync(guild=discord.Object(id=self.settings.guild_id)); self.scan_loop.change_interval(seconds=cfg["scan_interval_seconds"]); self.dashboard_loop.change_interval(seconds=cfg["dashboard_interval_seconds"]); self.scan_loop.start(); self.dashboard_loop.start()
    async def on_ready(self):
        LOG.info("Fortune On-Chain Radar connected as %s; dry_run=%s",self.user,self.settings.config["dry_run"])
        for channel_id in (self.settings.command_channel,self.settings.alerts_channel,self.settings.dashboard_channel):
            if not self.get_channel(channel_id): LOG.error("Configured Discord channel unavailable: %s",channel_id)
    async def close(self):
        self.scan_loop.cancel(); self.dashboard_loop.cancel();
        if self.session:await self.session.close()
        self.db.close(); await super().close()
    @tasks.loop(seconds=300)
    async def scan_loop(self): await self.run_scan(None)
    @scan_loop.before_loop
    async def before_scan(self): await self.wait_until_ready()
    @tasks.loop(seconds=300)
    async def dashboard_loop(self): await self.refresh_dashboard()
    @dashboard_loop.before_loop
    async def before_dashboard(self): await self.wait_until_ready()
    async def run_scan(self,actor_id):
        if self.scan_lock.locked():return 0
        async with self.scan_lock:
            contracts=[]
            for provider in (self.dex,self.gecko):
                try: contracts.extend(await provider.discover())
                except Exception:LOG.warning("Discovery provider failed: %s",provider.name,exc_info=True)
                finally:self.db.save_health(provider.health)
            contracts.extend(x["contract"] for x in self.db.watches()); contracts=list(dict.fromkeys(contracts))[:self.settings.config["maximum_candidates_per_scan"]]
            alerted=0
            for contract in contracts:
                try: result=await self.researcher.research(validate_contract(contract))
                except Exception: LOG.warning("Candidate research failed: %s",contract,exc_info=True); continue
                if not result.qualified:continue
                key=hashlib.sha256(f"{contract}:{result.score}:{datetime.now(UTC):%Y-%m-%d-%H}".encode()).hexdigest()
                allowed,_=self.db.alert_allowed(contract,key,self.settings.config["alert_cooldown_hours"],self.settings.config["daily_alert_limit"])
                if not allowed:continue
                if self.settings.config["dry_run"]: LOG.info("DRY RUN qualified %s score=%s",contract,result.score); continue
                channel=self.get_channel(self.settings.alerts_channel)
                if isinstance(channel,discord.TextChannel):
                    content=f"<@&{self.settings.alert_role}>" if self.settings.alert_role else None; mentions=discord.AllowedMentions(roles=[discord.Object(id=self.settings.alert_role)]) if self.settings.alert_role else discord.AllowedMentions.none()
                    await channel.send(content=content,embeds=research_embeds(result),allowed_mentions=mentions); self.db.record_alert(contract,key,result.score); alerted+=1
            await self.refresh_dashboard(); self.db.audit(actor_id,"SCAN_COMPLETED",{"candidates":len(contracts),"alerts":alerted,"dry_run":self.settings.config["dry_run"]}); return alerted
    async def refresh_dashboard(self):
        channel=self.get_channel(self.settings.dashboard_channel)
        if not isinstance(channel,discord.TextChannel):return
        embed=dashboard_embed(self.db.latest_scores(self.settings.config["dashboard_size"]),self.settings.config["dry_run"]); msg_id=self.db.setting("dashboard_message_id"); msg=None
        await upsert_dashboard(channel,self.db,embed,msg_id)


async def upsert_dashboard(channel,db,embed,msg_id):
    msg=None
    if msg_id:
        try:msg=await channel.fetch_message(int(msg_id)); await msg.edit(embed=embed)
        except discord.NotFound:msg=None
    if msg is None:msg=await channel.send(embed=embed); db.set_setting("dashboard_message_id",msg.id)
    return msg


def register_commands(bot:RadarBot):
    guild=discord.Object(id=bot.settings.guild_id)
    async def fail(i,e):
        sender=i.followup.send if i.response.is_done() else i.response.send_message; await sender(str(e) or "The request could not be completed.",ephemeral=True)
    def channel(i):
        if i.channel_id!=bot.settings.command_channel:raise ValueError("Use Fortune On-Chain Radar commands in the on-chain command center.")
    def admin(i):return bot.settings.admin_role in {r.id for r in getattr(i.user,"roles",[])}
    async def lookup(i,contract):
        try:channel(i); await i.response.defer(); result=await bot.researcher.research(validate_contract(contract)); await i.followup.send(embeds=research_embeds(result))
        except Exception as e:await fail(i,e)
    @bot.tree.command(name="coin",description="Full Solana contract research",guild=guild)
    async def coin(i:discord.Interaction,contract:str):await lookup(i,contract)
    @bot.tree.command(name="holders",description="Holder concentration research",guild=guild)
    async def holders(i:discord.Interaction,contract:str):await lookup(i,contract)
    @bot.tree.command(name="developer",description="Available developer and insider research",guild=guild)
    async def developer(i:discord.Interaction,contract:str):await lookup(i,contract)
    @bot.tree.command(name="trending",description="Current researched trending candidates",guild=guild)
    async def trending(i:discord.Interaction):
        try:channel(i); await i.response.send_message(embed=dashboard_embed(bot.db.latest_scores(bot.settings.config["dashboard_size"]),bot.settings.config["dry_run"]))
        except Exception as e:await fail(i,e)
    @bot.tree.command(name="watch",description="Add a Solana contract to the server watchlist",guild=guild)
    async def watch(i:discord.Interaction,contract:str):
        try:channel(i); contract=validate_contract(contract); bot.db.add_watch(contract,i.user.id); bot.db.audit(i.user.id,"WATCH_ADDED",{"contract":contract}); await i.response.send_message(f"`{contract}` added to the research watchlist.",ephemeral=True)
        except Exception as e:await fail(i,e)
    @bot.tree.command(name="unwatch",description="Remove a contract from the watchlist",guild=guild)
    async def unwatch(i:discord.Interaction,contract:str):
        try:channel(i); contract=validate_contract(contract); bot.db.remove_watch(contract); bot.db.audit(i.user.id,"WATCH_REMOVED",{"contract":contract}); await i.response.send_message("Removed from watchlist.",ephemeral=True)
        except Exception as e:await fail(i,e)
    @bot.tree.command(name="watchlist",description="Display the server watchlist",guild=guild)
    async def watchlist(i:discord.Interaction):
        try:channel(i); rows=bot.db.watches(); await i.response.send_message("\n".join(f"`{x['contract']}`" for x in rows)[:1900] or "Watchlist is empty.")
        except Exception as e:await fail(i,e)
    @bot.tree.command(name="radar_status",description="Show bot and provider health",guild=guild)
    async def status(i:discord.Interaction):
        try:
            channel(i); lines=[f"**Mode:** {'DRY RUN' if bot.settings.config['dry_run'] else 'LIVE ALERTS'}",f"**Database:** Online"]
            lines.extend(f"**{p.name}:** {p.health.status.value} • failures {p.health.consecutive_failures} • last success {p.health.last_success or 'Never'}" for p in bot.providers.values()); await i.response.send_message("\n".join(lines)[:1900],ephemeral=True)
        except Exception as e:await fail(i,e)
    @bot.tree.command(name="radar_scan",description="Administrator: run an immediate scan",guild=guild)
    async def scan(i:discord.Interaction):
        try:
            channel(i)
            if not admin(i):raise PermissionError("Administrator role required.")
            await i.response.defer(ephemeral=True); count=await bot.run_scan(i.user.id); await i.followup.send(f"Scan completed. Public alerts sent: {count}. Mode: {'DRY RUN' if bot.settings.config['dry_run'] else 'LIVE' }.",ephemeral=True)
        except Exception as e:await fail(i,e)
    @bot.tree.error
    async def error(i,e):await fail(i,getattr(e,"original",e))
