import math
import random
import datetime
import numpy as np
import hashlib
from fastapi.responses import JSONResponse
import threading
from typing import List, Literal, Optional, Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import uuid
from datetime import datetime, timedelta

# PRESETS
# =============================================================================
# 1) PRESETS POR FRUTA
# -----------------------------------------------------------------------------
# Each fruit has:
#
#   Termodinâmica / cinética:
#     - Tref_C      : temperature de referência dos parâmetros (°C)
#     - Ea_J        : activation energy p/ softening (J/mol)
#     - k_firm_ref  : taxa base de softening a Tref (1/dia aprox)
#
#   Humidade:
#     - RH_ref      : RH "ideal" (ou típica de armazenamento) para essa fruta (%)
#     - beta_RH     : sensibilidade à RH baixa (desidratação) no softening
#
#   Firmness:
#     - firmness_0_default : firmness típica no dia 0 (valor inicial sugerido, em N)
#     - firmness_min       : minimum limit (assíntota) de softening (em N)
#
#   Etileno e sensibilidade:
#     - alpha_E     : quanto o etileno total acelera o amolecimento (1/ppm)
#
#   Brix:
#     - brix_0_default : brix típico no dia 0
#     - brix_min/max   : limites mínimos/máximos teóricos no modelo
#     - brix_g         : taxa base logística (não é "dias até maturação")
#
#   Qualidade (índice 0–100):
#     - qual_firmness_threshold : "limiar" de firmness considerado aceitável (em N)
#     - qual_brix_target    : brix "alvo" (pico do score de brix)
#
#   Acidity:
#     - acidity_0_default : acidity típica no dia 0
#     - acidity_min       : acidity mínima teórica
#     - k_acidity_ref     : taxa base de degradação da acidity
#     - Ea_acidity_J      : activation energy
#     - qual_acidity_target: alvo de acidity para máxima qualidade
#
#   Tempo de Vida (Shelf Life):
#     - SL_ref           : tempo de vida máximo de referência em dias
#
#   Etileno endógeno (produção interna):
#     - E0_int      : etileno interno inicial (ppm)
#     - Eref_prod   : produção máxima (ppm/dia) em Tref e após rampa
#     - E_t0        : dia em que arranca a fase climatérica (sem E_ext)
#     - E_g         : inclinação da sigmóide da rampa climatérica
#     - E_auto      : autocatálise (mais E -> mais produção)
#     - E_decay     : remoção/degradação (1/dia)
#     - Ea_E_J      : energia de ativação para a produção de etileno
#     - E_ext_shift : quanto E_ext antecipa o gatilho climatérico
#
#   Bolor/podridão (RH alta):
#     - RH_mold_thr     : limiar (%) a partir do qual há risco significativo
#     - mold_rate_ref   : taxa base de crescimento do bolor em Tref (1/dia)
#     - mold_sens_RH    : sensibilidade ao excedente de RH acima do limiar
#     - mold_max_penalty: penalização máxima na qualidade (0..1)
#     - Ea_mold_J       : activation energy para crescimento de bolor
# =============================================================================

