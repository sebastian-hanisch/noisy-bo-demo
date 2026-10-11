"""Landschaften: Branin mit Gauß-Rauschen und Terminal-Scheibe aus zwei Tabellen echter Simulationen (unabhängige und gemeinsame Zufallszahlen)."""

import json
import os

import numpy as np

import nbo_benchmarks as B
import nbo_constants as C

_HERE = os.path.dirname(os.path.abspath(__file__))
_TABLES = {}


def _load(name):
    if name not in _TABLES:
        with open(os.path.join(_HERE, name), encoding="utf-8") as fh:
            _TABLES[name] = json.load(fh)
    return _TABLES[name]


def terminal_truth():
    """Wahrheit je Einstellung [Plätze, Tempo]: Mittel aus zwei Läufen à 100 000 Lkw (aus bayes-opt-demo)."""
    return np.array(_load("precomputed_slice.json")["truth"], float)


def terminal_reps(trucks, crn):
    """Wiederholungen [Plätze, Tempo, r]: unabhängige Seeds je Einstellung oder gemeinsame Seeds (Wiederholung r überall derselbe Seed)."""
    raw = _load("precomputed_crn.json" if crn else "precomputed_slice.json")
    return np.array(raw["reps"][str(trucks)], float)


def grid_points(shape):
    rows, cols = shape
    return np.array([(i, j) for i in range(rows) for j in range(cols)], dtype=int)


def to_unit(pts, shape):
    rows, cols = shape
    pts = np.asarray(pts, float)
    return np.column_stack([pts[:, 0] / (rows - 1), pts[:, 1] / (cols - 1)])


class BraninField:
    """Branin auf 31 x 31 mit Gauß-Rauschen; Zeilen = x2, Spalten = x1. Jede Auswertung zieht frisches Rauschen."""

    _GRID = None

    def __init__(self, noise, seed):
        self.noise = float(noise)
        self.rng = np.random.default_rng(seed + 31)

    @classmethod
    def _grid(cls):
        if cls._GRID is None:
            cls._GRID = B.branin_grid(C.BRANIN_STEPS)
        return cls._GRID

    @classmethod
    def axes(cls):
        return cls._grid()[0], cls._grid()[1]

    @classmethod
    def truth_grid(cls):
        return cls._grid()[2]

    def observe(self, i, j, k=0):
        return float(self.truth_grid()[i, j] + self.noise * self.rng.standard_normal())


class TerminalField:
    """Terminal-Scheibe. Unabhängig: je Einstellung eine noch nicht gezogene der 30 Wiederholungen. Gemeinsame Zufallszahlen: die k-te Auswertung
    **jeder** Einstellung eines Laufs nutzt dieselbe Wiederholung (r0 + k) mod 30, also dieselben Zufallszahlen."""

    def __init__(self, trucks, seed, crn=False):
        self.reps = terminal_reps(trucks, crn)
        self.crn = bool(crn)
        self.rng = np.random.default_rng(seed)
        self.r0 = int(self.rng.integers(0, C.REPLICATES))
        self.used = {}

    @staticmethod
    def truth_grid():
        return terminal_truth()

    def observe(self, i, j, k=0):
        if self.crn:
            return float(self.reps[i, j, (self.r0 + k) % C.REPLICATES])
        used = self.used.setdefault((i, j), [])
        free = [r for r in range(C.REPLICATES) if r not in used]
        if not free:
            used.clear()
            free = list(range(C.REPLICATES))
        r = int(self.rng.choice(free))
        used.append(r)
        return float(self.reps[i, j, r])
