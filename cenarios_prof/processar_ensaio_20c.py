"""
Script de automação para extrair, calcular e gerar:
1. Valores Reais em ficheiros Excel separados na pasta 'cenarios_prof/ensaio_20c/valores_reais':
   - 'medias_por_especie.xlsx'        (Médias por espécie: Gala e Golden organizadas por trajetória)
   - 'medias_por_produtor.xlsx'       (Médias por espécie e produtor: AMPS e CJL)
   - 'valores_reais_gala_amps.xlsx'   (Medições individuais Maçãs 1 a 5 da Gala AMPS)
   - 'valores_reais_gala_cjl.xlsx'    (Medições individuais Maçãs 1 a 5 da Gala CJL)
   - 'valores_reais_golden_amps.xlsx' (Medições individuais Maçãs 1 a 5 da Golden AMPS)
   - 'valores_reais_golden_cjl.xlsx'  (Medições individuais Maçãs 1 a 5 da Golden CJL)

2. Cenários Climáticos Preditivos compatíveis com a app LC-eureka (ui.py) na pasta 'cenarios_prof/ensaio_20c/':
   - 'cenario_maca_gala_ensaio_20c.xlsx'          (Timeline geral sala ambiente Gala)
   - 'cenario_maca_golden_ensaio_20c.xlsx'        (Timeline geral sala ambiente Golden)
   - 'cenario_maca_gala_t0_direto_20c.xlsx'       (Trajetória 0 Gala: 28 dias a 20ºC)
   - 'cenario_maca_gala_t1_frio1sem_20c.xlsx'     (Trajetória 1 Gala: 1 sem frio + 4 sem 20ºC)
   - 'cenario_maca_gala_t2_frio2sem_20c.xlsx'     (Trajetória 2 Gala: 2 sem frio + 4 sem 20ºC)
   - 'cenario_maca_gala_t3_frio3sem_20c.xlsx'     (Trajetória 3 Gala: 3 sem frio + 4 sem 20ºC)
   - 'cenario_maca_gala_t4_frio4sem_20c.xlsx'     (Trajetória 4 Gala: 4 sem frio + 4 sem 20ºC)
   - 'cenario_maca_gala_t5_frio5sem_20c.xlsx'     (Trajetória 5 Gala: 5 sem frio + 1 sem 20ºC)
   - 'cenario_maca_golden_t0_direto_20c.xlsx'     (Trajetória 0 Golden: 28 dias a 20ºC)
   - 'cenario_maca_golden_t1_frio1sem_20c.xlsx'   (Trajetória 1 Golden: 1 sem frio + 4 sem 20ºC)
   - 'cenario_maca_golden_t2_frio2sem_20c.xlsx'   (Trajetória 2 Golden: 2 sem frio + 3 sem 20ºC)
   - 'cenario_maca_golden_t3_frio3sem_20c.xlsx'   (Trajetória 3 Golden: 3 sem frio + 2 sem 20ºC)
   - 'cenario_maca_golden_t4_frio4sem_20c.xlsx'   (Trajetória 4 Golden: 4 sem frio + 1 sem 20ºC)

Fonte: 'cenarios_prof/Base de dados Maçã (Retaill) experiencias ESS_UTP.xlsx'
Folha: 'Ensaio 20ºC'
"""

import os
import sys
import glob
import datetime
import argparse
from collections import defaultdict

# Garante acesso aos pacotes instalados no ambiente virtual (.venv) se necessário
script_dir = os.path.dirname(os.path.abspath(__file__))
for potential_dir in [script_dir, os.path.dirname(script_dir)]:
    venv_site_packages = os.path.join(potential_dir, ".venv", "Lib", "site-packages")
    if os.path.exists(venv_site_packages) and venv_site_packages not in sys.path:
        sys.path.insert(0, venv_site_packages)
        break

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter, column_index_from_string

GRAVITY_CONSTANT = 9.80665

# ==============================================================================
# CONSTANTES DE CONFIGURAÇÃO (FICHEIRO, FOLHA E POSIÇÃO DAS COLUNAS)
# Qualquer alteração futura (ex: coluna Data passar de 'B' para 'D', ou novo nome
# de ficheiro) pode ser feita alterando apenas as constantes abaixo.
# Aceita letras de colunas ('A', 'B', ...) ou números inteiros (1, 2, ...).
# ==============================================================================
FICHEIRO_ENTRADA = "Base de dados Maçã (Retaill) experiencias ESS_UTP.xlsx"
FOLHA_ENTRADA = "Ensaio 20ºC"
LINHA_CABECALHO = 2
LINHA_INICIO_DADOS = 3

# Posições de Colunas
COL_PRODUTOR = "A"          # Col 1: Produtor
COL_DATA = "B"              # Col 2: Data (se passar para 'D', basta mudar aqui!)
COL_VARIEDADE = "C"         # Col 3: Variedade
COL_AMOSTRA = "D"           # Col 4: ref semana, amostras
COL_TIPOLOGIA = "E"         # Col 5: Tipologia (Receção, Amb (20ºC), Frio (2ºC))

# Séries meteorológicas semanais (7 dias: Segunda a Domingo)
COL_HUMIDADE_INICIO = "F"   # Col 6: Humidade dia 1 (F a L = 7 colunas)
COL_TEMPERATURA_INICIO = "M"# Col 13: Temperatura dia 1 (M a S = 7 colunas)

# Firmeza (5 maçãs x 2 furos = 10 colunas: T a AC = 20 a 29)
COL_FIRMEZA_INICIO = "T"    # Col 20

# Brix (5 maçãs = 5 colunas: AD a AH = 30 a 34)
COL_BRIX_INICIO = "AD"      # Col 30

# Acidez (g ácido málico/100 g)
COL_ACIDEZ = "AI"           # Col 35

