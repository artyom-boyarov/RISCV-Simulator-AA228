"""
Belief update + value of information for chip fault diagnosis.

Inputs you supply later:
  L[t, s, o] = P(outcome o | test t, fault state s)   (shape: n_tests x n_states x n_outcomes)
        - Note: outcomes may not be consecutively increasing. Maybe have array to map return values -> outcome index.
        - Test t: kernel.

  cost[t]    = cost of running test t
    - How long test takes to run.
  G[s, g]    = 1 if state s belongs to diagnosis group g (e.g. its component), else 0
               (use np.eye(n_states) to diagnose individual states)
"""
import numpy as np

R_CORRECT = 100.0   # reward for declaring the right diagnosis
P_WRONG = 100.0     # penalty for declaring the wrong one


def update_belief(b, L, t, o):
    """Bayes update after test t gave outcome o:  b'(s) ∝ P(o | s, t) * b(s).
    (Textbook discrete state filter; the fault never changes, so T = identity.)"""
    bp = L[t, :, o] * b
    return bp / bp.sum()


def outcome_probs(b, L, t):
    """P(o | belief, test t) = sum_s b(s) P(o | s, t)."""
    return b @ L[t]


def best_declare_value(b, G):
    """Expected utility of stopping now and declaring the most likely group."""
    p = (b @ G).max()
    return R_CORRECT * p - P_WRONG * (1 - p)


def voi(b, L, t, G):
    """Value of information of test t: E_o[value after seeing o] - value now."""
    value_after = 0.0
    for o, p_o in enumerate(outcome_probs(b, L, t)):
        if p_o > 0:
            value_after += p_o * best_declare_value(update_belief(b, L, t, o), G)
    return value_after - best_declare_value(b, G)


def next_test(b, L, cost, G):
    """Pick the test with the highest VOI - cost. Returns (test index, net value).
    If the net value is <= 0, no test is worth running: stop and declare."""
    net = [voi(b, L, t, G) - cost[t] for t in range(L.shape[0])]
    t = int(np.argmax(net))
    return t, net[t]


def lookahead_value(b, L, cost, G, depth):
    """Depth-limited forward search over (test, outcome) sequences.
    V(b, d) = max( declare now,  max_t [ -cost[t] + sum_o P(o) V(b_o, d-1) ] )
    Returns (value, best test index or None meaning "declare now")."""
    best_value, best_test = best_declare_value(b, G), None
    if depth == 0:
        return best_value, best_test
    for t in range(L.shape[0]):
        value = -cost[t]
        for o, p_o in enumerate(outcome_probs(b, L, t)):
            if p_o > 1e-12:
                value += p_o * lookahead_value(update_belief(b, L, t, o), L, cost, G, depth - 1)[0]
        if value > best_value + 1e-9:
            best_value, best_test = value, t
    return best_value, best_test


def next_test_lookahead(b, L, cost, G, depth=3):
    """Non-myopic version of next_test. Returns a test index, or None to declare now."""
    return lookahead_value(b, L, cost, G, depth)[1]


# ======================================================================
# Running the diagnosis on the real likelihood campaign
#   python VOI_Belief.py [campaign_dir] [--episodes N] [--depth D]
# ======================================================================
import argparse
import time


def load(campaign):
    d = np.load(f"{campaign}/likelihoods.npz", allow_pickle=False)
    L = d["L"]                                   # (tests, states, outcomes)
    cost = d["mean_seconds"].mean(axis=1)        # avg runtime of each test (seconds)
    return L, cost, d["test_names"].tolist(), d["state_names"].tolist()


def indistinguishable_groups(L):
    """States whose likelihoods are identical for every test can never be told apart,
    so diagnose the GROUP. Returns G[s, g] (one column per group)."""
    keys = [L[:, s, :].tobytes() for s in range(L.shape[1])]
    ids = {k: i for i, k in enumerate(dict.fromkeys(keys))}
    G = np.zeros((L.shape[1], len(ids)))
    for s, k in enumerate(keys):
        G[s, ids[k]] = 1
    return G


def diagnose(true_s, L, cost, G, pick_test, rng, max_tests=20, conf=0.9):
    """Run tests until belief in one group >= conf. Returns (correct, n_tests, total_cost)."""
    b = np.ones(L.shape[1]) / L.shape[1]
    n, total = 0, 0.0
    while n < max_tests and (b @ G).max() < conf:
        t = pick_test(b)
        if t is None:
            break
        o = rng.choice(L.shape[2], p=L[t, true_s])   # simulate running the test
        b = update_belief(b, L, t, o)
        n, total = n + 1, total + cost[t]
    return G[true_s, int((b @ G).argmax())] == 1, n, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("campaign", nargs="?", default="likelihood-campaign")
    ap.add_argument("--episodes", type=int, default=100)
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    L, cost, tests, states = load(args.campaign)
    G = indistinguishable_groups(L)
    rng = np.random.default_rng(args.seed)
    T, S = L.shape[0], L.shape[1]
    print(f"{T} tests, {S} states, {G.shape[1]} distinguishable groups")
    print("test costs (s):", dict(zip(tests, cost.round(2))))

    def myopic(b):
        t, net = next_test(b, L, cost, G)
        return t if net > 0 else None            # net <= 0 -> declare

    policies = {
        "random": lambda b: int(rng.integers(T)),
        "myopic VOI": myopic,
        f"forward search d={args.depth}": lambda b: next_test_lookahead(b, L, cost, G, args.depth),
    }
    truth = rng.integers(S, size=args.episodes)  # same true faults for every policy
    for name, pick in policies.items():
        t0 = time.time()
        r = [diagnose(s, L, cost, G, pick, rng) for s in truth]
        print(f"{name:22s} accuracy={np.mean([x[0] for x in r]):.3f}  "
              f"avg tests={np.mean([x[1] for x in r]):.2f}  "
              f"avg cost={np.mean([x[2] for x in r]):.2f}s  ({time.time() - t0:.0f}s to run)")


if __name__ == "__main__":
    main()