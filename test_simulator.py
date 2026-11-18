
"""Local tests for QIS-NET Project 2 Task 1."""

import json
import math

from simulator import run_one_hop, run_two_hop, run_variant_scenario
from policy import make_policy, BaselinePolicy


# Load Group 7 parameters
with open("variant_params.json", "r") as f:
    params = json.load(f)

seed = params["grading"]["seed"]
sim_time_ms = params["grading"]["sim_time_ms"]

expected = params["reference"]["expected"]
tolerances = params["grading"]["tolerances"]


# Test 1: One-hop simulation
print("\n--- Test 1: One-hop ---")

one = run_one_hop(params, sim_time_ms, seed)
print(one)

assert set(one.keys()) == {
    "rate", "mean_fidelity"
}

assert (
    abs(one["rate"] - expected["one_hop_rate"])
    / expected["one_hop_rate"]
    <= tolerances["rate_rel"]
)

print("One-hop test passed.")


# Test 2: Two-hop simulation
print("\n--- Test 2: Two-hop ---")

two = run_two_hop(params, sim_time_ms, seed)
print(two)

assert set(two.keys()) == {
    "rate", "mean_fidelity"
}

assert (
    abs(two["rate"] - expected["two_hop_rate"])
    / expected["two_hop_rate"]
    <= tolerances["rate_rel"]
)

assert (
    abs(two["mean_fidelity"] - expected["two_hop_fidelity"])
    <= tolerances["fid_abs"]
)

print("Two-hop test passed.")


# Test 3: Simulator calibration — the PROVIDED BaselinePolicy must reproduce
# calibration.baseline_policy (this validates the simulator, not our policy)
print("\n--- Test 3: Calibration (BaselinePolicy) ---")

variant = run_variant_scenario(
    params, sim_time_ms, seed, BaselinePolicy(params)
)

print(variant)

assert set(variant.keys()) == {
    "rate",
    "mean_fidelity",
    "p95_latency_ms",
    "pairs_consumed_per_delivery"
}

# Compare with the provided baseline calibration
baseline = params["calibration"]["baseline_policy"]

for key in baseline:
    assert math.isclose(
        variant[key],
        baseline[key],
        abs_tol=0.0001
    ), f"Mismatch in {key}"

print("Calibration test passed.")


# Test 3b: Our policy (make_policy) meets the rate and fidelity SLOs
print("\n--- Test 3b: Variant policy SLOs ---")

ours = run_variant_scenario(params, sim_time_ms, seed, make_policy(params))
print(ours)
slo = params["slo"]
assert ours["rate"] >= slo["min_rate"], "Rate SLO missed"
assert ours["mean_fidelity"] >= slo["min_fidelity"], "Fidelity SLO missed"
print("p95 latency %.2f ms (target <= %.1f): %s" % (
    ours["p95_latency_ms"], slo["max_p95_latency_ms"],
    "met" if ours["p95_latency_ms"] <= slo["max_p95_latency_ms"] else "MISSED"))

print("Variant policy SLO test passed.")


# Test 4: Seeded determinism
print("\n--- Test 4: Determinism ---")

variant_again = run_variant_scenario(
    params, sim_time_ms, seed, make_policy(params)
)

assert ours == variant_again

print("Determinism test passed.")


print("\nAll Task 1 local checks passed.")
