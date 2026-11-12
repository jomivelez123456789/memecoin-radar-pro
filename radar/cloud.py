"""Persistência autenticada e cifrada no próprio GitHub, sem caches/artifacts pagos."""
import base64
import os
import zlib
from pathlib import Path
from urllib.parse import quote
from cryptography.fernet import Fernet
from .http import Http, ApiError
from .app import run


class CloudState:
    def __init__(self, http=None):
        self.http = http or Http()
        self.repo = os.environ["GITHUB_REPOSITORY"]
        self.headers = {"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
                        "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        self.cipher = Fernet(os.environ["RADAR_STATE_KEY"].encode())
        self.base = "https://api.github.com/repos/" + self.repo
        self.branch = "radar-state"
        self.sha = None

    def api(self, path, payload=None, method=None):
        # Mutation requests must not be repeated after ambiguous network failures.
        return self.http.json(self.base + path, payload, self.headers, method, retry=payload is None)

    @staticmethod
    def not_found(error):
        return str(error).endswith("HTTP 404")

    def restore(self, path, initialize=False):
        repo = self.api("")
        if repo.get("private") is not False:
            raise ValueError("Automatização autorizada apenas em repositório público para evitar consumo pago")
        try:
            file = self.api("/contents/state.enc?ref=" + self.branch)
        except ApiError as error:
            if not initialize or not self.not_found(error):
                raise
            try:
                self.api("/git/ref/heads/" + self.branch)
            except ApiError as branch_error:
                if not self.not_found(branch_error):
                    raise
                ref = self.api("/git/ref/heads/" + quote(repo["default_branch"], safe=""))
                self.api("/git/refs", {"ref": "refs/heads/" + self.branch, "sha": ref["object"]["sha"]})
            # Initialization is one-time only. Never overwrite an existing local state.
            if Path(path).exists():
                raise ValueError("Estado local existente: interromper inicialização")
            return
        self.sha = file["sha"]
        encrypted = base64.b64decode(file["content"])
        compressed = self.cipher.decrypt(encrypted)  # Authentication failure is fatal, never reset state.
        decoder = zlib.decompressobj()
        raw = decoder.decompress(compressed, 20_000_001)
        if len(raw) > 20_000_000 or not decoder.eof:
            raise ValueError("Estado demasiado grande ou comprimido inválido")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(raw)

    def save(self, path):
        raw = Path(path).read_bytes()
        if len(raw) > 20_000_000:
            raise ValueError("Estado excede o limite; arquivar histórico antes de continuar")
        encrypted = self.cipher.encrypt(zlib.compress(raw, level=9))
        if len(encrypted) > 900_000:
            raise ValueError("Estado cifrado próximo do limite da API; arquivar histórico")
        payload = {"message": "radar: guardar estado cifrado", "branch": self.branch,
                   "content": base64.b64encode(encrypted).decode()}
        if self.sha:
            payload["sha"] = self.sha
        result = self.api("/contents/state.enc", payload, method="PUT")
        self.sha = result["content"]["sha"]


def main():
    # GitHub concurrency group serializes all runs using this state branch.
    path = "data/state.json"
    try:
        cloud = CloudState()
        cloud.restore(path, os.environ.get("RADAR_INITIALIZE") == "true")
        try:
            run(path)
        finally:
            if Path(path).exists():
                cloud.save(path)
    except Exception as error:
        print(f"Falha cloud ({type(error).__name__}); execução interrompida, segredos omitidos.")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
