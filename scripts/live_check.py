"""Verificação pública reproduzível; nunca faz pedidos ao Telegram ou transações."""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from radar.http import Http
from radar.market import Market
from radar.model import identity, links
from radar.app import load_config


def main():
    http = Http()
    market = Market(http)
    keys, discovery_errors = market.discover(["solana", "base"], 16)
    snapshots, missing = market.fetch(keys, time.time())
    known = [identity("solana", "So11111111111111111111111111111111111111112"),
             identity("base", "0x4200000000000000000000000000000000000006")]
    known_snapshots, known_missing = market.fetch(known, time.time())
    actions = {}
    for action, tag in (("checkout", "v4.2.2"), ("setup-python", "v5.6.0")):
        ref = http.json(f"https://api.github.com/repos/actions/{action}/git/ref/tags/{tag}")
        actions[action] = ref["object"]["sha"]
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "discovered": len(keys), "market_observations": len(snapshots),
              "missing": len(missing), "discovery_errors": discovery_errors,
              "known_tokens_observed": list(known_snapshots), "known_tokens_missing": known_missing,
              "action_pins": actions,
              "links": {key: links(s["chain"], s["address"], s["pair"]) for key, s in known_snapshots.items()},
              "iphone_opening": "não testado num iPhone", "telegram_delivery": "pendente de configuração",
              "github_execution": "pendente de publicação e segredos"}
    Path("docs/LIVE_CHECK.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("links",)}, ensure_ascii=False))
    if discovery_errors or missing or known_missing or not snapshots:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
