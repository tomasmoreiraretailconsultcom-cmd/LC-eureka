#!/usr/bin/env python
"""
calibrate_sofia_presets.py

Modular Mechanistic Co-Calibration Optimizer for Sofia Machado ODE Fruit Presets.
Divides calibration into distinct, decoupled ODE modules to strictly prevent cross-channel
overfitting and maintain physiological identifiability:

  • Module 1: Firmness / Softening ODE (dD/dt)      -> k_firm_ref, Ea_J, firmness_min, beta_RH
  • Module 2: Brix / Sugar Maturation ODE (db/dt)   -> brix_g, brix_min, brix_max
  • Module 3: Acidity Degradation ODE (dA/dt)       -> k_acidity_ref, Ea_acidity_J, acidity_min
  • Module 4: Chilling Injury ODE (d_chill/dt)      -> safe_temp_C, chill_rate_ref, chill_max_penalty

Anti-Overfitting Safeguards:
  1. Decoupled Calibration: Parameters for an ODE are only calibrated against their corresponding observed metric.
  2. Multi-Temperature Co-Calibration: Fits multiple thermal regimes (e.g. 1°C transport + 25°C shelf) simultaneously.
  3. Biological Noise-Floor Deadband: Prevents optimizer from chasing sub-measurement penetrometer/refractometer noise.
  4. Biophysical Prior Regularization: Penalizes deviation from peer-reviewed plant physiology ranges.
  5. Observability Rule: Unmeasured ODE modules are safely skipped rather than over-parameterized.

Usage:
    # Run all observed modules on Apple Gala:
    python test_scripts/calibrate_sofia_presets.py --fruit apple_gala --dir "tests/Apple - Gala"

    # Run ONLY the Firmness ODE module:
    python test_scripts/calibrate_sofia_presets.py --fruit apple_gala --dir "tests/Apple - Gala" --modules firmness

    # Run Firmness and Brix ODE modules:
    python test_scripts/calibrate_sofia_presets.py --fruit apple_gala --dir "tests/Apple - Gala" --modules firmness brix
"""

import os
import sys
import argparse
import datetime
import copy
import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from LC_model_v0_2_0 import (
    run_simulation_sofia_machado,
    PRESETS_SOFIA,
    STAKEHOLDER_PROFILES,
    PACKAGING_FACTORS
)

# Physiological literature prior defaults and typical standard deviations
PHYSIOLOGICAL_PRIORS = {
    # Module 1: Firmness Softening ODE
    "Ea_J": {"mean": 52000.0, "std": 8000.0, "bounds": (38000.0, 72000.0)},
    "k_firm_ref": {"mean": 0.035, "std": 0.020, "bounds": (0.005, 0.120)},
    "firmness_min": {"mean": 18.0, "std": 8.0, "bounds": (5.0, 38.0)},
    "beta_RH": {"mean": 1.0, "std": 0.5, "bounds": (0.1, 2.5)},
    
    # Module 2: Brix Evolution ODE
    "brix_g": {"mean": 0.20, "std": 0.10, "bounds": (0.05, 0.60)},
    "brix_min": {"mean": 11.5, "std": 2.0, "bounds": (7.0, 15.0)},
    "brix_max": {"mean": 16.0, "std": 2.0, "bounds": (12.0, 22.0)},
    
    # Module 3: Acidity Degradation ODE
    "k_acidity_ref": {"mean": 0.020, "std": 0.015, "bounds": (0.002, 0.080)},
    "Ea_acidity_J": {"mean": 55000.0, "std": 8000.0, "bounds": (35000.0, 75000.0)},
    "acidity_min": {"mean": 0.30, "std": 0.20, "bounds": (0.05, 1.0)},
    
    # Module 4: Cold Injury ODE
    "safe_temp_C": {"mean": 10.0, "std": 4.0, "bounds": (0.0, 15.0)},
    "chill_rate_ref": {"mean": 0.05, "std": 0.03, "bounds": (0.005, 0.25)},
    "chill_max_penalty": {"mean": 0.80, "std": 0.20, "bounds": (0.20, 1.00)}
}

