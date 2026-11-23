"""
Script de automação para extrair, calcular e gerar:
1. Valores Reais de BabyKiwi (Retaill) na pasta 'cenarios_reais/babykiwi_retaill/valores_reais':
   - 'medias_babykiwi.xlsx'         (Resumo T0 inicial + Médias de Firmeza, Brix e Acidez por folha T1..T5)
   - 'valores_reais_detalhado.xlsx' (Todas as réplicas individuais de penetrometria, Brix e acidez por folha T1..T5)

2. Cenários Climáticos Preditivos compatíveis com a plataforma LC-eureka (ui.py) na pasta 'cenarios_reais/babykiwi_retaill/':
   - 'cenario_babykiwi_t1_2c.xlsx'    (T1: 42 dias a 2ºC a partir de T0)
   - 'cenario_babykiwi_t2_5c.xlsx'    (T2: 42 dias a 5ºC a partir de T0)
   - 'cenario_babykiwi_t3_20c.xlsx'   (T3: 18 dias a 20ºC a partir de T0)
   - 'cenario_babykiwi_t4_2_20c.xlsx' (T4: 39 dias com alternância 2ºC <-> 20ºC a partir de T0)
   - 'cenario_babykiwi_t5_5_20c.xlsx' (T5: 39 dias com alternância 5ºC <-> 20ºC a partir de T0)

Fonte: 'cenarios_reais/fontes/Sensores Kiwis_Retaill/BabyKiwi Retaill.xlsx'
Folhas: 'T1', 'T2', 'T3', 'T4', 'T5'
Nota: T0 (2026-08-06) corresponde à receção do fruto, pelo que os seus valores de Firmeza,
Brix e Acidez são os valores iniciais (Dia 0) para a plataforma.
"""

import os
import sys
import glob
import math
import datetime
import argparse

# Garante acesso aos pacotes instalados no ambiente virtual (.venv) se necessário
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.dirname(script_dir)
for potential_dir in [script_dir, repo_dir]:
    venv_site_packages = os.path.join(potential_dir, ".venv", "Lib", "site-packages")
    if os.path.exists(venv_site_packages) and venv_site_packages not in sys.path:
        sys.path.insert(0, venv_site_packages)
        break

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter, column_index_from_string

GRAVITY_CONSTANT = 9.80665

# ==============================================================================
# CONSTANTES DE CONFIGURAÇÃO (FICHEIRO, FOLHAS E POSIÇÃO DAS COLUNAS)
# ==============================================================================
FICHEIRO_ENTRADA = os.path.join("fontes", "Sensores Kiwis_Retaill", "BabyKiwi Retaill.xlsx")
FOLHAS_CENARIOS = ["T1", "T2", "T3", "T4", "T5"]
LINHA_CABECALHO = 1
LINHA_INICIO_DADOS = 2

# Posições de Colunas em BabyKiwi Retaill.xlsx
COL_DATA = "A"                  # Col 1: Data
COL_AMOSTRA = "B"               # Col 2: Amostra
COL_FRUTO = "C"                 # Col 3: Fruto
COL_TIPOLOGIA = "D"             # Col 4: Tipologia
COL_HUMIDADE_INICIO = "E"       # Cols 5..11:  7 dias de Humidade (%)
COL_TEMPERATURA_INICIO = "L"    # Cols 12..18: 7 dias de Temperatura (ºC)
COL_FIRMEZA_INICIO = "S"        # Cols 19..28: 10 réplicas Penetrometria (kg/cm²)
N_FIRMEZA = 10
COL_BRIX_INICIO = "AC"          # Cols 29..33: 5 réplicas Brix (ºBx)
N_BRIX = 5
COL_ACIDEZ_INICIO = "AH"        # Cols 34..36: 3 réplicas Acidez (g ácido málico/100 g)
N_ACIDEZ = 3

# Paleta de Estilos Profissional (LC-eureka)
FONT_NAME = "Segoe UI"
HEADER_FILL = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
HEADER_FONT = Font(name=FONT_NAME, size=11, bold=True, color="FFFFFF")
TITLE_FILL = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
TITLE_FONT = Font(name=FONT_NAME, size=12, bold=True, color="FFFFFF")
SUBTITLE_FILL = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
SUBTITLE_FONT = Font(name=FONT_NAME, size=11, bold=True, color="1E293B")
TRAJ_FILL = PatternFill(start_color="CBD5E1", end_color="CBD5E1", fill_type="solid")
ROW_ALT_FILL = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
SUMMARY_FILL = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
SUMMARY_FONT = Font(name=FONT_NAME, size=11, bold=True, color="92400E")

