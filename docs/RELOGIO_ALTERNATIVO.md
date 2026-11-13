# Relógio alternativo — preparado, não ativado

O teste real mostrou uma execução `schedule` do GitHub às 22:50 UTC de 12/11/2026, depois de uma consulta manual às 17:35. Os pedidos de ajuda na fila foram respondidos às 22:50. Portanto, o agendamento nominal de poucos minutos não comprovou vigilância frequente nesse período. Não deve ser apresentado como proteção fiável para saídas com dinheiro real.

Foi preparado um pequeno Worker em `cloudflare/clock.mjs`, com configuração em `cloudflare/wrangler.toml`. Apenas pede ao GitHub para executar o radar; mantém o código Python, o token Telegram e a chave do histórico no GitHub. Não executa transações, não lê posições e não instala acesso remoto ao computador.

Publicar estes ficheiros no GitHub NÃO ativa um serviço Cloudflare. A ativação fica pendente de autorização específica e de uma conta Cloudflare. Não se cria conta, aceita termos, contrata plano pago ou introduz cartão automaticamente.

## Permissão necessária, se for autorizado

Um token GitHub de permissões finas, limitado **só a este repositório**, com `Actions: write`, seria guardado como segredo `GITHUB_DISPATCH_TOKEN` no Worker. Isso permite iniciar workflows existentes; não permite alterar código nem consultar os valores dos Actions Secrets. Não se deve conceder acesso a todos os repositórios, escrita de conteúdos ou administração. Não se deve enviar o token para chats, código, variáveis públicas ou logs.

Esta é uma nova transmissão de uma credencial para um serviço externo e precisa de autorização explícita antes da criação/configuração. Os tokens existentes do Telegram e da cifragem não são necessários nesse serviço.

## Limites e custos

A documentação oficial de [Workers Free](https://developers.cloudflare.com/workers/platform/pricing/) indica franquias gratuitas; [Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/) permite tarefas agendadas. O relógio prevê 288 pedidos/dia e um pedido ao GitHub por invocação. Só deve ser ativado no plano gratuito, sem cartão nem pagamentos. Se a plataforma exigir custos ou um cartão, interromper.

É uma alternativa para reduzir a dependência do relógio do GitHub, **não uma garantia de disponibilidade, prazo ou lucro**. Ainda podem existir falhas do relógio, atrasos na fila de runners, APIs indisponíveis ou problemas de entrega Telegram. O início de um workflow não prova que a análise tenha terminado nem que um aviso tenha chegado.

## Antes de considerar ativado

1. Autorizar o serviço e a credencial limitada; iniciar sessão pessoalmente se necessário.
2. Confirmar o plano gratuito e os limites atuais, sem adicionar pagamento.
3. Criar/configurar o segredo exclusivamente através da área segura do serviço.
4. Publicar o Worker e confirmar dois disparos agendados, os runs correspondentes no GitHub e a entrega no Telegram.
5. Só depois rever a redundância com o cron do GitHub e documentar os intervalos observados.

Ainda não se realizou nenhum destes passos de ativação. A ferramenta de teste local usa credenciais fictícias e não envia pedidos externos.
