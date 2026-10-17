import json,tempfile,unittest
from datetime import UTC,datetime,timedelta
from pathlib import Path
from fortune_radar.config import validate_config
from fortune_radar.database import Database
from fortune_radar.models import PoolMarket,RiskData
from fortune_radar.providers.dexscreener import DexScreenerProvider
from fortune_radar.providers.geckoterminal import GeckoTerminalProvider
from fortune_radar.providers.jupiter import JupiterProvider
from fortune_radar.providers.rugcheck import RugCheckProvider
from fortune_radar.providers.solana import SolanaProvider
from fortune_radar.scoring import merge_risks,score,select_best_pool
from fortune_radar.validation import validate_contract

ROOT=Path(__file__).parents[1]
def fixture(name):return json.loads((ROOT/"fixtures"/name).read_text())
def cfg():return json.loads((ROOT/"config.example.json").read_text())

class CoreTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.db=Database(f"sqlite:///{Path(self.tmp.name)/'db.sqlite'}")
    def tearDown(self):self.db.close();self.tmp.cleanup()
    def market(self,**changes):
        base=PoolMarket("test","So11111111111111111111111111111111111111112",liquidity_usd=100000,fdv=1000000,volume_h1=80000,buys_h1=60,sells_h1=40,change_h1=20,pool_created_at_ms=int((datetime.now(UTC)-timedelta(hours=2)).timestamp()*1000))
        for k,v in changes.items():setattr(base,k,v)
        return base
    def safe(self):return RiskData(mint_authority=False,freeze_authority=False,transfer_restricted=False,honeypot=False,top10_percent=30,developer_percent=5,insider_percent=10,bundled_percent=10,suspicious=False,sources=["A","B"])
    def test_contract_validation(self):
        self.assertEqual(validate_contract("So11111111111111111111111111111111111111112"),"So11111111111111111111111111111111111111112")
        for bad in ("abc","0OIl","111"):
            with self.assertRaises(ValueError):validate_contract(bad)
    def test_config_validation(self):validate_config(cfg())
    def test_bad_config(self):
        c=cfg();c["daily_alert_limit"]=0
        with self.assertRaises(ValueError):validate_config(c)
    def test_dex_fixture(self):
        rows=DexScreenerProvider.parse_pairs(fixture("dexscreener_pairs.json"));self.assertEqual(len(rows),1);self.assertEqual(rows[0].volume_h1,90000);self.assertEqual(rows[0].buys_h1,70)
    def test_gecko_fixture(self):self.assertEqual(GeckoTerminalProvider.parse_contracts(fixture("gecko_trending.json")),["So11111111111111111111111111111111111111112"])
    def test_jupiter_fixture(self):
        r=JupiterProvider.parse(fixture("jupiter_token.json"),"So11111111111111111111111111111111111111112");self.assertFalse(r.mint_authority);self.assertEqual(r.top10_percent,18.5);self.assertEqual(r.verification,"Verified")
    def test_rugcheck_fixture(self):self.assertFalse(RugCheckProvider.parse(fixture("rugcheck_report.json")).suspicious)
    def test_solana_fixture(self):
        f=fixture("solana_largest.json");r=SolanaProvider.parse(f["largest"],f["supply"],f["account"]);self.assertEqual(r.top10_percent,23);self.assertFalse(r.mint_authority)
    def test_best_pool(self):
        a=self.market(liquidity_usd=100000);b=self.market(liquidity_usd=200000);self.assertIs(select_best_pool([a,b]),b)
    def test_missing_pool_hard_block(self):self.assertIn("No active legitimate liquidity pool",score("x",None,self.safe(),cfg()).blockers)
    def test_safe_score_qualifies(self):
        r=score("x",self.market(),self.safe(),cfg());self.assertTrue(r.qualified);self.assertGreaterEqual(r.score,72)
    def test_mint_blocker_overrides_score(self):
        risk=self.safe();risk.mint_authority=True;r=score("x",self.market(),risk,cfg());self.assertFalse(r.qualified);self.assertIn("Mint authority enabled",r.blockers)
    def test_liquidity_filter(self):self.assertFalse(score("x",self.market(liquidity_usd=10),self.safe(),cfg()).qualified)
    def test_volume_filter(self):self.assertFalse(score("x",self.market(volume_h1=10),self.safe(),cfg()).qualified)
    def test_transaction_filter(self):self.assertFalse(score("x",self.market(buys_h1=2,sells_h1=2),self.safe(),cfg()).qualified)
    def test_buy_ratio_filter(self):self.assertFalse(score("x",self.market(buys_h1=30,sells_h1=70),self.safe(),cfg()).qualified)
    def test_fdv_liquidity_filter(self):self.assertFalse(score("x",self.market(fdv=100000000),self.safe(),cfg()).qualified)
    def test_extension_filter(self):self.assertFalse(score("x",self.market(change_h1=300),self.safe(),cfg()).qualified)
    def test_maximum_discovery_age(self):self.assertFalse(score("x",self.market(pool_created_at_ms=int((datetime.now(UTC)-timedelta(days=31)).timestamp()*1000)),self.safe(),cfg()).qualified)
    def test_developer_concentration_blocker(self):
        r=self.safe();r.developer_percent=25;self.assertFalse(score("x",self.market(),r,cfg()).qualified)
    def test_age_filter(self):self.assertFalse(score("x",self.market(pool_created_at_ms=int(datetime.now(UTC).timestamp()*1000)),self.safe(),cfg()).qualified)
    def test_missing_data_reduces_confidence(self):self.assertEqual(score("x",PoolMarket("x","x"),RiskData(),cfg()).confidence.value,"LOW")
    def test_risk_merge_is_conservative(self):
        r=merge_risks([RiskData(mint_authority=False,sources=["A"]),RiskData(mint_authority=True,sources=["B"])]);self.assertTrue(r.mint_authority);self.assertEqual(r.sources,["A","B"])
    def test_watchlist_persistence(self):
        c="So11111111111111111111111111111111111111112";self.db.add_watch(c,1);self.assertEqual(self.db.watches()[0]["contract"],c);self.db.remove_watch(c);self.assertEqual(self.db.watches(),[])
    def test_duplicate_alert(self):
        self.db.record_alert("x","key",80);allowed,reason=self.db.alert_allowed("x","key",12,8);self.assertFalse(allowed);self.assertEqual(reason,"Duplicate alert")
    def test_cooldown(self):
        self.db.record_alert("x","a",80);allowed,reason=self.db.alert_allowed("x","b",12,8);self.assertFalse(allowed);self.assertEqual(reason,"Token cooldown active")
    def test_daily_budget(self):
        for n in range(2):self.db.record_alert(str(n),str(n),80)
        self.assertEqual(self.db.alert_allowed("new","new",12,2)[1],"Daily alert limit reached")
    def test_dashboard_setting(self):self.db.set_setting("dashboard_message_id",123);self.assertEqual(self.db.setting("dashboard_message_id"),"123")
    def test_migration(self):self.assertEqual(self.db.c.execute("SELECT count(*) FROM migrations").fetchone()[0],1)

if __name__=="__main__":unittest.main()