BORDER_THIN = Border(
    left=Side(style="thin", color="CBD5E1"),
    right=Side(style="thin", color="CBD5E1"),
    top=Side(style="thin", color="CBD5E1"),
    bottom=Side(style="thin", color="CBD5E1"),
)

ALIGN_CENTER = Alignment(horizontal="center", vertical="center")
ALIGN_LEFT = Alignment(horizontal="left", vertical="center")
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")


def col2idx(col):
    """Converte letra de coluna ('A', 'B', 'AA') ou número inteiro para índice 1-based."""
    if isinstance(col, int):
        return col
    if isinstance(col, str):
        s = col.strip().upper()
        if s.isdigit():
            return int(s)
        return column_index_from_string(s)
    raise ValueError(f"Formato de coluna inválido: {col}")


def to_float(val):
    """Converte um valor de célula para float ou devolve None se não for numérico."""
    if val is None or isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(",", ".")
    if not s or s.upper() in ("SD", "ND", "*", "-", "FIM DA AMOSTRA"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_date(val):
    if isinstance(val, datetime.datetime):
        return val.date()
    if isinstance(val, datetime.date):
        return val
    return datetime.datetime.strptime(str(val).strip()[:10], "%Y-%m-%d").date()


def mean_std(vals):
    clean = [v for v in vals if v is not None]
    if not clean:
        return None, None
    m = sum(clean) / len(clean)
    if len(clean) < 2:
        return m, 0.0
    var = sum((x - m) ** 2 for x in clean) / (len(clean) - 1)
    return m, math.sqrt(var)


def ajustar_largura_colunas(ws):
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val = str(cell.value or "")
            if len(val) > 45 and getattr(cell, "alignment", None) and cell.alignment.horizontal == "left":
                continue
            max_len = max(max_len, len(val))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)


def aplicar_borda_tabela(ws, min_r, max_r, min_c, max_c):
    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            ws.cell(row=r, column=c).border = BORDER_THIN


def salvar_workbook(wb, caminho_saida):
    os.makedirs(os.path.dirname(os.path.abspath(caminho_saida)), exist_ok=True)
    try:
        wb.save(caminho_saida)
        print(f"[OK] Ficheiro gerado: {caminho_saida}")
        return True
    except PermissionError:
        print(
            f"[AVISO] Não foi possível atualizar '{caminho_saida}': o ficheiro está aberto noutro programa. "
            "Feche-o para permitir a atualização."
        )
        return False


def resolver_caminho_entrada(nome_ou_caminho):
    if os.path.isabs(nome_ou_caminho) and os.path.exists(nome_ou_caminho):
        return nome_ou_caminho
    fontes_dir = os.path.join(script_dir, "fontes")
    for base in [script_dir, fontes_dir, repo_dir, os.getcwd()]:
        cand = os.path.join(base, nome_ou_caminho)
        if os.path.exists(cand):
            return cand
    for search_root in [fontes_dir, script_dir, repo_dir]:
        encontrados = glob.glob(os.path.join(search_root, "**", "*BabyKiwi*.xlsx"), recursive=True)
        if encontrados:
            return encontrados[0]
    return os.path.join(script_dir, nome_ou_caminho)


