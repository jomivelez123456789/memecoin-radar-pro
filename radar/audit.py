"""Private, standalone review artifact. Caller controls where it is saved."""
import html
from .learning import metrics
from .paper import eur, statistics
from .telegram import stamp


def render(data, now):
    m = metrics(data); stats = statistics(data, now); book = data["paper"]
    rows = []
    for p in book["trades"]:
        closed = p.get("closed_at") is not None
        gross = p["budget"] * (p["exit_quote_eur"] / p["entry_quote_eur"] - 1) if closed else None
        values = [p["name"], p["key"].split(":", 1)[0], stamp(p["opened_at"]),
                  stamp(p.get("closed_at")) if closed else "Aberta — resultado por fechar",
                  eur(p.get("pnl")), eur(gross), eur(gross - p["pnl"]) if closed else "Por apurar",
                  p.get("reason", "Em acompanhamento"), "Sim" if p.get("monitoring_gap") else "Não registado",
                  "Recuperada do alerta original" if p.get("entry_evidence", {}).get("recovered_at") else
                  "Guardada na entrada" if p.get("entry_evidence") else "Em falta"]
        rows.append("<tr>" + "".join("<td>" + html.escape(str(v)) + "</td>" for v in values) + "</tr>")
    header = ["Moeda", "Rede", "Entrada UTC", "Saída UTC", "Resultado líquido fictício", "Cenário sem custos",
              "Diferença atribuída ao modelo de custos", "Motivo observado de saída", "Intervalo >15min", "Evidência de entrada"]
    return f'''<!doctype html><html lang="pt"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Auditoria privada do teste em euros</title><style>body{{font:16px system-ui;margin:30px;color:#182634}}h1{{font-size:26px}}.cards{{display:flex;gap:20px;flex-wrap:wrap}}.card{{padding:18px;background:#f0f3f7;border-radius:12px}}.scroll{{overflow:auto}}table{{border-collapse:collapse;font-size:13px}}td,th{{padding:10px;border-bottom:1px solid #ccd4dd;text-align:left;min-width:100px}}th{{background:#e5edf6}}p{{max-width:1000px;line-height:1.55}}</style>
<h1>Auditoria privada — teste fictício em euros</h1><p>Observação em {stamp(now)}. Não houve execução em carteira. O ficheiro contém apenas o ensaio e fica fora do repositório público.</p>
<div class="cards"><div class="card">Saldo total estimado<br><b>{eur(stats['equity'])}</b></div><div class="card">Fechadas<br><b>{stats['closed']} · {stats['wins']} ganhos · {stats['losses']} perdas</b></div><div class="card">Resultado das fechadas<br><b>{eur(m['realized'])}</b></div><div class="card">Diferença para cenário sem custos<br><b>{eur(m['cost_drag'])}</b></div></div>
<p>Sem taxas/desvios, as mesmas cotações de entrada e saída dariam {eur(m['gross_without_costs'])}. Isso é um contrafactual, não um lucro executável. Mantêm-se todos os custos assumidos e todas as perdas. Custos reais, capacidade de venda e impacto da ordem não foram medidos.</p>
<p>Os níveis −10%/+20% do ensaio original referem-se a movimentos da cotação em euros, antes de custos. Uma subida de 20% não implica ganho líquido de 20%; o preço observado entre consultas pode ultrapassar os níveis. Repetições do mesmo contrato e capacidade limitada fazem desta amostra uma avaliação exploratória, não uma prova estatística independente.</p>
<p>Novas hipóteses a testar prospectivamente: confirmação do mesmo par em duas consultas e suspensão de novas calls no mesmo contrato após duas perdas em 72h. O acompanhamento das posições existentes passa a consultar o par original quando conhecido. Resultados antigos não são reescritos.</p>
<h2>Todas as posições fictícias ({len(book['trades'])})</h2><div class="scroll"><table><thead><tr>{''.join('<th>'+html.escape(h)+'</th>' for h in header)}</tr></thead><tbody>{''.join(rows)}</tbody></table></div></html>'''
