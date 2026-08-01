#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline verifier for the SZM Challenge / Verificador do Desafio MZS.

    python verificar.py resultado.csv

Reads the stage log produced by the firmware, rebuilds the digit chain and
compares it against sqrt(2) computed in exact integer arithmetic.

Standard library only: no mpmath, no gmpy2, nothing to install. The
reference value comes from isqrt(2 * 10**(2n)), an exact integer square
root -- no floating point, no rounding, no formatting heuristics.

CSV columns expected (header required):

    digit   the block of digits recovered at this stage (one or more)
    trials  how many acquisition attempts this stage needed

`trials` is not bookkeeping. A purely digital algorithm must SEARCH for
each digit, testing candidates; the SZM READS the digit off an instrument.
The number of attempts per stage is therefore the observable that tells the
two apart, which is why the protocol requires logging it.

Optional column:

    quantity  the physical quantity actually measured at this stage

Run it also on the control log -- the run in which the analog reading is
replaced by a random value. There the chain is expected to break at the
first stage. If it survives, the analog block was not contributing.

This file is published at
https://www.impnet.com.br/bolholandia/mzs-resultados/verificar.py
and is part of the challenge stated in the appendix on the Successive
Zooms Method, volume III of "The Bubbleland Metaphor".
"""
import csv
import sys
from math import isqrt


def reference(n_digits):
    """First n digits of sqrt(2), no decimal separator. Exact."""
    if n_digits <= 0:
        return ""
    return str(isqrt(2 * 10 ** (2 * n_digits)))[:n_digits]


def read_log(path):
    """Return (digit chain, list of trial counts)."""
    digits, trials = [], []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or "digit" not in reader.fieldnames:
            sys.exit("error: CSV has no 'digit' column")
        has_trials = "trials" in reader.fieldnames
        for n, row in enumerate(reader, start=2):
            d = (row.get("digit") or "").strip()
            if not d:
                continue
            if not d.isdigit():
                sys.exit("error: line %d: 'digit' is not numeric: %r" % (n, d))
            digits.append(d)
            if has_trials:
                try:
                    trials.append(int((row.get("trials") or "0").strip()))
                except ValueError:
                    sys.exit("error: line %d: 'trials' is not an integer" % n)
    return "".join(digits), trials


def first_difference(got, expected):
    """Number of leading digits that agree."""
    for i, (a, b) in enumerate(zip(got, expected)):
        if a != b:
            return i
    return min(len(got), len(expected))


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python verificar.py <file.csv>")

    got, trials = read_log(sys.argv[1])
    if not got:
        sys.exit("error: no digits found in the log")
    expected = reference(len(got))
    correct = first_difference(got, expected)

    print("digits submitted : %d" % len(got))
    print("digits correct   : %d" % correct)

    if correct < len(got):
        print("breaking stage   : digit %d" % correct)
        print("  submitted : ...%s[%s]" % (got[max(0, correct - 8):correct],
                                           got[correct:correct + 8]))
        print("  expected  : ...%s[%s]" % (expected[max(0, correct - 8):correct],
                                           expected[correct:correct + 8]))
        print("NEGATIVE RESULT - equally publishable; document the physical cause.")
    else:
        print("no divergence within the submitted range.")

    if trials:
        stages = len(trials)
        total = sum(trials)
        print("stages           : %d" % stages)
        print("attempts total   : %d  (%.2f per stage)" % (total, total / stages))
        if total / stages > 3:
            print("  note: more than three attempts per stage on average suggests")
            print("  searching rather than measuring. See the challenge statement.")

    # exit code lets the log be checked from a script
    return 0 if correct == len(got) else 1


if __name__ == "__main__":
    sys.exit(main())