PRESETS = {
    # -------------------------------------------------------------------------
    # KIWI
    # -------------------------------------------------------------------------
    "kiwi_hayward": {
        "Tref_C": 0.0, "Ea_J": 40000, "k_firm_ref": 0.015, "beta_RH": 1.2, "RH_ref": 90,
        "firmness_min": 2.0, "firmness_0_default": 65,
        "brix_min": 6.0, "brix_max": 15.0, "brix_g": 0.35, "brix_0_default": 6.5,
        "qual_firmness_threshold": 8.0, "qual_brix_target": 14.0, "acidity_0_default": 1.2, "acidity_min": 0.5,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 1.0, "SL_ref": 120,
        # Etileno endógeno (climatérico moderado)
        "E0_int": 0.02, "Eref_prod": 0.15, "E_t0": 9, "E_g": 0.9, "E_auto": 0.4,
        "E_decay": 0.7, "Ea_E_J": 52000, "E_ext_shift": 2.0, "alpha_E": 2.0,
    },
    "kiwi_baby": {
        "Tref_C": 4.0, "Ea_J": 58000, "k_firm_ref": 0.18, "beta_RH": 2.0, "RH_ref": 95,
        "firmness_min": 1.5, "firmness_0_default": 40,
        "brix_min": 13.0, "brix_max": 18.0, "brix_g": 0.50, "brix_0_default": 8.0,
        "qual_firmness_threshold": 6.0, "qual_brix_target": 17.0, "acidity_0_default": 1.1, "acidity_min": 0.5,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 1.0, "SL_ref": 45,
        "E0_int": 0.02, "Eref_prod": 0.15, "E_t0": 9, "E_g": 0.9, "E_auto": 0.4,
        "E_decay": 0.7, "Ea_E_J": 52000, "E_ext_shift": 2.0, "alpha_E": 2.0,
    },
    "kiwi_gold": {
        "Tref_C": 0.5, "Ea_J": 42000, "k_firm_ref": 0.028, "beta_RH": 1.3, "RH_ref": 92,
        "firmness_min": 2.0, "firmness_0_default": 50,
        "brix_min": 8.0, "brix_max": 16.0, "brix_g": 0.30, "brix_0_default": 8.5,
        "qual_firmness_threshold": 6.0, "qual_brix_target": 15.0, "acidity_0_default": 1.0, "acidity_min": 0.4,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 0.9, "SL_ref": 90,
        "E0_int": 0.02, "Eref_prod": 0.15, "E_t0": 9, "E_g": 0.9, "E_auto": 0.4,
        "E_decay": 0.7, "Ea_E_J": 52000, "E_ext_shift": 2.0, "alpha_E": 2.0,
    },
    # -------------------------------------------------------------------------
    # APPLE
    # -------------------------------------------------------------------------
    "apple_fuji": {
        "Tref_C": 5.0, "Ea_J": 47000, "k_firm_ref": 0.018, "beta_RH": 0.7, "RH_ref": 95,
        "firmness_min": 15.0, "firmness_0_default": 85,
        "brix_min": 13.0, "brix_max": 17.0, "brix_g": 0.15, "brix_0_default": 13.0,
        "qual_firmness_threshold": 50.0, "qual_brix_target": 17.0, "acidity_0_default": 0.4, "acidity_min": 0.5,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 1.5, "SL_ref": 180,
        "E0_int": 0.01, "Eref_prod": 0.15, "E_t0": 12, "E_g": 0.8, "E_auto": 0.4,
        "E_decay": 0.8, "Ea_E_J": 52000, "E_ext_shift": 2.0, "alpha_E": 0.8,
    },
    "apple_golden": {
        "Tref_C": 1.5, "Ea_J": 44000, "k_firm_ref": 0.005, "beta_RH": 0.8, "RH_ref": 95,
        "firmness_min": 20.0, "firmness_0_default": 70,
        "brix_min": 10.0, "brix_max": 14.5, "brix_g": 0.18, "brix_0_default": 11.0,
        "qual_firmness_threshold": 50.0, "qual_brix_target": 13.5, "acidity_0_default": 0.5, "acidity_min": 0.5,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 1.0, "SL_ref": 150,
        "E0_int": 0.01, "Eref_prod": 0.15, "E_t0": 12, "E_g": 0.8, "E_auto": 0.4,
        "E_decay": 0.8, "Ea_E_J": 52000, "E_ext_shift": 2.0, "alpha_E": 0.8,
    },
    "apple_gala": {
        "Tref_C": 1.0, "Ea_J": 24000, "k_firm_ref": 0.002, "beta_RH": 0.9, "RH_ref": 95,
        "firmness_min": 16.0, "firmness_0_default": 70,
        "brix_min": 12.0, "brix_max": 15.0, "brix_g": 0.10, "brix_0_default": 12.0,
        "qual_firmness_threshold": 30.0, "qual_brix_target": 14.5, "acidity_0_default": 0.5, "acidity_min": 0.2,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 1.0, "SL_ref": 57,
        "E0_int": 0.01, "Eref_prod": 0.15, "E_t0": 12, "E_g": 0.8, "E_auto": 0.4,
        "E_decay": 0.8, "Ea_E_J": 52000, "E_ext_shift": 2.0, "alpha_E": 0.8,
    },
    "apple_reineta": {
        "Tref_C": 5.0, "Ea_J": 52000, "k_firm_ref": 0.035, "beta_RH": 1.0, "RH_ref": 90,
        "firmness_min": 18.0, "firmness_0_default": 65,
        "brix_min": 10.5, "brix_max": 13.5, "brix_g": 0.16, "brix_0_default": 10.5,
        "qual_firmness_threshold": 35.0, "qual_brix_target": 12.5, "acidity_0_default": 0.8, "acidity_min": 0.5,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 1.0, "SL_ref": 90,
        "E0_int": 0.01, "Eref_prod": 0.15, "E_t0": 12, "E_g": 0.8, "E_auto": 0.4,
        "E_decay": 0.8, "Ea_E_J": 52000, "E_ext_shift": 2.0, "alpha_E": 0.8,
    },
    "apple_granny_smith": {
        "Tref_C": 0.5, "Ea_J": 40000, "k_firm_ref": 0.006, "beta_RH": 0.6, "RH_ref": 95,
        "firmness_min": 25.0, "firmness_0_default": 90,
        "brix_min": 10.0, "brix_max": 13.0, "brix_g": 0.10, "brix_0_default": 11.5,
        "qual_firmness_threshold": 55.0, "qual_brix_target": 12.5, "acidity_0_default": 0.75, "acidity_min": 0.6,
        "k_acidity_ref": 0.015, "Ea_acidity_J": 50000, "qual_acidity_target": 1.8, "SL_ref": 210,
        "E0_int": 0.01, "Eref_prod": 0.15, "E_t0": 12, "E_g": 0.8, "E_auto": 0.4,
        "E_decay": 0.8, "Ea_E_J": 52000, "E_ext_shift": 2.0, "alpha_E": 0.8,
    },
    "apple_red_delicious": {
        "Tref_C": 0.5, "Ea_J": 44000, "k_firm_ref": 0.014, "beta_RH": 0.8, "RH_ref": 95,
        "firmness_min": 12.0, "firmness_0_default": 75,
        "brix_min": 11.0, "brix_max": 14.0, "brix_g": 0.14, "brix_0_default": 12.0,
        "qual_firmness_threshold": 40.0, "qual_brix_target": 13.0, "acidity_0_default": 0.3, "acidity_min": 0.15,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 0.35, "SL_ref": 150,
        "E0_int": 0.01, "Eref_prod": 0.15, "E_t0": 12, "E_g": 0.8, "E_auto": 0.4,
        "E_decay": 0.8, "Ea_E_J": 52000, "E_ext_shift": 2.0, "alpha_E": 0.8,
    },
    "apple_bravo_esmolfe": {
        "Tref_C": 3.0, "Ea_J": 50000, "k_firm_ref": 0.030, "beta_RH": 1.1, "RH_ref": 90,
        "firmness_min": 12.0, "firmness_0_default": 55,
        "brix_min": 12.0, "brix_max": 15.0, "brix_g": 0.15, "brix_0_default": 12.5,
        "qual_firmness_threshold": 25.0, "qual_brix_target": 14.0, "acidity_0_default": 0.6, "acidity_min": 0.4,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 52000, "qual_acidity_target": 1.0, "SL_ref": 75,
        "E0_int": 0.01, "Eref_prod": 0.15, "E_t0": 12, "E_g": 0.8, "E_auto": 0.4,
        "E_decay": 0.8, "Ea_E_J": 52000, "E_ext_shift": 2.0, "alpha_E": 0.8,
    },
    "apple_royal_gold": {
        "Tref_C": 1.5, "Ea_J": 45000, "k_firm_ref": 0.006, "beta_RH": 0.75, "RH_ref": 95,
        "firmness_min": 20.0, "firmness_0_default": 72,
        "brix_min": 11.0, "brix_max": 15.0, "brix_g": 0.17, "brix_0_default": 11.5,
        "qual_firmness_threshold": 48.0, "qual_brix_target": 14.0, "acidity_0_default": 0.45, "acidity_min": 0.3,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 0.9, "SL_ref": 150,
        "E0_int": 0.01, "Eref_prod": 0.15, "E_t0": 12, "E_g": 0.8, "E_auto": 0.4,
        "E_decay": 0.8, "Ea_E_J": 52000, "E_ext_shift": 2.0, "alpha_E": 0.8,
    },
    "apple_pink_lady": {
        "Tref_C": 0.5, "Ea_J": 38000, "k_firm_ref": 0.005, "beta_RH": 0.65, "RH_ref": 95,
        "firmness_min": 22.0, "firmness_0_default": 88,
        "brix_min": 13.0, "brix_max": 16.0, "brix_g": 0.12, "brix_0_default": 13.5,
        "qual_firmness_threshold": 55.0, "qual_brix_target": 15.0, "acidity_0_default": 0.55, "acidity_min": 0.4,
        "k_acidity_ref": 0.015, "Ea_acidity_J": 50000, "qual_acidity_target": 1.0, "SL_ref": 240,
        "E0_int": 0.01, "Eref_prod": 0.15, "E_t0": 12, "E_g": 0.8, "E_auto": 0.4,
        "E_decay": 0.8, "Ea_E_J": 52000, "E_ext_shift": 2.0, "alpha_E": 0.8,
    },
    "apple_jonagold": {
        "Tref_C": 1.0, "Ea_J": 46000, "k_firm_ref": 0.016, "beta_RH": 0.85, "RH_ref": 95,
        "firmness_min": 14.0, "firmness_0_default": 72,
        "brix_min": 12.0, "brix_max": 15.5, "brix_g": 0.16, "brix_0_default": 12.5,
        "qual_firmness_threshold": 38.0, "qual_brix_target": 14.5, "acidity_0_default": 0.5, "acidity_min": 0.35,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 0.9, "SL_ref": 130,
        "E0_int": 0.01, "Eref_prod": 0.15, "E_t0": 12, "E_g": 0.8, "E_auto": 0.4,
        "E_decay": 0.8, "Ea_E_J": 52000, "E_ext_shift": 2.0, "alpha_E": 0.8,
    },
    "apple_alcobaca": {
        "Tref_C": 2.0, "Ea_J": 48000, "k_firm_ref": 0.020, "beta_RH": 0.9, "RH_ref": 92,
        "firmness_min": 18.0, "firmness_0_default": 68,
        "brix_min": 11.0, "brix_max": 14.0, "brix_g": 0.15, "brix_0_default": 11.5,
        "qual_firmness_threshold": 38.0, "qual_brix_target": 13.0, "acidity_0_default": 0.55, "acidity_min": 0.4,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 53000, "qual_acidity_target": 1.0, "SL_ref": 120,
        "E0_int": 0.01, "Eref_prod": 0.15, "E_t0": 12, "E_g": 0.8, "E_auto": 0.4,
        "E_decay": 0.8, "Ea_E_J": 52000, "E_ext_shift": 2.0, "alpha_E": 0.8,
    },

    # -------------------------------------------------------------------------
    # BERRIES
    # -------------------------------------------------------------------------
    "strawberry": {
        "Tref_C": 2.0, "Ea_J": 52000, "k_firm_ref": 0.0012, "beta_RH": 2.4, "RH_ref": 90,
        "firmness_min": 1.0, "firmness_0_default": 5,
        "brix_min": 5.0, "brix_max": 9.0, "brix_g": 0.3, "brix_0_default": 7.5,
        "qual_firmness_threshold": 2.0, "qual_brix_target": 9.0, "acidity_0_default": 0.8, "acidity_min": 0.2,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 1.0, "SL_ref": 7,
        "E0_int": 0.002, "Eref_prod": 0.01, "E_t0": 999, "E_g": 0.2, "E_auto": 0.0,
        "E_decay": 0.8, "Ea_E_J": 50000, "E_ext_shift": 0.0, "alpha_E": 0.1,
    },
    "raspberry": {
        "Tref_C": 2.0, "Ea_J": 56000, "k_firm_ref": 0.060, "beta_RH": 2.2, "RH_ref": 95,
        "firmness_min": 1.5, "firmness_0_default": 6,
        "brix_min": 9.5, "brix_max": 10.0, "brix_g": 0.01, "brix_0_default": 9.5,
        "qual_firmness_threshold": 2.5, "qual_brix_target": 9.5, "acidity_0_default": 1.2, "acidity_min": 0.5,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 1.0, "SL_ref": 7,
        "E0_int": 0.002, "Eref_prod": 0.01, "E_t0": 999, "E_g": 0.2, "E_auto": 0.0,
        "E_decay": 0.8, "Ea_E_J": 50000, "E_ext_shift": 0.0, "alpha_E": 0.1,
    },
    "blueberry": {
        "Tref_C": 1.0, "Ea_J": 42000, "k_firm_ref": 0.030, "beta_RH": 1.6, "RH_ref": 90,
        "firmness_min": 3.0, "firmness_0_default": 10,
        "brix_min": 11.5, "brix_max": 14.0, "brix_g": 0.02, "brix_0_default": 11.5,
        "qual_firmness_threshold": 4.0, "qual_brix_target": 11.5, "acidity_0_default": 0.6, "acidity_min": 0.5,
        "k_acidity_ref": 0.009, "Ea_acidity_J": 30000, "qual_acidity_target": 1.0, "SL_ref": 21,
        "E0_int": 0.002, "Eref_prod": 0.01, "E_t0": 999, "E_g": 0.2, "E_auto": 0.0,
        "E_decay": 0.8, "Ea_E_J": 50000, "E_ext_shift": 0.0, "alpha_E": 0.1,
    },

    # -------------------------------------------------------------------------
    # POME / DRUPACEOUS (Cereja, Pêssego, Ameixa)
    # -------------------------------------------------------------------------
    "cherry": {
        "Tref_C": 2.0, "Ea_J": 48000, "k_firm_ref": 0.045, "beta_RH": 1.6, "RH_ref": 95,
        "firmness_min": 8.0, "firmness_0_default": 15,
        "brix_min": 16.0, "brix_max": 16.5, "brix_g": 0.01, "brix_0_default": 16.0,
        "qual_firmness_threshold": 10.0, "qual_brix_target": 16.0, "acidity_0_default": 0.5, "acidity_min": 0.5,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 1.0, "SL_ref": 21,
        "E0_int": 0.01, "Eref_prod": 0.18, "E_t0": 8, "E_g": 1.0, "E_auto": 0.5,
        "E_decay": 0.75, "Ea_E_J": 50000, "E_ext_shift": 2.0, "alpha_E": 1.0,
    },
    "peach": {
        "Tref_C": 2.0, "Ea_J": 56000, "k_firm_ref": 0.080, "beta_RH": 1.1, "RH_ref": 92,
        "firmness_min": 4.0, "firmness_0_default": 40,
        "brix_min": 10.0, "brix_max": 14.0, "brix_g": 0.20, "brix_0_default": 10.0,
        "qual_firmness_threshold": 8.0, "qual_brix_target": 13.0, "acidity_0_default": 0.6, "acidity_min": 0.5,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 1.0, "SL_ref": 14,
        "E0_int": 0.01, "Eref_prod": 0.18, "E_t0": 8, "E_g": 1.0, "E_auto": 0.5,
        "E_decay": 0.75, "Ea_E_J": 50000, "E_ext_shift": 2.0, "alpha_E": 1.0,
    },
    "plum": {
        "Tref_C": 2.0, "Ea_J": 52000, "k_firm_ref": 0.1, "beta_RH": 1.0, "RH_ref": 92,
        "firmness_min": 0.0, "firmness_0_default": 35,
        "brix_min": 10.0, "brix_max": 16.0, "brix_g": 0.25, "brix_0_default": 10.0,
        "qual_firmness_threshold": 10.0, "qual_brix_target": 15.0, "acidity_0_default": 0.8, "acidity_min": 0.5,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 1.175, "SL_ref": 21,
        "E0_int": 0.01, "Eref_prod": 0.18, "E_t0": 8, "E_g": 1.0, "E_auto": 0.5,
        "E_decay": 0.75, "Ea_E_J": 50000, "E_ext_shift": 2.0, "alpha_E": 1.0,
    },

    # -------------------------------------------------------------------------
    # CITRUS
    # -------------------------------------------------------------------------
    "orange": {
        "Tref_C": 5.0, "Ea_J": 42000, "k_firm_ref": 0.010, "beta_RH": 0.35, "RH_ref": 90,
        "firmness_min": 20.0, "firmness_0_default": 50,
        "brix_min": 11.0, "brix_max": 14, "brix_g": 0.01, "brix_0_default": 11.0,
        "qual_firmness_threshold": 35.0, "qual_brix_target": 13.0, "acidity_0_default": 1.0, "acidity_min": 0.5,
        "k_acidity_ref": 0.005, "Ea_acidity_J": 55000, "qual_acidity_target": 1.0, "SL_ref": 60,
    # Etileno externo antecipa o gatilho climatérico (mais E_ext -> t0 menor)
        "E0_int": 0.005, "Eref_prod": 0.02, "E_t0": 999, "E_g": 0.2, "E_auto": 0.0,
        "E_decay": 0.7, "Ea_E_J": 45000, "E_ext_shift": 0.0, "alpha_E": 0.15,
    },

    # -------------------------------------------------------------------------
    # OTHERS
    # -------------------------------------------------------------------------
    "banana": {
        "Tref_C": 5.0, "Ea_J": 42000, "k_firm_ref": 0.010, "beta_RH": 0.35, "RH_ref": 90,
        "firmness_min": 20.0, "firmness_0_default": 50,
        "brix_min": 11.0, "brix_max": 14, "brix_g": 0.01, "brix_0_default": 11.0,
        "qual_firmness_threshold": 35.0, "qual_brix_target": 12.0, "acidity_0_default": 1.0, "acidity_min": 0.5,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 1.0, "SL_ref": 90,
        "E0_int": 0.03, "Eref_prod": 0.3, "E_t0": 6, "E_g": 1.2, "E_auto": 0.6,
        "E_decay": 0.85, "Ea_E_J": 55000, "E_ext_shift": 2.5, "alpha_E": 1.2,
    },
    "pear": {
        "Tref_C": 2.0, "Ea_J": 54000, "k_firm_ref": 0.050, "beta_RH": 1.2, "RH_ref": 92,
        "firmness_min": 6.0, "firmness_0_default": 50,
        "brix_min": 11.0, "brix_max": 15.0, "brix_g": 0.25, "brix_0_default": 11.0,
        "qual_firmness_threshold": 12.0, "qual_brix_target": 14.0, "acidity_0_default": 0.3, "acidity_min": 0.5,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 1.0, "SL_ref": 90,
        "E0_int": 0.01, "Eref_prod": 0.18, "E_t0": 8, "E_g": 1.0, "E_auto": 0.5,
        "E_decay": 0.75, "Ea_E_J": 50000, "E_ext_shift": 2.0, "alpha_E": 1.0,
    },
    "grape": {
        "Tref_C": 1, "Ea_J": 45000, "k_firm_ref": 0.020, "beta_RH": 1.8, "RH_ref": 90.0,
        "firmness_min": 5.0, "firmness_0_default": 15,
        "brix_min": 16.0, "brix_max": 16.5, "brix_g": 0.01, "brix_0_default": 16.0,
        "qual_firmness_threshold": 8.0, "qual_brix_target": 16.0, "acidity_0_default": 0.6, "acidity_min": 0.5,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 1.0, "SL_ref": 25,
        "E0_int": 0.002, "Eref_prod": 0.01, "E_t0": 999, "E_g": 0.2, "E_auto": 0.0,
        "E_decay": 0.8, "Ea_E_J": 50000, "E_ext_shift": 0.0, "alpha_E": 0.1,
    },
    "fig": {
        "Tref_C": 2.0, "Ea_J": 52000, "k_firm_ref": 0.110, "beta_RH": 1.8, "RH_ref": 95,
        "firmness_min": 1.0, "firmness_0_default": 8,
        "brix_min": 16.0, "brix_max": 20.0, "brix_g": 0.15, "brix_0_default": 16.0,
        "qual_firmness_threshold": 2.0, "qual_brix_target": 19.0, "acidity_0_default": 0.3, "acidity_min": 0.5,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 1.0, "SL_ref": 7,
        "E0_int": 0.01, "Eref_prod": 0.18, "E_t0": 8, "E_g": 1.0, "E_auto": 0.5,
        "E_decay": 0.75, "Ea_E_J": 50000, "E_ext_shift": 2.0, "alpha_E": 1.0,
    },
    "melon": {
        "Tref_C": 7.0, "Ea_J": 52000, "k_firm_ref": 0.060, "beta_RH": 0.9, "RH_ref": 90,
        "firmness_min": 5.0, "firmness_0_default": 20,
        "brix_min": 10.0, "brix_max": 14.0, "brix_g": 0.22, "brix_0_default": 10.0,
        "qual_firmness_threshold": 8.0, "qual_brix_target": 13.5, "acidity_0_default": 0.2, "acidity_min": 0.5,
        "k_acidity_ref": 0.02, "Ea_acidity_J": 55000, "qual_acidity_target": 1.0, "SL_ref": 21,
    # Etileno externo antecipa o gatilho climatérico (mais E_ext -> t0 menor)
        "E0_int": 0.02, "Eref_prod": 0.2, "E_t0": 7, "E_g": 0.9, "E_auto": 0.45,
        "E_decay": 0.8, "Ea_E_J": 50000, "E_ext_shift": 1.8, "alpha_E": 1.0,
    },
}

