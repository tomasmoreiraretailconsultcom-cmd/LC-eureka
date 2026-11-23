# -*- coding: utf-8 -*-
"""
processar_amostra_camaras.py

Processa os 63 lotes com histórico de frio da folha '2025 2026' do ficheiro:
'CATF.IP23-Controlo Qualidade Embalamento v1.4-18-2-2025 GALA+GOLDEN vf.xlsx'

Gera para cada lote uma pasta individual dentro de 'cenarios_prof/amostra_camaras/':
  - cenario_lote_XX_...xlsx : Cenário diário compatível com a app (folha única 'Cenario')
  - valores_reais_lote_XX_...xlsx : 11 valores reais (10 maçãs + média) para Firmeza e Brix
    (Valores iniciais T0 importados de 'Base de dados Maçã (Retaill) experiencias ESS_UTP.xlsx'
     e valores finais medidos no embalamento da câmara)

Gera ainda um ficheiro de índice geral:
  - resumo_todos_lotes_amostra_camaras.xlsx
"""

import os
import sys
import glob
import datetime
from datetime import timedelta

# Forçar stdout em utf-8 no Windows se necessário
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter, column_index_from_string

# Constante de conversão de Firmeza: 1 kg/cm2 = 9.80665 N
KG_TO_N = 9.80665

# Caminhos base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTES_DIR = os.path.join(BASE_DIR, "fontes")
OUTPUT_DIR = os.path.join(BASE_DIR, "amostra_camaras_macas")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==============================================================================
# CONSTANTES DE CONFIGURAÇÃO (FICHEIROS, FOLHAS E POSIÇÃO DAS COLUNAS)
# Qualquer alteração futura (ex: coluna Data passar de 'B' para 'D', ou novo nome
# de ficheiro) pode ser feita alterando apenas as constantes abaixo.
# Aceita letras de colunas ('A', 'B', ...) ou números inteiros (1, 2, ...).
# ==============================================================================
# Ficheiros e Folhas
FICHEIRO_CAMARAS = "CATF.IP23-Controlo Qualidade Embalamento v1.4-18-2-2025 GALA+GOLDEN vf.xlsx"
FOLHA_CAMARAS = "2025 2026"
LINHA_INICIO_DADOS_CAMARAS = 5

FICHEIRO_ESS_UTP = "Base de dados Maçã (Retaill) experiencias ESS_UTP.xlsx"
FOLHA_ESS_UTP = "Amostra Coop (Frio <2ºC)"

# Colunas da folha de controlo de câmaras (pode usar letras 'A', 'B'... ou números 1, 2...)
COL_CAM_PRODUTOR = "A"           # Col 1: Produtor
COL_CAM_DATA_ENTRADA_FRIO = "B"  # Col 2: data entrada frio (se mudar para 'D', mudar aqui!)
COL_CAM_REFUGO_ENTRADA = "C"     # Col 3: % REFUGO (Perdas entrada)
COL_CAM_TIPO_CAMARA = "D"        # Col 4: Tipo de Camara (N/AM)
COL_CAM_TEMP_FRIO = "E"          # Col 5: Temp frio ºC
COL_CAM_HUMIDADE_FRIO = "F"      # Col 6: Humidade (%)
COL_CAM_TEMPO_FRIO_SEM = "G"     # Col 7: Tempo frio (s)
COL_CAM_DATA_EMBALAMENTO = "H"   # Col 8: Data de embalamento/EXPEDIÇÃO CLIENTE
COL_CAM_PRODUTO = "I"            # Col 9: Produto
COL_CAM_VARIEDADE = "J"          # Col 10: Variedade
COL_CAM_CALIBRE = "K"            # Col 11: Calibre
COL_CAM_CATEGORIA = "L"          # Col 12: Categoria
COL_CAM_COLORACAO = "M"          # Col 13: Coloração
COL_CAM_QTD_CAIXAS = "N"         # Col 14: Qtd caixas

# Firmeza / Penetrometria (10 Frutos das colunas Q a Z = 17 a 26, Média na coluna AA = 27)
COL_CAM_FIRMEZA_FRUTO1 = "Q"     # Col 17
COL_CAM_FIRMEZA_MEDIA = "AA"     # Col 27

# Brix (10 Frutos das colunas AB a AK = 28 a 37, Média na coluna AL = 38)
COL_CAM_BRIX_FRUTO1 = "AB"       # Col 28
COL_CAM_BRIX_MEDIA = "AL"        # Col 38

