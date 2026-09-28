import os
import sys
import argparse
import datetime
import numpy as np
import pandas as pd

# Add workspace root to sys.path so we can import LC_model_v0_2_0
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from LC_model_v0_2_0 import (
    run_simulation_sofia_machado,
    run_simulation_prof_luis_paulo,
    fill_nulls_with_warehouse_sim,
    PRESETS_SOFIA,
    PRESETS_ACADEMIC,
    STAKEHOLDER_PROFILES,
    COLD_INJURY_BY_FRUIT,
    PACKAGING_FACTORS
)

def run_single_test(excel_path):
    xls = pd.ExcelFile(excel_path)
    df_readings = pd.read_excel(xls, sheet_name='Simulation_Input')
    
    metadata = {}
    if 'Metadata' in xls.sheet_names:
        df_meta = pd.read_excel(xls, sheet_name='Metadata')
        for _, row in df_meta.iterrows():
            if pd.notnull(row.get('Parameter')):
                metadata[str(row['Parameter'])] = row.get('Value')
                
    fruit_key = str(metadata.get('Fruit_Key', 'kiwi_hayward'))
    current_owner = str(metadata.get('Current_Owner_Type', 'Retailer (Grocery Store)'))
    
    # Preset fallbacks
    preset = PRESETS_SOFIA.get(fruit_key, PRESETS_ACADEMIC.get(fruit_key, {}))
    
    f0 = float(metadata.get('Initial_Firmness', preset.get('firmness_0_default', 50.0)))
    b0 = float(metadata.get('Initial_Brix', preset.get('brix_0_default', 12.0)))
    a0 = float(metadata.get('Initial_Acidity', preset.get('acidity_0_default', 0.8)))
    
    exp_sl = float(metadata.get('Expected_Remaining_SL_Days', 0.0))
    tol_sl = float(metadata.get('Expected_Remaining_SL_Tolerance', 3.0))
    desc = str(metadata.get('Description', ''))
    doi = str(metadata.get('Reference_DOI', ''))
    
    T_raw = [float(t) if pd.notnull(t) else None for t in df_readings['Temperature_C']]
    RH_raw = [float(h) if pd.notnull(h) else None for h in df_readings['Humidity_Percent']]
    days = len(T_raw)
    
    # Handle sensor telemetry sparsity via regional weather warehouse imputation
    if any(t is None for t in T_raw) or any(h is None for h in RH_raw):
        start_date_str = str(df_readings['Date'].iloc[0]) if 'Date' in df_readings.columns and pd.notnull(df_readings['Date'].iloc[0]) else "2026-09-01"
        try:
            start_dt = datetime.datetime.strptime(start_date_str[:10], "%Y-%m-%d")
        except Exception:
            start_dt = datetime.datetime(2026, 9, 1)
        regions = df_readings['Region'].fillna('PT-LVT').tolist() if 'Region' in df_readings.columns else ['PT-LVT'] * days
        alphas = [0.9] * days
        T_c, RH_pct = fill_nulls_with_warehouse_sim(T_raw, RH_raw, regions, alphas, start_dt)
    else:
        T_c = [float(t) for t in T_raw]
        RH_pct = [float(h) for h in RH_raw]
    
    pkg_list = None
    if 'Packaging' in df_readings.columns:
        pkg_list = [str(p) if pd.notnull(p) else "Granel (Sem embalagem)" for p in df_readings['Packaging']]
        
    has_ethylene = ('Ethylene_ppm' in df_readings.columns and 
                    df_readings['Ethylene_ppm'].notnull().any() and 
                    (df_readings['Ethylene_ppm'] > 0.05).any() and
                    fruit_key in PRESETS_ACADEMIC)
    
    if has_ethylene:
        E_ppm = df_readings['Ethylene_ppm'].fillna(0.0).astype(float).tolist()
        final_q, pred_sl, final_f, final_b, arrays_dict = run_simulation_prof_luis_paulo(
            fruit_key=fruit_key,
            T_c=T_c,
            RH_pct=RH_pct,
            E_ext_ppm=E_ppm,
            days=days,
            firmness_0_user=f0,
            brix_0_user=b0
        )
        final_a = np.nan
        algorithm_used = "ode_academic"
    else:
        final_q, pred_sl, final_f, final_b, arrays_dict = run_simulation_sofia_machado(
            fruit_key=fruit_key,
            T_c=T_c,
            RH_pct=RH_pct,
            days=days,
            firmness_0_user=f0,
            brix_0_user=b0,
            acidity_0_user=a0,
            packaging_methods=pkg_list,
            current_owner_type=current_owner
        )
        final_a = arrays_dict["acidity"][-1] if "acidity" in arrays_dict else np.nan
        algorithm_used = "ode_sofia"
        
    # Evaluate metric errors over time
    t_sim = np.array(arrays_dict["t"])
    
    def sample_metric(metric_key, day_idx):
        if metric_key not in arrays_dict:
            return np.nan
        sim_arr = np.array(arrays_dict[metric_key])
        # Find index closest to day_idx
        idx = int(round(day_idx / 0.05))
        if idx < len(sim_arr):
            return sim_arr[idx]
        return sim_arr[-1]
        
    eval_records = []
    f_errors, b_errors, a_errors, q_errors = [], [], [], []
    
    for d_idx in range(days):
        row = df_readings.iloc[d_idx]
        rec = {"Day": d_idx + 1}
        has_obs = False
        
        # Firmness
        if pd.notnull(row.get('Real_Firmness')):
            r_f = float(row['Real_Firmness'])
            s_f = sample_metric("firmness", d_idx)
            rec["Real_Firmness"] = r_f
            rec["Sim_Firmness"] = s_f
            f_errors.append(abs(s_f - r_f))
            has_obs = True
            
        # Brix
        if pd.notnull(row.get('Real_BRIX')):
            r_b = float(row['Real_BRIX'])
            s_b = sample_metric("brix", d_idx)
            rec["Real_BRIX"] = r_b
            rec["Sim_BRIX"] = s_b
            b_errors.append(abs(s_b - r_b))
            has_obs = True
            
        # Acidity
        if pd.notnull(row.get('Real_Acidity')):
            r_a = float(row['Real_Acidity'])
            s_a = sample_metric("acidity", d_idx)
            rec["Real_Acidity"] = r_a
            rec["Sim_Acidity"] = s_a
            a_errors.append(abs(s_a - r_a))
            has_obs = True
            
        # Quality
        if pd.notnull(row.get('Real_Quality')):
            r_q = float(row['Real_Quality'])
            s_q = sample_metric("quality", d_idx)
            rec["Real_Quality"] = r_q
            rec["Sim_Quality"] = s_q
            q_errors.append(abs(s_q - r_q))
            has_obs = True
            
        if has_obs:
            eval_records.append(rec)
            
    mae_f = float(np.mean(f_errors)) if f_errors else None
    rmse_f = float(np.sqrt(np.mean(np.square(f_errors)))) if f_errors else None
    
    mae_b = float(np.mean(b_errors)) if b_errors else None
    rmse_b = float(np.sqrt(np.mean(np.square(b_errors)))) if b_errors else None
    
    mae_a = float(np.mean(a_errors)) if a_errors else None
    rmse_a = float(np.sqrt(np.mean(np.square(a_errors)))) if a_errors else None
    
    mae_q = float(np.mean(q_errors)) if q_errors else None
    rmse_q = float(np.sqrt(np.mean(np.square(q_errors)))) if q_errors else None
    
    sl_error = abs(pred_sl - exp_sl)
    is_sl_pass = sl_error <= tol_sl
    
    return {
        "file": os.path.basename(excel_path),
        "folder": os.path.basename(os.path.dirname(excel_path)),
        "path": excel_path,
        "fruit_key": fruit_key,
        "algorithm": algorithm_used,
        "days": days,
        "owner": current_owner,
        "final_quality": float(final_q),
        "final_firmness": float(final_f),
        "final_brix": float(final_b),
        "final_acidity": float(final_a) if pd.notnull(final_a) else None,
        "predicted_sl": float(pred_sl),
        "expected_sl": exp_sl,
        "sl_tolerance": tol_sl,
        "sl_error": float(sl_error),
        "sl_status": "PASS" if is_sl_pass else ("WARN" if sl_error <= tol_sl * 1.5 else "FAIL"),
        "eval_checkpoints": len(eval_records),
        "mae_firmness": mae_f,
        "rmse_firmness": rmse_f,
        "mae_brix": mae_b,
        "rmse_brix": rmse_b,
        "mae_acidity": mae_a,
        "rmse_acidity": rmse_a,
        "mae_quality": mae_q,
        "rmse_quality": rmse_q,
        "description": desc,
        "reference_doi": doi
    }