def col2idx(col):
    """Converte letra de coluna ('A', 'B', 'AA') ou número inteiro (1, 2) para índice 1-based."""
    if isinstance(col, int):
        return col
    if isinstance(col, str):
        s = col.strip().upper()
        if s.isdigit():
            return int(s)
        return column_index_from_string(s)
    raise ValueError(f"Formato de coluna inválido: {col}")

def resolver_caminho_ficheiro(nome_ou_caminho, base_dir, padrao_glob=None):
    """Resolve o caminho de um ficheiro de forma tolerante a caminhos relativos ou nomes parciais."""
    if os.path.isabs(nome_ou_caminho) and os.path.exists(nome_ou_caminho):
        return nome_ou_caminho
    cand = os.path.join(base_dir, nome_ou_caminho)
    if os.path.exists(cand):
        return cand
    if padrao_glob:
        encontrados = glob.glob(os.path.join(base_dir, padrao_glob))
        if encontrados:
            return encontrados[0]
    return cand

# Paleta de Estilos Profissional (LC-eureka)
FONT_NAME = "Segoe UI"
HEADER_FILL = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")       # Azul Escuro
HEADER_FONT = Font(name=FONT_NAME, size=11, bold=True, color="FFFFFF")
TITLE_FILL = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")        # Slate Escuro
TITLE_FONT = Font(name=FONT_NAME, size=12, bold=True, color="FFFFFF")
SUBTITLE_FILL = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")     # Cinzento Claro
SUBTITLE_FONT = Font(name=FONT_NAME, size=11, bold=True, color="1E293B")
TRAJ_FILL = PatternFill(start_color="CBD5E1", end_color="CBD5E1", fill_type="solid")         # Destaque de Trajetória
TRAJ_FONT = Font(name=FONT_NAME, size=11, bold=True, color="0F172A")
ROW_ALT_FILL = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")      # Zebrado suave
ROW_NORM_FILL = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

BORDER_THIN = Border(
    left=Side(style='thin', color='CBD5E1'),
    right=Side(style='thin', color='CBD5E1'),
    top=Side(style='thin', color='CBD5E1'),
    bottom=Side(style='thin', color='CBD5E1')
)

ALIGN_CENTER = Alignment(horizontal='center', vertical='center')
ALIGN_LEFT = Alignment(horizontal='left', vertical='center')
ALIGN_RIGHT = Alignment(horizontal='right', vertical='center')

HEADERS_TEMPO = [
    "Amostra", "Tipologia", "Dia", "Data Real",
    "Firmeza 1 (N [kg/cm²])", "Firmeza 2 (N [kg/cm²])", "Firmeza Média (N [kg/cm²])",
    "Brix (°Bx)", "Acidez (%)"
]

HEADERS_NUMERICOS = [
    "Amostra", "Tipologia", "Dia", "Data Real",
    "Firmeza 1 (N)", "Firmeza 1 (kg/cm²)",
    "Firmeza 2 (N)", "Firmeza 2 (kg/cm²)",
    "Firmeza Média (N)", "Firmeza Média (kg/cm²)",
    "Brix (°Bx)", "Acidez (%)"
]

def ajustar_largura_colunas(ws):
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val = str(cell.value or '')
            if len(val) > 40 and getattr(cell, 'alignment', None) and cell.alignment.horizontal == 'left':
                continue
            max_len = max(max_len, len(val))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

def aplicar_borda_tabela(ws, min_r, max_r, min_c, max_c):
    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            cell = ws.cell(row=r, column=c)
            cell.border = BORDER_THIN

def salvar_workbook(wb, caminho_saida):
    os.makedirs(os.path.dirname(os.path.abspath(caminho_saida)), exist_ok=True)
    try:
        wb.save(caminho_saida)
        print(f"[OK] Ficheiro gerado: {caminho_saida}")
        return True
    except PermissionError:
        print(f"[AVISO] Não foi possível atualizar '{caminho_saida}': o ficheiro está aberto noutro programa (ex: Excel). Feche o ficheiro para permitir a sua atualização.")
        return False

def parse_trajectory(amostra_str):
    """
    Retorna (traj_id, step) para ordenação por ramos térmicos.
    Ex:
    'T0'   -> (0, 0)
    'T0.1' -> (0, 1)
    'T1'   -> (1, 0)
    'T1.1' -> (1, 1)
    'T2'   -> (2, 0)
    'T2.1' -> (2, 1)
    """
    s = str(amostra_str).strip().upper().replace(" ", "")
    if s.startswith("T"):
        s = s[1:]
    parts = s.split(".")
    try:
        traj_id = int(parts[0])
        step = int(parts[1]) if len(parts) > 1 else 0
        return (traj_id, step)
    except Exception:
        return (99, 99)

def get_trajectory_label(traj_id):
    labels = {
        0: "Trajetória 0 — Ambiente Direto (20ºC)",
        1: "Trajetória 1 — 1 Semana Frio (2ºC) + Prateleira (20ºC)",
        2: "Trajetória 2 — 2 Semanas Frio (2ºC) + Prateleira (20ºC)",
        3: "Trajetória 3 — 3 Semanas Frio (2ºC) + Prateleira (20ºC)",
        4: "Trajetória 4 — 4 Semanas Frio (2ºC) + Prateleira (20ºC)",
        5: "Trajetória 5 — 5 Semanas Frio (2ºC) + Prateleira (20ºC)"
    }
    return labels.get(traj_id, f"Trajetória {traj_id}")