# Module Definitions & Data Channel Bindings
MODULE_DEFINITIONS = {
    "firmness": {
        "label": "Module 1: Firmness / Softening ODE",
        "ode_equation": "d(firmness)/dt = -kT_firm * resp_factor * k_VPD_firm * (firmness - firmness_min)",
        "obs_key": "f_obs",
        "channel_name": "Real_Firmness",
        "unit": "N",
        "default_noise_floor": 3.0,  # ±3.0 N penetrometer margin
        "params": ["k_firm_ref", "Ea_J", "firmness_min", "beta_RH"],
        "nested_key": None
    },
    "brix": {
        "label": "Module 2: Brix / Sugar Evolution ODE",
        "ode_equation": "d(brix)/dt = r_brix_mod * x * (1 - x / K)",
        "obs_key": "b_obs",
        "channel_name": "Real_BRIX",
        "unit": "°Brix",
        "default_noise_floor": 0.5,  # ±0.5 °Brix refractometer margin
        "params": ["brix_g", "brix_min", "brix_max"],
        "nested_key": None
    },
    "acidity": {
        "label": "Module 3: Acidity Degradation ODE",
        "ode_equation": "d(acidity)/dt = -kT_acidity * resp_factor * mat_factor * (acidity - acidity_min)",
        "obs_key": "a_obs",
        "channel_name": "Real_Acidity",
        "unit": "%",
        "default_noise_floor": 0.05,  # ±0.05% titratable acidity margin
        "params": ["k_acidity_ref", "Ea_acidity_J", "acidity_min"],
        "nested_key": None
    },
    "cold_injury": {
        "label": "Module 4: Chilling Injury / Cold Damage ODE",
        "ode_equation": "d(chill)/dt = chill_rate_ref * max(0, safe_temp_C - T)",
        "obs_key": "q_obs",
        "channel_name": "Real_Quality",
        "unit": "%",
        "default_noise_floor": 5.0,  # ±5.0% quality margin
        "params": ["safe_temp_C", "chill_rate_ref", "chill_max_penalty"],
        "nested_key": "cold_injury"
    }
}

def load_test_scenario(excel_path):
    """Loads simulation inputs, ground-truth observations, and metadata from an Excel test file."""
    xls = pd.ExcelFile(excel_path)
    df_readings = pd.read_excel(xls, sheet_name='Simulation_Input')
    
    metadata = {}
    if 'Metadata' in xls.sheet_names:
        df_meta = pd.read_excel(xls, sheet_name='Metadata')
        for _, row in df_meta.iterrows():
            if pd.notnull(row.get('Parameter')):
                metadata[str(row['Parameter'])] = row.get('Value')
                
    fruit_key = str(metadata.get('Fruit_Key', 'apple_gala'))
    owner = str(metadata.get('Current_Owner_Type', 'Retailer (Grocery Store)'))
    
    T_c = df_readings['Temperature_C'].fillna(5.0).astype(float).tolist()
    RH_pct = df_readings['Humidity_Percent'].fillna(90.0).astype(float).tolist()
    days = len(T_c)
    
    pkg_list = df_readings['Packaging'].fillna("Granel (Sem embalagem)").tolist() if 'Packaging' in df_readings.columns else ["Granel (Sem embalagem)"] * days
    
    # Extract discrete observations
    f_obs = {}
    b_obs = {}
    a_obs = {}
    q_obs = {}
    for idx, row in df_readings.iterrows():
        if pd.notnull(row.get('Real_Firmness')):
            f_obs[idx] = float(row['Real_Firmness'])
        if pd.notnull(row.get('Real_BRIX')):
            b_obs[idx] = float(row['Real_BRIX'])
        if pd.notnull(row.get('Real_Acidity')):
            a_obs[idx] = float(row['Real_Acidity'])
        if pd.notnull(row.get('Real_Quality')):
            q_obs[idx] = float(row['Real_Quality'])
            
    # Initial batch values
    f0 = float(metadata.get('Initial_Firmness', f_obs.get(0, 70.0)))
    b0 = float(metadata.get('Initial_Brix', b_obs.get(0, 12.0)))
    a0 = float(metadata.get('Initial_Acidity', a_obs.get(0, 0.4)))
    
    return {
        "file": os.path.basename(excel_path),
        "path": excel_path,
        "fruit_key": fruit_key,
        "owner": owner,
        "T_c": T_c,
        "RH_pct": RH_pct,
        "days": days,
        "pkg_list": pkg_list,
        "f0": f0,
        "b0": b0,
        "a0": a0,
        "f_obs": f_obs,
        "b_obs": b_obs,
        "a_obs": a_obs,
        "q_obs": q_obs
    }

