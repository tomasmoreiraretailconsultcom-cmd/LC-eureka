#!/usr/bin/env python
"""
calibration_common.py

Shared utilities, scenario loaders, biophysical literature priors,
deadband loss functions, and model file updating routines for the
modular ODE calibration suite.
"""

import os
import sys
import copy
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from LC_model_v0_2_0 import (
    run_simulation_sofia_machado,
    PRESETS_SOFIA,
    STAKEHOLDER_PROFILES,
    PACKAGING_FACTORS
)

# Physiological literature prior defaults and typical standard deviations
PHYSIOLOGICAL_PRIORS = {
    # Firmness Softening ODE
    "Ea_J": {"mean": 52000.0, "std": 8000.0, "bounds": (38000.0, 72000.0)},
    "k_firm_ref": {"mean": 0.035, "std": 0.020, "bounds": (0.005, 0.120)},
    "firmness_min": {"mean": 18.0, "std": 8.0, "bounds": (5.0, 38.0)},
    "beta_RH": {"mean": 1.0, "std": 0.5, "bounds": (0.1, 2.5)},
    
    # Brix Evolution ODE
    "brix_g": {"mean": 0.20, "std": 0.10, "bounds": (0.05, 0.60)},
    "brix_min": {"mean": 11.5, "std": 2.0, "bounds": (7.0, 15.0)},
    "brix_max": {"mean": 16.0, "std": 2.0, "bounds": (12.0, 22.0)},
    
    # Acidity Degradation ODE
    "k_acidity_ref": {"mean": 0.020, "std": 0.015, "bounds": (0.002, 0.080)},
    "Ea_acidity_J": {"mean": 55000.0, "std": 8000.0, "bounds": (35000.0, 75000.0)},
    "acidity_min": {"mean": 0.30, "std": 0.20, "bounds": (0.05, 1.0)},
    
    # Cold Injury ODE
    "safe_temp_C": {"mean": 10.0, "std": 4.0, "bounds": (0.0, 15.0)},
    "chill_rate_ref": {"mean": 0.05, "std": 0.03, "bounds": (0.005, 0.25)},
    "chill_max_penalty": {"mean": 0.80, "std": 0.20, "bounds": (0.20, 1.00)}
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
    f_obs, b_obs, a_obs, q_obs = {}, {}, {}, {}
    for idx, row in df_readings.iterrows():
        if pd.notnull(row.get('Real_Firmness')):
            f_obs[idx] = float(row['Real_Firmness'])
        if pd.notnull(row.get('Real_BRIX')):
            b_obs[idx] = float(row['Real_BRIX'])
        if pd.notnull(row.get('Real_Acidity')):
            a_obs[idx] = float(row['Real_Acidity'])
        if pd.notnull(row.get('Real_Quality')):
            q_obs[idx] = float(row['Real_Quality'])
            
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

def find_excel_files(fruit_key, files=None, directory=None):
    """Discovers Excel test files from CLI arguments or standard folders."""
    excel_paths = []
    if files:
        excel_paths.extend(files)
    elif directory:
        for root, _, fs in os.walk(directory):
            for f in sorted(fs):
                if f.endswith('.xlsx') and not f.startswith('~$'):
                    excel_paths.append(os.path.join(root, f))
    else:
        default_dir = os.path.join(ROOT_DIR, "tests")
        for root, _, fs in os.walk(default_dir):
            for f in sorted(fs):
                if f.endswith('.xlsx') and not f.startswith('~$') and fruit_key.lower() in (f.lower() + root.lower()):
                    excel_paths.append(os.path.join(root, f))
    return excel_paths

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
    Computes deadband loss:
    If error <= noise_floor, error is considered measurement noise -> loss = 0.
    If error > noise_floor, penalize only the excess beyond the noise floor.
    """
    if not residuals:
        return 0.0
    abs_res = np.abs(residuals)
    excess = np.maximum(0.0, abs_res - noise_floor)
    return float(np.mean(excess))

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
