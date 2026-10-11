"""Orakel-Tests noisy-bo-demo: Kern und Tabellen gegen unabhängige Rechenwege (ORACLE-PLAYBOOK).

* Gauß-Prozess: Vorhersage gegen scikit-learn; erwartete Verbesserung gegen numerische Integration.
* Auswahlverzerrung: Mittel des kleinsten von n unabhängigen N(0, 1) gegen die Formel E[min] = -∫ x φ(x) n (1 - Φ(x))^(n-1) dx (numerisch integriert).
* Tabelle mit gemeinsamen Zufallszahlen: eine Zelle wird mit dem Simulator neu gerechnet; die Varianz von Unterschieden ist kleiner als bei unabhängigen Zufallszahlen.
* Vorzeichentest gegen die Binomialverteilung von Hand.
"""

import numpy as np
import pytest

import nbo_algorithm as A
import nbo_constants as C
import nbo_evaluation as ev
import nbo_scenario as S


def test_gp_prediction_matches_scikit_learn_at_the_learned_hyperparameters():
    gpm = pytest.importorskip("sklearn.gaussian_process")
    from sklearn.gaussian_process.kernels import ConstantKernel, Matern

    rng = np.random.default_rng(11)
    X = rng.random((10, 2))
    y = np.sin(3 * X[:, 0]) + X[:, 1] ** 2 + 0.05 * rng.standard_normal(10)
    gp = A.GaussianProcess().fit(X, y)
    z = (y - gp.y_mean) / gp.y_std
    sk = gpm.GaussianProcessRegressor(ConstantKernel(gp.variance, "fixed") * Matern(gp.lengthscales, "fixed", nu=2.5), alpha=gp.noise + 1e-8, optimizer=None).fit(X, z)
    Xs = rng.random((12, 2))
    m_ref, s_ref = sk.predict(Xs, return_std=True)
    mu, sd = gp.predict(Xs)
    assert np.allclose((mu - gp.y_mean) / gp.y_std, m_ref, atol=1e-6)
    assert np.allclose(sd / gp.y_std, s_ref, atol=1e-5)


def test_ei_matches_numerical_integration():
    quad = pytest.importorskip("scipy.integrate").quad
    from scipy.stats import norm

    for mu, sd, best in [(0.3, 0.5, 0.0), (-0.2, 0.1, 0.0), (1.0, 2.0, 0.0)]:
        ref, _ = quad(lambda f: max(best - f, 0.0) * norm.pdf(f, mu, sd), mu - 12 * sd, mu + 12 * sd, limit=200)
        assert A.expected_improvement(np.array([mu]), np.array([sd]), best)[0] == pytest.approx(ref, rel=1e-6, abs=1e-9)


def test_selection_bias_of_the_smallest_observation_matches_the_order_statistic():
    """Unter n gleichen Einstellungen mit unabhängigem N(0, sigma²)-Rauschen ist die kleinste Beobachtung im Mittel E[min] = -sigma · 2,043 (n = 30)."""
    quad = pytest.importorskip("scipy.integrate").quad
    from scipy.stats import norm

    n, sigma = 30, 20.0
    e_min, _ = quad(lambda x: x * n * norm.pdf(x) * (1 - norm.cdf(x)) ** (n - 1), -10, 10)
    assert e_min == pytest.approx(-2.043, abs=3e-3)
    rng = np.random.default_rng(0)
    cand = np.linspace(0, 1, n)[:, None]
    mins = []
    for s in range(400):
        r = np.random.default_rng(1000 + s)
        idx, y = A.search(cand, lambda i, k, r=r: float(sigma * r.standard_normal()), n, np.random.default_rng(s), method="random")
        mins.append(min(y))
    assert np.mean(mins) == pytest.approx(sigma * e_min, abs=0.15 * sigma)


def test_repeats_reduce_the_selection_bias_roughly_like_one_over_sqrt_m():
    quad = pytest.importorskip("scipy.integrate").quad
    from scipy.stats import norm

    def bias(n, m, sigma=20.0, runs=400):
        out = []
        for s in range(runs):
            r = np.random.default_rng(5000 + s)
            idx, y = A.search(np.linspace(0, 1, n)[:, None], lambda i, k, r=r: float(sigma * r.standard_normal()), n * m, np.random.default_rng(s), repeats=m, method="random")
            out.append(min(y))
        return abs(np.mean(out))

    b1, b4 = bias(30, 1), bias(30, 4)
    assert b4 < 0.65 * b1                                   # Theorie: Faktor 1/2 bei gleich vielen Einstellungen
    assert b4 == pytest.approx(b1 / 2, rel=0.25)


def test_crn_table_cell_matches_a_fresh_simulation():
    import nbo_terminal as T
    reps = S.terminal_reps(3000, True)
    i, j, r = 3, 4, 7
    fresh = T.simulate_cost(C.PLACES[i], C.SPEEDS[j], 3000, C.CRN_SEED_BASE + r)
    assert fresh == pytest.approx(reps[i, j, r], rel=1e-9)


def test_crn_reduces_the_variance_of_differences_between_neighbouring_points():
    ind, crn = S.terminal_reps(3000, False), S.terminal_reps(3000, True)
    truth = S.terminal_truth()
    ok = truth[:, :-1] < 2000
    ok &= truth[:, 1:] < 2000
    v_ind = np.var(ind[:, 1:] - ind[:, :-1], axis=-1)
    v_crn = np.var(crn[:, 1:] - crn[:, :-1], axis=-1)
    assert np.median(v_crn[ok]) < 0.6 * np.median(v_ind[ok])


def test_sign_test_by_hand():
    from scipy.stats import binomtest
    assert binomtest(9, 10, 0.5).pvalue == pytest.approx(22 / 1024)


def test_paired_stats_on_a_known_pair(monkeypatch):
    fake = {"runs": {"branin_20.0": {"base": {"regret": [[0.0, 0.0, 10.0]] * 10}, "rep2": {"regret": [[0.0, 0.0, 9.0]] * 9 + [[0.0, 0.0, 11.0]]}}}}
    monkeypatch.setattr(ev, "study", lambda: fake)
    s = ev.paired_stats("branin", "rep2", 30, 20.0)
    assert (s["better"], s["worse"], s["equal"]) == (9, 1, 0) and s["p"] == pytest.approx(22 / 1024) and s["median_diff"] == pytest.approx(-1.0)
    assert ev.verdict_of(s) == "besser"
