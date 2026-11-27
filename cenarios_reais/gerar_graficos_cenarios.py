r"""
gerar_graficos_cenarios.py

Automação para correr o modelo preditivo (LC_model_v0_2_0.py) sobre todos os
cenários em 'cenarios_reais/' (amostra_macas_normal, ensaio_macas_20c,
amostra_camaras_macas, babykiwi_retaill), comparar Estimado vs. Real usando
Plotly (mesmo estilo da UI) e exportar os gráficos (.png) + tabela resumo de
erros (.xlsx) para 'cenarios_reais/resultados/'.

Nota: O ponto inicial (T0) é usado apenas como condição inicial (F0, B0, A0) do
modelo e NÃO é desenhado como ponto real no gráfico nem incluído no erro.

Uso:
    .\.venv\Scripts\python.exe cenarios_reais\gerar_graficos_cenarios.py
    .\.venv\Scripts\python.exe cenarios_reais\gerar_graficos_cenarios.py --grupo amostra_macas_normal
    .\.venv\Scripts\python.exe cenarios_reais\gerar_graficos_cenarios.py --grupo ensaio_macas_20c
    .\.venv\Scripts\python.exe cenarios_reais\gerar_graficos_cenarios.py --grupo amostra_camaras_macas --apenas-medias
    .\.venv\Scripts\python.exe cenarios_reais\gerar_graficos_cenarios.py --grupo babykiwi_retaill
"""

import os
import sys
import re
import glob
import math
import json
import base64
import asyncio
import tempfile
import argparse
import datetime
import pandas as pd
import openpyxl
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import choreographer

CENARIOS_REAIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(CENARIOS_REAIS_DIR)
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from LC_model_v0_2_0 import (
    PRESETS,
    forecast,
    LifecycleDataRequest,
    get_stakeholder_config,
)

KG_TO_N = 9.80665
BASE_DIR = REPO_DIR

PLOT_WIDTH = 780
PLOT_HEIGHT = 320


def parse_any_date(val):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    if isinstance(val, datetime.datetime):
        return val.date()
    if isinstance(val, datetime.date):
        return val
    s = str(val).strip()
    if not s or s == "-":
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(s[:10], fmt).date()
        except ValueError:
            pass
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.notnull(dt):
            return dt.date()
    except Exception:
        pass
    return None


def to_float(val):
    if val is None or isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        if math.isnan(val):
            return None
        return float(val)
    s = str(val).strip().replace("%", "").replace("°Bx", "").replace("ºBx", "").strip()
    if not s or s == "-" or s.lower() == "nan":
        return None
    try:
        return float(s)
    except ValueError:
        return None


class PlotlyRenderer:
    """Renderiza figuras Plotly em PNG usando uma única instância headless via choreographer."""

    def __init__(self, width=PLOT_WIDTH, height=PLOT_HEIGHT, scale=2):
        self.width = width
        self.height = height
        self.scale = scale
        self._loop = asyncio.new_event_loop()
        self._browser = None
        self._tab = None
        self._html_path = None

    def __enter__(self):
        plotly_js = os.path.join(os.path.dirname(plotly.__file__), "package_data", "plotly.min.js")
        plotly_js_url = "file:///" + plotly_js.replace("\\", "/")
        fd, self._html_path = tempfile.mkstemp(suffix=".html")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(
                f'<!DOCTYPE html><html><head><meta charset="utf-8">'
                f'<script src="{plotly_js_url}"></script></head>'
                f'<body style="margin:0;background:#FFFFFF;">'
                f'<div id="gd" style="width:{self.width}px;height:{self.height}px;"></div>'
                f'</body></html>'
            )

        async def _start():
            self._browser = await choreographer.Browser(headless=True)
            tab_url = "file:///" + self._html_path.replace("\\", "/")
            self._tab = await self._browser.create_tab(tab_url)
            await self._tab.send_command(
                "Emulation.setDeviceMetricsOverride",
                {
                    "width": 1200,
                    "height": 600,
                    "deviceScaleFactor": self.scale,
                    "mobile": False,
                },
            )
            await asyncio.sleep(0.5)

        self._loop.run_until_complete(_start())
        return self

    def save_png(self, fig: go.Figure, out_path: str, width=None, height=None):
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        w = int(width or self.width)
        h = int(height or self.height)
        fig_dict = fig.to_plotly_json()
        fig_dict.setdefault("layout", {})
        fig_dict["layout"]["width"] = w
        fig_dict["layout"]["height"] = h
        payload_json = json.dumps(fig_dict, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))

        async def _render():
            js = (
                f"(function() {{"
                f"  var gd = document.getElementById('gd');"
                f"  gd.style.width = '{w}px'; gd.style.height = '{h}px';"
                f"  var spec = {payload_json};"
                f"  return Plotly.react(gd, spec.data, spec.layout).then(function() {{"
                f"    return new Promise(function(resolve) {{"
                f"      requestAnimationFrame(function() {{ requestAnimationFrame(resolve); }});"
                f"    }});"
                f"  }});"
                f"}})()"
            )
            await self._tab.send_command("Runtime.evaluate", {"expression": js, "awaitPromise": True})
            res = await self._tab.send_command(
                "Page.captureScreenshot",
                {
                    "format": "png",
                    "clip": {"x": 0, "y": 0, "width": w, "height": h, "scale": 1},
                },
            )
            return base64.b64decode(res["result"]["data"])

        png_bytes = self._loop.run_until_complete(_render())
        with open(out_path, "wb") as f:
            f.write(png_bytes)

    def __exit__(self, exc_type, exc_val, exc_tb):
        async def _close():
            if self._browser is not None:
                await self._browser.close()

        try:
            self._loop.run_until_complete(_close())
        finally:
            self._loop.close()
            if self._html_path and os.path.exists(self._html_path):
                try:
                    os.remove(self._html_path)
                except OSError:
                    pass