# ==============================================================================
# EXTRAÇÃO DE DADOS DO EXCEL BabyKiwi Retaill.xlsx
# ==============================================================================
def extrair_dados_babykiwi(caminho_excel):
    """
    Lê as folhas T1, T2, T3, T4 e T5 de 'BabyKiwi Retaill.xlsx' e devolve:
    - dados_folhas: dict[sheet_name] -> lista de registos por linha (data, amostra, dia,
      tipologia, humidades[7], temperaturas[7], firmezas_kg[10], firmezas_n[10], brix[5], acidez[3], médias).
    - t0_info: registo da receção T0 (valores iniciais para a plataforma).
    """
    if not os.path.exists(caminho_excel):
        raise FileNotFoundError(f"Ficheiro Excel não encontrado: {caminho_excel}")

    wb = openpyxl.load_workbook(caminho_excel, data_only=True)

    c_dt = col2idx(COL_DATA)
    c_am = col2idx(COL_AMOSTRA)
    c_fruto = col2idx(COL_FRUTO)
    c_tip = col2idx(COL_TIPOLOGIA)
    c_hum = col2idx(COL_HUMIDADE_INICIO)
    c_temp = col2idx(COL_TEMPERATURA_INICIO)
    c_firm = col2idx(COL_FIRMEZA_INICIO)
    c_brix = col2idx(COL_BRIX_INICIO)
    c_acid = col2idx(COL_ACIDEZ_INICIO)

    dados_folhas = {}
    t0_info = None

    for sheet in FOLHAS_CENARIOS:
        if sheet not in wb.sheetnames:
            raise ValueError(f"Folha '{sheet}' não encontrada em {wb.sheetnames}")
        ws = wb[sheet]

        registos = []
        t0_date = None

        for r in range(LINHA_INICIO_DADOS, ws.max_row + 1):
            dt_val = ws.cell(r, c_dt).value
            am_val = ws.cell(r, c_am).value
            if dt_val is None or am_val is None:
                continue

            data_real = parse_date(dt_val)
            amostra = str(am_val).strip()
            fruto = str(ws.cell(r, c_fruto).value or "BabyKiwi").strip()
            tipologia = str(ws.cell(r, c_tip).value or "").strip()

            if amostra.upper() == "T0" and t0_date is None:
                t0_date = data_real

            dia = (data_real - t0_date).days if t0_date else 0

            hums = [to_float(ws.cell(r, c_hum + i).value) for i in range(7)]
            temps = [to_float(ws.cell(r, c_temp + i).value) for i in range(7)]

            firm_kg = [to_float(ws.cell(r, c_firm + i).value) for i in range(N_FIRMEZA)]
            firm_n = [round(v * GRAVITY_CONSTANT, 2) if v is not None else None for v in firm_kg]
            brix_list = [to_float(ws.cell(r, c_brix + i).value) for i in range(N_BRIX)]
            acid_list = [to_float(ws.cell(r, c_acid + i).value) for i in range(N_ACIDEZ)]

            fm_kg_mean, fm_kg_std = mean_std(firm_kg)
            fm_n_mean, fm_n_std = mean_std(firm_n)
            brix_mean, brix_std = mean_std(brix_list)
            acid_mean, acid_std = mean_std(acid_list)

            reg = {
                "sheet": sheet,
                "data_real": data_real,
                "amostra": amostra,
                "fruto": fruto,
                "tipologia": tipologia,
                "dia": dia,
                "hums": hums,
                "temps": temps,
                "firm_kg": firm_kg,
                "firm_n": firm_n,
                "brix": brix_list,
                "acidez": acid_list,
                "fm_kg_mean": round(fm_kg_mean, 2) if fm_kg_mean is not None else None,
                "fm_kg_std": round(fm_kg_std, 2) if fm_kg_std is not None else None,
                "fm_n_mean": round(fm_n_mean, 2) if fm_n_mean is not None else None,
                "fm_n_std": round(fm_n_std, 2) if fm_n_std is not None else None,
                "brix_mean": round(brix_mean, 2) if brix_mean is not None else None,
                "brix_std": round(brix_std, 2) if brix_std is not None else None,
                "acidez_mean": round(acid_mean, 3) if acid_mean is not None else None,
                "acidez_std": round(acid_std, 3) if acid_std is not None else None,
            }
            registos.append(reg)

            if amostra.upper() == "T0" and t0_info is None:
                t0_info = reg

        dados_folhas[sheet] = registos

    wb.close()
    return dados_folhas, t0_info


# ==============================================================================
# CONSTRUÇÃO DAS TIMELINES CLIMÁTICAS DIÁRIAS (A PARTIR DE T1..T5)
# ==============================================================================
def construir_timeline_continua(registos):
    """
    Constrói um dicionário {date: {'date', 'temp_c', 'hum_pct'}} a partir das linhas
    de uma folha contínua (T1, T2 ou T3), ignorando T0 (Receção).
    """
    t0_date = next((r["data_real"] for r in registos if r["amostra"].upper() == "T0"), None)
    dias = {}

    for reg in registos:
        if reg["amostra"].upper() == "T0":
            continue
        dt = reg["data_real"]
        # Contar quantos dias válidos existem nesta linha
        valid_pairs = [
            (reg["temps"][i], reg["hums"][i])
            for i in range(7)
            if reg["temps"][i] is not None and reg["hums"][i] is not None
        ]
        n = len(valid_pairs)
        if n == 0:
            continue

        # Os n valores representam n dias consecutivos que terminam na data 'dt'
        for idx, (t_val, h_val) in enumerate(valid_pairs):
            d = dt - datetime.timedelta(days=(n - 1 - idx))
            if t0_date and d <= t0_date:
                continue
            dias[d] = {
                "date": d,
                "temp_c": round(float(t_val), 2),
                "hum_pct": round(float(h_val), 2),
            }

    return [dias[d] for d in sorted(dias.keys())]