def extrair_dados_ensaio_20c(caminho_excel):
    """
    Lê a folha 'Ensaio 20ºC' do Excel e extrai:
    1. Medições reais por variedade, produtor, amostra, tipologia e maçã (1 a 5).
    2. Séries diárias contínuas de Temperatura e Humidade para a câmara de Frio e sala Ambiente.
    """
    if not os.path.exists(caminho_excel):
        raise FileNotFoundError(f"Ficheiro Excel não encontrado: {caminho_excel}")

    wb = openpyxl.load_workbook(caminho_excel, data_only=True)
    nome_folha = FOLHA_ENTRADA if FOLHA_ENTRADA in wb.sheetnames else next((s for s in wb.sheetnames if "ensaio 20" in s.lower() or "20º" in s.lower() or "20o" in s.lower()), None)
    if not nome_folha:
        raise ValueError(f"Folha '{FOLHA_ENTRADA}' não encontrada em {wb.sheetnames}")

    ws = wb[nome_folha]

    c_prod = col2idx(COL_PRODUTOR)
    c_dt = col2idx(COL_DATA)
    c_var = col2idx(COL_VARIEDADE)
    c_am = col2idx(COL_AMOSTRA)
    c_tipo = col2idx(COL_TIPOLOGIA)
    c_hum_start = col2idx(COL_HUMIDADE_INICIO)
    c_temp_start = col2idx(COL_TEMPERATURA_INICIO)
    c_firm_start = col2idx(COL_FIRMEZA_INICIO)
    c_brix_start = col2idx(COL_BRIX_INICIO)
    c_acidez = col2idx(COL_ACIDEZ)

    # Identificar T0 dates por variedade para calcular dias corridos
    t0_dates = {}
    for r in range(LINHA_INICIO_DADOS, ws.max_row + 1):
        var = ws.cell(r, c_var).value
        am = str(ws.cell(r, c_am).value or '').strip()
        dt = ws.cell(r, c_dt).value
        if var and am.upper() == 'T0' and dt:
            t0_dt = dt.date() if isinstance(dt, datetime.datetime) else dt
            if var not in t0_dates:
                t0_dates[var] = t0_dt

    if "Gala" not in t0_dates:
        t0_dates["Gala"] = datetime.date(2026, 8, 27)
    if "Golden" not in t0_dates:
        t0_dates["Golden"] = datetime.date(2026, 9, 24)

    def parse_float(val):
        if val is None:
            return None
        try:
            return float(str(val).replace(",", "."))
        except ValueError:
            return None

    medicoes = []
    sample_climate = {}
    climate_amb = {}
    climate_frio = {}

    for r in range(LINHA_INICIO_DADOS, ws.max_row + 1):
        prod = ws.cell(r, c_prod).value
        dt = ws.cell(r, c_dt).value
        var = ws.cell(r, c_var).value
        amostra = ws.cell(r, c_am).value
        tipo = ws.cell(r, c_tipo).value

        # Extrair dados climáticos diários
        # A semana meteorológica no Excel começa na Segunda-feira e termina no Domingo.
        # A coluna 'Data' (dt) indica a data da colheita/análise em laboratório (Quinta-feira).
        temps = [parse_float(ws.cell(r, c_temp_start + i).value) for i in range(7)]
        hums = [parse_float(ws.cell(r, c_hum_start + i).value) for i in range(7)]

        if dt and any(x is not None for x in temps):
            dt_val = dt.date() if isinstance(dt, datetime.datetime) else dt
            # Calcula a Segunda-feira da semana a que corresponde a linha
            monday = dt_val - datetime.timedelta(days=dt_val.weekday())
            for idx in range(7):
                t = temps[idx]
                h = hums[idx]
                if t is not None:
                    day_date = monday + datetime.timedelta(days=idx)
                    h_padrao = 65.0 if 'amb' in str(tipo).lower() else 82.0
                    hum_val = h if h is not None else h_padrao
                    if 'amb' in str(tipo).lower():
                        if day_date not in climate_amb:
                            climate_amb[day_date] = (t, hum_val)
                    else:
                        if day_date not in climate_frio:
                            climate_frio[day_date] = (t, hum_val)

        if not (prod and var and amostra):
            continue

        prod = str(prod).strip()
        var = str(var).strip()
        amostra = str(amostra).strip()
        tipo = str(tipo).strip() if tipo else "—"

        data_real = dt.date() if isinstance(dt, datetime.datetime) else dt
        t0_dt = t0_dates.get(var, data_real)
        dias_corridos = (data_real - t0_dt).days if (data_real and t0_dt) else 0

        traj_id, step = parse_trajectory(amostra)

        # Regista os 7 valores diários de Temperatura e Humidade da linha da amostra (Opção 1)
        key_sample = (var, amostra)
        if key_sample not in sample_climate and any(x is not None for x in temps):
            sample_climate[key_sample] = {
                "temps": [t if t is not None else (20.0 if 'amb' in str(tipo).lower() else 2.0) for t in temps],
                "hums": [h if h is not None else (65.0 if 'amb' in str(tipo).lower() else 82.0) for h in hums],
                "data_real": data_real,
                "tipologia": tipo
            }

        # Acidez
        acidez = parse_float(ws.cell(r, c_acidez).value)

        # 5 maçãs por linha
        for apple_idx in range(1, 6):
            col_pen1 = c_firm_start + (apple_idx - 1) * 2
            col_pen2 = col_pen1 + 1
            col_brix = c_brix_start + (apple_idx - 1)

            p1_kg = parse_float(ws.cell(r, col_pen1).value)
            p2_kg = parse_float(ws.cell(r, col_pen2).value)
            brix = parse_float(ws.cell(r, col_brix).value)

            p1_n = round(p1_kg * GRAVITY_CONSTANT, 1) if p1_kg is not None else None
            p2_n = round(p2_kg * GRAVITY_CONSTANT, 1) if p2_kg is not None else None

            if p1_n is not None and p2_n is not None:
                pm_n = round((p1_n + p2_n) / 2.0, 1)
                pm_kg = round((p1_kg + p2_kg) / 2.0, 2)
            elif p1_n is not None:
                pm_n = p1_n
                pm_kg = round(p1_kg, 2)
            elif p2_n is not None:
                pm_n = p2_n
                pm_kg = round(p2_kg, 2)
            else:
                pm_n = None
                pm_kg = None

            medicoes.append({
                "row_excel": r,
                "variedade": var,
                "produtor": prod,
                "amostra": amostra,
                "tipologia": tipo,
                "dia": dias_corridos,
                "data_real": data_real,
                "traj_id": traj_id,
                "step": step,
                "maca": apple_idx,
                "f1_n": p1_n,
                "f1_kg": round(p1_kg, 2) if p1_kg is not None else None,
                "f2_n": p2_n,
                "f2_kg": round(p2_kg, 2) if p2_kg is not None else None,
                "fm_n": pm_n,
                "fm_kg": pm_kg,
                "brix": round(brix, 2) if brix is not None else None,
                "acidez": round(acidez, 3) if acidez is not None else None
            })

    climate_data = {
        "amb": climate_amb,
        "frio": climate_frio,
        "sample_climate": sample_climate,
        "t0_dates": t0_dates
    }

    return medicoes, climate_data