MOLD_DEFAULTS = {
    "RH_mold_thr": 95.0,        # RH (%) a partir do qual começa risco significativo
    "mold_rate_ref": 0.06,      # taxa base (1/dia) em Tref
    "mold_sens_RH": 10.0,       # sensibilidade ao excedente de RH acima do limiar
    "mold_max_penalty": 0.80,   # máximo de penalização (0..1)
    "Ea_mold_J": 45000.0,       # sensibilidade à temperature (Arrhenius)
}

MOLD_BY_FRUIT = {
    # Very sensitive
    "strawberry":   {"RH_mold_thr": 93.0, "mold_rate_ref": 0.22, "mold_sens_RH": 16.0, "mold_max_penalty": 0.95, "Ea_mold_J": 52000.0},
    "raspberry": {"RH_mold_thr": 93.0, "mold_rate_ref": 0.20, "mold_sens_RH": 16.0, "mold_max_penalty": 0.95, "Ea_mold_J": 52000.0},
    "fig":      {"RH_mold_thr": 93.0, "mold_rate_ref": 0.18, "mold_sens_RH": 14.0, "mold_max_penalty": 0.92, "Ea_mold_J": 50000.0},

    # Sensitive
    "blueberry":   {"RH_mold_thr": 94.0, "mold_rate_ref": 0.12, "mold_sens_RH": 14.0, "mold_max_penalty": 0.90, "Ea_mold_J": 48000.0},
    "cherry":    {"RH_mold_thr": 94.0, "mold_rate_ref": 0.10, "mold_sens_RH": 13.0, "mold_max_penalty": 0.85, "Ea_mold_J": 47000.0},
    "peach":   {"RH_mold_thr": 94.0, "mold_rate_ref": 0.10, "mold_sens_RH": 12.0, "mold_max_penalty": 0.85, "Ea_mold_J": 48000.0},
    "plum":    {"RH_mold_thr": 94.0, "mold_rate_ref": 0.09, "mold_sens_RH": 12.0, "mold_max_penalty": 0.82, "Ea_mold_J": 47000.0},

    # Medium
    "pear":      {"RH_mold_thr": 95.0, "mold_rate_ref": 0.07, "mold_sens_RH": 10.0, "mold_max_penalty": 0.75, "Ea_mold_J": 45000.0},
    "melon":     {"RH_mold_thr": 95.0, "mold_rate_ref": 0.08, "mold_sens_RH": 10.0, "mold_max_penalty": 0.78, "Ea_mold_J": 45000.0},
    "grape":       {"RH_mold_thr": 95.0, "mold_rate_ref": 0.10, "mold_sens_RH": 14.0, "mold_max_penalty": 0.90, "Ea_mold_J": 46000.0},

    # Low to medium (kiwis/maçãs)
    "kiwi_hayward": {"RH_mold_thr": 95.0, "mold_rate_ref": 0.05,  "mold_sens_RH": 9.0,  "mold_max_penalty": 0.65, "Ea_mold_J": 43000.0},
    "kiwi_baby":    {"RH_mold_thr": 95.0, "mold_rate_ref": 0.07,  "mold_sens_RH": 10.0, "mold_max_penalty": 0.75, "Ea_mold_J": 45000.0},
    "kiwi_gold":    {"RH_mold_thr": 95.0, "mold_rate_ref": 0.08,  "mold_sens_RH": 11.0, "mold_max_penalty": 0.78, "Ea_mold_J": 45000.0},
    "apple_golden":  {"RH_mold_thr": 95.0, "mold_rate_ref": 0.04,  "mold_sens_RH": 8.0,  "mold_max_penalty": 0.60, "Ea_mold_J": 42000.0},
    "apple_reineta": {"RH_mold_thr": 95.0, "mold_rate_ref": 0.05,  "mold_sens_RH": 9.0,  "mold_max_penalty": 0.65, "Ea_mold_J": 43000.0},
    "apple_gala":    {"RH_mold_thr": 95.0, "mold_rate_ref": 0.05,  "mold_sens_RH": 9.0,  "mold_max_penalty": 0.65, "Ea_mold_J": 43000.0},
    "apple_fuji":    {"RH_mold_thr": 95.0, "mold_rate_ref": 0.035, "mold_sens_RH": 8.0,  "mold_max_penalty": 0.55, "Ea_mold_J": 42000.0},
    "apple_granny_smith":  {"RH_mold_thr": 95.0, "mold_rate_ref": 0.03,  "mold_sens_RH": 7.5,  "mold_max_penalty": 0.50, "Ea_mold_J": 41000.0},
    "apple_red_delicious": {"RH_mold_thr": 95.0, "mold_rate_ref": 0.05,  "mold_sens_RH": 9.0,  "mold_max_penalty": 0.65, "Ea_mold_J": 43000.0},
    "apple_bravo_esmolfe": {"RH_mold_thr": 94.0, "mold_rate_ref": 0.09,  "mold_sens_RH": 12.0, "mold_max_penalty": 0.78, "Ea_mold_J": 46000.0},
    "apple_royal_gold":    {"RH_mold_thr": 95.0, "mold_rate_ref": 0.04,  "mold_sens_RH": 8.0,  "mold_max_penalty": 0.60, "Ea_mold_J": 42000.0},
    "apple_pink_lady":     {"RH_mold_thr": 95.0, "mold_rate_ref": 0.03,  "mold_sens_RH": 7.5,  "mold_max_penalty": 0.50, "Ea_mold_J": 41000.0},
    "apple_jonagold":      {"RH_mold_thr": 95.0, "mold_rate_ref": 0.05,  "mold_sens_RH": 9.0,  "mold_max_penalty": 0.65, "Ea_mold_J": 43000.0},
    "apple_alcobaca":      {"RH_mold_thr": 95.0, "mold_rate_ref": 0.05,  "mold_sens_RH": 9.0,  "mold_max_penalty": 0.65, "Ea_mold_J": 43000.0},

    # Low (citrinos)
    "orange": {"RH_mold_thr": 96.0, "mold_rate_ref": 0.03, "mold_sens_RH": 8.0, "mold_max_penalty": 0.50, "Ea_mold_J": 42000.0},
    # Etileno externo antecipa o gatilho climatérico (mais E_ext -> t0 menor)
}