def find_and_calibrate_divergent_presets(results):
    """
    Identifies fruits with divergent benchmarks (FAIL / WARN or high MAE)
    that possess observed laboratory ground truth, and automatically runs
    the decoupled ODE optimizer to compute calibrated parameter improvements.
    """
    from calibrate_sofia_presets import calibrate_fruit, PRESETS_SOFIA
    
    grouped = {}
    for r in results:
        fk = r.get("fruit_key")
        if not fk or fk not in PRESETS_SOFIA:
            continue
        if fk not in grouped:
            grouped[fk] = []
        grouped[fk].append(r)
        
    proposals = []
    
    for fk, sc_list in grouped.items():
        has_divergence = any(
            s['sl_status'] in ['FAIL', 'WARN'] or
            (s['mae_firmness'] is not None and s['mae_firmness'] > 5.0) or
            (s['mae_brix'] is not None and s['mae_brix'] > 1.0)
            for s in sc_list
        )
        has_lab_data = any(s.get('eval_checkpoints', 0) > 0 for s in sc_list)
        
        if not (has_divergence and has_lab_data):
            continue
            
        file_paths = [s['path'] for s in sc_list]
        cal_res = calibrate_fruit(
            fruit_key=fk,
            excel_paths=file_paths,
            verbose=False
        )
        if not cal_res or not cal_res.get('module_improvements'):
            continue
            
        valid_improvements = {}
        for mod, stats in cal_res['module_improvements'].items():
            if stats.get('delta', 0.0) > 0.005:
                valid_improvements[mod] = stats
                
        if valid_improvements:
            proposals.append({
                "fruit_key": fk,
                "fruit_label": PRESETS_SOFIA[fk].get("label", fk),
                "folder": sc_list[0]['folder'],
                "improvements": valid_improvements,
                "calibrated_params": cal_res['calibrated_params'],
                "dict_str": cal_res['dict_str']
            })
            
    return proposals

