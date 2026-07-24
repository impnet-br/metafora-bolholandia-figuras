# -*- coding: utf-8 -*-
"""Formata os resultados da simulação de viabilidade do MZS em duas saídas:

  (1) tab_montecarlo_compacta.tex  -- tabela compacta para o LIVRO (Estudo B),
      do dispositivo horrível ao barato de 3 dígitos e meio, mostrando o joelho.
  (2) montecarlo_completa.html + .csv -- a grade completa (Estudo A) para
      publicação eletrônica (GitHub + QR).

É o "código formatador" que acompanha a POC. Lê os CSVs gerados por
varrer_viabilidade.py; não roda a simulação.
"""
import csv
import html
import sys
from pathlib import Path

SP = Path(__file__).parent

# rótulos para as linhas do Estudo B (livro), na ordem do CSV
ROTULOS_B = {
    (2, 0.1, 0.01):     ("Horr\\'ivel",              False),
    (2, 0.05, 0.005):   ("Ruim",                     False),
    (2, 0.02, 0.0001):  ("Razo\\'avel (2 d\\'igitos)", False),
    (3, 0.02, 0.0001):  ("\\textbf{Barato: 3\\textonehalf\\ d\\'igitos}", True),
    (4, 0.02, 0.0001):  ("4 d\\'igitos",             False),
    (3, 0.01, 0.0001):  ("3\\textonehalf\\ d\\'igitos, ru\\'ido menor", False),
}


def f2(x):
    return f"{float(x):.2f}"


def pct(x):
    return f"{float(x)*100:.3f}\\%".replace(".", "{,}")


def vir(x):
    return str(x).replace(".", "{,}")


# ---------------------------------------------------------------- LIVRO (B)
def gerar_latex_compacta(csv_b: Path, saida: Path):
    rows = list(csv.DictReader(csv_b.open(encoding="utf-8")))
    L = []
    L.append("% Gerado por formatar_tabelas_mzs.py -- NAO editar a mao.")
    L.append("% Tabela compacta (Estudo B). A grade completa (Estudo A) fica")
    L.append("% em .../tabelas/montecarlo/ (QR na legenda).")
    L.append("\\begin{table}[H]")
    L.append("\\centering")
    L.append("\\small")
    L.append("\\setlength{\\tabcolsep}{5pt}")
    L.append("\\renewcommand{\\arraystretch}{1.15}")
    L.append("\\begin{tabular}{@{}lccccc@{}}")
    L.append("\\toprule")
    L.append("Cen\\'ario & \\makecell{d\\\\(d\\'ig./leit.)} & "
             "\\makecell{ru\\'ido no\\\\\\'ult.\\ d\\'igito} & rodadas & "
             "\\makecell{taxa de\\\\recupera\\c{c}\\~ao} & "
             "\\makecell{reproc.\\\\por bloco} \\\\")
    L.append("\\midrule")
    for r in rows:
        chave = (int(r["d"]), float(r["p_last"]), float(r["p_block"]))
        rot, destaque = ROTULOS_B.get(chave, (f"d={r['d']}", False))
        linha = (f"{rot} & {r['d']} & {pct(r['p_last'])} & {r['rodadas']} & "
                 f"{pct(r['taxa_recuperacao'])} & {vir(f2(r['reproc_por_bloco']))}")
        if destaque:
            linha = "\\rowcolor{green!12}\n" + linha
        L.append(linha + " \\\\")
    L.append("\\bottomrule")
    L.append("\\end{tabular}")
    L.append("\\caption[Viabilidade do MZS: desempenho por qualidade de dispositivo]{%")
    L.append("Viabilidade do MZS por qualidade de dispositivo (prec=20, "
             "20\\,000 sess\\~oes por cen\\'ario, tr\\^es dispositivos com "
             "protocolo de unanimidade que \\emph{reprocessa at\\'e o \\^exito}). "
             "O valor \\'e sempre recuperado, a menos da rar\\'issima "
             "\\emph{unanimidade errada} (os tr\\^es dispositivos concordam no "
             "\\emph{mesmo} valor incorreto): da\\'i a taxa de recupera\\c{c}\\~ao "
             "ficar em 99{,}99\\,\\% e n\\~ao em 100\\,\\%. O ponto de opera\\c{c}\\~ao "
             "recomendado (verde) \\'e um dispositivo barato de 3\\textonehalf\\ "
             "d\\'igitos: recupera com reprocessamento \\'infimo e em menos rodadas "
             "que um de 2 d\\'igitos. Passar a 4 d\\'igitos poupa apenas duas rodadas, "
             "sem justificar o custo. A grade completa (todas as combina\\c{c}\\~oes "
             "de ru\\'ido) est\\'a dispon\\'ivel eletronicamente pelo QR ao lado.}")
    L.append("\\label{tab:montecarlo}")
    L.append("\\end{table}")
    saida.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  {saida.name}: {len(rows)} linhas")