def criar_arquivo_cenario(caminho_saida, dias_climaticos):
    """
    Gera ficheiro de cenário individual com folha 'Cenario', 100% compatível com o simulador LC-eureka (ui.py):
    Colunas: Segment_ID, Date, Day, Temperature_C, Humidity_Percent, Region, Packaging
    """
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    ws = wb.create_sheet(title="Cenario")
    ws.views.sheetView[0].showGridLines = True
    headers = ["Segment_ID", "Date", "Day", "Temperature_C", "Humidity_Percent", "Region", "Packaging"]
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(1, c)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = ALIGN_CENTER
    ws.row_dimensions[1].height = 24

    for idx, dc in enumerate(dias_climaticos, 1):
        ws.append([
            1,
            dc["date"].strftime("%Y-%m-%d"),
            idx,
            round(dc["temp_c"], 2),
            round(dc["hum_pct"], 2),
            "PT-LVT",
            "bulk",
        ])
        if idx % 2 == 0:
            for c in range(1, len(headers) + 1):
                ws.cell(idx + 1, c).fill = ROW_ALT_FILL
        ws.cell(idx + 1, 1).alignment = ALIGN_CENTER
        ws.cell(idx + 1, 2).alignment = ALIGN_CENTER
        ws.cell(idx + 1, 3).alignment = ALIGN_CENTER

    aplicar_borda_tabela(ws, 1, len(dias_climaticos) + 1, 1, len(headers))
    ajustar_largura_colunas(ws)
    salvar_workbook(wb, caminho_saida)


def construir_timeline_swing(registos_swing, tl_cold_ref):
    """
    Constrói uma única timeline contínua (swing frio <-> 20ºC) a partir de T4 ou T5:
    - Dia 1 (T0+1 = 2026-08-07): preenchido a partir da referência fria (T1 ou T2) se não constar na 1.ª linha.
    - Para cada linha da folha (T4.1..T4.10 ou T5.1..T5.10), percorre os 7 dias cronológicos
      que terminam na data da amostra, dando prioridade aos dias a 20ºC das amostras pares
      (4 dias consecutivos a 20ºC) e preenchendo os dias intermédios (3 dias) com o frio.
    """
    t0_date = next((r["data_real"] for r in registos_swing if r["amostra"].upper() == "T0"), None)
    dias = {}

    # Pré-preencher o dia T0+1 (ex.: 2026-08-07) a partir da folha fria correspondente
    if tl_cold_ref:
        first_cold = tl_cold_ref[0]
        dias[first_cold["date"]] = dict(first_cold)

    # Primeiro aplicar as linhas ímpares (frio + 1.º dia a 20ºC) e depois as pares (que consolidam os 4 dias a 20ºC)
    # Processando por ordem cronológica, cada dia fica com o valor exato da janela da folha T4/T5:
    # - 07..13/08: frio; 14..17/08: 20ºC; 18..20/08: frio; 21..24/08: 20ºC; ...
    for reg in registos_swing:
        if reg["amostra"].upper() == "T0":
            continue
        dt = reg["data_real"]
        num = int(reg["amostra"].split(".")[1])
        is_par = (num % 2 == 0)

        for idx in range(7):
            t_val = reg["temps"][idx]
            h_val = reg["hums"][idx]
            if t_val is None or h_val is None:
                continue
            d = dt - datetime.timedelta(days=(6 - idx))
            if t0_date and d <= t0_date:
                continue
            # Nas linhas ímpares (ex: 21/08), só preencher os dias ainda não cobertos (os 3 dias de frio 18..20/08 + 21/08)
            # Nas linhas pares (ex: 24/08), atualizar os 4 dias a 20ºC (idx 3..6)
            if is_par:
                if idx >= 3 or d not in dias:
                    dias[d] = {"date": d, "temp_c": round(float(t_val), 2), "hum_pct": round(float(h_val), 2)}
            else:
                if d not in dias:
                    dias[d] = {"date": d, "temp_c": round(float(t_val), 2), "hum_pct": round(float(h_val), 2)}

    return [dias[d] for d in sorted(dias.keys())]


