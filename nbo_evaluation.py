"""Auswertung: ein Lauf mit Empfehlungsregel, Wiederholungen und Zufallszahlen-Modus gegen Basis und Zufall; Optimismus der besten Beobachtung; vorgerechnete Studie."""

import json
import os
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

import nbo_algorithm as A
import nbo_constants as C
import nbo_scenario as S

_HERE = os.path.dirname(os.path.abspath(__file__))


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N                 # Budget in Auswertungen (Simulationsläufen)
    noise: float = C.DEFAULT_NOISE       # Branin: Standardabweichung des Rauschens
    trucks: int = C.DEFAULT_TRUCKS       # Terminal: Lkw je Auswertung
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class Choice:
    rule: str = "obs"
    repeats: int = 1
    crn: bool = False                    # nur Terminal wirksam


BASE = Choice()


@dataclass
class Run:
    label: str
    idx: list                # ausgewertete Einstellungen in Reihenfolge
    y: list                  # Mittelwert je Einstellung
    truth_by_points: list    # wahrer Wert der Empfehlung nach p Einstellungen (p = 1 …)
    rec: int                 # endgültig empfohlene Einstellung
    optimism: float          # beobachteter Wert der Empfehlung minus ihr wahrer Wert (negativ: die Beobachtung ist zu schön)
    repeats: int = 1         # Auswertungen je Einstellung


@dataclass
class Analysis:
    kind: str
    settings: Settings
    runs: dict
    truth: np.ndarray
    optimum: tuple
    x_values: list
    y_values: list


def landscape(kind, settings, seed, crn=False):
    """(Kandidaten im Einheitswürfel, Wahrheit flach, observe(i_flat, k), Rastergröße, Gitterpunkte)."""
    if kind == "branin":
        field = S.BraninField(settings.noise, seed)
    else:
        field = S.TerminalField(settings.trucks, seed, crn)
    grid = field.truth_grid()
    pts = S.grid_points(grid.shape)
    cand = S.to_unit(pts, grid.shape)
    flat = grid.reshape(-1)
    return cand, flat, (lambda i, k=0: field.observe(int(pts[i][0]), int(pts[i][1]), k)), grid.shape


def run_one(kind, choice, settings, evals, seed_offset=0, method="bo", label=""):
    """Ein Suchlauf. Reproduzierbar: Zufallsströme aus Seed und Offset; Startdesign hängt nur vom Seed ab (gepaarter Vergleich möglich)."""
    seed = settings.seed + seed_offset
    cand, truth, ev, _ = landscape(kind, settings, seed, choice.crn and kind == "terminal")
    rng = np.random.default_rng(seed + 7)
    idx, y = A.search(cand, ev, evals, rng, repeats=choice.repeats, n_start=C.N_START, method=method)
    by_points = []
    for p in range(1, len(idx) + 1):
        r = A.recommend(cand, idx[:p], y[:p], choice.rule)
        by_points.append(float(truth[r]))
    rec = A.recommend(cand, idx, y, choice.rule)
    obs = float(y[idx.index(rec)])
    return Run(label, [int(i) for i in idx], [float(v) for v in y], by_points, int(rec), obs - float(truth[rec]), choice.repeats)


def truth_at(run, evals, repeats):
    """Wahrer Wert der Empfehlung nach `evals` Auswertungen (also evals // repeats Einstellungen, mindestens eine)."""
    p = max(1, min(len(run.truth_by_points), evals // repeats))
    return run.truth_by_points[p - 1]


def analyse(settings, choice, kind):
    runs = {
        "random": run_one(kind, BASE, settings, settings.n, 11, method="random", label="Zufall"),
        "base": run_one(kind, BASE, settings, settings.n, 0, label="Basis"),
        "choice": run_one(kind, choice, settings, settings.n, 0, label="Gewählt"),
    }
    truth = S.BraninField.truth_grid() if kind == "branin" else S.terminal_truth()
    if kind == "branin":
        x1, x2 = S.BraninField.axes()
        xs, ys = list(map(float, x1)), list(map(float, x2))
    else:
        xs, ys = list(C.SPEEDS), list(C.PLACES)
    i, j = np.unravel_index(int(np.argmin(truth)), truth.shape)
    return Analysis(kind, settings, runs, truth, (int(i), int(j), float(truth[i, j])), xs, ys)


def final_regret(a):
    return {k: truth_at(r, a.settings.n, r.repeats) - a.optimum[2] for k, r in a.runs.items()}


# --- Vorgerechnete Studie ------------------------------------------------------------------------------------------------------------------

@lru_cache(maxsize=1)
def study():
    with open(os.path.join(_HERE, "precomputed_study.json"), encoding="utf-8") as fh:
        return json.load(fh)


def study_key(kind, noise=None, trucks=None):
    return f"branin_{float(noise)}" if kind == "branin" else f"terminal_{int(trucks)}"


def optimum_of(kind):
    return float(study()["optimum"][kind])


def variant_table(kind, noise=None, trucks=None):
    """Median und 90-%-Quantil des Regrets je Variante und Prüfpunkt (20 feste Läufe) sowie der mittlere Optimismus der besten Beobachtung."""
    raw = study()["runs"][study_key(kind, noise, trucks)]
    opt = optimum_of(kind)
    out = {}
    for key, rec in raw.items():
        arr = np.array(rec["regret"])                 # Läufe x Prüfpunkt
        out[key] = {cp: {"median": float(np.median(arr[:, k])), "q90": float(np.quantile(arr[:, k], 0.9))} for k, cp in enumerate(C.CHECKPOINTS)}
        out[key]["optimism"] = float(np.mean(rec["optimism"]))
    return out, opt


def paired_stats(kind, key, checkpoint, noise=None, trucks=None, tol=1e-6):
    """Gepaarter Vergleich Variante gegen Basis über die 20 Läufe: besser, schlechter, gleich, Median der Differenz (negativ = Variante besser), Vorzeichentest-p."""
    from scipy.stats import binomtest
    raw = study()["runs"][study_key(kind, noise, trucks)]
    k = C.CHECKPOINTS.index(checkpoint)
    diff = np.array(raw[key]["regret"])[:, k] - np.array(raw["base"]["regret"])[:, k]
    better, worse = int((diff < -tol).sum()), int((diff > tol).sum())
    p = float(binomtest(better, better + worse, 0.5).pvalue) if better + worse else 1.0
    return {"better": better, "worse": worse, "equal": int(len(diff) - better - worse), "median_diff": float(np.median(diff)), "p": p, "n": int(len(diff))}


def verdict_of(stats, alpha=0.05):
    if stats["p"] < alpha:
        return "besser" if stats["better"] > stats["worse"] else "schlechter"
    return "kein Unterschied nachweisbar"