def run_model(df_cenario, fruit_key, f0, b0, a0, stakeholder="Retailer"):
    df_cenario = df_cenario.copy()
    if "Segment_ID" not in df_cenario.columns:
        df_cenario["Segment_ID"] = 1

    sensor_history = []
    for seg_id, group in df_cenario.groupby("Segment_ID", sort=False):
        daily_readings = []
        for _, row in group.iterrows():
            r_dt = parse_any_date(row.get("Date"))
            r_date = r_dt.isoformat() if r_dt else datetime.date.today().isoformat()
            reading = {"date": r_date, "source": "SIMULATION_INPUT"}
            if pd.notnull(row.get("Temperature_C")):
                reading["temperature_celsius"] = float(row["Temperature_C"])
            if pd.notnull(row.get("Humidity_Percent")):
                reading["humidity_percent"] = float(row["Humidity_Percent"])
            if "Ethylene_ppm" in row and pd.notnull(row.get("Ethylene_ppm")):
                reading["ethylene_ppm"] = float(row["Ethylene_ppm"])
            daily_readings.append(reading)

        first_row = group.iloc[0]
        first_dt = parse_any_date(first_row.get("Date"))
        first_date = first_dt.isoformat() if first_dt else datetime.date.today().isoformat()

        sensor_history.append({
            "warehouse_id": int(seg_id),
            "warehouse_location": f"Armazém {int(seg_id)}",
            "meteo_source": "SIMULATION",
            "region": str(first_row.get("Region", "PT-LVT")),
            "total_days_recorded": len(group),
            "packaging_method": str(first_row.get("Packaging", "bulk")),
            "starting_date": first_date,
            "daily_readings": daily_readings,
        })

    total_days = sum(sh["total_days_recorded"] for sh in sensor_history)
    payload = {
        "version": "1.0",
        "export_metadata": {
            "generated_at": datetime.datetime.now().isoformat(),
            "days_elapsed_total": total_days,
        },
        "lot_identification": {
            "lot_id": 101,
            "batch_id": f"BATCH-{fruit_key.upper()}",
            "culture_name": fruit_key,
            "fruit_type": fruit_key,
            "producer": "Produtor Certificado",
            "current_owner": "Detentor Atual",
            "current_owner_type": stakeholder,
            "harvest_date": (datetime.date.today() - datetime.timedelta(days=total_days)).isoformat(),
            "initial_quantity_kg": 1000.0,
            "current_stock_kg": 1000.0,
            "delivered_quantity_kg": 0.0,
            "initial_metrics": {
                "soluble_solids_brix": float(b0),
                "firmness": float(f0),
                "acidity": float(a0),
            },
        },
        "meteorology_and_imputation_strategy": {
            "json_fallback_mode": "IPMA",
            "fixed_temperature_celsius": 4.0,
            "fixed_humidity_percent": 90.0,
            "fixed_ethylene_ppm": 0.0,
        },
        "sensor_history_by_warehouse": sensor_history,
        "plot_info": True,
    }
    req = LifecycleDataRequest(**payload)
    res = forecast(req)
    return res.model_dump()


