"""
Script de automação para extrair, calcular e gerar os ficheiros Excel de:
1. Valores Reais em ficheiros Excel separados na pasta 'valores_reais':
   - 'medias_por_especie.xlsx'          (Apenas médias por espécie de maçã)
   - 'medias_por_produtor.xlsx'         (Médias por espécie e produtor)
   - 'valores_reais_gala_amps.xlsx'     (Medições individuais Maçãs 1 a 5 da Gala AMPS)
   - 'valores_reais_gala_cjl.xlsx'      (Medições individuais Maçãs 1 a 5 da Gala CJL)
   - 'valores_reais_golden_amps.xlsx'   (Medições individuais Maçãs 1 a 5 da Golden AMPS)
   - 'valores_reais_golden_cjl.xlsx'    (Medições individuais Maçãs 1 a 5 da Golden CJL)
2. Cenários climáticos preditivos atualizados na pasta 'amostra_normal_ess'

Fonte: 'cenarios_prof/Base de dados Maçã (Retaill) experiencias ESS_UTP.xlsx'
Folha: 'Amostra Coop (Frio <2ºC)'
"""

import os
import sys
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

import glob
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
FOLHA_ENTRADA = "Amostra Coop (Frio <2ºC)"
LINHA_CABECALHO = 2
LINHA_INICIO_DADOS = 3

# Posições de Colunas
COL_PRODUTOR = "A"          # Col 1: Produtor
COL_DATA = "B"              # Col 2: Data (se passar para 'D', basta mudar aqui!)
COL_VARIEDADE = "C"         # Col 3: Variedade
COL_AMOSTRA = "D"           # Col 4: Amostra

# Séries meteorológicas semanais (7 dias: Segunda a Domingo)
COL_HUMIDADE_INICIO = "E"   # Col 5: Humidade dia 1 (E a K = 7 colunas)
COL_TEMPERATURA_INICIO = "L"# Col 12: Temperatura dia 1 (L a R = 7 colunas)

# Firmeza (5 maçãs x 2 furos = 10 colunas: S a AB = 19 a 28)
COL_FIRMEZA_INICIO = "S"    # Col 19

# Brix (5 maçãs = 5 colunas: AC a AG = 29 a 33)
COL_BRIX_INICIO = "AC"      # Col 29

# Acidez (g ácido málico/100 g)
COL_ACIDEZ = "AH"           # Col 34

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
ROW_ALT_FILL = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")      # Zebrado suave
ROW_NORM_FILL = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
SUMMARY_FILL = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")      # Destaque Amarelo Claro
SUMMARY_FONT = Font(name=FONT_NAME, size=11, bold=True, color="92400E")

BORDER_THIN = Border(
    left=Side(style='thin', color='CBD5E1'),
    right=Side(style='thin', color='CBD5E1'),
    top=Side(style='thin', color='CBD5E1'),
    bottom=Side(style='thin', color='CBD5E1')
)

ALIGN_CENTER = Alignment(horizontal='center', vertical='center')
ALIGN_LEFT = Alignment(horizontal='left', vertical='center')
ALIGN_RIGHT = Alignment(horizontal='right', vertical='center')

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