def evaluate_scenario_metric(scenario, preset_candidate, metric_key):
    """Simulates a scenario with preset_candidate and computes residuals for a specific metric."""
    _, _, _, _, arrays_dict = run_simulation_sofia_machado(
        fruit_key=scenario["fruit_key"],
        T_c=scenario["T_c"],
        RH_pct=scenario["RH_pct"],
        days=scenario["days"],
        firmness_0_user=scenario["f0"],
        brix_0_user=scenario["b0"],
        acidity_0_user=scenario["a0"],
        packaging_methods=scenario["pkg_list"],
        custom_preset=preset_candidate,
        current_owner_type=scenario["owner"]
    )
    
    dt = 0.05
    def get_val_at_day(arr, day_idx):
        idx = int(round(day_idx / dt))
        if idx < len(arr):
            return arr[idx]
        return arr[-1]
        
    sim_map = {
        "firmness": np.array(arrays_dict.get("firmness", [])),
        "brix": np.array(arrays_dict.get("brix", [])),
        "acidity": np.array(arrays_dict.get("acidity", [])),
        "cold_injury": np.array(arrays_dict.get("quality", []))
    }
    
    obs_map = {
        "firmness": scenario["f_obs"],
        "brix": scenario["b_obs"],
        "acidity": scenario["a_obs"],
        "cold_injury": scenario["q_obs"]
    }
    
    sim_arr = sim_map.get(metric_key, np.array([]))
    obs_dict = obs_map.get(metric_key, {})
    
    if len(sim_arr) == 0 or len(obs_dict) == 0:
        return {"mae": None, "rmse": None, "residuals": []}
        
    resids = []
    for day_idx, obs_val in obs_dict.items():
        pred_val = get_val_at_day(sim_arr, day_idx)
        resids.append(pred_val - obs_val)
        
    mae = float(np.mean(np.abs(resids))) if resids else None
    rmse = float(np.sqrt(np.mean(np.square(resids)))) if resids else None
    
    return {"mae": mae, "rmse": rmse, "residuals": resids}

def deadband_loss(residuals, noise_floor):
    """
    Computes loss with a deadband threshold:
    If error <= noise_floor, error is considered experimental noise -> loss = 0.
    If error > noise_floor, penalize only the excess beyond the noise floor.
    This strictly prevents overfitting to sub-measurement orchard variations.
    """
    if not residuals:
        return 0.0
    abs_res = np.abs(residuals)
    excess = np.maximum(0.0, abs_res - noise_floor)
    return float(np.mean(excess))

