"""
simulator.py — QIS-NET Project 2 runner (group 7, variant 07).

Drive the provided harness (qnetsim.py) to implement the three graded
entry points. Signatures are normative; the autograder imports them.

Only numpy + standard library + qnetsim may be used.
"""

import math

import numpy as np

from qnetsim import Link, Simulator, DeliveredPair, summarise


# ---------------------------------------------------------------- helpers


def make_links(params, which="variant"):
    """Build Link objects from the variant parameter dict.

    `which="one_hop"` / `"two_hop"` select the reference scenarios defined in
    params["reference"]; `which="variant"` builds the full variant topology.
    PROVIDED — you should not need to change this.
    """
    links = []
    if which == "one_hop":
        ref = params["reference"]["one_hop"]
        links.append(Link(link_id=0, nodes=(0, 1),
                          attempt_rate=ref["attempt_rate"],
                          p_success=ref["p_success"],
                          f_link=params["physics"]["f_link"]))
    elif which == "two_hop":
        ref = params["reference"]["two_hop"]
        for i, lp in enumerate(ref["links"]):
            links.append(Link(link_id=i, nodes=(i, i + 1),
                              attempt_rate=lp["attempt_rate"],
                              p_success=lp["p_success"],
                              f_link=params["physics"]["f_link"]))
    else:
        for i, lp in enumerate(params["topology"]["links"]):
            links.append(Link(link_id=i, nodes=tuple(lp["nodes"]),
                              attempt_rate=lp["attempt_rate"],
                              p_success=lp["p_success"],
                              f_link=params["physics"]["f_link"]))
    return links


def request_times(params, sim_time_ms, seed):
    """Deterministic request arrival times (ms) for the variant workload.
    Uses a generator derived from `seed` so runs are reproducible.
    PROVIDED."""
    wl = params["workload"]
    rng = np.random.default_rng(seed + 7919)
    t, times = 0.0, []
    while True:
        t += rng.exponential(1000.0 / wl["arrival_rate_per_s"])
        if t > sim_time_ms:
            break
        times.append(t)
    return times




def run_one_hop(params, sim_time_ms, seed) -> dict:
    """Reference scenario: a single elementary link, no swapping.
    Return {"rate": ..., "mean_fidelity": ...}.

    TODO: build the one-hop links, run the Simulator for sim_time_ms with
    policy=None, and use qnetsim.summarise on a delivered-list you fill
    yourself (every generated pair counts as delivered here — record
    deliveries via a tiny inline policy or by reading state.pairs/stats).

    HINT: the harness only records `delivered` on swap; for the one-hop
    case, write a 3-line policy class whose on_pair_ready appends a
    DeliveredPair-equivalent record (or count pairs via state.stats and
    track fidelities in a list).
    """

    links = make_links(params, "one_hop")

    sim = Simulator(
        links=links,
        t2=math.inf,
        q_swap=1.0,
        f_swap=1.0,
        purification_allowed=False,
        seed=seed
    )

    class OneHopPolicy:
        def on_pair_ready(self, link, pair, state, sim):
            sim.delivered.append(
                DeliveredPair(
                    request_id=-1,
                    delivered_at=state.now,
                    fidelity=state.current_fidelity(pair),
                    consumed=1
                )
            )

    delivered = sim.run(sim_time_ms, policy=OneHopPolicy())
    results = summarise(delivered, sim_time_ms)

    return {
        "rate": results["rate"],
        "mean_fidelity": results["mean_fidelity"]
    }

def run_two_hop(params, sim_time_ms, seed) -> dict:
    """Reference scenario: two links, one repeater, immediate swap,
    T2 = infinity, q_swap = 1 (params['reference']['two_hop']).
    Return {"rate": ..., "mean_fidelity": ...}.

    TODO: build links, construct the Simulator with t2=math.inf,
    q_swap=1.0, f_swap=params['physics']['f_swap']; use a policy that swaps
    as soon as both links hold a pair; summarise with qnetsim.summarise.
    """
    links = make_links(params, "two_hop")

    sim = Simulator(
        links=links,
        t2=math.inf,
        q_swap=1.0,
        f_swap=params["physics"]["f_swap"],
        purification_allowed=False,
        seed=seed
    )

    class ImmediateSwapPolicy:
        def on_pair_ready(self, link, pair, state, sim):
            if state.pairs.get(0) and state.pairs.get(1):
                sim.swap(0, 1)

    delivered = sim.run(sim_time_ms, policy=ImmediateSwapPolicy())
    results = summarise(delivered, sim_time_ms)

    return {
        "rate": results["rate"],
        "mean_fidelity": results["mean_fidelity"]
    }

def run_variant_scenario(params, sim_time_ms, seed, policy) -> dict:
    """Full variant scenario with YOUR policy.
    Return {"rate": ..., "mean_fidelity": ..., "p95_latency_ms": ...,
            "pairs_consumed_per_delivery": ...}.

    TODO:
      * build the variant topology links;
      * construct the Simulator with your variant's physics
        (t2, q_swap, f_swap, purification_allowed, seed);
      * generate request_times(...); use a pooled unlimited end-to-end buffer.
        A request consumes a buffered pair at zero latency, or queues FIFO
        for a later delivery. Exclude unserved requests from p95. Fidelity
        is measured at generation; this buffer does not model further decay;
      * return the four metrics. pairs_consumed_per_delivery =
        stats['generated'] / max(1, delivered).
    """
    
    physics = params["physics"]

    links = make_links(params, "variant")

    sim = Simulator(
        links=links,
        t2=physics["t2_ms"],
        q_swap=physics["q_swap"],
        f_swap=physics["f_swap"],
        purification_allowed=physics["purification_allowed"],
        seed=seed
    )

    sim.run(sim_time_ms, policy=policy)

    deliveries = sorted(
        sim.delivered,
        key=lambda pair: pair.delivered_at
    )

    arrivals = request_times(params, sim_time_ms, seed)

    served = min(len(arrivals), len(deliveries))

    latencies = []

    for i in range(served):
        latency = max(
            0.0,
            deliveries[i].delivered_at - arrivals[i]
        )
        latencies.append(latency)

    latencies.sort()

    if latencies:
        rank = math.ceil(0.95 * len(latencies)) - 1
        p95_latency_ms = latencies[rank]
    else:
        p95_latency_ms = math.inf

    results = summarise(deliveries, sim_time_ms)

    pairs_consumed = (
        sim.state.stats["generated"]
        / max(1, len(deliveries))
    )

    return {
        "rate": results["rate"],
        "mean_fidelity": results["mean_fidelity"],
        "p95_latency_ms": p95_latency_ms,
        "pairs_consumed_per_delivery": pairs_consumed
    }
