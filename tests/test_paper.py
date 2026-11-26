import base64
import copy
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from cryptography.fernet import Fernet
from radar import paper, fx
from radar.app import scan, load_config
from radar.cloud import CloudState, safe_failure
from radar.commands import process
from radar.http import ApiError
from radar.state import State
from test_radar import sample, FakeMarket, NOW


class PaperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = State(Path(self.temp.name)/"state.json")
        self.d = self.state.data
        self.config = load_config()
        self.d["fx"] = {"usd_per_eur": 1.25, "date_at": NOW//86400*86400,
                        "date": datetime.fromtimestamp(NOW, timezone.utc).strftime("%Y-%m-%d")}
        self.s = sample(); self.s["price"] = 1.25
        paper.start(self.d, NOW)

    def tearDown(self):
        self.temp.cleanup()

    def tick(self, price=1.25, at=NOW, call=False):
        s = {**self.s, "price": price, "observed_at": at}
        self.d["snapshots"][s["key"]] = s
        return paper.step(self.d, {s["key"]: s}, {s["key"]: {"risk": []}}, [s["key"]] if call else [], at)

    def test_initial_euros_no_fake_wins_and_no_old_manual_examples(self):
        self.d["positions"].append({"realized_pnl": 9999, "remaining": 0})
        s = paper.statistics(self.d, NOW)
        self.assertEqual(s["equity"], 1000)
        self.assertIsNone(s["win_rate"])
        self.assertEqual(s["closed"], 0)
        self.assertIn("sem calls fechadas", paper.report(self.d, NOW))
        self.assertIn("€", paper.report(self.d, NOW))

    def test_entry_budget_includes_fees_and_slippage(self):
        self.tick(call=True)
        p = paper.opened(self.d)[0]; r = self.d["paper"]["rules"]
        self.assertEqual(self.d["paper"]["cash"], 900)
        self.assertAlmostEqual(p["quantity"] * p["entry_fill_eur"] * (1+r["fee"]) + r["fixed_fee"], 100)
        self.assertAlmostEqual(p["entry_quote_eur"], 1)
        self.assertEqual(self.d["positions"], [])
        self.assertLess(paper.statistics(self.d, NOW)["equity"], 1000)

    def test_one_profitable_call_is_100_percent_accuracy_not_return(self):
        self.tick(call=True); self.tick(1.25*1.25, NOW+300)
        s = paper.statistics(self.d, NOW+300)
        self.assertEqual(s["win_rate"], 100)
        self.assertEqual(s["wins"], 1)
        self.assertGreater(s["return"], 0)
        self.assertLess(s["return"], 3)
        self.assertAlmostEqual(s["equity"], 1000+s["realized"])

    def test_wins_and_losses_both_remain_in_denominator(self):
        self.tick(call=True); self.tick(1.5625, NOW+300)
        self.tick(1.25, NOW+600, call=True); self.tick(.9, NOW+900)
        s = paper.statistics(self.d, NOW+900)
        self.assertEqual((s["wins"],s["losses"],s["closed"]), (1,1,2))
        self.assertEqual(s["win_rate"], 50)

    def test_missing_quote_is_unresolved_never_zero_or_a_win(self):
        self.tick(call=True); self.tick(None, NOW+300)
        s = paper.statistics(self.d, NOW+300)
        self.assertIsNone(s["equity"])
        self.assertEqual(s["unresolved"], 1)
        self.assertEqual(s["closed"], 0)
        self.assertEqual(self.d["paper"]["cash"], 900)

    def test_dust_that_cannot_cover_exit_costs_is_not_an_invented_sale(self):
        self.tick(call=True); self.tick(1e-12, NOW+300)
        s=paper.statistics(self.d,NOW+300)
        self.assertIsNone(s["equity"])
        self.assertEqual(s["closed"],0)
        self.assertEqual(s["unresolved"],1)

    def test_tls_validation_remains_required(self):
        import ssl
        from radar.http import Http
        ctx=Http().context
        self.assertTrue(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode,ssl.CERT_REQUIRED)

    def test_gap_fills_at_recovery_price_not_ideal_stop(self):
        self.tick(call=True); self.tick(None, NOW+1200)
        self.tick(.625, NOW+3000)
        p = self.d["paper"]["trades"][0]
        self.assertTrue(p["monitoring_gap"])
        self.assertEqual(p["exit_quote_eur"], .5)
        self.assertLess(p["pnl"], -50)

    def test_expired_fx_blocks_new_entries_and_marks_open_unknown(self):
        self.tick(call=True)
        self.d["fx"]["date_at"] = NOW-5*86400
        self.tick(1.5625, NOW+300, call=True)
        self.assertEqual(len(self.d["paper"]["trades"]), 1)
        self.assertIsNone(paper.statistics(self.d, NOW+300)["equity"])

    def test_fx_changes_affect_eur_result_and_preserve_entry_rate(self):
        self.tick(call=True)
        self.d["fx"]["usd_per_eur"] = 1
        self.tick(1.25, NOW+300)
        p = self.d["paper"]["trades"][0]
        self.assertEqual(p["entry_fx"]["usd_per_eur"], 1.25)
        self.assertEqual(p["exit_fx"]["usd_per_eur"], 1)
        self.assertGreater(p["pnl"], 0)

    def test_budget_limit_skips_calls_transparently_no_negative_cash(self):
        snaps = {}
        for i in range(6):
            s = {**self.s,"key":f"base:0x{i+1:040x}","chain":"base","address":f"0x{i+1:040x}"}
            snaps[s["key"]] = s
        self.d["snapshots"].update(snaps)
        paper.step(self.d, snaps, {}, list(snaps), NOW)
        self.assertEqual(len(paper.opened(self.d)), 5)
        self.assertEqual(self.d["paper"]["cash"], 500)
        self.assertEqual(self.d["paper"]["calls"], 6)
        self.assertEqual(self.d["paper"]["skipped"], 1)
        self.assertLess(len(paper.report(self.d, NOW)), 3500)

    def test_pausing_still_monitors_exits_and_restart_never_resets(self):
        self.tick(call=True)
        process('/teste_parar', self.state, self.config, NOW+1)
        self.tick(.625, NOW+300)
        cash = self.d["paper"]["cash"]
        process('/teste_iniciar', self.state, self.config, NOW+600)
        self.assertEqual(self.d["paper"]["cash"], cash)
        self.assertEqual(len(self.d["paper"]["trades"]), 1)
        self.assertTrue(self.d["paper"]["running"])

    def test_flat_price_after_deadline_loses_costs_not_fake_break_even(self):
        self.tick(call=True); self.tick(1.25, NOW+48*3600)
        s = paper.statistics(self.d, NOW+48*3600)
        self.assertEqual(s["losses"], 1)
        self.assertLess(s["realized"], 0)

    def test_scan_opens_only_actual_eligible_A_and_preserves_manual_positions(self):
        scan(self.state, self.config, FakeMarket(self.s), NOW - 300)
        scan(self.state, self.config, FakeMarket(self.s), NOW)
        self.assertEqual(len(paper.opened(self.d)), 1)
        self.assertEqual(self.d["positions"], [])
        s = {**self.s,"price":1.5625,"observed_at":NOW+300}
        scan(self.state, self.config, FakeMarket(s), NOW+300)
        self.assertEqual(paper.statistics(self.d, NOW+300)["wins"], 1)
        self.assertEqual(self.d["paper"]["calls"], 1)

    def test_no_entry_signal_means_no_trade_not_a_fabricated_result(self):
        s={**self.s,"pool_age_hours":1}
        scan(self.state, self.config, FakeMarket(s), NOW)
        self.assertEqual(self.d["paper"]["trades"], [])
        self.assertIsNone(paper.statistics(self.d,NOW)["win_rate"])

    def test_fx_xml_date_validation_and_unsafe_xml_rejection(self):
        day=self.d["fx"]["date"]
        xml=f'<Envelope><Cube><Cube time="{day}"><Cube currency="USD" rate="1.25"/></Cube></Cube></Envelope>'
        self.assertEqual(fx.parse(xml,NOW)["usd_per_eur"],1.25)
        for text in (xml.replace('1.25','NaN'),xml.replace(day,'2000-01-01'),'<!DOCTYPE x>'+xml):
            with self.assertRaises(ValueError): fx.parse(text,NOW)

    def test_fx_failure_reuses_only_a_valid_reference_without_fabrication(self):
        class Offline:
            def text(self,url): raise ApiError('offline')
        fx.refresh(self.d, Offline(), NOW)
        self.assertEqual(self.d["fx"]["usd_per_eur"],1.25)
        self.assertTrue(fx.valid(self.d["fx"],NOW))
        self.assertFalse(fx.valid(self.d["fx"],NOW+5*86400))


