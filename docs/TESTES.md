# Registo de validação — 12 a 17/11/2026

## Ensaio em euros e recuperação — 17/11/2026

107 testes Python e cinco testes do relógio passaram localmente. Foram acrescentados casos de lucro versus taxa de acerto, perdas, câmbio EUR/USD variável, cotação/câmbio ausentes, posições sem valor para cobrir custos de saída, custos e desvio em ambos os lados, limite de cinco posições, pausa sem apagar perdas, saída ao preço observado após um intervalo, ausência de call sem compra fictícia, segurança XML/TLS e escrita remota ambígua reconciliada antes de repetir. Cenários artificiais não contam como ganhos de mercado.

A leitura real do BCE validou a referência de 16/11/2026 (1 EUR = 1,1014 USD), com TLS verificado. Em 17/11, foram consultadas 25 execuções consecutivas bem-sucedidas entre 10:56 e 12:56 UTC. As falhas de API de 16/11 às 22:26/22:31 têm mensagem antiga genérica e não permitem atribuir com certeza a causa a um fornecedor. O novo diagnóstico preserva apenas etapa, host autorizado e código HTTP; não imprime conteúdos de exceções ou credenciais.

O protocolo prospetivo está em [TESTE_EUROS.md](TESTE_EUROS.md). Os exemplos manuais anteriores são excluídos. Só novas calls A efetivamente emitidas podem abrir posições na carteira fictícia; zero calls fechadas implica taxa de acerto por apurar.

## Atualização de experiência e acompanhamento

**86 testes Python e 4 testes do relógio passaram localmente e no GitHub no commit `4a3681f`. Na correção de 16/11, os cinco testes atualizados do relógio passaram localmente, incluindo redirecionamentos recusados, sucesso 200/204 e erros sem credenciais.** A suite inclui os 48 testes anteriores e casos de formulários com vírgulas decimais, validação atómica, venda parcial/total, alteração de níveis, cancelamentos antigos, botões expirados, autorização e repetição de callbacks, compatibilidade do estado existente, prioridade das posições perante novos sinais, limites de mensagens, proteção de XML/links/notícias e aviso de interrupções observadas.

Teste real de notícias: Cointelegraph e Decrypt responderam; CoinDesk foi marcado indisponível. Foram retidos 40 títulos/links recentes, sem copiar artigos nem associar moedas pelo símbolo. Esta recolha não valida a veracidade dos títulos ou uma estratégia de lucro.

### Verificação real da versão visual, em 13/11/2026

- [Ajuda com emojis e formulário de simulação](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43339035184): sucesso e mensagens recebidas no Telegram.
- [Registo guiado, notícias e aviso de saída individual](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43339248832): sucesso. O aviso identificou explicitamente a simulação, explicou a perda estimada e mostrou níveis e botões.
- [Botão «Registar venda»](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43339433661): callback processado e formulário recebido, sem transações.
- [Venda fictícia com vírgulas decimais e consulta de posições](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43339628142): sucesso; registo encerrado e zero posições abertas. O teste não avaliou uma estratégia de lucro.
- [Uma execução por horário foi confirmada](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43323546163), às 22:50 UTC de 12/11, após uma consulta manual às 17:35. As respostas que aguardavam na fila chegaram às 22:50. Este intervalo observado de horas impede apresentar o cron do GitHub como vigilância frequente garantida.

O relógio Cloudflare foi publicado em 13/11/2026 às 14:57 UTC, após autorização e configuração de acessos limitados. Workers Free e ausência de método de pagamento foram confirmados no painel. A credencial temporária de publicação, restrita a este Worker, foi revogada após publicar. A correção de 16/11 substituiu a opção de redirecionamento não suportada por `manual`, mantendo a recusa de redirecionamentos. Foram confirmadas a [primeira análise automática](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43927860052) e a [segunda](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43928718040), pedidas às 18:20:53 e 18:25:52 UTC, ambas concluídas com sucesso, e respostas de ajuda/estado no Telegram às 18:21 e 18:26. O estado confirmou funcionamento, 16 observações e zero ausentes. O diagnóstico temporário foi desativado e o acesso de publicação revogado. Os cinco testes desse componente usam credencial fictícia e não fazem pedidos externos. A nota de interrupções do radar só consegue avisar quando uma execução volta a ocorrer.

## Testes locais concluídos

**48 testes automáticos passaram**, sem chamadas externas, em Python 3.14.5 no Windows. A sintaxe de todos os módulos/scripts foi verificada. Os mesmos testes passaram também em Python 3.12 no GitHub: [execução remota concluída com sucesso](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43264568600), commit `841a066`.

Cobertura funcional: indicadores e limites, dados ausentes, volume relativo sem histórico suficiente, entrada, saída por deterioração, níveis de posições simuladas, risco de subida anormal, queda de liquidez apenas no mesmo par, limites de lotes de API, seleção de pares, identificação de tokens/redes, links CAIP-19, mensagem escapada e tamanho, cópia de contrato, autorização por utilizador e conversa privada, comandos antigos ignorados, comandos sem duplicação, gravação/recuperação, bloqueio local, fila após falha e descarte de sinais expirados, vendas parciais e P/L, prevenção de venda superior ao saldo, cifragem/autenticação, recuperação cloud simulada, recusa de repositório privado e de estado ausente sem inicialização, erros sem token e respeito pelo Retry-After limitado.

