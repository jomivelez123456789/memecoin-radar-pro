"""Cópia da chave cifrada: chave RSA privada protegida pelo Windows DPAPI.

prepare: gerar chave pública e proteger a chave privada para esta conta Windows.
check: confirmar que a cópia cifrada contém uma chave Fernet válida, sem a mostrar.
recover: apresentar a chave apenas no terminal local, para recuperação manual.
Nunca recebe nem guarda o token Telegram.
"""
import argparse
import ctypes
import os
from pathlib import Path
from ctypes import wintypes
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

ROOT = Path(__file__).resolve().parents[1] / "data"


class Blob(ctypes.Structure):
    _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]


def dpapi(raw, encrypt):
    if os.name != "nt":
        raise RuntimeError("Esta cópia só funciona na conta Windows que a criou")
    buffer = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
    source, target = Blob(len(raw), buffer), Blob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    method = crypt.CryptProtectData if encrypt else crypt.CryptUnprotectData
    method.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                       ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    method.restype = wintypes.BOOL
    if not method(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise RuntimeError("Proteção Windows indisponível")
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel.LocalFree(ctypes.cast(target.data, ctypes.c_void_p))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "check", "recover"])
    args = parser.parse_args()
    ROOT.mkdir(exist_ok=True)
    protected = ROOT / "backup-private.dpapi"
    public = ROOT / "backup-public.pem"
    if args.action == "prepare":
        if protected.exists() or public.exists():
            raise RuntimeError("Já existe uma chave de cópia; não sobrescrever")
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        der = key.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption())
        protected.write_bytes(dpapi(der, True))
        public.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,
                                                        serialization.PublicFormat.SubjectPublicKeyInfo))
        assert dpapi(protected.read_bytes(), False) == der
        print("Chave privada de cópia protegida pelo Windows; chave pública preparada.")
        return
    private = serialization.load_der_private_key(dpapi(protected.read_bytes(), False), None)
    value = private.decrypt((ROOT / "state-key-backup.enc").read_bytes(),
                            padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    Fernet(value)  # Validate without exposing the key.
    if args.action == "recover":
        print("SEGREDO: copiar apenas para RADAR_STATE_KEY em GitHub Actions Secrets. Não partilhar.")
        print(value.decode("ascii"))
    else:
        print("Cópia cifrada verificada. Recuperável nesta conta Windows, sem apresentar a chave.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Falha na cópia ({type(error).__name__}); segredos omitidos.")
        raise SystemExit(1) from None
