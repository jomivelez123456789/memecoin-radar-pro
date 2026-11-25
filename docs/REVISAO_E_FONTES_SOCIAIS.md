# Revisão e investigação social — 25/11/2026

## Diagnóstico observado

Auditoria de todas as 56 posições fictícias e dos alertas originais: 51 encerradas, 18 com ganho, 33 com perda, resultado realizado −122,61 €. Ganhos somados 316,28 €, perdas somadas 438,89 €. A mesma sequência de cotações, sem custos, daria +85,80 €; a diferença de 208,41 € vem do modelo de taxas/desvios, não de comissões reais medidas. O saldo com abertas varia e não é um saldo bancário. As contas entre caixa, montantes abertos e resultados realizados conferiram.

Os níveis −10%/+20% referem-se a movimentos da cotação em euros antes de custos. Não garantem uma perda máxima de 10% ou lucro líquido de 20%. Houve perdas superiores ao nível entre observações. Apenas uma call fechada tinha a marca de intervalo >15min; era vencedora. Não se atribuem todas as perdas a atrasos. Duas saídas de Pump coincidiram com alertas próximos de um par diferente: isso motivou consultar o par original, sem reescrever resultados antigos nem afirmar causalidade comprovada.

## Revisão automática e hipótese nova

`/aprender` (atalho `/erros`) apresenta resultados, custos teóricos, versões e incidentes. Cada encerramento novo recebe uma revisão descritiva, uma única vez. A entrada guarda cópia da cotação, análise, par e versão do código; a saída guarda par e riscos observados. Entradas antigas só recuperam evidência de um único alerta A com contrato/rede/instante exatos, identificando a recuperação posterior.

A partir da nova versão, uma possível entrada precisa de outra consulta qualificada do mesmo par, separada por 3–10 minutos. A moeda pendente continua a ser consultada mesmo que deixe a lista de descoberta. Uma falha dos filtros ou intervalo excessivo obriga a recomeçar a confirmação. Duas perdas fictícias fechadas no mesmo contrato/rede nos últimos 72h suspendem novas calls desse contrato até a condição deixar de se aplicar. Posições existentes continuam acompanhadas.

Esta política é um teste prospetivo, não uma otimização comprovada. A mesma memória pode impedir uma entrada que acabaria vencedora. Não se eliminam perdas, não se baixam custos e não se aumenta exposição para recuperar perdas. O histórico continua acumulado; a versão em cada entrada permite separar períodos. O registo de incidentes começa na ativação desta atualização e não reconstrói todos os erros antigos.

## Cobertura social real

- **X:** leitura sem sessão do HTML público de `x.com/coinbureau`, perfil ligado pelo site do próprio editor. Apenas strings JSON de dados são descodificadas: nenhum código da página é executado. Aceitam-se autor exato, identificador e data válidos, até 48h. Lê texto, não áudio/vídeo/comentários; opiniões não são factos verificados. Esta estrutura pública pode mudar ou ser bloqueada.
- **Reddit:** [pré-visualizações Redlisten sem chave](https://www.redlisten.com/docs#previews-without-a-key), fornecedor independente do Reddit. São amostras limitadas, não todo o Reddit nem todas as publicações. Consultas horárias; data do fornecedor visível. Rejeitam-se amostras atualizadas há mais de 24h e posts fora das 48h. O teste aceitou amostras de r/solana e r/CryptoCurrency; rejeitou r/memecoins por atualização antiga. Nenhuma conta foi criada nem cartão introduzido.
- **TikTok:** a visita manual ao perfil público Coin Bureau mostrou descrições e links. O servidor do bot recebeu uma página sem publicações legíveis: a recolha automática não ficou confirmada. A tentativa pública a cada 6h regista esse limite. O [Research API](https://developers.tiktok.com/docs/en/research-api-faq/) requer elegibilidade/aprovação; não foi ativado. oEmbed do perfil só devolveu código de incorporação, sem dados de posts úteis para este coletor.
- **Instagram:** o perfil ligado pelo site Coin Bureau apareceu indisponível na visita manual. O coletor público não obteve posts validados. Não existe autorização Instagram nem acesso abrangente a contas públicas configurado.
- **APIs pagas/restritas:** a [API X](https://docs.x.com/x-api/getting-started/pricing) cobra por utilização; não foi ativada. A [Meta Content Library API](https://developers.facebook.com/docs/content-library-and-api/content-library-api/overview) funciona em ambientes de investigação aprovados; não é uma API geral livre para este bot. O [Reddit terminou suporte RSS em 13/11](https://support.reddithelp.com/hc/en-us/articles/54353370049684-Changelog-October-8-2026); não se usam esses feeds nem endpoints privados.

`/sociais` mostra fontes, datas, amostras e bloqueios. Uma resposta HTTP 200 sem posts não conta como acompanhamento. As informações sociais dão contexto e não aumentam o score nem contornam critérios de entrada. Não há leitura de contas privadas, mensagens ou sessões pessoais, nem contorno de CAPTCHA/login.

## Validação

130 testes Python passaram localmente antes da entrega (o total pode crescer com correções posteriores). Incluem confirmação temporal/par exato, memória de perdas só de resultados passados, manutenção da consulta de candidatos pendentes, recuperação exata de alertas antigos, par original ausente sem substituir por outro, preservação de saldo/perdas, custos, fontes sociais inválidas, autor/data X, URLs externas recusadas, cache e amostras antigas. Cotações dos pares originais foram testadas sem alterar o estado remoto: quatro de cinco responderam nessa consulta; um ficou sem cotação. Ausência de cotação não é preço zero nem venda inventada.
