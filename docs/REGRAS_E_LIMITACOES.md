# Regras, arquitetura e limites

## Decisão experimental

Não existe uma estratégia validada. O score é uma classificação de critérios, não uma probabilidade de lucro. Os valores iniciais são parâmetros de desenvolvimento, sem adequação financeira pessoal.

Cada critério vale 12,5 pontos: liquidez mínima de 50 000 USD; volume 1h mínimo de 10 000 USD; idade mínima do par de 6h; pelo menos 40 transações em 1h; fração de compras mínima de 58%; variação em 1h entre 2% e 35%; volume relativo mínimo 1,5; campos de mercado completos. **Todos os critérios são obrigatórios**; baixar `entry_score` não remove os filtros obrigatórios.

Volume relativo = volume da última hora / ((volume de 24h − volume da última hora) / 23). É exigida idade do par de pelo menos 24h para este cálculo, pelo que, apesar do filtro de idade de 6h, uma entrada só pode ocorrer com esse histórico mínimo. Zero, ausência ou inconsistência no denominador impede a entrada. Não usa candles inventados. Idade do par não prova a idade do token.

Pressão compradora = número de compras / (compras + vendas). Não mede capital líquido comprador nem carteiras únicas: bots e wash trading podem inflacionar a métrica. A API não fornece a hora da última negociação neste endpoint. `observed_at` é a hora UTC da consulta, não uma garantia de frescura do preço.

Os parâmetros estão em `config.json`. Altera-os com cuidado e volta a executar os testes. O bot não otimiza filtros para maximizar lucros.

## Categorias

| Categoria | Comportamento |
| --- | --- |
| A — Possível entrada | Cumpriu todos os filtros, sem risco observado nos campos disponíveis. Contrato não auditado; risco continua elevado. |
| B — Alerta de saída | Token acompanhado/sinalizado apresenta queda de preço de pelo menos 15%/1h, liquidez abaixo do mínimo, perda de pelo menos 40% de liquidez entre duas observações do mesmo par, ou uma posição atinge stop/objetivo registado. |
| C — Alerta de risco | Token acompanhado sobe acima de 35%/1h, ou há ausência de dados de tokens acompanhados. Não comprova fraude. Riscos de descida que também justificam saída são apresentados como B para evitar duplicação. |
| D — Contexto de notícia | Um RSS recente menciona o contrato completo e a rede de um token observado e existe atividade crescente sem os riscos de mercado filtrados. Não verifica a veracidade da notícia, não prova causalidade nem ligação oficial e não altera o score. |

Entradas não criam posições. Tokens com sinal A são candidatos a acompanhamento por 48h, dentro do limite de capacidade, dando prioridade aos sinais mais recentes. Posições abertas e até 30 tokens manuais têm prioridade e não são substituídos por novas descobertas. Uma posição aberta continua acompanhada até o saldo registado chegar a zero. «Só acompanhar» não significa compra.

O cooldown de alertas gerais por token/categoria é de seis horas. Nas posições, o aviso é separado por ID de posição, tipo (limite, objetivo ou risco) e versão dos níveis. Assim, atingir um objetivo depois de um limite não fica escondido pelo aviso anterior e outra posição na mesma moeda tem o seu próprio controlo. Repetições do mesmo tipo ainda podem ser suprimidas. Alterar os níveis volta a permitir avaliação dos novos níveis.

Cada posição aberta recebe também um resumo periódico no máximo a cada seis horas, sujeito à disponibilidade e limite de mensagens. Ausência de novo aviso não prova segurança nem recomenda manter. O resultado aberto é teórico, deduz a parte proporcional da taxa de entrada e não inclui taxa futura de saída/desvio de execução. Não há sincronização com carteiras.

Por execução há até oito alertas/resumos, com avisos de saída das posições primeiro. Notícias têm no máximo dois avisos por ciclo e só usam espaço restante. Tokens sem cotação geram um aviso agregado, no máximo a cada seis horas; confirmações de comandos e mensagem diária são adicionais. O limite pode adiar avisos de menor prioridade. A fila tenta entrega posterior, sem garantia de prazo. Sinais de mercado em fila com mais de 30 minutos são descartados para evitar entregar uma indicação antiga como atual; o cooldown pode continuar ativo. Pode haver duplicação numa falha ambígua.

## Cobertura e fontes

Solana e Base por defeito. Ethereum tem identificação e links preparados e pode ser acrescentada à configuração, mas as verificações reais desta entrega cobrem Solana e Base. Endereços EVM são normalizados para minúsculas; endereços Solana preservam maiúsculas e são validados como base58 de 32 bytes. Símbolos nunca são identificadores.

Perfis recentes do DexScreener e pools recentes do GeckoTerminal produzem uma amostra limitada de candidatos. Perfis e promoção podem ter viés comercial; não é um varrimento de todas as emissões nem uma classificação garantida de memecoins. A presença numa fonte não prova legitimidade. Até 16 candidatos por execução; até 100 tokens consultados, dando prioridade a posições, lista manual e sinais recentes. Até 30 posições abertas e 30 tokens manuais.

