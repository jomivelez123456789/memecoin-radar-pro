# Teste automático com saldo fictício em euros

Este ensaio usa cotações futuras observadas pelo radar. Não compra, vende, liga carteiras ou usa dinheiro real. Os exemplos e posições manuais antigos não entram nos resultados deste teste.

## Contas que aparecem no Telegram

- `/teste_iniciar`: inicia 1 000 € fictícios. Repetir este comando mantém saldo/histórico; não apaga perdas. Se estava pausado, retoma novas entradas.
- `/resultados` (ou `/teste`): mostra saldo disponível, saldo estimado incluindo abertas, resultado das calls fechadas, rendimento do saldo e taxa de acerto.
- `/teste_parar`: pausa novas entradas; as posições fictícias já abertas continuam acompanhadas até ao encerramento.
- Há aviso por entrada/saída e um resumo a cada seis horas. Comandos aguardam a próxima execução.

**Taxa de acerto** = calls simuladas fechadas com lucro / todas as calls simuladas fechadas, incluindo empates. Uma vencedora em uma encerrada dá 100% de acerto; não significa ganhar 100% do dinheiro. Abertas e casos sem cotação não são contados como vitórias. O relatório mostra também quantas calls ficaram de fora por limites ou dados em falta.

**Rendimento em euros** = (saldo total estimado / saldo inicial − 1) × 100. Se houver posições sem cotação, sem câmbio válido ou sem valor para cobrir os custos de saída assumidos, o saldo total e o rendimento ficam por apurar. O resultado das fechadas é mostrado separadamente. Não se inventa preço zero nem se omitem perdas do histórico.

## Protocolo inicial, definido antes das novas calls

- Saldo inicial: 1 000 €; até 100 € por call, incluindo custos de entrada; no máximo cinco abertas.
- Entram apenas os alertas A realmente emitidos após o início. Sem call que cumpra todos os filtros, não se força uma compra.
- A descoberta passa de até 16 para até 30 candidatas por consulta. Os filtros de entrada não foram abrandados. Isto não é toda a Internet nem todas as moedas.
- Custo fictício em **cada** lado: 1% do montante mais 0,05 €. Preço de entrada 1% desfavorável e preço de saída 1% desfavorável. São hipóteses do ensaio, não tarifas nem condições reais verificadas.
- Limite de perda: 10%; objetivo: 20%, em relação ao preço de referência em euros. Há saída também por risco de mercado ou após 48 horas, à primeira observação válida disponível.
- O teste usa o preço observado no momento da saída. Se um intervalo ultrapassou o limite, não assume venda ao preço ideal do limite. Fica registado que houve um intervalo.
- As contas de saída são arredondadas ao cêntimo. Cotações não comprovam execução, impostos, taxas reais, liquidez utilizável, impacto de uma ordem ou possibilidade de vender o token.
- O histórico do ensaio e a configuração inicial ficam no estado cifrado do radar. Não há reinicialização automática para apagar perdas.

## Euros e câmbio

As fontes de mercado devolvem preços em USD. O ensaio divide a cotação em USD pelo número de USD por euro da referência diária do [BCE](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html). Guarda a taxa e a data na entrada e na saída, pelo que variações do câmbio podem afetar o resultado em euros.

É uma referência informativa diária, não a taxa que um banco/carteira executaria. O relatório mostra a data. A referência é atualizada de seis em seis horas; após falha, tenta novamente em quinze minutos. Uma referência com mais de quatro dias é recusada, incluindo para novas entradas. A ligação TLS continua validada usando autoridades Mozilla; não se desativam verificações de certificados.

O teste automático está em EUR. Os formulários manuais antigos de compras/simulações continuam a exigir USD; são registos separados, não são somados a esta carteira fictícia.

## O que estes resultados provam

Testes automáticos de software usam cenários artificiais para verificar contas, perdas, faltas de dados, limites, câmbio e recuperação. Passarem não demonstra uma estratégia rentável. Só as novas calls acompanhadas no mercado alimentam o ensaio prospetivo. Uma amostra pequena, mesmo com 100% de acerto, não permite concluir lucro futuro.

## Emails e intervalos de novembro de 2026

Foram confirmadas falhas de API em execuções de 16/11, incluindo às 22:26 e 22:31 UTC. Os registos antigos apenas dizem `ApiError`; não identificam com certeza o serviço que falhou. Em 17/11, as 25 execuções mais recentes consultadas, entre 10:56 e 12:56 UTC, concluíram com sucesso em intervalos de cinco minutos. Isto não apaga os intervalos anteriores nem garante o horário futuro.

A atualização acrescenta diagnóstico com etapa, serviço e código HTTP, sem texto de exceções, URLs com segredos ou conteúdos de respostas. Numa falha ambígua ao guardar, consulta primeiro o ficheiro remoto: se já estiver guardado, não repete; se o estado tiver mudado, recusa sobrescrever; se estiver inalterado e a falha for transitória, faz uma tentativa adicional limitada. Não silencia emails de falha nem avisos de intervalos.
