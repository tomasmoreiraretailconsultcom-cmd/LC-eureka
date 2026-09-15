import json
import os
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import datetime

from lang.lang import *

st.set_page_config(layout="wide", page_title="LC_model_v0_2_0 Simulator")

# =============================================================================
# FRUIT PRESETS & CONSTANTS
# =============================================================================

REGIONS = [
    "PT-NL", "PT-NI", "PT-CL", "PT-CI", "PT-LVT", 
    "PT-AL", "PT-ALG", "PT-SM", "PT-MAD", "PT-ACO"
]

PRESETS = {
    "kiwi_hayward": {"firmeza_0_default": 65, "brix_0_default": 6.5, "acidez_0_default": 1.2},
    "kiwi_baby": {"firmeza_0_default": 40, "brix_0_default": 8.0, "acidez_0_default": 1.1},
    "kiwi_gold": {"firmeza_0_default": 50, "brix_0_default": 8.5, "acidez_0_default": 1.0},
    "maca_fuji": {"firmeza_0_default": 85, "brix_0_default": 13.0, "acidez_0_default": 0.4},
    "maca_golden": {"firmeza_0_default": 70, "brix_0_default": 11.0, "acidez_0_default": 0.5},
    "maca_gala": {"firmeza_0_default": 70, "brix_0_default": 12.0, "acidez_0_default": 0.4},
    "maca_reineta": {"firmeza_0_default": 65, "brix_0_default": 10.5, "acidez_0_default": 0.8},
    "maca_granny_smith": {"firmeza_0_default": 90, "brix_0_default": 11.5, "acidez_0_default": 0.75},
    "maca_red_delicious": {"firmeza_0_default": 75, "brix_0_default": 12.0, "acidez_0_default": 0.3},
    "maca_bravo_esmolfe": {"firmeza_0_default": 55, "brix_0_default": 12.5, "acidez_0_default": 0.6},
    "maca_royal_gold": {"firmeza_0_default": 72, "brix_0_default": 11.5, "acidez_0_default": 0.45},
    "maca_pink_lady": {"firmeza_0_default": 88, "brix_0_default": 13.5, "acidez_0_default": 0.55},
    "maca_jonagold": {"firmeza_0_default": 72, "brix_0_default": 12.5, "acidez_0_default": 0.5},
    "maca_alcobaca": {"firmeza_0_default": 68, "brix_0_default": 11.5, "acidez_0_default": 0.55},
    "morango": {"firmeza_0_default": 5, "brix_0_default": 7.5, "acidez_0_default": 0.8},
    "framboesa": {"firmeza_0_default": 6, "brix_0_default": 9.5, "acidez_0_default": 1.2},
    "mirtilo": {"firmeza_0_default": 10, "brix_0_default": 11.5, "acidez_0_default": 0.6},
    "cereja": {"firmeza_0_default": 15, "brix_0_default": 16.0, "acidez_0_default": 0.5},
    "pessego": {"firmeza_0_default": 40, "brix_0_default": 10.0, "acidez_0_default": 0.6},
    "ameixa": {"firmeza_0_default": 35, "brix_0_default": 10.0, "acidez_0_default": 0.8},
    "laranja": {"firmeza_0_default": 50, "brix_0_default": 11.0, "acidez_0_default": 1.0},
    "banana": {"firmeza_0_default": 80, "brix_0_default": 5.0, "acidez_0_default": 0.4},
    "pera": {"firmeza_0_default": 50, "brix_0_default": 11.0, "acidez_0_default": 0.3},
    "uva": {"firmeza_0_default": 15, "brix_0_default": 16.0, "acidez_0_default": 0.6},
    "figo": {"firmeza_0_default": 8, "brix_0_default": 16.0, "acidez_0_default": 0.3},
    "melao": {"firmeza_0_default": 20, "brix_0_default": 10.0, "acidez_0_default": 0.2},
}

def get_presets_from_api(api_url):
    try:
        url = f"{api_url.rstrip('/')}/presets"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json().get("fruits", list(PRESETS.keys()))
    except:
        pass
    return list(PRESETS.keys())

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
            "region": "PT-LVT"
        }]

