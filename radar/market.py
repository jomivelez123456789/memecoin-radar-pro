from urllib.parse import quote
from itertools import zip_longest
from .model import identity, normalize
from .http import ApiError


class Market:
    def __init__(self, http):
        self.http = http

    def discover(self, chains, limit):
        buckets, errors = {}, []
        # Profiles are a biased sample, not an exhaustive list of new tokens.
        try:
            profiles = self.http.json("https://api.dexscreener.com/token-profiles/latest/v1")
            if not isinstance(profiles, list):
                raise ApiError("Formato de perfis inválido")
            for profile in profiles:
                if profile.get("chainId") in chains:
                    try:
                        key = identity(profile["chainId"], profile.get("tokenAddress"))
                        buckets.setdefault(("dex", profile["chainId"]), []).append(key)
                    except ValueError:
                        pass
        except ApiError:
            errors.append("descoberta DexScreener indisponível")
        # Public new pools: no key, no paid plan. Take base token identity, never a symbol.
        for chain in chains:
            network = "eth" if chain == "ethereum" else chain
            try:
                data = self.http.json(f"https://api.geckoterminal.com/api/v2/networks/{network}/new_pools?include=base_token")
                for token in data.get("included", []):
                    address = token.get("attributes", {}).get("address")
                    try:
                        buckets.setdefault(("gecko", chain), []).append(identity(chain, address))
                    except ValueError:
                        pass
            except ApiError:
                errors.append(f"descoberta GeckoTerminal {chain} indisponível")
        # Interleave source/network buckets so one busy feed cannot hide the others.
        ordered = [buckets.get((source, chain), []) for source in ("dex", "gecko") for chain in chains]
        result = [key for row in zip_longest(*ordered) for key in row if key is not None]
        return list(dict.fromkeys(result))[:limit], errors

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