def gerar_todos_cenarios(dados_folhas, cenarios_dir):
    """
    Gera os 5 ficheiros de cenários climáticos (1 por cada folha T1..T5) a partir de T0 (2026-08-06):
    - T1 (2ºC, 42 dias), T2 (5ºC, 42 dias), T3 (20ºC, 18 dias)
    - T4 (2ºC <-> 20ºC, 39 dias), T5 (5ºC <-> 20ºC, 39 dias)
    """
    os.makedirs(cenarios_dir, exist_ok=True)

    # Limpar eventuais ficheiros antigos de trajetórias separadas T4/T5 (frio*sem)
    for old_f in glob.glob(os.path.join(cenarios_dir, "cenario_babykiwi_t[45]_frio*sem_20c.xlsx")):
        try:
            os.remove(old_f)
        except OSError:
            pass

    tl_t1 = construir_timeline_continua(dados_folhas["T1"])
    tl_t2 = construir_timeline_continua(dados_folhas["T2"])
    tl_t3 = construir_timeline_continua(dados_folhas["T3"])
    tl_t4 = construir_timeline_swing(dados_folhas["T4"], tl_t1)
    tl_t5 = construir_timeline_swing(dados_folhas["T5"], tl_t2)

    criar_arquivo_cenario(os.path.join(cenarios_dir, "cenario_babykiwi_t1_2c.xlsx"), tl_t1)
    criar_arquivo_cenario(os.path.join(cenarios_dir, "cenario_babykiwi_t2_5c.xlsx"), tl_t2)
    criar_arquivo_cenario(os.path.join(cenarios_dir, "cenario_babykiwi_t3_20c.xlsx"), tl_t3)
    criar_arquivo_cenario(os.path.join(cenarios_dir, "cenario_babykiwi_t4_2_20c.xlsx"), tl_t4)
    criar_arquivo_cenario(os.path.join(cenarios_dir, "cenario_babykiwi_t5_5_20c.xlsx"), tl_t5)


# ==============================================================================
# GERAÇÃO DOS FICHEIROS DE VALORES REAIS (MÉDIAS E RÉPLICAS INDIVIDUAIS)
# ==============================================================================
def escrever_tabela_medias(ws, titulo, registos, start_row=1):
    """Escreve um bloco formatado de médias numa folha Excel."""
    headers = [
        "Amostra",
        "Tipologia",
        "Dia",
        "Data",
        "Firmeza Média (N)",
        "Firmeza DP (N)",
        "Firmeza Média (kg/cm²)",
        "Brix Médio (°Bx)",
        "Brix DP (°Bx)",
        "Acidez Média (g/100g)",
        "Acidez DP (g/100g)",
    ]
    n_cols = len(headers)

    ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row, end_column=n_cols)
    c_title = ws.cell(start_row, 1, titulo)
    c_title.fill = TITLE_FILL
    c_title.font = TITLE_FONT
    c_title.alignment = ALIGN_LEFT
    ws.row_dimensions[start_row].height = 26

    h_row = start_row + 1
    for c_idx, h in enumerate(headers, 1):
        cell = ws.cell(h_row, c_idx, h)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = ALIGN_CENTER
    ws.row_dimensions[h_row].height = 22

    curr_r = h_row + 1
    for idx, reg in enumerate(registos):
        vals = [
            reg["amostra"],
            reg["tipologia"],
            reg["dia"],
            reg["data_real"].strftime("%Y-%m-%d"),
            reg["fm_n_mean"],
            reg["fm_n_std"],
            reg["fm_kg_mean"],
            reg["brix_mean"],
            reg["brix_std"],
            reg["acidez_mean"],
            reg["acidez_std"],
        ]
        for c_idx, v in enumerate(vals, 1):
            cell = ws.cell(curr_r, c_idx, v)
            if reg["amostra"].upper() == "T0":
                cell.fill = SUMMARY_FILL
                cell.font = SUMMARY_FONT
            elif idx % 2 == 1:
                cell.fill = ROW_ALT_FILL
            cell.alignment = ALIGN_CENTER if c_idx <= 4 else ALIGN_RIGHT
        curr_r += 1

    aplicar_borda_tabela(ws, h_row, curr_r - 1, 1, n_cols)
    return curr_r + 1


