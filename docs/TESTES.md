# Registo de validação — 12/11/2026

## Atualização de experiência e acompanhamento

**83 testes locais passaram** após acrescentar mensagens simples, botões, formulários em português, resumos por posição, avisos independentes por posição/nível e RSS. A suite inclui os 48 testes anteriores e 35 casos adicionais: formulários com vírgulas decimais, validação atómica, venda parcial/total, alteração de níveis, cancelamentos antigos, botões expirados, autorização e repetição de callbacks, compatibilidade do estado existente, prioridade das posições perante novos sinais, limites de mensagens e proteção de XML/links/notícias.

Teste real de notícias: Cointelegraph e Decrypt responderam; CoinDesk foi marcado indisponível. Foram retidos 40 títulos/links recentes, sem copiar artigos nem associar moedas pelo símbolo. Esta recolha não valida a veracidade dos títulos ou uma estratégia de lucro.

Publicação e teste real dos novos botões/formulários são verificados durante a entrega desta atualização; o histórico abaixo descreve a primeira versão já validada.

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
2. Confirmar uma execução disparada pelo agendamento e uma execução posterior com o computador desligado.
3. Rever as respostas do utilizador às perguntas finais da formação antes de considerar dinheiro real.

**Monitorização configurada e ativada, com execuções cloud e entrega Telegram verificadas.** As verificações adicionais acima continuam pendentes; o agendamento não oferece uma garantia de disponibilidade. Não se enviou nem executou qualquer transação.

## Repetir

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m radar.app --dry-run
.\.venv\Scripts\python.exe scripts\live_check.py
```

Os dois últimos comandos precisam de Internet. O modo de ensaio guarda os resultados localmente em `data/dry-run.json`, fora do Git e separado do estado real. O relatório público contém só verificações técnicas e endereços de ativos públicos, sem posições ou identificadores Telegram pessoais.
