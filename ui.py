import os
import datetime
import json
import base64
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from LC_model_v0_2_0 import (
    PRESETS,
    PACKAGING_FACTORS,
    STAKEHOLDER_CONFIG_BY_GROUP,
    get_fruit_group,
    get_stakeholder_config,
    forecast,
    LifecycleDataRequest,
    LotIdentification,
    InitialMetrics,
    WarehouseHistory,
    DailyReading
)

# Page configuration
st.set_page_config(
    page_title="Lifecycle Post-Harvest Intelligence",
    page_icon="🍏",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High-End SaaS Styling (Modern Design System)
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    /* Main App Soft Grayish Background */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #F1F5F9 !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #E2E8F0 !important;
    }

    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F172A;
    }
    
    /* Top Navigation / Brand Banner */
    .top-brand-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 1.1rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
        color: white;
    }
    .brand-title {
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .brand-tagline {
        font-size: 0.85rem;
        color: #94A3B8;
        font-weight: 500;
    }
    .live-badge {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 8px #10B981;
    }

    /* Card Panels */
    .panel-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04), 0 2px 4px -2px rgba(0, 0, 0, 0.03);
    }
    .panel-header {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* KPI Highlights */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 1rem;
        margin-bottom: 1.25rem;
    }
    .kpi-tile {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 1rem 1.2rem;
        transition: transform 0.2s, box-shadow 0.2s;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .kpi-tile:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px -4px rgba(0,0,0,0.08);
    }
    .kpi-tile-header {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748B;
        margin-bottom: 0.35rem;
    }
    .kpi-tile-number {
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.1;
    }
    .kpi-unit {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        margin-left: 0.15rem;
    }
    .kpi-subtext {
        font-size: 0.72rem;
        color: #94A3B8;
        margin-top: 0.3rem;
        font-weight: 500;
    }

    .theme-emerald { color: #059669; }
    .theme-blue { color: #2563EB; }
    .theme-indigo { color: #4F46E5; }
    .theme-amber { color: #D97706; }
    .theme-rose { color: #E11D48; }

    /* Model Status Banner */
    .engine-banner {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #3B82F6;
        padding: 0.9rem 1.2rem;
        border-radius: 10px;
        margin-bottom: 1.25rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.9rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .engine-title {
        font-weight: 700;
        color: #1E293B;
    }
    .engine-chip {
        background: #DBEAFE;
        color: #1D4ED8;
        font-weight: 700;
        font-size: 0.75rem;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
    }

    /* Buttons */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: white;
        font-weight: 700;
        border: none;
        border-radius: 12px;
        padding: 0.65rem 1.5rem;
        font-size: 0.95rem;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
        transition: all 0.2s;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%);
        box-shadow: 0 6px 18px rgba(37, 99, 235, 0.35);
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# Helper function to get preset keys
def get_fruit_keys():
    return list(PRESETS.keys())

# =============================================================================
# HEADER BRAND BANNER
# =============================================================================

def get_base64_img(img_path):
    candidates = [img_path, os.path.join("img", os.path.basename(img_path)), os.path.basename(img_path)]
    for path in candidates:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
    return ""

logo_b64 = get_base64_img("img/retaill.png")
logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height: 38px; border-radius: 6px; margin-right: 0.75rem; vertical-align: middle; object-fit: contain;" alt="Logo" />' if logo_b64 else '🍏 '

st.markdown(f"""
<div class="top-brand-bar">
    <div style="display: flex; align-items: center;">
        {logo_html}
        <div class="brand-title">LIFECYCLE CORE™</div>
    </div>
    <div class="live-badge">
        <div class="pulse-dot"></div> ENGINE v2.0 ACTIVE
    </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# TOP CONFIGURATION BAR
# =============================================================================

with st.container():
    c_cfg1, c_cfg2, c_cfg3 = st.columns([1.6, 1.6, 1.0])

    with c_cfg1:
        fruit_list = get_fruit_keys()
        selected_fruit = st.selectbox(
            "🍎 **Fruto / Cultura**",
            fruit_list,
            index=fruit_list.index("apple_gala") if "apple_gala" in fruit_list else 0,
            format_func=lambda x: PRESETS.get(x, {}).get("label", x)
        )
        preset_data = PRESETS[selected_fruit]
        fruit_group = get_fruit_group(selected_fruit)

    with c_cfg2:
        stakeholder_options = [
            "Producer",
            "Processor",
            "Retailer",
            "Industry"
        ]
        selected_stakeholder = st.selectbox(
            "🏢 **Comprador / Stakeholder**",
            stakeholder_options,
            index=2
        )
        st_cfg = get_stakeholder_config(selected_fruit, selected_stakeholder)
        min_qual = st_cfg["min_quality"]
        mold_lim = st_cfg["mold_limit"]

    with c_cfg3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        # Template download dropdown or popover
        if os.path.exists("example_files/example_inputs.xlsx"):
            with open("example_files/example_inputs.xlsx", "rb") as f_ex:
                st.download_button(
                    "📥 Descarregar Template",
                    f_ex.read(),
                    file_name="template_lifecycle.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# =============================================================================
# WORKSPACE: 2-COLUMN ENTERPRISE LAYOUT
# =============================================================================

col_left, col_right = st.columns([1, 2.2], gap="large")

# -----------------------------------------------------------------------------
# LEFT COLUMN: INPUT CONTROLS & DATASETS
# -----------------------------------------------------------------------------
with col_left:
    st.markdown("""
    <div class="panel-box">
        <div class="panel-header">📦 Ingestão de Dados do Lote</div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Carregar ficheiro (.xlsx, .json)",
        type=["xlsx", "json"],
        label_visibility="collapsed",
        help="Colunas: Segment_ID, Date, Temperature_C, Humidity_Percent, Ethylene_ppm (opcional), Region, Packaging"
    )

    df_input = None
    if uploaded_file is not None:
        file_sig = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.get("last_uploaded_file_sig") != file_sig:
            st.session_state["last_uploaded_file_sig"] = file_sig
            st.session_state["simulation_result"] = None
            st.session_state["simulation_meta"] = None
        
        try:
            if uploaded_file.name.endswith(".json"):
                j_data = json.load(uploaded_file)
                if isinstance(j_data, dict) and "sensor_history_by_warehouse" in j_data:
                    rows = []
                    for wh in j_data["sensor_history_by_warehouse"]:
                        wh_id = wh.get("warehouse_id", 1)
                        region = wh.get("region", "PT-LVT")
                        pkg = wh.get("packaging_method", "bulk")
                        for dr in wh.get("daily_readings", []):
                            row = {
                                "Segment_ID": wh_id,
                                "Date": dr.get("date"),
                                "Temperature_C": dr.get("temperature_celsius"),
                                "Humidity_Percent": dr.get("humidity_percent"),
                                "Region": region,
                                "Packaging": pkg
                            }
                            if "ethylene_ppm" in dr and dr.get("ethylene_ppm") is not None:
                                row["Ethylene_ppm"] = float(dr.get("ethylene_ppm"))
                            rows.append(row)
                    df_input = pd.DataFrame(rows)
                elif isinstance(j_data, list):
                    df_input = pd.DataFrame(j_data)
                else:
                    st.error("Estrutura JSON não suportada.")
            else:
                df_input = pd.read_excel(uploaded_file)
                
            st.session_state["df_loaded"] = df_input
        except Exception as e:
            st.error(f"Erro ao ler ficheiro: {e}")
    else:
        st.markdown("<p style='font-size:0.8rem; color:#64748B; margin-bottom:0.5rem;'>Ou carregue um dataset de teste pré-configurado:</p>", unsafe_allow_html=True)
        c_quick1, c_quick2 = st.columns(2)
        with c_quick1:
            if st.button("🍃 Sem Etileno", use_container_width=True, help="Testar modelo da Sofia com Maçã Gala"):
                if os.path.exists("example_files/example_inputs.xlsx"):
                    df_input = pd.read_excel("example_files/example_inputs.xlsx")
                    st.session_state["df_loaded"] = df_input
                    st.session_state["simulation_result"] = None
                    st.session_state["simulation_meta"] = None
        with c_quick2:
            if st.button("💨 Com Etileno", use_container_width=True, help="Testar modelo do Prof. Luís Paulo com Kiwi"):
                if os.path.exists("example_files/example_inputs_ethylene.xlsx"):
                    df_input = pd.read_excel("example_files/example_inputs_ethylene.xlsx")
                    st.session_state["df_loaded"] = df_input
                    st.session_state["simulation_result"] = None
                    st.session_state["simulation_meta"] = None

        if "df_loaded" in st.session_state and df_input is None:
            df_input = st.session_state["df_loaded"]

    # Weather Imputation Section: Only appears AFTER a file is loaded
    fallback_mode = "IPMA"
    fixed_temp = 4.0
    fixed_rh = 90.0
    fixed_eth = 0.05

    if df_input is not None:
        st.markdown("<hr style='margin:0.8rem 0; border:none; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)
        with st.expander("🌦️ **Imputação de Clima (Preenchimento)**", expanded=False):
            st.caption("Define como preencher eventuais variáveis meteorológicas ausentes no ficheiro.")
            fallback_mode = st.selectbox(
                "Estratégia de Imputação",
                ["IPMA", "FIXED"],
                format_func=lambda x: "Regional IPMA (Histórico Climático)" if x == "IPMA" else "Valores Fixos Constantes"
            )
            if fallback_mode == "FIXED":
                c_fx1, c_fx2, c_fx3 = st.columns(3)
                with c_fx1:
                    fixed_temp = st.number_input("Temp (°C)", value=4.0, step=0.5)
                with c_fx2:
                    fixed_rh = st.number_input("HR (%)", value=90.0, step=1.0, min_value=10.0, max_value=100.0)
                with c_fx3:
                    fixed_eth = st.number_input("Etileno (ppm)", value=0.05, step=0.01, min_value=0.0)

    # Initial Physiological Metrics
    st.markdown("<hr style='margin:1rem 0; border:none; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-header' style='font-size:0.95rem; margin-bottom:0.5rem;'>📏 Métricas Iniciais Pós-Colheita</div>", unsafe_allow_html=True)
    
    c_in1, c_in2, c_in3 = st.columns(3)
    with c_in1:
        f0_val = st.number_input("Firmeza (N)", value=float(preset_data.get("firmness_0_default", 50.0)), step=1.0)
    with c_in2:
        b0_val = st.number_input("Brix (°Bx)", value=float(preset_data.get("brix_0_default", 12.0)), step=0.5)
    with c_in3:
        a0_val = st.number_input("Acidez (%)", value=float(preset_data.get("acidity_0_default", 0.8)), step=0.1)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    run_simulation_btn = st.button("⚡ Executar Análise Preditiva", type="primary", use_container_width=True)

    if df_input is not None:
        with st.expander("📋 Ver Dados do Histórico Carregado", expanded=False):
            st.dataframe(df_input, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Execute simulation only upon button click
    if run_simulation_btn:
        if df_input is None:
            st.warning("⚠️ Carregue primeiro um ficheiro Excel ou JSON antes de executar a análise.")
        else:
            req_cols = ["Segment_ID", "Temperature_C", "Humidity_Percent"]
            missing_cols = [rc for rc in req_cols if rc not in df_input.columns]
            if missing_cols:
                st.error(f"Coluna(s) obrigatória(s) em falta no ficheiro: {', '.join(missing_cols)}")
            else:
                df_calc = df_input.copy()
                if "Day" not in df_calc.columns:
                    df_calc["Day"] = range(1, len(df_calc) + 1)

                if 'Date' in df_calc.columns:
                    df_calc['Date'] = pd.to_datetime(df_calc['Date'])
                    df_calc = df_calc.sort_values('Date')

                df_calc['block'] = (df_calc['Segment_ID'] != df_calc['Segment_ID'].shift(1)).cumsum()
                sensor_history = []

                for (seg_id, _), group in df_calc.groupby(['Segment_ID', 'block']):
                    daily_readings = []
                    for _, row in group.iterrows():
                        r_date = pd.to_datetime(row['Date']).date().isoformat() if pd.notnull(row.get('Date')) else datetime.date.today().isoformat()
                        reading = {
                            "date": r_date,
                            "source": "SIMULATION_INPUT"
                        }
                        if pd.notnull(row.get('Temperature_C')): reading["temperature_celsius"] = float(row['Temperature_C'])
                        if pd.notnull(row.get('Humidity_Percent')): reading["humidity_percent"] = float(row['Humidity_Percent'])
                        if 'Ethylene_ppm' in row and pd.notnull(row.get('Ethylene_ppm')): reading["ethylene_ppm"] = float(row['Ethylene_ppm'])
                        daily_readings.append(reading)

                    first_row = group.iloc[0]
                    first_date = pd.to_datetime(first_row['Date']).date().isoformat() if pd.notnull(first_row.get('Date')) else datetime.date.today().isoformat()

                    sensor_history.append({
                        "warehouse_id": int(seg_id),
                        "warehouse_location": f"Armazém {int(seg_id)}",
                        "meteo_source": "SIMULATION",
                        "region": str(first_row.get('Region', 'PT-LVT')),
                        "total_days_recorded": len(group),
                        "packaging_method": str(first_row.get('Packaging', 'bulk')),
                        "starting_date": first_date,
                        "daily_readings": daily_readings
                    })

                total_days = sum(sh["total_days_recorded"] for sh in sensor_history)

                payload = {
                    "version": "1.0",
                    "export_metadata": {
                        "generated_at": datetime.datetime.now().isoformat(),
                        "days_elapsed_total": total_days
                    },
                    "lot_identification": {
                        "lot_id": 101,
                        "batch_id": f"BATCH-{selected_fruit.upper()}",
                        "culture_name": selected_fruit,
                        "fruit_type": selected_fruit,
                        "producer": "Produtor Certificado",
                        "current_owner": "Detentor Atual",
                        "current_owner_type": selected_stakeholder,
                        "harvest_date": (datetime.date.today() - datetime.timedelta(days=total_days)).isoformat(),
                        "initial_quantity_kg": 1000.0,
                        "current_stock_kg": 1000.0,
                        "delivered_quantity_kg": 0.0,
                        "initial_metrics": {
                            "soluble_solids_brix": float(b0_val),
                            "firmness": float(f0_val),
                            "acidity": float(a0_val)
                        }
                    },
                    "meteorology_and_imputation_strategy": {
                        "json_fallback_mode": fallback_mode,
                        "fixed_temperature_celsius": float(fixed_temp),
                        "fixed_humidity_percent": float(fixed_rh),
                        "fixed_ethylene_ppm": float(fixed_eth)
                    },
                    "sensor_history_by_warehouse": sensor_history,
                    "plot_info": True
                }

                req = LifecycleDataRequest(**payload)
                res = forecast(req)

                if hasattr(res, "status_code") and res.status_code != 200:
                    st.error("Erro na execução do modelo preditivo.")
                else:
                    st.session_state["simulation_result"] = res.model_dump()
                    st.session_state["simulation_meta"] = {
                        "total_days": total_days,
                        "selected_stakeholder": selected_stakeholder,
                        "min_qual": min_qual,
                        "mold_lim": mold_lim
                    }

# -----------------------------------------------------------------------------
# RIGHT COLUMN: PREDICTIVE COCKPIT & GRAPHS
# -----------------------------------------------------------------------------
with col_right:
    if df_input is None:
        st.markdown("""
        <div class="panel-box" style="text-align: center; padding: 4.5rem 1.5rem; background: #FFFFFF; border-radius: 12px; border: 1px dashed #CBD5E1;">
            <div style="font-size: 3rem; margin-bottom: 0.8rem;">📦</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: #1E293B; margin-bottom: 0.4rem;">
                Aguardando Dados do Lote
            </div>
            <div style="font-size: 0.9rem; color: #64748B; max-width: 440px; margin: 0 auto;">
                Carregue um ficheiro <b>Excel (.xlsx)</b> ou <b>JSON</b> no painel da esquerda para iniciar a análise de vida útil e cinética pós-colheita.
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state.get("simulation_result") is None:
        st.markdown("""
        <div class="panel-box" style="text-align: center; padding: 4.5rem 1.5rem; background: #FFFFFF; border-radius: 12px; border: 1px dashed #CBD5E1;">
            <div style="font-size: 3rem; margin-bottom: 0.8rem;">⚡</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: #1E293B; margin-bottom: 0.4rem;">
                Ficheiro Carregado com Sucesso!
            </div>
            <div style="font-size: 0.9rem; color: #64748B; max-width: 480px; margin: 0 auto 1.2rem auto;">
                Ajuste os parâmetros fisiológicos iniciais e o stakeholder pretendido no painel à esquerda e clique no botão abaixo para gerar as projeções.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        result = st.session_state["simulation_result"]
        meta = st.session_state.get("simulation_meta", {})
        total_days = meta.get("total_days", 0)
        selected_stakeholder = meta.get("selected_stakeholder", selected_stakeholder)
        min_qual = meta.get("min_qual", min_qual)
        mold_lim = meta.get("mold_lim", mold_lim)

        algo = result.get("algorithm")
        algo_badge = "🔬 Modelo COM Etileno (Prof. Luís Paulo - 2D)" if algo == "ode_academic" else "🍃 Modelo SEM Etileno (Sofia Machado - 4D)"
        
        cdata = result.get("continuous_data", {})
        final_q = result.get("quality_index", 0.0)
        comm_life = result.get("commercial_lifetime_remaining", 0.0)
        bio_life = result.get("biological_lifetime_remaining", 0.0)
        final_f = result.get("firmness", 0.0)
        final_b = result.get("brix", 0.0)
        pt_a = result.get("point_a_day", 0.0)
        pt_b = result.get("point_b_day", 0.0)

        # -------------------------------------------------------------
        # EXECUTIVE KPI TILES
        # -------------------------------------------------------------
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-tile">
                <div class="kpi-tile-header">Histórico</div>
                <div class="kpi-tile-number theme-blue">{int(round(total_days))}<span class="kpi-unit">dias</span></div>
                <div class="kpi-subtext">Desde a colheita</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-tile-header">Qualidade Atual</div>
                <div class="kpi-tile-number {'theme-emerald' if final_q >= min_qual else 'theme-rose'}">{final_q:.1f}<span class="kpi-unit">%</span></div>
                <div class="kpi-subtext">{'Aprovado' if final_q >= min_qual else 'Fora de Padrão'}</div>
            </div>
            <div class="kpi-tile" style="border-left: 3px solid #059669;">
                <div class="kpi-tile-header">🟢 Vida Comercial</div>
                <div class="kpi-tile-number theme-emerald">+{int(round(comm_life))}<span class="kpi-unit">dias</span></div>
                <div class="kpi-subtext">Ponto A: Dia {int(round(pt_a))}</div>
            </div>
            <div class="kpi-tile" style="border-left: 3px solid #D97706;">
                <div class="kpi-tile-header">🔴 Vida Biológica</div>
                <div class="kpi-tile-number theme-amber">+{int(round(bio_life))}<span class="kpi-unit">dias</span></div>
                <div class="kpi-subtext">Ponto B: Dia {int(round(pt_b))}</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-tile-header">Firmeza Atual</div>
                <div class="kpi-tile-number theme-indigo">{final_f:.1f}<span class="kpi-unit">N</span></div>
                <div class="kpi-subtext">Resistência mecânica</div>
            </div>
            <div class="kpi-tile">
                <div class="kpi-tile-header">Brix Atual</div>
                <div class="kpi-tile-number theme-amber">{final_b:.1f}<span class="kpi-unit">°Bx</span></div>
                <div class="kpi-subtext">Teor de açúcares</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # -------------------------------------------------------------
        # UNIFIED QUALITY LIFESPAN CHART (HERO PLOT)
        # -------------------------------------------------------------
        if cdata and "t" in cdata and "quality" in cdata:
            t_arr = cdata["t"]
            q_arr = cdata["quality"]

            fig_q = go.Figure()

            # Shaded Background Zones for Visual Wow Factor
            fig_q.add_hrect(
                y0=min_qual, y1=105,
                fillcolor="rgba(16, 185, 129, 0.05)",
                layer="below", line_width=0,
            )
            fig_q.add_hrect(
                y0=30, y1=min_qual,
                fillcolor="rgba(245, 158, 11, 0.04)",
                layer="below", line_width=0,
            )
            fig_q.add_hrect(
                y0=-2, y1=30,
                fillcolor="rgba(239, 68, 68, 0.04)",
                layer="below", line_width=0,
            )

            # Continuous Smooth Quality Curve
            fig_q.add_trace(go.Scatter(
                x=t_arr,
                y=q_arr,
                mode='lines',
                name='Índice de Qualidade (%)',
                line=dict(color='#2563EB', width=3.5),
                hovertemplate="<b>Dia %{x:.0f}</b><br>Qualidade: <b>%{y:.1f}%</b><extra></extra>"
            ))

            # Stakeholder Threshold Dashed Line
            fig_q.add_hline(
                y=min_qual,
                line_dash="dash",
                line_color="#059669",
                line_width=1.8,
                annotation_text=f"Limiar Mínimo {selected_stakeholder} ({min_qual:.0f}%)",
                annotation_position="top right",
                annotation_font=dict(color="#059669", size=11, family="Plus Jakarta Sans")
            )

            # Today Vertical Marker
            fig_q.add_vline(
                x=total_days,
                line_dash="dot",
                line_color="#64748B",
                line_width=1.5,
                annotation_text=f"Hoje (Dia {int(round(total_days))})",
                annotation_position="top left",
                annotation_font=dict(color="#475569", size=10)
            )

            # Marker Point A (Commercial Life Limit)
            if pt_a <= t_arr[-1]:
                idx_a = min(int(pt_a / 0.05), len(q_arr) - 1)
                fig_q.add_trace(go.Scatter(
                    x=[pt_a],
                    y=[q_arr[idx_a]],
                    mode='markers+text',
                    name=f'🟢 Ponto A: Fim Vida Comercial (Dia {int(round(pt_a))})',
                    text=[f"🟢 Ponto A (Dia {int(round(pt_a))})"],
                    textposition="top center",
                    textfont=dict(family="Plus Jakarta Sans", size=11, color="#065F46"),
                    marker=dict(color='#059669', size=14, symbol='circle', line=dict(color='#FFFFFF', width=2.5))
                ))

            # Marker Point B (Biological Decay / 0%)
            if pt_b <= t_arr[-1]:
                fig_q.add_trace(go.Scatter(
                    x=[pt_b],
                    y=[0],
                    mode='markers+text',
                    name=f'🔴 Ponto B: Fim Biológico (Dia {int(round(pt_b))})',
                    text=[f"🔴 Ponto B (Dia {int(round(pt_b))})"],
                    textposition="bottom center",
                    textfont=dict(family="Plus Jakarta Sans", size=11, color="#991B1B"),
                    marker=dict(color='#DC2626', size=14, symbol='diamond', line=dict(color='#FFFFFF', width=2.5))
                ))

            fig_q.update_layout(
                title=dict(
                    text="<b>Trajetória Contínua da Qualidade & Marcos Críticos de Decisão</b>",
                    font=dict(size=15, color="#0F172A", family="Plus Jakarta Sans")
                ),
                height=450,
                xaxis=dict(
                    title="<b>Tempo Total Decorrido (Dias de Armazenamento & Prateleira)</b>",
                    rangemode="tozero",
                    showgrid=True,
                    gridcolor="#F1F5F9"
                ),
                yaxis=dict(
                    title="<b>Qualidade Comercial (%)</b>",
                    range=[-2, 105],
                    rangemode="tozero",
                    showgrid=True,
                    gridcolor="#F1F5F9"
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=10.5)
                ),
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                margin=dict(l=20, r=20, t=50, b=20),
                hovermode="x unified"
            )

            st.plotly_chart(fig_q, use_container_width=True)

        # -------------------------------------------------------------
        # DETAILED PHYSICAL DYNAMICS (ELEGANT TABBED SECTION)
        # -------------------------------------------------------------
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        
        tab_firm, tab_chem, tab_env, tab_bio = st.tabs([
            "📉 Firmeza & Textura",
            "🍬 Açúcares & Acidez",
            "🌡️ Termodinâmica & VPD",
            "💨 Etileno & Cinética Fúngica"
        ])

        with tab_firm:
            if "firmness" in cdata:
                fig_f = go.Figure()
                fig_f.add_trace(go.Scatter(
                    x=t_arr, y=cdata["firmness"],
                    mode='lines', name='Firmeza Estrutural (N)',
                    line=dict(color='#1E40AF', width=2.5),
                    fill='tozeroy', fillcolor='rgba(30, 64, 175, 0.04)'
                ))
                fig_f.add_hline(
                    y=float(preset_data.get("qual_firmness_threshold", 8.0)),
                    line_dash="dot", line_color="#DC2626",
                    annotation_text="Limiar Mínimo Textura", annotation_position="bottom right"
                )
                fig_f.update_layout(
                    height=300, xaxis_title="Dias", yaxis_title="Firmeza (Newtons)",
                    plot_bgcolor="#FFFFFF", margin=dict(l=20, r=20, t=25, b=20),
                    yaxis=dict(rangemode="tozero")
                )
                st.plotly_chart(fig_f, use_container_width=True)

        with tab_chem:
            fig_chem = make_subplots(specs=[[{"secondary_y": True}]])
            if "brix" in cdata:
                fig_chem.add_trace(go.Scatter(
                    x=t_arr, y=cdata["brix"],
                    mode='lines', name='Açúcares (°Brix)',
                    line=dict(color='#D97706', width=2.5)
                ), secondary_y=False)
            if "acidity" in cdata:
                fig_chem.add_trace(go.Scatter(
                    x=t_arr, y=cdata["acidity"],
                    mode='lines', name='Acidez Titulável (%)',
                    line=dict(color='#DC2626', width=2.5, dash='dash')
                ), secondary_y=True)
            fig_chem.update_layout(
                height=300, xaxis_title="Dias", plot_bgcolor="#FFFFFF",
                margin=dict(l=20, r=20, t=25, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig_chem.update_yaxes(title_text="Açúcares (°Bx)", secondary_y=False, rangemode="tozero")
            fig_chem.update_yaxes(title_text="Acidez (%)", secondary_y=True, rangemode="tozero")
            st.plotly_chart(fig_chem, use_container_width=True)

        with tab_env:
            fig_env = make_subplots(specs=[[{"secondary_y": True}]])
            if "temperature" in cdata:
                fig_env.add_trace(go.Scatter(
                    x=t_arr, y=cdata["temperature"],
                    mode='lines', name='Temperatura (°C)',
                    line=dict(color='#7C3AED', width=2.2)
                ), secondary_y=False)
            if "humidity" in cdata:
                fig_env.add_trace(go.Scatter(
                    x=t_arr, y=cdata["humidity"],
                    mode='lines', name='Humidade Relativa (%)',
                    line=dict(color='#0EA5E9', width=2.2, dash='dot')
                ), secondary_y=True)
            fig_env.update_layout(
                height=300, xaxis_title="Dias", plot_bgcolor="#FFFFFF",
                margin=dict(l=20, r=20, t=25, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig_env.update_yaxes(title_text="Temperatura (°C)", secondary_y=False)
            fig_env.update_yaxes(title_text="Humidade (%)", secondary_y=True, range=[0, 105])
            st.plotly_chart(fig_env, use_container_width=True)

        with tab_bio:
            fig_bio = make_subplots(specs=[[{"secondary_y": True}]])
            if "mold" in cdata:
                fig_bio.add_trace(go.Scatter(
                    x=t_arr, y=[m*100 for m in cdata["mold"]],
                    mode='lines', name='Incidência de Bolor (%)',
                    line=dict(color='#475569', width=2.5)
                ), secondary_y=False)
            if "ethylene" in cdata:
                fig_bio.add_trace(go.Scatter(
                    x=t_arr, y=cdata["ethylene"],
                    mode='lines', name='Etileno Total (ppm)',
                    line=dict(color='#F59E0B', width=2.5, dash='dash')
                ), secondary_y=True)
            fig_bio.update_layout(
                height=300, xaxis_title="Dias", plot_bgcolor="#FFFFFF",
                margin=dict(l=20, r=20, t=25, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig_bio.update_yaxes(title_text="Bolor (%)", secondary_y=False, rangemode="tozero")
            fig_bio.update_yaxes(title_text="Etileno (ppm)", secondary_y=True, rangemode="tozero")
            st.plotly_chart(fig_bio, use_container_width=True)