def gerar_excel_medias(dados_folhas, t0_info, caminho_saida):
    """
    Gera 'medias_babykiwi.xlsx' com:
    - Resumo_T0_Inicial: parâmetros iniciais (Dia 0) prontos para a plataforma LC-eureka
    - T1_2C, T2_5C, T3_20C: evolução temporal das médias
    - T4_2_20C, T5_5_20C: médias agrupadas por trajetória (T0 -> saída do frio -> +1d 20ºC -> +4d 20ºC)
    """
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # 1. Folha Resumo_T0_Inicial
    ws0 = wb.create_sheet(title="Resumo_T0_Inicial")
    ws0.views.sheetView[0].showGridLines = True

    ws0.merge_cells("A1:E1")
    ws0["A1"] = "BABYKIWI RETAILL — VALORES INICIAIS DE RECEÇÃO (T0 / DIA 0 PARA A PLATAFORMA)"
    ws0["A1"].fill = TITLE_FILL
    ws0["A1"].font = TITLE_FONT
    ws0["A1"].alignment = ALIGN_LEFT
    ws0.row_dimensions[1].height = 26

    headers_t0 = ["Parâmetro", "Valor Inicial (Média T0)", "Desvio-Padrão", "Unidade", "Nº Réplicas"]
    for c_idx, h in enumerate(headers_t0, 1):
        cell = ws0.cell(2, c_idx, h)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = ALIGN_CENTER
    ws0.row_dimensions[2].height = 22

    n_f = sum(1 for x in t0_info["firm_n"] if x is not None)
    n_b = sum(1 for x in t0_info["brix"] if x is not None)
    n_a = sum(1 for x in t0_info["acidez"] if x is not None)

    linhas_t0 = [
        ("Data de Receção (T0)", t0_info["data_real"].strftime("%Y-%m-%d"), "—", "YYYY-MM-DD", "—"),
        ("Firmeza Inicial (Plataforma)", t0_info["fm_n_mean"], t0_info["fm_n_std"], "N", n_f),
        ("Firmeza Inicial (Penetrometria)", t0_info["fm_kg_mean"], t0_info["fm_kg_std"], "kg/cm²", n_f),
        ("Brix Inicial (TSS)", t0_info["brix_mean"], t0_info["brix_std"], "°Bx", n_b),
        ("Acidez Inicial (Ácido Málico)", t0_info["acidez_mean"], t0_info["acidez_std"], "g/100 g", n_a),
    ]
    for r_idx, row_vals in enumerate(linhas_t0, 3):
        for c_idx, v in enumerate(row_vals, 1):
            cell = ws0.cell(r_idx, c_idx, v)
            cell.fill = SUMMARY_FILL if r_idx in (4, 6, 7) else ROW_ALT_FILL
            cell.font = SUMMARY_FONT if c_idx <= 2 and r_idx in (4, 6, 7) else Font(name=FONT_NAME, size=11)
            cell.alignment = ALIGN_LEFT if c_idx == 1 else ALIGN_CENTER
    aplicar_borda_tabela(ws0, 2, 2 + len(linhas_t0), 1, len(headers_t0))
    ajustar_largura_colunas(ws0)

    # 2. Folhas T1..T5 (1 tabela contínua por folha)
    map_folhas = [
        ("T1", "T1_2C", "BABYKIWI — T1 (Conservação contínua a 2ºC)"),
        ("T2", "T2_5C", "BABYKIWI — T2 (Conservação contínua a 5ºC)"),
        ("T3", "T3_20C", "BABYKIWI — T3 (Prateleira contínua a 20ºC)"),
        ("T4", "T4_2_20C", "BABYKIWI — T4 (Alternância 2ºC <-> 20ºC)"),
        ("T5", "T5_5_20C", "BABYKIWI — T5 (Alternância 5ºC <-> 20ºC)"),
    ]
    for src_sheet, dst_sheet, titulo in map_folhas:
        ws = wb.create_sheet(title=dst_sheet)
        ws.views.sheetView[0].showGridLines = True
        escrever_tabela_medias(ws, titulo, dados_folhas[src_sheet], start_row=1)
        ajustar_largura_colunas(ws)

    salvar_workbook(wb, caminho_saida)