# Colunas de T0 na folha ESS_UTP (Amostra Coop)
COL_ESS_PRODUTOR = "A"            # Col 1
COL_ESS_DATA = "B"                # Col 2
COL_ESS_VARIEDADE = "C"           # Col 3
COL_ESS_AMOSTRA = "D"             # Col 4
COL_ESS_FIRMEZA_FRUTO1 = "S"      # Col 19: Fruto 1 (10 frutos)
COL_ESS_BRIX_FRUTO1 = "AC"        # Col 29: Fruto 1 (5 frutos)
COL_ESS_ACIDEZ = "AH"             # Col 34: g ácido málico/100 g

# Linhas de T0 em ESS_UTP
LINHA_ESS_GALA_AMPS_T0 = 3
LINHA_ESS_GALA_CJL_T0 = 4
LINHA_ESS_GOLDEN_AMPS_T0 = 19
LINHA_ESS_GOLDEN_CJL_T0 = 20

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

# Cores e Estilos (Segoe UI)
FONT_FAMILY = "Segoe UI"
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")       # Azul Escuro
SUBHEADER_FILL = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")    # Azul Intermédio
SECTION_FILL = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")      # Azul Muito Claro
ACCENT_FILL = PatternFill(start_color="F2F4F8", end_color="F2F4F8", fill_type="solid")       # Cinza Suave Alternado
WHITE_BOLD_FONT = Font(name=FONT_FAMILY, size=11, bold=True, color="FFFFFF")
DARK_BOLD_FONT = Font(name=FONT_FAMILY, size=11, bold=True, color="1F4E79")
TITLE_FONT = Font(name=FONT_FAMILY, size=14, bold=True, color="1F4E79")
SUBTITLE_FONT = Font(name=FONT_FAMILY, size=10, italic=True, color="595959")
REGULAR_FONT = Font(name=FONT_FAMILY, size=10, color="000000")
BOLD_FONT = Font(name=FONT_FAMILY, size=10, bold=True, color="000000")

ALIGN_CENTER = Alignment(horizontal="center", vertical="center")
ALIGN_LEFT = Alignment(horizontal="left", vertical="center")
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")

BORDER_THIN = Border(
    left=Side(style="thin", color="D9D9D9"),
    right=Side(style="thin", color="D9D9D9"),
    top=Side(style="thin", color="D9D9D9"),
    bottom=Side(style="thin", color="D9D9D9")
)
BORDER_BOTTOM_DOUBLE = Border(
    left=Side(style="thin", color="D9D9D9"),
    right=Side(style="thin", color="D9D9D9"),
    top=Side(style="thin", color="D9D9D9"),
    bottom=Side(style="double", color="1F4E79")
)

