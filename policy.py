"""
policy.py — QIS-NET Project 2 policy (STUDENT FILE: replace the baseline).

The policy decides, each time a fresh pair arrives on a link, what to do:
swap immediately, purify first, hold, or discard aged pairs. Your variant's
SLOs (rate, fidelity, p95 latency) will typically NOT be met by the
baseline policy below.

Design space (see spec section 3.2):
  * purify while the freshest link fidelity is below a threshold AND a
    second pair is available on the same link;
  * hold vs swap rules (e.g., wait for a purified partner);
  * discard pairs whose current fidelity has fallen below a floor.
"""

import math


class FreshestPolicy:
    """Swap-as-soon-as-possible but use the NEWEST pair
    on each link instead of the oldest.

    swap() always selects the oldest pair by default. As measured with test.py, link 1 generates more pairs
    than link 0 can take (about 189 vs 96 pairs/s), so we can expect that its old pairs add up and the fidelity decays.
    However, the baseline policy class just basically swaps those decayed pairs returning fidelity ~ 0.31.

    Taking into account these metrics, we changed the policy so that new pairs are appended at the end of each list,
    so the last position is the freshest pair. Now with test.py, we can see how the fidelity improved to ~ 0.81

    purify() will always take the two oldest pairs and then use the 
    minimum of their fidelities, so with low-fidelity pairs the outcome is poor. Thats why we dont use it in this policy.
    """
    

    def __init__(self, params):
        self.params = params
        # map each repeater node to its adjacent link pairs for swapping
        self.chains = params["policy"]["swap_chains"]  # list of [left, right]

    def on_pair_ready(self, link, pair, state, sim):
        for left, right in self.chains:
            left_pairs = state.pairs.get(left, [])
            right_pairs = state.pairs.get(right, [])
            if len(left_pairs) > 0 and len(right_pairs) > 0:
                sim.swap(left, right,
                         left_index=len(left_pairs) - 1,
                         right_index=len(right_pairs) - 1)

def make_policy(params):
    """Return your policy object. Replace BaselinePolicy with your own class
    (same constructor signature and on_pair_ready hook)."""

    return FreshestPolicy(params)