def extrair_dados_amostra_normal_ess(caminho_excel):
    """
    Lê a folha 'Amostra Coop (Frio <2ºC)' do Excel e extrai:
    1. Medições reais por variedade, produtor, amostra e maçã (1 a 5).
    2. Sequências diárias de Temperatura e Humidade para construção de cenários.
    """
    if not os.path.exists(caminho_excel):
        raise FileNotFoundError(f"Ficheiro Excel não encontrado: {caminho_excel}")

    wb = openpyxl.load_workbook(caminho_excel, data_only=True)
    nome_folha = FOLHA_ENTRADA if FOLHA_ENTRADA in wb.sheetnames else next((s for s in wb.sheetnames if "amostra coop" in s.lower() or "amostra normal" in s.lower() or "amostra_normal" in s.lower()), None)
    if not nome_folha:
        raise ValueError(f"Folha '{FOLHA_ENTRADA}' não encontrada em {wb.sheetnames}")

    ws = wb[nome_folha]

    c_prod = col2idx(COL_PRODUTOR)
    c_dt = col2idx(COL_DATA)
    c_var = col2idx(COL_VARIEDADE)
    c_am = col2idx(COL_AMOSTRA)
    c_hum_start = col2idx(COL_HUMIDADE_INICIO)
    c_temp_start = col2idx(COL_TEMPERATURA_INICIO)
    c_firm_start = col2idx(COL_FIRMEZA_INICIO)
    c_brix_start = col2idx(COL_BRIX_INICIO)
    c_acidez = col2idx(COL_ACIDEZ)

    header_row = LINHA_CABECALHO

    # Descobrir datas de T0 para cada variedade
    t0_dates = {}
    for r in range(LINHA_INICIO_DADOS, ws.max_row + 1):
        var = ws.cell(r, c_var).value
        amostra = ws.cell(r, c_am).value
        dt = ws.cell(r, c_dt).value
        if var and amostra and str(amostra).strip().upper() == "T0" and dt:
            var_norm = str(var).strip()
            if isinstance(dt, datetime.datetime):
                dt_date = dt.date()
            elif isinstance(dt, datetime.date):
                dt_date = dt
            else:
                dt_date = datetime.datetime.strptime(str(dt)[:10], "%Y-%m-%d").date()
            if var_norm not in t0_dates:
                t0_dates[var_norm] = dt_date

    medicoes_individuais = []
    dados_cenarios = {}

    for r in range(LINHA_INICIO_DADOS, ws.max_row + 1):
        produtor = ws.cell(r, c_prod).value
        dt_val = ws.cell(r, c_dt).value
        var_val = ws.cell(r, c_var).value
        amostra_val = ws.cell(r, c_am).value

        if not (produtor and var_val and amostra_val and dt_val):
            continue

        produtor = str(produtor).strip()
        variedade = str(var_val).strip()
        amostra = str(amostra_val).strip()

        if isinstance(dt_val, datetime.datetime):
            data_real = dt_val.date()
        elif isinstance(dt_val, datetime.date):
            data_real = dt_val
        else:
            data_real = datetime.datetime.strptime(str(dt_val)[:10], "%Y-%m-%d").date()

        t0_d = t0_dates.get(variedade, data_real)
        dia = (data_real - t0_d).days

        # Verificar se existem medições de Firmeza
        tem_firmeza = any(ws.cell(r, c_firm_start + i).value is not None for i in range(10))
        acidez_val = ws.cell(r, c_acidez).value

        if tem_firmeza:
            for apple_idx in range(1, 6):
                f1_kg = ws.cell(r, c_firm_start + (apple_idx - 1) * 2).value
                f2_kg = ws.cell(r, c_firm_start + (apple_idx - 1) * 2 + 1).value
                brix = ws.cell(r, c_brix_start + (apple_idx - 1)).value

                if f1_kg is not None:
                    f1_kg = float(f1_kg)
                    f1_n = round(f1_kg * GRAVITY_CONSTANT, 1)
                else:
                    f1_kg, f1_n = None, None

                if f2_kg is not None:
                    f2_kg = float(f2_kg)
                    f2_n = round(f2_kg * GRAVITY_CONSTANT, 1)
                else:
                    f2_kg, f2_n = None, None

                if f1_kg is not None and f2_kg is not None:
                    fm_kg = round((f1_kg + f2_kg) / 2.0, 2)
                    fm_n = round((f1_n + f2_n) / 2.0, 1)
                elif f1_kg is not None:
                    fm_kg, fm_n = f1_kg, f1_n
                else:
                    fm_kg, fm_n = None, None

                brix_val = float(brix) if brix is not None else None
                ac_val = float(acidez_val) if acidez_val is not None else None

                medicoes_individuais.append({
                    "variedade": variedade,
                    "produtor": produtor,
                    "amostra": amostra,
                    "maca": apple_idx,
                    "dia": dia,
                    "data_real": data_real,
                    "f1_kg": f1_kg,
                    "f1_n": f1_n,
                    "f2_kg": f2_kg,
                    "f2_n": f2_n,
                    "fm_kg": fm_kg,
                    "fm_n": fm_n,
                    "brix": brix_val,
                    "acidez": ac_val
                })

        # Extração climática
        if variedade not in dados_cenarios:
            dados_cenarios[variedade] = {"dias_climaticos": {}, "amostras_processadas": set(), "t0_date": t0_d}

        if amostra not in dados_cenarios[variedade]["amostras_processadas"]:
            hums = [ws.cell(r, c_hum_start + i).value for i in range(7)]
            temps = [ws.cell(r, c_temp_start + i).value for i in range(7)]
            if any(t is not None for t in temps):
                dados_cenarios[variedade]["amostras_processadas"].add(amostra)
                # A semana meteorológica no Excel começa na Segunda-feira e termina no Domingo
                monday = data_real - datetime.timedelta(days=data_real.weekday())
                for idx in range(7):
                    t_val = temps[idx]
                    h_val = hums[idx]
                    if t_val is not None:
                        day_dt = monday + datetime.timedelta(days=idx)
                        if day_dt not in dados_cenarios[variedade]["dias_climaticos"]:
                            dados_cenarios[variedade]["dias_climaticos"][day_dt] = {
                                "date": day_dt,
                                "temp_c": float(t_val),
                                "hum_pct": float(h_val) if h_val is not None else 82.0
                            }

    return medicoes_individuais, dados_cenarios