def build_quality_figure(t_arr, q_arr, min_qual, stakeholder, total_days, pt_a, pt_b):
    """Replica fielmente o gráfico de qualidade da plataforma ui.py."""
    fig_q = go.Figure()

    # Shaded Background Zones
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
        y0=-12, y1=30,
        fillcolor="rgba(239, 68, 68, 0.04)",
        layer="below", line_width=0,
    )

    # Continuous Smooth Quality Curve
    fig_q.add_trace(go.Scatter(
        x=t_arr,
        y=q_arr,
        mode="lines",
        name="Índice de Qualidade (%)",
        line=dict(color="#2563EB", width=3.5),
    ))

    # Stakeholder Threshold Dashed Line
    fig_q.add_hline(
        y=min_qual,
        line_dash="dash",
        line_color="#059669",
        line_width=1.8,
        annotation_text=f"Limiar Mínimo {stakeholder} ({min_qual:.0f}%)",
        annotation_position="top right",
        annotation_font=dict(color="#059669", size=11, family="Plus Jakarta Sans"),
    )

    # Today Vertical Marker
    fig_q.add_vline(
        x=total_days,
        line_dash="dot",
        line_color="#64748B",
        line_width=1.5,
        annotation_text=f"Hoje (Dia {int(round(total_days))})",
        annotation_position="top left",
        annotation_font=dict(color="#475569", size=10),
    )

    # Marker Point A (Commercial Life Limit)
    if pt_a <= t_arr[-1]:
        idx_a = min(int(round(pt_a / 0.05)), len(q_arr) - 1)
        fig_q.add_trace(go.Scatter(
            x=[pt_a],
            y=[q_arr[idx_a]],
            mode="markers+text",
            name=f"🟢 Ponto A: Fim Vida Comercial (Dia {int(round(pt_a))})",
            text=[f"🟢 Ponto A (Dia {int(round(pt_a))})"],
            textposition="top center",
            textfont=dict(family="Plus Jakarta Sans", size=11, color="#065F46"),
            marker=dict(color="#059669", size=14, symbol="circle", line=dict(color="#FFFFFF", width=2.5)),
            cliponaxis=False,
        ))

    # Marker Point B (Biological Decay / 0%)
    if pt_b <= t_arr[-1]:
        fig_q.add_trace(go.Scatter(
            x=[pt_b],
            y=[0],
            mode="markers+text",
            name=f"🔴 Ponto B: Fim Biológico (Dia {int(round(pt_b))})",
            text=[f"🔴 Ponto B (Dia {int(round(pt_b))})"],
            textposition="bottom center",
            textfont=dict(family="Plus Jakarta Sans", size=11, color="#991B1B"),
            marker=dict(color="#DC2626", size=14, symbol="diamond", line=dict(color="#FFFFFF", width=2.5)),
            cliponaxis=False,
        ))

    fig_q.update_layout(
        title=dict(
            text="<b>Trajetória Contínua da Qualidade & Marcos Críticos de Decisão</b>",
            font=dict(size=15, color="#0F172A", family="Plus Jakarta Sans"),
            x=0.02,
            xanchor="left",
            y=0.97,
            yanchor="top",
        ),
        height=480,
        xaxis=dict(
            title="<b>Tempo Total Decorrido (Dias de Armazenamento & Prateleira)</b>",
            range=[0, max(float(t_arr[-1]), 1.0) * 1.06],
            rangemode="tozero",
            showgrid=True,
            gridcolor="#F1F5F9",
            automargin=True,
        ),
        yaxis=dict(
            title="<b>Qualidade Comercial (%)</b>",
            range=[-12, 108],
            rangemode="tozero",
            showgrid=True,
            gridcolor="#F1F5F9",
            automargin=True,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.0,
            font=dict(size=10.5),
        ),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=65, r=40, t=95, b=60),
    )
    return fig_q


def _slice_to_x_max(t_arr, y_arr, x_max):
    """Corta as séries estimadas exatamente no último ponto real (x_max)."""
    if x_max is None or not t_arr:
        return t_arr, y_arr
    cut_idx = max(1, min(len(t_arr), day_to_idx(x_max, len(t_arr)) + 1))
    return t_arr[:cut_idx], y_arr[:cut_idx]


def _add_mae_annotation(fig, mae, unit=""):
    """Adiciona uma observação com o Erro (MAE) no topo esquerdo do gráfico."""
    if mae is None:
        return
    label = f"<b>Erro (MAE): {mae:.2f} {unit}</b>" if unit else f"<b>Erro (MAE): {mae:.2f}</b>"
    fig.add_annotation(
        text=label,
        xref="paper",
        yref="paper",
        x=0.0,
        y=1.02,
        xanchor="left",
        yanchor="bottom",
        showarrow=False,
        font=dict(size=11, color="#0F172A"),
        bgcolor="#F8FAFC",
        bordercolor="#CBD5E1",
        borderwidth=1,
        borderpad=4,
    )


def build_firmness_figure(t_arr, cdata, fx, fy, threshold, x_max=None, mae=None):
    x_end = x_max if x_max is not None else (max(fx) if fx else float(t_arr[-1]))
    t_plot, f_plot = _slice_to_x_max(t_arr, cdata["firmness"], x_end)

    fig_f = go.Figure()
    fig_f.add_trace(
        go.Scatter(
            x=t_plot,
            y=f_plot,
            mode="lines",
            name="Firmeza Estimada (N)",
            line=dict(color="#1E40AF", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(30, 64, 175, 0.04)",
        )
    )
    if fx:
        fig_f.add_trace(
            go.Scatter(
                x=fx,
                y=fy,
                mode="markers",
                name="Firmeza Real (N)",
                marker=dict(color="#DC2626", size=10, symbol="diamond"),
                cliponaxis=False,
            )
        )
    fig_f.add_hline(
        y=threshold,
        line_dash="dot",
        line_color="#DC2626",
        annotation_text="Limiar Mínimo Textura",
        annotation_position="bottom right",
    )
    _add_mae_annotation(fig_f, mae, unit="N")
    fig_f.update_layout(
        showlegend=False,
        xaxis_title="Dias",
        yaxis_title="Firmeza (Newtons)",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=55, r=30, t=38, b=45),
        yaxis=dict(rangemode="tozero", gridcolor="#E2E8F0"),
        xaxis=dict(range=[0, max(float(x_end), 1.0)], rangemode="tozero", gridcolor="#E2E8F0"),
    )
    return fig_f