def calcular_medias(medicoes):
    """
    Calcula médias agregadas:
    1. Por Espécie e Amostra
    2. Por Espécie, Produtor e Amostra
    """
    esp_tempo = defaultdict(list)
    esp_prod_tempo = defaultdict(list)

    for m in medicoes:
        key_esp = (m["variedade"], m["amostra"], m["tipologia"], m["dia"], m["data_real"], m["traj_id"], m["step"])
        esp_tempo[key_esp].append(m)

        key_esp_prod = (m["variedade"], m["produtor"], m["amostra"], m["tipologia"], m["dia"], m["data_real"], m["traj_id"], m["step"])
        esp_prod_tempo[key_esp_prod].append(m)

    def stats(items):
        f1_n = [x["f1_n"] for x in items if x["f1_n"] is not None]
        f1_kg = [x["f1_kg"] for x in items if x["f1_kg"] is not None]
        f2_n = [x["f2_n"] for x in items if x["f2_n"] is not None]
        f2_kg = [x["f2_kg"] for x in items if x["f2_kg"] is not None]
        fm_n = [x["fm_n"] for x in items if x["fm_n"] is not None]
        fm_kg = [x["fm_kg"] for x in items if x["fm_kg"] is not None]
        brix = [x["brix"] for x in items if x["brix"] is not None]
        acidez = [x["acidez"] for x in items if x["acidez"] is not None]

        return {
            "n": len(items),
            "f1_n": sum(f1_n) / len(f1_n) if f1_n else 0.0,
            "f1_kg": sum(f1_kg) / len(f1_kg) if f1_kg else 0.0,
            "f2_n": sum(f2_n) / len(f2_n) if f2_n else 0.0,
            "f2_kg": sum(f2_kg) / len(f2_kg) if f2_kg else 0.0,
            "fm_n": sum(fm_n) / len(fm_n) if fm_n else 0.0,
            "fm_kg": sum(fm_kg) / len(fm_kg) if fm_kg else 0.0,
            "brix": sum(brix) / len(brix) if brix else 0.0,
            "acidez": sum(acidez) / len(acidez) if acidez else 0.0,
        }

    return {
        "especie_tempo": {k: stats(v) for k, v in esp_tempo.items()},
        "especie_prod_tempo": {k: stats(v) for k, v in esp_prod_tempo.items()}
    }