def calibrate_module(
    module_key,
    scenarios,
    current_preset,
    noise_floor=None,
    prior_weight=0.05,
    verbose=True
):
    """
    Calibrates a single decoupled ODE module against its corresponding data channel.
    """
    mod_spec = MODULE_DEFINITIONS[module_key]
    obs_key = mod_spec["obs_key"]
    
    # Check observability
    total_obs = sum(len(sc[obs_key]) for sc in scenarios)
    if total_obs == 0:
        if verbose:
            print(f"\n[{mod_spec['label']}]")
            print(f"  [!] SKIPPED: No observations for '{mod_spec['channel_name']}' in provided test files (Observability Rule).")
        return current_preset, False, None
        
    if noise_floor is None:
        noise_floor = mod_spec["default_noise_floor"]
        
    param_names = mod_spec["params"]
    nested_key = mod_spec["nested_key"]
    
    initial_values = []
    bounds = []
    for p_name in param_names:
        if nested_key and nested_key in current_preset:
            val = current_preset[nested_key].get(p_name, PHYSIOLOGICAL_PRIORS[p_name]["mean"])
        else:
            val = current_preset.get(p_name, PHYSIOLOGICAL_PRIORS[p_name]["mean"])
        initial_values.append(float(val))
        bounds.append(PHYSIOLOGICAL_PRIORS[p_name]["bounds"])
        
    if verbose:
        print(f"\n{'=' * 80}")
        print(f"CALIBRATING: {mod_spec['label'].upper()}")
        print(f"Governing ODE : {mod_spec['ode_equation']}")
        print(f"Target Channel: {mod_spec['channel_name']} (Total {total_obs} observed points)")
        print(f"Noise-Floor Deadband : ±{noise_floor:.2f} {mod_spec['unit']}")
        print(f"Parameters to Tune   : {', '.join(param_names)}")
        print(f"{'-' * 80}")
    
    # Baseline evaluation before this module's calibration
    base_maes = []
    for sc in scenarios:
        ev = evaluate_scenario_metric(sc, current_preset, module_key)
        if ev['mae'] is not None:
            base_maes.append(ev['mae'])
    pre_avg_mae = np.mean(base_maes) if base_maes else 0.0
    if verbose:
        print(f"Pre-Calibration Mean MAE : {pre_avg_mae:.3f} {mod_spec['unit']}")
    
    # Objective function for this specific module
    def module_objective(theta):
        cand = copy.deepcopy(current_preset)
        for name, val in zip(param_names, theta):
            if nested_key:
                if nested_key not in cand:
                    cand[nested_key] = {}
                cand[nested_key][name] = float(val)
            else:
                cand[name] = float(val)
                
        total_loss = 0.0
        active_count = 0
        for sc in scenarios:
            ev = evaluate_scenario_metric(sc, cand, module_key)
            if ev['residuals']:
                loss_val = deadband_loss(ev['residuals'], noise_floor)
                total_loss += loss_val
                active_count += 1
                
        mean_scenario_loss = total_loss / max(1, active_count)
        
        # Prior regularization
        prior_penalty = 0.0
        for name, val in zip(param_names, theta):
            prior_spec = PHYSIOLOGICAL_PRIORS.get(name)
            if prior_spec:
                norm_diff = (val - prior_spec["mean"]) / prior_spec["std"]
                prior_penalty += (norm_diff ** 2)
                
        return mean_scenario_loss + prior_weight * prior_penalty

    # Optimize this module
    opt_res = minimize(
        module_objective,
        x0=np.array(initial_values),
        bounds=bounds,
        method='L-BFGS-B',
        options={'maxiter': 50, 'ftol': 1e-4}
    )
    
    # Apply calibrated values to candidate preset
    updated_preset = copy.deepcopy(current_preset)
    for name, val in zip(param_names, opt_res.x):
        if nested_key:
            if nested_key not in updated_preset:
                updated_preset[nested_key] = {}
            updated_preset[nested_key][name] = float(val)
        else:
            updated_preset[name] = float(val)
            
    # Post-calibration evaluation
    post_maes = []
    if verbose:
        print(f"{'-' * 80}")
        print(f"{'Scenario File':<40} {'Pre MAE':<18} {'Post MAE':<18}")
        print(f"{'-' * 80}")
    for sc in scenarios:
        pre_ev = evaluate_scenario_metric(sc, current_preset, module_key)
        post_ev = evaluate_scenario_metric(sc, updated_preset, module_key)
        if post_ev['mae'] is not None:
            post_maes.append(post_ev['mae'])
            if verbose:
                pre_str = f"{pre_ev['mae']:.3f} {mod_spec['unit']}" if pre_ev['mae'] is not None else "-"
                post_str = f"{post_ev['mae']:.3f} {mod_spec['unit']}"
                print(f"{sc['file']:<40} {pre_str:<18} {post_str:<18}")
            
    post_avg_mae = np.mean(post_maes) if post_maes else 0.0
    if verbose:
        print(f"{'-' * 80}")
        print(f"{'MODULE AVERAGE':<40} {pre_avg_mae:6.3f} {mod_spec['unit']:<10} {post_avg_mae:6.3f} {mod_spec['unit']}")
        print(f"Improvement: {(pre_avg_mae - post_avg_mae):.3f} {mod_spec['unit']} reduction in error.")
        print(f"{'=' * 80}")
        
    stats = {
        "module_label": mod_spec["label"],
        "unit": mod_spec["unit"],
        "pre_mae": pre_avg_mae,
        "post_mae": post_avg_mae,
        "delta": pre_avg_mae - post_avg_mae,
        "param_shifts": {
            name: {
                "before": float(current_preset[nested_key][name]) if nested_key and nested_key in current_preset and name in current_preset[nested_key] else float(current_preset.get(name, 0.0)),
                "after": float(updated_preset[nested_key][name]) if nested_key and nested_key in updated_preset and name in updated_preset[nested_key] else float(updated_preset.get(name, 0.0))
            }
            for name in param_names
        }
    }
    
    return updated_preset, True, stats

