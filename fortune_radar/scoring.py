from __future__ import annotations
from datetime import UTC, datetime
from .models import Confidence, PoolMarket, RiskData, TokenResearch


def select_best_pool(pools:list[PoolMarket])->PoolMarket|None:
    eligible=[p for p in pools if p.contract and (p.liquidity_usd or 0)>0]
    return max(eligible,key=lambda p:((p.liquidity_usd or 0),(p.volume_h1 or 0),(p.buys_h1 or 0)+(p.sells_h1 or 0)),default=None)


def merge_risks(items:list[RiskData])->RiskData:
    out=RiskData()
    fields=("mint_authority","freeze_authority","transfer_restricted","honeypot","holder_count","top10_percent","adjusted_top10_percent","developer_percent","insider_percent","bundled_percent","suspicious","organic_score","liquidity_locked_percent")
    for item in items:
        for field in fields:
            value=getattr(item,field)
            if value is None: continue
            old=getattr(out,field)
            if isinstance(value,bool): setattr(out,field,bool(old) or value)
            elif old is None: setattr(out,field,value)
        if item.verification!="Unavailable": out.verification=item.verification
        if item.developer_history!="Unavailable": out.developer_history=item.developer_history
        out.exclusions.extend(item.exclusions); out.warnings.extend(item.warnings); out.sources.extend(item.sources)
    out.sources=list(dict.fromkeys(out.sources)); out.warnings=list(dict.fromkeys(out.warnings)); return out


def score(contract:str,market:PoolMarket|None,risk:RiskData,cfg:dict,now_ms:int|None=None)->TokenResearch:
    now_ms=now_ms or int(datetime.now(UTC).timestamp()*1000); result=TokenResearch(contract,market,risk,analyzed_at=datetime.now(UTC).isoformat(),provider_sources=list(dict.fromkeys(([market.source] if market else [])+risk.sources)))
    if not market: result.blockers.append("No active legitimate liquidity pool"); return _finish(result,cfg,0,0)
    points=0; known=0; total_checks=17; maximum_points=19
    def check(name,ok,weight=1,hard=False):
        nonlocal points,known
        if ok is None: result.missing.append(name); return
        known+=1
        if ok: points+=weight; result.passed.append(name)
        elif hard: result.blockers.append(name)
        else: result.warnings.append(name)
    age_min=(now_ms-market.pool_created_at_ms)/60000 if market.pool_created_at_ms else None
    tx=(market.buys_h1 or 0)+(market.sells_h1 or 0) if market.buys_h1 is not None and market.sells_h1 is not None else None
    ratio=(market.buys_h1/tx*100) if tx else None; cap=market.market_cap or market.fdv; capliq=(cap/market.liquidity_usd) if cap and market.liquidity_usd else None
    check("Minimum age",None if age_min is None else age_min>=cfg["minimum_age_minutes"],2,True)
    check("Within maximum discovery age",None if age_min is None else age_min<=cfg["maximum_discovery_age_days"]*1440,1,True)
    check("Liquidity threshold",None if market.liquidity_usd is None else market.liquidity_usd>=cfg["minimum_liquidity_usd"],2,True)
    check("One-hour volume",None if market.volume_h1 is None else market.volume_h1>=cfg["minimum_volume_h1_usd"],1,True)
    check("One-hour transactions",None if tx is None else tx>=cfg["minimum_transactions_h1"],1,True)
    check("Buy ratio",None if ratio is None else ratio>=cfg["minimum_buy_ratio_percent"],1,True)
    check("FDV/liquidity ratio",None if capliq is None else capliq<=cfg["maximum_fdv_liquidity_ratio"],1,True)
    check("Price extension",None if market.change_h1 is None else abs(market.change_h1)<=cfg["maximum_price_change_h1_percent"],1,True)
    blockers=cfg.get("hard_blockers",{})
    for label,field,key in (("Mint authority enabled","mint_authority","mint_authority"),("Freeze authority enabled","freeze_authority","freeze_authority"),("Transfer restriction detected","transfer_restricted","transfer_restriction"),("Honeypot indication","honeypot","honeypot"),("Suspicious-token status","suspicious","suspicious_token")):
        value=getattr(risk,field); check(label,None if value is None else not value,1,bool(blockers.get(key,True)))
    if risk.top10_percent is None: result.missing.append("Top-holder concentration")
    else:
        known+=1
        if risk.top10_percent>cfg["maximum_top10_holder_percent"] and blockers.get("extreme_holder_concentration",True): result.blockers.append(f"Extreme top-holder concentration ({risk.top10_percent:.1f}%)")
        elif risk.top10_percent>50: result.warnings.append(f"High top-holder concentration ({risk.top10_percent:.1f}%)")
        else: points+=1; result.passed.append("Holder concentration")
    for label,field,threshold,key in (("Developer concentration","developer_percent",cfg["maximum_developer_percent"],"developer_concentration"),("Insider concentration","insider_percent",cfg["maximum_insider_percent"],"insider_concentration"),("Bundled launch concentration","bundled_percent",cfg["maximum_bundled_percent"],"bundled_launch")):
        value=getattr(risk,field)
        if value is None: result.missing.append(label); continue
        known+=1
        if value>threshold and blockers.get(key,True): result.blockers.append(f"{label} ({value:.1f}%)")
        elif value>threshold: result.warnings.append(f"{label} ({value:.1f}%)")
        else: points+=1; result.passed.append(label)
    raw=round(points/maximum_points*100); return _finish(result,cfg,raw,known/total_checks)


def _finish(r,cfg,raw,coverage):
    penalty=min(30,len(r.missing)*3); r.score=max(0,min(100,raw-penalty)); r.grade="A" if r.score>=90 else "B" if r.score>=80 else "C" if r.score>=70 else "D" if r.score>=60 else "F"
    r.confidence=Confidence.HIGH if coverage>=.8 and len(r.provider_sources)>=2 else Confidence.MEDIUM if coverage>=.55 else Confidence.LOW
    order={"LOW":0,"MEDIUM":1,"HIGH":2}; r.qualified=not r.blockers and r.score>=cfg["minimum_fortune_score"] and order[r.confidence.value]>=order[cfg["minimum_confidence"]]
    r.warnings=list(dict.fromkeys(r.warnings+r.risk.warnings)); return r