def build_chem_figure(t_arr, cdata, bx, by, ax, ay, active="brix", x_max=None, mae=None):
    brix_vis = True if active == "brix" else "legendonly"
    acid_vis = True if active == "acidity" else "legendonly"

    active_x = bx if active == "brix" else ax
    x_end = x_max if x_max is not None else (max(active_x) if active_x else float(t_arr[-1]))

    fig_chem = make_subplots(specs=[[{"secondary_y": True}]])
    if "brix" in cdata:
        t_plot_b, b_plot = _slice_to_x_max(t_arr, cdata["brix"], x_end)
        fig_chem.add_trace(
            go.Scatter(
                x=t_plot_b,
                y=b_plot,
                mode="lines",
                name="Açúcares Estimado (°Bx)",
                line=dict(color="#D97706", width=2.5),
                visible=brix_vis,
            ),
            secondary_y=False,
        )
        if bx:
            fig_chem.add_trace(
                go.Scatter(
                    x=bx,
                    y=by,
                    mode="markers",
                    name="Brix Real",
                    marker=dict(color="#D97706", size=9, symbol="circle"),
                    visible=brix_vis,
                    cliponaxis=False,
                ),
                secondary_y=False,
            )
    if "acidity" in cdata:
        t_plot_a, a_plot = _slice_to_x_max(t_arr, cdata["acidity"], x_end)
        fig_chem.add_trace(
            go.Scatter(
                x=t_plot_a,
                y=a_plot,
                mode="lines",
                name="Acidez Estimada (%)",
                line=dict(color="#DC2626", width=2.5, dash="dash"),
                visible=acid_vis,
            ),
            secondary_y=True,
        )
        if ax:
            fig_chem.add_trace(
                go.Scatter(
                    x=ax,
                    y=ay,
                    mode="markers",
                    name="Acidez Real",
                    marker=dict(color="#DC2626", size=9, symbol="square"),
                    visible=acid_vis,
                    cliponaxis=False,
                ),
                secondary_y=True,
            )
    unit = "°Bx" if active == "brix" else "%"
    _add_mae_annotation(fig_chem, mae, unit=unit)
    fig_chem.update_layout(
        xaxis_title="Dias",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=55, r=55, t=42, b=45),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(range=[0, max(float(x_end), 1.0)], rangemode="tozero", gridcolor="#E2E8F0"),
    )
    fig_chem.update_yaxes(title_text="Açúcares (°Bx)", secondary_y=False, rangemode="tozero", gridcolor="#E2E8F0")
    fig_chem.update_yaxes(title_text="Acidez (%)", secondary_y=True, rangemode="tozero", showgrid=False)
    return fig_chem


def day_to_idx(day: float, t_len: int, dt: float = 0.05) -> int:
    return max(0, min(int(round(day / dt)), t_len - 1))


def calc_mae(abs_errors):
    if not abs_errors:
        return None
    return sum(abs_errors) / len(abs_errors)