def format_preset_dict(fruit_key, calibrated_preset, base_preset, all_calibrated_params):
    """Formats the entire calibrated preset dictionary as clean, valid Python code with comments."""
    lines = [f'PRESETS_SOFIA["{fruit_key}"] = {{']
    for k, v in calibrated_preset.items():
        if k in all_calibrated_params:
            lines.append(f'    "{k}": {v:.4f},  # <-- Calibrated (was {base_preset.get(k)})')
        elif isinstance(v, dict):
            lines.append(f'    "{k}": {{')
            for sub_k, sub_v in v.items():
                if isinstance(sub_v, dict):
                    inner_items = ", ".join([f'"{ik}": {iv}' for ik, iv in sub_v.items()])
                    lines.append(f'        "{sub_k}": {{{inner_items}}},')
                elif sub_k in all_calibrated_params:
                    old_v = base_preset.get(k, {}).get(sub_k)
                    lines.append(f'        "{sub_k}": {sub_v:.4f},  # <-- Calibrated (was {old_v})')
                else:
                    lines.append(f'        "{sub_k}": {repr(sub_v)},')
            lines.append('    },')
        elif isinstance(v, list):
            lines.append(f'    "{k}": {repr(v)},')
        else:
            lines.append(f'    "{k}": {repr(v)},')
    lines.append('}')
    return "\n".join(lines)