PACKAGING_FACTORS = {
   "Granel (Sem embalagem)": 1.0,
   "Caixa de Cartão Aberta": 0.85,
   "Saco Plástico Perfurado": 0.45,
   "MAP (Atmosfera Modificada) / Plástico Selado": 0.10
}

# Aplica defaults e depois overrides por fruta
for k in PRESETS:
    for kk, vv in MOLD_DEFAULTS.items():
        PRESETS[k].setdefault(kk, vv)
    if k in MOLD_BY_FRUIT:
        PRESETS[k].update(MOLD_BY_FRUIT[k])

# Temperature / RH Warehouse Deduction
# =============================================================================

def get_region_weather(region_code, target_date):
    """
    Simulates climate data based on region profile and seasonality.

    Args:
        region_code (str): The region identifier.
        target_date (datetime): The target date to simulate the weather for.

    Returns:
        tuple: A tuple containing (temperature, humidity).
    """
    # Perfis: (Temp_Média, Temp_Amplitude, Humidade_Média, Humidade_Amplitude)
    profiles = {
        'PT-NL': (14.5, 5.0, 83.0, 5.0),   # Norte Litoral: húmido, moderado
        'PT-NI': (13.5, 10.0, 72.0, 12.0), # Norte Interior: grande amplitude, frio/quente
        'PT-CL': (15.5, 6.0, 78.0, 6.0),   # Centro Litoral: temperate marítimo
        'PT-CI': (14.0, 9.0, 70.0, 10.0),  # Centro Interior: continental
        'PT-LVT': (17.0, 7.0, 72.0, 8.0),  # Lisboa e Vale do Tejo: mediterrânico moderado
        'PT-AL': (17.5, 11.0, 64.0, 15.0), # Alentejo: seco, verão quente, invernos frios
        'PT-ALG': (18.5, 6.5, 67.0, 8.0),  # Algarve: mediterrânico ameno, seco
        'PT-SM': (8.5, 9.5, 78.0, 12.0),   # Serra da Estrela: montanha, frio rigoroso
        'PT-MAD': (19.5, 3.5, 74.0, 4.0),  # Madeira: subtropical estável
        'PT-ACO': (17.5, 3.0, 85.0, 4.0),  # Açores: oceânico muito húmido, estável
    }
    
    # Fallback se a região não for encontrada
    base_temp, temp_amp, base_hum, hum_amp = profiles.get(region_code, (16.0, 7.0, 75.0, 8.0))
    
    # Sazonalidade via curva senoidal
    day_of_year = target_date.timetuple().tm_yday
    # Pico no dia 200 (Julho)
    seasonal_factor = math.sin(2 * math.pi * (day_of_year - 110) / 365)
    
    # Cálculo das condições simulando o ambiente exterior da região
    temp = round(base_temp + temp_amp * seasonal_factor + random.uniform(-1.2, 1.2), 1)
    
    # Humidade inverte a temperature (mais quente = mais seco)
    hum = round(base_hum - hum_amp * seasonal_factor + random.uniform(-2.5, 2.5), 1)
    
    return temp, hum