def run_all_tests(fruit_filter=None, test_dir="all", auto_optimize=True):
    if test_dir.lower() == "all":
        target_dirs = ["tests", "tests_1"]
        all_results = {}
        for d in target_dirs:
            d_path = os.path.join(ROOT_DIR, d)
            if os.path.exists(d_path):
                all_results[d] = run_all_tests(
                    fruit_filter,
                    test_dir=d,
                    auto_optimize=auto_optimize
                )
        return all_results

    tests_dir = os.path.join(ROOT_DIR, test_dir)
    excel_files = []
    
    for root, _, files in os.walk(tests_dir):
        for f in sorted(files):
            if f.endswith('.xlsx') and not f.startswith('~$'):
                excel_files.append(os.path.join(root, f))
                
    if fruit_filter:
        excel_files = [p for p in excel_files if fruit_filter.lower() in p.lower()]
        
    if not excel_files:
        print(f"No Excel test files found in {tests_dir}.")
        return []
        
    print("=" * 115)
    print(f"{'EUREKA LC MODEL v0.2.0 - SCIENTIFIC BENCHMARK SUITE (' + test_dir + ')':^115}")
    print("=" * 115)
    print(f"{'Fruit / Scenario':<30} {'Days':<5} {'Sampling':<10} {'Sim Quality':<12} {'Pred SL':<10} {'Exp SL':<10} {'SL Status':<10} {'Firm MAE':<10} {'Brix MAE':<10}")
    print("-" * 115)
    
    results = []
    pass_count, warn_count, fail_count = 0, 0, 0
    
    for p in excel_files:
        try:
            res = run_single_test(p)
            results.append(res)
            
            status = res['sl_status']
            if status == "PASS": pass_count += 1
            elif status == "WARN": warn_count += 1
            else: fail_count += 1
            
            f_mae_str = f"{res['mae_firmness']:.2f} N" if res['mae_firmness'] is not None else "-"
            b_mae_str = f"{res['mae_brix']:.2f}" if res['mae_brix'] is not None else "-"
            q_str = f"{res['final_quality']:.1f}%"
            sl_pred_str = f"{res['predicted_sl']:.1f} d"
            sl_exp_str = f"{res['expected_sl']:.1f} d"
            pts_str = f"{res['eval_checkpoints']} pts"
            
            name = f"{res['folder']}: {res['file'].replace('.xlsx', '')}"
            if len(name) > 28:
                name = name[:26] + ".."
                
            print(f"{name:<30} {res['days']:<5} {pts_str:<10} {q_str:<12} {sl_pred_str:<10} {sl_exp_str:<10} {status:<10} {f_mae_str:<10} {b_mae_str:<10}")
        except Exception as e:
            print(f"Error testing {p}: {e}")
            fail_count += 1
            
    print("-" * 115)
    total = len(results)
    print(f"Summary: {total} Scientific Benchmarks | {pass_count} Passed | {warn_count} Within Margin | {fail_count} Failed")
    print("=" * 115)
    
    # Run automated preset calibration analysis for divergent fruits
    optimization_proposals = []
    if auto_optimize:
        print("\n" + "=" * 115)
        print(f"{'RUNNING AUTOMATED PRESET OPTIMIZATION ANALYSIS':^115}")
        print("=" * 115)
        optimization_proposals = find_and_calibrate_divergent_presets(results)
        if optimization_proposals:
            print(f"Co-calibrated {len(optimization_proposals)} divergent fruit preset(s) against laboratory checkpoints:\n")
            for p in optimization_proposals:
                print(f"* {p['fruit_label']} [{p['fruit_key']}]:")
                for mod_name, stat in p['improvements'].items():
                    print(f"  - {stat['module_label']:<28}: MAE {stat['pre_mae']:5.2f} {stat['unit']} -> {stat['post_mae']:5.2f} {stat['unit']} (-{stat['delta']:.2f} {stat['unit']})")
                    shift_items = [f"{pn}: {pv['before']:.4f} -> {pv['after']:.4f}" for pn, pv in stat['param_shifts'].items() if abs(pv['before'] - pv['after']) > 1e-4]
                    if shift_items:
                        print(f"    Parameters: {', '.join(shift_items)}")
                print(f"  --> Calibrate command: python test_scripts/calibrate_sofia_presets.py --fruit {p['fruit_key']}\n")
            print("-" * 115)
        else:
            print("No divergent fruits with observed laboratory data required calibration adjustments.")
            print("-" * 115)
            
    # Save benchmark report markdown
    save_reports(results, tests_dir, optimization_proposals=optimization_proposals)
    return results

