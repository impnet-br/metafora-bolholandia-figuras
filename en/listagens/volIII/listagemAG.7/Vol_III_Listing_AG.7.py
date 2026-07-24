#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ------------------
# Source file:       szm_device.py
# Author:            Antonio Ferrão Neto
# Creation date:     2025-08-08
# Last modified:     2025-08-08
#
# Description:
# Proof of concept for the "Method of Successive Zooms" (SZM) with emphasis on the
# **inaccessibility of the target number**: the analog result (target value) is
# neither exposed nor stored as an object attribute. Only the strictly necessary
# artifacts for incremental extraction (normalized mantissa, exponent, and sign)
# are kept, already *decoupled* from the original value.
#
# The "device" simulates a sensor that returns **blocks of 2 significant digits**
# of the mantissa per interaction. At each reading, it applies **zoom + translation**
# to the residual to bring the next digits into view. The process ends when the
# residual falls below the threshold defined by the precision.
#
# Copyright:
# Copyright: (C) 2025 Antonio Ferrão Neto. All rights reserved.
#
# Usage:
#     python szm_device.py
#
# Example output:
#     n          blocks    mantissas         cumulative_digits
#     0            45       0.34697376592671294822           45
#     1            34       0.69737659267129482276         4534
#     2            69       0.73765926712948227638       453469
#     ...
#     Final result: 4.534697e-27
# ------------------
import decimal
from decimal import Decimal, getcontext, ROUND_FLOOR


class SZMDevice:
    """
    SZM device that **does not store** the target number as an attribute.
    It only keeps the normalized mantissa (in [1,10)), scientific exponent, and sign,
    enough to simulate incremental readings. The original value is never
    exposed and is not recoverable via the public API.
    """

    __slots__ = ("_precision", "_mantissa_norm", "_exponent", "_sign", "_threshold")

    def __init__(self, precision: int, number=None):
        if precision < 1:
            raise ValueError("precision must be >= 1")
        self._precision = int(precision)

        # Note: modifies decimal.getcontext() globally.
        # For concurrent use, replace with decimal.localcontext().
        getcontext().prec = self._precision

        # --- Scientific normalization of the target value (without storing it afterward) ---
        if number is None:
            _value = Decimal('0.000000000000000000000000004534697376592671294822767382'
                             '8785441322473869300353232')
        else:
            _value = Decimal(str(number))

        if _value.is_zero():
            self._sign = ''
            self._exponent = 0
            self._mantissa_norm = Decimal(0)
        else:
            self._sign = '-' if _value.is_signed() else ''
            adj = _value.adjusted()                # scientific exponent
            self._exponent = adj
            self._mantissa_norm = _value.copy_abs().scaleb(-adj)  # in [1,10)

        # Discard the reference to the original value - makes it inaccessible
        del _value

        # Smallest "perceptible" value at the current precision
        self._threshold = Decimal('1').scaleb(-(self._precision - 1))

    # --------- Basic shielding against casual introspection ----------
    def __repr__(self):
        return f"<SZMDevice precision={self._precision} state=protected>"

    # ------------------- Public API -------------------

    @property
    def precision(self) -> int:
        return self._precision

    def extract_pairs(self):
        """
        Returns a dictionary with:
          - 'blocks'          : blocks of 2 digits (strings "00".."99")
          - 'mantissas'  : normalized residuals after each extraction (string)
          - 'cumulative_digits'     : cumulative concatenation of the blocks (string)
        """
        if self._mantissa_norm.is_zero():
            return {'blocks': [], 'mantissas': [], 'cumulative_digits': []}

        block_list = []
        residual_list = []
        accum_list = []

        mant = +self._mantissa_norm   # working copy
        accum = ""

        # Each step consumes 2 significant digits
        # (precision + 2) // 2 steps to cover all the digits, +2 for margin
        max_steps = (self._precision + 2) // 2 + 2

        for _ in range(max_steps):
            if mant.is_zero():
                break
            if mant < 0:
                raise RuntimeError("Negative residual -- extraction error")

            # first two significant digits (10..99)
            d2 = (mant * 10).to_integral_value(rounding=ROUND_FLOOR)   # ex.: 45
            nxt = d2 / Decimal(10)                                    # 4.5

            # zoom + translation
            mant = (mant - nxt) * 100

            # elimination of residual numerical noise
            if mant.copy_abs() < self._threshold:
                mant = Decimal(0)

            block = f"{int(d2):02d}"
            accum += block
            block_list.append(block)
            residual_list.append(f"{mant.normalize():f}")
            accum_list.append(accum)

        return {
            'blocks': block_list,
            'mantissas': residual_list,
            'cumulative_digits': accum_list
        }

    def recompose(self, block_list):
        """
        Reconstructs the number (approximation) only from the blocks read.
        Does not use or expose the original value.
        """
        if not block_list:
            return "0e0"
        digits = ''.join(block_list)
        mant_str = digits[0] + '.' + digits[1:]
        return f"{self._sign}{mant_str}e{self._exponent}"


if __name__ == "__main__":
    dev = SZMDevice(precision=20)
    d = dev.extract_pairs()

    # Print header
    keys = list(d.keys())
    pr = dev.precision
    print(f"{'n':^10}", end=' ')
    for k in keys:
        if k == 'blocks':
            print(f"{k:10}", end=' ')
        else:
            print(f"{k:{pr + 3}}", end=' ')
    print()

    # Number of rows
    m = min((len(v) for v in d.values()), default=0)

    # Table
    for i in range(m):
        print(f"{i:^10}", end=' ')
        for k in keys:
            vals = d[k]
            if k == 'blocks':
                print(f"{vals[i]:^10}", end=' ')
            else:
                print(f"{vals[i]:{pr + 3}}", end=' ')
        print('')

    # Final result
    print("\nFinal result:", dev.recompose(d.get('blocks', [])))
