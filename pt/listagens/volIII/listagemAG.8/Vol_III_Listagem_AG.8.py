#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ------------------
# Nome do Fonte:     mzs_simulacao.py
# Autor:             Antonio Ferrão Neto
#
# Descrição:
# Simulador de Monte Carlo para o Método dos Zooms
# Sucessivos (MZS). Gera a sequência "verdadeira" de blocos
# e modela três dispositivos ruidosos independentes cujas
# leituras precisam atingir unanimidade (com retries e
# fallback de maioria 2-de-3). Invocado por
# run_montecarlo.bat.
#
# Execução:
#     python mzs_simulacao.py [--mc] [--prec N]
#            [--p_second P] [--p_both P] ...
# ------------------

import argparse
import random
from decimal import Decimal, getcontext, ROUND_FLOOR
from typing import List, Tuple, Dict, Optional

# ========================================
#  Base: gera a sequencia "verdadeira" de blocos (sem ruido)
# ========================================

class MZSBase:
    __slots__ = (
        "_precisao", "_mantissa_norm", "_expoente",
        "_signo", "_limiar",
    )

    def __init__(self, precisao: int,
                 numero: Optional[Decimal] = None):
        if precisao < 1:
            raise ValueError("precisao deve ser >= 1")
        self._precisao = int(precisao)
        getcontext().prec = self._precisao

        if numero is None:
            _valor = Decimal(
                '0.000000000000000000000000004534697376'
                '59267129482276738287854413224738693003'
                '53232')
        else:
            _valor = Decimal(str(numero))

        if _valor.is_zero():
            self._signo = ''
            self._expoente = 0
            self._mantissa_norm = Decimal(0)
        else:
            self._signo = '-' if _valor.is_signed() else ''
            adj = _valor.adjusted()
            self._expoente = adj
            # mantissa normalizada em [1, 10)
            self._mantissa_norm = \
                _valor.copy_abs().scaleb(-adj)

        del _valor
        self._limiar = Decimal('1').scaleb(
            -(self._precisao - 1))

    def gerar_blocos(self,
                     max_passos: Optional[int] = None
                     ) -> List[str]:
        if self._mantissa_norm.is_zero():
            return []
        mant = +self._mantissa_norm
        if max_passos is None:
            max_passos = (self._precisao + 2)//2 + 2
        out: List[str] = []
        for _ in range(max_passos):
            if mant <= 0:
                break
            # dois primeiros digitos significativos (10..99)
            d2 = (mant * 10).to_integral_value(
                rounding=ROUND_FLOOR)
            prox = d2 / Decimal(10)
            mant = (mant - prox) * 100
            if mant.copy_abs() < self._limiar:
                mant = Decimal(0)
            out.append(f"{int(d2):02d}")
        return out

# ========================================
#  Dispositivo ruidoso (independente)
#  p_second: erro apenas no 2o digito
#  p_both  : erro nos 2 primeiros digitos
# ========================================

class NoisyDevice:
    __slots__ = ("p_second", "p_both", "rng")

    def __init__(self, p_second: float, p_both: float,
                 seed: int):
        if not (0.0 <= p_second <= 1.0
                and 0.0 <= p_both <= 1.0):
            raise ValueError(
                "probabilidades devem estar em [0,1]")
        if p_second + p_both > 1.0:
            raise ValueError(
                "p_second + p_both nao pode exceder 1")
        self.p_second = float(p_second)
        self.p_both = float(p_both)
        self.rng = random.Random(seed)

    def corrupt(self, true_block: str) -> str:
        u = self.rng.random()
        a, b = int(true_block[0]), int(true_block[1])

        # erro nos dois digitos
        if u < self.p_both:
            while True:
                cand = self.rng.randrange(0, 100)
                if cand != a*10 + b:
                    return f"{cand:02d}"

        # erro somente no segundo digito
        if u < self.p_both + self.p_second:
            nb = (b + 1 + self.rng.randrange(9)) % 10
            return f"{a}{nb}"

        # sem erro
        return true_block

# ========================================
#  Unanimidade com retries; fallback = maioria 2-de-3
# ========================================

def unanimity_step(
        block_true: str,
        devs: Tuple[NoisyDevice, NoisyDevice, NoisyDevice],
        retries: int) -> Tuple[str, int, bool, bool]:
    """
    Retorna:
      (bloco_aceito, tentativas, inconsistencia,
       triple_equal_wrong)
      inconsistencia=True se nao houve unanimidade limpa
      (ou unanimidade errada); triple_equal_wrong=True se
      houve unanimidade errada (rarissimo).
    """
    attempts = 0
    while True:
        attempts += 1
        b1 = devs[0].corrupt(block_true)
        b2 = devs[1].corrupt(block_true)
        b3 = devs[2].corrupt(block_true)

        if b1 == b2 == b3:
            accepted = b1
            inconsistency = (accepted != block_true)
            triple_equal_wrong = inconsistency
            return (accepted, attempts, inconsistency,
                    triple_equal_wrong)

        if attempts > retries:
            # fallback: maioria 2-de-3 (ou desempate
            # arbitrario)
            if b1 == b2 or b1 == b3:
                accepted = b1
            elif b2 == b3:
                accepted = b2
            else:
                accepted = b1  # desempate
            return accepted, attempts, True, False
        # caso contrario, refaz o passo

