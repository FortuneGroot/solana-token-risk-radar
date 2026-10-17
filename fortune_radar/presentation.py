from __future__ import annotations
import json
import discord
from .models import TokenResearch

DISCLAIMER="Fortune&Finance educational on-chain research. This is not personalized financial advice, a safety guarantee, or an instruction to buy."


def research_embeds(r:TokenResearch)->list[discord.Embed]:
    m=r.market; color=0x2ECC71 if r.qualified else 0xD4AF37 if not r.blockers else 0xE74C3C
    title=f"{m.name} ({m.symbol})" if m else "Unknown Solana Token"
    first=discord.Embed(title=title,description=f"**Fortune Score: {r.score}/100 • Grade {r.grade}**\n**Confidence: {r.confidence.value}**\n**Qualified: {'YES' if r.qualified else 'NO'}\n`{r.contract}`",color=color)
    if m:
        tx=(m.buys_h1 or 0)+(m.sells_h1 or 0); ratio=(m.buys_h1/tx*100) if tx else None
        first.add_field(name="Market",value=f"Price: {_money(m.price_usd)}\nLiquidity: {_money(m.liquidity_usd)}\nMarket Cap/FDV: {_money(m.market_cap or m.fdv)}",inline=True)
        first.add_field(name="Activity",value=f"Vol 5m/1h: {_money(m.volume_m5)} / {_money(m.volume_h1)}\nVol 6h/24h: {_money(m.volume_h6)} / {_money(m.volume_h24)}\nBuys/Sells 1h: {m.buys_h1 if m.buys_h1 is not None else 'Unavailable'} / {m.sells_h1 if m.sells_h1 is not None else 'Unavailable'} ({f'{ratio:.1f}%' if ratio is not None else 'Unavailable'})",inline=True)
        first.add_field(name="Pool",value=f"DEX: {m.dex or 'Unavailable'}\n1h change: {f'{m.change_h1:+.1f}%' if m.change_h1 is not None else 'Unavailable'}\nGraduated Pump.fun: {'Recognized' if m.graduated_pumpfun else 'Not confirmed'}",inline=False)
    risk=r.risk
    first.add_field(name="Risk Data",value=f"Mint authority: {_flag(risk.mint_authority)}\nFreeze authority: {_flag(risk.freeze_authority)}\nTransfer restriction: {_flag(risk.transfer_restricted)}\nHoneypot indication: {_flag(risk.honeypot)}\nTop 10: {f'{risk.top10_percent:.1f}%' if risk.top10_percent is not None else 'Unavailable'}\nHolders: {risk.holder_count if risk.holder_count is not None else 'Unavailable'}\nVerification: {risk.verification}\nOrganic score: {risk.organic_score if risk.organic_score is not None else 'Unavailable'}",inline=False)
    links=[]
    if m and m.url:links.append(f"[DEX Screener]({m.url})")
    links.extend([f"[Jupiter](https://jup.ag/swap/SOL-{r.contract})",f"[RugCheck](https://rugcheck.xyz/tokens/{r.contract})",f"[BubbleMaps](https://app.bubblemaps.io/sol/token/{r.contract})",f"[Solscan](https://solscan.io/token/{r.contract})"])
    first.add_field(name="Research Links",value=" • ".join(links)[:1024],inline=False); first.set_footer(text=DISCLAIMER)
    return [first]


def dashboard_embed(rows:list[dict],dry_run:bool)->discord.Embed:
    e=discord.Embed(title="FORTUNE ON-CHAIN RADAR • TRENDING BOARD",description=("**DRY RUN — automatic alerts disabled**\n" if dry_run else "")+"These rankings are educational research shortlists, not buy signals.",color=0xD4AF37)
    lines=[]
    for rank,row in enumerate(rows,1):
        data=json.loads(row["payload_json"]); m=data.get("market") or {}; lines.append(f"**{rank}. {m.get('symbol','UNKNOWN')} • {row['score']}/100 • {row['confidence']}**\nLiq {_money(m.get('liquidity_usd'))} • Vol 1h {_money(m.get('volume_h1'))} • Change {m.get('change_h1','Unavailable')}%\n[Chart]({m.get('url') or 'https://dexscreener.com/solana/'+row['contract']}) • `{row['contract'][:6]}…{row['contract'][-4:]}`")
    e.add_field(name="Top candidates",value="\n\n".join(lines)[:1024] or "No researched candidates yet.",inline=False); e.set_footer(text=DISCLAIMER); return e

def _money(v):
    if v is None:return "Unavailable"
    if abs(v)>=1_000_000:return f"${v/1_000_000:.2f}M"
    if abs(v)>=1_000:return f"${v/1_000:.1f}K"
    return f"${v:,.8f}" if abs(v)<1 else f"${v:,.2f}"
def _flag(v):return "Detected" if v is True else "Not detected" if v is False else "Unavailable"
def _list(v,empty):return ("\n".join(f"• {x}" for x in v) or empty)[:1024]