def save_reports(results, out_dir, optimization_proposals=None):
    md_path = os.path.join(out_dir, "benchmark_report.md")
    
    total = len(results)
    passed = sum(1 for r in results if r['sl_status'] == 'PASS')
    warned = sum(1 for r in results if r['sl_status'] == 'WARN')
    failed = sum(1 for r in results if r['sl_status'] == 'FAIL')
    pass_pct = (passed / total * 100.0) if total > 0 else 0.0
    
    firm_maes = [r['mae_firmness'] for r in results if r['mae_firmness'] is not None]
    avg_f_mae = np.mean(firm_maes) if firm_maes else 0.0
    
    brix_maes = [r['mae_brix'] for r in results if r['mae_brix'] is not None]
    avg_b_mae = np.mean(brix_maes) if brix_maes else 0.0
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 🧪 Scientific Validation & Benchmark Report\n\n")
        f.write("> **Engine Version:** `LC_model_v0_2_0.py`  \n")
        f.write(f"> **Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"> **Directory:** `{os.path.basename(out_dir)}/` (Excel Format with Scientific Calibration)  \n\n")
        
        # High-level scorecard
        f.write("## 1. Benchmark Scorecard\n\n")
        f.write("| Total Test Scenarios | Passed (Within Tol.) | Within Margin (Warn) | Divergent (Fail) | Pass Rate | Mean Firmness MAE | Mean Brix MAE |\n")
        f.write("| :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        f.write(f"| **{total}** | **{passed}** | **{warned}** | **{failed}** | **{pass_pct:.1f}%** | **{avg_f_mae:.2f} N** | **{avg_b_mae:.2f} °Brix** |\n\n")
        
        # Main results table
        f.write("## 2. Scientific Benchmark Results\n\n")
        f.write("| Fruit / Scenario | Days | Sampling Points | Engine | Final Quality | Predicted SL | Expected SL | Status | Firmness MAE | Brix MAE | Academic Reference |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |\n")
        
        for r in results:
            status_icon = "✅ PASS" if r['sl_status'] == "PASS" else ("⚠️ WARN" if r['sl_status'] == "WARN" else "❌ FAIL")
            f_mae = f"{r['mae_firmness']:.2f} N" if r['mae_firmness'] is not None else "-"
            b_mae = f"{r['mae_brix']:.2f}" if r['mae_brix'] is not None else "-"
            pts = f"{r.get('eval_checkpoints', '-')} pts"
            pred_sl = f"{r['predicted_sl']:.1f} d"
            exp_sl = f"{r['expected_sl']:.1f} d (±{r['sl_tolerance']:.0f})"
            ref_link = r['reference_doi']
            if ref_link.startswith("http"):
                ref_str = f"[{r['folder']}]({ref_link})"
            else:
                ref_str = ref_link
            
            f.write(f"| **{r['folder']}**<br>`{r['file']}` | {r['days']} | {pts} | `{r['algorithm']}` | {r['final_quality']:.1f}% | {pred_sl} | {exp_sl} | {status_icon} | {f_mae} | {b_mae} | {ref_str} |\n")
            
        # Detailed scenario sections
        f.write("\n## 3. Scenario Analysis & Findings\n\n")
        for r in results:
            status_icon = "✅ PASS" if r['sl_status'] == "PASS" else ("⚠️ WARN" if r['sl_status'] == "WARN" else "❌ FAIL")
            f.write(f"### {r['folder']}: `{r['file']}` ({status_icon})\n")
            f.write(f"- **Description:** {r['description']}\n")
            f.write(f"- **Duration & Sampling:** {r['days']} total simulation days with {r['eval_checkpoints']} laboratory measurement checkpoints.\n")
            f.write(f"- **Predicted vs Literature Shelf Life:** Predicted `{r['predicted_sl']:.1f} days` vs Expected `{r['expected_sl']:.1f} ± {r['sl_tolerance']:.0f} days` (Residual: `{r['sl_error']:.1f} days`).\n")
            f.write(f"- **Reference:** {r['reference_doi']}\n\n")
            
        # Section 4: Presets Optimization & Calibration Proposals
        if optimization_proposals:
            f.write("## 4. Presets Optimization & Calibration Proposals\n\n")
            f.write("> **Automated Optimizer Engine:** `test_scripts/calibrate_sofia_presets.py`  \n")
            f.write("> Evaluated divergent fruits against discrete laboratory checkpoints to determine optimal biophysical parameter adjustments.\n\n")
            
            for prop in optimization_proposals:
                f.write(f"### {prop['fruit_label']} (`{prop['fruit_key']}`)\n\n")
                f.write("| Calibrated ODE Module | Pre-Calibration MAE | Post-Calibration MAE | Error Reduction | Key Parameter Adjustments |\n")
                f.write("| :--- | :---: | :---: | :---: | :--- |\n")
                
                for mod_name, stat in prop['improvements'].items():
                    shifts = []
                    for p_name, p_vals in stat['param_shifts'].items():
                        before = p_vals['before']
                        after = p_vals['after']
                        if abs(before - after) > 1e-4:
                            shifts.append(f"`{p_name}`: `{before:.4f}` → `{after:.4f}`")
                    shift_str = "<br>".join(shifts) if shifts else "Retained"
                    f.write(f"| **{stat['module_label']}** | {stat['pre_mae']:.2f} {stat['unit']} | **{stat['post_mae']:.2f} {stat['unit']}** | **-{stat['delta']:.2f} {stat['unit']}** | {shift_str} |\n")
                    
                f.write(f"\n- **Co-Calibration Command:**  \n")
                f.write(f"  ```powershell\n  python test_scripts/calibrate_sofia_presets.py --fruit {prop['fruit_key']}\n  ```\n\n")
            
    print(f"\nSaved benchmark markdown report:")
    print(f"  Markdown: {md_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Scientific Benchmark Runner for LC_model_v0_2_0")
    parser.add_argument("--fruit", type=str, default=None, help="Filter by fruit name")
    parser.add_argument("--dir", type=str, default="all", help="Target test directory ('tests', 'tests_1', or 'all' to run both, default: all)")
    parser.add_argument("--no-optimize", action="store_true", help="Skip automated preset calibration analysis")
    args = parser.parse_args()
    
    run_all_tests(
        fruit_filter=args.fruit,
        test_dir=args.dir,
        auto_optimize=not args.no_optimize
    )