Os testes de Telegram utilizam um destinatário simulado e verificam conteúdo/comportamento, **não comprovam entrega no serviço real**. A recuperação cloud usa uma API GitHub simulada; não comprova permissões na conta do utilizador. Os cenários artificiais não demonstram rentabilidade.

## Verificações públicas reais

Executado `scripts/live_check.py`. Resultado reproduzível em [LIVE_CHECK.json](LIVE_CHECK.json):

- Descoberta via DexScreener e GeckoTerminal sem erros.
- 16 candidatos com observações válidas, zero ausentes.
- Consulta adicional de WSOL/Solana e WETH/Base com identidades verificadas por rede e contrato.
- Hashes das Actions comparados com referências oficiais GitHub para as versões fixadas.
- Links de gráfico/token construídos a partir das identidades devolvidas, sem copiar URLs arbitrários dos fornecedores.

Executado também o modo de ensaio completo com mercado real: 16 observações, zero erros e zero sinais nessa execução. Não se afrouxaram os filtros para forçar um alerta.

## Integração real concluída

- [Primeira execução do radar](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43270113986): sucesso, 16 observações válidas e confirmação real recebida na conversa privada Telegram.
- [Segunda execução](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43270396493): sucesso, recuperação do estado cifrado, processamento de `/help`, `/health` e criação de uma posição simulada.
- Alerta B recebido no Telegram com rede, contrato, dados de mercado, motivo explicitamente simulado e botões de gráfico, Phantom e cópia do contrato. O nível da posição fictícia foi escolhido para testar o aviso; não corresponde a uma compra real nem valida uma estratégia.
- Ficheiro remoto `state.enc` confirmado como cifrado; valores das credenciais não são publicados no código nem neste relatório.
- Cópia local da chave cifrada, com chave privada protegida pelo Windows DPAPI: geração, recuperação e validação de uma chave Fernet verificadas sem mostrar o segredo.
- Após o teste real, as mensagens de estado foram simplificadas e o link de formação foi corrigido. Os 48 testes passaram novamente localmente e no GitHub no commit `68e6819`.
- Duas vendas fictícias de metade da posição foram processadas numa execução posterior. O bot confirmou o saldo final zero, o resultado simulado e o estado de funcionamento com datas legíveis. A posição de teste ficou encerrada; nenhuma carteira foi utilizada.
- [Terceira execução do radar](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43271016640): sucesso, incluindo processamento das vendas simuladas e nova gravação cifrada.

## Validações ainda pendentes

1. Confirmar visualização das mensagens no iPhone e abertura dos botões no Phantom instalado, confirmando rede e endereço completos. A receção no Telegram Web não comprova notificações push no iPhone.
2. Melhorar e observar a regularidade do agendamento antes de depender dos avisos com dinheiro real. A existência de uma execução agendada não garante frequência, disponibilidade ou entrega. Não foi realizado um teste físico de desligar este computador durante a verificação.
3. Rever as respostas do utilizador às perguntas finais da formação antes de considerar dinheiro real.

**Monitorização configurada e ativada, com execuções cloud e entrega Telegram verificadas.** As verificações adicionais acima continuam pendentes; o agendamento não oferece uma garantia de disponibilidade. Não se enviou nem executou qualquer transação.

## Repetir

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m radar.app --dry-run
.\.venv\Scripts\python.exe scripts\live_check.py
```

Os dois últimos comandos precisam de Internet. O modo de ensaio guarda os resultados localmente em `data/dry-run.json`, fora do Git e separado do estado real. O relatório público contém só verificações técnicas e endereços de ativos públicos, sem posições ou identificadores Telegram pessoais.
# Pesquisa ampliada — 18/11/2026

113 testes Python e 5 testes do relógio passaram localmente. Novos casos: identidade/data/URL de vídeo YouTube, XML com DTD recusado, fontes indisponíveis sem interromper o mercado, cache, benchmark inválido sem preço inventado, contagem de repetidas/distintas, relatórios a cada 3h, amostra antiga sem moedas apresentadas como atuais, preservação do saldo/histórico, tendências quando pools novos falham e rotação da amostra.

Teste público real, sem enviar alertas ou alterar a carteira fictícia: 60 candidatos com 60 cotações, Solana (30), Base (20) e Ethereum (10), 23 pares com pelo menos 24h. Nenhuma entrada cumpriu todos os critérios. Um endpoint de novos pools Ethereum esteve indisponível e foi identificado. As contagens variam com a consulta. Os dois feeds YouTube e os três benchmarks Coinbase responderam; 10 títulos recentes retidos. Não foi demonstrada rentabilidade.

Diagnóstico agregado anterior à ampliação: a consulta de 18/11 às 14:01 UTC observou 30 candidatos; todos sem idade/histórico suficientes para a comparação de volume, 28 abaixo da liquidez mínima. O teste prospetivo tinha cerca de 25h, 1 000 € fictícios, zero calls e nenhuma taxa de acerto calculável. O universo foi ampliado sem apagar resultados nem afrouxar os filtros obrigatórios.
