# Registo de validação — 12 e 13/11/2026

## Atualização de experiência e acompanhamento

**86 testes Python locais e 4 testes do relógio opcional passaram.** Os 83 testes da atualização visual passaram também no GitHub no commit `8c6481f`. A suite inclui os 48 testes anteriores e casos de formulários com vírgulas decimais, validação atómica, venda parcial/total, alteração de níveis, cancelamentos antigos, botões expirados, autorização e repetição de callbacks, compatibilidade do estado existente, prioridade das posições perante novos sinais, limites de mensagens, proteção de XML/links/notícias e aviso de interrupções observadas.

Teste real de notícias: Cointelegraph e Decrypt responderam; CoinDesk foi marcado indisponível. Foram retidos 40 títulos/links recentes, sem copiar artigos nem associar moedas pelo símbolo. Esta recolha não valida a veracidade dos títulos ou uma estratégia de lucro.

### Verificação real da versão visual, em 13/11/2026

- [Ajuda com emojis e formulário de simulação](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43339035184): sucesso e mensagens recebidas no Telegram.
- [Registo guiado, notícias e aviso de saída individual](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43339248832): sucesso. O aviso identificou explicitamente a simulação, explicou a perda estimada e mostrou níveis e botões.
- [Botão «Registar venda»](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43339433661): callback processado e formulário recebido, sem transações.
- [Venda fictícia com vírgulas decimais e consulta de posições](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43339628142): sucesso; registo encerrado e zero posições abertas. O teste não avaliou uma estratégia de lucro.
- [Uma execução por horário foi confirmada](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43323546163), às 22:50 UTC de 12/11, após uma consulta manual às 17:35. As respostas que aguardavam na fila chegaram às 22:50. Este intervalo observado de horas impede apresentar o cron do GitHub como vigilância frequente garantida.

O relógio Cloudflare está preparado mas NÃO foi ativado; precisa de conta e autorização específica para uma credencial limitada. Os quatro testes desse componente são locais, com credencial fictícia e sem pedidos externos. A nota de interrupções do radar só consegue avisar quando uma execução volta a ocorrer.

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
