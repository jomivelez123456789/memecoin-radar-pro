# Instalar e ativar

## 1. O que já está preparado neste computador

O código e o ambiente Python estão na pasta `C:\Users\User\Desktop\MEMECOINS AI`. Abre `INICIAR.cmd` com duplo clique para consultar o mercado sem Telegram e sem transações. Uma resposta com `observations` superior a zero confirma recolha, não uma oportunidade nem rentabilidade.

Não é necessário instalar uma carteira para usar o radar ou simular posições. Não uses dinheiro real nesta configuração.

## 2. Preparar Python noutro computador

Instala Python 3.12 ou superior em [python.org](https://www.python.org/downloads/), sem comprar ferramentas. Abre um terminal na pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Se `python` abrir a Microsoft Store, usa o caminho da instalação oficial. Neste computador foi utilizada a instalação Python já existente, sem instalar outro Python. A única dependência direta adicional é `cryptography`, para cifrar o estado cloud; recolha e análise usam a biblioteca padrão.

## 3. Criar o teu bot Telegram no iPhone

1. Instala/abre a aplicação oficial Telegram. Pesquisa o bot oficial [@BotFather](https://t.me/BotFather) e verifica a identificação oficial; evita nomes parecidos.
2. Envia `/newbot`. Escolhe um nome e um nome de utilizador terminado em `bot`.
3. O BotFather entrega um token. Trata-o como uma chave do bot. **Não o coloques neste chat, numa imagem, no código ou num ficheiro público.** Se for exposto, revoga-o no BotFather e atualiza o segredo.
4. Abre o novo bot pelo link fornecido pelo BotFather e envia `/start` numa conversa privada.
5. No computador, abre `CONFIGURAR_TELEGRAM.cmd`. Introduz o token no pedido oculto; não fica gravado pelo assistente. Segue as instruções e confirma a conversa antes da mensagem de teste.
6. Guarda os dois identificadores apresentados para configurar os segredos abaixo. O assistente não aceita grupos e interrompe se houver várias conversas candidatas.
7. Confirma a receção do teste no iPhone. Ativa notificações do Telegram nas Definições do iPhone e verifica modos de concentração/silêncio.

O assistente envia apenas uma mensagem de teste para a conversa que confirmares. Se houver um webhook antigo configurado neste bot, `getUpdates` pode falhar; usa um bot novo dedicado ao radar. Não partilhes o bot com outras pessoas.

## 4. Publicar no GitHub sem pagar

A publicação necessita da tua sessão numa conta GitHub. Não atives trials, Codespaces, runners maiores, subscrições ou cartões.

1. Entra em [github.com](https://github.com). Se não tens conta, cria a modalidade gratuita e aceita pessoalmente os termos aplicáveis.
2. Cria um repositório **público**, por exemplo `memecoin-radar-pro`, com branch principal `main`. Código e documentação ficam públicos; dados pessoais ficam excluídos e o estado cloud será cifrado. Não envies o teu pedido pessoal original.
3. A opção mais simples é usar o GitHub Desktop já instalado: `File > Add local repository`, escolher a pasta deste projeto e `Publish repository`. Desmarca `Keep this code private` para a infraestrutura gratuita escolhida. Se o nome já existir, escolhe outro. Se preferires upload web, extrai o ZIP de distribuição e envia o conteúdo, incluindo `.github/workflows/`; confirma que os ficheiros de automatização aparecem no repositório.
4. Antes de publicar, confirma que a lista não contém `.venv`, `data`, `.env`, chaves, tokens ou credenciais. O `.gitignore` já os exclui ao usar Git.

O bot cloud recusa um repositório privado para evitar consumo de recursos faturáveis. Não muda a visibilidade de nenhum repositório existente. Se não quiseres código público, mantém o projeto local e não atives este workflow; será preciso estudar outra alternativa dentro do orçamento.

## 5. Configurar os segredos

No repositório, abre `Settings > Secrets and variables > Actions > New repository secret`. Adiciona:

| Nome | Valor |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Token entregue pelo BotFather |
| `TELEGRAM_CHAT_ID` | ID da conversa privada apresentado pelo assistente local |
| `TELEGRAM_USER_ID` | ID do utilizador apresentado pelo assistente local |
| `RADAR_STATE_KEY` | Chave criada pelo comando abaixo |

Para criar a chave, executa **tu**, localmente, sem enviar a saída para este chat:

```powershell
.\.venv\Scripts\python.exe scripts\generate_key.py
```

Copia a chave diretamente para o segredo `RADAR_STATE_KEY` e guarda uma cópia privada offline. Não a introduzas como uma variável normal. Quem tiver a chave e o estado cifrado consegue ler o histórico. Perder a chave impede recuperar o histórico; trocá-la sem migração interrompe a execução em vez de apagar dados.

O `GITHUB_TOKEN` é criado automaticamente pelo GitHub para cada execução; não cries um token pessoal. O workflow pede escrita no repositório apenas para guardar o ficheiro cifrado. Pessoas com acesso de escrita podem alterar workflows e capturar segredos: não concedas esse acesso a desconhecidos. Pedidos de alteração de terceiros não recebem os segredos do radar.

## 6. Ativar e comprovar

1. Em `Actions`, confirma que os testes automáticos terminaram com sucesso. Depois de configurar todos os segredos, abre `Memecoin Radar` e escolhe `Enable workflow`: o radar foi deixado desativado enquanto falta a configuração pessoal.
2. Abre `Memecoin Radar > Run workflow`. Na **primeira execução apenas**, assinala `initialize` e executa na branch `main`.
3. Confirma a execução verde, a criação da branch `radar-state` com `state.enc` e a mensagem diária de funcionamento no Telegram.
4. Envia `/health` e aguarda a próxima execução. Confirma a resposta e a hora da observação. O comando não recebe resposta instantânea.
5. Faz uma simulação do guia. Confirma `/positions`, os links e o botão de copiar contrato no iPhone.
6. Desliga o computador. Mais tarde, verifica no iPhone uma resposta ou confirmação de uma execução posterior. **Só este teste, juntamente com os registos do Actions, comprova funcionamento remoto.**

Se falta o estado e `initialize` não foi autorizado, o radar para. Não uses repetidamente a inicialização para esconder um erro de recuperação. Recupera a branch/chave correta.

## 7. Frequência, custos e disponibilidade

O agendamento é aos minutos 07, 22, 37 e 52 de cada hora UTC. Não exige computador ou ChatGPT ligados **depois de ativado no GitHub**. São até 96 execuções diárias; não é streaming nem vigilância contínua. Há uma janela entre consultas e a saída pode ocorrer muito depois de o mercado ter mudado.

O GitHub confirma execução gratuita em repositórios públicos com runners padrão; repositórios privados têm franquias e podem gerar cobrança. Este projeto usa `ubuntu-latest` padrão, sem cache nem upload de artifacts. Limita cada execução a dez minutos e mantém execuções serializadas. Não utiliza APIs pagas nem introduz pagamentos. Fontes públicas podem mudar condições ou ficar indisponíveis.

O agendamento pode atrasar, omitir tarefas em períodos de carga e ser desativado após 60 dias de inatividade do repositório público. Verifica regularmente `Actions`; não assumes que gravações automáticas na branch do estado impedem a desativação. O intervalo mínimo suportado pelo GitHub é cinco minutos; reduzir o intervalo não cria uma garantia de disponibilidade.

## 8. Diagnóstico e recuperação

- **Sem mensagem após 26 horas:** verifica `Actions` e as notificações de falha do GitHub. Se o próprio agendamento parou, o bot não consegue avisar por si. Configura pessoalmente os emails de falha nas preferências de notificações do GitHub.
- **Falha de Telegram:** confirma os três segredos, que iniciaste a conversa e não bloqueaste o bot. Não publiques logs com credenciais. A fila fica persistida e tenta novamente na próxima execução.
- **Falha de mercado/rate limit:** o radar usa timeout, espaçamento e até três tentativas em pedidos de leitura. Não transforma ausência de dados em preço zero.
- **Erro de chave/estado:** não apagues o estado. Confirma a chave guardada e a branch `radar-state`. Guarda uma cópia privada do ficheiro cifrado antes de alterações.
- **Execução interrompida:** consulta a execução seguinte e o histórico da branch. Existe um pequeno risco de repetir uma notificação se o envio tiver sido aceite mas a confirmação não tiver sido persistida.
- **Bloqueio local:** só se não houver processo do radar em execução, podes remover manualmente `data/state.lock` ou `data/dry-run.lock` após uma interrupção abrupta. Não executes duas instâncias com o mesmo estado.
- **Parar:** em `Actions > Memecoin Radar`, escolhe `Disable workflow`. Não apaga histórico nem fecha posições; não existem ordens colocadas pelo bot.

Nunca envies o ficheiro `data/state.json` para um repositório público. Para suporte, envia apenas a categoria do erro e o estado geral, sem chaves ou dados pessoais.
