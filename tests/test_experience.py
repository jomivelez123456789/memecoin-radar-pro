import copy
import html
import os
import tempfile
import unittest
from email.utils import formatdate
from pathlib import Path
from unittest.mock import patch
from radar.app import load_config, scan
from radar.commands import consume, process, enqueue
from radar.education import page
from radar.engine import evaluate
from radar.forms import callback, begin, reply, values
from radar.http import ApiError, Http
from radar.model import identity
from radar.news import parse_feed, refresh, correlate, news_view, FEEDS
from radar.positions import register
from radar.state import State
from radar.telegram import Telegram, alert
from radar.views import token_ref, position_message, money
from test_radar import sample, FakeMarket, NOW, SOL, EVM


class ExperienceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = State(Path(self.temp.name) / "state.json")
        self.config = load_config()
        self.s = sample()
        self.state.data["snapshots"][self.s["key"]] = self.s

    def tearDown(self):
        self.temp.cleanup()

    def position(self):
        return register(self.state.data, "simulada", "solana", SOL, .01, 100, 0, .008, .014, NOW)

    def test_help_is_plain_language_and_links_to_steps(self):
        message = process("/ajuda", self.state, self.config, NOW)
        self.assertIn("/depositar", message["text"])
        self.assertIn("/retirar", message["text"])
        self.assertIn("TODAS", message["text"])
        self.assertIn("não ordens", page("saidas"))

    def test_watch_button_never_registers_purchase(self):
        callback("watch:" + token_ref(self.s["key"]), self.state, self.config, NOW)
        self.assertEqual(self.state.data["watched"], [self.s["key"]])
        self.assertFalse(self.state.data["positions"])

    def test_expired_token_button_does_not_pick_similar_name(self):
        result = callback("buy:ffffffffffff", self.state, self.config, NOW)
        self.assertIn("antiga", result["text"])
        self.assertNotIn("form", self.state.data)

    def test_form_portuguese_decimals_and_labels(self):
        begin(self.state.data, "sim", NOW, key=self.s["key"])
        result = reply(self.state.data, "Preço: 0,01\nQuantidade: 100\nTaxa: 0,10\nLimite: 0,008\nObjetivo: 0,014", NOW)
        self.assertIn("SIMULAÇÃO", result["text"])
        self.assertEqual(self.state.data["positions"][0]["entry_fee"], .1)
        self.assertNotIn("form", self.state.data)

    def test_real_registration_requires_explicit_real_path(self):
        callback("buy:" + token_ref(self.s["key"]), self.state, self.config, NOW)
        reply(self.state.data, ".01 100 0 .008 .014", NOW)
        self.assertEqual(self.state.data["positions"][0]["mode"], "real")

    def test_invalid_form_is_atomic_and_keeps_form(self):
        begin(self.state.data, "sim", NOW, key=self.s["key"])
        for text in (".01 100 0 .02 .03", ".01 -1 0 .008 .014", "nan 100 0 .008 .014", "1e308 1e308 0 1 1e309"):
            result = reply(self.state.data, text, NOW)
            self.assertIn("Não consegui", result["text"])
            self.assertFalse(self.state.data["positions"])
            self.assertIn("form", self.state.data)

    def test_old_cancel_button_does_not_cancel_current_form(self):
        begin(self.state.data, "sim", NOW, key=self.s["key"])
        previous = self.state.data["form"]["nonce"]
        begin(self.state.data, "buy", NOW, key=self.s["key"])
        callback("cancel:" + previous, self.state, self.config, NOW)
        self.assertEqual(self.state.data["form"]["kind"], "buy")

    def test_expired_form_does_not_create_position(self):
        begin(self.state.data, "sim", NOW, key=self.s["key"])
        reply(self.state.data, ".01 100 0 .008 .014", NOW + 86401)
        self.assertFalse(self.state.data["positions"])

    def test_form_sale_partial_then_full(self):
        p = self.position()
        for quantity in (40, 60):
            begin(self.state.data, "sell", NOW, position_id=p["id"])
            reply(self.state.data, f".012 {quantity} 0", NOW)
        self.assertEqual(p["remaining"], 0)
        self.assertAlmostEqual(p["realized_pnl"], .2)

    def test_oversell_form_does_not_mutate_balance(self):
        p = self.position()
        begin(self.state.data, "sell", NOW, position_id=p["id"])
        reply(self.state.data, ".012 101 0", NOW)
        self.assertEqual(p["remaining"], 100)

    def test_levels_can_lock_profit_without_recommending_levels(self):
        p = self.position()
        begin(self.state.data, "levels", NOW, position_id=p["id"])
        reply(self.state.data, ".011 .02", NOW)
        self.assertEqual(p["stop"], .011)
        self.assertEqual(p["levels_updated_at"], NOW)

    def test_registration_and_plain_form_reply_are_idempotent(self):
        messages = [{"update_id": 11, "callback_query": {"id": "q", "data": "sim:" + token_ref(self.s["key"]),
            "from": {"id": 1}, "message": {"chat": {"id": 1, "type": "private"}}}},
            {"update_id": 12, "message": {"date": NOW, "text": ".01 100 0 .008 .014"}}]
        class Bot:
            def updates(self, offset): return messages
            def authorized(self, message): return True
            def answer(self, callback_id): raise ApiError("callback demasiado antigo")
        consume(Bot(), self.state, self.config, NOW)
        consume(Bot(), self.state, self.config, NOW)
        self.assertEqual(len(self.state.data["positions"]), 1)
        self.assertEqual(self.state.data["offset"], 13)

    def test_unauthorized_callback_has_no_effect(self):
        class Bot:
            def updates(self, offset): return [{"update_id": 1, "callback_query": {"id": "q", "data": "sim:" + token_ref(sample()["key"]), "from": {}, "message": {}}}]
            def authorized(self, message): return False
        consume(Bot(), self.state, self.config, NOW)
        self.assertNotIn("form", self.state.data)

    def test_old_state_works_without_migration_reset(self):
        self.state.save()
        restored = State(self.state.path)
        callback("sim:" + token_ref(self.s["key"]), restored, self.config, NOW)
        restored.save()
        self.assertEqual(State(self.state.path).data["form"]["kind"], "sim")

    def test_each_position_has_independent_exit_cooldown(self):
        p1, p2 = self.position(), self.position()
        s = sample(); s["price"] = .007
        self.state.data["cooldowns"]["B:" + s["key"]] = NOW
        scan(self.state, self.config, FakeMarket(s), NOW + 900)
        exits = [h for h in self.state.data["history"] if h["category"].startswith("B")]
        self.assertEqual({h["position_id"] for h in exits}, {p1["id"], p2["id"]})
        self.assertTrue(all(h["position_mode"] == "simulada" for h in exits))

    def test_take_after_stop_not_hidden_by_same_token_cooldown(self):
        self.position()
        s = sample(); s["price"] = .007
        scan(self.state, self.config, FakeMarket(s), NOW)
        s = sample(); s["price"] = .015
        scan(self.state, self.config, FakeMarket(s), NOW + 900)
        self.assertEqual(len([h for h in self.state.data["history"] if h["category"].startswith("B")]), 2)

    def test_open_positions_get_periodic_updates_without_spam(self):
        p = self.position()
        scan(self.state, self.config, FakeMarket(), NOW + 21601)
        n = len(self.state.data["outbox"])
        scan(self.state, self.config, FakeMarket(), NOW + 21901)
        self.assertEqual(len(self.state.data["outbox"]), n)
        self.assertEqual(p["last_update_at"], NOW + 21601)

    def test_many_other_signals_cannot_evict_owned_position(self):
        p = self.position()
        for index in range(150):
            self.state.data["signaled"][identity("base", "0x" + f"{index:040x}")] = NOW
        class Capture(FakeMarket):
            def fetch(self, keys, now):
                self.keys = keys
                return super().fetch(keys, now)
        market = Capture()
        scan(self.state, self.config, market, NOW)
        self.assertIn(p["key"], market.keys)
        self.assertLessEqual(len(market.keys), self.config["max_tracked_tokens"])

    def test_risk_alert_for_owned_position_identifies_its_mode(self):
        self.position()
        s = sample(); s["change_h1"] = 100
        scan(self.state, self.config, FakeMarket(s), NOW)
        messages = self.state.data["outbox"]
        self.assertTrue(any("risco na tua posição" in m["text"] and "SIMULAÇÃO" in m["text"] for m in messages))

    def test_closed_positions_have_no_periodic_update(self):
        p = self.position(); p["remaining"] = 0
        s = sample(); s["change_h1"] = 0
        scan(self.state, self.config, FakeMarket(s), NOW + 86400)
        self.assertNotIn("last_update_at", p)

    def test_position_view_explains_mode_and_has_sale_help(self):
        p = self.position()
        result = position_message(p, sample())
        self.assertIn("SIMULAÇÃO", result["text"])
        self.assertIn("limite de perda", result["text"])
        self.assertIn("O radar não vendeu nada", result["text"])
        self.assertTrue(any(b.get("callback_data") == "sell:" + p["id"] for row in result["buttons"] for b in row))

    def test_new_alerts_are_readable_escaped_and_have_bounded_callbacks(self):
        result = alert(self.s, evaluate(self.s, self.config), "A", [], self.config)
        self.assertIn("Em palavras simples", result["text"])
        self.assertNotIn("RVOL:", result["text"])
        self.assertNotIn("Score:", result["text"])
        self.assertIn("&lt;falso&gt;", result["text"])
        self.assertLess(len(result["text"].encode("utf-16-le")) // 2, 4096)
        self.assertTrue(all(len(b.get("callback_data", "").encode()) <= 64 for row in result["buttons"] for b in row))

    def test_tiny_prices_are_not_displayed_as_zero(self):
        self.assertNotEqual(money(.00000000123), "0,00 USD")

    def test_position_cards_are_queued_separately(self):
        self.position(); self.position()
        result = process("/posicoes", self.state, self.config, NOW)
        enqueue(self.state, result)
        self.assertEqual(len(self.state.data["outbox"]), 3)

    def test_update_api_requests_callbacks_too(self):
        class Fake:
            def json(self, url, payload, **kwargs):
                self.payload = payload; return {"ok": True, "result": []}
        fake = Fake()
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test", "TELEGRAM_CHAT_ID": "1"}):
            Telegram(fake).updates(1)
        self.assertIn("callback_query", fake.payload["allowed_updates"])


def feed(title="Notícia", description="", url="https://cointelegraph.com/news/test", date=NOW):
    return ("<rss><channel><item><title>" + html.escape(title) + "</title><description>" + html.escape(description)
            + "</description><link>" + html.escape(url) + "</link><pubDate>" + formatdate(date, usegmt=True)
            + "</pubDate></item></channel></rss>")


class NewsTests(unittest.TestCase):
    def setUp(self): self.config = load_config()
    def parse(self, content): return parse_feed(content, "Cointelegraph", {"cointelegraph.com"}, NOW)

    def test_rejects_xml_entities(self):
        with self.assertRaises(ValueError): self.parse('<!DOCTYPE rss [<!ENTITY secret "x">]><rss/>')

    def test_rejects_official_lookalike_or_unsafe_links(self):
        for url in ("https://cointelegraph.com.evil.example/x", "javascript:alert(1)", "https://user@cointelegraph.com/x", "https://cointelegraph.com:444/x"):
            self.assertFalse(self.parse(feed(url=url)))

    def test_rejects_future_or_ancient_news(self):
        self.assertFalse(self.parse(feed(date=NOW + 3600)))
        self.assertFalse(self.parse(feed(date=NOW - 3 * 86400)))

    def test_same_symbol_does_not_associate_token(self):
        items = self.parse(feed(title="TEST rises on Solana"))
        self.assertFalse(items[0]["mentions"])
        self.assertFalse(correlate({"news": {"items": items}}, {sample()["key"]: sample()}, self.config, NOW))

    def test_contract_without_network_does_not_associate(self):
        self.assertFalse(self.parse(feed(description=EVM))[0]["mentions"])

    def test_wrong_chain_is_not_same_asset(self):
        items = self.parse(feed(description="Ethereum token " + EVM))
        self.assertIn(identity("ethereum", EVM), items[0]["mentions"])
        self.assertNotIn(identity("base", EVM), items[0]["mentions"])

    def test_exact_contract_network_and_activity_emit_context_once(self):
        items = self.parse(feed(description="Solana token " + SOL))
        data = {"news": {"items": items, "alerted": {}}}
        s = sample()
        first = correlate(data, {s["key"]: s}, self.config, NOW)
        self.assertEqual(len(first), 1)
        self.assertIn("NÃO prova", first[0]["text"])
        self.assertFalse(correlate(data, {s["key"]: s}, self.config, NOW + 10))

    def test_news_never_overrides_market_risk(self):
        items = self.parse(feed(description="Solana token " + SOL))
        s = sample(); s["liquidity"] = 1
        self.assertFalse(correlate({"news": {"items": items}}, {s["key"]: s}, self.config, NOW))

    def test_news_caches_and_does_not_repeatedly_fetch(self):
        class Fake:
            def __init__(self): self.calls = 0
            def text(self, url): self.calls += 1; return feed()
        fake, data = Fake(), {}
        refresh(data, fake, NOW); refresh(data, fake, NOW + 300)
        self.assertEqual(fake.calls, len(FEEDS))

    def test_feed_failure_is_explicit_and_does_not_stop_market(self):
        class Fake:
            def text(self, url): raise ApiError("indisponível")
        with tempfile.TemporaryDirectory() as directory:
            state = State(Path(directory) / "state.json")
            result = scan(state, self.config, FakeMarket(), NOW, news_http=Fake())
            self.assertEqual(result["observations"], 1)
            self.assertIn("indisponível", news_view(state.data, NOW))


if __name__ == "__main__": unittest.main()
