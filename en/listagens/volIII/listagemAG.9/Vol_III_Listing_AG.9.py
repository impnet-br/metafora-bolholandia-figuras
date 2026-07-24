# -*- coding: utf-8 -*-
"""Runs the two SZM feasibility studies and writes CSVs.

  Study B (BOOK, compact): a few points that tell the story -- from the
    terrible device to the cheap three-and-a-half-digit one -- showing the
    cost knee.
  Study A (ELECTRONIC, full): grid (d, p_last, p_block) to publish on GitHub
    with a QR. Shows that recovery stays ~100% across the whole space and how
    the reprocessing cost varies.

Writes incrementally (one line per combo, with flush) so as not to lose
progress if interrupted. Prints progress.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from szm_feasibility import monte_carlo  # noqa: E402

PRECISION, N_RUNS, SEED0 = 20, 20000, 20250809
OUT = Path(__file__).parent

COLS = ["d", "p_last", "p_block", "rounds", "recovery_rate",
        "frac_wrong_unanimity", "refetches_per_block", "refetches_per_session",
        "attempts_per_block", "worst_case_attempts"]


def csv_row(d, p_last, p_block, mc):
    vals = [d, p_last, p_block, mc["rounds"], mc["recovery_rate"],
            mc["frac_wrong_unanimity"], mc["refetches_per_block"],
            mc["refetches_per_session"], mc["attempts_per_block"],
            mc["worst_case_attempts"]]
    return ",".join(str(v) for v in vals)


def run_study(name, combos, filename):
    path = OUT / filename
    t0 = time.time()
    with path.open("w", encoding="utf-8") as f:
        f.write(",".join(COLS) + "\n")
        f.flush()
        for i, (d, pl, pb) in enumerate(combos, 1):
            mc = monte_carlo(N_RUNS, PRECISION, d, pl, pb, SEED0)
            f.write(csv_row(d, pl, pb, mc) + "\n")
            f.flush()
            print(f"[{name} {i:3d}/{len(combos)}] d={d} p_last={pl} p_block={pb}"
                  f"  rec={mc['recovery_rate']:.4f}"
                  f"  refetch/block={mc['refetches_per_block']:.4f}"
                  f"  ({time.time()-t0:.0f}s)", flush=True)
    print(f"== {name} done: {path.name} ({time.time()-t0:.0f}s)\n", flush=True)


def main():
    # ---- Study B: BOOK (compact) ----------------------------------------
    # From the terrible to the cheap-viable, plus the "best" to show the knee.
    study_b = [
        (2, 0.10, 0.010),   # terrible device
        (2, 0.05, 0.005),   # bad
        (2, 0.02, 0.0001),  # 2 digits, low noise
        (3, 0.02, 0.0001),  # ** cheap three-and-a-half digits -- the operating point **
        (4, 0.02, 0.0001),  # best (does not justify the cost)
        (3, 0.01, 0.0001),  # 3.5 with even lower noise
    ]
    run_study("Study B (book)", study_b, "feas_study_B_book.csv")

    # ---- Study A: ELECTRONIC (full) -------------------------------------
    ds = [2, 3, 4]
    p_lasts = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10,
               0.15, 0.20]
    p_blocks = [0.0001, 0.001, 0.002, 0.005, 0.010]
    combos = [(d, pl, pb) for d in ds for pl in p_lasts for pb in p_blocks]
    print(f"Study A: {len(combos)} combinations x {N_RUNS} sessions\n", flush=True)
    run_study("Study A (electronic)", combos, "feas_study_A_full.csv")

    print("ALL DONE.", flush=True)


if __name__ == "__main__":
    sys.exit(main())
