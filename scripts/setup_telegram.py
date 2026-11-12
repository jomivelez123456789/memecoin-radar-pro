"""Assistente local. Não grava o token, não apresenta URLs com credenciais."""
import getpass
import os
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from radar.http import Http
from radar.telegram import Telegram


def main():
    os.environ["TELEGRAM_BOT_TOKEN"] = getpass.getpass("Token do BotFather (oculto, apenas neste processo): ").strip()
    os.environ["TELEGRAM_CHAT_ID"] = "setup"
    bot = Telegram(Http())
    bot.call("getMe", {})
    print("No iPhone, abre o teu bot e envia /start. Não adiciones o bot a grupos.")
    input("Depois de enviares /start, prime Enter aqui: ")
    updates = bot.updates(0)
    candidates = [u["message"] for u in updates if u.get("message", {}).get("chat", {}).get("type") == "private"
                  and u["message"].get("text") == "/start" and time.time() - u["message"].get("date", 0) < 1800]
    identities = {(m["chat"]["id"], m["from"]["id"]) for m in candidates}
    if len(identities) != 1:
        raise ValueError("Sem conversa privada única recente. Volta a enviar /start e repete.")
    chat, user = identities.pop()
    print("Confirma que o ID abaixo pertence à tua conversa. Se não tens a certeza, interrompe.")
    print(f"TELEGRAM_CHAT_ID={chat}\nTELEGRAM_USER_ID={user}")
    if input("Escreve CONFIRMO para enviar mensagem de teste: ").strip() != "CONFIRMO":
        return
    bot.chat, bot.user = str(chat), str(user)
    bot.send("Memecoin Radar Pro: teste de ligação concluído. Monitorização ainda não ativada.")
    print("Recebeste a mensagem? Configura agora os segredos no GitHub seguindo docs/INSTALACAO.md.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Não foi possível concluir ({type(error).__name__}). Token omitido.")
        raise SystemExit(1) from None