def gerar_excel_apenas_medias_especie(medias_info, caminho_saida):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    ws_main = wb.create_sheet(title="Medias_Por_Especie")
    ws_main.views.sheetView[0].showGridLines = True
    curr_r = 1

    variedades = sorted(list(set(k[0] for k in medias_info["especie_tempo"].keys())))

    for sp in variedades:
        ws_main.cell(curr_r, 1, f"Maçã {sp} — Médias Gerais por Trajetória (AMPS + CJL)")
        ws_main.merge_cells(start_row=curr_r, start_column=1, end_row=curr_r, end_column=len(HEADERS_TEMPO))
        ws_main.cell(curr_r, 1).fill = TITLE_FILL
        ws_main.cell(curr_r, 1).font = TITLE_FONT
        ws_main.cell(curr_r, 1).alignment = ALIGN_CENTER
        ws_main.row_dimensions[curr_r].height = 26
        curr_r += 1

        sub_items = [(k, v) for k, v in medias_info["especie_tempo"].items() if k[0] == sp]
        traj_groups = defaultdict(list)
        for item in sub_items:
            traj_id = item[0][5]
            traj_groups[traj_id].append(item)

        for traj_id in sorted(traj_groups.keys()):
            items_traj = traj_groups[traj_id]
            items_traj.sort(key=lambda x: (x[0][5], x[0][6], x[0][3]))

            ws_main.cell(curr_r, 1, get_trajectory_label(traj_id))
            ws_main.merge_cells(start_row=curr_r, start_column=1, end_row=curr_r, end_column=len(HEADERS_TEMPO))
            ws_main.cell(curr_r, 1).fill = TRAJ_FILL
            ws_main.cell(curr_r, 1).font = TRAJ_FONT
            ws_main.cell(curr_r, 1).alignment = ALIGN_LEFT
            ws_main.row_dimensions[curr_r].height = 22
            curr_r += 1

            for c_idx, h in enumerate(HEADERS_TEMPO, 1):
                cell = ws_main.cell(curr_r, c_idx, h)
                cell.fill = HEADER_FILL
                cell.font = HEADER_FONT
                cell.alignment = ALIGN_CENTER
            ws_main.row_dimensions[curr_r].height = 20
            start_table = curr_r
            curr_r += 1

            for (v_sp, am, tipo, d, dt, t_id, st), s in items_traj:
                ws_main.append([
                    am, tipo, d,
                    dt.strftime("%Y-%m-%d") if isinstance(dt, datetime.date) else str(dt),
                    f"{s['f1_n']:.1f} N ({s['f1_kg']:.2f} kg/cm²)",
                    f"{s['f2_n']:.1f} N ({s['f2_kg']:.2f} kg/cm²)",
                    f"{s['fm_n']:.1f} N ({s['fm_kg']:.2f} kg/cm²)",
                    f"{s['brix']:.2f} °Bx",
                    f"{s['acidez']:.3f} %"
                ])
                r_c = ws_main[curr_r]
                r_c[0].font = Font(name=FONT_NAME, bold=True)
                r_c[0].alignment = ALIGN_CENTER
                r_c[1].alignment = ALIGN_CENTER
                r_c[2].alignment = ALIGN_CENTER
                r_c[3].alignment = ALIGN_CENTER
                r_c[6].font = Font(name=FONT_NAME, bold=True)
                curr_r += 1

            aplicar_borda_tabela(ws_main, start_table, curr_r - 1, 1, len(HEADERS_TEMPO))
            curr_r += 1

        curr_r += 1

    ajustar_largura_colunas(ws_main)

    for sp in variedades:
        ws_sp = wb.create_sheet(title=f"Dados_Numericos_{sp}")
        ws_sp.views.sheetView[0].showGridLines = True
        ws_sp.append(HEADERS_NUMERICOS)
        for c in range(1, len(HEADERS_NUMERICOS) + 1):
            ws_sp.cell(1, c).fill = HEADER_FILL
            ws_sp.cell(1, c).font = HEADER_FONT
            ws_sp.cell(1, c).alignment = ALIGN_CENTER
        ws_sp.row_dimensions[1].height = 24

        sub_items = [(k, v) for k, v in medias_info["especie_tempo"].items() if k[0] == sp]
        sub_items.sort(key=lambda x: (x[0][5], x[0][6], x[0][3]))

        for r_i, ((v_sp, am, tipo, d, dt, t_id, st), s) in enumerate(sub_items, 2):
            ws_sp.append([
                am, tipo, d,
                dt.strftime("%Y-%m-%d") if isinstance(dt, datetime.date) else str(dt),
                round(s['f1_n'], 1), round(s['f1_kg'], 2),
                round(s['f2_n'], 1), round(s['f2_kg'], 2),
                round(s['fm_n'], 1), round(s['fm_kg'], 2),
                round(s['brix'], 2), round(s['acidez'], 3)
            ])
            if r_i % 2 == 1:
                for c in range(1, len(HEADERS_NUMERICOS) + 1):
                    ws_sp.cell(r_i, c).fill = ROW_ALT_FILL
        aplicar_borda_tabela(ws_sp, 1, len(sub_items) + 1, 1, len(HEADERS_NUMERICOS))
        ajustar_largura_colunas(ws_sp)

    salvar_workbook(wb, caminho_saida)

