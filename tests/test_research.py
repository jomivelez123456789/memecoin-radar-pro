import copy
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from radar import research
from radar.app import load_config
from radar.engine import evaluate
from radar.http import ApiError
from radar.market import Market
from test_radar import NOW, SOL, EVM, sample


def feed(channel=None, video="abcdefghijk", date=None):
    channel = channel or research.CHANNELS["Coin Bureau"]
    date = date or datetime.fromtimestamp(NOW, timezone.utc).isoformat()
    return f'''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015">
    <yt:channelId>{channel}</yt:channelId><entry><yt:videoId>{video}</yt:videoId>
    <title>&lt;b&gt;Opinion&lt;/b&gt;</title><published>{date}</published></entry></feed>'''


class ResearchTests(unittest.TestCase):
    def test_channel_identity_dates_and_video_ids(self):
        cid = research.CHANNELS["Coin Bureau"]
        self.assertEqual(len(research.youtube_items(feed(), "Coin Bureau", cid, NOW)), 1)
        self.assertEqual(len(research.youtube_items(feed(cid[2:]), "Coin Bureau", cid, NOW)), 1)
        with self.assertRaises(ValueError):
            research.youtube_items(feed("wrong"), "Coin Bureau", cid, NOW)
        for xml in (feed(video="../bad"), feed(date="2020-01-01T00:00:00+00:00"), feed(date="2027-01-01T00:00:00+00:00")):
            self.assertEqual(research.youtube_items(xml, "Coin Bureau", cid, NOW), [])
        with self.assertRaises(ValueError):
            research.youtube_items('<!DOCTYPE feed>' + feed(), "Coin Bureau", cid, NOW)

    def test_failure_is_explicit_and_cache_respected(self):
        class Fake:
            calls = 0
            def json(self, url): self.calls += 1; raise ApiError("offline")
            def text(self, url): self.calls += 1; raise ApiError("offline")
        fake, data = Fake(), {}
        research.refresh(data, fake, NOW)
        research.refresh(data, fake, NOW + 300)
        self.assertEqual(fake.calls, 5)
        self.assertFalse(data["research"]["benchmarks"])
        self.assertTrue(all("indisponível" in status for status in data["research"]["sources"].values()))

    def test_invalid_benchmark_never_becomes_zero(self):
        class Fake:
            def json(self, url): return {"open": "0", "last": "nan"}
            def text(self, url): raise ApiError("offline")
        data = {}
        research.refresh(data, Fake(), NOW)
        self.assertEqual(data["research"]["benchmarks"], {})

    def test_window_counts_duplicates_without_invented_calls_and_preserves_test(self):
        config = load_config(); s = sample(); s["pool_age_hours"] = 1
        a = evaluate(s, config)
        data = {"paper": {"cash": 900, "trades": [{"pnl": -100}]}}
        original = copy.deepcopy(data["paper"])
        for time in (NOW, NOW + 300):
            research.observe(data, {s["key"]: s}, {s["key"]: a}, [], {}, config, time)
        window = data["research"]["window"]
        self.assertEqual((window["observations"], len(window["unique"]), window["calls"]), (2, 1, 0))
        self.assertEqual(data["paper"]["cash"], original["cash"])
        self.assertEqual(data["paper"]["trades"], original["trades"])
        self.assertEqual(len(data["paper"]["research_changes"]), 1)
        self.assertIn("par demasiado recente", research.view(data, NOW + 300))
        self.assertNotIn("<falso>", research.view(data, NOW + 300))
        self.assertIsNotNone(research.periodic(data, NOW + 300))
        self.assertIsNone(research.periodic(data, NOW + 600))
        research.observe(data, {s["key"]: s}, {s["key"]: a}, [], {}, config, NOW + 11100)
        self.assertIsNotNone(research.periodic(data, NOW + 11100))
        self.assertNotIn("Exemplos da última", research.view(data, NOW + 13000))

    def test_trending_mature_tokens_are_discovered_when_new_pools_fail(self):
        class Fake:
            def json(self, url):
                if "trending_pools" in url:
                    return {"included": [{"attributes": {"address": EVM}}]}
                raise ApiError("offline")
        market = Market(Fake())
        keys, errors = market.discover(["base"], 60)
        self.assertEqual(keys, ["base:" + EVM])
        self.assertTrue(errors)
        self.assertEqual(market.coverage["GeckoTerminal base tendências"], "disponível")

    def test_rotation_reaches_beyond_first_sample(self):
        class Fake:
            def json(self, url):
                if "dexscreener" in url: return []
                return {"included": [{"attributes": {"address": "0x" + f"{i:040x}"}} for i in range(5)]}
        market = Market(Fake())
        with patch("radar.market.time.time", return_value=0): first, _ = market.discover(["base"], 2)
        with patch("radar.market.time.time", return_value=300): second, _ = market.discover(["base"], 2)
        self.assertFalse(set(first) & set(second))


if __name__ == "__main__": unittest.main()
