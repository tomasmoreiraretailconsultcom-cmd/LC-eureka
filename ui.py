import json
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import datetime

from LC_model_v0_2_0 import PRESETS_ACADEMIC, PRESETS_SOFIA, PACKAGING_FACTORS
from LC_model_v0_2_0 import forecast, add_preset, LifecycleDataRequest, PresetRequest

from lang.lang import *

st.set_page_config(layout="wide", page_title="Lifecycle")

# =============================================================================
# FRUIT PRESETS & CONSTANTS
# =============================================================================

REGIONS = [
    "PT-NL", "PT-NI", "PT-CL", "PT-CI", "PT-LVT", 
    "PT-AL", "PT-ALG", "PT-SM", "PT-MAD", "PT-ACO"
]

def get_presets_from_api():
    return list(set(list(PRESETS_ACADEMIC.keys()) + list(PRESETS_SOFIA.keys())))

FORECAST_CLIENT_ID = os.getenv("FORECAST_CLIENT_ID", "streamlit-ui")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def init_session_state():
    if "segments" not in st.session_state:
        st.session_state.segments = [{
            "duration": 5, 
            "is_controlled": False,
            "start_date": datetime.date.today(),
            "warehouse_id": 1,
            "region": "PT-LVT",
            "packaging_method": list(PACKAGING_FACTORS.keys())[0]
        }]

def build_lifecycle_payload(fruit_key, initial_firmness, initial_brix, initial_acidity, lot_id, json_fallback_mode, fixed_temp, fixed_rh, plot_info, current_owner_type):
    """Build the complex LifecycleDataRequest expected by LC_model_v0_2_0 API."""
    
    sensor_history = []
    current_date = datetime.date.today()
    
    for i, seg in enumerate(st.session_state.segments):
        daily_readings = []
        seg_start_date = seg.get("start_date", datetime.date.today())
        
        if seg.get("is_controlled"):
            for d in range(seg["duration"]):
                current_date = seg_start_date + datetime.timedelta(days=d)
                reading = {
                    "date": current_date.isoformat(),
                    "source": "SIMULATION_UI"
                }
                
                val_t = st.session_state.get(f"val_t_{i}_{d}")
                if val_t is not None:
                    reading["temperature_celsius"] = float(val_t)
                    
                val_h = st.session_state.get(f"val_h_{i}_{d}")
                if val_h is not None:
                    reading["humidity_percent"] = float(val_h)
                    
                val_e = st.session_state.get(f"val_e_{i}_{d}")
                if val_e is not None:
                    reading["ethylene_ppm"] = float(val_e)
                    
                daily_readings.append(reading)
            
        history_entry = {
            "warehouse_id": seg["warehouse_id"],
            "warehouse_location": f"Warehouse {seg['warehouse_id']}",
            "meteo_source": "SIMULATION",
            "region": seg["region"],
            "total_days_recorded": seg["duration"],
            "packaging_method": seg.get("packaging_method"),
            "daily_readings": daily_readings
        }
        
        if not seg.get("is_controlled"):
            history_entry["keptancy_start_date"] = seg_start_date.isoformat()
            
        sensor_history.append(history_entry)
            
    total_days = sum(sh["total_days_recorded"] for sh in sensor_history)
    
    return {
        "version": "1.0",
        "export_metadata": {
            "generated_at": datetime.datetime.now().isoformat(),
            "target_service": "Lifecycle Decay Prediction Model Web Service",
            "days_elapsed_total": total_days,
        },
        "lot_identification": {
            "lot_id": lot_id,
            "batch_id": f"BATCH-{lot_id}",
            "culture_name": fruit_key,
            "fruit_type": fruit_key,
            "producer": "Simulated Producer",
            "current_owner": "Simulated Retailer",
            "current_owner_type": current_owner_type,
            "harvest_date": (datetime.date.today() - datetime.timedelta(days=total_days)).isoformat(),
            "initial_quantity_kg": 1000.0,
            "current_stock_kg": 1000.0,
            "delivered_quantity_kg": 0.0,
            "initial_metrics": {
                "soluble_solids_brix": float(initial_brix),
                "quality_score": 100,
                "waste_kg": 0.0,
                "firmness": float(initial_firmness),
                "acidity": float(initial_acidity)
            }
        },
        "plantation_origin": {
            "farm_id": "F-01",
            "location": "Simulated Location",
            "region_code": "PT-LVT",
            "soil_type": "Unknown",
            "irrigation_system": "Unknown"
        },
        "plantation_agricultural_events": [],
        "meteorology_and_imputation_strategy": {
            "json_fallback_mode": json_fallback_mode,
            "json_fallback_display": json_fallback_mode,
            "fixed_temperature_celsius": float(fixed_temp),
            "fixed_humidity_percent": float(fixed_rh),
            "ipma_region_code": "PT-LVT",
            "imputation_instructions": "Simulation defaults"
        },
        "blockchain_ledger": {
            "total_blocks_count": 0,
            "blocks": []
        },
        "transport_and_logistics": [],
        "current_warehouse": {
            "id": st.session_state.segments[-1]["warehouse_id"] if st.session_state.segments else None
        },
        "sensor_history_by_warehouse": sensor_history,
        "plot_info": plot_info
    }

