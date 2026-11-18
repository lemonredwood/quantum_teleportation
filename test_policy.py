import json
from simulator import run_variant_scenario
from policy import make_policy

params = json.load(open("variant_params.json"))
sim_time = params["grading"]["sim_time_ms"]

for i, l in enumerate(params["topology"]["links"]):
    print("link", i, l["attempt_rate"] * l["p_success"] * 1000, "pairs/s")

print(run_variant_scenario(params, sim_time, 7023, make_policy(params)))
print(params["calibration"]["reference_policy"])