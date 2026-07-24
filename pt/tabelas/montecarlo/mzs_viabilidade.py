#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ------------------
# Nome do Fonte:     mzs_viabilidade.py
# Autor:             Antonio Ferrao Neto
#
# Descrição:
# Simulador de Monte Carlo para o Método dos Zooms Sucessivos (MZS),
# ESTENDIDO em relação ao mzs_simulacao.py original para demonstrar a
# VIABILIDADE do método com hardware realista e barato.
#
# Duas mudanças de modelo em relação ao original:
#
#   (1) DÍGITOS POR LEITURA (d): o dispositivo lê d dígitos significativos por
#       passo (o original fixava d=2). O zoom avança x10^d. Mais dígitos por
#       rodada => menos rodadas => mais rápido, ao custo de um dispositivo mais
#       caro. O ruído concentra-se no ÚLTIMO dígito lido (o "meio" de um
#       dispositivo de 3 dígitos e meio).
#
#   (2) REPROCESSA ATÉ O ÊXITO: os 3 dispositivos leem o mesmo resíduo; se há
#       unanimidade, aceita e avança; se há discordância, o monitor a detecta e
#       manda reler, repetindo até unanimidade (teto de segurança alto). A
#       maioria 2-de-3 fica como desempate de último recurso, quase nunca usado.
#       Consequência: o valor é SEMPRE recuperado (a menos da raríssima
#       "unanimidade errada"). O que se mede não é "falha", é o CUSTO DE TEMPO
#       (reprocessamentos).
#
# A técnica de monitoramento aqui é apenas a maioria-de-3. Outras (p.ex.
# Extrapolação de Richardson, comentada no apêndice) ficam fora do escopo de
# uma POC -- pertencem ao projeto de engenharia eletrônica.
# ------------------

import argparse
import math
import random
from decimal import Decimal, getcontext, ROUND_FLOOR
from typing import List, Tuple, Dict, Optional

TETO_REPROC = 100000  # teto de segurança; na prática nunca alcançado


# ========================================
#  Sequência "verdadeira" de blocos de d dígitos (sem ruído)
# ========================================

class MZSBase:
    __slots__ = ("_prec", "_mant", "_exp", "_sinal", "_limiar", "_d")

    NUMERO_PADRAO = ('0.000000000000000000000000004534697376'
                     '5926712948227673828785441322473869300353232')

    def __init__(self, prec: int, d: int, numero: Optional[Decimal] = None):
        if prec < 1:
            raise ValueError("prec >= 1")
        if d < 1:
            raise ValueError("d >= 1")
        self._prec = int(prec)
        self._d = int(d)
        getcontext().prec = self._prec
        v = Decimal(self.NUMERO_PADRAO) if numero is None else Decimal(str(numero))
        if v.is_zero():
            self._sinal, self._exp, self._mant = '', 0, Decimal(0)
        else:
            self._sinal = '-' if v.is_signed() else ''
            adj = v.adjusted()
            self._exp = adj
            self._mant = v.copy_abs().scaleb(-adj)   # [1,10)
        del v
        self._limiar = Decimal('1').scaleb(-(self._prec - 1))

    def gerar_blocos(self) -> List[str]:
        """Blocos de d dígitos, em ordem de significância."""
        if self._mant.is_zero():
            return []
        d = self._d
        fator = Decimal(10) ** (d - 1)   # traz d dígitos para a parte inteira
        zoom = Decimal(10) ** d
        mant = +self._mant
        n_passos = (self._prec + d) // d + 2
        out: List[str] = []
        for _ in range(n_passos):
            if mant <= 0:
                break
            bloco = (mant * fator).to_integral_value(rounding=ROUND_FLOOR)
            prox = bloco / fator
            mant = (mant - prox) * zoom
            if mant.copy_abs() < self._limiar:
                mant = Decimal(0)
            out.append(f"{int(bloco):0{d}d}")
        return out


# ========================================
#  Dispositivo ruidoso: ruído no ÚLTIMO dígito (p_last) ou no bloco (p_block)
# ========================================

class NoisyDevice:
    __slots__ = ("p_last", "p_block", "d", "rng")

    def __init__(self, p_last: float, p_block: float, d: int, seed: int):
        if not (0 <= p_last <= 1 and 0 <= p_block <= 1):
            raise ValueError("probabilidades em [0,1]")
        if p_last + p_block > 1:
            raise ValueError("p_last + p_block <= 1")
        self.p_last = float(p_last)
        self.p_block = float(p_block)
        self.d = int(d)
        self.rng = random.Random(seed)

    def ler(self, bloco_true: str) -> str:
        u = self.rng.random()
        # erro no bloco inteiro (catastrófico, raro): outro valor de d dígitos
        if u < self.p_block:
            while True:
                cand = self.rng.randrange(10 ** self.d)
                s = f"{cand:0{self.d}d}"
                if s != bloco_true:
                    return s
        # erro só no último dígito
        if u < self.p_block + self.p_last:
            ult = int(bloco_true[-1])
            novo = (ult + 1 + self.rng.randrange(9)) % 10
            return bloco_true[:-1] + str(novo)
        # sem erro
        return bloco_true


