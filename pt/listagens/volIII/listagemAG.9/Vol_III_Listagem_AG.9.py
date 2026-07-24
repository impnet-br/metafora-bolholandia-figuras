# -*- coding: utf-8 -*-
"""Roda os dois estudos de viabilidade do MZS e grava CSVs.

  Estudo B (LIVRO, compacto): poucos pontos que contam a história -- do
    dispositivo horrível ao barato de 3 dígitos e meio -- mostrando o joelho
    de custo.
  Estudo A (ELETRÔNICO, completo): grade (d, p_last, p_block) para publicar no
    GitHub com QR. Mostra que a recuperação permanece ~100% em todo o espaço e
    como o custo de reprocessamento varia.

Escreve incrementalmente (uma linha por combo, com flush) para não se perder se
for interrompido. Imprime progresso.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mzs_viabilidade import monte_carlo  # noqa: E402

PREC, N_RUNS, SEED0 = 20, 20000, 20250809
OUT = Path(__file__).parent

COLS = ["d", "p_last", "p_block", "rodadas", "taxa_recuperacao",
        "frac_unanimidade_errada", "reproc_por_bloco", "reproc_por_sessao",
        "tentativas_por_bloco", "pior_caso_tentativas"]


def linha_csv(d, p_last, p_block, mc):
    vals = [d, p_last, p_block, mc["rodadas"], mc["taxa_recuperacao"],
            mc["frac_unanimidade_errada"], mc["reproc_por_bloco"],
            mc["reproc_por_sessao"], mc["tentativas_por_bloco"],
            mc["pior_caso_tentativas"]]
    return ",".join(str(v) for v in vals)


def rodar(nome, combos, arquivo):
    caminho = OUT / arquivo
    t0 = time.time()
    with caminho.open("w", encoding="utf-8") as f:
        f.write(",".join(COLS) + "\n")
        f.flush()
        for i, (d, pl, pb) in enumerate(combos, 1):
            mc = monte_carlo(N_RUNS, PREC, d, pl, pb, SEED0)
            f.write(linha_csv(d, pl, pb, mc) + "\n")
            f.flush()
            print(f"[{nome} {i:3d}/{len(combos)}] d={d} p_last={pl} p_block={pb}"
                  f"  rec={mc['taxa_recuperacao']:.4f}"
                  f"  reproc/bloco={mc['reproc_por_bloco']:.4f}"
                  f"  ({time.time()-t0:.0f}s)", flush=True)
    print(f"== {nome} pronto: {caminho.name} ({time.time()-t0:.0f}s)\n", flush=True)


def main():
    # ---- Estudo B: LIVRO (compacto) -------------------------------------
    # Do horrível ao barato-viável, mais o "melhor" para mostrar o joelho.
    estudo_b = [
        (2, 0.10, 0.010),   # dispositivo horrível
        (2, 0.05, 0.005),   # ruim
        (2, 0.02, 0.0001),  # 2 dígitos, baixo ruído
        (3, 0.02, 0.0001),  # ** barato 3 dígitos e meio -- o ponto de operação **
        (4, 0.02, 0.0001),  # melhor (não compensa o custo)
        (3, 0.01, 0.0001),  # 3.5 com ruído ainda menor
    ]
    rodar("Estudo B (livro)", estudo_b, "viab_estudo_B_livro.csv")

    # ---- Estudo A: ELETRÔNICO (completo) --------------------------------
    ds = [2, 3, 4]
    p_lasts = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10,
               0.15, 0.20]
    p_blocks = [0.0001, 0.001, 0.002, 0.005, 0.010]
    combos = [(d, pl, pb) for d in ds for pl in p_lasts for pb in p_blocks]
    print(f"Estudo A: {len(combos)} combinacoes x {N_RUNS} sessoes\n", flush=True)
    rodar("Estudo A (eletronico)", combos, "viab_estudo_A_completo.csv")

    print("TUDO PRONTO.", flush=True)


if __name__ == "__main__":
    sys.exit(main())