def clean_num(val):
    """Limpa e converte valores numéricos que possam vir com vírgulas duplas ou texto."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(",,", ".").replace(",", ".")
    try:
        return float(s)
    except:
        return None

def clean_produtor(p):
    """Normaliza nomes de produtores."""
    if not p:
        return "desconhecido"
    s = str(p).strip()
    s_upper = s.upper()
    if "ALG" in s_upper:
        return "ALG"
    if "CJ" in s_upper:
        return "CJGL"
    if "AMPS" in s_upper:
        return "AMPS"
    if "EFM" in s_upper:
        return "EFM"
    if "MNMPC" in s_upper:
        return "MNMPC"
    return s_upper

def clean_variedade(v):
    """Normaliza nomes de variedades (Gala / Golden)."""
    if not v:
        return "Gala"
    s = str(v).strip().lower()
    if "golden" in s:
        return "Golden"
    return "Gala"

def clean_calibre_str(cal):
    """Formata calibre para nome seguro em pasta e ficheiro."""
    if cal is None:
        return "cal_nd"
    s = str(cal).strip().replace("/", "_").replace("+", "plus").replace(" ", "")
    return f"cal{s}"

def extrair_t0_ess():
    """
    Extrai os valores de referência inicial T0 de 'Base de dados Maçã (Retaill) experiencias ESS_UTP.xlsx'
    para Gala e Golden (AMPS, CJL e média geral).
    """
    caminho_ess = resolver_caminho_ficheiro(FICHEIRO_ESS_UTP, FONTES_DIR, "*experiencias ESS_UTP*.xlsx")
    if not os.path.exists(caminho_ess):
        caminho_ess = resolver_caminho_ficheiro(FICHEIRO_ESS_UTP, BASE_DIR, "*experiencias ESS_UTP*.xlsx")
    wb = openpyxl.load_workbook(caminho_ess, data_only=True)
    nome_folha = FOLHA_ESS_UTP if FOLHA_ESS_UTP in wb.sheetnames else wb.sheetnames[0]
    ws = wb[nome_folha]
    
    t0_data = {
        "Gala": {"AMPS": {}, "CJL": {}, "Geral": {}},
        "Golden": {"AMPS": {}, "CJL": {}, "Geral": {}}
    }
    
    row_mapping = {
        LINHA_ESS_GALA_AMPS_T0: ("Gala", "AMPS"),
        LINHA_ESS_GALA_CJL_T0: ("Gala", "CJL"),
        LINHA_ESS_GOLDEN_AMPS_T0: ("Golden", "AMPS"),
        LINHA_ESS_GOLDEN_CJL_T0: ("Golden", "CJL")
    }
    
    c_f_start = col2idx(COL_ESS_FIRMEZA_FRUTO1)
    c_b_start = col2idx(COL_ESS_BRIX_FRUTO1)
    c_acidez = col2idx(COL_ESS_ACIDEZ)
    
    for r, (var, prod) in row_mapping.items():
        f_vals = [clean_num(ws.cell(r, c_f_start + i).value) for i in range(10)]
        f_med = sum(f_vals) / len(f_vals) if f_vals else None
        
        # Brix: medido em 5 maçãs em ESS_UTP
        b_vals_5 = [clean_num(ws.cell(r, c_b_start + i).value) for i in range(5)]
        b_med = sum(b_vals_5) / len(b_vals_5) if b_vals_5 else None
        b_vals_10 = b_vals_5 + [None] * (10 - len(b_vals_5))
        
        acidez = clean_num(ws.cell(r, c_acidez).value)
        
        t0_data[var][prod] = {
            "f_vals": f_vals,
            "f_med_kg": f_med,
            "f_med_n": f_med * KG_TO_N if f_med else None,
            "b_vals": b_vals_10,
            "b_med": b_med,
            "acidez": acidez
        }
    
    # Calcular médias gerais de T0 para Gala e Golden
    for var in ["Gala", "Golden"]:
        p1 = t0_data[var]["AMPS"]
        p2 = t0_data[var]["CJL"]
        
        f_vals_geral = []
        for i in range(10):
            v1 = p1["f_vals"][i] if i < len(p1["f_vals"]) else None
            v2 = p2["f_vals"][i] if i < len(p2["f_vals"]) else None
            if v1 is not None and v2 is not None:
                f_vals_geral.append(round((v1 + v2) / 2.0, 2))
            elif v1 is not None:
                f_vals_geral.append(v1)
            elif v2 is not None:
                f_vals_geral.append(v2)
            else:
                f_vals_geral.append(None)
                
        f_med_geral = sum(f_vals_geral) / len(f_vals_geral)
        
        b_vals_geral = []
        for i in range(5):
            v1 = p1["b_vals"][i]
            v2 = p2["b_vals"][i]
            if v1 is not None and v2 is not None:
                b_vals_geral.append(round((v1 + v2) / 2.0, 2))
            elif v1 is not None:
                b_vals_geral.append(v1)
            elif v2 is not None:
                b_vals_geral.append(v2)
            else:
                b_vals_geral.append(None)
        b_vals_geral_10 = b_vals_geral + [None] * 5
        b_med_geral = sum(b_vals_geral) / len(b_vals_geral)
        
        acidez_geral = round((p1["acidez"] + p2["acidez"]) / 2.0, 4) if (p1["acidez"] and p2["acidez"]) else (p1["acidez"] or p2["acidez"])
        
        t0_data[var]["Geral"] = {
            "f_vals": f_vals_geral,
            "f_med_kg": f_med_geral,
            "f_med_n": f_med_geral * KG_TO_N,
            "b_vals": b_vals_geral_10,
            "b_med": b_med_geral,
            "acidez": acidez_geral
        }
        
    return t0_data

def extrair_lotes_camaras():
    """
    Lê o ficheiro de controlo de câmaras e extrai os 63 lotes com câmara de frio preenchida.
    """
    caminho_cam = resolver_caminho_ficheiro(FICHEIRO_CAMARAS, FONTES_DIR, "*Controlo Qualidade Embalamento*.xlsx")
    if not os.path.exists(caminho_cam):
        caminho_cam = resolver_caminho_ficheiro(FICHEIRO_CAMARAS, BASE_DIR, "*Controlo Qualidade Embalamento*.xlsx")
    wb = openpyxl.load_workbook(caminho_cam, data_only=True)
    nome_folha = FOLHA_CAMARAS if FOLHA_CAMARAS in wb.sheetnames else "2025 2026"
    ws = wb[nome_folha]
    
    c_prod = col2idx(COL_CAM_PRODUTOR)
    c_dt_frio = col2idx(COL_CAM_DATA_ENTRADA_FRIO)
    c_camara = col2idx(COL_CAM_TIPO_CAMARA)
    c_temp = col2idx(COL_CAM_TEMP_FRIO)
    c_hum = col2idx(COL_CAM_HUMIDADE_FRIO)
    c_tempo_sem = col2idx(COL_CAM_TEMPO_FRIO_SEM)
    c_dt_emb = col2idx(COL_CAM_DATA_EMBALAMENTO)
    c_prod_nome = col2idx(COL_CAM_PRODUTO)
    c_var = col2idx(COL_CAM_VARIEDADE)
    c_calibre = col2idx(COL_CAM_CALIBRE)
    c_cat = col2idx(COL_CAM_CATEGORIA)
    c_color = col2idx(COL_CAM_COLORACAO)
    c_qtd = col2idx(COL_CAM_QTD_CAIXAS)
    c_f_start = col2idx(COL_CAM_FIRMEZA_FRUTO1)
    c_f_med = col2idx(COL_CAM_FIRMEZA_MEDIA)
    c_b_start = col2idx(COL_CAM_BRIX_FRUTO1)
    c_b_med = col2idx(COL_CAM_BRIX_MEDIA)
    
    lotes = []
    
    for r in range(LINHA_INICIO_DADOS_CAMARAS, ws.max_row + 1):
        dt_frio = ws.cell(r, c_dt_frio).value
        temp_val = ws.cell(r, c_temp).value
        
        # Filtra apenas linhas com histórico de frio preenchido
        if dt_frio is not None and temp_val is not None:
            prod_raw = ws.cell(r, c_prod).value
            camara_raw = ws.cell(r, c_camara).value
            hum_val = ws.cell(r, c_hum).value
            tempo_frio_sem = ws.cell(r, c_tempo_sem).value
            dt_emb = ws.cell(r, c_dt_emb).value
            prod_nome = ws.cell(r, c_prod_nome).value
            var_raw = ws.cell(r, c_var).value
            calibre_raw = ws.cell(r, c_calibre).value
            categoria_raw = ws.cell(r, c_cat).value
            coloracao_raw = ws.cell(r, c_color).value
            qtd_caixas = ws.cell(r, c_qtd).value
            
            # Limpeza de campos
            produtor = clean_produtor(prod_raw)
            variedade = clean_variedade(var_raw)
            camara = str(camara_raw).strip().upper() if camara_raw else "N"
            temp_c = clean_num(temp_val)
            hum_p = clean_num(hum_val)
            tempo_sem = clean_num(tempo_frio_sem)
            
            # Garantir formato datetime
            if hasattr(dt_frio, "date"):
                dt_frio_dt = datetime.datetime.combine(dt_frio.date(), datetime.time(0, 0))
            else:
                dt_frio_dt = dt_frio
                
            if hasattr(dt_emb, "date"):
                dt_emb_dt = datetime.datetime.combine(dt_emb.date(), datetime.time(0, 0))
            else:
                dt_emb_dt = dt_emb
                
            dias_em_frio = (dt_emb_dt.date() - dt_frio_dt.date()).days
            
            # 10 medições de penetrometria (Kg/cm2) e média
            f_vals = [clean_num(ws.cell(r, c_f_start + i).value) for i in range(10)]
            f_med = clean_num(ws.cell(r, c_f_med).value)
            if f_med is None and f_vals:
                valid_f = [x for x in f_vals if x is not None]
                if valid_f:
                    f_med = sum(valid_f) / len(valid_f)
            f_med_n = f_med * KG_TO_N if f_med is not None else None
            
            # 10 medições de Brix e média
            b_vals = [clean_num(ws.cell(r, c_b_start + i).value) for i in range(10)]
            b_med = clean_num(ws.cell(r, c_b_med).value)
            if b_med is None and b_vals:
                valid_b = [x for x in b_vals if x is not None]
                if valid_b:
                    b_med = sum(valid_b) / len(valid_b)
                    
            lotes.append({
                "row_idx": r,
                "produtor": produtor,
                "variedade": variedade,
                "camara": camara,
                "calibre": calibre_raw,
                "calibre_str": clean_calibre_str(calibre_raw),
                "categoria": categoria_raw,
                "coloracao": coloracao_raw,
                "qtd_caixas": qtd_caixas,
                "dt_frio": dt_frio_dt,
                "dt_emb": dt_emb_dt,
                "dias_frio": dias_em_frio,
                "tempo_semanas": tempo_sem,
                "temp_c": temp_c,
                "hum_p": hum_p,
                "f_vals": f_vals,
                "f_med_kg": f_med,
                "f_med_n": f_med_n,
                "b_vals": b_vals,
                "b_med": b_med
            })
            
    return lotes

def criar_excel_cenario(lote, filepath):
    """
    Cria o ficheiro de cenário climático (.xlsx) com a folha única 'Cenario'.
    Segment_ID, Date, Day, Temperature_C, Humidity_Percent, Region, Packaging
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Cenario"
    ws.views.sheetView[0].showGridLines = True
    
    headers = [
        "Segment_ID", "Date", "Day", "Temperature_C", "Humidity_Percent", "Region", "Packaging"
    ]
    ws.append(headers)
    
    # Formatar cabeçalho
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = HEADER_FILL
        cell.font = WHITE_BOLD_FONT
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_THIN
    ws.row_dimensions[1].height = 26
    
    start_date = lote["dt_frio"].date()
    end_date = lote["dt_emb"].date()
    total_days = (end_date - start_date).days + 1  # inclusivo
    
    for day_num in range(1, total_days + 1):
        curr_date = start_date + timedelta(days=day_num - 1)
        row_vals = [
            1,                                      # Segment_ID
            curr_date.strftime("%Y-%m-%d"),         # Date
            day_num,                                # Day
            round(lote["temp_c"], 2),               # Temperature_C
            round(lote["hum_p"], 2),                # Humidity_Percent
            "PT-LVT",                               # Region
            "bulk"                                  # Packaging
        ]
        ws.append(row_vals)
        
        row_idx = day_num + 1
        ws.row_dimensions[row_idx].height = 20
        for col_idx in range(1, len(row_vals) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = REGULAR_FONT
            cell.border = BORDER_THIN
            if col_idx in [1, 2, 3]:
                cell.alignment = ALIGN_CENTER
            elif col_idx in [4, 5]:
                cell.alignment = ALIGN_RIGHT
                cell.number_format = "0.00"
            else:
                cell.alignment = ALIGN_CENTER
                
    # Auto-ajuste de largura de colunas
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
        
    wb.save(filepath)

def criar_excel_valores_reais(lote, t0_info, filepath):
    """
    Cria o ficheiro de valores reais de referência com 10 maçãs + média
    para Firmeza e Brix, em T0 (início) e no Embalamento (saída).
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Valores_Reais"
    ws.views.sheetView[0].showGridLines = True
    
    # 1. TÍTULO E METADADOS DO LOTE
    ws.cell(1, 1, f"Amostra Câmaras — Lote {lote['id_str']}")
    ws.cell(1, 1).font = TITLE_FONT
    ws.merge_cells("A1:K1")
    ws.row_dimensions[1].height = 28
    
    ws.cell(2, 1, (
        f"Espécie: Maçã {lote['variedade']} | Produtor: {lote['produtor']} | "
        f"Câmara: {lote['camara']} | Calibre: {lote['calibre']} | Linha Excel Original: {lote['row_idx']}"
    ))
    ws.cell(2, 1).font = SUBTITLE_FONT
    ws.merge_cells("A2:K2")
    ws.row_dimensions[2].height = 18
    
    ws.cell(3, 1, (
        f"Período em Frio: {lote['dt_frio'].strftime('%Y-%m-%d')} a {lote['dt_emb'].strftime('%Y-%m-%d')} "
        f"({lote['dias_frio']} dias / {lote['tempo_semanas']} semanas) | "
        f"Condições Câmara: {lote['temp_c']} ºC, {lote['hum_p']:.0f}% HR"
    ))
    ws.cell(3, 1).font = SUBTITLE_FONT
    ws.merge_cells("A3:K3")
    ws.row_dimensions[3].height = 18
    
    curr_row = 5
    
    # 2. TABELA 1: SÍNTESE DOS VALORES REAIS (MÉDIAS)
    ws.cell(curr_row, 1, "1. Síntese dos Valores Médios Reais")
    ws.cell(curr_row, 1).font = DARK_BOLD_FONT
    curr_row += 1
    
    headers_sintese = [
        "Momento", "Data Real", "Dia Cenário", 
        "Firmeza Média (kg/cm²)", "Firmeza Média (N)", 
        "Brix Médio (ºBx)", "Acidez Média (%)", "Origem dos Dados"
    ]
    ws.row_dimensions[curr_row].height = 24
    for c_idx, h in enumerate(headers_sintese, 1):
        cell = ws.cell(curr_row, c_idx, h)
        cell.fill = HEADER_FILL
        cell.font = WHITE_BOLD_FONT
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_THIN
    curr_row += 1
    
    # Linha T0
    row_t0 = [
        "T0 (Entrada Frio)",
        lote["dt_frio"].strftime("%Y-%m-%d"),
        1,
        round(t0_info["f_med_kg"], 2),
        round(t0_info["f_med_n"], 1),
        round(t0_info["b_med"], 2),
        f"{t0_info['acidez']:.3f} %" if t0_info["acidez"] else "-",
        f"Referência ESS_UTP ({t0_info['fonte']})"
    ]
    # Linha Embalamento
    row_emb = [
        "Embalamento (Saída Frio)",
        lote["dt_emb"].strftime("%Y-%m-%d"),
        lote["dias_frio"] + 1,
        round(lote["f_med_kg"], 2) if lote["f_med_kg"] else "-",
        round(lote["f_med_n"], 1) if lote["f_med_n"] else "-",
        round(lote["b_med"], 2) if lote["b_med"] else "-",
        "-",
        f"Medição Câmara (Linha {lote['row_idx']})"
    ]
    
    for r_vals in [row_t0, row_emb]:
        ws.row_dimensions[curr_row].height = 20
        for c_idx, val in enumerate(r_vals, 1):
            cell = ws.cell(curr_row, c_idx, val)
            cell.font = REGULAR_FONT
            cell.border = BORDER_THIN
            if c_idx in [1, 8]:
                cell.alignment = ALIGN_LEFT
            elif c_idx in [2, 3]:
                cell.alignment = ALIGN_CENTER
            else:
                cell.alignment = ALIGN_RIGHT
        curr_row += 1
        
    curr_row += 2
    
    # 3. TABELA 2: DETALHE FRUTO A FRUTO — FIRMEZA (kg/cm² e N)
    ws.cell(curr_row, 1, "2. Firmeza Fruto a Fruto — 10 Frutos e Média (kg/cm² e Newtons)")
    ws.cell(curr_row, 1).font = DARK_BOLD_FONT
    curr_row += 1
    
    headers_f = ["Momento", "Data Real"] + [f"Fruto {i}" for i in range(1, 11)] + ["Média (kg/cm²)", "Média (N)"]
    ws.row_dimensions[curr_row].height = 24
    for c_idx, h in enumerate(headers_f, 1):
        cell = ws.cell(curr_row, c_idx, h)
        cell.fill = SUBHEADER_FILL
        cell.font = WHITE_BOLD_FONT
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_THIN
    curr_row += 1
    
    # Firmeza T0
    f_row_t0 = ["T0 (Entrada Frio)", lote["dt_frio"].strftime("%Y-%m-%d")]
    for val in t0_info["f_vals"]:
        f_row_t0.append(round(val, 2) if val is not None else "-")
    f_row_t0.append(round(t0_info["f_med_kg"], 2))
    f_row_t0.append(round(t0_info["f_med_n"], 1))
    
    # Firmeza Embalamento
    f_row_emb = ["Embalamento (Saída Frio)", lote["dt_emb"].strftime("%Y-%m-%d")]
    for val in lote["f_vals"]:
        f_row_emb.append(round(val, 2) if val is not None else "-")
    f_row_emb.append(round(lote["f_med_kg"], 2) if lote["f_med_kg"] else "-")
    f_row_emb.append(round(lote["f_med_n"], 1) if lote["f_med_n"] else "-")
    
    for r_vals in [f_row_t0, f_row_emb]:
        ws.row_dimensions[curr_row].height = 20
        for c_idx, val in enumerate(r_vals, 1):
            cell = ws.cell(curr_row, c_idx, val)
            cell.font = REGULAR_FONT
            cell.border = BORDER_THIN
            if c_idx == 1:
                cell.alignment = ALIGN_LEFT
            elif c_idx == 2:
                cell.alignment = ALIGN_CENTER
            elif c_idx in [13, 14]:
                cell.font = BOLD_FONT
                cell.alignment = ALIGN_RIGHT
            else:
                cell.alignment = ALIGN_RIGHT
        curr_row += 1
        
    curr_row += 2
    
    # 4. TABELA 3: DETALHE FRUTO A FRUTO — BRIX (ºBx)
    ws.cell(curr_row, 1, "3. Teor de Sólidos Solúveis (ºBrix) — 10 Frutos e Média")
    ws.cell(curr_row, 1).font = DARK_BOLD_FONT
    curr_row += 1
    
    headers_b = ["Momento", "Data Real"] + [f"Fruto {i}" for i in range(1, 11)] + ["Média (ºBx)"]
    ws.row_dimensions[curr_row].height = 24
    for c_idx, h in enumerate(headers_b, 1):
        cell = ws.cell(curr_row, c_idx, h)
        cell.fill = SUBHEADER_FILL
        cell.font = WHITE_BOLD_FONT
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_THIN
    curr_row += 1
    
    # Brix T0
    b_row_t0 = ["T0 (Entrada Frio)", lote["dt_frio"].strftime("%Y-%m-%d")]
    for val in t0_info["b_vals"]:
        b_row_t0.append(round(val, 2) if val is not None else "-")
    b_row_t0.append(round(t0_info["b_med"], 2))
    
    # Brix Embalamento
    b_row_emb = ["Embalamento (Saída Frio)", lote["dt_emb"].strftime("%Y-%m-%d")]
    for val in lote["b_vals"]:
        b_row_emb.append(round(val, 2) if val is not None else "-")
    b_row_emb.append(round(lote["b_med"], 2) if lote["b_med"] else "-")
    
    for r_vals in [b_row_t0, b_row_emb]:
        ws.row_dimensions[curr_row].height = 20
        for c_idx, val in enumerate(r_vals, 1):
            cell = ws.cell(curr_row, c_idx, val)
            cell.font = REGULAR_FONT
            cell.border = BORDER_THIN
            if c_idx == 1:
                cell.alignment = ALIGN_LEFT
            elif c_idx == 2:
                cell.alignment = ALIGN_CENTER
            elif c_idx == 13:
                cell.font = BOLD_FONT
                cell.alignment = ALIGN_RIGHT
            else:
                cell.alignment = ALIGN_RIGHT
        curr_row += 1

    # Auto-ajuste de colunas
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            if cell.row in [1, 2, 3]:
                continue
            v = str(cell.value or "")
            if len(v) > max_len:
                max_len = len(v)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 11)
        
    wb.save(filepath)

def criar_resumo_todos_lotes(lotes, filepath):
    """
    Cria uma tabela mestre de índice geral com todos os 63 lotes processados.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Resumo_Lotes_Camaras"
    ws.views.sheetView[0].showGridLines = True
    
    headers = [
        "Lote", "Linha Original", "Espécie", "Produtor", "Câmara", "Calibre",
        "Data Entrada Frio", "Data Embalamento", "Dias Frio", "Semanas",
        "Temp (ºC)", "Humidade (%)",
        "Firmeza T0 (kg/cm²)", "Firmeza T0 (N)", "Firmeza Emb (kg/cm²)", "Firmeza Emb (N)", "Delta Firmeza (N)",
        "Brix T0 (ºBx)", "Brix Emb (ºBx)", "Delta Brix (ºBx)",
        "Pasta do Lote"
    ]
    
    ws.append(headers)
    for c_idx in range(1, len(headers) + 1):
        cell = ws.cell(1, c_idx)
        cell.fill = HEADER_FILL
        cell.font = WHITE_BOLD_FONT
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_THIN
    ws.row_dimensions[1].height = 26
    
    for idx, lote in enumerate(lotes, 1):
        f_t0_n = lote["t0_info"]["f_med_n"]
        f_emb_n = lote["f_med_n"]
        delta_f_n = (f_emb_n - f_t0_n) if (f_emb_n and f_t0_n) else None
        
        b_t0 = lote["t0_info"]["b_med"]
        b_emb = lote["b_med"]
        delta_b = (b_emb - b_t0) if (b_emb and b_t0) else None
        
        row_vals = [
            lote["id_str"],
            lote["row_idx"],
            lote["variedade"],
            lote["produtor"],
            lote["camara"],
            str(lote["calibre"]),
            lote["dt_frio"].strftime("%Y-%m-%d"),
            lote["dt_emb"].strftime("%Y-%m-%d"),
            lote["dias_frio"],
            lote["tempo_semanas"],
            round(lote["temp_c"], 2),
            round(lote["hum_p"], 1),
            round(lote["t0_info"]["f_med_kg"], 2),
            round(f_t0_n, 1),
            round(lote["f_med_kg"], 2) if lote["f_med_kg"] else "-",
            round(f_emb_n, 1) if f_emb_n else "-",
            round(delta_f_n, 1) if delta_f_n is not None else "-",
            round(b_t0, 2),
            round(b_emb, 2) if b_emb else "-",
            round(delta_b, 2) if delta_b is not None else "-",
            lote["folder_name"]
        ]
        ws.append(row_vals)
        r_idx = idx + 1
        ws.row_dimensions[r_idx].height = 20
        
        for c_idx, val in enumerate(row_vals, 1):
            cell = ws.cell(r_idx, c_idx)
            cell.font = REGULAR_FONT
            cell.border = BORDER_THIN
            if c_idx in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
                cell.alignment = ALIGN_CENTER
            elif c_idx == len(row_vals):
                cell.alignment = ALIGN_LEFT
            else:
                cell.alignment = ALIGN_RIGHT
                
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 11)
        
    wb.save(filepath)

