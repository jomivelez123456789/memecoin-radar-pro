# Aprender a usar o radar, sem dinheiro real

Este guia começa com simulação. Nenhuma conclusão de lucro, segurança ou prontidão para investir foi validada. Memecoins podem perder todo o valor, ficar impossíveis de vender ou ter preços manipulados. Não é necessário depositar dinheiro para concluir os exercícios.

## Módulo 1 — Compreender os termos

| Termo | Significado prático |
| --- | --- |
| Memecoin | Token associado a uma piada, comunidade ou tema cultural, frequentemente com procura especulativa. Um nome conhecido não prova ligação oficial. |
| Blockchain | Registo partilhado de transações, com regras e ativos próprios. Uma transferência confirmada costuma ser irreversível. |
| Token | Ativo identificado por rede e endereço. Nome, símbolo e logótipo podem ser copiados. |
| Carteira | Aplicação que gere as chaves usadas para autorizar transações. Os ativos são registados na rede. |
| Solana | Rede cujo ativo nativo é SOL, utilizado para pagar taxas. Usa endereços diferentes dos EVM. |
| Ethereum | Rede cujo ativo nativo é ETH. Taxas variáveis podem tornar operações pequenas dispendiosas. |
| Base | Rede EVM de camada 2 que usa ETH para taxas. ETH em Ethereum e ETH em Base são saldos em redes distintas. |
| DEX | Protocolo onde se trocam ativos através de contratos e pools. Não há necessariamente uma entidade que reverta erros. |
| Agregador | Procura rotas entre DEXs para uma troca; pode cobrar comissões e não elimina riscos do token. |
| Exchange centralizada | Serviço que gere a negociação e normalmente guarda ativos numa conta. Pode exigir identificação e limitar levantamentos. |
| Gas/network fee | Custo de processamento na rede; pode existir mesmo numa tentativa falhada. |
| Liquidez | Recursos disponíveis para trocas num mercado. Pouca liquidez causa impacto elevado e pode impedir venda. |
| Market cap | Preço multiplicado pela oferta em circulação, quando essa oferta é conhecida. Não é dinheiro disponível para levantar. |
| FDV | Preço multiplicado pela oferta total/máxima conforme a fonte. Pode ser muito superior ao valor realizável. |
| Slippage | Diferença entre preço esperado e executado. A tolerância define o desvio aceite pela operação; aumentá-la pode piorar muito o resultado. |
| Price impact | Variação provocada pela tua própria troca na liquidez disponível; é diferente de movimento externo durante a execução. |
| Rug pull | Ação maliciosa, como retirar liquidez ou descarregar oferta concentrada, que prejudica compradores. |
| Honeypot | Token que permite comprar mas bloqueia ou penaliza severamente a venda. Um gráfico ativo não demonstra que tu possas vender. |

Uma carteira e uma exchange são produtos diferentes: numa carteira com autocustódia, perder as chaves pode significar perder o acesso. Uma DEX/agregador usa a carteira para pedir autorização. O radar só consulta dados e envia mensagens; não guarda fundos.

## Escolha inicial de aplicação

Para aprender no iPhone, a recomendação inicial é **Phantom como carteira, começando por observar Solana**. O radar já constrói links oficiais para a página do token e a aplicação inclui uma interface de troca. Isso reduz passos para um principiante, mas não torna as memecoins seguras. Base fica disponível para observação; aprender uma rede de cada vez reduz erros de transferência. Não ligar carteiras nem comprar é necessário para a simulação do bot.

| Opção | Tipo e redes relevantes | Custos e implicações | Uso inicial |
| --- | --- | --- | --- |
| Phantom | Carteira de autocustódia com swaps; Solana, Base e Ethereum entre as redes suportadas | Documentação indica 0,85% na maioria dos swaps, além de custos de rede/rota. Confirmar sempre a cotação real. Suporta links CAIP-19 e avisos, sem garantir deteção de fraudes. | Escolha inicial pela interface e link direto ao token. |
| Jupiter | Agregador/plataforma de negociação de Solana, usado com uma carteira | Custo varia com produto, rota, rede e eventuais taxas de plataforma; não assumir que é sempre gratuito. A cotação final deve discriminar custos. | Comparar cotações mais tarde; não necessário na primeira simulação. Evitar funcionalidades de alavancagem/perpétuos. |
| Coinbase Wallet / Base app | Carteira/interface distinta da exchange Coinbase; ecossistema EVM/Base e outros ativos conforme produto/versão | Ajuda oficial de swaps refere comissão até 1%, com possíveis custos de agregador e rede. Compatibilidade e funcionalidades variam por aplicação/versão. | Alternativa para uma futura aprendizagem centrada em Base, sem criar uma segunda carteira agora. |

