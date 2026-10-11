"""Jede Zahl aus dem README, nachgerechnet über dieselben Auswertungsfunktionen wie die App (vorgerechnete Studie, 20 feste gepaarte Läufe).

Die Studie ist festgeschrieben (precomputed_study.json); die Bänder decken eine Neuberechnung auf anderer Plattform ab."""

import pytest

import nbo_constants as C
import nbo_evaluation as ev


def stats(kind, key, cp, level):
    nz = level if kind == "branin" else None
    tr = level if kind == "terminal" else None
    return ev.paired_stats(kind, key, cp, nz, tr)


def test_repeats_hurt_where_the_noise_is_moderate_and_in_the_terminal():
    for kind, level in (("branin", 5.0), ("terminal", 3000), ("terminal", 15000)):
        for key in ("rep3", "rep5"):
            s = stats(kind, key, 30, level)
            assert ev.verdict_of(s) == "schlechter", (kind, level, key)
    s = stats("branin", "rep5", 30, 5.0)
    assert (s["better"], s["worse"]) == (2, 17) and s["p"] < 0.01


def test_repeats_are_not_distinguishable_at_strong_branin_noise():
    for key in ("rep2", "rep3", "rep5"):
        assert ev.verdict_of(stats("branin", key, 30, 20.0)) == "kein Unterschied nachweisbar"
        assert stats("branin", key, 30, 20.0)["p"] > 0.1


def test_the_best_observation_is_too_good_and_repeats_shrink_the_bias():
    for kind, level, base_bias, band in (("branin", 5.0, -8.3, 2.0), ("branin", 20.0, -38.0, 8.0), ("terminal", 3000, -21.4, 6.0), ("terminal", 15000, -3.8, 3.0)):
        tab, _ = ev.variant_table(kind, level if kind == "branin" else None, level if kind == "terminal" else None)
        assert tab["base"]["optimism"] == pytest.approx(base_bias, abs=band), (kind, level)
        assert tab["rep5"]["optimism"] > tab["base"]["optimism"], (kind, level)           # weniger negativ: näher an der Wahrheit
    tab, _ = ev.variant_table("branin", 20.0, None)
    assert abs(tab["base"]["optimism"]) > 4 * abs(tab["rep5"]["optimism"])


def test_the_model_mean_rule_is_not_reliably_better():
    verdicts = [ev.verdict_of(stats(k, "rule_mean", cp, lv)) for k, lv in (("branin", 5.0), ("branin", 20.0), ("terminal", 3000), ("terminal", 15000)) for cp in C.CHECKPOINTS]
    assert "besser" not in verdicts
    assert verdicts.count("schlechter") <= 2
    tab, _ = ev.variant_table("branin", 20.0, None)
    assert abs(tab["rule_mean"]["optimism"]) < 0.6 * abs(tab["base"]["optimism"])           # verringert den Optimismus der Beobachtung, nicht den Regret


def test_common_random_numbers_help_at_short_runs_at_twenty_evaluations():
    s = stats("terminal", "crn", 20, 3000)
    assert (s["better"], s["worse"]) == (15, 3) and s["p"] < 0.01 and s["median_diff"] < 0
    assert ev.verdict_of(stats("terminal", "crn", 30, 3000)) == "kein Unterschied nachweisbar"
    assert ev.verdict_of(stats("terminal", "crn", 30, 15000)) == "kein Unterschied nachweisbar"
    tab, _ = ev.variant_table("terminal", None, 3000)
    assert abs(tab["crn"]["optimism"]) < 0.1 * abs(tab["base"]["optimism"])                  # gemeinsame Zufallszahlen: Beobachtung ≈ Wahrheit


def test_crn_with_repeats_is_worse_than_the_base():
    for lv in (3000, 15000):
        assert ev.verdict_of(stats("terminal", "crn_rep3", 30, lv)) == "schlechter"


def test_basis_does_not_beat_random_at_the_terminal_with_few_evaluations():
    tab, _ = ev.variant_table("terminal", None, 3000)
    assert tab["base"][20]["median"] > tab["random"][20]["median"]


def test_study_geometry():
    st = ev.study()
    assert st["meta"]["seeds"] == 20
    assert set(st["runs"]) == {"branin_5.0", "branin_20.0", "terminal_3000", "terminal_15000"}
    for name, runs in st["runs"].items():
        for key, rec in runs.items():
            assert len(rec["regret"]) == 20 and len(rec["optimism"]) == 20, (name, key)
        assert ("crn" in runs) == name.startswith("terminal")
