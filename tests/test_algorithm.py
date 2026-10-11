"""Einheiten des Kerns an Mini-Instanzen (Handrechnung): Kern, Akquisition, Wiederholungen, Empfehlungsregeln, Suche."""

import math

import numpy as np
import pytest

import nbo_algorithm as A


def test_matern_kernel_by_hand():
    """Bei sqrt(5) r = 1 ist k = (1 + 1 + 1/3) e^-1 = 0,85836 (Varianz 1); k(x, x) = Varianz."""
    r = 1.0 / math.sqrt(5.0)
    assert A.matern52(np.array([[0.0]]), np.array([[r]]), np.array([1.0]), 1.0)[0, 0] == pytest.approx((7 / 3) * math.exp(-1), rel=1e-12)
    assert A.matern52(np.array([[0.3]]), np.array([[0.3]]), np.array([0.5]), 2.5)[0, 0] == pytest.approx(2.5)


def test_expected_improvement_by_hand():
    one = np.array([1.0])
    assert A.expected_improvement(np.array([0.0]), one, 0.0)[0] == pytest.approx(0.3989422804, rel=1e-9)
    assert A.expected_improvement(np.array([1.0]), one, 0.0)[0] == pytest.approx(0.0833155, rel=1e-5)
    assert A.expected_improvement(np.array([-2.0]), np.array([0.0]), 0.0)[0] == pytest.approx(2.0, abs=1e-9)


def test_evaluate_point_averages_the_repeats_and_passes_the_repeat_index():
    seen = []

    def ev(i, k):
        seen.append((i, k))
        return float(10 * i + k)

    assert A.evaluate_point(ev, 4, 3) == pytest.approx((40 + 41 + 42) / 3)
    assert seen == [(4, 0), (4, 1), (4, 2)]


def test_search_spends_the_budget_in_evaluations(toy):
    cand, f = toy
    for repeats, expected_points in ((1, 12), (2, 6), (3, 4), (5, 2)):
        calls = []
        idx, y = A.search(cand, lambda i, k, c=calls: (c.append(1), f[i])[1], 12, np.random.default_rng(1), repeats=repeats, n_start=5)
        assert len(idx) == expected_points == len(set(idx)) and len(calls) == expected_points * repeats, repeats


def test_random_search_has_no_repeats_and_budget_points(toy):
    cand, f = toy
    idx, y = A.search(cand, lambda i, k: f[i], 8, np.random.default_rng(2), method="random")
    assert len(idx) == 8 == len(set(idx)) and np.allclose(y, f[idx])


def test_recommend_rules_follow_their_definitions_and_differ_on_noisy_data():
    """'obs' ist die kleinste Beobachtung, 'mean' der kleinste Mittelwert des Modells an den Beobachtungen (unabhängig nachgerechnet); bei verrauschten
    Daten weichen sie in einem Teil der Läufe voneinander ab (Zweig-Test: die Regel wirkt)."""
    cand = np.linspace(0, 1, 41)[:, None]
    idx = list(range(0, 41, 2))
    truth = 4.0 * (cand[:, 0] - 0.5) ** 2
    differ = 0
    for seed in range(12):
        y = list(truth[idx] + 0.6 * np.random.default_rng(seed).standard_normal(len(idx)))
        assert A.recommend(cand, idx, y, "obs") == idx[int(np.argmin(y))]
        mu = A.GaussianProcess().fit(cand[idx], y).predict(cand[idx])[0]
        assert A.recommend(cand, idx, y, "mean") == idx[int(np.argmin(mu))]
        differ += int(A.recommend(cand, idx, y, "obs") != A.recommend(cand, idx, y, "mean"))
    assert 1 <= differ


def test_gp_learns_more_noise_from_noisier_data():
    rng = np.random.default_rng(5)
    x = np.linspace(0, 1, 20)[:, None]
    base = np.sin(3 * x[:, 0])
    small = A.GaussianProcess().fit(x, base + 0.02 * rng.standard_normal(20))
    big = A.GaussianProcess().fit(x, base + 0.5 * rng.standard_normal(20))
    assert big.noise > small.noise


def test_search_never_picks_an_evaluated_point_twice(toy):
    cand, f = toy
    idx, y = A.search(cand, lambda i, k: f[i], 10, np.random.default_rng(3), repeats=1, n_start=3)
    assert len(idx) == len(set(idx)) == 10