def simular_sessao(prec=20,
                   p_second=0.01,
                   p_both=0.001,
                   retries=3,
                   seed_base=1234) -> Dict[str, object]:
    base = MZSBase(prec)
    true_blocks = base.gerar_blocos()
    devs = (
        NoisyDevice(p_second, p_both, seed_base + 0),
        NoisyDevice(p_second, p_both, seed_base + 1),
        NoisyDevice(p_second, p_both, seed_base + 2),
    )

    accepted: List[str] = []
    attempts_per_step: List[int] = []
    inconsistencies = 0
    unanimous_wrong = 0
    refetches = 0

    for tb in true_blocks:
        acc, att, inc, triple_wrong = unanimity_step(
            tb, devs, retries)
        accepted.append(acc)
        attempts_per_step.append(att)
        if att > 1:
            refetches += (att - 1)
        if inc:
            inconsistencies += 1
        if triple_wrong:
            unanimous_wrong += 1

    return {
        "true_blocks": true_blocks,
        "accepted_blocks": accepted,
        "attempts_per_step": attempts_per_step,
        "inconsistencies": inconsistencies,
        "unanimous_wrong": unanimous_wrong,
        "refetches": refetches,
        "params": {
            "prec": prec, "p_second": p_second,
            "p_both": p_both, "retries": retries,
            "seed_base": seed_base,
        }
    }

# ========================================
#  Monte Carlo (opcional, plug-and-play)
# ========================================

def monte_carlo(n_runs: int = 1000,
                prec: int = 20,
                p_second: float = 0.01,
                p_both: float = 0.001,
                retries: int = 3,
                seed0: int = 999) -> Dict[str, float]:
    """
    Executa n_runs sessoes independentes e estima:
      - frac_inconsistency: fração de sessoes com alguma
        inconsistência
      - mean_inconsistencies: inconsistencias medias por
        sessao
      - mean_unanimous_wrong: unanimidades erradas medias
        por sessao (rarissimo)
      - mean_refetches: reexecucoes medias por sessao
      - mean_attempts_per_step: media global de tentativas
        por passo
    """
    rng = random.Random(seed0)
    total_incons_sessions = 0
    sum_incons = 0
    sum_unanimous_wrong = 0
    sum_refetches = 0
    sum_attempts = 0
    sum_steps = 0

    for _ in range(n_runs):
        seed_base = rng.randrange(1 << 30)
        r = simular_sessao(prec=prec, p_second=p_second,
                           p_both=p_both, retries=retries,
                           seed_base=seed_base)
        inc = r["inconsistencies"]
        uw = r["unanimous_wrong"]
        rf = r["refetches"]
        atts = r["attempts_per_step"]
        steps = len(atts)

        if inc > 0 or uw > 0:
            total_incons_sessions += 1
        sum_incons += inc
        sum_unanimous_wrong += uw
        sum_refetches += rf
        sum_attempts += sum(atts)
        sum_steps += steps

    return {
        "runs": n_runs,
        "frac_inconsistency":
            total_incons_sessions / n_runs if n_runs else 0.0,
        "mean_inconsistencies":
            sum_incons / n_runs if n_runs else 0.0,
        "mean_unanimous_wrong":
            sum_unanimous_wrong / n_runs if n_runs else 0.0,
        "mean_refetches":
            sum_refetches / n_runs if n_runs else 0.0,
        "mean_attempts_per_step":
            (sum_attempts / sum_steps) if sum_steps else 0.0,
    }

# ========================================
#  CLI
# ========================================

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Simulação MZS com unanimidade e "
                    "Monte Carlo opcional")
    p.add_argument("--prec", type=int, default=20,
                   help="Precisao (define ~numero de "
                        "passos)")
    p.add_argument("--p_second", type=float, default=0.01,
                   help="Probabilidade de erro no 2o "
                        "dígito")
    p.add_argument("--p_both", type=float, default=0.001,
                   help="Probabilidade de erro nos 2 "
                        "primeiros dígitos")
    p.add_argument("--retries", type=int, default=3,
                   help="Retries para obter unanimidade "
                        "antes do fallback")
    p.add_argument("--seed", type=int, default=42,
                   help="Seed base (execucao unica)")
    p.add_argument("--mc", action="store_true",
                   help="Ativa Monte Carlo")
    p.add_argument("--n_runs", type=int, default=500,
                   help="Numero de sessoes no Monte Carlo")
    p.add_argument("--mc_seed0", type=int, default=20250809,
                   help="Seed do Monte Carlo (selecao de "
                        "seeds base)")
    return p.parse_args()

def main():
    args = parse_args()

    # Execucao unica (amostra)
    r = simular_sessao(prec=args.prec,
                       p_second=args.p_second,
                       p_both=args.p_both,
                       retries=args.retries,
                       seed_base=args.seed)

    print("Params:", {"prec": args.prec,
                      "p_second": args.p_second,
                      "p_both": args.p_both,
                      "retries": args.retries,
                      "seed_base": args.seed})
    print("True   :", " ".join(r["true_blocks"]))
    print("Accept :", " ".join(r["accepted_blocks"]))
    print("Inconsistencies:", r["inconsistencies"],
          "UnanimousWrong:", r["unanimous_wrong"],
          "Refetches:", r["refetches"])
    print("Attempts/step:", r["attempts_per_step"])

    # Monte Carlo (opcional)
    if args.mc:
        mc = monte_carlo(n_runs=args.n_runs,
                         prec=args.prec,
                         p_second=args.p_second,
                         p_both=args.p_both,
                         retries=args.retries,
                         seed0=args.mc_seed0)
        print("\n--- Monte Carlo ---")
        for k, v in mc.items():
            print(f"{k}: {v}")

if __name__ == "__main__":
    main()
