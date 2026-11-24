"""
Belief update + value of information for chip fault diagnosis.

Inputs you supply later:
  L[t, s, o] = P(outcome o | test t, fault state s)   (shape: n_tests x n_states x n_outcomes)
  cost[t]    = cost of running test t
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
