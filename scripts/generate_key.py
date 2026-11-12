"""Gerar chave para copiar diretamente para um GitHub Actions Secret."""
from cryptography.fernet import Fernet
if __name__ == "__main__":
    print("Chave privada de cifragem do histórico. Não colar em chats, commits ou logs públicos.")
    print("Guardar em GitHub Secret RADAR_STATE_KEY e numa cópia offline privada:")
    print(Fernet.generate_key().decode())