def calc_absolute_humidity(T_cels, RH_pct):
    """
    Calculates the Absolute Humidity (HA) given Temperature and Relative Humidity.

    Args:
        T_cels (float): Temperature in degrees Celsius.
        RH_pct (float): Relative humidity percentage (0-100).

    Returns:
        float: The absolute humidity.
    """
    numerator = 2.16679 * RH_pct * 6.112 * math.exp((17.67 * T_cels) / (T_cels + 243.5))
    denominator = T_cels + 273.15
    return numerator / denominator

def calc_relative_humidity(T_cels, HA):
    """
    Calculates the Relative Humidity (%) given Temperature and Absolute Humidity.

    Args:
        T_cels (float): Temperature in degrees Celsius.
        HA (float): Absolute humidity.

    Returns:
        float: Relative humidity percentage, capped at 100.0%.
    """
    numerator = HA * (T_cels + 273.15)
    denominator = 2.16679 * 6.112 * math.exp((17.67 * T_cels) / (T_cels + 243.5))
    HR = numerator / denominator
    return min(HR, 100.0)

def simulate_warehouse_climate(T_ext_series, HR_ext_series, alphas=None, T_int_initial=None):
    if not T_ext_series or len(T_ext_series) != len(HR_ext_series):
        return [], []
    
    if alphas is None:
        alphas = [0.9] * len(T_ext_series)
    elif not isinstance(alphas, list):
        alphas = [alphas] * len(T_ext_series)
        
    T_int_series = []
    HR_int_series = []
    
    if T_int_initial is None:
        T_int_prev = T_ext_series[0]
    else:
        T_int_prev = T_int_initial
        
    for i in range(len(T_ext_series)):
        T_ext = T_ext_series[i]
        HR_ext = HR_ext_series[i]
        alpha = alphas[i]
        
        T_int = alpha * T_int_prev + (1 - alpha) * T_ext
        T_int_series.append(round(T_int, 2))
        
        HA_ext = calc_absolute_humidity(T_ext, HR_ext)
        HR_int = calc_relative_humidity(T_int, HA_ext)
        HR_int_series.append(round(HR_int, 2))
        
        T_int_prev = T_int
        
    return T_int_series, HR_int_series

# Temperature / RH Safety Rules
# =============================================================================
def fill_nulls_with_constant(data_array, replacement_value):
    """
    Replaces Null/None values in an array with a specified constant number.
    
    Args:
        data_array (list): The array containing potential None values.
        replacement_value (float): The value to substitute for None.
        
    Returns:
        list: The array with None values replaced.
    """
    return [replacement_value if x is None else x for x in data_array]


def fill_nulls_with_warehouse_sim(temp_array, rh_array, region_codes, alphas, start_date):
    # Generate external climate data
    T_ext_series = []
    HR_ext_series = []
    
    for i in range(len(temp_array)):
        current_date = start_date + datetime.timedelta(days=i)
        temp, hum = get_region_weather(region_codes[i], current_date)
        T_ext_series.append(temp)
        HR_ext_series.append(hum)
        
    # Simulate internal warehouse climate
    T_int_series, HR_int_series = simulate_warehouse_climate(T_ext_series, HR_ext_series, alphas=alphas)
    
    # Replace nulls
    res_temp = []
    res_rh = []
    
    for i in range(len(temp_array)):
        t_val = temp_array[i]
        rh_val = rh_array[i]
        
        if t_val is None:
            res_temp.append(T_int_series[i])
        else:
            res_temp.append(t_val)
            
        if rh_val is None:
            res_rh.append(HR_int_series[i])
        else:
            res_rh.append(rh_val)
            
    return res_temp, res_rh

