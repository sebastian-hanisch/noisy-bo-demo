"""Landschaften und Läufe: Form, Ziehen ohne Zurücklegen, gemeinsame Zufallszahlen, Reproduzierbarkeit, Budget in Auswertungen."""

import numpy as np
import pytest

import nbo_constants as C
import nbo_evaluation as ev
import nbo_scenario as S


def test_branin_noise_has_the_requested_spread():
    f = S.BraninField(20.0, 3)
    draws = np.array([f.observe(10, 10) for _ in range(4000)])
    assert draws.mean() == pytest.approx(S.BraninField.truth_grid()[10, 10], abs=1.5)
    assert draws.std() == pytest.approx(20.0, rel=0.08)


def test_terminal_independent_field_draws_without_replacement():
    f = S.TerminalField(3000, 1, crn=False)
    vals = [f.observe(3, 4) for _ in range(C.REPLICATES)]
    assert sorted(vals) == sorted(S.terminal_reps(3000, False)[3, 4].tolist())


def test_terminal_crn_field_uses_the_same_replicate_for_every_setting():
    f = S.TerminalField(3000, 1, crn=True)
    reps = S.terminal_reps(3000, True)
    for k in range(3):
        r = (f.r0 + k) % C.REPLICATES
        for (i, j) in ((0, 0), (5, 7), (11, 16)):
            assert f.observe(i, j, k) == reps[i, j, r]


def test_tables_have_the_grid_shape():
    for crn in (False, True):
        for t in C.TRUCK_CHOICES:
            assert S.terminal_reps(t, crn).shape == (C.N_PLACES, C.N_SPEEDS, C.REPLICATES)
    assert S.terminal_truth().shape == (C.N_PLACES, C.N_SPEEDS)


def test_runs_are_reproducible_and_basis_and_choice_share_the_start_design():
    s = ev.Settings(n=12, noise=20.0, trucks=3000, seed=7)
    a = ev.run_one("terminal", ev.BASE, s, 12)
    b = ev.run_one("terminal", ev.BASE, s, 12)
    assert a.idx == b.idx and a.y == b.y
    c = ev.run_one("terminal", ev.Choice(rule="mean"), s, 12)
    assert a.idx == c.idx                                       # nur die Empfehlung ist anders
    r = ev.run_one("terminal", ev.Choice(repeats=3), s, 12)
    assert len(r.idx) == 4 and len(r.truth_by_points) == 4        # 12 Auswertungen, drei je Einstellung


def test_truth_at_maps_evaluations_to_points():
    s = ev.Settings(n=12, noise=5.0, seed=3)
    r = ev.run_one("branin", ev.Choice(repeats=3), s, 12)
    assert ev.truth_at(r, 12, 3) == r.truth_by_points[3]
    assert ev.truth_at(r, 6, 3) == r.truth_by_points[1]
    assert ev.truth_at(r, 1, 3) == r.truth_by_points[0]


def test_optimism_is_observation_minus_truth_of_the_recommended_setting():
    s = ev.Settings(n=12, noise=20.0, seed=5)
    r = ev.run_one("branin", ev.BASE, s, 12)
    truth = S.BraninField.truth_grid().reshape(-1)
    assert r.optimism == pytest.approx(min(r.y) - truth[r.rec])
    assert r.rec == r.idx[int(np.argmin(r.y))]