def gerar_excel_medias_por_produtor(medias_info, caminho_saida):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    ws_main = wb.create_sheet(title="Medias_Por_Produtor")
    ws_main.views.sheetView[0].showGridLines = True
    curr_r = 1

    keys = list(medias_info["especie_prod_tempo"].keys())
    variedades = sorted(list(set(k[0] for k in keys)))
    produtores = sorted(list(set(k[1] for k in keys)))

    for sp in variedades:
        for pr in produtores:
            sub_items = [(k, v) for k, v in medias_info["especie_prod_tempo"].items() if k[0] == sp and k[1] == pr]
            if not sub_items:
                continue

            ws_main.cell(curr_r, 1, f"Maçã {sp} | Produtor {pr} — Médias por Trajetória")
            ws_main.merge_cells(start_row=curr_r, start_column=1, end_row=curr_r, end_column=len(HEADERS_TEMPO))
            ws_main.cell(curr_r, 1).fill = TITLE_FILL
            ws_main.cell(curr_r, 1).font = TITLE_FONT
            ws_main.cell(curr_r, 1).alignment = ALIGN_CENTER
            ws_main.row_dimensions[curr_r].height = 26
            curr_r += 1

            traj_groups = defaultdict(list)
            for item in sub_items:
                traj_id = item[0][6]
                traj_groups[traj_id].append(item)

            for traj_id in sorted(traj_groups.keys()):
                items_traj = traj_groups[traj_id]
                items_traj.sort(key=lambda x: (x[0][6], x[0][7], x[0][4]))

                ws_main.cell(curr_r, 1, get_trajectory_label(traj_id))
                ws_main.merge_cells(start_row=curr_r, start_column=1, end_row=curr_r, end_column=len(HEADERS_TEMPO))
                ws_main.cell(curr_r, 1).fill = TRAJ_FILL
                ws_main.cell(curr_r, 1).font = TRAJ_FONT
                ws_main.cell(curr_r, 1).alignment = ALIGN_LEFT
                ws_main.row_dimensions[curr_r].height = 22
                curr_r += 1

                for c_idx, h in enumerate(HEADERS_TEMPO, 1):
                    cell = ws_main.cell(curr_r, c_idx, h)
                    cell.fill = HEADER_FILL
                    cell.font = HEADER_FONT
                    cell.alignment = ALIGN_CENTER
                ws_main.row_dimensions[curr_r].height = 20
                start_table = curr_r
                curr_r += 1

                for (v_sp, v_pr, am, tipo, d, dt, t_id, st), s in items_traj:
                    ws_main.append([
                        am, tipo, d,
                        dt.strftime("%Y-%m-%d") if isinstance(dt, datetime.date) else str(dt),
                        f"{s['f1_n']:.1f} N ({s['f1_kg']:.2f} kg/cm²)",
                        f"{s['f2_n']:.1f} N ({s['f2_kg']:.2f} kg/cm²)",
                        f"{s['fm_n']:.1f} N ({s['fm_kg']:.2f} kg/cm²)",
                        f"{s['brix']:.2f} °Bx",
                        f"{s['acidez']:.3f} %"
                    ])
                    r_c = ws_main[curr_r]
                    r_c[0].font = Font(name=FONT_NAME, bold=True)
                    r_c[0].alignment = ALIGN_CENTER
                    r_c[1].alignment = ALIGN_CENTER
                    r_c[2].alignment = ALIGN_CENTER
                    r_c[3].alignment = ALIGN_CENTER
                    r_c[6].font = Font(name=FONT_NAME, bold=True)
                    curr_r += 1

                aplicar_borda_tabela(ws_main, start_table, curr_r - 1, 1, len(HEADERS_TEMPO))
                curr_r += 1

            curr_r += 1

    ajustar_largura_colunas(ws_main)

    for sp in variedades:
        for pr in produtores:
            sub_items = [(k, v) for k, v in medias_info["especie_prod_tempo"].items() if k[0] == sp and k[1] == pr]
            if not sub_items:
                continue
            sub_items.sort(key=lambda x: (x[0][6], x[0][7], x[0][4]))

            ws_tab = wb.create_sheet(title=f"{sp[:6]}_{pr}")
            ws_tab.views.sheetView[0].showGridLines = True
            ws_tab.append(HEADERS_NUMERICOS)
            for c in range(1, len(HEADERS_NUMERICOS) + 1):
                ws_tab.cell(1, c).fill = HEADER_FILL
                ws_tab.cell(1, c).font = HEADER_FONT
                ws_tab.cell(1, c).alignment = ALIGN_CENTER
            ws_tab.row_dimensions[1].height = 24

            for r_i, ((v_sp, v_pr, am, tipo, d, dt, t_id, st), s) in enumerate(sub_items, 2):
                ws_tab.append([
                    am, tipo, d,
                    dt.strftime("%Y-%m-%d") if isinstance(dt, datetime.date) else str(dt),
                    round(s['f1_n'], 1), round(s['f1_kg'], 2),
                    round(s['f2_n'], 1), round(s['f2_kg'], 2),
                    round(s['fm_n'], 1), round(s['fm_kg'], 2),
                    round(s['brix'], 2), round(s['acidez'], 3)
                ])
                if r_i % 2 == 1:
                    for c in range(1, len(HEADERS_NUMERICOS) + 1):
                        ws_tab.cell(r_i, c).fill = ROW_ALT_FILL

            aplicar_borda_tabela(ws_tab, 1, len(sub_items) + 1, 1, len(HEADERS_NUMERICOS))
            ajustar_largura_colunas(ws_tab)

    salvar_workbook(wb, caminho_saida)