def calcular_medias(medicoes):
    """Calcula médias por espécie e por espécie+produtor para cada tempo e médias globais."""
    from collections import defaultdict
    
    por_especie_tempo = defaultdict(list)
    por_especie_produtor_tempo = defaultdict(list)
    por_especie_global = defaultdict(list)
    por_especie_produtor_global = defaultdict(list)

    for m in medicoes:
        sp = m["variedade"]
        pr = m["produtor"]
        am = m["amostra"]
        por_especie_tempo[(sp, am, m["dia"], m["data_real"])].append(m)
        por_especie_produtor_tempo[(sp, pr, am, m["dia"], m["data_real"])].append(m)
        por_especie_global[sp].append(m)
        por_especie_produtor_global[(sp, pr)].append(m)

    def stats(lista):
        if not lista:
            return {}
        return {
            "n": len(lista),
            "f1_n": sum(x["f1_n"] for x in lista) / len(lista),
            "f1_kg": sum(x["f1_kg"] for x in lista) / len(lista),
            "f2_n": sum(x["f2_n"] for x in lista) / len(lista),
            "f2_kg": sum(x["f2_kg"] for x in lista) / len(lista),
            "fm_n": sum(x["fm_n"] for x in lista) / len(lista),
            "fm_kg": sum(x["fm_kg"] for x in lista) / len(lista),
            "brix": sum(x["brix"] for x in lista) / len(lista),
            "acidez": sum(x["acidez"] for x in lista) / len(lista),
        }

    res_especie_tempo = {}
    for k, v in por_especie_tempo.items():
        res_especie_tempo[k] = stats(v)

    res_especie_prod_tempo = {}
    for k, v in por_especie_produtor_tempo.items():
        res_especie_prod_tempo[k] = stats(v)

    res_especie_global = {k: stats(v) for k, v in por_especie_global.items()}
    res_especie_prod_global = {k: stats(v) for k, v in por_especie_produtor_global.items()}

    return {
        "especie_tempo": res_especie_tempo,
        "especie_prod_tempo": res_especie_prod_tempo,
        "especie_global": res_especie_global,
        "especie_prod_global": res_especie_prod_global
    }

# =====================================================================
# GERADORES DE EXCELS INDIVIDUAIS ESPECÍFICOS
# =====================================================================

HEADERS_TEMPO = [
    "Amostra", "Dia", "Data Real",
    "Firmeza 1 (N [kg/cm²])", "Firmeza 2 (N [kg/cm²])", "Firmeza Média (N [kg/cm²])",
    "Brix (°Bx)", "Acidez (%)"
]

HEADERS_NUMERICOS = [
    "Amostra", "Dia", "Data Real",
    "Firmeza 1 (N)", "Firmeza 1 (kg/cm²)",
    "Firmeza 2 (N)", "Firmeza 2 (kg/cm²)",
    "Firmeza Média (N)", "Firmeza Média (kg/cm²)",
    "Brix (°Bx)", "Acidez (%)"
]

