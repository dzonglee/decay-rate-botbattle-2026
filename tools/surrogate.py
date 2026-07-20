#!/usr/bin/env python3
"""SURROGATE-ASSISTED PRE-SELECTION (deliverable 3, Chris's build order 2026-07-10).

The pragmatic ML nudge, per the surrogate-assisted evolutionary computation
literature (Jin 2005/2011 surveys; "pre-selection" strategy): learn a cheap
fitness predictor from (genome -> measured mean_mass) pairs the league already
produces for free every generation, then OVERSAMPLE offspring and simulate only
the most promising fraction. Sims are ~10^6x the cost of the predictor, so even
a weakly-correlated surrogate buys generations.

Design choices (deliberately boring & robust):
  - Ridge regression on standardized gene vectors, pure stdlib (no numpy/sklearn):
    genome dims ~97, ring buffer of the last N=600 evaluations, refit per gen
    (closed-form via Gauss-Jordan on the 97x97 normal matrix — milliseconds).
  - log1p-transform on the target (mass is heavy-tailed).
  - Trust guard: each refit reports leave-out-last-gen Spearman rho; if rho < 0.2
    the caller should fall back to random selection (surrogate has no signal yet
    or the landscape moved — e.g., after a room change or fitness void).
  - NEVER replaces real evaluation: only chooses WHICH children get born.
    Selection/promotion still runs on simulated fitness only (laws intact).

API:
    s = Surrogate(keys)                  # gene-name order
    s.observe(genome, fitness)           # call for every league evaluation
    s.fit()                              # refit; returns rho (trust signal)
    s.rank(candidates)                   # -> candidates sorted best-first

Integration sketch for evolve_v2.py (NOT applied — see README_BUILD.md):
    children = []
    while len(children) < need:
        pool = [mutate(crossover(*random.sample(elites,2)), sigma, prob)
                for _ in range(OVERSAMPLE * batch)]         # e.g. OVERSAMPLE=4
        pool = SURR.rank(pool) if SURR.trust >= 0.2 else pool
        children.extend(pool[:batch])
"""
import math, random

class Surrogate:
    def __init__(self, keys, capacity=600, ridge=1.0):
        self.keys = list(keys)
        self.cap = capacity
        self.lam = ridge
        self.X, self.y = [], []
        self.w = None
        self.mu = self.sd = None
        self.trust = 0.0

    def _vec(self, genome):
        return [float(genome.get(k, 0.0)) for k in self.keys]

    def observe(self, genome, fitness):
        self.X.append(self._vec(genome))
        self.y.append(math.log1p(max(fitness, 0.0)))
        if len(self.X) > self.cap:
            self.X.pop(0); self.y.pop(0)

    def _standardize(self, X):
        n, d = len(X), len(self.keys)
        self.mu = [sum(r[j] for r in X) / n for j in range(d)]
        self.sd = [max(1e-9, math.sqrt(sum((r[j] - self.mu[j]) ** 2 for r in X) / n)) for j in range(d)]
        return [[(r[j] - self.mu[j]) / self.sd[j] for j in range(d)] for r in X]

    def fit(self):
        n = len(self.X)
        if n < 40:
            self.trust = 0.0
            return 0.0
        # holdout = most recent 20% for the trust signal
        cut = max(1, n // 5)
        Xtr, ytr = self.X[:-cut], self.y[:-cut]
        Z = self._standardize(Xtr)
        d = len(self.keys)
        # normal equations A w = b with ridge
        A = [[self.lam if i == j else 0.0 for j in range(d + 1)] for i in range(d + 1)]
        b = [0.0] * (d + 1)
        for r, t in zip(Z, ytr):
            row = r + [1.0]
            for i in range(d + 1):
                b[i] += row[i] * t
                for j in range(i, d + 1):
                    A[i][j] += row[i] * row[j]
        for i in range(d + 1):
            for j in range(i):
                A[i][j] = A[j][i]
        self.w = _solve(A, b)
        # trust: rank correlation on the holdout
        preds = [self._predict_vec(v) for v in self.X[-cut:]]
        self.trust = _spearman(preds, self.y[-cut:]) if cut >= 5 else 0.0
        return self.trust

    def _predict_vec(self, v):
        if self.w is None:
            return 0.0
        z = [(v[j] - self.mu[j]) / self.sd[j] for j in range(len(self.keys))]
        return sum(w * x for w, x in zip(self.w[:-1], z)) + self.w[-1]

    def predict(self, genome):
        return self._predict_vec(self._vec(genome))

    def rank(self, candidates):
        return sorted(candidates, key=lambda g: -self.predict(g))

def _solve(A, b):
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        piv = M[c][c] or 1e-12
        M[c] = [x / piv for x in M[c]]
        for r in range(n):
            if r != c and M[r][c]:
                f = M[r][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [M[i][n] for i in range(n)]

def _spearman(a, b):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0.0] * len(v)
        for pos, i in enumerate(order):
            rk[i] = pos
        return rk
    ra, rb = ranks(a), ranks(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) or 1e-12
    return num / den

if __name__ == "__main__":
    # self-test on a synthetic quadratic landscape
    random.seed(1)
    keys = [f"g{i}" for i in range(30)]
    def true_fit(g): return 50 - sum((g[k] - 0.3 * i) ** 2 for i, k in enumerate(keys[:5])) + random.gauss(0, 2)
    s = Surrogate(keys)
    for _ in range(300):
        g = {k: random.uniform(-2, 2) for k in keys}
        s.observe(g, max(0, true_fit(g)))
    rho = s.fit()
    pool = [{k: random.uniform(-2, 2) for k in keys} for _ in range(100)]
    ranked = s.rank(pool)
    top = sum(true_fit(g) for g in ranked[:10]) / 10
    rnd = sum(true_fit(g) for g in pool[:10]) / 10
    print(f"self-test: trust rho={rho:.2f}  surrogate-top10 fitness={top:.1f} vs random10={rnd:.1f}")