As fontes oficiais consultadas não constituem confirmação individual de todas as funcionalidades em Portugal nem da disponibilidade na tua conta/App Store portuguesa. Verifica a página oficial na tua App Store e os avisos regionais da aplicação; compras por terceiros, Cash, cartões e outros produtos têm condições próprias. Não uses VPN para contornar restrições. Se uma função estiver indisponível, mantém a simulação e interrompe esse percurso.

Escolhe a instalação apenas a partir de [phantom.com](https://phantom.com/). Jupiter oficial: [jup.ag](https://jup.ag/). Para Base/Coinbase parte de [ajuda oficial](https://help.coinbase.com/en-ca/wallet/getting-started/dex-swap). Evita anúncios de pesquisa, mensagens privadas de “suporte” e links em nomes de tokens.

## Módulo 2 — Preparar a carteira, apenas quando fizer sentido

1. No site oficial Phantom, segue o link para a App Store. Confirma a origem antes de instalar; não instales perfis de configuração ou ficheiros enviados por terceiros.
2. Escolhe criar uma carteira nova seguindo o método disponível na tua versão. Para uma carteira com frase de recuperação, anota a frase offline, na ordem correta e num local privado. Não a fotografes, envies por email ou introduzas no radar. Outros métodos de recuperação exigem compreender as suas próprias condições.
3. Ativa bloqueio da aplicação, biometria e código do iPhone. Não partilhes ecrã durante a criação/recuperação. Mantém o sistema atualizado.
4. Aprende onde aparecem rede, endereço público de receção, saldo e histórico. Um endereço público pode ser usado para receber; a frase de recuperação autoriza acesso aos fundos.
5. **No exercício não deposites nada.** Para um eventual depósito futuro, a rede de levantamento e a rede da carteira devem coincidir. Confirma a origem do ativo, endereço e custos antes de uma transferência; nunca assumes que ETH em duas redes é intercambiável sem uma operação específica.
6. Compreende as taxas de compra na origem, levantamento, rede, swap e possível conversão EUR/USD. A infraestrutura do radar gratuita não elimina estes custos.
7. Encontra um token pelo contrato completo e pela rede. Se não aparecer, não escolhas um semelhante pelo nome. Pode não existir suporte ou rota de negociação.
8. Antes de qualquer autorização futura, verifica a aplicação, a rede, o que é enviado, o que é recebido, mínimo recebido e permissões pedidas. Aprovações de tokens EVM podem dar acesso a gastar um ativo; não assines permissões ilimitadas ou pedidos que não compreendas.

Nunca precisas de “validar” uma carteira numa página que pede a frase de recuperação para desbloquear um alerta. Não existe suporte legítimo do radar que a deva pedir.

## Módulo 3 — Ler um alerta e simular uma compra

Uma mensagem A significa que certos dados passaram filtros experimentais, não que devas comprar. B pede avaliação de uma saída; C assinala um risco ou ausência de dados. D ainda não existe nesta versão.

1. Abre a mensagem no Telegram e lê categoria, data/hora UTC e motivo. Um alerta antigo pode já não descrever o mercado atual.
2. Identifica rede e contrato. Copia o contrato com o botão; compara o endereço completo com o gráfico e a carteira. Nome e símbolo servem só para leitura.
3. Abre `Ver gráfico`. Consulta períodos diferentes, liquidez e atividade. Uma subida vertical com poucas transações, grandes spreads ou falta de liquidez não é confirmação de oportunidade.
4. Envia `/detail REDE CONTRATO` para consultar os filtros e as ausências de dados; a resposta chega numa execução posterior. Repara nas verificações on-chain que não existem.
5. Se tiveres instalado Phantom, `Abrir token no Phantom` deve mostrar a página do token na rede certa. **Nesta fase não inicies nem confirmes uma troca.** Se o link não abrir corretamente, interrompe e pesquisa pelo endereço. Abertura no iPhone ainda precisa deste teste manual.
6. Escolhe um montante fictício e converte-o em quantidade: quantidade = valor fictício / preço fictício. Regista taxas separadamente, em USD.
7. Numa compra real futura, terias de conferir preço/rota, impacto, tolerância de slippage, comissões e mínimo recebido antes de assinar. Não aumentes slippage repetidamente só para forçar uma operação.
8. Uma compra só está concluída depois de o histórico/explorador indicar sucesso na rede correta e o saldo corresponder. “Submetida” ou “pendente” ainda não é confirmação. Não repitas uma operação pendente.
9. No exercício, usa o comando abaixo para criar a simulação. Os números são **inteiramente fictícios**. WSOL é usado só por ter uma identidade conhecida para aprender comandos, não como exemplo de memecoin recomendada.

```text
/simulate solana So11111111111111111111111111111111111111112 100 0.1 0.20 80 130
```

Este comando regista: entrada fictícia a 100 USD, 0,1 unidades, valor de 10 USD, taxa de entrada 0,20 USD, stop de referência 80 USD e objetivo 130 USD. O mercado real de WSOL pode ser muito diferente: não interpretes alertas de nível desta posição de formação como recomendação.

10. Aguarda a próxima execução e guarda o ID devolvido pelo bot. Envia `/positions`. A posição deve estar identificada como `simulada`; o preço de referência será de mercado real quando disponível. P/L aberto é apenas uma estimativa, sem taxa futura de saída ou slippage.

Uma compra efetuada manualmente fora do bot só fica registada se usares `/register real` seguido dos mesmos sete campos. Usa preço médio efetivamente executado e quantidade efetivamente recebida. **Não uses esse comando no exercício.** Registar não comunica com a carteira.

## Módulo 4 — Simular uma venda e aprender a verificar uma saída

1. Envia `/positions` e encontra o ID, tipo, quantidade restante e preço de referência. Confirma a data da observação; pode estar desatualizada.
2. Num alerta B, lê se foi atingido um nível da posição ou se há deterioração do mercado. O bot não vendeu nada. Uma posição simulada continua simulada.
3. Para registar a venda fictícia de metade do exemplo a 120 USD, substitui `ID_DEVOLVIDO` pelo ID real que o bot te forneceu:

```text
/close ID_DEVOLVIDO 120 0.05 0.10
```

4. O resultado esperado desta parcela é `(120 − 100) × 0,05 − 0,20 × (0,05 / 0,1) − 0,10 = 0,80 USD`. Restam 0,05 unidades. O bot guarda preço, quantidade, custo e data do registo.
5. Para encerrar o restante a um preço fictício de 90 USD:

```text
/close ID_DEVOLVIDO 90 0.05 0.10
```

O resultado desta parcela é −0,70 USD; resultado realizado total de 0,10 USD. A quantidade restante deve ser zero. Já não deverá provocar alertas de posição aberta; acompanhamento manual ou por sinal é independente.

Numa venda real futura, abre o token na carteira, escolhe vender/trocar, confirma a rede e o ativo a receber, define a parcela e revê o valor líquido e mínimo recebido. Só confirma se compreenderes a autorização e os custos. Verifica o sucesso no histórico/explorador e o saldo recebido antes de registar o resultado no radar.

Uma venda pode falhar por falta de liquidez, gas insuficiente, slippage, congestionamento, bloqueio de transferências ou restrição do token. Pode executar a um preço muito inferior ao gráfico; uma tentativa falhada pode consumir taxas. Se uma operação parecer falhada, consulta primeiro o estado na rede antes de repetir. Nunca confundas valor de referência de uma carteira com dinheiro que podes retirar.

Não alteres o registo para fingir que uma venda falhada aconteceu. O radar não lê a tua carteira para corrigir os dados por ti.

## Módulo 5 — Gestão de risco e custos

Não foi avaliada a tua situação financeira. Não há recomendação de capital, percentagens pessoais ou valores a investir. Não uses dinheiro necessário para despesas, dívidas ou emergências e não uses alavancagem para este exercício.

Num exercício hipotético, define primeiro o valor total que podes perder na simulação e um limite por operação. Uma conta útil é:

`quantidade teórica = perda tolerada / (preço de entrada − stop)`

Esta conta ignora taxas, slippage, falha do stop e perda total; portanto **não limita garantidamente a perda**. Num token ilíquido/honeypot a perda pode ser todo o montante, mesmo que tenhas escolhido um stop próximo. O máximo por operação também tem de respeitar o orçamento de perda total, não apenas a conta do stop.

Stop-loss é uma condição pretendida de saída para limitar perdas; take-profit é uma condição de realização de ganho. Nem todas as DEXs suportam ordens condicionais e as soluções que existem têm condições e falhas próprias. Neste radar são apenas alertas periódicos. Mesmo uma ordem real pode falhar ou ser executada pior do que o nível pretendido.

Calcula resultado líquido: montante recebido na venda − custo efetivo de aquisição − comissões de entrada/saída − custos de rede e outros custos ainda não incluídos. Se o preço efetivo já reflete slippage, não o subtraias uma segunda vez. O bot guarda valores em USD e não calcula impostos ou efeitos EUR/USD; guarda os teus registos originais e consulta informação oficial aplicável antes de operações reais.

Não decidas por FOMO: uma subida que perdeste não cria obrigação de entrar. Observa o plano escrito antes do sinal. Rejeita urgência artificial, promessas de retorno, “suporte” por mensagem privada, pedidos de seed, airdrops com autorizações estranhas e tokens com contratos que não consegues confirmar. Muitas compras podem ser atividade artificial. Um falso sinal é uma possibilidade normal e não é resolvido duplicando a exposição.

## Módulo 6 — Exercícios e confirmação de compreensão

Faz estes exercícios sem assinar transações:

1. Dois tokens têm símbolo `DOG` e contratos diferentes. Explica porque são ativos diferentes. Repete com o mesmo contrato EVM em Base e Ethereum.
2. No gráfico de um token observado, identifica período, direção do preço, volume e liquidez. Distingue “o preço subiu” de “conseguiria vender este montante”. Se não houver candles/volume fiáveis, assinala a ausência.
3. Cria a posição fictícia do módulo 3. Confirma tipo `simulada` e valor de 10 USD, além da taxa.
4. Regista as duas vendas parciais do módulo 4. Confirma saldo zero e resultado total de 0,10 USD.
5. Calcula uma compra fictícia de 20 USD com taxa de 0,85%: 0,17 USD antes de rede/outros custos. Se a venda render 21 USD e cobrar também 0,85% (0,1785 USD), o ganho antes de outros custos é 0,6515 USD. Infraestrutura gratuita não significa negociação gratuita.
6. Recebes um B e a venda falha. Explica porque a posição continua aberta e porque precisas de verificar o estado na rede antes de repetir.
7. Recebes um A com contrato não auditado. Lista pelo menos três riscos que o radar não verificou.

Respostas de referência: (1) rede e endereço definem identidade; (4) 0,80 − 0,70 = 0,10; (6) alerta/registo não executa nem comprova venda; (7) holders, mint/freeze, LP, honeypot ou restrições de venda, entre outros.

**Antes de considerar dinheiro real, responde no chat, pelas tuas palavras:**

- Como confirmas que o token e a rede são os corretos?
- O que fazes com a frase de recuperação, e quem a pode pedir?
- Um alerta B ou um stop registado vende automaticamente?
- Como confirmas que uma transação foi executada e o que fazes se estiver pendente?
- Porque podes perder tudo mesmo quando o radar emite A?
- Como calculas o valor líquido depois de comissões e slippage?

A tua compreensão ainda não foi confirmada. Completar este documento ou instalar uma aplicação não substitui responder e corrigir dúvidas. Até lá, mantém apenas observação e simulações.