#SIM WITH ETHYLENE (Firmness, Brix, Shelf Life & Mold) Luís Paulo
# =============================================================================
def run_simulation_prof_luis_paulo(fruit_key, T_c, E_ext_ppm, RH_pct, days, firmness_0_user, brix_0_user, custom_preset=None):
    """
    Runs the post-harvest simulation incorporating Ethylene effects.

    Args:
        fruit_key (str): The fruit identifier from presets.
        T_c (list[float]): Array of temperatures in Celsius.
        E_ext_ppm (list[float] | float): External Ethylene concentration in ppm.
        RH_pct (list[float]): Array of relative humidities in percentage.
        days (int): The number of days to simulate.
        firmness_0_user (float): Initial firmness.
        brix_0_user (float): Initial Brix value.
        custom_preset (dict, optional): Custom preset properties to override defaults. Defaults to None.

    Returns:
        tuple[float, float]: The quality index and the remaining shelf life on the final simulation day.
    """

    dt = 0.05  # passo temporal (dias). 0.05 ~ 1.2 horas.
    R = 8.314  # constante dos gases (J/mol/K)

    def k_temp_scaling(Ea, T, Tref):
        """
        Arrhenius-type scaling relative to a reference temperature.

        Args:
            Ea (float): Activation energy.
            T (float): Current temperature in Kelvin.
            Tref (float): Reference temperature in Kelvin.

        Returns:
            float: Multiplicative scaling factor.
        """
        return np.exp((-Ea / R) * (1/T - 1/Tref))

    def sigmoid(x):
        """
        Classic sigmoid function.

        Args:
            x (float): Input value.

        Returns:
            float: Sigmoid of x.
        """
        return 1.0 / (1.0 + np.exp(-x))

    if custom_preset is not None:
        p = custom_preset
        for kk, vv in MOLD_DEFAULTS.items():
            p.setdefault(kk, vv)
    else:
        p = PRESETS[fruit_key]
    max_sim_days = max(days + 200, 365)
    t = np.arange(0, max_sim_days, dt)
    
    extra_days = max_sim_days - days
    if extra_days > 0:
        T_c = list(T_c) + [p["Tref_C"]] * extra_days
        RH_pct = list(RH_pct) + [p["RH_ref"]] * extra_days
        
    T_c = np.array(T_c)
    T_c = np.repeat(T_c, int(1/dt))
    RH_pct = np.array(RH_pct)
    RH_pct = np.repeat(RH_pct, int(1/dt))

    if np.isscalar(E_ext_ppm):
        E_ext_ppm = np.full(len(t), float(E_ext_ppm))
    else:
        if extra_days > 0:
            E_ext_ppm = list(E_ext_ppm) + [0.0] * extra_days
        E_ext_ppm = np.array(E_ext_ppm)
        E_ext_ppm = np.repeat(E_ext_ppm, int(1/dt))

    # -------------------------------------------------------------------------
    # 4.1) Efeito da temperature no softening (kT_firm)
    # -------------------------------------------------------------------------
    T_K = T_c + 273.15
    Tref_K = p["Tref_C"] + 273.15

    # k_firm_ref é a taxa de softening em Tref
    # Ea_J controla quão depressa k cresce com a temperature
    kT_firm = p["k_firm_ref"] * k_temp_scaling(p["Ea_J"], T_K, Tref_K)

    # -------------------------------------------------------------------------
    # 4.2) Efeito da RH baixa no softening (desidratação)
    # -------------------------------------------------------------------------
    RH_ref = p["RH_ref"]  # RH "ideal/típica" para minimizar desidratação

    # -------------------------------------------------------------------------
    # 4.3) ETILENO ENDÓGENO (E_int) e etileno total
    # -------------------------------------------------------------------------
    # Modelo:
    #   dE/dt = prod(t)*(1 + E_auto*E) - E_decay*E
    # prod(t) tem rampa sigmóide (climatérica) e aumenta com T.
    E_int = np.zeros_like(t)
    E_int[0] = float(p.get("E0_int", 0.01))

    Ea_E_J = float(p.get("Ea_E_J", 52000))
    Eref_prod = float(p.get("Eref_prod", 0.08))     # produção máxima (ppm/dia)
    E_decay = float(p.get("E_decay", 0.7))          # remoção (1/dia)
    E_t0 = float(p.get("E_t0", 15.0))               # gatilho sem E_ext (dias)
    E_g = float(p.get("E_g", 0.8))                  # inclinação do gatilho
    E_auto = float(p.get("E_auto", 0.35))           # autocatálise
    E_ext_shift = float(p.get("E_ext_shift", 2.0))  # E_ext antecipa o gatilho

    # Etileno externo antecipa o gatilho climatérico (mais E_ext -> t0 menor)
    t0_eff = E_t0 - E_ext_shift * np.log1p(np.maximum(0.0, E_ext_ppm))

    # Produção de etileno aumenta com T (usamos Ea_E_J)
    prod_T = k_temp_scaling(Ea_E_J, T_K, Tref_K)

    for i in range(1, len(t)):
        ramp = sigmoid(E_g * (t[i-1] - (t0_eff[i-1] if not np.isscalar(t0_eff) else t0_eff)))      # 0..1
        prod = Eref_prod * prod_T[i-1] * ramp             # ppm/dia
        dE = (prod * (1.0 + E_auto * E_int[i-1]) - E_decay * E_int[i-1]) * dt
        E_int[i] = max(0.0, E_int[i-1] + dE)

    # Etileno total que influencia amadurecimento
    E_total = E_ext_ppm + E_int

    # -------------------------------------------------------------------------
    # 4.4) DUREZA (softening) via ODE
    # -------------------------------------------------------------------------
    # dD/dt = -k(t) * (D - D_min), com k(t) = kT_firm * kRH * (1 + alpha_E * E_total)
    firmness = np.zeros_like(t)
    firmness_min = float(p["firmness_min"])
    firmness[0] = max(firmness_min + 1e-6, float(firmness_0_user))

    alpha_E = float(p.get("alpha_E", 0.1))
    for i in range(1, len(t)):
        kE = (1.0 + alpha_E * E_total[i-1])
        # 4.2) Efeito da RH baixa no softening (desidratação)
        RH_deficit = max(0.0, (RH_ref - RH_pct[i-1]) / 100.0)
        kRH = (1 + p["beta_RH"] * RH_deficit)  # RH baixa => kRH > 1 => amolece mais rápido
        k = kT_firm[i-1] * kRH * kE
        dD = (-k * (firmness[i-1] - firmness_min)) * dt
        firmness[i] = max(firmness_min, firmness[i-1] + dD)

    # -------------------------------------------------------------------------
    # 4.5) BRIX (sweetness) via ODE logística
    # -------------------------------------------------------------------------
    # db/dt = r(t) * x * (1 - x/K), com x = b - b_min, K = b_max - b_min
    brix = np.zeros_like(t)
    brix_min = float(p["brix_min"])
    brix_max = float(p["brix_max"])
    brix[0] = float(brix_0_user)

    r0 = float(p.get("brix_g", 0.1))      # taxa base
    alpha_bE = 0.25              # etileno acelera conversões (heurístico)

    # Efeito da temperature na taxa de brix (usando Ea_E_J como aproximação)
    rT = k_temp_scaling(Ea_E_J, T_K, Tref_K)

    for i in range(1, len(t)):
        # RH baixa pode reduzir a “eficiência” (stress/desidratação)
        bRH = max(0.0, (RH_ref - RH_pct[i-1]) / 100.0)
        rRH = (1.0 - 0.6 * bRH)
        r = r0 * rT[i-1] * rRH * (1.0 + alpha_bE * E_total[i-1])
        x = max(0.0, brix[i-1] - brix_min)
        K = max(1e-6, (brix_max - brix_min))
        db = (r * x * (1.0 - x / K)) * dt
        brix[i] = min(brix_max, max(brix_min, brix[i-1] + db))

    # -------------------------------------------------------------------------
    # 4.6) QUALIDADE base (0–100)
    # -------------------------------------------------------------------------
    firm_score = 1 / (1 + np.exp(-0.35 * (firmness - float(p["qual_firmness_threshold"]))))
    brix_score = np.exp(-((brix - float(p["qual_brix_target"]))**2) / 2)
    quality_base = 100 * (0.65 * firm_score + 0.35 * brix_score)

    # -------------------------------------------------------------------------
    # 4.7) BOLOR / PODRIDÃO (RH alta)
    # -------------------------------------------------------------------------
    # mold(t) cresce quando RH > RH_mold_thr:
    #   dm/dt = rate * (1 - m)
    # rate aumenta com temperature e com excedente de RH.
    RH_mold_thr = float(p["RH_mold_thr"])
    mold_rate_ref = float(p["mold_rate_ref"])
    mold_sens_RH = float(p["mold_sens_RH"])
    mold_max_penalty = float(p["mold_max_penalty"])
    Ea_mold_J = float(p["Ea_mold_J"])

    mold_T = k_temp_scaling(Ea_mold_J, T_K, Tref_K)


    mold = np.zeros_like(t)
    mold[0] = 0.0
    for i in range(1, len(t)):
        RH_excess = max(0.0, (RH_pct[i-1] - RH_mold_thr) / 100.0)
        RH_factor = 1.0 - np.exp(-mold_sens_RH * RH_excess)  # 0..~1
        rate = mold_rate_ref * mold_T[i-1] * RH_factor
        dm = (rate * (1.0 - mold[i-1])) * dt
        mold[i] = min(1.0, max(0.0, mold[i-1] + dm))

    mold_penalty = mold_max_penalty * mold
    quality = quality_base * (1.0 - mold_penalty)

    # Find quality at requested 'days'
    idx_days = int(days / dt) - 1
    if idx_days < 0: idx_days = 0
    if idx_days >= len(quality): idx_days = len(quality) - 1
    
    final_quality = quality[idx_days]
    
    # Calculate remaining shelf life based on 30% quality threshold
    below_30 = np.where(quality <= 30.0)[0]
    if len(below_30) > 0:
        idx_30 = below_30[0]
        if idx_30 <= idx_days:
            remaining_SL = 0.0
        else:
            remaining_SL = t[idx_30] - days
    else:
        remaining_SL = float(max_sim_days - days)
        
    arrays_dict = {"quality": quality.tolist(), "firmness": firmness.tolist(), "brix": brix.tolist()}
    return final_quality, remaining_SL, firmness[idx_days], brix[idx_days], arrays_dict

