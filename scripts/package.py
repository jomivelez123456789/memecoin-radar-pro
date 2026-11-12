"""ZIP só de código/documentação, com lista explícita; exclui dados e credenciais."""
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
files = [root / name for name in ("README.md", "requirements.txt", "config.json", ".gitignore", ".gitattributes",
                                  "INICIAR.cmd", "CONFIGURAR_TELEGRAM.cmd")]
for folder in ("radar", "tests", "scripts", "docs", ".github"):
    files.extend(p for p in (root / folder).rglob("*")
                 if p.is_file() and "__pycache__" not in p.parts and p.suffix not in (".pyc", ".key", ".enc", ".log"))
target = root / "dist" / "memecoin-radar-pro.zip"
target.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
    for file in sorted(files):
        archive.write(file, file.relative_to(root).as_posix())
print(f"Pacote criado: {len(files)} ficheiros, sem ambiente Python nem estado pessoal.")