def gerar_excel_produtor_individual(medicoes, medias_info, variedade, produtor, caminho_saida):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    sub_meds = [m for m in medicoes if m["variedade"].lower() == variedade.lower() and m["produtor"].lower() == produtor.lower()]
    if not sub_meds:
        return

    ws_all = wb.create_sheet(title="Macas_1_a_5")
    ws_all.views.sheetView[0].showGridLines = True
    curr_r = 1

    for apple_idx in range(1, 6):
        maca_rows = [m for m in sub_meds if m["maca"] == apple_idx]
        if not maca_rows:
            continue

        ws_all.cell(curr_r, 1, f"Maçã {apple_idx} — {produtor} ({variedade})")
        ws_all.merge_cells(start_row=curr_r, start_column=1, end_row=curr_r, end_column=len(HEADERS_TEMPO))
        ws_all.cell(curr_r, 1).fill = TITLE_FILL
        ws_all.cell(curr_r, 1).font = TITLE_FONT
        ws_all.cell(curr_r, 1).alignment = ALIGN_LEFT
        ws_all.row_dimensions[curr_r].height = 24
        curr_r += 1

        traj_groups = defaultdict(list)
        for m in maca_rows:
            traj_groups[m["traj_id"]].append(m)

        for traj_id in sorted(traj_groups.keys()):
            items_traj = traj_groups[traj_id]
            items_traj.sort(key=lambda x: (x["traj_id"], x["step"], x["dia"]))

            ws_all.cell(curr_r, 1, get_trajectory_label(traj_id))
            ws_all.merge_cells(start_row=curr_r, start_column=1, end_row=curr_r, end_column=len(HEADERS_TEMPO))
            ws_all.cell(curr_r, 1).fill = TRAJ_FILL
            ws_all.cell(curr_r, 1).font = TRAJ_FONT
            ws_all.cell(curr_r, 1).alignment = ALIGN_LEFT
            ws_all.row_dimensions[curr_r].height = 20
            curr_r += 1

            for c_idx, h in enumerate(HEADERS_TEMPO, 1):
                cell = ws_all.cell(curr_r, c_idx, h)
                cell.fill = HEADER_FILL
                cell.font = HEADER_FONT
                cell.alignment = ALIGN_CENTER
            ws_all.row_dimensions[curr_r].height = 20
            start_table = curr_r
            curr_r += 1

            for m in items_traj:
                f1_str = f"{m['f1_n']:.1f} N ({m['f1_kg']:.1f} kg/cm²)" if m['f1_n'] is not None else "—"
                f2_str = f"{m['f2_n']:.1f} N ({m['f2_kg']:.1f} kg/cm²)" if m['f2_n'] is not None else "—"
                fm_str = f"{m['fm_n']:.1f} N ({m['fm_kg']:.2f} kg/cm²)" if m['fm_n'] is not None else "—"
                bx_str = f"{m['brix']:.1f} °Bx" if m['brix'] is not None else "—"
                ac_str = f"{m['acidez']:.3f} %" if m['acidez'] is not None else "—"

                ws_all.append([
                    m["amostra"], m["tipologia"], m["dia"],
                    m["data_real"].strftime("%Y-%m-%d") if isinstance(m["data_real"], datetime.date) else str(m["data_real"]),
                    f1_str, f2_str, fm_str, bx_str, ac_str
                ])
                r_c = ws_all[curr_r]
                r_c[0].font = Font(name=FONT_NAME, bold=True)
                r_c[0].alignment = ALIGN_CENTER
                r_c[1].alignment = ALIGN_CENTER
                r_c[2].alignment = ALIGN_CENTER
                r_c[3].alignment = ALIGN_CENTER
                r_c[6].font = Font(name=FONT_NAME, bold=True)
                curr_r += 1

            aplicar_borda_tabela(ws_all, start_table, curr_r - 1, 1, len(HEADERS_TEMPO))
            curr_r += 1

        curr_r += 1

    ajustar_largura_colunas(ws_all)

    for apple_idx in range(1, 6):
        maca_rows = [m for m in sub_meds if m["maca"] == apple_idx]
        maca_rows.sort(key=lambda x: (x["traj_id"], x["step"], x["dia"]))
        if not maca_rows:
            continue

        ws_m = wb.create_sheet(title=f"Maca_{apple_idx}")
        ws_m.views.sheetView[0].showGridLines = True
        ws_m.append(HEADERS_NUMERICOS)
        for c in range(1, len(HEADERS_NUMERICOS) + 1):
            ws_m.cell(1, c).fill = HEADER_FILL
            ws_m.cell(1, c).font = HEADER_FONT
            ws_m.cell(1, c).alignment = ALIGN_CENTER
        ws_m.row_dimensions[1].height = 24

        for r_i, m in enumerate(maca_rows, 2):
            ws_m.append([
                m["amostra"], m["tipologia"], m["dia"],
                m["data_real"].strftime("%Y-%m-%d") if isinstance(m["data_real"], datetime.date) else str(m["data_real"]),
                m["f1_n"], m["f1_kg"],
                m["f2_n"], m["f2_kg"],
                m["fm_n"], m["fm_kg"],
                m["brix"], m["acidez"]
            ])
            if r_i % 2 == 1:
                for c in range(1, len(HEADERS_NUMERICOS) + 1):
                    ws_m.cell(r_i, c).fill = ROW_ALT_FILL
        aplicar_borda_tabela(ws_m, 1, len(maca_rows) + 1, 1, len(HEADERS_NUMERICOS))
        ajustar_largura_colunas(ws_m)

    salvar_workbook(wb, caminho_saida)

def criar_arquivo_cenario(caminho_saida, dias_climaticos):
    """
    Gera ficheiro de cenário individual com 1 folha ('Cenario'), perfeitamente compatível com o simulador LC-eureka (ui.py):
    - Folha 'Cenario': Segment_ID, Date, Day, Temperature_C, Humidity_Percent, Region, Packaging
    """
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # 1. Folha Cenario
    ws_cen = wb.create_sheet(title="Cenario")
    ws_cen.views.sheetView[0].showGridLines = True
    headers_cen = ["Segment_ID", "Date", "Day", "Temperature_C", "Humidity_Percent", "Region", "Packaging"]
    ws_cen.append(headers_cen)
    for c in range(1, len(headers_cen) + 1):
        ws_cen.cell(1, c).fill = HEADER_FILL
        ws_cen.cell(1, c).font = HEADER_FONT
        ws_cen.cell(1, c).alignment = ALIGN_CENTER

    for idx, dc in enumerate(dias_climaticos, 1):
        ws_cen.append([
            1,
            dc["date"].strftime("%Y-%m-%d"),
            idx,
            round(dc["temp_c"], 2),
            round(dc["hum_pct"], 2),
            "PT-LVT",
            "bulk"
        ])
    aplicar_borda_tabela(ws_cen, 1, len(dias_climaticos) + 1, 1, len(headers_cen))
    ajustar_largura_colunas(ws_cen)

    salvar_workbook(wb, caminho_saida)