def evaluate_and_save_case(
    renderer: PlotlyRenderer,
    grupo,
    cenario_nome,
    caso_nome,
    df_cenario,
    fruit_key,
    real_points,
    out_dir,
    stakeholder="Retailer",
):
    """
    real_points: lista ordenada cronologicamente; o primeiro ponto (T0) define
    F0/B0/A0 e os restantes pontos (real_points[1:]) são desenhados no gráfico.
    """
    if not real_points:
        return None

    preset = PRESETS[fruit_key]
    scen_dates = [parse_any_date(d) for d in df_cenario["Date"] if parse_any_date(d) is not None]
    start_dt = min(scen_dates)

    # Valores iniciais T0 (apenas para arrancar o modelo, NÃO entram nos pontos do gráfico)
    t0_point = real_points[0]
    f0 = t0_point.get("firmness") if t0_point.get("firmness") is not None else float(preset.get("firmness_0_default", 50.0))
    b0 = t0_point.get("brix") if t0_point.get("brix") is not None else float(preset.get("brix_0_default", 12.0))
    a0 = t0_point.get("acidity") if t0_point.get("acidity") is not None else float(preset.get("acidity_0_default", 0.5))

    res = run_model(df_cenario, fruit_key, f0, b0, a0, stakeholder=stakeholder)
    cdata = res.get("continuous_data", {})
    t_arr = cdata.get("t", [])
    if not t_arr:
        return None

    eval_points = real_points[1:]

    def _xy(metric):
        xs, ys = [], []
        for p in eval_points:
            if p.get(metric) is not None and p.get("date") is not None:
                xs.append(float((p["date"] - start_dt).days))
                ys.append(float(p[metric]))
        return xs, ys

    def _abs_errors(metric):
        errs = []
        if metric not in cdata:
            return errs
        arr = cdata[metric]
        for p in eval_points:
            if p.get(metric) is not None and p.get("date") is not None:
                d = float((p["date"] - start_dt).days)
                idx = day_to_idx(d, len(t_arr))
                errs.append(abs(float(arr[idx]) - float(p[metric])))
        return errs

    if "quality" in cdata:
        st_cfg = get_stakeholder_config(fruit_key, stakeholder)
        min_qual = float(st_cfg["min_quality"])
        total_days = len(df_cenario)
        pt_a = float(res.get("point_a_day", 0.0))
        pt_b = float(res.get("point_b_day", 0.0))
        fig_q = build_quality_figure(
            t_arr,
            cdata["quality"],
            min_qual,
            stakeholder,
            total_days,
            pt_a,
            pt_b,
        )
        renderer.save_png(fig_q, os.path.join(out_dir, "qualidade.png"), width=1050, height=480)

    fx, fy = _xy("firmness")
    bx, by = _xy("brix")
    ax, ay = _xy("acidity")

    abs_f = _abs_errors("firmness")
    abs_b = _abs_errors("brix")
    abs_a = _abs_errors("acidity")
    mae_f = calc_mae(abs_f)
    mae_b = calc_mae(abs_b)
    mae_a = calc_mae(abs_a)

    if "firmness" in cdata:
        fig_f = build_firmness_figure(
            t_arr,
            cdata,
            fx,
            fy,
            float(preset.get("qual_firmness_threshold", 8.0)),
            x_max=max(fx) if fx else None,
            mae=mae_f,
        )
        renderer.save_png(fig_f, os.path.join(out_dir, "firmeza.png"))

    if "brix" in cdata:
        fig_brix = build_chem_figure(
            t_arr, cdata, bx, by, ax, ay, active="brix",
            x_max=max(bx) if bx else None,
            mae=mae_b,
        )
        renderer.save_png(fig_brix, os.path.join(out_dir, "brix.png"))

    if "acidity" in cdata:
        if ax:
            fig_acid = build_chem_figure(
                t_arr, cdata, bx, by, ax, ay, active="acidity",
                x_max=max(ax),
                mae=mae_a,
            )
            renderer.save_png(fig_acid, os.path.join(out_dir, "acidez.png"))

    return {
        "grupo": grupo,
        "cenario": cenario_nome,
        "caso": caso_nome,
        "fruit_key": fruit_key,
        "stakeholder": stakeholder,
        "n_firmness": len(abs_f),
        "mae_firmness": mae_f,
        "n_brix": len(abs_b),
        "mae_brix": mae_b,
        "n_acidity": len(abs_a),
        "mae_acidity": mae_a,
        "_abs_firmness": abs_f,
        "_abs_brix": abs_b,
        "_abs_acidity": abs_a,
    }


def read_ess_sheet_points(xlsx_path, sheet_name, amostra_prefix=None):
    """Lê uma folha numérica de amostra_normal_ess ou ensaio_20c."""
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
    points = []
    for _, row in df.iterrows():
        amostra = str(row.get("Amostra", "")).strip()
        if amostra_prefix is not None:
            if not (amostra == amostra_prefix or amostra.startswith(amostra_prefix + ".")):
                continue
        dt = parse_any_date(row.get("Data Real"))
        if dt is None:
            continue
        points.append({
            "amostra": amostra,
            "date": dt,
            "firmness": to_float(row.get("Firmeza Média (N)")),
            "brix": to_float(row.get("Brix (°Bx)")),
            "acidity": to_float(row.get("Acidez (%)")),
        })
    return points


