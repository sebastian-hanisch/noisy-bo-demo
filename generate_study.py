"""Vorgerechnete Studie: Empfehlungsregel, Wiederholungen und gemeinsame Zufallszahlen gegen die Basis, 20 feste Läufe, vier Rauschstufen
(Branin 5 und 20, Terminal 3 000 und 15 000 Lkw). Rund 5 bis 10 Minuten auf 14 Kernen. Braucht `precomputed_crn.json` (generate_crn_table.py).

    python generate_study.py            # schreibt precomputed_study.json
"""
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import nbo_constants as C
import nbo_evaluation as ev
import nbo_scenario as S

VARIANTS = {
    "random": (ev.Choice(), "random"),
    "base": (ev.Choice(), "bo"),
    "rule_mean": (ev.Choice(rule="mean"), "bo"),
    "rep2": (ev.Choice(repeats=2), "bo"),
    "rep3": (ev.Choice(repeats=3), "bo"),
    "rep5": (ev.Choice(repeats=5), "bo"),
    "crn": (ev.Choice(crn=True), "bo"),
    "crn_rep3": (ev.Choice(repeats=3, crn=True), "bo"),
}
TERMINAL_ONLY = {"crn", "crn_rep3"}


def job(args):
    kind, level, key, seed = args
    choice, method = VARIANTS[key]
    st = ev.Settings(n=max(C.CHECKPOINTS), noise=level if kind == "branin" else C.DEFAULT_NOISE, trucks=int(level) if kind == "terminal" else C.DEFAULT_TRUCKS, seed=seed)
    run = ev.run_one(kind, choice, st, st.n, 0, method)
    opt = float(S.BraninField.truth_grid().min()) if kind == "branin" else float(S.terminal_truth().min())
    regret = [ev.truth_at(run, cp, choice.repeats) - opt for cp in C.CHECKPOINTS]
    return kind, level, key, seed, regret, run.optimism


def main(workers=14):
    t0 = time.time()
    jobs = []
    for z in C.BRANIN_NOISES:
        jobs += [("branin", z, k, s) for k in VARIANTS if k not in TERMINAL_ONLY for s in C.SWEEP_SEEDS]
    for t in C.TRUCK_CHOICES:
        jobs += [("terminal", t, k, s) for k in VARIANTS for s in C.SWEEP_SEEDS]
    runs = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for kind, level, key, seed, regret, opt_ in ex.map(job, jobs, chunksize=2):
            name = f"branin_{float(level)}" if kind == "branin" else f"terminal_{int(level)}"
            rec = runs.setdefault(name, {}).setdefault(key, {"regret": [], "optimism": []})
            rec["regret"].append(regret)
            rec["optimism"].append(opt_)
    out = {"runs": runs, "optimum": {"branin": float(S.BraninField.truth_grid().min()), "terminal": float(S.terminal_truth().min())},
           "meta": {"seeds": len(C.SWEEP_SEEDS), "jobs": len(jobs), "seconds": round(time.time() - t0)}}
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "precomputed_study.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    print("fertig", len(jobs), "Läufe in", round(time.time() - t0), "s")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 14)
