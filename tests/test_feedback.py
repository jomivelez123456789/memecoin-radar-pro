import copy
import tempfile
import unittest
from pathlib import Path
from radar import entry_memory, learning, paper
from radar.app import scan, load_config
from radar.engine import evaluate
from radar.market import Market
from radar.state import State
from test_radar import NOW, EVM, sample, FakeMarket


class FeedbackTests(unittest.TestCase):
    def test_confirmation_exact_pair_gap_and_lost_filter_reset(self):
        d = {}; s = sample(); a = evaluate(s, load_config())
        self.assertTrue(entry_memory.check(d, s, a, NOW))
        self.assertTrue(entry_memory.check(d, s, a, NOW + 30))
        self.assertFalse(entry_memory.check(d, s, a, NOW + 300))
        self.assertTrue(entry_memory.check(d, s, a, NOW + 1000))
        bad = {**a, "entry": False}; entry_memory.check(d, s, bad, NOW + 1100)
        self.assertNotIn(s["key"], d["entry_memory"])
        self.assertTrue(entry_memory.check(d, s, a, NOW + 1300))
        s["pair"] = EVM
        self.assertTrue(entry_memory.check(d, s, a, NOW + 1600))

    def test_loss_memory_uses_only_closed_same_contract_and_past(self):
        s = sample(); a = evaluate(s, load_config()); d = {"paper": {"trades": []}}
        for at in (NOW - 100, NOW - 500):
            d["paper"]["trades"].append({"key": s["key"], "closed_at": at, "pnl": -10})
        entry_memory.check(d, s, a, NOW)
        self.assertIn("duas perdas", " ".join(entry_memory.check(d, s, a, NOW + 300)))
        for p in d["paper"]["trades"]: p["closed_at"] = NOW + 10000
        self.assertFalse(entry_memory.check(d, s, a, NOW + 600))

    def test_original_entry_recovered_once_only_on_unique_exact_history(self):
        s = sample(); p = {"key": s["key"], "opened_at": NOW}
        d = {"paper": {"trades": [p]}, "history": [{"category": "A", "key": s["key"], "at": NOW,
                                                     "snapshot": s, "analysis": {"entry": True}}]}
        self.assertEqual(learning.recover_entries(d, NOW + 100), 1)
        self.assertEqual(learning.recover_entries(d, NOW + 200), 0)
        self.assertEqual(p["entry_pair"], s["pair"])
        p.pop("entry_evidence"); d["history"].append(copy.deepcopy(d["history"][0]))
        self.assertEqual(learning.recover_entries(d, NOW + 200), 0)

    def test_pending_confirmation_kept_when_no_longer_discovered(self):
        class Disappearing(FakeMarket):
            def discover(self, chains, limit): return [], []
            def fetch(self, keys, now):
                self.asserted_keys = keys
                return super().fetch(keys, now)
        with tempfile.TemporaryDirectory() as directory:
            st = State(Path(directory)/"state.json"); config = load_config()
            scan(st, config, FakeMarket(), NOW)
            self.assertFalse(st.data["signaled"])
            market = Disappearing(); scan(st, config, market, NOW+300)
            self.assertIn(sample()["key"], market.asserted_keys)
            self.assertTrue(st.data["signaled"])

    def test_pinned_pair_does_not_switch_to_higher_liquidity_pool(self):
        original = "0x" + "1"*40; other = "0x" + "2"*40
        def pair(address, liquidity):
            return {"chainId": "base", "baseToken": {"address": EVM}, "pairAddress": address,
                    "priceUsd": "1", "liquidity": {"usd": liquidity}}
        class HTTP:
            def json(self, url): return [pair(other, 10000), pair(original, 100)]
        market = Market(HTTP()); market.preferred_pairs = {"base:"+EVM: original}
        snapshots, errors = market.fetch(["base:"+EVM], NOW)
        self.assertFalse(errors)
        self.assertEqual(snapshots["base:"+EVM]["pair"], original)

    def test_missing_pinned_pool_is_missing_quote_never_substitute_pool(self):
        original = "0x"+"1"*40; other = "0x"+"2"*40
        class HTTP:
            def json(self, url):
                if "/latest/dex/pairs/" in url: return {"pairs": None}
                return [{"chainId": "base", "baseToken": {"address": EVM}, "pairAddress": other, "priceUsd": "10"}]
        market = Market(HTTP()); market.preferred_pairs = {"base:"+EVM: original}
        snapshots, errors = market.fetch(["base:"+EVM], NOW)
        self.assertFalse(snapshots); self.assertEqual(errors, ["base:"+EVM])


if __name__ == "__main__": unittest.main()
