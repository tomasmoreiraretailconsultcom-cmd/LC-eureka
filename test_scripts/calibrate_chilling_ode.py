#!/usr/bin/env python
"""
calibrate_chilling_ode.py

Standalone Mechanistic Calibrator for the Cold Damage / Chilling Injury ODE:
    d(chill)/dt = chill_rate_ref * max(0, safe_temp_C - T)

Calibrates:
    • safe_temp_C       : Minimum safe storage temperature threshold (°C)
    • chill_rate_ref    : Rate of irreversible chilling injury accumulation (1/day)
    • chill_max_penalty : Maximum commercial quality loss penalty fraction (0..1)

Usage:
    python test_scripts/calibrate_chilling_ode.py --fruit banana --dir "tests/Banana"
"""

import sys
import copy
import argparse
import numpy as np
from scipy.optimize import minimize

from calibration_common import (
    PRESETS_SOFIA,
    PHYSIOLOGICAL_PRIORS,
    load_test_scenario,
    find_excel_files,
    evaluate_scenario_metric,
    deadband_loss,
    format_preset_dict
)

PARAM_NAMES = ["safe_temp_C", "chill_rate_ref", "chill_max_penalty"]
DEFAULT_NOISE_FLOOR = 5.0  # ±5.0% quality margin

def run_chilling_calibration(fruit_key, scenarios, noise_floor=DEFAULT_NOISE_FLOOR, prior_weight=0.05):
    base_preset = copy.deepcopy(PRESETS_SOFIA[fruit_key])
    
    total_obs = sum(len(sc["q_obs"]) for sc in scenarios)
    if total_obs == 0:
        print(f"Error: No 'Real_Quality' chilling injury observations found in the {len(scenarios)} provided test files.")
        sys.exit(1)
        
    ci_base = base_preset.get("cold_injury", {})
    initial_values = [float(ci_base.get(p, PHYSIOLOGICAL_PRIORS[p]["mean"])) for p in PARAM_NAMES]
    bounds = [PHYSIOLOGICAL_PRIORS[p]["bounds"] for p in PARAM_NAMES]
    
    print("=" * 80)
    print(f"STANDALONE CALIBRATION: CHILLING INJURY ODE ({fruit_key.upper()})")
    print("ODE : d(chill)/dt = chill_rate_ref * max(0, safe_temp_C - T)")
    print(f"Target Channel : Real_Quality ({total_obs} observed data points across {len(scenarios)} files)")
    print(f"Noise Floor    : ±{noise_floor:.1f} % (Quality deadband)")
    print(f"Parameters     : {', '.join(PARAM_NAMES)}")
    print("=" * 80)
    
    base_maes = [evaluate_scenario_metric(sc, base_preset, "cold_injury")["mae"] for sc in scenarios]
    base_maes = [m for m in base_maes if m is not None]
    pre_avg = np.mean(base_maes) if base_maes else 0.0
    print(f"Pre-Calibration Mean Quality MAE: {pre_avg:.2f} %\n")
    
    def objective(theta):
        cand = copy.deepcopy(base_preset)
        if "cold_injury" not in cand:
            cand["cold_injury"] = {}
        for name, val in zip(PARAM_NAMES, theta):
            cand["cold_injury"][name] = float(val)
            
        total_loss = 0.0
        active_count = 0
        for sc in scenarios:
            ev = evaluate_scenario_metric(sc, cand, "cold_injury")
            if ev["residuals"]:
                total_loss += deadband_loss(ev["residuals"], noise_floor)
                active_count += 1
                
        mean_loss = total_loss / max(1, active_count)
        
        prior_penalty = sum(
            ((val - PHYSIOLOGICAL_PRIORS[name]["mean"]) / PHYSIOLOGICAL_PRIORS[name]["std"]) ** 2
            for name, val in zip(PARAM_NAMES, theta)
        )
        return mean_loss + prior_weight * prior_penalty

    opt_res = minimize(
        objective,
        x0=np.array(initial_values),
        bounds=bounds,
        method="L-BFGS-B",
        options={"maxiter": 200, "ftol": 1e-5}
    )
    
    calibrated_preset = copy.deepcopy(base_preset)
    if "cold_injury" not in calibrated_preset:
        calibrated_preset["cold_injury"] = {}
    for name, val in zip(PARAM_NAMES, opt_res.x):
        calibrated_preset["cold_injury"][name] = float(val)
        
    post_maes = []
    print(f"{'-' * 80}")
    print(f"{'Scenario File':<40} {'Pre MAE':<18} {'Post MAE':<18}")
    print(f"{'-' * 80}")
    for sc in scenarios:
        pre_ev = evaluate_scenario_metric(sc, base_preset, "cold_injury")
        post_ev = evaluate_scenario_metric(sc, calibrated_preset, "cold_injury")
        if post_ev["mae"] is not None:
            post_maes.append(post_ev["mae"])
            pre_str = f"{pre_ev['mae']:.2f} %" if pre_ev["mae"] is not None else "-"
            post_str = f"{post_ev['mae']:.2f} %"
            print(f"{sc['file']:<40} {pre_str:<18} {post_str:<18}")
            
    post_avg = np.mean(post_maes) if post_maes else 0.0
    print(f"{'-' * 80}")
    print(f"{'OVERALL AVERAGE':<40} {pre_avg:6.2f} %        {post_avg:6.2f} %")
    print(f"Improvement: {(pre_avg - post_avg):.2f} % reduction in MAE.")
    print("=" * 80)
    
    print("\nCALIBRATED PRESET VALUES:")
    print(format_preset_dict(fruit_key, calibrated_preset, base_preset, PARAM_NAMES))
    print("=" * 80)
    
    return calibrated_preset

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Standalone Chilling Injury / Cold Damage ODE Calibrator")
    parser.add_argument("--fruit", type=str, required=True, help="Fruit key (e.g. banana, orange)")
    parser.add_argument("--files", nargs="*", default=None, help="List of Excel test file paths")
    parser.add_argument("--dir", type=str, default=None, help="Directory containing test Excel files for this fruit")
    parser.add_argument("--noise-floor", type=float, default=DEFAULT_NOISE_FLOOR, help=f"Quality noise floor deadband (default: {DEFAULT_NOISE_FLOOR} %%)")
    parser.add_argument("--prior-weight", type=float, default=0.05, help="Weight of literature prior regularization penalty")
    args = parser.parse_args()
    
    paths = find_excel_files(args.fruit, args.files, args.dir)
    if not paths:
        print(f"Error: No Excel test files found for fruit '{args.fruit}'. Specify --files or --dir.")
        sys.exit(1)
        
    scenarios = [load_test_scenario(p) for p in paths]
    calibrated = run_chilling_calibration(args.fruit, scenarios, args.noise_floor, args.prior_weight)