# ------------------------------------------------------------ ELETRÔNICO (A)
CSS = """
:root{color-scheme:light dark;--bg:#f4f6f7;--fg:#1a2327;--card:#fff;
--muted:#5b6b72;--acc:#0f6d7a;--line:#dce3e5;--warn:#b45309}
@media(prefers-color-scheme:dark){:root{--bg:#12181a;--fg:#e6edef;
--card:#1b2427;--muted:#93a4aa;--acc:#4fd0e0;--line:#2a363a;--warn:#f0b35b}}
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 -apple-system,Segoe UI,Roboto,Arial,sans-serif;
background:var(--bg);color:var(--fg)}
.wrap{max-width:1000px;margin:0 auto;padding:24px 18px 60px}
h1{font-size:1.4rem;margin:.2em 0}
.sub{color:var(--muted);margin:.2em 0 1.2em}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:14px 16px;margin:0 0 18px}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{padding:6px 10px;text-align:right;border-bottom:1px solid var(--line)}
th{position:sticky;top:0;background:var(--card);text-align:right;font-size:.82rem;
color:var(--muted)}
td:first-child,th:first-child{text-align:left}
tbody tr:hover{background:color-mix(in srgb,var(--acc) 8%,transparent)}
.scroll{overflow-x:auto}
.btn{display:inline-block;padding:10px 16px;border-radius:9px;background:var(--acc);
color:#fff;text-decoration:none;font-weight:600}
footer{color:var(--muted);font-size:.8rem;margin:36px 0 0;border-top:1px solid var(--line);
padding-top:14px}
footer a{color:var(--acc)}
"""

COLS_HTML = [
    ("d", "d (díg./leit.)"), ("p_last", "ruído últ. díg."),
    ("p_block", "ruído bloco"), ("rodadas", "rodadas"),
    ("taxa_recuperacao", "recuperação"),
    ("frac_unanimidade_errada", "falha residual"),
    ("reproc_por_bloco", "reproc./bloco"),
    ("reproc_por_sessao", "reproc./sessão"),
    ("pior_caso_tentativas", "pior caso"),
]


def gerar_html_completa(csv_a: Path, saida_html: Path, saida_csv: Path):
    rows = list(csv.DictReader(csv_a.open(encoding="utf-8")))
    saida_csv.write_text(csv_a.read_text(encoding="utf-8"), encoding="utf-8")

    def cel(col, v):
        if col in ("taxa_recuperacao",):
            return f"{float(v)*100:.3f}%"
        if col in ("p_last", "p_block", "frac_unanimidade_errada",
                   "reproc_por_bloco", "reproc_por_sessao"):
            return f"{float(v):.4f}".rstrip("0").rstrip(".") or "0"
        return str(v)

    trs = []
    for r in rows:
        tds = "".join(f"<td>{html.escape(cel(c, r[c]))}</td>" for c, _ in COLS_HTML)
        trs.append(f"<tr>{tds}</tr>")
    ths = "".join(f"<th>{html.escape(t)}</th>" for _, t in COLS_HTML)
    corpo = f"""<div class="wrap">
<h1>MZS &mdash; simulação de Monte Carlo (tabela completa)</h1>
<p class="sub">Estudo de viabilidade do Método dos Zooms Sucessivos.
{len(rows)} configurações &middot; 20 000 sessões cada &middot; precisão 20 dígitos.</p>
<div class="card">
<b>Como ler.</b> Três dispositivos ruidosos leem cada bloco; se discordam, o
monitor manda reprocessar até haver unanimidade. O valor é recuperado quase
sempre &mdash; a <i>falha residual</i> é a rara <i>unanimidade errada</i> (os três
concordam no mesmo valor errado), que a maioria-de-3 não detecta. <code>d</code>
é o número de dígitos lidos por rodada; mais dígitos = menos rodadas, ao custo
de um dispositivo mais caro.
</div>
<div class="card">
<b>Downloads.</b> Tudo o que esta legenda promete, num só lugar:
<p style="margin:10px 0 0">
<a class="btn" href="montecarlo_completa.csv" download>Tabela completa (CSV)</a>
<a class="btn" href="mzs_viabilidade.py" download>Simulador (.py)</a>
<a class="btn" href="formatar_tabelas_mzs.py" download>Formatador (.py)</a>
</p>
<p class="sub" style="margin:10px 0 0">O simulador gera os dados; o formatador
produz esta tabela e a versão compacta do livro. Sementes fixas &mdash; quem rodar
obtém exatamente estes números.</p>
</div>
<div class="card scroll"><table><thead><tr>{ths}</tr></thead>
<tbody>{''.join(trs)}</tbody></table></div>
<footer>Gerado por <code>formatar_tabelas_mzs.py</code> a partir do simulador
<code>mzs_viabilidade.py</code>. Sementes fixas &mdash; resultados reproduzíveis.
<a href="https://github.com/impnet-br/metafora-bolholandia-figuras">Repositório</a>.
</footer></div>"""
    doc = ('<!doctype html><html lang="pt-br"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width,initial-scale=1">'
           '<title>MZS &mdash; Monte Carlo completo</title>'
           f'<style>{CSS}</style></head><body>{corpo}</body></html>')
    saida_html.write_text(doc, encoding="utf-8")
    print(f"  {saida_html.name}: {len(rows)} linhas + CSV")


def main():
    print("Formatando:")
    gerar_latex_compacta(SP / "viab_estudo_B_livro.csv",
                         SP / "tab_montecarlo_compacta.tex")
    gerar_html_completa(SP / "viab_estudo_A_completo.csv",
                        SP / "montecarlo_completa.html",
                        SP / "montecarlo_completa.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