# SIM (Firmness, Brix, Acidity, VPD, Shelf Life & Mold) Sofia Machado
# =============================================================================
def run_simulation_sofia_machado(fruit_key: str, T_c: list[float], RH_pct: list[float], days: int,
                   firmness_0_user: float, brix_0_user: float, acidity_0_user: float, 
                   packaging_methods: Optional[list[str]] = None,
                   dt: int = 0.05, custom_preset: dict = None
                   ) -> tuple[float, float]:
    """
    Runs the post-harvest simulation to predict fruit quality and remaining shelf life.

    Args:
        fruit_key (str): The fruit identifier from presets.
        T_c (list[float]): Array of temperatures in Celsius.
        RH_pct (list[float]): Array of relative humidities in percentage.
        days (int): The number of days to simulate.
        firmness_0_user (float): Initial firmness.
        brix_0_user (float): Initial Brix value.
        acidity_0_user (float): Initial acidity.
        packaging_methods (list[str] | None, optional): Array of packaging methods. Defaults to None.
        dt (int | None, optional): Time interval for simulation. Defaults to 0.05.
        custom_preset (dict, optional): Custom preset properties to override defaults. Defaults to None.

    Returns:
        tuple[float, float]: The quality index and the remaining shelf life on the final simulation day.
    """
    R = 8.314

    def k_temp_scaling(Ea, T, Tref):
        return np.exp((-Ea / R) * (1/T - 1/Tref))

    def calc_vpd(T_cels, RH_p):
        es = 0.6108 * np.exp(17.27 * T_cels / (T_cels + 237.3))
        ea = es * (RH_p / 100.0)
        return es - ea

    if custom_preset is not None:
        p = custom_preset
        for kk, vv in MOLD_DEFAULTS.items():
            p.setdefault(kk, vv)
    else:
        p = PRESETS[fruit_key]
        
    if packaging_methods is None:
        packaging_methods = ["Granel (Sem embalagem)"] * days
    else:
        packaging_methods = [pm if pm is not None else "Granel (Sem embalagem)" for pm in packaging_methods]
        
    t = np.arange(0, days, dt)
    T_c = np.repeat(np.array(T_c), int(1/dt))
    RH_pct = np.repeat(np.array(RH_pct), int(1/dt))
    packaging_methods_rep = np.repeat(np.array(packaging_methods), int(1/dt))

    T_K = T_c + 273.15
    Tref_K = p["Tref_C"] + 273.15

    # Thermal Time
    TT = np.zeros_like(t)
    T_base = 0
    for i in range(1, len(t)):
        TT[i] = TT[i-1] + max(0, T_c[i-1] - T_base) * dt

    # VPD
    VPD = calc_vpd(T_c, RH_pct)
    VPD_ref = calc_vpd(p["Tref_C"], p["RH_ref"])

    # Firmness
    kT_firm = p["k_firm_ref"] * k_temp_scaling(p["Ea_J"], T_K, Tref_K)
    firmness = np.zeros_like(t)
    firmness_min = float(p["firmness_min"])
    firmness[0] = max(firmness_min + 1e-6, float(firmness_0_user))

    # Brix
    brix = np.zeros_like(t)
    brix_min = float(p["brix_min"])
    brix_max = float(p["brix_max"])
    brix[0] = float(brix_0_user)
    r0 = float(p["brix_g"])
    rT = k_temp_scaling(52000, T_K, Tref_K)

    # Acidity
    acidity = np.zeros_like(t)
    acidity_min = float(p["acidity_min"])
    acidity[0] = max(acidity_min + 1e-6, float(acidity_0_user))
    kT_acidity = p["k_acidity_ref"] * k_temp_scaling(p["Ea_acidity_J"], T_K, Tref_K)
    # Remaining Shelf Life
    SL_ref = float(p.get("SL_ref", 30))
    consumed_SL = np.zeros_like(t)

    for i in range(1, len(t)):
        VPD_excess = max(0, VPD[i-1] - VPD_ref)
        fator_embalagem = PACKAGING_FACTORS.get(packaging_methods_rep[i-1], 1.0)
        VPD_efetivo = VPD_excess * fator_embalagem
        # Firmness ODE
        k_VPD_firm = 1 + p.get("beta_RH", 1.0) * VPD_efetivo
        dD = (-kT_firm[i-1] * k_VPD_firm * (firmness[i-1] - firmness_min)) * dt
        firmness[i] = max(firmness_min, firmness[i-1] + dD)

        # Brix ODE
        r_VPD_brix = max(0, 1.0 - 0.2 * VPD_efetivo)
        r_brix = r0 * rT[i-1] * r_VPD_brix
        x = max(0.0, brix[i-1] - brix_min)
        K = max(1e-6, (brix_max - brix_min))
        db = (r_brix * x * (1.0 - x / K)) * dt
        brix[i] = min(brix_max, max(brix[i-1] + db, brix_min))

        # Acidity ODE
        dA = (-kT_acidity[i-1] * (acidity[i-1] - acidity_min)) * dt
        acidity[i] = max(acidity_min, acidity[i-1] + dA)

        # Shelf Life Consumption
        r_T_SL = k_temp_scaling(55000, T_K[i-1], Tref_K)
        r_VPD_SL = 1 + 0.5 * VPD_efetivo
        consumed_SL[i] = consumed_SL[i-1] + (r_T_SL * r_VPD_SL) * dt

    remaining_SL = np.maximum(0, SL_ref - consumed_SL)

    # Quality
    firm_score = 1 / (1 + np.exp(-0.35 * (firmness - float(p["qual_firmness_threshold"]))))
    brix_score = np.exp(-((brix - float(p["qual_brix_target"]))**2) / 2)
    acidity_score = np.exp(-((acidity - float(p.get("qual_acidity_target", 1.0)))**2) / 0.5)

    # Maturation Index
    maturation_index = brix / acidity
    # 1. Calcular o Rácio Alvo (ideal) baseado nos presets
    target_ratio = float(p["qual_brix_target"]) / float(p.get("qual_acidity_target", 1.0))

    # 2. Criar um score para o rácio (penaliza desvios do rácio ideal)
    # O divisor 25.0 controla a "largura" da aceitação. Podes ajustar se quiseres ser mais rigoroso.
    ratio_score = np.exp(-((maturation_index - target_ratio)**2) / 10.0)

    quality_base = 100 * (0.40 * firm_score + 0.30 * ratio_score + 0.15 * brix_score + 0.15 * acidity_score)

    # Mold
    RH_mold_thr = float(p["RH_mold_thr"])
    mold_rate_ref = float(p["mold_rate_ref"])
    mold_sens_RH = float(p["mold_sens_RH"])
    mold_max_penalty = float(p["mold_max_penalty"])
    Ea_mold_J = float(p["Ea_mold_J"])

    mold_T = k_temp_scaling(Ea_mold_J, T_K, Tref_K)

    mold = np.zeros_like(t)
    mold[0] = 0.0
    for i in range(1, len(t)):
        VPD_thr = calc_vpd(T_c[i-1], RH_mold_thr)
        VPD_deficit = max(VPD_thr - VPD[i-1], 0) # Menor VPD = Maior humidade
        VPD_factor = 1.0 - np.exp(-mold_sens_RH * VPD_deficit * 5.0)
        rate = mold_rate_ref * mold_T[i-1] * VPD_factor
        dm = (rate * (1.0 - mold[i-1])) * dt
        mold[i] = min(1.0, np.max(np.append(np.array(mold[i-1] + dm), 0)))

    mold_penalty = mold_max_penalty * mold
    quality = quality_base * (1.0 - mold_penalty)

    remaining_SL = np.where(mold_penalty > 0, 0, remaining_SL)

    arrays_dict = {"quality": quality.tolist(), "firmness": firmness.tolist(), "brix": brix.tolist(), "acidity": acidity.tolist()}
    return quality[len(quality) - 1], remaining_SL[len(remaining_SL) - 1], firmness[len(firmness) - 1], brix[len(brix) - 1], arrays_dict

# FORECAST API ENDPOINT
# ========================================================================

app = FastAPI()

_inference_lock = threading.Lock()
_status_lock = threading.Lock()
_current_operation = {
    "operation": None,
    "client_id": None,
    "store_id": None,
    "product_id": None,
    "algorithm": None,
}

class InitialMetrics(BaseModel):
    soluble_solids_brix: Optional[float] = None
    caliber_mm: Optional[float] = None
    quality_score: Optional[int] = None
    waste_kg: Optional[float] = None
    expiration_date: Optional[str] = None

class LotIdentification(BaseModel):
    lot_id: int
    batch_id: str
    culture_name: str
    fruit_type: str
    producer: str
    current_owner: str
    harvest_date: str
    initial_quantity_kg: float
    current_stock_kg: float
    delivered_quantity_kg: float
    initial_metrics: InitialMetrics

class DailyReading(BaseModel):
    date: str
    temperature_celsius: Optional[float] = None
    humidity_percent: Optional[float] = None
    ethylene_ppm: Optional[float] = None
    source: str

class WarehouseHistory(BaseModel):
    warehouse_id: int
    warehouse_location: str
    region: str
    meteo_source: str
    total_days_recorded: int
    keptancy_start_date: Optional[str] = None # Not on JSON
    packaging_method: Optional[str] = None
    daily_readings: List[DailyReading] = []

