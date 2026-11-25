import copy
import json
import unittest
from datetime import datetime, timezone
from radar import learning, social, paper
from radar.http import ApiError
from test_radar import NOW, sample


class LearningTests(unittest.TestCase):
    def test_no_trades_no_invented_lesson(self):
        d = {"positions": [{"realized_pnl": 10000}]}
        self.assertIsNone(learning.review(d, NOW))
        self.assertIn("Ainda não há resultados", learning.view(d, NOW))

    def test_losses_costs_gaps_and_versions_preserved_and_review_once(self):
        d = {"paper": {"cash": 950, "trades": [
            {"name": "<fake>", "closed_at": NOW, "pnl": -15, "entry_quote_eur": 1,
             "exit_quote_eur": .9, "budget": 100, "monitoring_gap": True, "research_version": "v1"},
            {"name": "winner", "closed_at": NOW, "pnl": 10, "entry_quote_eur": 1,
             "exit_quote_eur": 1.15, "budget": 100, "entry_evidence": {"checks": {}}, "research_version": "v2"},
            {"name": "open", "closed_at": None}]}}
        old = copy.deepcopy(d)
        self.assertIsNotNone(learning.review(d, NOW))
        self.assertIsNone(learning.review(d, NOW + 1))
        trades = d["paper"]["trades"]
        self.assertEqual(trades[0]["review"]["outcome"], "perda")
        self.assertAlmostEqual(trades[0]["review"]["cost_drag_eur"], 5)
        self.assertNotIn("review", trades[2])
        self.assertEqual(d["paper"]["cash"], old["paper"]["cash"])
        self.assertEqual([p.get("pnl") for p in trades], [p.get("pnl") for p in old["paper"]["trades"]])
        text = learning.view(d, NOW)
        self.assertIn("2 versão", text); self.assertIn("1 com perda", text)
        self.assertNotIn("<fake>", text)

    def test_incidents_separate_and_sanitized_bounded(self):
        d = {}
        for i in range(205): learning.incident(d, NOW, "falha da execução", "secret.example", 500)
        self.assertEqual(len(d["learning"]["incidents"]), 200)
        self.assertNotIn("secret.example", str(d))
        self.assertIn("200", learning.view(d, NOW))
        self.assertIsNone(learning.review(d, NOW))

    def test_entry_records_frozen_evidence(self):
        d = {"snapshots": {}, "fx": {"usd_per_eur": 1, "date_at": NOW//86400*86400}}
        paper.start(d, NOW); s = sample(); s["price"] = 1
        a = {"risk": [], "checks": {"test": True}}
        paper.step(d, {s["key"]: s}, {s["key"]: a}, [s["key"]], NOW)
        p = paper.opened(d)[0]
        s["price"] = 2; a["checks"]["test"] = False
        self.assertEqual(p["entry_evidence"]["snapshot"]["price"], 1)
        self.assertTrue(p["entry_evidence"]["analysis"]["checks"]["test"])


class SocialTests(unittest.TestCase):
    def test_html_app_shell_is_not_a_successful_feed(self):
        text = '<!DOCTYPE html><script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">{"__DEFAULT_SCOPE__":{"config":{}}}</script>'
        self.assertFalse(social.parse(text, "TikTok #memecoin", NOW))

    def test_tiktok_public_posts_identity_and_freshness(self):
        post = {"id": "1234567890123456789", "author": {"uniqueId": "public.author"}, "desc": "<pump>", "createTime": NOW}
        def page(p): return '<script id="SIGI_STATE">' + json.dumps({"ItemModule": {"item": p}}) + '</script>'
        items = social.parse(page(post), "TikTok #memecoin", NOW)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://www.tiktok.com/@public.author/video/1234567890123456789")
        for changes in ({"createTime": NOW + 1000}, {"createTime": NOW - 3*86400}, {"author": {"uniqueId": "evil/x"}}, {"id": "javascript:bad"}):
            self.assertFalse(social.parse(page({**post, **changes}), "TikTok #memecoin", NOW))

    def test_reddit_post_and_foreign_links_rejected(self):
        date = datetime.fromtimestamp(NOW, timezone.utc).isoformat()
        template = '<shreddit-post post-title="Public title" permalink="{}" created-timestamp="' + date + '"></shreddit-post>'
        self.assertEqual(len(social.parse(template.format('/r/solana/comments/abc123/topic/'), "Reddit r/solana", NOW)), 1)
        for path in ('https://evil.example/', '/r/other/comments/abc123/topic/', '//evil.example/'):
            self.assertFalse(social.parse(template.format(path), "Reddit r/solana", NOW))

    def test_failures_do_not_fake_posts_or_repeat_requests(self):
        class Fake:
            calls = 0
            def json(self, url, **kwargs):
                self.calls += 1
                self.assertion = kwargs["retry"]
                raise ApiError("private URL not retained", status=429)
        h, d = Fake(), {}
        social.refresh(d, h, NOW); social.refresh(d, h, NOW + 300)
        self.assertEqual(h.calls, len(social.PAGES) + len(social.PREVIEWS)); self.assertFalse(h.assertion)
        self.assertEqual(d["social"]["items"], [])
        self.assertTrue(all("429" in s for s in d["social"]["sources"].values()))
        self.assertNotIn("private URL", str(d))
        self.assertIn("indisponível", social.view(d, NOW))

    def test_reddit_provider_identity_timestamps_and_urls(self):
        p = {"subreddit": "r/solana", "updated": datetime.fromtimestamp(NOW, timezone.utc).isoformat(),
             "newest_posts": [{"title": "Public preview", "created_utc": NOW,
                                "url": "https://www.reddit.com/r/solana/comments/abc123/topic/"}]}
        items, updated = social.reddit_preview(p, "solana", NOW)
        self.assertEqual(len(items), 1); self.assertEqual(updated, NOW)
        for invalid in ({**p, "subreddit": "r/other"}, {**p, "updated": "2020-01-01T00:00:00Z"}):
            with self.assertRaises(ValueError): social.reddit_preview(invalid, "solana", NOW)
        p["newest_posts"][0]["url"] = "https://www.reddit.com@evil.example/r/solana/comments/abc123/topic/"
        self.assertEqual(social.reddit_preview(p, "solana", NOW)[0], [])

    def test_x_login_page_is_not_posts_but_valid_public_structured_post_is(self):
        self.assertEqual(social.parse('<html><h1>Sign in</h1></html>', "X Coin Bureau", NOW), [])
        p = {"@type": "SocialMediaPosting", "headline": "Public crypto opinion", "url": "https://x.com/coinbureau/status/123456789",
             "datePublished": datetime.fromtimestamp(NOW, timezone.utc).isoformat()}
        doc = '<script type="application/ld+json">' + json.dumps(p) + '</script>'
        self.assertEqual(len(social.parse(doc, "X Coin Bureau", NOW)), 1)

    def test_x_public_serialized_json_checks_author_date_and_never_executes_js(self):
        post = {"rest_id": "1234567890123456789", "details": {"full_text": "Public opinion", "created_at_ms": NOW*1000},
                "core": {"user_results": {"result": {"core": {"screen_name": "coinbureau"}}}}}
        def document(item):
            return '<script>untrustedCode();var payload=' + json.dumps(json.dumps({"data": item})) + ';</script>'
        self.assertEqual(len(social.parse(document(post), "X Coin Bureau", NOW)), 1)
        post["core"]["user_results"]["result"]["core"]["screen_name"] = "other"
        self.assertEqual(social.parse(document(post), "X Coin Bureau", NOW), [])
        post["core"]["user_results"]["result"]["core"]["screen_name"] = "coinbureau"
        post["details"]["created_at_ms"] = (NOW - 3*86400)*1000
        self.assertEqual(social.parse(document(post), "X Coin Bureau", NOW), [])


if __name__ == "__main__": unittest.main()
