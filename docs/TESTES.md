# Registo de validação — 12/11/2026

## Testes locais concluídos

**48 testes automáticos passaram**, sem chamadas externas, em Python 3.14.5 no Windows. A sintaxe de todos os módulos/scripts foi verificada. O workflow está preparado para repetir os testes com Python 3.12 no GitHub; essa execução remota ainda não foi feita.

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

## Validações que precisam da configuração do utilizador

1. Criar o bot e confirmar entrega real da mensagem de teste no iPhone.
2. Publicar o repositório e configurar os segredos.
3. Executar o workflow remoto, confirmar gravação/recuperação em duas execuções consecutivas e processamento de comandos.
4. Testar os botões no Phantom instalado no iPhone, confirmando rede e endereço completos. Validação de formato não equivale a um teste no dispositivo.
5. Criar uma simulação e registar venda parcial/total pelo Telegram.
6. Confirmar uma execução remota posterior com o computador desligado.
7. Rever as respostas do utilizador às perguntas finais da formação antes de considerar dinheiro real.

Estes passos estão pendentes; **o bot ainda não está ativo no Telegram nem no GitHub**. Não se enviou nem executou qualquer transação.

## Repetir

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m radar.app --dry-run
.\.venv\Scripts\python.exe scripts\live_check.py
```

Os dois últimos comandos precisam de Internet. O modo de ensaio guarda os resultados localmente em `data/dry-run.json`, fora do Git e separado do estado real. O relatório público contém só verificações técnicas e endereços de ativos públicos, sem posições ou identificadores Telegram pessoais.