Para cada token, o radar escolhe o par com maior liquidez USD reportada em que o token é a base e a rede coincide. Não soma liquidez entre DEXs e não estima quanto conseguirias vender. Mudança de par não é interpretada como queda de liquidez entre observações. A API de mercado principal é DexScreener; GeckoTerminal complementa descoberta, não substitui cotações em caso de falha.

Espaçamento: DexScreener 0,3s entre pedidos, GeckoTerminal 2,1s, Telegram 1,1s. Endpoints de perfis têm limite anunciado de 60 pedidos/minuto; dados de tokens 300/minuto; GeckoTerminal público 30/minuto. O volume normal deste projeto é muito inferior; 429 usa espera limitada e nova tentativa. Não contorna bloqueios.

## Riscos que não são avaliados

Não há verificação de concentração/contagem de holders, carteiras relevantes, baleias, autoridades mint/freeze, extensões Token-2022, propriedade do contrato, permissões de transferência, taxa de venda, honeypot, liquidez bloqueada/queimada, concentração de LP ou possibilidade real de vender. Também não há simulação de transação on-chain.

Não existe um estado “seguro”. Os dados de mercado podem ser manipulados ou incorretos; os alertas só identificam anomalias observáveis. Não ligues uma carteira nem concedas permissões por confiar no score.

## Links e gráficos

Links para gráficos são construídos no domínio oficial DexScreener, com a rede e o par. O link de token usa o formato oficial `phantom.com/ul/v1/fungible` com CAIP-19: Solana mainnet (`solana:4sGjMW1sUnHzSxGspuhpqLDx6wiyjNtZ/spl:`), Base (`eip155:8453/erc20:`) e Ethereum (`eip155:1/erc20:`). Só abre a página do token, não uma ordem. O funcionamento final depende da versão do Phantom e da existência do token nessa aplicação. Um link válido não garante rota de swap nem liquidez.

Estrutura dos links e identificadores testados; **abertura real no iPhone ainda por confirmar pelo utilizador**. Se o link falhar ou abrir um token diferente, interrompe e pesquisa manualmente pelo contrato na rede correta. Não substituas por um token com símbolo semelhante.

As notificações usam links de gráficos. Imagens ficam para outra versão, com OHLCV real, volume, marca temporal do sinal e referências, sem candles reconstruídos a partir de preços isolados.

## Histórico e segurança

Estado local JSON com gravação atómica e bloqueio de processo. Contém dados de posições em texto simples, acessíveis à conta do computador; protege a sessão Windows e o disco. Não há carteira ligada. Só token Telegram e chave de cifragem são credenciais necessárias; não são guardados pelo assistente local.

Na cloud: chave Fernet em Actions Secrets; estado comprimido e autenticado/cifrado na branch `radar-state`. Escrita condicionada ao SHA anterior previne sobrescrever alterações concorrentes; o workflow serializa execuções. Estado ausente sem inicialização explícita, chave errada ou corrupção interrompem a execução. O horário e tamanho aproximado das atualizações cifradas ficam visíveis num repositório público, mas as posições não ficam legíveis sem chave.

Últimos 5000 sinais no estado atual; versões anteriores cifradas permanecem no histórico Git. Cada gravação cifrada é diferente e aumenta o tamanho do repositório; esta solução inicial precisa de revisão de armazenamento/arquivamento antes de uso prolongado. Não há exportação analítica, backtest nem avaliação estatística de rentabilidade. O estado tem limites de tamanho (20 MB antes de compressão, 900 kB cifrado); ao exceder, interrompe em vez de truncar dados de posições. A execução GitHub pode falhar antes de persistir; não há transação distribuída entre GitHub e Telegram nem garantia de entrega exatamente uma vez.

## Expansão prevista

RSS públicos configurados: Cointelegraph, Decrypt e CoinDesk. Na verificação real desta atualização, Cointelegraph e Decrypt responderam e CoinDesk ficou indisponível. O estado de cada fonte é mostrado em `/noticias`; uma falha não interrompe alertas de mercado. São consultados no máximo de 30 em 30 minutos. Guardam-se títulos, links, hora de publicação indicada pela fonte e menções explícitas a redes/contratos; não se copiam artigos completos.

A ligação a um token exige endereço completo e rede no texto disponibilizado pelo RSS, juntamente com atividade crescente nos dados de mercado. Títulos podem estar errados ou ser incompletos; não há verificação independente dos factos nem leitura de toda a Internet. Uma notícia sobre GTA 6 não prova ligação oficial de um token ao jogo. Uma correspondência por nome ou símbolo nunca basta. Não há prémio no score por notícias.

X, Telegram público, Reddit, TikTok, Instagram e YouTube não são monitorizados nesta versão. Disponibilidade, autorização e limites devem ser avaliados antes de criar cada integração. Não há scraping de conteúdos privados nem contorno de restrições. A categoria D fornece contexto de uma fonte identificada, não uma recomendação de compra.

Prioridades seguintes: ativação real, confirmação de links iPhone, auditoria on-chain gratuita com estados desconhecidos explícitos, exportação e avaliação de sinais, e só depois tendências e imagens.
