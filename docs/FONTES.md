# Fontes oficiais consultadas

Verificação em 12/11/2026. Preços, limites, interfaces e disponibilidade regional podem mudar; confirmar novamente antes de ativar serviços ou usar fundos.

- [DexScreener — API](https://docs.dexscreener.com/api/reference): perfis recentes, dados por rede/contrato, limites e campos de pares.
- [GeckoTerminal — API pública](https://api.geckoterminal.com/docs/index.html) e [limite público de 30 pedidos/minuto](https://support.coingecko.com/articles/6867086195-does-geckoterminal-have-an-api).
- [Telegram — Bot API](https://core.telegram.org/bots/api): getUpdates, sendMessage, botões, copy_text e autenticação por token.
- [GitHub — faturação de Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions): runners padrão gratuitos em repositórios públicos; franquias e cobrança de outros recursos. Não assumir uma franquia antiga fixa de 2000 minutos em contas privadas.
- [GitHub — eventos schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule): atrasos, tarefas omitidas, branch principal, mínimo de cinco minutos e desativação por inatividade.
- [Phantom — links de token](https://docs.phantom.com/phantom-deeplinks/other-methods/fungible): CAIP-19 e abertura de página sem sessão nem assinatura.
- [Phantom — swaps e custos](https://help.phantom.com/articles/5985106844435): utilização e taxa de 0,85% na maioria dos swaps, além de outros custos.
- [Phantom — limitações regionais](https://help.phantom.com/articles/if-a-feature-is-unavailable-in-your-country-or-region-36291719105299): funcionalidades dependem do país/produto; não valida automaticamente uma conta portuguesa.
- [Jupiter — documentação oficial](https://dev.jup.ag/): infraestrutura de agregação/swaps. Não se assume negociação sem custos nem é utilizada a API de execução.
- [Coinbase — swaps em DEX](https://help.coinbase.com/en-ca/wallet/getting-started/dex-swap): carteira distinta da exchange, taxas até 1% e possíveis custos adicionais.
- [Cryptography — documentação](https://cryptography.io/en/50.0.2/): biblioteca de cifragem utilizada, versão fixada e instalada a partir do PyPI.
- RSS públicos de [Cointelegraph](https://cointelegraph.com/rss), [Decrypt](https://decrypt.co/feed) e [CoinDesk](https://www.coindesk.com/arc/outboundfeeds/rss/): títulos e links, sem reprodução de artigos completos. Na atualização de experiência, os dois primeiros responderam; CoinDesk não respondeu ao cliente. Disponibilidade não garante veracidade editorial.

Os hashes das Actions foram comparados com as referências oficiais da API GitHub e estão registados em `LIVE_CHECK.json`. Os testes unitários usam dados sintéticos identificados como exemplos e não são prova de eficácia de trading.