# ========================================
#  Passo com reprocessamento até a unanimidade (monitor = maioria-de-3)
# ========================================

def passo_unanimidade(bloco_true: str,
                      devs: Tuple[NoisyDevice, NoisyDevice, NoisyDevice]
                      ) -> Tuple[str, int, bool]:
    """Devolve (bloco_aceito, tentativas, unanimidade_errada).

    Relê até os três concordarem. Só aceita bloco errado se os três derem o
    MESMO valor errado (unanimidade errada, raríssima). O teto é de segurança."""
    tent = 0
    while tent < TETO_REPROC:
        tent += 1
        b1 = devs[0].ler(bloco_true)
        b2 = devs[1].ler(bloco_true)
        b3 = devs[2].ler(bloco_true)
        if b1 == b2 == b3:
            return b1, tent, (b1 != bloco_true)
        # discordância: o monitor detecta e manda reprocessar
    # teto atingido (praticamente nunca): desempate por maioria
    if b1 == b2 or b1 == b3:
        acc = b1
    elif b2 == b3:
        acc = b2
    else:
        acc = b1
    return acc, tent, (acc != bloco_true)


def simular_sessao(prec: int, d: int, p_last: float, p_block: float,
                   seed_base: int) -> Dict[str, object]:
    base = MZSBase(prec, d)
    blocos_true = base.gerar_blocos()
    devs = (
        NoisyDevice(p_last, p_block, d, seed_base + 0),
        NoisyDevice(p_last, p_block, d, seed_base + 1),
        NoisyDevice(p_last, p_block, d, seed_base + 2),
    )
    aceitos: List[str] = []
    tent_por_bloco: List[int] = []
    reproc = 0
    unan_errada = 0
    for bt in blocos_true:
        acc, tent, uw = passo_unanimidade(bt, devs)
        aceitos.append(acc)
        tent_por_bloco.append(tent)
        reproc += (tent - 1)
        if uw:
            unan_errada += 1
    recuperado = (aceitos == blocos_true)
    return {
        "n_blocos": len(blocos_true),
        "reproc": reproc,
        "tent_por_bloco": tent_por_bloco,
        "unan_errada": unan_errada,
        "recuperado": recuperado,
    }


# ========================================
#  Monte Carlo
# ========================================

def monte_carlo(n_runs: int, prec: int, d: int, p_last: float, p_block: float,
                seed0: int) -> Dict[str, float]:
    rng = random.Random(seed0)
    n_recuperado = 0
    n_unan_errada_sessoes = 0
    soma_reproc = 0
    soma_tent = 0
    soma_blocos = 0
    pior_caso = 0
    n_blocos_fixo = 0
    for _ in range(n_runs):
        sb = rng.randrange(1 << 30)
        r = simular_sessao(prec, d, p_last, p_block, sb)
        if r["recuperado"]:
            n_recuperado += 1
        if r["unan_errada"] > 0:
            n_unan_errada_sessoes += 1
        soma_reproc += r["reproc"]
        soma_tent += sum(r["tent_por_bloco"])
        soma_blocos += r["n_blocos"]
        m = max(r["tent_por_bloco"]) if r["tent_por_bloco"] else 0
        if m > pior_caso:
            pior_caso = m
        n_blocos_fixo = r["n_blocos"]
    return {
        "runs": n_runs,
        "d": d,
        "digitos_por_rodada": d,
        "rodadas": n_blocos_fixo,
        "taxa_recuperacao": n_recuperado / n_runs if n_runs else 0.0,
        "frac_unanimidade_errada":
            n_unan_errada_sessoes / n_runs if n_runs else 0.0,
        "reproc_por_bloco":
            soma_reproc / soma_blocos if soma_blocos else 0.0,
        "reproc_por_sessao":
            soma_reproc / n_runs if n_runs else 0.0,
        "tentativas_por_bloco":
            soma_tent / soma_blocos if soma_blocos else 0.0,
        "pior_caso_tentativas": pior_caso,
    }


# ========================================
#  CLI
# ========================================

def main():
    p = argparse.ArgumentParser(
        description="Simulacao MZS de viabilidade (d digitos, reprocessa ate exito)")
    p.add_argument("--prec", type=int, default=20)
    p.add_argument("--d", type=int, default=2, help="digitos por leitura")
    p.add_argument("--p_last", type=float, default=0.02,
                   help="prob. de erro no ULTIMO digito")
    p.add_argument("--p_block", type=float, default=0.0001,
                   help="prob. de erro no bloco inteiro (catastrofico)")
    p.add_argument("--n_runs", type=int, default=20000)
    p.add_argument("--seed0", type=int, default=20250809)
    args = p.parse_args()
    mc = monte_carlo(args.n_runs, args.prec, args.d, args.p_last, args.p_block,
                     args.seed0)
    print(f"--- MZS viabilidade  d={args.d} p_last={args.p_last} "
          f"p_block={args.p_block} runs={args.n_runs} ---")
    for k, v in mc.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