def gerar_excel_apenas_medias_especie(medias_info, caminho_saida):
    """
    Gera ficheiro Excel dedicado: 'medias_por_especie.xlsx'
    Contém apenas as médias por espécie de maçã (Gala e Golden).
    """
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    variedades = sorted(list(set(k[0] for k in medias_info["especie_tempo"].keys())))

    # Folha de Visão Global
    ws_main = wb.create_sheet(title="Medias_Por_Especie")
    ws_main.views.sheetView[0].showGridLines = True
    curr_r = 1

    for sp in variedades:
        ws_main.cell(curr_r, 1, f"Maca {sp} — Medias Gerais por Amostra (AMPS + CJL, n=10)")
        ws_main.merge_cells(start_row=curr_r, start_column=1, end_row=curr_r, end_column=len(HEADERS_TEMPO))
        ws_main.cell(curr_r, 1).fill = TITLE_FILL
        ws_main.cell(curr_r, 1).font = TITLE_FONT
        ws_main.cell(curr_r, 1).alignment = ALIGN_LEFT
        ws_main.row_dimensions[curr_r].height = 25
        curr_r += 1

        for c_idx, h in enumerate(HEADERS_TEMPO, 1):
            cell = ws_main.cell(curr_r, c_idx, h)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.alignment = ALIGN_CENTER
        ws_main.row_dimensions[curr_r].height = 22
        start_table = curr_r
        curr_r += 1

        sub_items = [(k, v) for k, v in medias_info["especie_tempo"].items() if k[0] == sp]
        sub_items.sort(key=lambda x: x[0][2])

        for (v_sp, am, d, dt), s in sub_items:
            ws_main.append([
                am, d, dt.strftime("%Y-%m-%d") if isinstance(dt, datetime.date) else str(dt),
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
            r_c[5].font = Font(name=FONT_NAME, bold=True)
            curr_r += 1

        aplicar_borda_tabela(ws_main, start_table, curr_r - 1, 1, len(HEADERS_TEMPO))
        curr_r += 2

    ajustar_largura_colunas(ws_main)

    # Folhas individuais por variedade com números brutos
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
        sub_items.sort(key=lambda x: x[0][2])
        for r_i, ((v_sp, am, d, dt), s) in enumerate(sub_items, 2):
            ws_sp.append([
                am, d, dt.strftime("%Y-%m-%d") if isinstance(dt, datetime.date) else str(dt),
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
    """
    Gera ficheiro Excel dedicado: 'medias_por_produtor.xlsx'
    Contém apenas as médias por espécie e produtor (Gala AMPS, Gala CJL, Golden AMPS, Golden CJL).
    """
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    ws_main = wb.create_sheet(title="Medias_Por_Produtor")
    ws_main.views.sheetView[0].showGridLines = True
    curr_r = 1

    variedades = sorted(list(set(k[0] for k in medias_info["especie_prod_tempo"].keys())))
    produtores = sorted(list(set(k[1] for k in medias_info["especie_prod_tempo"].keys())))

    for sp in variedades:
        for pr in produtores:
            sub_items = [(k, v) for k, v in medias_info["especie_prod_tempo"].items() if k[0] == sp and k[1] == pr]
            if not sub_items:
                continue
            sub_items.sort(key=lambda x: x[0][3])

            ws_main.cell(curr_r, 1, f"Maçã {sp} | Produtor {pr} — Média das Maçãs (n=5)")
            ws_main.merge_cells(start_row=curr_r, start_column=1, end_row=curr_r, end_column=len(HEADERS_TEMPO))
            ws_main.cell(curr_r, 1).fill = TITLE_FILL
            ws_main.cell(curr_r, 1).font = TITLE_FONT
            ws_main.cell(curr_r, 1).alignment = ALIGN_LEFT
            ws_main.row_dimensions[curr_r].height = 25
            curr_r += 1

            for c_idx, h in enumerate(HEADERS_TEMPO, 1):
                cell = ws_main.cell(curr_r, c_idx, h)
                cell.fill = HEADER_FILL
                cell.font = HEADER_FONT
                cell.alignment = ALIGN_CENTER
            ws_main.row_dimensions[curr_r].height = 22
            start_table = curr_r
            curr_r += 1

            for (v_sp, v_pr, am, d, dt), s in sub_items:
                ws_main.append([
                    am, d, dt.strftime("%Y-%m-%d") if isinstance(dt, datetime.date) else str(dt),
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
                r_c[5].font = Font(name=FONT_NAME, bold=True)
                curr_r += 1

            aplicar_borda_tabela(ws_main, start_table, curr_r - 1, 1, len(HEADERS_TEMPO))
            curr_r += 2

    ajustar_largura_colunas(ws_main)

    # Folhas individuais por combinação Espécie x Produtor
    for sp in variedades:
        for pr in produtores:
            sub_items = [(k, v) for k, v in medias_info["especie_prod_tempo"].items() if k[0] == sp and k[1] == pr]
            if not sub_items:
                continue
            sub_items.sort(key=lambda x: x[0][3])

            ws_tab = wb.create_sheet(title=f"{sp[:6]}_{pr}")
            ws_tab.views.sheetView[0].showGridLines = True
            ws_tab.append(HEADERS_NUMERICOS)
            for c in range(1, len(HEADERS_NUMERICOS) + 1):
                ws_tab.cell(1, c).fill = HEADER_FILL
                ws_tab.cell(1, c).font = HEADER_FONT
                ws_tab.cell(1, c).alignment = ALIGN_CENTER
            ws_tab.row_dimensions[1].height = 24

            for r_i, ((v_sp, v_pr, am, d, dt), s) in enumerate(sub_items, 2):
                ws_tab.append([
                    am, d, dt.strftime("%Y-%m-%d") if isinstance(dt, datetime.date) else str(dt),
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
    """
    Gera ficheiro Excel dedicado para um Produtor e Variedade específicos:
    ex: 'valores_reais_gala_amps.xlsx'
    Contém:
    - Sheet 1: Visão Geral Maçãs 1 a 5 (Tabelas sequenciais)
    - Sheets 2 a 6: Cada Maçã (1 a 5) na sua folha dedicada
    """
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    sub_meds = [m for m in medicoes if m["variedade"].lower() == variedade.lower() and m["produtor"].lower() == produtor.lower()]
    if not sub_meds:
        return

    # 1. Folha Geral: Todas as 5 maçãs organizadas
    ws_all = wb.create_sheet(title="Macas_1_a_5")
    ws_all.views.sheetView[0].showGridLines = True
    curr_r = 1

    for apple_idx in range(1, 6):
        maca_rows = [m for m in sub_meds if m["maca"] == apple_idx]
        maca_rows.sort(key=lambda x: x["dia"])
        if not maca_rows:
            continue

        ws_all.cell(curr_r, 1, f"Cenário / Maçã {apple_idx} — {produtor} ({variedade})")
        ws_all.merge_cells(start_row=curr_r, start_column=1, end_row=curr_r, end_column=len(HEADERS_TEMPO))
        ws_all.cell(curr_r, 1).fill = TITLE_FILL
        ws_all.cell(curr_r, 1).font = TITLE_FONT
        ws_all.cell(curr_r, 1).alignment = ALIGN_LEFT
        ws_all.row_dimensions[curr_r].height = 24
        curr_r += 1

        for c_idx, h in enumerate(HEADERS_TEMPO, 1):
            cell = ws_all.cell(curr_r, c_idx, h)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.alignment = ALIGN_CENTER
        ws_all.row_dimensions[curr_r].height = 20
        start_table = curr_r
        curr_r += 1

        for m in maca_rows:
            f1_str = f"{m['f1_n']:.1f} N ({m['f1_kg']:.1f} kg/cm²)" if m['f1_n'] else "—"
            f2_str = f"{m['f2_n']:.1f} N ({m['f2_kg']:.1f} kg/cm²)" if m['f2_n'] else "—"
            fm_str = f"{m['fm_n']:.1f} N ({m['fm_kg']:.2f} kg/cm²)" if m['fm_n'] else "—"
            bx_str = f"{m['brix']:.1f} °Bx" if m['brix'] else "—"
            ac_str = f"{m['acidez']:.3f} %" if m['acidez'] else "—"

            ws_all.append([
                m["amostra"], m["dia"],
                m["data_real"].strftime("%Y-%m-%d") if isinstance(m["data_real"], datetime.date) else str(m["data_real"]),
                f1_str, f2_str, fm_str, bx_str, ac_str
            ])
            r_c = ws_all[curr_r]
            r_c[0].font = Font(name=FONT_NAME, bold=True)
            r_c[0].alignment = ALIGN_CENTER
            r_c[1].alignment = ALIGN_CENTER
            r_c[2].alignment = ALIGN_CENTER
            r_c[5].font = Font(name=FONT_NAME, bold=True)
            curr_r += 1

        aplicar_borda_tabela(ws_all, start_table, curr_r - 1, 1, len(HEADERS_TEMPO))
        curr_r += 2

    ajustar_largura_colunas(ws_all)

    # 2. Folhas individuais para cada Maçã (1 a 5)
    for apple_idx in range(1, 6):
        maca_rows = [m for m in sub_meds if m["maca"] == apple_idx]
        maca_rows.sort(key=lambda x: x["dia"])
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
                m["amostra"], m["dia"],
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

def atualizar_cenarios_amostra_normal_ess(dados_cenarios, medias_info, output_dir):
    """
    Gera/atualiza os ficheiros de cenários climáticos (.xlsx) na pasta 'amostra_normal_ess':
    - Sheet 'Cenario': Timeline diária com Temperature_C e Humidity_Percent
    - Sheet 'Valores Reais': Médias de Firmeza (N), Brix (°Bx) e Acidez (%) por data
    """
    os.makedirs(output_dir, exist_ok=True)

    for variedade, info in dados_cenarios.items():
        var_slug = "gala" if "gala" in variedade.lower() else "golden" if "golden" in variedade.lower() else variedade.lower()
        nome_ficheiro = f"cenario_maca_{var_slug}_amostra_normal_ess.xlsx"
        caminho_saida = os.path.join(output_dir, nome_ficheiro)

        dias_dict = info["dias_climaticos"]
        t0_date = info["t0_date"]

        if not dias_dict:
            continue

        dias_ordenados = sorted(dias_dict.values(), key=lambda x: x["date"])
        # Iniciar no dia seguinte à recepção T0
        dias_ordenados = [d for d in dias_ordenados if d["date"] > t0_date]

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

        for idx, dc in enumerate(dias_ordenados, 1):
            ws_cen.append([
                1,
                dc["date"].strftime("%Y-%m-%d"),
                idx,
                round(dc["temp_c"], 2),
                round(dc["hum_pct"], 2),
                "PT-LVT",
                "bulk"
            ])

        aplicar_borda_tabela(ws_cen, 1, len(dias_ordenados) + 1, 1, len(headers_cen))
        ajustar_largura_colunas(ws_cen)


        if salvar_workbook(wb, caminho_saida):
            print(f"[OK] Cenario climatico atualizado: {caminho_saida} ({len(dias_ordenados)} dias)")

def main():
    default_input = resolver_caminho_ficheiro(FICHEIRO_ENTRADA, script_dir, "*experiencias ESS_UTP*.xlsx")
    parser = argparse.ArgumentParser(description="Extrai e gera Excels separados para cada categoria de valores reais.")
    parser.add_argument("--input", default=default_input,
                        help="Caminho do ficheiro Excel de entrada.")
    parser.add_argument("--valores-dir", default=os.path.join(script_dir, "amostra_normal_ess", "valores_reais"),
                        help="Pasta de saída para os ficheiros Excel de valores reais.")
    parser.add_argument("--cenarios-dir", default=os.path.join(script_dir, "amostra_normal_ess"),
                        help="Pasta de saída para os cenários Excel.")
    args = parser.parse_args()

    print("=" * 75)
    print("GERAÇÃO DE EXCELS SEPARADOS: VALORES REAIS, MÉDIAS E PRODUTORES")
    print("=" * 75)
    print(f"Ficheiro de Entrada: {args.input}")
    print(f"Diretoria de Saída:  {args.valores_dir}")

    medicoes, dados_cenarios = extrair_dados_amostra_normal_ess(args.input)
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

    print("\n--- 3. Valores Reais por Produtor e Espécie (Maçãs Individuais) ---")
    for sp in variedades:
        for pr in produtores:
            slug_sp = sp.lower()
            slug_pr = pr.lower()
            nome_f = f"valores_reais_{slug_sp}_{slug_pr}.xlsx"
            caminho_f = os.path.join(args.valores_dir, nome_f)
            gerar_excel_produtor_individual(medicoes, medias_info, sp, pr, caminho_f)

    print("\n--- 4. Atualização dos Cenários Climáticos (amostra_normal_ess) ---")
    atualizar_cenarios_amostra_normal_ess(dados_cenarios, medias_info, args.cenarios_dir)

    print("\n" + "=" * 75)
    print("TODOS OS EXCELS FORAM GERADOS COM SUCESSO!")
    print("=" * 75)

if __name__ == "__main__":
    main()