def gerar_excel_detalhado(dados_folhas, caminho_saida):
    """Gera 'valores_reais_detalhado.xlsx' com todas as réplicas numéricas por folha (T1..T5)."""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    headers = (
        ["Amostra", "Tipologia", "Dia", "Data"]
        + [f"Firmeza_{i} (kg/cm²)" for i in range(1, N_FIRMEZA + 1)]
        + ["Firmeza Média (N)"]
        + [f"Brix_{i} (°Bx)" for i in range(1, N_BRIX + 1)]
        + ["Brix Médio (°Bx)"]
        + [f"Acidez_{i} (g/100g)" for i in range(1, N_ACIDEZ + 1)]
        + ["Acidez Média (g/100g)"]
    )

    for sheet in FOLHAS_CENARIOS:
        ws = wb.create_sheet(title=sheet)
        ws.views.sheetView[0].showGridLines = True
        ws.append(headers)
        for c in range(1, len(headers) + 1):
            cell = ws.cell(1, c)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.alignment = ALIGN_CENTER
        ws.row_dimensions[1].height = 24

        for r_idx, reg in enumerate(dados_folhas[sheet], 2):
            row = (
                [reg["amostra"], reg["tipologia"], reg["dia"], reg["data_real"].strftime("%Y-%m-%d")]
                + reg["firm_kg"]
                + [reg["fm_n_mean"]]
                + reg["brix"]
                + [reg["brix_mean"]]
                + reg["acidez"]
                + [reg["acidez_mean"]]
            )
            ws.append(row)
            if reg["amostra"].upper() == "T0":
                for c in range(1, len(headers) + 1):
                    ws.cell(r_idx, c).fill = SUMMARY_FILL
                    ws.cell(r_idx, c).font = SUMMARY_FONT
            elif r_idx % 2 == 1:
                for c in range(1, len(headers) + 1):
                    ws.cell(r_idx, c).fill = ROW_ALT_FILL

        aplicar_borda_tabela(ws, 1, len(dados_folhas[sheet]) + 1, 1, len(headers))
        ajustar_largura_colunas(ws)

    salvar_workbook(wb, caminho_saida)


def main():
    default_input = resolver_caminho_entrada(FICHEIRO_ENTRADA)
    parser = argparse.ArgumentParser(
        description="Extrai e gera Valores Reais e Cenários Climáticos para BabyKiwi Retaill (T1..T5)."
    )
    parser.add_argument(
        "--input",
        default=default_input,
        help="Caminho do ficheiro 'BabyKiwi Retaill.xlsx'.",
    )
    parser.add_argument(
        "--valores-dir",
        default=os.path.join(script_dir, "babykiwi_retaill", "valores_reais"),
        help="Pasta de saída para os ficheiros Excel de valores reais.",
    )
    parser.add_argument(
        "--cenarios-dir",
        default=os.path.join(script_dir, "babykiwi_retaill"),
        help="Pasta de saída para os cenários climáticos compatíveis com LC-eureka.",
    )
    args = parser.parse_args()

    print("=" * 75)
    print("BABYKIWI RETAILL: GERAÇÃO DE VALORES REAIS E CENÁRIOS CLIMÁTICOS")
    print("=" * 75)
    print(f"Ficheiro de Entrada: {args.input}")
    print(f"Diretoria Valores:   {args.valores_dir}")
    print(f"Diretoria Cenários:  {args.cenarios_dir}")

    dados_folhas, t0_info = extrair_dados_babykiwi(args.input)
    print(
        f"\n[T0 Receção | {t0_info['data_real']}] "
        f"Firmeza = {t0_info['fm_n_mean']} N ({t0_info['fm_kg_mean']} kg/cm²) | "
        f"Brix = {t0_info['brix_mean']} °Bx | "
        f"Acidez = {t0_info['acidez_mean']} g/100g"
    )

    print("\n--- 1. Valores Reais (Médias e Réplicas Individuais) ---")
    gerar_excel_medias(dados_folhas, t0_info, os.path.join(args.valores_dir, "medias_babykiwi.xlsx"))
    gerar_excel_detalhado(dados_folhas, os.path.join(args.valores_dir, "valores_reais_detalhado.xlsx"))

    print("\n--- 2. Cenários Climáticos Compatíveis com LC-eureka (ui.py) ---")
    gerar_todos_cenarios(dados_folhas, args.cenarios_dir)

    print("\n" + "=" * 75)
    print("TODOS OS EXCELS DE BABYKIWI FORAM GERADOS COM SUCESSO!")
    print("=" * 75)


if __name__ == "__main__":
    main()
