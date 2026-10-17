from __future__ import annotations
import json,sqlite3,threading
from contextlib import contextmanager
from datetime import UTC,datetime
from pathlib import Path
from .models import ProviderHealth,TokenResearch


class Database:
    def __init__(self,url):
        if not url.startswith("sqlite:///"): raise RuntimeError("Version 1 requires SQLite")
        path=url.removeprefix("sqlite:///");
        if path!=":memory:": Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.c=sqlite3.connect(path,check_same_thread=False); self.c.row_factory=sqlite3.Row; self.lock=threading.RLock(); self.migrate()
    @contextmanager
    def tx(self):
        with self.lock:
            try: yield; self.c.commit()
            except: self.c.rollback(); raise
    def migrate(self):
        with self.tx(): self.c.executescript("""
        CREATE TABLE IF NOT EXISTS migrations(version INTEGER PRIMARY KEY,applied_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS watchlist(contract TEXT PRIMARY KEY,added_by INTEGER NOT NULL,added_at TEXT NOT NULL,name TEXT,symbol TEXT,last_research TEXT,last_score INTEGER,status TEXT);
        CREATE TABLE IF NOT EXISTS alerts(id INTEGER PRIMARY KEY AUTOINCREMENT,contract TEXT NOT NULL,idempotency_key TEXT UNIQUE NOT NULL,created_at TEXT NOT NULL,score INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_alert_contract_time ON alerts(contract,created_at);
        CREATE TABLE IF NOT EXISTS score_history(id INTEGER PRIMARY KEY AUTOINCREMENT,contract TEXT NOT NULL,score INTEGER,qualified INTEGER,confidence TEXT,payload_json TEXT,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS provider_health(name TEXT PRIMARY KEY,payload_json TEXT NOT NULL,updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL,updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,actor_id INTEGER,action TEXT,details_json TEXT,created_at TEXT NOT NULL);
        INSERT OR IGNORE INTO migrations VALUES(1,datetime('now'));
        """)
    def add_watch(self,contract,user):
        with self.tx(): self.c.execute("INSERT OR IGNORE INTO watchlist(contract,added_by,added_at,status) VALUES(?,?,?,?)",(contract,user,_now(),"WATCHING"))
    def remove_watch(self,contract):
        with self.tx(): self.c.execute("DELETE FROM watchlist WHERE contract=?",(contract,))
    def watches(self): return [dict(x) for x in self.c.execute("SELECT * FROM watchlist ORDER BY added_at")]
    def setting(self,key):
        row=self.c.execute("SELECT value FROM settings WHERE key=?",(key,)).fetchone(); return row[0] if row else None
    def set_setting(self,key,value):
        with self.tx(): self.c.execute("INSERT INTO settings(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",(key,str(value),_now()))
    def save_score(self,r:TokenResearch):
        with self.tx(): self.c.execute("INSERT INTO score_history(contract,score,qualified,confidence,payload_json,created_at) VALUES(?,?,?,?,?,?)",(r.contract,r.score,int(r.qualified),r.confidence.value,json.dumps(r.to_dict(),default=str),_now()))
    def latest_scores(self,limit=10):
        return [dict(x) for x in self.c.execute("SELECT s.* FROM score_history s JOIN (SELECT contract,max(id) id FROM score_history GROUP BY contract) q ON s.id=q.id ORDER BY score DESC LIMIT ?",(limit,))]
    def alert_allowed(self,contract,key,cooldown_hours,daily_limit,now:datetime|None=None):
        now=now or datetime.now(UTC); day=now.strftime("%Y-%m-%d"); cutoff=now.timestamp()-cooldown_hours*3600
        if self.c.execute("SELECT 1 FROM alerts WHERE idempotency_key=?",(key,)).fetchone(): return False,"Duplicate alert"
        today=self.c.execute("SELECT count(*) FROM alerts WHERE created_at LIKE ?",(day+"%",)).fetchone()[0]
        if today>=daily_limit:return False,"Daily alert limit reached"
        row=self.c.execute("SELECT created_at FROM alerts WHERE contract=? ORDER BY id DESC LIMIT 1",(contract,)).fetchone()
        if row and datetime.fromisoformat(row[0]).timestamp()>cutoff:return False,"Token cooldown active"
        return True,"Allowed"
    def record_alert(self,contract,key,score):
        with self.tx(): self.c.execute("INSERT INTO alerts(contract,idempotency_key,created_at,score) VALUES(?,?,?,?)",(contract,key,_now(),score))
    def save_health(self,h:ProviderHealth):
        with self.tx(): self.c.execute("INSERT INTO provider_health(name,payload_json,updated_at) VALUES(?,?,?) ON CONFLICT(name) DO UPDATE SET payload_json=excluded.payload_json,updated_at=excluded.updated_at",(h.name,json.dumps(h.__dict__ if hasattr(h,'__dict__') else {k:getattr(h,k) for k in h.__slots__},default=str),_now()))
    def health(self): return [dict(x) for x in self.c.execute("SELECT * FROM provider_health ORDER BY name")]
    def audit(self,actor,action,details):
        with self.tx(): self.c.execute("INSERT INTO audit(actor_id,action,details_json,created_at) VALUES(?,?,?,?)",(actor,action,json.dumps(details),_now()))
    def close(self): self.c.close()
def _now():return datetime.now(UTC).isoformat()
