#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ------------------
# Source file:       szm_feasibility.py
# Author:            Antonio Ferrão Neto
#
# Description:
# Monte Carlo simulator for the Successive Zooms Method (SZM),
# EXTENDED from the original szm_simulation.py to demonstrate the
# FEASIBILITY of the method with realistic, cheap hardware.
#
# Two model changes relative to the original:
#
#   (1) DIGITS PER READING (d): the device reads d significant digits per
#       step (the original fixed d=2). The zoom advances x10^d. More digits
#       per round => fewer rounds => faster, at the cost of a more expensive
#       device. The noise concentrates on the LAST digit read (the "half" of
#       a three-and-a-half-digit device).
#
#   (2) REPROCESS UNTIL SUCCESS: the 3 devices read the same residual; if
#       there is unanimity, accept and advance; if there is disagreement, the
#       monitor detects it and orders a reread, repeating until unanimity
#       (high safety cap). The 2-of-3 majority remains as a last-resort
#       tie-break, almost never used. Consequence: the value is ALWAYS
#       recovered (except for the extremely rare "wrong unanimity"). What is
#       measured is not "failure", it is the TIME COST (reprocessings).
#
# The monitoring technique here is only the majority-of-3. Others (e.g.
# Richardson Extrapolation, discussed in the appendix) fall outside the scope
# of a POC -- they belong to the electronic engineering project.
# ------------------

import argparse
import math
import random
from decimal import Decimal, getcontext, ROUND_FLOOR
from typing import List, Tuple, Dict, Optional

RETRY_CAP = 100000  # safety cap; in practice never reached


# ========================================
#  "True" sequence of blocks of d digits (noise-free)
# ========================================

class SZMBase:
    __slots__ = ("_precision", "_mantissa_norm", "_exponent",
                 "_sign", "_threshold", "_d")

    DEFAULT_NUMBER = ('0.000000000000000000000000004534697376'
                      '5926712948227673828785441322473869300353232')

    def __init__(self, precision: int, d: int,
                 number: Optional[Decimal] = None):
        if precision < 1:
            raise ValueError("precision must be >= 1")
        if d < 1:
            raise ValueError("d must be >= 1")
        self._precision = int(precision)
        self._d = int(d)
        getcontext().prec = self._precision
        v = Decimal(self.DEFAULT_NUMBER) if number is None else Decimal(str(number))
        if v.is_zero():
            self._sign, self._exponent, self._mantissa_norm = '', 0, Decimal(0)
        else:
            self._sign = '-' if v.is_signed() else ''
            adj = v.adjusted()
            self._exponent = adj
            self._mantissa_norm = v.copy_abs().scaleb(-adj)   # [1,10)
        del v
        self._threshold = Decimal('1').scaleb(-(self._precision - 1))

    def generate_blocks(self) -> List[str]:
        """Blocks of d digits, in order of significance."""
        if self._mantissa_norm.is_zero():
            return []
        d = self._d
        factor = Decimal(10) ** (d - 1)   # brings d digits into the integer part
        zoom = Decimal(10) ** d
        mant = +self._mantissa_norm
        n_steps = (self._precision + d) // d + 2
        out: List[str] = []
        for _ in range(n_steps):
            if mant <= 0:
                break
            block = (mant * factor).to_integral_value(rounding=ROUND_FLOOR)
            nxt = block / factor
            mant = (mant - nxt) * zoom
            if mant.copy_abs() < self._threshold:
                mant = Decimal(0)
            out.append(f"{int(block):0{d}d}")
        return out


# ========================================
#  Noisy device: noise in the LAST digit (p_last) or the whole block (p_block)
# ========================================

class NoisyDevice:
    __slots__ = ("p_last", "p_block", "d", "rng")

    def __init__(self, p_last: float, p_block: float, d: int, seed: int):
        if not (0 <= p_last <= 1 and 0 <= p_block <= 1):
            raise ValueError("probabilities must be in [0,1]")
        if p_last + p_block > 1:
            raise ValueError("p_last + p_block cannot exceed 1")
        self.p_last = float(p_last)
        self.p_block = float(p_block)
        self.d = int(d)
        self.rng = random.Random(seed)

    def read(self, true_block: str) -> str:
        u = self.rng.random()
        # error in the whole block (catastrophic, rare): another d-digit value
        if u < self.p_block:
            while True:
                cand = self.rng.randrange(10 ** self.d)
                s = f"{cand:0{self.d}d}"
                if s != true_block:
                    return s
        # error only in the last digit
        if u < self.p_block + self.p_last:
            last = int(true_block[-1])
            new = (last + 1 + self.rng.randrange(9)) % 10
            return true_block[:-1] + str(new)
        # no error
        return true_block


