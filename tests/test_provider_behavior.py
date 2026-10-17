import asyncio,time,unittest
from fortune_radar.models import HealthStatus
from fortune_radar.providers.base import BaseProvider,ProviderError

class Response:
    def __init__(self,status=200,data=None,error=None):self.status=status;self.data=data or {"ok":True};self.error=error
    async def __aenter__(self):return self
    async def __aexit__(self,*args):return False
    def raise_for_status(self):
        if self.error:raise self.error
    async def json(self,content_type=None):return self.data
class Session:
    def __init__(self,responses):self.responses=list(responses);self.calls=0
    def get(self,*args,**kwargs):self.calls+=1;return self.responses.pop(0)

class ProviderBehaviorTests(unittest.TestCase):
    def test_success_and_cache(self):
        session=Session([Response(data={"value":1})]);p=BaseProvider(session,retries=1,cache_seconds=60)
        first=asyncio.run(p.get_json("https://example.test"));second=asyncio.run(p.get_json("https://example.test"))
        self.assertEqual(first,second);self.assertEqual(session.calls,1);self.assertEqual(p.health.status,HealthStatus.HEALTHY)
    def test_stale_cache_fallback_is_degraded(self):
        session=Session([Response(data={"value":1}),Response(error=RuntimeError("offline"))]);p=BaseProvider(session,retries=1,cache_seconds=0)
        asyncio.run(p.get_json("https://example.test"));value=asyncio.run(p.get_json("https://example.test"))
        self.assertEqual(value,{"value":1});self.assertEqual(p.health.status,HealthStatus.DEGRADED)
    def test_rate_limit_health(self):
        p=BaseProvider(Session([Response(status=429)]),retries=1,cache_seconds=0)
        with self.assertRaises(ProviderError):asyncio.run(p.get_json("https://example.test"))
        self.assertEqual(p.health.status,HealthStatus.RATE_LIMITED)

if __name__=="__main__":unittest.main()