def main():
    print("=" * 70)
    print("PROCESSAMENTO DOS CENÁRIOS E VALORES REAIS - AMOSTRA CÂMARAS")
    print("=" * 70)
    
    # 1. Carregar valores T0 da ESS_UTP
    print("\n[1/4] A extrair valores de referência T0 de 'Base de dados Maçã (Retaill) experiencias ESS_UTP.xlsx'...")
    t0_data = extrair_t0_ess()
    print("  [OK] Gala AMPS T0: Firmeza = {:.2f} kg/cm2 ({:.1f} N) | Brix = {:.2f} degBx".format(
        t0_data["Gala"]["AMPS"]["f_med_kg"], t0_data["Gala"]["AMPS"]["f_med_n"], t0_data["Gala"]["AMPS"]["b_med"]))
    print("  [OK] Gala Geral T0: Firmeza = {:.2f} kg/cm2 ({:.1f} N) | Brix = {:.2f} degBx".format(
        t0_data["Gala"]["Geral"]["f_med_kg"], t0_data["Gala"]["Geral"]["f_med_n"], t0_data["Gala"]["Geral"]["b_med"]))
    print("  [OK] Golden AMPS T0: Firmeza = {:.2f} kg/cm2 ({:.1f} N) | Brix = {:.2f} degBx".format(
        t0_data["Golden"]["AMPS"]["f_med_kg"], t0_data["Golden"]["AMPS"]["f_med_n"], t0_data["Golden"]["AMPS"]["b_med"]))
    print("  [OK] Golden Geral T0: Firmeza = {:.2f} kg/cm2 ({:.1f} N) | Brix = {:.2f} degBx".format(
        t0_data["Golden"]["Geral"]["f_med_kg"], t0_data["Golden"]["Geral"]["f_med_n"], t0_data["Golden"]["Geral"]["b_med"]))
    
    # 2. Carregar os 63 lotes do ficheiro de câmaras
    print("\n[2/4] A ler lotes com câmara de frio...")
    lotes = extrair_lotes_camaras()
    print(f"  [OK] Total de lotes identificados: {len(lotes)}")
    
    # 3. Associar T0 a cada lote e gerar ficheiros individuais
    print("\n[3/4] A gerar pastas, cenários e valores reais individuais em 'cenarios_reais/amostra_camaras_macas/'...")
    
    for idx, lote in enumerate(lotes, 1):
        lote["id_num"] = idx
        lote["id_str"] = f"Lote_{idx:02d}"
        
        var = lote["variedade"]
        prod = lote["produtor"]
        
        if prod in t0_data[var]:
            t0_ref = dict(t0_data[var][prod])
            t0_ref["fonte"] = f"{var} {prod}"
        else:
            t0_ref = dict(t0_data[var]["Geral"])
            t0_ref["fonte"] = f"{var} Geral"
            
        lote["t0_info"] = t0_ref
        
        # Nome da pasta do lote
        folder_name = (
            f"lote_{idx:02d}_{var.lower()}_{prod.lower()}_{lote['camara']}_"
            f"{lote['calibre_str']}_{lote['dias_frio']}d_r{lote['row_idx']}"
        )
        lote["folder_name"] = folder_name
        
        lot_dir = os.path.join(OUTPUT_DIR, folder_name)
        os.makedirs(lot_dir, exist_ok=True)
        
        # Ficheiros dentro da pasta
        cenario_filename = f"cenario_{folder_name}.xlsx"
        valores_reais_filename = f"valores_reais_{folder_name}.xlsx"
        
        cenario_path = os.path.join(lot_dir, cenario_filename)
        valores_reais_path = os.path.join(lot_dir, valores_reais_filename)
        
        # Gerar os dois Excels
        criar_excel_cenario(lote, cenario_path)
        criar_excel_valores_reais(lote, t0_ref, valores_reais_path)
        
        if idx % 10 == 0 or idx == len(lotes):
            print(f"  -> Processados {idx}/{len(lotes)} lotes...")
            
    # 4. Gerar ficheiro resumo geral
    print("\n[4/4] A criar ficheiro de índice geral 'resumo_todos_lotes_amostra_camaras.xlsx'...")
    resumo_path = os.path.join(OUTPUT_DIR, "resumo_todos_lotes_amostra_camaras.xlsx")
    criar_resumo_todos_lotes(lotes, resumo_path)
    print(f"  [OK] Índice geral guardado em: {resumo_path}")
    
    print("\n" + "=" * 70)
    print(f"CONCLUÍDO COM SUCESSO! {len(lotes)} lotes gerados na pasta:")
    print(f"  {OUTPUT_DIR}")
    print("=" * 70)

if __name__ == "__main__":
    main()
