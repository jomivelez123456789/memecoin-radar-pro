# Memecoin Radar Pro

Monitorização experimental em Python, em português europeu. **Não compra, vende, assina transações ou acede a carteiras.** Não existem probabilidades de lucro validadas.

## Estado desta entrega

- Recolha real de DexScreener e descoberta complementar de pools no GeckoTerminal: verificadas.
- Motor de filtros, alertas A/B/C, lista manual, posições simuladas/reais registadas manualmente, vendas parciais e histórico: implementados.
- Mensagens Telegram com gráfico, token no Phantom, contrato copiável e `/detail`: implementadas; entrega num Telegram real depende da configuração pessoal.
- Código e workflows publicados no GitHub; testes remotos e duas execuções reais do radar concluídos com sucesso. Telegram configurado e agendamento de 15 em 15 minutos ativado, com histórico cifrado.
- Notícias e categoria D, auditoria on-chain e imagens de gráficos: melhorias futuras, sem acesso fictício a plataformas.

## Começar

Se estás a usar a instalação já configurada, começa pelo [guia rápido](docs/UTILIZACAO_RAPIDA.md). Os passos abaixo servem também para reproduzir a instalação.

1. Experimenta [INICIAR.cmd](INICIAR.cmd): consulta mercado real sem enviar mensagens ou usar dinheiro.
2. Segue [Instalação e ativação](docs/INSTALACAO.md).
3. Lê [Formação prática](docs/FORMACAO.md) e faz a simulação antes de considerar dinheiro real.
4. Consulta [Regras e limitações](docs/REGRAS_E_LIMITACOES.md) e [Validação](docs/TESTES.md).

A instalação desta entrega usa [@MemecoinRadarPro_7F3A_bot](https://t.me/MemecoinRadarPro_7F3A_bot), com comandos limitados ao proprietário. O código público não permite consultar posições ou controlar o bot sem os segredos. Noutro computador é necessário instalar Python e preparar o ambiente de acordo com o guia.

## Utilização após ativação

No Telegram, envia `/help`, `/health` ou `/positions`. Os comandos são processados durante a execução seguinte, com atraso nominal de até 15 minutos, potencialmente maior. Não há um serviço permanentemente ligado.

`/simulate REDE CONTRATO PREÇO QTD TAXA STOP OBJETIVO` regista uma simulação. `/register real ...` serve exclusivamente para registar uma compra que já efetuaste manualmente. Nenhum sinal significa que compraste.

Todos os preços e registos monetários são em USD. Um preço apresentado não garante uma venda por esse preço. Stop e objetivo são referências para alertas, sem execução de ordens.

## Organização

`radar/`: rede, identificação, dados de mercado, regras, Telegram, comandos, posições, persistência e execução cloud. `config.json`: filtros. `tests/`: testes sem rede. `scripts/`: configuração pessoal e verificações públicas. `.github/workflows/`: testes e agendamento.

Para desenvolver:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m radar.app --dry-run
```

O estado local está em `data/` e é excluído do Git. A versão de ensaio usa `data/dry-run.json`, separada do bot. Na cloud, o estado é comprimido e cifrado com Fernet e guardado na branch `radar-state`; só a chave privada em GitHub Actions Secrets permite ler posições e histórico.

Não publiques `data/`, `.env`, tokens, chaves ou registos pessoais. Nunca introduzas uma seed phrase neste projeto.

Fontes e limites consultados em 12/11/2026: [fontes oficiais](docs/FONTES.md). Gratuito refere-se à infraestrutura escolhida; negociar com dinheiro real tem custos e pode resultar na perda total.