def process_amostra_normal_ess(renderer, out_root, stakeholder):
    base = os.path.join(CENARIOS_REAIS_DIR, "amostra_macas_normal")
    vr_dir = os.path.join(base, "valores_reais")
    rows = []

    configs = [
        ("gala", "apple_gala", "cenario_maca_gala_amostra_normal_ess.xlsx", "Dados_Numericos_Gala"),
        ("golden", "apple_golden", "cenario_maca_golden_amostra_normal_ess.xlsx", "Dados_Numericos_Golden"),
    ]

    for sp_slug, fruit_key, scen_file, sp_sheet in configs:
        df_scen = pd.read_excel(os.path.join(base, scen_file))
        scen_label = f"amostra_macas_normal_{sp_slug}"

        pts_sp = read_ess_sheet_points(os.path.join(vr_dir, "medias_por_especie.xlsx"), sp_sheet)
        r = evaluate_and_save_case(
            renderer, "amostra_macas_normal", scen_label, "media_especie", df_scen, fruit_key, pts_sp,
            os.path.join(out_root, "amostra_macas_normal", sp_slug, "media_especie"), stakeholder
        )
        if r:
            rows.append(r)

        for prod in ("amps", "cjl"):
            prod_sheet = f"{sp_slug.capitalize()}_{prod.upper()}"
            pts_prod = read_ess_sheet_points(os.path.join(vr_dir, "medias_por_produtor.xlsx"), prod_sheet)
            r = evaluate_and_save_case(
                renderer, "amostra_macas_normal", scen_label, f"media_{prod}", df_scen, fruit_key, pts_prod,
                os.path.join(out_root, "amostra_macas_normal", sp_slug, f"media_{prod}"), stakeholder
            )
            if r:
                rows.append(r)

            ind_file = os.path.join(vr_dir, f"valores_reais_{sp_slug}_{prod}.xlsx")
            for m_idx in range(1, 6):
                pts_m = read_ess_sheet_points(ind_file, f"Maca_{m_idx}")
                caso = f"maca_{m_idx}_{prod}_{sp_slug}"
                r = evaluate_and_save_case(
                    renderer, "amostra_macas_normal", scen_label, caso, df_scen, fruit_key, pts_m,
                    os.path.join(out_root, "amostra_macas_normal", caso), stakeholder
                )
                if r:
                    rows.append(r)

    return rows


def process_ensaio_20c(renderer, out_root, stakeholder):
    base = os.path.join(CENARIOS_REAIS_DIR, "ensaio_macas_20c")
    vr_dir = os.path.join(base, "valores_reais")
    rows = []

    scen_files = sorted(glob.glob(os.path.join(base, "cenario_*.xlsx")))
    for sf in scen_files:
        fname = os.path.basename(sf)
        m = re.search(r"cenario_maca_(gala|golden)_(t\d+)_", fname)
        if not m:
            continue
        sp_slug = m.group(1)
        traj = m.group(2).upper()
        fruit_key = "apple_gala" if sp_slug == "gala" else "apple_golden"
        sp_sheet = f"Dados_Numericos_{sp_slug.capitalize()}"
        scen_label = fname.replace("cenario_", "").replace(".xlsx", "")
        df_scen = pd.read_excel(sf)

        pts_sp = read_ess_sheet_points(os.path.join(vr_dir, "medias_por_especie.xlsx"), sp_sheet, amostra_prefix=traj)
        if pts_sp:
            r = evaluate_and_save_case(
                renderer, "ensaio_macas_20c", scen_label, "media_especie", df_scen, fruit_key, pts_sp,
                os.path.join(out_root, "ensaio_macas_20c", scen_label, "media_especie"), stakeholder
            )
            if r:
                rows.append(r)

        for prod in ("amps", "cjl"):
            prod_sheet = f"{sp_slug.capitalize()}_{prod.upper()}"
            pts_prod = read_ess_sheet_points(os.path.join(vr_dir, "medias_por_produtor.xlsx"), prod_sheet, amostra_prefix=traj)
            if pts_prod:
                r = evaluate_and_save_case(
                    renderer, "ensaio_macas_20c", scen_label, f"media_{prod}", df_scen, fruit_key, pts_prod,
                    os.path.join(out_root, "ensaio_macas_20c", scen_label, f"media_{prod}"), stakeholder
                )
                if r:
                    rows.append(r)

            ind_file = os.path.join(vr_dir, f"valores_reais_{sp_slug}_{prod}.xlsx")
            for m_idx in range(1, 6):
                pts_m = read_ess_sheet_points(ind_file, f"Maca_{m_idx}", amostra_prefix=traj)
                if pts_m:
                    caso = f"maca_{m_idx}_{prod}"
                    r = evaluate_and_save_case(
                        renderer, "ensaio_macas_20c", scen_label, caso, df_scen, fruit_key, pts_m,
                        os.path.join(out_root, "ensaio_macas_20c", scen_label, caso), stakeholder
                    )
                    if r:
                        rows.append(r)

    return rows


def _read_section_rows(ws, title_prefix):
    """Lê dinamicamente as linhas de dados de uma secção de Valores_Reais até à primeira linha em branco."""
    rows = []
    for r in range(1, ws.max_row + 1):
        val = str(ws.cell(r, 1).value or "").strip()
        if val.startswith(title_prefix):
            curr = r + 2  # Salta título da secção e cabeçalho da tabela
            while curr <= ws.max_row:
                label = ws.cell(curr, 1).value
                if label is None or str(label).strip() == "":
                    break
                rows.append(curr)
                curr += 1
            break
    return rows