def calibrate_fruit(
    fruit_key,
    excel_paths=None,
    modules=None,
    noise_floor_f=None,
    noise_floor_b=None,
    noise_floor_a=None,
    prior_weight=0.05,
    verbose=True
):
    """
    Programmatic entrypoint to co-calibrate all or specified ODE modules for a fruit.
    Returns a structured dictionary of calibrated parameters, preset, and error improvements.
    """
    if modules is None or "all" in modules:
        modules_to_run = ["firmness", "brix", "acidity", "cold_injury"]
    else:
        modules_to_run = modules
        
    if excel_paths is None:
        excel_paths = []
        default_dir = os.path.join(ROOT_DIR, "tests")
        for root, _, files in os.walk(default_dir):
            for f in sorted(files):
                if f.endswith('.xlsx') and not f.startswith('~$') and fruit_key.lower() in (f.lower() + root.lower()):
                    excel_paths.append(os.path.join(root, f))
                    
    if not excel_paths:
        if verbose:
            print(f"Error: No Excel test files found for fruit '{fruit_key}'.")
        return None
        
    scenarios = [load_test_scenario(p) for p in excel_paths]
    
    if fruit_key not in PRESETS_SOFIA:
        if verbose:
            print(f"Error: Unknown fruit key '{fruit_key}' in PRESETS_SOFIA.")
        return None
        
    base_preset = copy.deepcopy(PRESETS_SOFIA[fruit_key])
    current_preset = copy.deepcopy(base_preset)
    
    if verbose:
        print("=" * 80)
        print(f"MODULAR MECHANISTIC CALIBRATION SUITE: {fruit_key.upper()}")
        print("=" * 80)
        print(f"Scenarios loaded: {len(scenarios)} files")
        for sc in scenarios:
            print(f"  • {sc['file']:<35} (Days: {sc['days']:3d}, F_pts: {len(sc['f_obs'])}, B_pts: {len(sc['b_obs'])}, A_pts: {len(sc['a_obs'])}, Q_pts: {len(sc['q_obs'])})")
        print(f"Modules selected for sequential calibration: {', '.join(modules_to_run)}")
        
    noise_floor_map = {
        "firmness": noise_floor_f,
        "brix": noise_floor_b,
        "acidity": noise_floor_a,
        "cold_injury": None
    }
    
    all_calibrated_params = []
    module_improvements = {}
    
    for mod_name in modules_to_run:
        updated_preset, was_calibrated, stats = calibrate_module(
            module_key=mod_name,
            scenarios=scenarios,
            current_preset=current_preset,
            noise_floor=noise_floor_map.get(mod_name),
            prior_weight=prior_weight,
            verbose=verbose
        )
        if was_calibrated:
            current_preset = updated_preset
            all_calibrated_params.extend(MODULE_DEFINITIONS[mod_name]["params"])
            if stats:
                module_improvements[mod_name] = stats
                
    dict_str = format_preset_dict(fruit_key, current_preset, base_preset, all_calibrated_params)
    
    if verbose:
        print("\n" + "=" * 80)
        print("FINAL MODULAR CALIBRATED PRESET DICTIONARY:")
        print("=" * 80)
        print(dict_str)
        print("=" * 80)
        
    return {
        "fruit_key": fruit_key,
        "calibrated_params": all_calibrated_params,
        "calibrated_preset": current_preset,
        "base_preset": base_preset,
        "module_improvements": module_improvements,
        "dict_str": dict_str
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Modular Mechanistic Co-Calibration Optimizer for Sofia Machado ODE Fruit Model")
    parser.add_argument("--fruit", type=str, required=True, help="Fruit key (e.g. apple_gala, apple_golden, kiwi_hayward)")
    parser.add_argument("--files", nargs="*", default=None, help="List of Excel test file paths")
    parser.add_argument("--dir", type=str, default=None, help="Directory containing test Excel files for this fruit")
    parser.add_argument("--modules", nargs="*", default=["all"], 
                        choices=["all", "firmness", "brix", "acidity", "cold_injury"],
                        help="Specific ODE module(s) to calibrate (default: all)")
    parser.add_argument("--noise-floor-f", type=float, default=None, help="Custom firmness noise floor deadband (default: 3.0 N)")
    parser.add_argument("--noise-floor-b", type=float, default=None, help="Custom Brix noise floor deadband (default: 0.5 °Brix)")
    parser.add_argument("--noise-floor-a", type=float, default=None, help="Custom acidity noise floor deadband (default: 0.05 %%)")
    parser.add_argument("--prior-weight", type=float, default=0.05, help="Weight of literature prior regularization penalty")
    args = parser.parse_args()

    excel_paths = []
    if args.files:
        excel_paths.extend(args.files)
    elif args.dir:
        for root, _, files in os.walk(args.dir):
            for f in sorted(files):
                if f.endswith('.xlsx') and not f.startswith('~$'):
                    excel_paths.append(os.path.join(root, f))
    else:
        default_dir = os.path.join(ROOT_DIR, "tests")
        for root, _, files in os.walk(default_dir):
            for f in sorted(files):
                if f.endswith('.xlsx') and not f.startswith('~$') and args.fruit.lower() in (f.lower() + root.lower()):
                    excel_paths.append(os.path.join(root, f))
                    
    calibrate_fruit(
        fruit_key=args.fruit,
        excel_paths=excel_paths,
        modules=args.modules,
        noise_floor_f=args.noise_floor_f,
        noise_floor_b=args.noise_floor_b,
        noise_floor_a=args.noise_floor_a,
        prior_weight=args.prior_weight,
        verbose=True
    )
