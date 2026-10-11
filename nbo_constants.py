"""Konstanten der Demo „Verrauschte Auswertungen“: Landschaften, Terminal-Annahmen, Regler, Presets, Studie, Farben.

Das Terminal ist das Netz aus jackson-network-demo mit Platzgrenze am Stapel (wie in bayes-opt-demo): Zeiten in Minuten, Kosten in EUR je Stunde. Die
Terminal-Scheibe (Plätze am Stapel x Tempo des Stapels, 12 x 17 Einstellungen) hat zwei Tabellen echter Simulationen: unabhängige Wiederholungen
(`precomputed_slice.json`, aus bayes-opt-demo) und Wiederholungen mit **gemeinsamen Zufallszahlen** (`precomputed_crn.json`, `generate_crn_table.py`).
"""

# --- Landschaften -----------------------------------------------------------------------------------------------------------------------
KINDS = ("branin", "terminal")
KIND_LABELS = {"branin": "Branin (Gauß-Rauschen)", "terminal": "Terminal-Scheibe (echte Simulationen)"}
BRANIN_STEPS = 31
BRANIN_NOISES = (5.0, 20.0)
NOISE_LABEL = {5.0: "5 (mäßig)", 20.0: "20 (stark)"}
DEFAULT_NOISE = 20.0
TRUCK_CHOICES = (3000, 15000)
TRUCKS_LABEL = {3000: "3 000 Lkw (billig, verrauscht)", 15000: "15 000 Lkw (teurer, ruhiger)"}
DEFAULT_TRUCKS = 3000
PLACES = tuple(range(2, 14))
SPEEDS = tuple(round(0.6 + 0.05 * i, 2) for i in range(17))
N_PLACES, N_SPEEDS = len(PLACES), len(SPEEDS)
REPLICATES = 30

# --- Das Terminal (Annahmen der Demo, wie in bayes-opt-demo) -----------------------------------------------------------------------------
GAMMA_PER_HOUR = 33.0
GATE_SERVERS, KRAN_SERVERS, STAPEL_SERVERS = 4, 4, 5
GATE_MEAN, KRAN_BASE_MEAN, STAPEL_BASE_MEAN = 3.0, 2.4, 4.0
KRAN_SPEED = 0.7
CS2 = 2.0
T_CAP = 300.0
K_GATE, K_KRAN, K_STAPEL, K_PLACE = 20.0, 120.0, 60.0, 4.0
V_WAIT = 40.0
CRN_SEED_BASE = 5000             # Wiederholung r aller Einstellungen nutzt denselben Seed CRN_SEED_BASE + r

# --- Verfahren --------------------------------------------------------------------------------------------------------------------------
RULES = ("obs", "mean")
RULE_LABELS = {"obs": "beste Beobachtung", "mean": "bester Mittelwert des Modells"}
REPEAT_CHOICES = (1, 2, 3, 5)
N_START = 5

# --- Regler -----------------------------------------------------------------------------------------------------------------------------
N_MIN, N_MAX, DEFAULT_N = 10, 30, 20
SEED_MAX, DEFAULT_SEED = 999999, 35
SWEEP_SEEDS = tuple(range(500000, 500020))
CHECKPOINTS = (10, 20, 30)

PRESETS = {
    "Standardfall (Voreinstellung)": {"n": DEFAULT_N, "noise": DEFAULT_NOISE, "trucks": DEFAULT_TRUCKS, "rule": "obs", "repeats": 1, "crn": False, "seed": DEFAULT_SEED},
    "Modell traut dem Mittelwert": {"n": DEFAULT_N, "noise": DEFAULT_NOISE, "trucks": DEFAULT_TRUCKS, "rule": "mean", "repeats": 1, "crn": False, "seed": DEFAULT_SEED},
    "Jeder Punkt dreimal": {"n": DEFAULT_N, "noise": DEFAULT_NOISE, "trucks": DEFAULT_TRUCKS, "rule": "obs", "repeats": 3, "crn": False, "seed": DEFAULT_SEED},
    "Gemeinsame Zufallszahlen": {"n": DEFAULT_N, "noise": DEFAULT_NOISE, "trucks": DEFAULT_TRUCKS, "rule": "obs", "repeats": 1, "crn": True, "seed": DEFAULT_SEED},
    "Mäßiges Rauschen": {"n": DEFAULT_N, "noise": 5.0, "trucks": 15000, "rule": "obs", "repeats": 1, "crn": False, "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "Starkes Rauschen (Branin 20, Terminal 3 000 Lkw), Empfehlung = beste Beobachtung, jede Einstellung einmal.",
    "Modell traut dem Mittelwert": "Empfohlen wird die Einstellung mit dem besten Mittelwert des Ersatzmodells statt der besten Einzelbeobachtung.",
    "Jeder Punkt dreimal": "Jede ausgewählte Einstellung wird dreimal ausgewertet und gemittelt: dreimal so wenige verschiedene Einstellungen für dasselbe Budget.",
    "Gemeinsame Zufallszahlen": "Terminal: alle Einstellungen werden mit denselben Zufallszahlen gerechnet, Unterschiede zwischen Einstellungen sind dadurch genauer.",
    "Mäßiges Rauschen": "Branin 5, Terminal 15 000 Lkw: jede Auswertung ist verlässlicher.",
}

COLOR_OBS = "#2F6B65"
COLOR_NEXT = "#D68A2E"
COLOR_BAD = "#B3463A"
COLOR_BASE = "#14233B"
COLOR_CHOICE = "#2F6B65"
COLOR_RANDOM = "#8c8c8c"
