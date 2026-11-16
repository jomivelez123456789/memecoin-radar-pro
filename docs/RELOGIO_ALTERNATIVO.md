# Relógio externo Cloudflare — correção de 16/11/2026

O cron do GitHub apresentou intervalos de horas. Foi publicado um pequeno Worker em `cloudflare/clock.mjs`, configurado para pedir uma análise ao GitHub a cada cinco minutos. A análise continua a decorrer no GitHub e não depende de manter este computador ligado. O cron do GitHub mantém-se como alternativa.

## Estado confirmado

- O proprietário autorizou o serviço e os acessos limitados e entrou pessoalmente na conta Cloudflare.
- Plano **Workers Free** ativo, sem método de pagamento associado. Não foi contratado um plano pago.
- `GITHUB_DISPATCH_TOKEN` guardado como **Secret / Value encrypted** na Cloudflare, só em produção.
- Credencial GitHub de permissões finas: apenas `memecoin-radar-pro`, `Actions: read/write` e leitura obrigatória de metadados. Sem escrita de código, administração ou acesso a carteiras. Actions permite gerir execuções e artefactos desse repositório; não é uma permissão exclusiva de dispatch.
- Primeira publicação em 13/11/2026; código corrigido e republicado em 16/11/2026, com horário `1-59/5 * * * *`, URLs de produção e preview desativados e sem registo de logs/traces.
- Os acessos Cloudflare usados para publicar tinham **Individual Workers Editor** apenas neste Worker e foram revogados após a instalação e após a correção. A cópia local cifrada da credencial foi removida. O diagnóstico temporário foi desativado após a correção. Não foi concluída autorização OAuth abrangente da conta.

Em 16/11/2026 foi corrigida uma incompatibilidade com o runtime Cloudflare: `redirect: error` impedia o pedido antes de contactar o GitHub. O código passou a usar `redirect: manual`, recusando respostas de redirecionamento, e a aceitar os códigos de sucesso 200/204 da API GitHub. O horário foi novamente registado. Cinco testes locais do relógio passaram, incluindo a recusa de redirecionamentos sem reencaminhar credenciais.

Duas análises automáticas foram confirmadas em 16/11/2026: [primeira](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43927860052), pedida às 18:20:53 UTC, e [segunda](https://github.com/jomivelez123456789/memecoin-radar-pro/actions/runs/43928718040), pedida às 18:25:52 UTC. Ambas terminaram com sucesso. A ajuda e o estado chegaram ao Telegram às 18:21 e 18:26 UTC. A segunda resposta confirmou o radar a funcionar, com 16 moedas observadas e zero dados ausentes. São duas observações de funcionamento, não uma garantia de disponibilidade futura. Publicação/configuração, início de uma execução, conclusão da análise e entrega da mensagem são etapas diferentes.

## Renovar antes de 13/12/2026

A credencial GitHub expira em **13 de dezembro de 2026**. Antes dessa data:

1. No GitHub, abre Settings → Developer settings → Personal access tokens → Fine-grained tokens.
2. Cria uma substituta limitada apenas a este repositório e às mesmas permissões. Não concedas escrita de conteúdos nem acesso a todos os repositórios.
3. Na Cloudflare, abre Workers & Pages → memecoin-radar-clock → Settings → Runtime variables and secrets.
4. Atualiza `GITHUB_DISPATCH_TOKEN` como **Secret**, apenas em produção. Nunca coloques o valor no código, em chats ou numa variável pública.
5. Confirma uma análise automática terminada no GitHub e uma resposta a `/estado` no Telegram antes de revogar a credencial antiga.

Se a credencial expirar, o relógio externo deixa de conseguir iniciar análises. O cron GitHub pode continuar, mas já mostrou atrasos de horas. Não existe renovação automática, disponibilidade garantida ou proteção de saída.

## Dados e limites

A Cloudflare recebe a credencial limitada GitHub para iniciar verificações. Não recebe o token Telegram, a chave do histórico nem dados das posições. O Worker só usa o endereço fixo do workflow do radar, com `initialize: false`; não executa transações e não instala acesso remoto ao computador.

O horário prevê 288 pedidos por dia e um pedido GitHub por invocação. O plano [Workers Free](https://developers.cloudflare.com/workers/platform/pricing/) tem limites; não equivale a um serviço ilimitado ou garantido. [Alterações de cron](https://developers.cloudflare.com/workers/configuration/cron-triggers/) podem demorar até 15 minutos a propagar. Ainda podem existir falhas do relógio, filas GitHub, APIs indisponíveis e falhas Telegram.

## Parar

Para suspender o relógio, remove o cron em Workers & Pages → memecoin-radar-clock → Settings → Cron triggers. Para impedir também o agendamento alternativo GitHub, abre Actions → Memecoin Radar → Disable workflow. Nenhuma destas ações vende ativos ou altera saldos de carteiras. Para voltar a publicar código, será necessário criar um novo acesso de publicação limitado e revogá-lo no fim.