class RecoveryTests(unittest.TestCase):
    def cloud(self, fake):
        with patch.dict(os.environ,{"GITHUB_REPOSITORY":"a/b","GITHUB_TOKEN":"dummy",
                                  "RADAR_STATE_KEY":Fernet.generate_key().decode()}):
            c=CloudState(fake)
        c.sha='old'
        return c

    def test_ambiguous_write_already_saved_is_not_sent_twice(self):
        class Fake:
            puts=0
            def json(self,url,payload=None,headers=None,method=None,retry=True):
                if method=='PUT':
                    self.puts+=1; self.remote={"sha":"new","content":payload['content']}
                    raise ApiError('untrusted secret text',host='api.github.com')
                return self.remote
        f=Fake(); c=self.cloud(f)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state'; p.write_text('{}'); c.save(p)
        self.assertEqual(f.puts,1); self.assertEqual(c.sha,'new')

    def test_transient_write_retries_same_payload_only_if_remote_is_unchanged(self):
        class Fake:
            payloads=[]
            def json(self,url,payload=None,headers=None,method=None,retry=True):
                if method=='PUT':
                    self.payloads.append(copy.deepcopy(payload))
                    if len(self.payloads)==1: raise ApiError('offline',status=503)
                    return {'content':{'sha':'new'}}
                return {'sha':'old','content':base64.b64encode(b'older').decode()}
        f=Fake(); f.payloads=[]; c=self.cloud(f)
        with tempfile.TemporaryDirectory() as d, patch('radar.cloud.time.sleep'):
            p=Path(d)/'state'; p.write_text('{}'); c.save(p)
        self.assertEqual(f.payloads[0],f.payloads[1])

    def test_changed_remote_state_never_overwritten(self):
        class Fake:
            puts=0
            def json(self,url,payload=None,headers=None,method=None,retry=True):
                if method=='PUT': self.puts+=1; raise ApiError('offline',status=503)
                return {'sha':'other','content':base64.b64encode(b'other').decode()}
        f=Fake(); c=self.cloud(f)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state'; p.write_text('{}')
            with self.assertRaises(ValueError): c.save(p)
        self.assertEqual(f.puts,1)

    def test_safe_diagnostic_never_prints_exception_content(self):
        text=safe_failure(ApiError('SECRET/URL/header/body',host='api.github.com',status=403),'guardar estado cifrado')
        self.assertNotIn('SECRET',text); self.assertIn('403',text); self.assertIn('api.github.com',text)


if __name__=='__main__': unittest.main()
