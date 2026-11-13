# Memecoin Radar Pro

Monitorização experimental em Python, em português europeu. **Não compra, vende, assina transações ou acede a carteiras.** Não existem probabilidades de lucro validadas.

## Estado desta entrega

- Recolha real de DexScreener e descoberta complementar de pools no GeckoTerminal: verificadas.
- Motor de filtros, alertas A/B/C, lista manual, posições simuladas/reais registadas manualmente, vendas parciais e histórico: implementados.
- Mensagens Telegram com gráfico, token no Phantom, contrato copiável e `/detail`: implementadas; entrega num Telegram real depende da configuração pessoal.
- Código e workflows publicados no GitHub; Telegram configurado e consultas previstas a cada 5 minutos, com histórico cifrado. O agendamento pode atrasar ou falhar; não há garantia de serviço contínuo em tempo real.
- Mensagens simples com emojis, botões, registo guiado de compras/simulações/vendas e acompanhamento separado de até 30 posições abertas, com resumos periódicos e avisos de níveis/risco.
- RSS de Cointelegraph, Decrypt e CoinDesk, com falhas explicitamente identificadas. Notícias só são ligadas a uma moeda quando mencionam endereço completo e rede, juntamente com atividade de mercado. Não verificam a veracidade da notícia nem aumentam o score.
- Redes sociais, auditoria on-chain e imagens de gráficos continuam fora desta versão; não existe acesso fictício a plataformas nem uma estratégia de lucro validada.

**Disponibilidade:** foi observado um atraso de horas no cron GitHub. Embora esteja configurado para cinco minutos, não deve ser usado como proteção de saídas urgentes. Há um [relógio alternativo preparado, ainda não ativado](docs/RELOGIO_ALTERNATIVO.md), que requer autorização e uma conta adicional. Mantém simulações enquanto a disponibilidade não for adequada ao uso pretendido.

## Começar

Se estás a usar a instalação já configurada, começa pelo [guia rápido](docs/UTILIZACAO_RAPIDA.md). Os passos abaixo servem também para reproduzir a instalação.

1. Experimenta [INICIAR.cmd](INICIAR.cmd): consulta mercado real sem enviar mensagens ou usar dinheiro.
2. Segue [Instalação e ativação](docs/INSTALACAO.md).
3. Lê [Formação prática](docs/FORMACAO.md) e faz a simulação antes de considerar dinheiro real.
4. Consulta [Regras e limitações](docs/REGRAS_E_LIMITACOES.md) e [Validação](docs/TESTES.md).

A instalação desta entrega usa [@MemecoinRadarPro_7F3A_bot](https://t.me/MemecoinRadarPro_7F3A_bot), com comandos limitados ao proprietário. O código público não permite consultar posições ou controlar o bot sem os segredos. Noutro computador é necessário instalar Python e preparar o ambiente de acordo com o guia.

## Utilização após ativação

No Telegram, envia `/ajuda`, `/estado` ou `/posicoes`. `/comprar`, `/vender`, `/depositar`, `/retirar` e `/saidas` explicam os passos sem jargão. Os comandos e botões são processados durante a execução seguinte, prevista de 5 em 5 minutos, potencialmente mais tarde. Não há um serviço permanentemente ligado.

Usa «🧪 Simular» ou «📝 Já comprei» no alerta, confirma o contrato e responde a um formulário curto numa única mensagem. Só regista compras reais que já efetuaste manualmente. «👀 Só acompanhar» não cria uma posição. Em `/posicoes`, «📝 Registar venda» atualiza o registo depois da venda manual ou durante uma simulação. `/tecnico` mantém os comandos completos opcionais. Nenhum sinal significa que compraste.

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
