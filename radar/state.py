import json
import os
from contextlib import contextmanager
from pathlib import Path


def blank():
    return {"version": 1, "offset": 0, "watched": [], "signaled": {}, "snapshots": {},
            "positions": [], "history": [], "cooldowns": {}, "outbox": [], "health": {}}


class State:
    def __init__(self, path="data/state.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else blank()
        if self.data.get("version") != 1 or set(blank()) - self.data.keys():
            raise ValueError("Estado inválido: recuperar cópia; não reinicializar automaticamente")

    def save(self):
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as file:
            json.dump(self.data, file, ensure_ascii=False, allow_nan=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(tmp, self.path)

    @contextmanager
    def lock(self):
        path = self.path.with_suffix(".lock")
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            yield
        finally:
            os.close(descriptor)
            path.unlink()
