#!/usr/bin/env python
"""
calibrate_brix_ode.py

Standalone Mechanistic Calibrator for the Brix / Sugar Evolution ODE:
    d(brix)/dt = r_brix_mod * x * (1 - x / K)

Calibrates:
    • brix_g   : Base logistic sugar maturation speed (1/day)
    • brix_min : Lower physiological limit of soluble solids (°Brix)
    • brix_max : Upper saturation plateau of soluble solids (°Brix)

Usage:
    python test_scripts/calibrate_brix_ode.py --fruit apple_gala --dir "tests/Apple - Gala"
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

PARAM_NAMES = ["brix_g", "brix_min", "brix_max"]
DEFAULT_NOISE_FLOOR = 0.5  # ±0.5 °Brix refractometer margin

def run_brix_calibration(fruit_key, scenarios, noise_floor=DEFAULT_NOISE_FLOOR, prior_weight=0.05):
    base_preset = copy.deepcopy(PRESETS_SOFIA[fruit_key])
    
    total_obs = sum(len(sc["b_obs"]) for sc in scenarios)
    if total_obs == 0:
        print(f"Error: No 'Real_BRIX' observations found in the {len(scenarios)} provided test files.")
        sys.exit(1)
        
    initial_values = [float(base_preset.get(p, PHYSIOLOGICAL_PRIORS[p]["mean"])) for p in PARAM_NAMES]
    bounds = [PHYSIOLOGICAL_PRIORS[p]["bounds"] for p in PARAM_NAMES]
    
    print("=" * 80)
    print(f"STANDALONE CALIBRATION: BRIX / SUGAR EVOLUTION ODE ({fruit_key.upper()})")
    print("ODE : d(brix)/dt = r_brix_mod * x * (1 - x / K)")
    print(f"Target Channel : Real_BRIX ({total_obs} observed data points across {len(scenarios)} files)")
    print(f"Noise Floor    : ±{noise_floor:.2f} °Brix (Refractometer deadband)")
    print(f"Parameters     : {', '.join(PARAM_NAMES)}")
    print("=" * 80)
    
    base_maes = [evaluate_scenario_metric(sc, base_preset, "brix")["mae"] for sc in scenarios]
    base_maes = [m for m in base_maes if m is not None]
    pre_avg = np.mean(base_maes) if base_maes else 0.0
    print(f"Pre-Calibration Mean Brix MAE: {pre_avg:.3f} °Brix\n")
    
    def objective(theta):
        cand = copy.deepcopy(base_preset)
        for name, val in zip(PARAM_NAMES, theta):
            cand[name] = float(val)
            
        total_loss = 0.0
        active_count = 0
        for sc in scenarios:
            ev = evaluate_scenario_metric(sc, cand, "brix")
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
    for name, val in zip(PARAM_NAMES, opt_res.x):
        calibrated_preset[name] = float(val)
        
    post_maes = []
    print(f"{'-' * 80}")
    print(f"{'Scenario File':<40} {'Pre MAE':<18} {'Post MAE':<18}")
    print(f"{'-' * 80}")
    for sc in scenarios:
        pre_ev = evaluate_scenario_metric(sc, base_preset, "brix")
        post_ev = evaluate_scenario_metric(sc, calibrated_preset, "brix")
        if post_ev["mae"] is not None:
            post_maes.append(post_ev["mae"])
            pre_str = f"{pre_ev['mae']:.3f} °Brix" if pre_ev["mae"] is not None else "-"
            post_str = f"{post_ev['mae']:.3f} °Brix"
            print(f"{sc['file']:<40} {pre_str:<18} {post_str:<18}")
            
    post_avg = np.mean(post_maes) if post_maes else 0.0
    print(f"{'-' * 80}")
    print(f"{'OVERALL AVERAGE':<40} {pre_avg:6.3f} °Brix    {post_avg:6.3f} °Brix")
    print(f"Improvement: {(pre_avg - post_avg):.3f} °Brix reduction in MAE.")
    print("=" * 80)
    
    print("\nCALIBRATED PRESET VALUES:")
    print(format_preset_dict(fruit_key, calibrated_preset, base_preset, PARAM_NAMES))
    print("=" * 80)
    
    return calibrated_preset

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Standalone Brix / Sugar Evolution ODE Calibrator")
    parser.add_argument("--fruit", type=str, required=True, help="Fruit key (e.g. apple_gala, apple_golden)")
    parser.add_argument("--files", nargs="*", default=None, help="List of Excel test file paths")
    parser.add_argument("--dir", type=str, default=None, help="Directory containing test Excel files for this fruit")
    parser.add_argument("--noise-floor", type=float, default=DEFAULT_NOISE_FLOOR, help=f"Brix noise floor deadband (default: {DEFAULT_NOISE_FLOOR} °Brix)")
    parser.add_argument("--prior-weight", type=float, default=0.05, help="Weight of literature prior regularization penalty")
    args = parser.parse_args()
    
    paths = find_excel_files(args.fruit, args.files, args.dir)
    if not paths:
        print(f"Error: No Excel test files found for fruit '{args.fruit}'. Specify --files or --dir.")
        sys.exit(1)
        
    scenarios = [load_test_scenario(p) for p in paths]
    calibrated = run_brix_calibration(args.fruit, scenarios, args.noise_floor, args.prior_weight)