# ========================================
#  Step with reprocessing until unanimity (monitor = majority-of-3)
# ========================================

def unanimity_step(true_block: str,
                   devs: Tuple[NoisyDevice, NoisyDevice, NoisyDevice]
                   ) -> Tuple[str, int, bool]:
    """Returns (accepted_block, attempts, wrong_unanimity).

    Rereads until the three agree. Only accepts a wrong block if the three
    give the SAME wrong value (wrong unanimity, extremely rare). The cap is a
    safety measure."""
    attempts = 0
    while attempts < RETRY_CAP:
        attempts += 1
        b1 = devs[0].read(true_block)
        b2 = devs[1].read(true_block)
        b3 = devs[2].read(true_block)
        if b1 == b2 == b3:
            return b1, attempts, (b1 != true_block)
        # disagreement: the monitor detects it and orders a reprocess
    # cap reached (practically never): tie-break by majority
    if b1 == b2 or b1 == b3:
        acc = b1
    elif b2 == b3:
        acc = b2
    else:
        acc = b1
    return acc, attempts, (acc != true_block)


def simulate_session(precision: int, d: int, p_last: float, p_block: float,
                     seed_base: int) -> Dict[str, object]:
    base = SZMBase(precision, d)
    true_blocks = base.generate_blocks()
    devs = (
        NoisyDevice(p_last, p_block, d, seed_base + 0),
        NoisyDevice(p_last, p_block, d, seed_base + 1),
        NoisyDevice(p_last, p_block, d, seed_base + 2),
    )
    accepted: List[str] = []
    attempts_per_block: List[int] = []
    refetches = 0
    wrong_unan = 0
    for tb in true_blocks:
        acc, attempts, wu = unanimity_step(tb, devs)
        accepted.append(acc)
        attempts_per_block.append(attempts)
        refetches += (attempts - 1)
        if wu:
            wrong_unan += 1
    recovered = (accepted == true_blocks)
    return {
        "n_blocks": len(true_blocks),
        "refetches": refetches,
        "attempts_per_block": attempts_per_block,
        "wrong_unan": wrong_unan,
        "recovered": recovered,
    }


# ========================================
#  Monte Carlo
# ========================================

def monte_carlo(n_runs: int, precision: int, d: int, p_last: float,
                p_block: float, seed0: int) -> Dict[str, float]:
    rng = random.Random(seed0)
    n_recovered = 0
    n_wrong_unan_sessions = 0
    sum_refetches = 0
    sum_attempts = 0
    sum_blocks = 0
    worst_case = 0
    n_blocks_fixed = 0
    for _ in range(n_runs):
        sb = rng.randrange(1 << 30)
        r = simulate_session(precision, d, p_last, p_block, sb)
        if r["recovered"]:
            n_recovered += 1
        if r["wrong_unan"] > 0:
            n_wrong_unan_sessions += 1
        sum_refetches += r["refetches"]
        sum_attempts += sum(r["attempts_per_block"])
        sum_blocks += r["n_blocks"]
        m = max(r["attempts_per_block"]) if r["attempts_per_block"] else 0
        if m > worst_case:
            worst_case = m
        n_blocks_fixed = r["n_blocks"]
    return {
        "runs": n_runs,
        "d": d,
        "digits_per_round": d,
        "rounds": n_blocks_fixed,
        "recovery_rate": n_recovered / n_runs if n_runs else 0.0,
        "frac_wrong_unanimity":
            n_wrong_unan_sessions / n_runs if n_runs else 0.0,
        "refetches_per_block":
            sum_refetches / sum_blocks if sum_blocks else 0.0,
        "refetches_per_session":
            sum_refetches / n_runs if n_runs else 0.0,
        "attempts_per_block":
            sum_attempts / sum_blocks if sum_blocks else 0.0,
        "worst_case_attempts": worst_case,
    }


# ========================================
#  CLI
# ========================================

def main():
    p = argparse.ArgumentParser(
        description="SZM feasibility simulation (d digits, reprocess until success)")
    p.add_argument("--precision", type=int, default=20)
    p.add_argument("--d", type=int, default=2, help="digits per reading")
    p.add_argument("--p_last", type=float, default=0.02,
                   help="prob. of error in the LAST digit")
    p.add_argument("--p_block", type=float, default=0.0001,
                   help="prob. of error in the whole block (catastrophic)")
    p.add_argument("--n_runs", type=int, default=20000)
    p.add_argument("--seed0", type=int, default=20250809)
    args = p.parse_args()
    mc = monte_carlo(args.n_runs, args.precision, args.d, args.p_last,
                     args.p_block, args.seed0)
    print(f"--- SZM feasibility  d={args.d} p_last={args.p_last} "
          f"p_block={args.p_block} runs={args.n_runs} ---")
    for k, v in mc.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