def post_simulation(payload, language_code):
    """Call the simulation directly natively and return normalized response or error."""
    try:
        req = LifecycleDataRequest(**payload)
        response = forecast(req, client_id=FORECAST_CLIENT_ID)
        if hasattr(response, "status_code") and response.status_code != 200:
            import json as j
            st.error(f"Error {response.status_code}: {j.loads(response.body)}")
            return None
            
        return response.model_dump()
    except Exception as e:
        st.error(f"Execution error: {e}")
        return None

def plot_results(results, lang_sel="en", real_data_df=None, current_owner_type=None):
    if not results:
        return
        
    cdata = results.get("continuous_data")
    if cdata:
        firmness = cdata.get("firmness", [])
        brix = cdata.get("brix", [])
        acidity = cdata.get("acidity", [])
        quality = cdata.get("quality", [])
        quality_base = cdata.get("quality_base", [])
        ratio = cdata.get("ratio", [])
        days = cdata.get("t", list(range(len(firmness))))
        st.markdown(f"### {CONT_SIM_RESULTS_TITLE.get(lang_sel, 'Continuous Simulation Results')}")
        
        _days = CHART_DAYS.get(lang_sel, 'Days')
        _firmness = FIRMNESS_LBL.get(lang_sel, 'Firmness (N)')
        _acidity = ACIDITY_LBL.get(lang_sel, 'Acidity')
        _quality_idx = CHART_QUALITY_INDEX.get(lang_sel, 'Quality Index')
        _quality_base_word = CHART_QUALITY.get(lang_sel, 'Quality')
        if current_owner_type:
            short_owner = current_owner_type.split(" ")[0]
            _quality = f"{short_owner} - {_quality_base_word}"
        else:
            _quality = _quality_base_word
        
        c1, c2 = st.columns(2)
        with c1:
            if firmness:
                fig_f = go.Figure(go.Scatter(x=days, y=firmness, mode='lines', name=_firmness, line=dict(color='#1f77b4')))
                if real_data_df is not None and "Real_Firmness" in real_data_df.columns and "Day" in real_data_df.columns:
                    fig_f.add_trace(go.Scatter(x=real_data_df["Day"], y=real_data_df["Real_Firmness"], mode='markers', name='Real', marker=dict(color='black', size=8, symbol='x')))
                fig_f.update_layout(title=_firmness, xaxis_title=_days, yaxis_title=_firmness, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_f, width="stretch")
            if acidity:
                fig_a = go.Figure(go.Scatter(x=days, y=acidity, mode='lines', name=_acidity, line=dict(color='#d62728')))
                if real_data_df is not None and "Real_Acidity" in real_data_df.columns and "Day" in real_data_df.columns:
                    fig_a.add_trace(go.Scatter(x=real_data_df["Day"], y=real_data_df["Real_Acidity"], mode='markers', name='Real', marker=dict(color='black', size=8, symbol='x')))
                fig_a.update_layout(title=_acidity, xaxis_title=_days, yaxis_title=_acidity, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_a, width="stretch")
                
        with c2:
            if brix:
                fig_b = go.Figure(go.Scatter(x=days, y=brix, mode='lines', name='Brix', line=dict(color='#ff7f0e')))
                if real_data_df is not None and "Real_BRIX" in real_data_df.columns and "Day" in real_data_df.columns:
                    fig_b.add_trace(go.Scatter(x=real_data_df["Day"], y=real_data_df["Real_BRIX"], mode='markers', name='Real', marker=dict(color='black', size=8, symbol='x')))
                fig_b.update_layout(title="Brix", xaxis_title=_days, yaxis_title="Brix", margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_b, width="stretch")
            if quality:
                fig_q = go.Figure(go.Scatter(x=days, y=quality, mode='lines', name=_quality, line=dict(color='#2ca02c')))
                if quality_base:
                    _base_quality = CHART_BASE_QUALITY.get(lang_sel, 'Base Quality')
                    fig_q.add_trace(go.Scatter(x=days, y=quality_base, mode='lines', name=_base_quality, line=dict(color='#17becf', dash='dash')))
                if real_data_df is not None and "Real_Quality" in real_data_df.columns and "Day" in real_data_df.columns:
                    fig_q.add_trace(go.Scatter(x=real_data_df["Day"], y=real_data_df["Real_Quality"], mode='markers', name='Real', marker=dict(color='black', size=8, symbol='x')))
                fig_q.update_layout(title=_quality_idx, xaxis_title=_days, yaxis_title=_quality, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_q, width="stretch")
            if ratio:
                fig_r = go.Figure(go.Scatter(x=days, y=ratio, mode='lines', name='Brix/Acidity Ratio', line=dict(color='#8c564b')))
                fig_r.update_layout(title="Brix/Acidity Ratio", xaxis_title=_days, yaxis_title="Ratio", margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_r, width="stretch")
                
        return

    history = results.get("history")
    if not history:
        return
        
    days = [entry.get("day", i) for i, entry in enumerate(history)]
    firmness = [entry.get("firmness", 0) for entry in history]
    brix = [entry.get("brix", 0) for entry in history]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=firmness, mode='lines', name='Firmness'))
    fig.add_trace(go.Scatter(x=days, y=brix, mode='lines', name='Brix', yaxis="y2"))
    
    fig.update_layout(
        title="Simulation Results",
        xaxis_title="Days",
        yaxis_title="Firmness",
        yaxis2=dict(
            title="Brix",
            overlaying="y",
            side="right"
        ),
        legend=dict(x=0.1, y=0.9)
    )
    st.plotly_chart(fig, width="stretch")

