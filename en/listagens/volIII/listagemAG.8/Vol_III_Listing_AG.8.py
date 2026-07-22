#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ------------------
# Source file:       szm_simulation.py
# Author:            Antonio Ferrão Neto
#
# Description:
# Monte Carlo simulator for the Successive Zooms Method
# (SZM). Generates the "true" block sequence and models
# three independent noisy devices whose readings must
# reach unanimity (with retries and a 2-of-3 majority
# fallback). Invoked by run_montecarlo.bat.
#
# Usage:
#     python szm_simulation.py [--mc] [--prec N]
#            [--p_second P] [--p_both P] ...
# ------------------

import argparse
import random
from decimal import Decimal, getcontext, ROUND_FLOOR
from typing import List, Tuple, Dict, Optional

# ========================================
#  Base: generates the "true" block sequence (noise-free)
# ========================================

class SZMBase:
    __slots__ = (
        "_precision", "_mantissa_norm", "_exponent",
        "_sign", "_threshold",
    )

    def __init__(self, precision: int,
                 number: Optional[Decimal] = None):
        if precision < 1:
            raise ValueError("precision must be >= 1")
        self._precision = int(precision)
        getcontext().prec = self._precision

        if number is None:
            _value = Decimal(
                '0.000000000000000000000000004534697376'
                '59267129482276738287854413224738693003'
                '53232')
        else:
            _value = Decimal(str(number))

        if _value.is_zero():
            self._sign = ''
            self._exponent = 0
            self._mantissa_norm = Decimal(0)
        else:
            self._sign = '-' if _value.is_signed() else ''
            adj = _value.adjusted()
            self._exponent = adj
            # normalized mantissa in [1, 10)
            self._mantissa_norm = \
                _value.copy_abs().scaleb(-adj)

        del _value
        self._threshold = Decimal('1').scaleb(
            -(self._precision - 1))

    def generate_blocks(self,
                        max_steps: Optional[int] = None
                        ) -> List[str]:
        if self._mantissa_norm.is_zero():
            return []
        mant = +self._mantissa_norm
        if max_steps is None:
            max_steps = (self._precision + 2)//2 + 2
        out: List[str] = []
        for _ in range(max_steps):
            if mant <= 0:
                break
            # first two significant digits (10..99)
            d2 = (mant * 10).to_integral_value(
                rounding=ROUND_FLOOR)
            nxt = d2 / Decimal(10)
            mant = (mant - nxt) * 100
            if mant.copy_abs() < self._threshold:
                mant = Decimal(0)
            out.append(f"{int(d2):02d}")
        return out

# ========================================
#  Noisy device (independent)
#  p_second: error only in the 2nd digit
#  p_both  : error in the first 2 digits
# ========================================

class NoisyDevice:
    __slots__ = ("p_second", "p_both", "rng")

    def __init__(self, p_second: float, p_both: float,
                 seed: int):
        if not (0.0 <= p_second <= 1.0
                and 0.0 <= p_both <= 1.0):
            raise ValueError(
                "probabilities must be in [0,1]")
        if p_second + p_both > 1.0:
            raise ValueError(
                "p_second + p_both cannot exceed 1")
        self.p_second = float(p_second)
        self.p_both = float(p_both)
        self.rng = random.Random(seed)

    def corrupt(self, true_block: str) -> str:
        u = self.rng.random()
        a, b = int(true_block[0]), int(true_block[1])

        # error in both digits
        if u < self.p_both:
            while True:
                cand = self.rng.randrange(0, 100)
                if cand != a*10 + b:
                    return f"{cand:02d}"

        # error only in the second digit
        if u < self.p_both + self.p_second:
            nb = (b + 1 + self.rng.randrange(9)) % 10
            return f"{a}{nb}"

        # no error
        return true_block

# ========================================
#  Unanimity with retries; fallback = 2-of-3 majority
# ========================================

def unanimity_step(
        block_true: str,
        devs: Tuple[NoisyDevice, NoisyDevice, NoisyDevice],
        retries: int) -> Tuple[str, int, bool, bool]:
    """
    Returns:
      (accepted_block, attempts, inconsistency,
       triple_equal_wrong)
      inconsistency=True if there was no clean unanimity
      (or a wrong unanimity); triple_equal_wrong=True if
      there was a wrong unanimity (extremely rare).
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
            # fallback: 2-of-3 majority (or arbitrary
            # tie-break)
            if b1 == b2 or b1 == b3:
                accepted = b1
            elif b2 == b3:
                accepted = b2
            else:
                accepted = b1  # tie-break
            return accepted, attempts, True, False
        # otherwise, redo the step

def simulate_session(prec=20,
                     p_second=0.01,
                     p_both=0.001,
                     retries=3,
                     seed_base=1234) -> Dict[str, object]:
    base = SZMBase(prec)
    true_blocks = base.generate_blocks()
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
#  Monte Carlo (optional, plug-and-play)
# ========================================

def monte_carlo(n_runs: int = 1000,
                prec: int = 20,
                p_second: float = 0.01,
                p_both: float = 0.001,
                retries: int = 3,
                seed0: int = 999) -> Dict[str, float]:
    """
    Runs n_runs independent sessions and estimates:
      - frac_inconsistency: fraction of sessions with
        any inconsistency
      - mean_inconsistencies: mean inconsistencies per
        session
      - mean_unanimous_wrong: mean wrong unanimities per
        session (extremely rare)
      - mean_refetches: mean re-executions per session
      - mean_attempts_per_step: global mean of attempts
        per step
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
        r = simulate_session(prec=prec, p_second=p_second,
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
        description="SZM simulation with unanimity and "
                    "optional Monte Carlo")
    p.add_argument("--prec", type=int, default=20,
                   help="Precision (defines ~number of "
                        "steps)")
    p.add_argument("--p_second", type=float, default=0.01,
                   help="Probability of error in the 2nd "
                        "digit")
    p.add_argument("--p_both", type=float, default=0.001,
                   help="Probability of error in the first "
                        "2 digits")
    p.add_argument("--retries", type=int, default=3,
                   help="Retries to reach unanimity before "
                        "the fallback")
    p.add_argument("--seed", type=int, default=42,
                   help="Base seed (single run)")
    p.add_argument("--mc", action="store_true",
                   help="Enable Monte Carlo")
    p.add_argument("--n_runs", type=int, default=500,
                   help="Number of sessions in the Monte "
                        "Carlo")
    p.add_argument("--mc_seed0", type=int, default=20250809,
                   help="Monte Carlo seed (selection of "
                        "base seeds)")
    return p.parse_args()

def main():
    args = parse_args()

    # Single run (sample)
    r = simulate_session(prec=args.prec,
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

    # Monte Carlo (optional)
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
