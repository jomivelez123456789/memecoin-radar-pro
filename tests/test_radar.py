import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from cryptography.fernet import Fernet, InvalidToken
from radar.app import load_config, scan, flush
from radar.commands import consume, process
from radar.engine import evaluate
from radar.http import Http, ApiError, NoRedirect
from radar.model import identity, links, normalize, number
from radar.market import Market
from radar.positions import register, close, estimate
from radar.state import State
from radar.telegram import Telegram, alert
from radar.cloud import CloudState

SOL = "So11111111111111111111111111111111111111112"
EVM = "0x4200000000000000000000000000000000000006"
NOW = 1800000000


def sample():
    return {"key": identity("solana", SOL), "chain": "solana", "address": SOL,
            "name": "Exemplo <falso>", "symbol": "TEST", "price": .01,
            "liquidity": 100000, "volume_h1": 40000, "volume_h24": 270000,
            "buys": 80, "sells": 20, "change_h1": 10, "change_h24": 20,
            "pool_age_hours": 24, "observed_at": NOW, "pair": SOL, "source": "teste"}


class FakeMarket:
    def __init__(self, s=None, missing=False):
        self.s = s or sample()
        self.missing = missing
    def discover(self, chains, limit):
        return [self.s["key"]], []
    def fetch(self, keys, now):
        return ({}, keys) if self.missing else ({self.s["key"]: self.s}, [])


class RadarTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = State(Path(self.temp.name) / "state.json")
        self.config = load_config()
    def tearDown(self):
        self.temp.cleanup()

    def test_healthy_market_entry(self):
        a = evaluate(sample(), self.config)
        self.assertTrue(a["entry"])
        self.assertEqual(a["score"], 100)
        self.assertEqual(a["relative_volume"], 4)
        self.assertIn("não auditado", a["risk_class"])

    def test_missing_fields_block_entry(self):
        for field in ("price", "liquidity", "volume_h1", "volume_h24", "buys", "sells", "change_h1", "pool_age_hours"):
            with self.subTest(field=field):
                s = sample(); s[field] = None
                self.assertFalse(evaluate(s, self.config)["entry"])

    def test_volume_no_history_blocks(self):
        s = sample(); s["volume_h24"] = s["volume_h1"]
        self.assertFalse(evaluate(s, self.config)["entry"])

    def test_low_liquidity_blocks(self):
        s = sample(); s["liquidity"] = 10
        a = evaluate(s, self.config)
        self.assertFalse(a["entry"]); self.assertTrue(a["risk"])

    def test_filter_boundaries(self):
        for field, value in (("pool_age_hours", 1), ("volume_h1", 100), ("buys", 1), ("change_h1", 1)):
            s = sample(); s[field] = value
            self.assertFalse(evaluate(s, self.config)["entry"])

    def test_exit_for_signaled_token(self):
        s = sample(); s["change_h1"] = -20
        self.assertTrue(evaluate(s, self.config, tracked=True)["exits"])

    def test_exit_stop_take_for_simulated_position(self):
        p = register(self.state.data, "simulada", "solana", SOL, .01, 1000, 1, .008, .014, NOW)
        for price in (.007, .015):
            s = sample(); s["price"] = price
            self.assertTrue(evaluate(s, self.config, positions=[p])["exits"])

    def test_liquidity_drop_same_pool(self):
        old, new = sample(), sample(); new["liquidity"] = 55000
        self.assertTrue(evaluate(new, self.config, old)["risk"])
        new["pair"] = EVM
        self.assertFalse(evaluate(new, self.config, old)["risk"])

    def test_extreme_rise_is_risk_not_entry(self):
        s = sample(); s["change_h1"] = 100
        a = evaluate(s, self.config, tracked=True)
        self.assertTrue(a["risk"]); self.assertFalse(a["entry"]); self.assertFalse(a["exits"])

    def test_identity_not_symbol(self):
        self.assertNotEqual(identity("base", EVM), identity("ethereum", EVM))
        self.assertEqual(identity("base", EVM.upper().replace("0X", "0x")), identity("base", EVM))

    def test_invalid_addresses(self):
        for chain, address in (("solana", "O" * 44), ("solana", "z" * 44), ("base", "0x123"), ("unknown", SOL), ("base", EVM + "/x")):
            with self.assertRaises(ValueError):
                identity(chain, address)

    def test_phantom_caip_networks(self):
        from urllib.parse import parse_qs, urlsplit
        for chain, address, prefix in (("solana", SOL, "solana:4sGj"), ("base", EVM, "eip155:8453/erc20:"), ("ethereum", EVM, "eip155:1/erc20:")):
            link = links(chain, address)
            token = parse_qs(urlsplit(link["app"]).query)["token"][0]
            self.assertTrue(token.startswith(prefix)); self.assertTrue(token.endswith(address))
            self.assertIn("dexscreener.com/" + chain + "/", link["chart"])

    def test_quote_identity_checked(self):
        pair = {"chainId": "base", "baseToken": {"address": EVM}, "priceUsd": "1"}
        self.assertIsNone(normalize(pair, "solana", SOL, NOW))
        self.assertIsNotNone(normalize(pair, "base", EVM, NOW))
        pair["baseToken"]["address"] = "0x" + "1" * 40
        self.assertIsNone(normalize(pair, "base", EVM, NOW))

    def test_missing_age_never_zero(self):
        pair = {"chainId": "base", "baseToken": {"address": EVM}, "priceUsd": "0"}
        s = normalize(pair, "base", EVM, NOW)
        self.assertIsNone(s["price"]); self.assertIsNone(s["pool_age_hours"])

    def test_nonfinite_input_rejected(self):
        for value in ("nan", "inf", "-inf", True, None):
            self.assertIsNone(number(value))

    def test_roundtrip_state(self):
        self.state.data["watched"] = [identity("base", EVM)]
        self.state.save()
        self.assertEqual(State(self.state.path).data, self.state.data)

    def test_corrupt_state_fails_closed(self):
        self.state.path.write_text("{}")
        with self.assertRaises(ValueError): State(self.state.path)

    def test_lock_prevents_concurrent_writes(self):
        with self.state.lock():
            with self.assertRaises(FileExistsError):
                with self.state.lock(): pass

    def test_scan_cooldown_persists(self):
        scan(self.state, self.config, FakeMarket(), NOW)
        n = len(self.state.data["outbox"])
        restored = State(self.state.path)
        scan(restored, self.config, FakeMarket(), NOW + 900)
        self.assertEqual(len(restored.data["outbox"]), n)
        self.assertEqual(len(restored.data["history"]), 1)

    def test_scan_dry_run_does_not_queue_or_set_cooldown(self):
        scan(self.state, self.config, FakeMarket(), NOW, dry=True)
        self.assertFalse(self.state.data["outbox"])
        self.assertFalse(self.state.data["cooldowns"])

    def test_signal_never_implies_ownership(self):
        scan(self.state, self.config, FakeMarket(), NOW)
        self.assertFalse(self.state.data["positions"])
        self.assertTrue(self.state.data["signaled"])

    def test_scan_exit_alert(self):
        key = sample()["key"]; self.state.data["signaled"][key] = NOW
        s = sample(); s["change_h1"] = -30
        scan(self.state, self.config, FakeMarket(s), NOW + 900)
        self.assertTrue(self.state.data["history"][0]["category"].startswith("B"))

    def test_scan_risk_alert(self):
        self.state.data["watched"].append(sample()["key"])
        s = sample(); s["change_h1"] = 100
        scan(self.state, self.config, FakeMarket(s), NOW)
        self.assertTrue(self.state.data["history"][0]["category"].startswith("C"))

    def test_no_market_data_is_failure_not_zero(self):
        self.state.data["watched"].append(sample()["key"])
        with self.assertRaises(ApiError): scan(self.state, self.config, FakeMarket(missing=True), NOW)
        self.assertFalse(self.state.data["snapshots"])
        self.assertTrue(self.state.data["outbox"])

    def test_partial_sale_pnl(self):
        p = register(self.state.data, "simulada", "base", EVM, 2, 10, 1, 1, 3, NOW)
        _, pnl = close(self.state.data, p["id"], 3, 4, .2, NOW + 100)
        self.assertAlmostEqual(pnl, 3.4); self.assertEqual(p["remaining"], 6)
        self.assertAlmostEqual(estimate(p, 3), 5.4)
        self.assertEqual(p["mode"], "simulada")

    def test_oversell_and_invalid_thresholds(self):
        with self.assertRaises(ValueError): register(self.state.data, "simulada", "base", EVM, 2, 1, 0, 3, 4, NOW)
        p = register(self.state.data, "real", "base", EVM, 2, 1, 0, 1, 4, NOW)
        with self.assertRaises(ValueError): close(self.state.data, p["id"], 3, 2, 0, NOW)

    def test_authorized_chat_and_user(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test", "TELEGRAM_CHAT_ID": "123", "TELEGRAM_USER_ID": "123"}):
            bot = Telegram(Http())
        msg = {"chat": {"id": 123, "type": "private"}, "from": {"id": 123}}
        self.assertTrue(bot.authorized(msg))
        msg["from"]["id"] = 124; self.assertFalse(bot.authorized(msg))
        msg["from"]["id"] = 123; msg["chat"]["type"] = "group"; self.assertFalse(bot.authorized(msg))

    def test_command_offset_and_position_idempotency(self):
        msg = {"update_id": 5, "message": {"date": NOW,
               "text": f"/simulate base {EVM} 2 10 1 1 4"}}
        class Bot:
            def updates(self, offset): return [msg]
            def authorized(self, message): return True
        consume(Bot(), self.state, self.config, NOW)
        consume(Bot(), self.state, self.config, NOW)
        self.assertEqual(len(self.state.data["positions"]), 1)
        self.assertEqual(self.state.data["offset"], 6)

    def test_unauthorized_command_has_no_effect(self):
        class Bot:
            def updates(self, offset): return [{"update_id": 1, "message": {"date": NOW, "text": f"/watch base {EVM}"}}]
            def authorized(self, message): return False
        consume(Bot(), self.state, self.config, NOW)
        self.assertFalse(self.state.data["watched"])

    def test_outbox_retry_and_success(self):
        self.state.data["outbox"] = [{"text": "exemplo"}]
        class Fail:
            def send(self, *args): raise ApiError("Falha")
        with self.assertRaises(ApiError): flush(self.state, Fail())
        self.assertEqual(len(self.state.data["outbox"]), 1)
        class Ok:
            def send(self, *args): return {"message_id": 1}
        flush(self.state, Ok()); self.assertFalse(self.state.data["outbox"])

    def test_alert_escapes_token_names(self):
        s = sample(); msg = alert(s, evaluate(s, self.config), "A", ["<spam>"], self.config)
        self.assertIn("&lt;falso&gt;", msg["text"])
        self.assertNotIn("<spam>", msg["text"])
        self.assertLess(len(msg["text"]), 4096)
        self.assertEqual(msg["buttons"][1][0]["copy_text"]["text"], SOL)

    def test_http_rejects_unapproved_destination(self):
        for url in ("http://api.telegram.org/a", "https://evil.example/a"):
            with self.assertRaises(ApiError): Http().json(url)

    def test_redirects_disabled(self):
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.example"))

    def test_cloud_authenticated_encryption_and_tamper(self):
        cipher = Fernet(Fernet.generate_key())
        encrypted = cipher.encrypt(b'{"position":"private"}')
        self.assertNotIn(b"private", encrypted)
        self.assertEqual(cipher.decrypt(encrypted), b'{"position":"private"}')
        with self.assertRaises(InvalidToken): Fernet(Fernet.generate_key()).decrypt(encrypted)

    def test_cloud_refuses_private_repo(self):
        class Fake:
            def json(self, *args, **kwargs): return {"private": True}
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "a/b", "GITHUB_TOKEN": "test", "RADAR_STATE_KEY": Fernet.generate_key().decode()}):
            cloud = CloudState(Fake())
        with self.assertRaises(ValueError): cloud.restore(self.state.path)

    def test_cloud_missing_state_fails_without_explicit_initialize(self):
        class Fake:
            def json(self, url, *args, **kwargs):
                if url.endswith("a/b"): return {"private": False}
                raise ApiError("api.github.com: HTTP 404")
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "a/b", "GITHUB_TOKEN": "test", "RADAR_STATE_KEY": Fernet.generate_key().decode()}):
            cloud = CloudState(Fake())
        with self.assertRaises(ApiError): cloud.restore(self.state.path)

    def test_public_workflow_has_no_paid_storage_or_pr_secrets(self):
        workflow = Path(".github/workflows/radar.yml").read_text()
        self.assertNotIn("upload-artifact", workflow); self.assertNotIn("actions/cache", workflow)
        self.assertNotIn("pull_request", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertIn("cron: '7,22,37,52 * * * *'", workflow)

    def test_pool_younger_than_day_has_no_full_volume_baseline(self):
        s = sample(); s["pool_age_hours"] = 10
        a = evaluate(s, self.config)
        self.assertFalse(a["entry"]); self.assertIsNone(a["relative_volume"])

    def test_market_selects_largest_matching_base_pair(self):
        def pair(address, liquidity, chain="base"):
            return {"chainId": chain, "baseToken": {"address": address},
                    "liquidity": {"usd": liquidity}, "priceUsd": "2"}
        class Fake:
            def json(self, url): return [pair(EVM, 10), pair(EVM, 100), pair(EVM, 9999, "ethereum")]
        key = identity("base", EVM)
        snapshots, errors = Market(Fake()).fetch([key], NOW)
        self.assertEqual(snapshots[key]["liquidity"], 100); self.assertFalse(errors)

    def test_market_batches_at_thirty(self):
        class Fake:
            def __init__(self): self.calls = []
            def json(self, url): self.calls.append(url); return []
        fake = Fake()
        keys = [identity("base", "0x" + f"{i:040x}") for i in range(31)]
        _, errors = Market(fake).fetch(keys, NOW)
        self.assertEqual(len(fake.calls), 2); self.assertEqual(len(errors), 31)

    def test_discovery_interleaves_networks_and_sources(self):
        class Fake:
            def json(self, url):
                if "dexscreener" in url:
                    return [{"chainId": "solana", "tokenAddress": SOL}]
                if "/base/" in url:
                    return {"included": [{"attributes": {"address": EVM}}]}
                return {"included": []}
        discovered, errors = Market(Fake()).discover(["solana", "base"], 2)
        self.assertEqual(set(discovered), {identity("solana", SOL), identity("base", EVM)})
        self.assertFalse(errors)

    def test_stale_command_not_executed(self):
        class Bot:
            def updates(self, offset): return [{"update_id": 2, "message": {"date": NOW - 90000, "text": f"/watch base {EVM}"}}]
            def authorized(self, message): return True
        consume(Bot(), self.state, self.config, NOW)
        self.assertFalse(self.state.data["watched"])

    def test_command_requires_explicit_real_mode(self):
        with self.assertRaises(ValueError):
            process(f"/register base {EVM} 2 10 1 1 4", self.state, self.config, NOW)
        self.assertFalse(self.state.data["positions"])

    def test_closed_position_does_not_trigger_exit_levels(self):
        p = register(self.state.data, "simulada", "solana", SOL, .01, 100, 0, .008, .014, NOW)
        close(self.state.data, p["id"], .01, 100, 0, NOW)
        s = sample(); s["price"] = .02
        scan(self.state, self.config, FakeMarket(s), NOW)
        self.assertFalse(any(h["category"].startswith("B") for h in self.state.data["history"]))

    def test_cloud_roundtrip_and_wrong_key_fail_closed(self):
        class Fake:
            def __init__(self): self.file = None
            def json(self, url, payload=None, headers=None, method=None, retry=True):
                if url.endswith("a/b"): return {"private": False}
                if method == "PUT":
                    self.file = {"sha": "saved", "content": payload["content"]}
                    return {"content": {"sha": "saved"}}
                return self.file
        fake = Fake()
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "a/b", "GITHUB_TOKEN": "test", "RADAR_STATE_KEY": Fernet.generate_key().decode()}):
            cloud = CloudState(fake)
        register(self.state.data, "simulada", "base", EVM, 2, 10, 1, 1, 4, NOW)
        self.state.save(); cloud.save(self.state.path)
        output = Path(self.temp.name) / "restored.json"
        cloud.restore(output)
        self.assertEqual(State(output).data, self.state.data)
        self.assertNotIn("simulada", fake.file["content"])
        cloud.cipher = Fernet(Fernet.generate_key())
        with self.assertRaises(InvalidToken): cloud.restore(output)

    def test_http_error_does_not_reveal_token_url(self):
        import urllib.error
        class FakeOpener:
            def open(self, request, timeout):
                raise urllib.error.HTTPError("https://api.telegram.org/botSECRET/getMe", 401, "secret-body", {}, None)
        with patch("urllib.request.build_opener", return_value=FakeOpener()):
            with self.assertRaises(ApiError) as caught:
                Http().json("https://api.telegram.org/botSECRET/getMe")
        self.assertNotIn("SECRET", str(caught.exception)); self.assertNotIn("secret-body", str(caught.exception))

    def test_http_rate_limit_retried_with_bounded_wait(self):
        import urllib.error
        class FakeOpener:
            def __init__(self): self.calls = 0
            def open(self, request, timeout):
                self.calls += 1
                raise urllib.error.HTTPError(request.full_url, 429, "", {"Retry-After": "999999"}, None)
        fake = FakeOpener()
        with patch("urllib.request.build_opener", return_value=fake), patch("time.sleep") as sleeper:
            with self.assertRaises(ApiError): Http().json("https://api.dexscreener.com/a")
        self.assertEqual(fake.calls, 3)
        self.assertTrue(all(call.args[0] <= 30 for call in sleeper.call_args_list))

    def test_expired_market_alert_not_delivered(self):
        self.state.data["outbox"] = [{"text": "A sinal antigo", "expires_at": 1}]
        class Bot:
            def send(self, *args): raise AssertionError("Não deve enviar sinal expirado")
        flush(self.state, Bot())
        self.assertFalse(self.state.data["outbox"])


if __name__ == "__main__":
    unittest.main()
