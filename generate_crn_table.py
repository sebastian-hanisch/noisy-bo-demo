"""Tabelle der Terminal-Scheibe mit **gemeinsamen Zufallszahlen**: Wiederholung r aller 204 Einstellungen nutzt denselben Simulations-Seed.

    python generate_crn_table.py            # schreibt precomputed_crn.json (rund 3 bis 5 Minuten auf 14 Kernen)

Gegenstück zu `precomputed_slice.json` (aus bayes-opt-demo), dessen Wiederholungen je Einstellung unabhängige Seeds haben. Jede Zahl ist eine echte Simulation.
"""
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import nbo_constants as C
import nbo_terminal as T


def cell(args):
    i, j = args
    k, sp = C.PLACES[i], C.SPEEDS[j]
    return i, j, {t: [T.simulate_cost(k, sp, t, C.CRN_SEED_BASE + r) for r in range(C.REPLICATES)] for t in C.TRUCK_CHOICES}


def main(workers=14):
    t0 = time.time()
    reps = {str(t): [[None] * C.N_SPEEDS for _ in range(C.N_PLACES)] for t in C.TRUCK_CHOICES}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for i, j, vals in ex.map(cell, [(i, j) for i in range(C.N_PLACES) for j in range(C.N_SPEEDS)], chunksize=1):
            for t in C.TRUCK_CHOICES:
                reps[str(t)][i][j] = vals[t]
    out = {"places": list(C.PLACES), "speeds": list(C.SPEEDS), "reps": reps, "meta": {"seed_base": C.CRN_SEED_BASE, "replicates": C.REPLICATES, "seconds": round(time.time() - t0)}}
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "precomputed_crn.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    print("fertig in", round(time.time() - t0), "s")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 14)