# =============================================================================
# MAIN UI
# =============================================================================

def main():
    init_session_state()
    
    # ── Sidebar ──
    st.sidebar.image("./img/rc.svg")
    st.sidebar.image("./img/retaill.png")
    
    lang_sel = st.session_state.get("lang", "en")
    st.sidebar.title(CONFIGURATION_TITLE.get(lang_sel, "Configuration"))
    lang_sel = st.sidebar.selectbox(LANGUAGE_SEL.get(lang_sel, "Language"), ["en", "pt", "es", "tr"], key="lang")
    
    st.sidebar.markdown("---")
    
    current_owner_type = st.sidebar.selectbox(
        STAKEHOLDER_ROLE_LBL.get(lang_sel, "Stakeholder Role"), 
        ["Retailer (Grocery Store)", "Producer / Exporter", "Industry (Juices/Jellies)"]
    )
    
    st.sidebar.markdown("---")
    
    # Fallback mode in sidebar
    json_fallback_mode = st.sidebar.selectbox(FALLBACK_MODE.get(lang_sel, "Fallback Mode"), ["FIXED", "IPMA"], index=1)
    if json_fallback_mode == "FIXED":
        fixed_temp = st.sidebar.number_input(FIXED_TEMP.get(lang_sel, "Fixed Temp (°C)"), value=4.0)
        fixed_rh = st.sidebar.number_input(FIXED_RH.get(lang_sel, "Fixed RH (%)"), value=90.0)
    else:
        fixed_temp = 4.0
        fixed_rh = 90.0
    
    # ── Main Area ──
    st.title(f"🍎 {APP_TITLE.get(lang_sel, 'Life Cycle - LC - Eureka')}")
    
    tab1, tab2 = st.tabs([f"1. 📈 {SIM_TAB.get(lang_sel, 'Simulation')}", f"2. 📜 {CREATE_PRESET_TAB.get(lang_sel, 'Create Preset')}"])
    
    with tab1:
        # ── Fruit Selection & Initial Metrics (directly visible) ──
        fruits_list = get_presets_from_api()
        fruit_key = st.selectbox(FRUIT_LBL.get(lang_sel, "Fruit"), fruits_list)
        preset = PRESETS_SOFIA.get(fruit_key, PRESETS_ACADEMIC.get(fruit_key, {"firmness_0_default": 60, "brix_0_default": 10.0, "acidity_0_default": 1.0}))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            f0 = st.number_input(FIRMNESS_LBL.get(lang_sel, "Firmness (N)"), value=float(preset.get("firmness_0_default", 60)))
        with col2:
            b0 = st.number_input(BRIX_LBL.get(lang_sel, "Brix"), value=float(preset.get("brix_0_default", 10.0)))
        with col3:
            a0 = st.number_input(ACIDITY_LBL.get(lang_sel, "Acidity"), value=float(preset.get("acidity_0_default", 1.0)))
        
        st.markdown("---")
        
        # ── Real Data Comparison (collapsed, optional) ──
        real_data_df = None
        with st.expander(f"📊 {REAL_DATA_COMP_TITLE.get(lang_sel, 'Real Measured Data Comparison')}", expanded=False):
            c_dl, c_up = st.columns(2)
            with c_dl:
                example_df = pd.DataFrame({
                    "Day": [1, 5, 10],
                    "Real_BRIX": [11.2, 11.5, 12.0],
                    "Real_Acidity": [0.6, 0.55, 0.5],
                    "Real_Firmness": [60.0, 55.0, 45.0],
                    "Real_Quality": [90.0, 85.0, 70.0]
                })
                csv_data = example_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=DOWNLOAD_CSV_LBL.get(lang_sel, "Download Example CSV Template"),
                    data=csv_data,
                    file_name='example_real_data.csv',
                    mime='text/csv',
                )
            with c_up:
                uploaded_file = st.file_uploader(UPLOAD_DATA_LBL.get(lang_sel, "Upload Real Data (CSV or Excel)"), type=["csv", "xlsx"])
                if uploaded_file is not None:
                    try:
                        if uploaded_file.name.endswith('.csv'):
                            real_data_df = pd.read_csv(uploaded_file)
                        elif uploaded_file.name.endswith('.xlsx'):
                            real_data_df = pd.read_excel(uploaded_file)
                        st.success(FILE_UPLOAD_SUCCESS.get(lang_sel, "File uploaded successfully!"))
                    except Exception as e:
                        st.error(f"{FILE_UPLOAD_ERROR.get(lang_sel, 'Error reading file:')} {e}")
        
        # ── Storage Segments ──
        st.markdown(f"### {SEGMENTS_TITLE.get(lang_sel, 'Storage Segments')}")
        
        col_btn1, col_btn2, _ = st.columns([1, 1, 2])
        with col_btn1:
            if st.button(ADD_SEGMENT_BTN.get(lang_sel, "Add Storage Segment")):
                st.session_state.segments.append({
                    "duration": 5, "is_controlled": False, "start_date": datetime.date.today(),
                    "warehouse_id": 1, "region": "PT-LVT", "packaging_method": list(PACKAGING_FACTORS.keys())[0]
                })
                st.rerun()
        with col_btn2:
            if st.button(REMOVE_SEGMENT_BTN.get(lang_sel, "Remove Storage Segment")) and len(st.session_state.segments) > 1:
                st.session_state.segments.pop()
                st.rerun()
        
        lot_id = 1
        
        for i, seg in enumerate(st.session_state.segments):
            with st.expander(f"📦 {SEGMENTS_TITLE.get(lang_sel, 'Storage Segments').split(' ')[-1]} {i+1}", expanded=True):
                seg["warehouse_id"] = i + 1
                w_col1, w_col2 = st.columns(2)
                with w_col1:
                    seg["region"] = st.selectbox(REGION_LBL.get(lang_sel, "Region"), REGIONS, index=REGIONS.index(seg.get("region", "PT-LVT")) if seg.get("region", "PT-LVT") in REGIONS else 4, key=f"reg_{i}")
                with w_col2:
                    packaging_opts = list(PACKAGING_FACTORS.keys())
                    seg["packaging_method"] = st.selectbox(PACKAGING_LBL.get(lang_sel, "Packaging"), packaging_opts, format_func=lambda x: PACKAGING_TRANS.get(lang_sel, {}).get(x, x), index=packaging_opts.index(seg.get("packaging_method", packaging_opts[0])) if seg.get("packaging_method") in packaging_opts else 0, key=f"pack_{i}")
                
                d_col1, d_col2, d_col3 = st.columns(3)
                with d_col1:
                    seg["duration"] = st.number_input(DURATION_DAYS.get(lang_sel, "Days"), min_value=1, value=seg["duration"], key=f"dur_{i}")
                with d_col2:
                    seg["start_date"] = st.date_input(START_DATE.get(lang_sel, "Start Date"), value=seg.get("start_date", datetime.date.today()), key=f"start_date_{i}")
                with d_col3:
                    st.write("")
                    st.write("")
                    seg["is_controlled"] = st.checkbox(IS_CONTROLLED.get(lang_sel, "Is the warehouse controlled?"), value=seg.get("is_controlled", False), key=f"controlled_{i}")
                    
                if seg.get("is_controlled"):
                    st.markdown(f"#### {DAILY_READINGS.get(lang_sel, 'Daily Readings')}")
                    st.caption(DAILY_READINGS_HINT.get(lang_sel, "Fill in values you have. Leave empty to let the model estimate."))
                    # Header row
                    hc1, hc2, hc3, hc4 = st.columns([0.5, 1, 1, 1])
                    with hc1:
                        st.markdown(f"**{DAY_LABEL.get(lang_sel, 'Day')}**")
                    with hc2:
                        st.markdown(f"**{TEMP_SHORT.get(lang_sel, 'Temp')} (°C)**")
                    with hc3:
                        st.markdown(f"**{RH_SHORT.get(lang_sel, 'RH')} (%)**")
                    with hc4:
                        st.markdown(f"**{ETH_SHORT.get(lang_sel, 'Eth')} (ppm)**")
                    # Data rows — fill what you have, leave empty for model estimation
                    for d in range(seg["duration"]):
                        c1, c2, c3, c4 = st.columns([0.5, 1, 1, 1])
                        with c1:
                            st.markdown(f"**{d+1}**")
                        with c2:
                            st.number_input("t", value=None, key=f"val_t_{i}_{d}", label_visibility="collapsed", placeholder="—")
                        with c3:
                            st.number_input("h", value=None, key=f"val_h_{i}_{d}", label_visibility="collapsed", placeholder="—")
                        with c4:
                            st.number_input("e", value=None, key=f"val_e_{i}_{d}", label_visibility="collapsed", placeholder="—")
        
        plot_info = True
        submitted = st.button(RUN_SIMULATION_BTN.get(lang_sel, "Run Simulation"), type="primary")

        if submitted:
            payload = build_lifecycle_payload(fruit_key, f0, b0, a0, lot_id, json_fallback_mode, fixed_temp, fixed_rh, plot_info, current_owner_type)
            with st.spinner(SIMULATING_SPINNER.get(lang_sel, "Simulating...")):
                result = post_simulation(payload, lang_sel)
                if result:
                    algo = result.get("algorithm", "unknown")
                    st.success(f"{SIMULATION_COMPLETE.get(lang_sel, 'Simulation Complete!')} {ALGORITHM_USED.get(lang_sel, 'Algorithm used')}: {algo}")
                    
                    if result.get("continuous_data") and result["continuous_data"].get("firmness"):
                        final_f = result["continuous_data"]["firmness"][-1]
                        
                        brix_list = result["continuous_data"].get("brix")
                        final_b = f"{brix_list[-1]:.1f}" if brix_list else "N/A"
                        
                        acidity_list = result["continuous_data"].get("acidity")
                        final_a = f"{acidity_list[-1]:.2f}" if acidity_list else "N/A"
                        
                        quality_list = result["continuous_data"].get("quality")
                        final_q = f"{quality_list[-1]:.1f}/100" if quality_list else "N/A"
                        
                        if "t" in result["continuous_data"]:
                            days_sim = round(result["continuous_data"]["t"][-1], 2)
                        else:
                            days_sim = sum(seg["duration"] for seg in st.session_state.segments)
                        
                        st.markdown(f"### {KPI_TITLE.get(lang_sel, 'Key Performance Indicators')}")
                        m1, m2, m3, m4, m5 = st.columns(5)
                        m1.metric(KPI_DAYS_SIM.get(lang_sel, 'Days Simulated'), days_sim)
                        m2.metric(KPI_FINAL_QUALITY.get(lang_sel, 'Final Quality'), final_q)
                        m3.metric(KPI_FINAL_FIRMNESS.get(lang_sel, 'Final Firmness'), f"{final_f:.1f} N")
                        m4.metric(KPI_FINAL_BRIX.get(lang_sel, 'Final Brix'), f"{final_b} ºBrix")
                        m5.metric(KPI_FINAL_ACIDITY.get(lang_sel, 'Final Acidity'), f"{final_a} %")
                        st.markdown("---")
                    
                    try:
                        plot_results(result, lang_sel, real_data_df, current_owner_type)
                    except Exception as e:
                        pass
                    
    with tab2:
        st.header(CREATE_NEW_PRESET_TITLE.get(lang_sel, "Create New Preset"))
        new_fruit_key = st.text_input(FRUIT_KEY_LBL.get(lang_sel, "Fruit Key (e.g., apple_gala_custom)"), "")
        
        use_ethylene = st.toggle(ENABLE_ETHYLENE_TOGGLE.get(lang_sel, "Enable Ethylene Properties (Academic Model)"), value=False)
        
        with st.expander(GENERAL_KINETICS_TITLE.get(lang_sel, "General / Kinetics"), expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                Tref_C = st.number_input("Tref_C", value=0.0)
                Ea_J = st.number_input("Ea_J", value=40000.0)
                k_firm_ref = st.number_input("k_firm_ref", value=0.015)
                beta_RH = st.number_input("beta_RH", value=1.2)
                RH_ref = st.number_input("RH_ref", value=90.0)
                firmness_min = st.number_input("firmness_min", value=2.0)
                firmness_0_default = st.number_input("firmness_0_default", value=65.0)
            with c2:
                brix_min = st.number_input("brix_min", value=6.0)
                brix_max = st.number_input("brix_max", value=15.0)
                brix_g = st.number_input("brix_g", value=0.35)
                brix_0_default = st.number_input("brix_0_default", value=6.5)
                qual_firmness_threshold = st.number_input("qual_firmness_threshold", value=8.0)
                qual_brix_target = st.number_input("qual_brix_target", value=14.0)
                if not use_ethylene:
                    acidity_0_default = st.number_input("acidity_0_default", value=1.2)
            with c3:
                if not use_ethylene:
                    acidity_min = st.number_input("acidity_min", value=0.5)
                    k_acidity_ref = st.number_input("k_acidity_ref", value=0.02)
                    Ea_acidity_J = st.number_input("Ea_acidity_J", value=55000.0)
                    qual_acidity_target = st.number_input("qual_acidity_target", value=1.0)
                    SL_ref = st.number_input("SL_ref", value=120.0)
                else:
                    acidity_0_default = acidity_min = k_acidity_ref = Ea_acidity_J = qual_acidity_target = SL_ref = None
            
        if use_ethylene:
            with st.expander(ETHYLENE_PROP_TITLE.get(lang_sel, "Ethylene Properties"), expanded=True):
                e1, e2, e3 = st.columns(3)
                with e1:
                    E0_int = st.number_input("E0_int", value=0.02)
                    Eref_prod = st.number_input("Eref_prod", value=0.15)
                    E_t0 = st.number_input("E_t0", value=9.0)
                with e2:
                    E_g = st.number_input("E_g", value=0.9)
                    E_auto = st.number_input("E_auto", value=0.4)
                    E_decay = st.number_input("E_decay", value=0.7)
                with e3:
                    Ea_E_J = st.number_input("Ea_E_J", value=52000.0)
                    E_ext_shift = st.number_input("E_ext_shift", value=2.0)
                    alpha_E = st.number_input("alpha_E", value=2.0)
        else:
            E0_int = Eref_prod = E_t0 = E_g = E_auto = E_decay = Ea_E_J = E_ext_shift = alpha_E = None
            
        with st.expander(MOLD_PROP_TITLE.get(lang_sel, "Mold Properties"), expanded=True):
            m1, m2, m3 = st.columns(3)
            with m1:
                RH_mold_thr = st.number_input("RH_mold_thr", value=95.0)
                mold_rate_ref = st.number_input("mold_rate_ref", value=0.05)
            with m2:
                mold_sens_RH = st.number_input("mold_sens_RH", value=9.0)
                mold_max_penalty = st.number_input("mold_max_penalty", value=0.65)
            with m3:
                Ea_mold_J = st.number_input("Ea_mold_J", value=43000.0)
            
        if st.button(SAVE_PRESET_BTN.get(lang_sel, "Save Custom Preset"), type="primary"):
            if not new_fruit_key:
                st.error(PLEASE_ENTER_KEY_ERR.get(lang_sel, "Please enter a Fruit Key."))
            else:
                preset_payload = {
                    "fruit_key": new_fruit_key,
                    "preset": {
                        "Tref_C": Tref_C, "Ea_J": Ea_J, "k_firm_ref": k_firm_ref, "beta_RH": beta_RH,
                        "RH_ref": RH_ref, "firmness_min": firmness_min, "firmness_0_default": firmness_0_default,
                        "brix_min": brix_min, "brix_max": brix_max, "brix_g": brix_g, "brix_0_default": brix_0_default,
                        "qual_firmness_threshold": qual_firmness_threshold, "qual_brix_target": qual_brix_target,
                        "acidity_0_default": acidity_0_default, "acidity_min": acidity_min, "k_acidity_ref": k_acidity_ref,
                        "Ea_acidity_J": Ea_acidity_J, "qual_acidity_target": qual_acidity_target, "SL_ref": SL_ref,
                        "E0_int": E0_int, "Eref_prod": Eref_prod, "E_t0": E_t0, "E_g": E_g, "E_auto": E_auto,
                        "E_decay": E_decay, "Ea_E_J": Ea_E_J, "E_ext_shift": E_ext_shift, "alpha_E": alpha_E
                    },
                    "mold_preset": {
                        "RH_mold_thr": RH_mold_thr, "mold_rate_ref": mold_rate_ref, "mold_sens_RH": mold_sens_RH,
                        "mold_max_penalty": mold_max_penalty, "Ea_mold_J": Ea_mold_J
                    }
                }
                try:
                    req = PresetRequest(**preset_payload)
                    add_preset(req)
                    st.success(f"{PRESET_CREATED_SUCC.get(lang_sel, 'Preset created successfully!')} ({new_fruit_key})")
                    st.rerun()
                except Exception as e:
                    st.error(f"{PRESET_SAVE_ERR.get(lang_sel, 'Error saving preset:')} {e}")

if __name__ == "__main__":
    main()