def process_amostra_camaras(renderer, out_root, stakeholder, apenas_medias=False):
    base = os.path.join(CENARIOS_REAIS_DIR, "amostra_camaras_macas")
    lote_dirs = sorted(
        d for d in glob.glob(os.path.join(base, "cenario_*")) + glob.glob(os.path.join(base, "lote_*"))
        if os.path.isdir(d)
    )
    rows = []

    for ldir in lote_dirs:
        if not os.path.isdir(ldir):
            continue
        lote_name = os.path.basename(ldir)
        fruit_key = "apple_gala" if "_gala_" in lote_name.lower() else "apple_golden"

        scen_files = glob.glob(os.path.join(ldir, "cenario_*.xlsx"))
        vr_files = glob.glob(os.path.join(ldir, "valores_reais_*.xlsx"))
        if not scen_files or not vr_files:
            continue

        df_scen = pd.read_excel(scen_files[0])
        wb = openpyxl.load_workbook(vr_files[0], data_only=True)
        ws = wb["Valores_Reais"]

        sintese_rows = _read_section_rows(ws, "1. Síntese")
        pts_media = []
        for r_idx in sintese_rows:
            dt = parse_any_date(ws.cell(r_idx, 2).value)
            if dt is None:
                continue
            pts_media.append({
                "date": dt,
                "firmness": to_float(ws.cell(r_idx, 5).value),
                "brix": to_float(ws.cell(r_idx, 6).value),
                "acidity": to_float(ws.cell(r_idx, 7).value),
            })

        r = evaluate_and_save_case(
            renderer, "amostra_camaras_macas", lote_name, "media_lote", df_scen, fruit_key, pts_media,
            os.path.join(out_root, "amostra_camaras_macas", lote_name, "media_lote"), stakeholder
        )
        if r:
            rows.append(r)

        if apenas_medias:
            continue

        firmeza_rows = _read_section_rows(ws, "2. Firmeza")
        brix_rows = _read_section_rows(ws, "3. Teor")
        ac_t0 = pts_media[0]["acidity"] if pts_media else None
        brix_t0_media = pts_media[0]["brix"] if pts_media else None

        n_pts = max(len(firmeza_rows), len(brix_rows))
        for f_idx in range(1, 11):
            col = 2 + f_idx
            pts_fruto = []
            for p_i in range(n_pts):
                r_f = firmeza_rows[p_i] if p_i < len(firmeza_rows) else None
                r_b = brix_rows[p_i] if p_i < len(brix_rows) else None

                dt_f = parse_any_date(ws.cell(r_f, 2).value) if r_f else None
                dt_b = parse_any_date(ws.cell(r_b, 2).value) if r_b else None
                dt = dt_f or dt_b
                if dt is None:
                    continue

                f_kg = to_float(ws.cell(r_f, col).value) if r_f else None
                b_val = to_float(ws.cell(r_b, col).value) if r_b else None
                if p_i == 0 and b_val is None:
                    b_val = brix_t0_media

                pts_fruto.append({
                    "date": dt,
                    "firmness": f_kg * KG_TO_N if f_kg is not None else None,
                    "brix": b_val,
                    "acidity": ac_t0 if p_i == 0 else None,
                })

            caso = f"fruto_{f_idx:02d}"
            r = evaluate_and_save_case(
                renderer, "amostra_camaras_macas", lote_name, caso, df_scen, fruit_key, pts_fruto,
                os.path.join(out_root, "amostra_camaras_macas", lote_name, caso), stakeholder
            )
            if r:
                rows.append(r)

    return rows


def read_babykiwi_sheet_blocks(xlsx_path, sheet_name):
    """Lê blocos de tabelas de medias_babykiwi.xlsx (1 bloco em T1/T2/T3; 5 blocos em T4/T5)."""
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb[sheet_name]
    blocks = []
    current = None

    for r in range(1, ws.max_row + 1):
        c1 = ws.cell(r, 1).value
        if c1 is None:
            continue
        s1 = str(c1).strip()
        if s1.startswith("BABYKIWI") or s1.startswith("Trajetória"):
            if current:
                blocks.append(current)
            current = {"title": s1, "points": []}
            continue
        if s1 == "Amostra":
            continue
        dt = parse_any_date(ws.cell(r, 4).value)
        if dt is None or current is None:
            continue
        current["points"].append({
            "amostra": s1,
            "date": dt,
            "firmness": to_float(ws.cell(r, 5).value),
            "brix": to_float(ws.cell(r, 8).value),
            "acidity": to_float(ws.cell(r, 10).value),
        })

    if current:
        blocks.append(current)
    wb.close()
    return blocks


def process_babykiwi_retaill(renderer, out_root, stakeholder):
    base = os.path.join(CENARIOS_REAIS_DIR, "babykiwi_retaill")
    medias_xlsx = os.path.join(base, "valores_reais", "medias_babykiwi.xlsx")
    if not os.path.exists(medias_xlsx):
        return []

    rows = []
    fruit_key = "kiwi_baby"

    configs = [
        ("cenario_babykiwi_t1_2c.xlsx", "T1_2C"),
        ("cenario_babykiwi_t2_5c.xlsx", "T2_5C"),
        ("cenario_babykiwi_t3_20c.xlsx", "T3_20C"),
        ("cenario_babykiwi_t4_2_20c.xlsx", "T4_2_20C"),
        ("cenario_babykiwi_t5_5_20c.xlsx", "T5_5_20C"),
    ]
    for scen_file, sheet_name in configs:
        sf = os.path.join(base, scen_file)
        if not os.path.exists(sf):
            continue
        df_scen = pd.read_excel(sf)
        scen_label = scen_file.replace("cenario_", "").replace(".xlsx", "")
        blocks = read_babykiwi_sheet_blocks(medias_xlsx, sheet_name)
        if not blocks or not blocks[0]["points"]:
            continue
        r = evaluate_and_save_case(
            renderer, "babykiwi_retaill", scen_label, "media", df_scen, fruit_key, blocks[0]["points"],
            os.path.join(out_root, "babykiwi_retaill", scen_label, "media"), stakeholder
        )
        if r:
            rows.append(r)

    return rows


