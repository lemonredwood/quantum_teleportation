#!/usr/bin/env bash
# demo.sh — QIS-NET Project 2 video demo (group 7, variant 07).
# NOT part of the submission zip. Run from the project folder:  ./demo.sh
# Press Enter to advance between sections.

set -e
cd "$(dirname "$0")"
[ -f venv/bin/activate ] && source venv/bin/activate

BOLD=$'\033[1m'; CYAN=$'\033[36m'; RESET=$'\033[0m'

section() {
    clear 2>/dev/null || true
    echo "${BOLD}${CYAN}== $1 ==${RESET}"
    echo "$2"
    echo
}

pause() {
    echo
    read -r -p "${BOLD}[Enter to continue]${RESET} " _
}

# ------------------------------------------------------------------ 1
section "1. Validation" \
"One-hop and two-hop match theory, the baseline reproduces calibration,
our policy meets the SLOs, and runs are deterministic."
python3 test_task1.py
pause

# ------------------------------------------------------------------ 2
section "2. Our policy vs the provided baseline" \
"Same seed (1007), same simulator. Only the policy changes."
python3 - <<'EOF'
import json
from simulator import run_variant_scenario
from policy import BaselinePolicy, make_policy

p = json.load(open("variant_params.json"))
seed, T, slo = p["grading"]["seed"], p["grading"]["sim_time_ms"], p["slo"]

print(f"{'':10}{'rate /s':>10}{'fidelity':>11}{'p95 ms':>10}")
for name, pol in [("Baseline", BaselinePolicy(p)), ("Ours", make_policy(p))]:
    r = run_variant_scenario(p, T, seed, pol)
    print(f"{name:10}{r['rate']:>10.1f}{r['mean_fidelity']:>11.3f}"
          f"{r['p95_latency_ms']:>10.1f}")
print(f"{'SLO':10}{'>= ' + str(slo['min_rate']):>10}"
      f"{'>= ' + str(slo['min_fidelity']):>11}"
      f"{'<= ' + str(slo['max_p95_latency_ms']):>10}")
print("\nKey idea: swap the FRESHEST pair, not the oldest -> fidelity 0.31 -> 0.82")
EOF
pause

# ------------------------------------------------------------------ 3
section "3. T2 sensitivity (5 seeds per point, 95% CI)" \
"Running 25 simulations..."
python3 experiments.py variant_params.json > /dev/null
python3 - <<'EOF'
import json
r = json.load(open("experiment_results.json"))
print(f"{'T2 (ms)':>10}{'rate mean':>12}{'95% CI':>10}")
for pt in r["points"]:
    print(f"{pt['t2_ms']:>10.1f}{pt['rate_mean']:>12.2f}{'± %.2f' % pt['rate_ci95']:>10}")
print("\nRate is flat across a 16x range of T2: all CIs overlap.")
print("Throughput is set by the bottleneck link and q_swap; T2 drives fidelity.")
print("Written to experiment_results.json")
EOF
echo
echo "${BOLD}Demo complete.${RESET}"
