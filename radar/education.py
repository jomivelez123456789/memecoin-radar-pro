"""Ajuda prática, sem transações, credenciais ou recomendações de montantes."""
GUIDE = "https://github.com/jomivelez123456789/memecoin-radar-pro/blob/main/docs/FORMACAO.md"
PAGES = {
    "ajuda": """🧭 <b>O teu radar, em linguagem simples</b>

🟡 <b>Possível entrada</b> = há atividade que passou filtros. Não significa que devas comprar, nem que a moeda seja segura.
🟠 <b>Rever saída</b> = atingiste um nível que registaste ou apareceu um risco. O bot NÃO vende.
🔴 <b>Risco</b> = aconteceu algo preocupante ou faltam dados.

<b>Se escolheres uma moeda:</b>
1️⃣ Abre o gráfico e confirma rede e contrato.
2️⃣ Começa por carregar em «🧪 Simular» no alerta.
3️⃣ Se um dia comprares manualmente, usa «📝 Já comprei». Só então será uma posição tua no radar.
4️⃣ O bot continua a verificar TODAS as tuas posições abertas, mesmo quando aparecem outras moedas.
5️⃣ Depois de venderes manualmente, regista a venda. Receber um alerta não fecha a posição.

📚 /comprar — passos para comprar/simular
💸 /vender — passos para vender e registar
💳 /depositar — compreender como entram fundos
🏦 /retirar — compreender como voltam ao banco
🎯 /saidas — quando aparecem avisos de saída
💼 /posicoes — ver as moedas que registaste
📰 /noticias — fontes disponíveis e notícias recentes
📡 /estado — última verificação
🛑 /cancelar — cancelar um formulário

⏳ Consultas previstas a cada 5 minutos; o GitHub pode atrasá-las. Respostas e botões também aguardam uma execução. Não é um serviço em tempo real.
💵 USD significa dólares americanos. Não mistures preços em euros com preços em dólares no registo.
🔐 Nunca envies frases de recuperação, chaves ou palavras-passe.""",
    "comprar": """🛒 <b>Comprar: começa SEM dinheiro real</b>

1️⃣ No alerta, abre «📈 Gráfico». Confirma a rede e o contrato completo. O nome pode ser copiado por burlões.
2️⃣ Para aprender, usa «🧪 Simular»: isso só cria um registo fictício no radar. Não precisas de carteira nem de depósito.
3️⃣ Para uma eventual compra manual futura, instala Phantom apenas em https://phantom.com e protege a recuperação offline. Não a partilhes.
4️⃣ «👛 Abrir no Phantom» abre a página do token. Confirma novamente a rede e o endereço; não aceites um token parecido.
5️⃣ Na carteira, a opção de compra/troca permite escolher o ativo de pagamento e o montante. Lê quantidade recebida, mínimo recebido, impacto no preço e TODAS as taxas. Não forces uma troca aumentando o desvio aceite (slippage).
6️⃣ Só uma transação confirmada na rede significa compra executada. «Pendente» ainda não significa sucesso.
7️⃣ Depois de uma compra manual confirmada, usa «📝 Já comprei» no alerta. Preenche os dados REAIS da execução e os níveis que decidiste acompanhar.

⚠️ O bot não compra, não aprova transações e não verifica se consegues vender. Uma memecoin pode perder tudo.
📘 Primeiro faz os exercícios do guia. /depositar explica fundos; /saidas explica os níveis.""",
    "vender": """💸 <b>Vender: o alerta não vende por ti</b>

1️⃣ Abre /posicoes e identifica a posição e a rede certas.
2️⃣ Lê o aviso: pode ser «limite de perda atingido», «objetivo atingido» ou «mercado piorou». Não é garantia de execução.
3️⃣ Para uma venda real, abre o token no Phantom e a opção de vender/trocar. Escolhe a parcela e o ativo a receber, na MESMA rede.
4️⃣ Revê o valor líquido, mínimo recebido, taxas e impacto no preço. Só tu decides se confirmas.
5️⃣ Espera pela confirmação na rede e confere o saldo recebido. Se ficar pendente, verifica o histórico antes de repetir. Uma tentativa falhada pode gastar taxas.
6️⃣ Só DEPOIS usa «📝 Registar venda» em /posicoes, com preço executado, quantidade vendida e taxas. O radar não vê a carteira.

🧪 Numa posição simulada, esses passos são apenas um exercício: regista um preço fictício, sem abrir uma transação.
🏦 Trocar uma moeda por SOL/USDC não envia euros para o banco. Para essa etapa lê /retirar.
🔒 Enquanto não compreenderes estes passos, mantém apenas simulações.""",
    "depositar": """💳 <b>Como entram fundos — formação</b>

🧪 Por agora, não precisas de depositar nada: /comprar explica a simulação.

Se mais tarde decidires usar fundos, depois de compreenderes os riscos:
1️⃣ Uma carteira e uma exchange são coisas diferentes. Uma exchange pode permitir comprar cripto com euros; disponibilidade, identificação e taxas dependem do serviço.
2️⃣ Na carteira oficial, «Receber» mostra um ENDEREÇO PÚBLICO e uma rede. A frase de recuperação nunca é um endereço de depósito.
3️⃣ A rede de saída na origem tem de ser exatamente a rede de destino. SOL em Solana e ETH em Base são percursos diferentes; não uses bridges nesta aprendizagem.
4️⃣ Antes de transferir, confere endereço completo, ativo, rede, taxa de levantamento e mínimo. Uma transferência confirmada geralmente não pode ser revertida.
5️⃣ Confirma o estado na rede e o saldo na carteira. Reserva o ativo nativo necessário para taxas; não suponhas que todo o saldo pode ser gasto na compra.

⚠️ Não indico um montante pessoal nem escolho uma exchange sem avaliar requisitos e custos. Não envies dinheiro para pessoas ou endereços apresentados como «suporte».
📚 Consulta o guia e esclarece dúvidas ANTES de transferir. Nenhum pagamento é necessário para o radar.""",
    "retirar": """🏦 <b>Como sair para euros — formação</b>

1️⃣ Primeiro distingue vender o token de levantar para o banco. Uma venda na carteira pode deixar-te com outro criptoativo, não com euros.
2️⃣ Se escolheres usar uma exchange para converter em euros, confirma que aceita o ativo E a rede em que o tens. A conta deve ser tua e o serviço deve estar disponível para ti.
3️⃣ Obtém nessa exchange o endereço de DEPÓSITO correto e confirma qualquer identificador adicional exigido. Nunca uses um endereço de outra rede por parecer semelhante.
4️⃣ Confere taxas, mínimos, estado do depósito e só depois a conversão para euros. Não repitas transferências que ainda estejam pendentes.
5️⃣ Um levantamento em euros para uma conta bancária tua tem condições, prazos e possíveis custos próprios. Guarda os registos; o radar não calcula impostos.

🔐 O bot não recebe fundos, não transfere e não pede dados bancários ou credenciais.
🧪 Antes de fazer qualquer transferência real, termina a simulação e confirma que sabes verificar rede, contrato, taxas e confirmação.""",
    "saidas": """🎯 <b>Como saber quando REVER uma saída</b>

Ao registares uma posição defines dois PREÇOS de referência:
🛑 <b>Limite de perda (stop)</b>: se a cotação observada descer até esse nível, o radar avisa.
🎯 <b>Objetivo (take-profit)</b>: se subir até esse nível, o radar avisa para avaliares realizar o resultado.
🔴 Também pode avisar se a liquidez desaparecer ou houver uma queda acentuada.

💼 O acompanhamento mantém-se enquanto a posição tiver quantidade em aberto. Podes ter várias moedas registadas; cada uma tem os seus níveis e resultado estimado. Uma moeda nova não substitui a anterior.
👀 «Só acompanhar» não significa que compraste. Um alerta de entrada também não significa compra.
📝 Depois de venderes manualmente, regista a parcela vendida. Com saldo zero deixa de ser acompanhada como posição aberta.

📬 Além de situações novas de risco/nível, há um resumo periódico das posições abertas, no máximo a cada 6 horas por posição.
⚠️ Estes níveis são AVISOS, não ordens automáticas. Há intervalos entre consultas, atrasos e preços não executáveis. Podes perder mais do que imaginavas ou não conseguir vender. Não há um momento de saída garantidamente lucrativo.""",
}


def page(name):
    return PAGES.get(name, PAGES["ajuda"]) + f'\n\n📖 <a href="{GUIDE}">Guia completo e exercícios</a>'