class LifecycleDataRequest(BaseModel):
    version: str
    export_metadata: Dict[str, Any]
    lot_identification: LotIdentification
    plantation_origin: Dict[str, Any]
    plantation_agricultural_events: List[Any]
    current_warehouse: Dict[str, Any]
    meteorology_and_imputation_strategy: Dict[str, Any]
    blockchain_ledger: Dict[str, Any]
    transport_and_logistics: List[Any]
    sensor_history_by_warehouse: List[WarehouseHistory]
    plot_info: bool = False

class ForecastResponse(BaseModel):
    service: Literal["inference"]
    client_id: str
    store_id: str
    algorithm: Literal["ode", "ode_academic", "ode_new"]
    product_id: str
    quality_index: float
    remaining_lifetime: float
    firmness: float
    brix: float
    continuous_data: Optional[Dict[str, List[float]]] = None

class StatusResponse(BaseModel):
    busy: bool
    operation: Optional[str] = None
    message: Literal["Available", "Busy"]
    client_id: Optional[str] = None
    store_id: Optional[str] = None
    product_id: Optional[str] = None
    algorithm: Optional[Literal["ode", "ode_academic", "ode_new"]] = None

@app.post("/forecast", response_model=ForecastResponse)
def forecast(request: LifecycleDataRequest, client_id: str = "dummy_client", store_id: str = "dummy_store"):
    # Generate fruit_key
    fruit_type = request.lot_identification.fruit_type.lower()
    culture_name = request.lot_identification.culture_name.lower()
    raw_key = f"{fruit_type}_{culture_name}"
    if raw_key in PRESETS:
        fruit_key = raw_key
    elif fruit_type in PRESETS:
        fruit_key = fruit_type
    elif culture_name in PRESETS:
        fruit_key = culture_name
    else:
        fruit_key = raw_key

    if fruit_key not in PRESETS:
        return JSONResponse(
            status_code=400,
            content={"detail": f"Unknown fruit key derived from fruit_type and culture_name: {fruit_key}. Valid keys: {list(PRESETS.keys())}"}
        )

    acquired = _inference_lock.acquire(blocking=False)
    operation_id = str(uuid.uuid4())
    with _status_lock:
        _current_operation.update({
            "operation": operation_id,
            "client_id": client_id,
            "store_id": store_id,
            "product_id": fruit_key,
            "algorithm": "ode",
        })
    if not acquired:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too Many Requests",
                "message": "Inference already running"
            }
        )

    try:
        # Extract sequences chronologically
        T_c = []
        RH_pct = []
        E_ppm = []
        region_codes = []
        alphas = []
        packaging_methods = []
        
        # Determine alpha for imputation (dummy logic based on current warehouse alpha if we had one)
        # Using 0.9 as default thick/closed warehouse
        default_alpha = 0.9
        
        start_date_str = None

        for wh in request.sensor_history_by_warehouse:
            if not wh.daily_readings and wh.keptancy_start_date and wh.total_days_recorded > 0:
                s_dt = datetime.strptime(wh.keptancy_start_date, "%Y-%m-%d")
                for j in range(wh.total_days_recorded):
                    c_dt = s_dt + timedelta(days=j)
                    wh.daily_readings.append(DailyReading(date=c_dt.strftime("%Y-%m-%d"), source="GENERATED"))
            # We assume chronological order in JSON or we could sort by date
            for reading in wh.daily_readings:
                if start_date_str is None:
                    start_date_str = reading.date
                T_c.append(reading.temperature_celsius)
                RH_pct.append(reading.humidity_percent)
                E_ppm.append(reading.ethylene_ppm)
                region_codes.append(wh.region)
                alphas.append(default_alpha)
                packaging_methods.append(wh.packaging_method)

        if not T_c:
             return JSONResponse(status_code=400, content={"detail": "No sensor history data found."})
        
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        days = len(T_c)
        
        # Impute missing T and RH using refactored function
        fallback_mode = request.meteorology_and_imputation_strategy.get("json_fallback_mode", "IPMA")
        if fallback_mode == "FIXED":
            fixed_t = request.meteorology_and_imputation_strategy.get("fixed_temperature_celsius", 4.0)
            fixed_rh = request.meteorology_and_imputation_strategy.get("fixed_humidity_percent", 90.0)
            T_c = [t if t is not None else fixed_t for t in T_c]
            RH_pct = [rh if rh is not None else fixed_rh for rh in RH_pct]
        else:
            # Impute missing T and RH using IPMA refactored function
            T_c, RH_pct = fill_nulls_with_warehouse_sim(T_c, RH_pct, region_codes, alphas, start_date)
        
        # Handle ethylene nulls
        has_ethylene = any(e is not None for e in E_ppm)
        if has_ethylene:
            # fill nulls with 0 or forward fill
            E_ppm_filled = [e if e is not None else 0.0 for e in E_ppm]
        else:
            E_ppm_filled = None
            
        # Get defaults
        preset = PRESETS[fruit_key]
        
        b0 = request.lot_identification.initial_metrics.soluble_solids_brix
        if b0 is None:
            b0 = preset["brix_0_default"]
            
        f0 = preset["firmness_0_default"]
        a0 = preset.get("acidity_0_default", 0.5)
        if has_ethylene:
            algorithm = "ode_academic"
            quality, lifetime, final_f, final_b, arrays_dict = run_simulation_prof_luis_paulo(
                fruit_key=fruit_key,
                T_c=T_c,
                RH_pct=RH_pct,
                E_ext_ppm=E_ppm_filled,
                days=days,
                firmness_0_user=f0,
                brix_0_user=b0
            )
        else:
            algorithm = "ode_new"
            quality, lifetime, final_f, final_b, arrays_dict = run_simulation_sofia_machado(
                fruit_key=fruit_key,
                T_c=T_c,
                RH_pct=RH_pct,
                days=days,
                firmness_0_user=f0,
                brix_0_user=b0,
                acidity_0_user=a0,
                packaging_methods=packaging_methods
            )

        return ForecastResponse(
            service="inference",
            client_id=client_id,
            store_id=store_id,
            algorithm=algorithm,
            product_id=fruit_key,
            quality_index=quality,
            remaining_lifetime=lifetime,
            firmness=final_f,
            brix=final_b,
            continuous_data=arrays_dict if request.plot_info else None
        )
    finally:
        with _status_lock:
            _current_operation.update({
                "operation": None,
                "client_id": None,
                "store_id": None,
                "product_id": None,
                "algorithm": None,
            })
        _inference_lock.release()

@app.get("/status", response_model=StatusResponse)
def status():
    busy = _inference_lock.locked()
    if not busy:
        return StatusResponse(
            busy=False,
            message="Available"
        )
    with _status_lock:
        op = dict(_current_operation)
    return StatusResponse(
        busy=True,
        operation=op["operation"],
        message="Busy",
        client_id=op["client_id"],
        store_id=op["store_id"],
        product_id=op["product_id"],
        algorithm=op["algorithm"],
    )




class PresetModel(BaseModel):
    Tref_C: float
    Ea_J: float
    k_firm_ref: float
    beta_RH: float
    RH_ref: float
    firmness_min: float
    firmness_0_default: float
    brix_min: float
    brix_max: float
    brix_g: float
    brix_0_default: float
    qual_firmness_threshold: float
    qual_brix_target: float
    acidity_0_default: float
    acidity_min: float
    k_acidity_ref: float
    Ea_acidity_J: float
    qual_acidity_target: float
    SL_ref: float
    E0_int: float
    Eref_prod: float
    E_t0: float
    E_g: float
    E_auto: float
    E_decay: float
    Ea_E_J: float
    E_ext_shift: float
    alpha_E: float

class MoldPresetModel(BaseModel):
    RH_mold_thr: float
    mold_rate_ref: float
    mold_sens_RH: float
    mold_max_penalty: float
    Ea_mold_J: float

class PresetRequest(BaseModel):
    fruit_key: str
    preset: PresetModel
    mold_preset: MoldPresetModel

@app.post("/preset")
def add_preset(request: PresetRequest):
    PRESETS[request.fruit_key] = request.preset.model_dump()
    MOLD_BY_FRUIT[request.fruit_key] = request.mold_preset.model_dump()
    return {"message": "Preset added successfully", "fruit_key": request.fruit_key}

@app.get("/presets")
def get_presets():
    return {"fruits": list(PRESETS.keys())}

if __name__ == "__main__":
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8181)

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    try:
        server_thread.join()
    except KeyboardInterrupt:
        pass