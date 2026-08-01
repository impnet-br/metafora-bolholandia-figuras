# SUBMISSAO DE EXEMPLO -- FICTICIA. Nao corresponde a montagem real alguma. Existe para demonstrar o formato esperado.

# Submissao de exemplo -- Desafio MZS

> **SUBMISSAO DE EXEMPLO -- FICTICIA. Nao corresponde a montagem real alguma. Existe para demonstrar o formato esperado.**
>
> **EXAMPLE SUBMISSION -- FICTITIOUS. It does not correspond to any real build. It exists to demonstrate the expected format.**

## O que ha aqui

| arquivo | conteudo |
|---|---|
| `log_estagios.csv` | log da sessao de aquisicao, 128 estagios |
| `log_controle.csv` | ensaio de controle: leitura analogica trocada por ruido |
| `componentes.csv` | lista de componentes com fabricante, modelo e lote |
| `firmware.ino` | esboco do laco de controle |
| `esquematico.svg` | diagrama de blocos da montagem |

## Como conferir

    python verificar.py log_estagios.csv     # deve dar 128/128 digitos corretos
    python verificar.py log_controle.csv     # deve QUEBRAR no primeiro estagio

O segundo e o ponto: se a cadeia sobrevivesse ao ruido, o bloco analogico
nao estaria contribuindo, e a submissao nao demonstraria o metodo.

O verificador esta em <../verificar.py>.

## Colunas do log

`stage`, `digit`, `trials`, `monitor_a`, `monitor_b`, `monitor_c`,
`quantity`, `temp_c`, `vref_v`.

`trials` nao e formalidade: um algoritmo puramente digital PROCURA cada
digito, testando candidatos; o MZS o LE de um instrumento. A contagem de
tentativas por estagio e o observavel que separa os dois casos.