def export_mae_summary_excel(all_rows, out_dir):
    """Exporta resumo_erros.xlsx com o MAE por caso e agregado por grupo."""
    if not all_rows:
        return None

    casos_clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in all_rows]
    df_casos = pd.DataFrame(casos_clean)

    def _agg_group(label, subset):
        abs_f = [e for r in subset for e in r["_abs_firmness"]]
        abs_b = [e for r in subset for e in r["_abs_brix"]]
        abs_a = [e for r in subset for e in r["_abs_acidity"]]
        return {
            "Grupo": label,
            "N_Casos": len(subset),
            "N_Firmness": len(abs_f),
            "MAE_Firmness_N": calc_mae(abs_f),
            "N_Brix": len(abs_b),
            "MAE_Brix_Bx": calc_mae(abs_b),
            "N_Acidity": len(abs_a),
            "MAE_Acidity_pct": calc_mae(abs_a),
        }

    grupos_presentes = []
    for r in all_rows:
        if r["grupo"] not in grupos_presentes:
            grupos_presentes.append(r["grupo"])

    resumo_rows = [_agg_group(g, [r for r in all_rows if r["grupo"] == g]) for g in grupos_presentes]
    resumo_rows.append(_agg_group("TOTAL", all_rows))
    df_resumo = pd.DataFrame(resumo_rows)

    xlsx_path = os.path.join(out_dir, "resumo_erros.xlsx")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df_resumo.to_excel(writer, sheet_name="Resumo_Global", index=False)
        df_casos.to_excel(writer, sheet_name="Casos", index=False)
    return xlsx_path


def main():
    parser = argparse.ArgumentParser(description="Gerar gráficos Estimado vs. Real automaticamente com Plotly.")
    parser.add_argument(
        "--grupo",
        choices=["all", "amostra_macas_normal", "ensaio_macas_20c", "amostra_camaras_macas", "babykiwi_retaill"],
        default="all",
        help="Grupo de cenários a processar (default: all)",
    )
    parser.add_argument(
        "--stakeholder",
        choices=["Producer", "Processor", "Retailer", "Industry"],
        default="Retailer",
        help="Stakeholder para o modelo (default: Retailer)",
    )
    parser.add_argument(
        "--out",
        default=os.path.join(CENARIOS_REAIS_DIR, "resultados"),
        help="Pasta de destino dos gráficos e resumo de erros (default: cenarios_reais/resultados)",
    )
    parser.add_argument(
        "--apenas-medias",
        action="store_true",
        help="Em amostra_camaras_macas, gerar apenas media_lote (ignora os 10 frutos individuais)",
    )
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    all_rows = []

    with PlotlyRenderer() as renderer:
        if args.grupo in ("all", "amostra_macas_normal"):
            print("[1/4] A processar amostra_macas_normal...")
            rows = process_amostra_normal_ess(renderer, args.out, args.stakeholder)
            all_rows.extend(rows)
            print(f"      -> {len(rows)} casos gerados.")

        if args.grupo in ("all", "ensaio_macas_20c"):
            print("[2/4] A processar ensaio_macas_20c...")
            rows = process_ensaio_20c(renderer, args.out, args.stakeholder)
            all_rows.extend(rows)
            print(f"      -> {len(rows)} casos gerados.")

        if args.grupo in ("all", "amostra_camaras_macas"):
            print("[3/4] A processar amostra_camaras_macas...")
            rows = process_amostra_camaras(renderer, args.out, args.stakeholder, apenas_medias=args.apenas_medias)
            all_rows.extend(rows)
            print(f"      -> {len(rows)} casos gerados.")

        if args.grupo in ("all", "babykiwi_retaill"):
            print("[4/4] A processar babykiwi_retaill...")
            rows = process_babykiwi_retaill(renderer, args.out, args.stakeholder)
            all_rows.extend(rows)
            print(f"      -> {len(rows)} casos gerados.")

    if all_rows:
        xlsx_path = export_mae_summary_excel(all_rows, args.out)
        print(f"\nConcluído! {len(all_rows)} casos processados.")
        print(f"Gráficos guardados em: {args.out}")
        if xlsx_path:
            print(f"Resumo de erros guardado em: {xlsx_path}")
    else:
        print("Nenhum caso encontrado para processar.")


if __name__ == "__main__":
    main()