def build_lifecycle_payload(fruit_key, initial_firmness, initial_brix, initial_acidity, lot_id, json_fallback_mode, fixed_temp, fixed_rh, plot_info):
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
                
                if st.session_state.get(f"has_t_{i}_{d}"):
                    reading["temperature_celsius"] = float(st.session_state.get(f"val_t_{i}_{d}", 20.0))
                    
                if st.session_state.get(f"has_h_{i}_{d}"):
                    reading["humidity_percent"] = float(st.session_state.get(f"val_h_{i}_{d}", 85.0))
                    
                if st.session_state.get(f"has_e_{i}_{d}"):
                    reading["ethylene_ppm"] = float(st.session_state.get(f"val_e_{i}_{d}", 0.0))
                    
                daily_readings.append(reading)
            
        history_entry = {
            "warehouse_id": seg["warehouse_id"],
            "warehouse_location": f"Warehouse {seg['warehouse_id']}",
            "meteo_source": "SIMULATION",
            "region": seg["region"],
            "total_days_recorded": seg["duration"],
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

def post_simulation(api_url, payload, language_code):
    """POST request and return normalized response or error."""
    try:
        url = f"{api_url.rstrip('/')}/forecast"
        response = requests.post(
            url,
            json=payload,
            timeout=120,
            headers={"Accept": "application/json", "client-id": FORECAST_CLIENT_ID},
        )
        if not response.ok:
            st.error(f"Error {response.status_code}: {response.text}")
            return None
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None

def plot_results(results, real_data_df=None):
    if not results:
        return
        
    cdata = results.get("continuous_data")
    if cdata:
        firmness = cdata.get("firmness", [])
        brix = cdata.get("brix", [])
        acidity = cdata.get("acidity", [])
        quality = cdata.get("quality", [])
        days = list(range(len(firmness)))
        st.markdown("### Continuous Simulation Results")
        
        c1, c2 = st.columns(2)
        with c1:
            if firmness:
                fig_f = go.Figure(go.Scatter(x=days, y=firmness, mode='lines', name='Firmness', line=dict(color='#1f77b4')))
                if real_data_df is not None and "Real_Firmness" in real_data_df.columns and "Day" in real_data_df.columns:
                    fig_f.add_trace(go.Scatter(x=real_data_df["Day"], y=real_data_df["Real_Firmness"], mode='markers', name='Real Firmness', marker=dict(color='black', size=8, symbol='x')))
                fig_f.update_layout(title="Firmness", xaxis_title="Days", yaxis_title="Firmness (N)", margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_f, width="stretch")
            if acidity:
                fig_a = go.Figure(go.Scatter(x=days, y=acidity, mode='lines', name='Acidity', line=dict(color='#d62728')))
                if real_data_df is not None and "Real_Acidity" in real_data_df.columns and "Day" in real_data_df.columns:
                    fig_a.add_trace(go.Scatter(x=real_data_df["Day"], y=real_data_df["Real_Acidity"], mode='markers', name='Real Acidity', marker=dict(color='black', size=8, symbol='x')))
                fig_a.update_layout(title="Acidity", xaxis_title="Days", yaxis_title="Acidity", margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_a, width="stretch")
                
        with c2:
            if brix:
                fig_b = go.Figure(go.Scatter(x=days, y=brix, mode='lines', name='Brix', line=dict(color='#ff7f0e')))
                if real_data_df is not None and "Real_BRIX" in real_data_df.columns and "Day" in real_data_df.columns:
                    fig_b.add_trace(go.Scatter(x=real_data_df["Day"], y=real_data_df["Real_BRIX"], mode='markers', name='Real Brix', marker=dict(color='black', size=8, symbol='x')))
                fig_b.update_layout(title="Brix", xaxis_title="Days", yaxis_title="Brix", margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_b, width="stretch")
            if quality:
                fig_q = go.Figure(go.Scatter(x=days, y=quality, mode='lines', name='Quality', line=dict(color='#2ca02c')))
                if real_data_df is not None and "Real_Quality" in real_data_df.columns and "Day" in real_data_df.columns:
                    fig_q.add_trace(go.Scatter(x=real_data_df["Day"], y=real_data_df["Real_Quality"], mode='markers', name='Real Quality', marker=dict(color='black', size=8, symbol='x')))
                fig_q.update_layout(title="Quality Index", xaxis_title="Days", yaxis_title="Quality", margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_q, width="stretch")
                
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
    
    st.sidebar.image("./img/rc.svg")
    st.sidebar.image("./img/retaill.png")
    
    st.sidebar.title("Configuration")
    lang_sel = st.sidebar.selectbox("Language", ["en", "pt", "es", "tr"])
    
    st.sidebar.markdown("---")
    st.sidebar.subheader(API_V020_LABEL.get(lang_sel, "API Base URL"))
    api_url = st.sidebar.text_input("URL", "http://localhost:8181")
    
    st.title("Life Cycle - LC - Eureka")
    
    tab1, tab2 = st.tabs([SIM_TAB.get(lang_sel, "Simulation"), "Create Preset"])
    
    with tab1:
        fruits_list = get_presets_from_api(api_url)
        fruit_key = st.selectbox("Fruit", fruits_list)
        preset = PRESETS.get(fruit_key, {"firmeza_0_default": 60, "brix_0_default": 10.0, "acidez_0_default": 1.0})
        
        st.header(METADATA_TITLE.get(lang_sel, "Metadata"))
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            lot_id = st.number_input(LOT_ID.get(lang_sel, "Lot ID"), value=1, min_value=1)
        with col_m2:
            json_fallback_mode = st.selectbox(FALLBACK_MODE.get(lang_sel, "Fallback Mode"), ["FIXED", "IPMA"])
            if json_fallback_mode == "FIXED":
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    fixed_temp = st.number_input(FIXED_TEMP.get(lang_sel, "Fixed Temp (°C)"), value=4.0)
                with col_f2:
                    fixed_rh = st.number_input(FIXED_RH.get(lang_sel, "Fixed RH (%)"), value=90.0)
            else:
                fixed_temp = 4.0
                fixed_rh = 90.0
        
        st.header(INITIAL_METRICS_TITLE.get(lang_sel, "Initial Metrics"))
        col1, col2, col3 = st.columns(3)
        with col1:
            f0 = st.number_input("Firmness (N)", value=float(preset.get("firmeza_0_default", 60)))
        with col2:
            b0 = st.number_input("Brix", value=float(preset.get("brix_0_default", 10.0)))
        with col3:
            a0 = st.number_input("Acidity", value=float(preset.get("acidez_0_default", 1.0)))
            
        st.header(SEGMENTS_TITLE.get(lang_sel, "Storage Segments"))
        
        for i, seg in enumerate(st.session_state.segments):
            st.markdown(f"### {SEGMENTS_TITLE.get(lang_sel, 'Storage Segments').split(' ')[-1]} {i+1}")
            
            w_col1, w_col2 = st.columns(2)
            with w_col1:
                seg["warehouse_id"] = st.number_input(WAREHOUSE_ID.get(lang_sel, "Warehouse ID"), value=seg.get("warehouse_id", 1), key=f"wh_{i}")
            with w_col2:
                seg["region"] = st.selectbox("Region", REGIONS, index=REGIONS.index(seg.get("region", "PT-LVT")) if seg.get("region", "PT-LVT") in REGIONS else 4, key=f"reg_{i}")
            
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
                for d in range(seg["duration"]):
                    c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 0.8, 1.2, 0.8, 1.2, 0.8, 1.2])
                    with c1:
                        st.write("")
                        st.markdown(f"**{DAY_LABEL.get(lang_sel, 'Day')} {d+1}**")
                    with c2:
                        st.write("")
                        has_t = st.checkbox(TEMP_SHORT.get(lang_sel, "Temp"), key=f"has_t_{i}_{d}")
                    with c3:
                        if has_t:
                            st.number_input("°C", value=20.0, key=f"val_t_{i}_{d}", label_visibility="collapsed")
                    with c4:
                        st.write("")
                        has_h = st.checkbox(RH_SHORT.get(lang_sel, "RH"), key=f"has_h_{i}_{d}")
                    with c5:
                        if has_h:
                            st.number_input("%", value=85.0, key=f"val_h_{i}_{d}", label_visibility="collapsed")
                    with c6:
                        st.write("")
                        has_e = st.checkbox(ETH_SHORT.get(lang_sel, "Eth"), key=f"has_e_{i}_{d}")
                    with c7:
                        if has_e:
                            st.number_input("ppm", value=0.0, key=f"val_e_{i}_{d}", label_visibility="collapsed")
            
            st.markdown("---")
            
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button(ADD_SEGMENT_BTN.get(lang_sel, "Add Storage Segment")):
                st.session_state.segments.append({
                    "duration": 5, "is_controlled": False, "start_date": datetime.date.today(),
                    "warehouse_id": 1, "region": "PT-LVT"
                })
                st.rerun()
        with col_btn2:
            if st.button(REMOVE_SEGMENT_BTN.get(lang_sel, "Remove Storage Segment")) and len(st.session_state.segments) > 1:
                st.session_state.segments.pop()
                st.rerun()
                
        st.markdown("---")
        st.markdown("### Real Measured Data Comparison")
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
                label="Download Example CSV Template",
                data=csv_data,
                file_name='example_real_data.csv',
                mime='text/csv',
            )
        with c_up:
            uploaded_file = st.file_uploader("Upload Real Data (CSV or Excel)", type=["csv", "xlsx"])
            real_data_df = None
            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        real_data_df = pd.read_csv(uploaded_file)
                    elif uploaded_file.name.endswith('.xlsx'):
                        real_data_df = pd.read_excel(uploaded_file)
                    st.success("File uploaded successfully!")
                except Exception as e:
                    st.error(f"Error reading file: {e}")

        st.markdown("---")
        plot_info = st.checkbox("Show continuous data plots (plot_info)", value=False)
        if st.button(RUN_SIMULATION_BTN.get(lang_sel, "Run Simulation"), type="primary"):
            payload = build_lifecycle_payload(fruit_key, f0, b0, a0, lot_id, json_fallback_mode, fixed_temp, fixed_rh, plot_info)
            with st.spinner("Simulating..."):
                result = post_simulation(api_url, payload, lang_sel)
                if result:
                    st.success(SIMULATION_COMPLETE.get(lang_sel, "Simulation Complete!"))
                    st.json(result)
                    plot_results(result, real_data_df)
                    
    with tab2:
        st.header("Create New Preset")
        new_fruit_key = st.text_input("Fruit Key (e.g., apple_gala_custom)", "")
        
        st.subheader("General / Kinetics")
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
            acidity_0_default = st.number_input("acidity_0_default", value=1.2)
        with c3:
            acidity_min = st.number_input("acidity_min", value=0.5)
            k_acidity_ref = st.number_input("k_acidity_ref", value=0.02)
            Ea_acidity_J = st.number_input("Ea_acidity_J", value=55000.0)
            qual_acidity_target = st.number_input("qual_acidity_target", value=1.0)
            SL_ref = st.number_input("SL_ref", value=120.0)
            
        st.subheader("Ethylene Properties")
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
            
        st.subheader("Mold Properties")
        m1, m2, m3 = st.columns(3)
        with m1:
            RH_mold_thr = st.number_input("RH_mold_thr", value=95.0)
            mold_rate_ref = st.number_input("mold_rate_ref", value=0.05)
        with m2:
            mold_sens_RH = st.number_input("mold_sens_RH", value=9.0)
            mold_max_penalty = st.number_input("mold_max_penalty", value=0.65)
        with m3:
            Ea_mold_J = st.number_input("Ea_mold_J", value=43000.0)
            
        if st.button("Save Custom Preset", type="primary"):
            if not new_fruit_key:
                st.error("Please enter a Fruit Key.")
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
                    url = f"{api_url.rstrip('/')}/preset"
                    res = requests.post(url, json=preset_payload, timeout=10)
                    if res.status_code == 200:
                        st.success(f"Preset '{new_fruit_key}' created successfully!")
                        # Add to local cache for instant UI availability
                        PRESETS[new_fruit_key] = preset_payload["preset"]
                        st.rerun()
                    else:
                        st.error(f"Failed to create preset. Status code: {res.status_code}")
                        st.write(res.text)
                except Exception as e:
                    st.error(f"Error calling API: {e}")

if __name__ == "__main__":
    main()
