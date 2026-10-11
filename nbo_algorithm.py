"""Kern der Demo: Gauß-Prozess (Matérn-5/2, Längenmaße und Rauschen gelernt), erwartete Verbesserung und eine Suche mit Wiederholungen und zwei Empfehlungsregeln.

Alles auf dem Einheitswürfel, Minimierung, nur numpy/scipy. Eine Einheit = eine Regel (DEMO-PLAYBOOK §1b): `matern52` (Kern), `GaussianProcess.fit/predict`,
`expected_improvement` (Akquisition), `search` (Auswahlregel mit Wiederholungen), `recommend` (Empfehlungsregel). Zufall nur über übergebene Generatoren.
"""

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize
from scipy.stats import norm


def matern52(A, B, lengthscales, variance):
    """Matérn-5/2-Kern k(a, b) = σ² (1 + √5 r + 5r²/3) exp(−√5 r), r = Abstand mit je Eingabe eigenem Längenmaß."""
    r2 = np.maximum((((A[:, None, :] - B[None, :, :]) / lengthscales) ** 2).sum(-1), 0.0)
    s = np.sqrt(5.0) * np.sqrt(r2)
    return variance * (1.0 + s + s * s / 3.0) * np.exp(-s)


class GaussianProcess:
    """Gauß-Prozess-Regression, Ausgabe standardisiert; Längenmaße, Signal- und Rauschvarianz durch Maximieren der Randwahrscheinlichkeit (L-BFGS-B, feste Starts)."""

    def __init__(self, restarts=3):
        self.restarts = restarts

    def _unpack(self, theta, d):
        return np.exp(theta[:d]), np.exp(theta[d]), np.exp(theta[d + 1])

    def _neg_log_marginal(self, theta, X, z):
        ls, var, nz = self._unpack(theta, X.shape[1])
        K = matern52(X, X, ls, var) + (nz + 1e-8) * np.eye(len(X))
        try:
            c = cho_factor(K, lower=True)
        except np.linalg.LinAlgError:
            return 1e10
        a = cho_solve(c, z)
        return 0.5 * z @ a + np.log(np.diag(c[0])).sum() + 0.5 * len(z) * np.log(2 * np.pi)

    def fit(self, X, y):
        X = np.asarray(X, float)
        y = np.asarray(y, float)
        self.X = X
        self.y_mean = float(y.mean())
        self.y_std = max(float(y.std()), 1e-9)
        z = (y - self.y_mean) / self.y_std
        d = X.shape[1]
        bounds = [(np.log(0.05), np.log(10.0))] * d + [(np.log(0.05), np.log(10.0)), (np.log(1e-6), np.log(2.0))]
        starts = np.random.default_rng(0).uniform(0.15, 1.0, (self.restarts, d))
        best = None
        for r in range(self.restarts):
            th0 = np.concatenate([np.log(starts[r]), [0.0, np.log(1e-2)]])
            res = minimize(self._neg_log_marginal, th0, args=(X, z), method="L-BFGS-B", bounds=bounds)
            if best is None or res.fun < best.fun:
                best = res
        self.lengthscales, self.variance, self.noise = self._unpack(best.x, d)
        K = matern52(X, X, self.lengthscales, self.variance) + (self.noise + 1e-8) * np.eye(len(X))
        self._chol = cho_factor(K, lower=True)
        self._alpha = cho_solve(self._chol, z)
        return self

    def predict(self, Xs):
        """Mittelwert und Standardabweichung der **Funktion** (ohne Beobachtungsrauschen)."""
        Ks = matern52(np.asarray(Xs, float), self.X, self.lengthscales, self.variance)
        mu = Ks @ self._alpha
        v = cho_solve(self._chol, Ks.T)
        var = np.maximum(self.variance - (Ks * v.T).sum(1), 1e-12)
        return mu * self.y_std + self.y_mean, np.sqrt(var) * self.y_std


def expected_improvement(mu, sd, best):
    """Erwartete Verbesserung (Minimierung): E[max(best − f, 0)], f ~ N(mu, sd²)."""
    sd = np.maximum(np.asarray(sd, float), 1e-12)
    z = (best - mu) / sd
    return (best - mu) * norm.cdf(z) + sd * norm.pdf(z)


def evaluate_point(evaluate, i, repeats):
    """Mittel aus `repeats` Auswertungen derselben Einstellung; der k-te Wiederholungsindex geht an `evaluate` (für gemeinsame Zufallszahlen)."""
    return float(np.mean([evaluate(i, k) for k in range(repeats)]))


def search(cand, evaluate, evals, rng, repeats=1, n_start=5, method="bo"):
    """Suche mit Budget in **Auswertungen**: es werden evals // repeats verschiedene Einstellungen gewählt und je `repeats`-mal ausgewertet.
    method: 'bo' (EI mit dem besten Mittelwert des Modells an den Beobachtungen als Maßstab) oder 'random'. Gibt (Indizes, Mittelwerte je Einstellung) zurück."""
    n = len(cand)
    points = max(1, evals // repeats)
    start = min(n_start, points)
    if method == "random":
        idx = [int(i) for i in rng.choice(n, size=min(points, n), replace=False)]
        return idx, [evaluate_point(evaluate, i, repeats) for i in idx]
    idx = [int(i) for i in rng.choice(n, size=start, replace=False)]
    y = [evaluate_point(evaluate, i, repeats) for i in idx]
    while len(idx) < points:
        gp = GaussianProcess().fit(cand[idx], y)
        mu, sd = gp.predict(cand)
        ei = expected_improvement(mu, sd, float(np.min(gp.predict(cand[idx])[0])))
        ei[idx] = -np.inf
        i = int(np.argmax(ei))
        idx.append(i)
        y.append(evaluate_point(evaluate, i, repeats))
    return idx, y


def recommend(cand, idx, y, rule="obs"):
    """Empfehlungsregel. 'obs': die Einstellung mit der kleinsten Beobachtung. 'mean': die beobachtete Einstellung mit dem kleinsten Mittelwert des Ersatzmodells."""
    if rule == "obs" or len(idx) < 3:
        return idx[int(np.argmin(y))]
    gp = GaussianProcess().fit(cand[idx], y)
    return idx[int(np.argmin(gp.predict(cand[idx])[0]))]
