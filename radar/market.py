from urllib.parse import quote
from itertools import zip_longest
import time
from .model import identity, normalize
from .http import ApiError


class Market:
    def __init__(self, http):
        self.http = http
        self.coverage = {}

    def discover(self, chains, limit):
        buckets, errors = {}, []
        self.coverage = {}
        # Profiles are a biased sample, not an exhaustive list of new tokens.
        try:
            profiles = self.http.json("https://api.dexscreener.com/token-profiles/latest/v1")
            if not isinstance(profiles, list):
                raise ApiError("Formato de perfis inválido")
            self.coverage["DexScreener perfis"] = "disponível"
            for profile in profiles:
                if profile.get("chainId") in chains:
                    try:
                        key = identity(profile["chainId"], profile.get("tokenAddress"))
                        buckets.setdefault(("dex", profile["chainId"]), []).append(key)
                    except ValueError:
                        pass
        except ApiError:
            errors.append("descoberta DexScreener indisponível")
            self.coverage["DexScreener perfis"] = "indisponível"
        # Public new pools: no key, no paid plan. Take base token identity, never a symbol.
        for chain in chains:
            network = "eth" if chain == "ethereum" else chain
            for source, endpoint in (("tendências", "trending_pools"), ("novos", "new_pools")):
                label = f"GeckoTerminal {chain} {source}"
                try:
                    data = self.http.json(f"https://api.geckoterminal.com/api/v2/networks/{network}/{endpoint}?include=base_token")
                    if not isinstance(data, dict) or not isinstance(data.get("included", []), list):
                        raise ApiError("Formato de descoberta inválido")
                    for token in data.get("included", []):
                        if not isinstance(token, dict):
                            continue
                        address = token.get("attributes", {}).get("address")
                        try:
                            buckets.setdefault((source, chain), []).append(identity(chain, address))
                        except ValueError:
                            pass
                    self.coverage[label] = "disponível"
                except ApiError:
                    errors.append(f"descoberta {label} indisponível")
                    self.coverage[label] = "indisponível"
        # Interleave source/network buckets so one busy feed cannot hide the others.
        ordered = [buckets.get((source, chain), []) for source in ("tendências", "dex", "novos") for chain in chains]
        result = [key for row in zip_longest(*ordered) for key in row if key is not None]
        unique = list(dict.fromkeys(result))
        # Rotate a bounded public sample instead of repeatedly inspecting only its first page.
        offset = (int(time.time() // 300) * limit) % len(unique) if len(unique) > limit else 0
        return (unique[offset:] + unique[:offset])[:limit], errors

    def fetch(self, keys, now):
        snapshots, errors = {}, []
        for chain in sorted({key.split(":", 1)[0] for key in keys}):
            addresses = [key.split(":", 1)[1] for key in keys if key.startswith(chain + ":")]
            for index in range(0, len(addresses), 30):
                batch = addresses[index:index + 30]
                url = f"https://api.dexscreener.com/tokens/v1/{chain}/" + quote(",".join(batch), safe=",")
                try:
                    pairs = self.http.json(url)
                    if not isinstance(pairs, list):
                        raise ApiError("Formato de pares inválido")
                except ApiError:
                    errors.extend(identity(chain, address) for address in batch)
                    continue
                for address in batch:
                    candidates = [s for pair in pairs if isinstance(pair, dict)
                                  and (s := normalize(pair, chain, address, now)) is not None]
                    if candidates:
                        best = max(candidates, key=lambda s: s.get("liquidity") or 0)
                        snapshots[best["key"]] = best
                    else:
                        errors.append(identity(chain, address))
        return snapshots, errors