def gerar_cenarios_ensaio_20c(climate_data, medias_info, output_dir):
    """
    Gera ficheiros de cenário .xlsx compatíveis com a app LC-eureka (ui.py) para
    cada trajetória térmica individual (T0 Direto 20ºC, T1 Vinda do Frio (1 sem) + Prateleira 20ºC, etc.)
    seguindo a Opção 1:
    - O ponto inicial (Dia 0) é a medição real de entrada no retalho (T0 para traj 0, ou Tk para traj k, vinda do frio).
    - Para cada passo subsequente na prateleira (Tk.1, Tk.2...), os 7 valores diários de temperatura e humidade
      são extraídos direta e exclusivamente da linha dessa amostra específica no Excel original.
    - A folha 'Cenario' mapeia os 7 dias de cada passo terminando na respetiva data de medição (Quinta-feira).
    - A folha 'Valores Reais' contém a amostra base Tk (Dia 0) e as amostras Tk.s com os dias correspondentes (7, 14, 21, 28).
    """
    os.makedirs(output_dir, exist_ok=True)
    sample_climate = climate_data.get("sample_climate", {})

    esp_tempo = medias_info["especie_tempo"]
    variedades = sorted(list(set(k[0] for k in esp_tempo.keys())))

    for sp in variedades:
        slug_sp = "gala" if "gala" in sp.lower() else "golden"

        sub_items = [
            {
                "variedade": k[0], "amostra": k[1], "tipologia": k[2],
                "dia": k[3], "data_real": k[4], "traj_id": k[5], "step": k[6],
                "fm_n": v["fm_n"], "brix": v["brix"], "acidez": v["acidez"]
            }
            for k, v in esp_tempo.items() if k[0] == sp
        ]

        traj_ids = sorted(list(set(x["traj_id"] for x in sub_items)))

        for traj_id in traj_ids:
            # Amostra base de entrada no retalho para esta trajetória
            if traj_id == 0:
                base_candidates = [x for x in sub_items if x["traj_id"] == 0 and (x["amostra"] == "T0" or x["step"] == 0)]
            else:
                base_candidates = [x for x in sub_items if x["traj_id"] == traj_id and x["step"] == 0]

            if not base_candidates:
                continue
            base_sample = base_candidates[0]
            base_dt = base_sample["data_real"]

            # Passos em prateleira (ambiente 20ºC) desta trajetória ordenados por step
            amb_steps = [x for x in sub_items if x["traj_id"] == traj_id and x["step"] > 0]
            amb_steps.sort(key=lambda x: x["step"])

            # 1. Timeline no Cenario: 7 dias por cada passo, extraídos diretamente da linha da amostra
            # A semana meteorológica no Excel começa na Segunda-feira (idx 0) e termina no Domingo (idx 6).
            # A coluna 'Data' do Excel (s_dt) indica a data da medição laboratorial (Quinta-feira, idx 3 - a coluna do meio).
            dias_traj = []
            day_counter = 1
            for s_item in amb_steps:
                am = s_item["amostra"]
                s_dt = s_item["data_real"]
                c_info = sample_climate.get((sp, am))
                temps = c_info["temps"] if c_info else [20.0] * 7
                hums = c_info["hums"] if c_info else [65.0] * 7

                monday = s_dt - datetime.timedelta(days=s_dt.weekday())
                for idx in range(7):
                    t_val = temps[idx] if temps[idx] is not None else 20.0
                    h_val = hums[idx] if hums[idx] is not None else 65.0
                    day_dt = monday + datetime.timedelta(days=idx)
                    dias_traj.append({
                        "date": day_dt,
                        "day": day_counter,
                        "temp_c": float(t_val),
                        "hum_pct": float(h_val)
                    })
                    day_counter += 1

            traj_slug = f"t{traj_id}_direto_20c" if traj_id == 0 else f"t{traj_id}_frio{traj_id}sem_20c"
            caminho_traj = os.path.join(output_dir, f"cenario_maca_{slug_sp}_{traj_slug}.xlsx")
            criar_arquivo_cenario(caminho_traj, dias_traj)

def main():
    default_input = resolver_caminho_ficheiro(FICHEIRO_ENTRADA, script_dir, "*experiencias ESS_UTP*.xlsx")
    parser = argparse.ArgumentParser(description="Extrai e gera Excels de Valores Reais e Cenários para Ensaio 20ºC.")
    parser.add_argument("--input", default=default_input,
                        help="Caminho do ficheiro Excel de entrada.")
    parser.add_argument("--valores-dir", default=os.path.join(script_dir, "ensaio_20c", "valores_reais"),
                        help="Pasta de saída para os ficheiros Excel de valores reais.")
    parser.add_argument("--cenarios-dir", default=os.path.join(script_dir, "ensaio_20c"),
                        help="Pasta de saída para os ficheiros Excel de cenários compatíveis com LC-eureka.")
    args = parser.parse_args()

    print("=" * 75)
    print("ENSAIO 20ºC: GERAÇÃO DE VALORES REAIS E CENÁRIOS CLIMÁTICOS (OPÇÃO A)")
    print("=" * 75)
    print(f"Ficheiro de Entrada: {args.input}")
    print(f"Diretoria Valores:   {args.valores_dir}")
    print(f"Diretoria Cenários:  {args.cenarios_dir}")

    medicoes, climate_data = extrair_dados_ensaio_20c(args.input)
    print(f"Total de medições individuais extraídas: {len(medicoes)}")

    medias_info = calcular_medias(medicoes)

    variedades = sorted(list(set(m["variedade"] for m in medicoes)))
    produtores = sorted(list(set(m["produtor"] for m in medicoes)))

    print("\n--- 1. Apenas Médias (Por Espécie) ---")
    caminho_esp = os.path.join(args.valores_dir, "medias_por_especie.xlsx")
    gerar_excel_apenas_medias_especie(medias_info, caminho_esp)

    print("\n--- 2. Média do Produtor (Por Espécie e Produtor) ---")
    caminho_prod = os.path.join(args.valores_dir, "medias_por_produtor.xlsx")
    gerar_excel_medias_por_produtor(medias_info, caminho_prod)

    print("\n--- 3. Valores Reais por Produtor e Espécie (Maçãs Individuais 1 a 5) ---")
    for sp in variedades:
        for pr in produtores:
            slug_sp = sp.lower()
            slug_pr = pr.lower()
            nome_f = f"valores_reais_{slug_sp}_{slug_pr}.xlsx"
            caminho_f = os.path.join(args.valores_dir, nome_f)
            gerar_excel_produtor_individual(medicoes, medias_info, sp, pr, caminho_f)

    print("\n--- 4. Cenários Climáticos Compatíveis com LC-eureka (ui.py) ---")
    gerar_cenarios_ensaio_20c(climate_data, medias_info, args.cenarios_dir)

    print("\n" + "=" * 75)
    print("TODOS OS EXCELS (VALORES REAIS E CENÁRIOS) GERADOS COM SUCESSO!")
    print("=" * 75)

if __name__ == "__main__":
    main()
