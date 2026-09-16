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

# PRESETS & CONFIGURATION
# =============================================================================
# 1) FRUIT PRESETS
# -----------------------------------------------------------------------------
# Each fruit has:
#
#   Thermodynamics / Kinetics:
#     - Tref_C      : reference temperature for parameters (°C)
#     - Ea_J        : activation energy for softening (J/mol)
#     - k_firm_ref  : base rate of softening at Tref (1/day approx)
#
#   Humidity:
#     - RH_ref      : RH "ideal" (or typical storage) for this fruit (%)
#     - beta_RH     : sensitivity to low RH (dehydration) in softening
#
#   Firmness:
#     - firmness_0_default : typical firmness at day 0 (suggested initial value, in N)
#     - firmness_min       : minimum limit (asymptote) of softening (in N)
#
#   Ethylene and Sensitivity:
#     - alpha_E     : how much total ethylene accelerates softening (1/ppm)
#
#   Brix:
#     - brix_0_default : typical brix at day 0
#     - brix_min/max   : theoretical minimum/maximum limits in the model
#     - brix_g         : base logistic rate (not 'days to maturation')
#
#   Quality (Index 0-100):
#     - qual_firmness_threshold : 'threshold' of firmness considered acceptable (in N)
#     - qual_brix_target    : 'target' brix (peak of brix score)
#
#   Acidity:
#     - acidity_0_default : typical acidity at day 0
#     - acidity_min       : theoretical minimum acidity
#     - k_acidity_ref     : base rate of acidity degradation
#     - Ea_acidity_J      : activation energy
#     - qual_acidity_target: target acidity for maximum quality
#
#   Shelf Life:
#     - SL_ref           : maximum reference shelf life in days
#
#   Endogenous Ethylene (internal production):
#     - E0_int      : initial internal ethylene (ppm)
#     - Eref_prod   : maximum production (ppm/day) at Tref and after ramp
#     - E_t0        : day when climacteric phase starts (without E_ext)
#     - E_g         : slope of climacteric ramp sigmoid
#     - E_auto      : autocatalysis (more E -> more production)
#     - E_decay     : removal/degradation (1/day)
#     - Ea_E_J      : activation energy for ethylene production
#     - E_ext_shift : how much E_ext anticipates the climacteric trigger
#
#   Mold/Rot (high RH):
#     - RH_mold_thr     : threshold (%) from which there is significant risk
#     - mold_rate_ref   : base rate of mold growth at Tref (1/day)
#     - mold_sens_RH    : sensitivity to RH surplus above threshold
#     - mold_max_penalty: maximum quality penalty (0..1)
#     - Ea_mold_J       : activation energy for mold growth
#
# 2) PACKAGING FACTORS (PACKAGING_FACTORS)
# -----------------------------------------------------------------------------
# These act as multipliers applied directly to the Vapor Pressure Deficit (VPD)
# and External Ethylene (E_ext) based on the packaging type, simulating modified
# atmospheres or barriers that reduce moisture loss and gas exchange.
#
# 3) STAKEHOLDER PROFILES (STAKEHOLDER_PROFILES)
# -----------------------------------------------------------------------------
# Profiles defining custom quality limits based on who currently owns the fruit.
# Contains relative multipliers applied to the fruit's base properties:
#   - firm_multiplier: strictness on structural integrity
#   - brix_multiplier / ratio_multiplier: strictness on sweetness and maturation
#   - mold_limit / min_quality: hard absolute thresholds before rejection
# =============================================================================

PRESETS_ACADEMIC = {
    "kiwi_hayward": {
        "label": "Kiwi (Hayward)",
        "Tref_C": 5.0,
        "Ea_J": 60000,
        "k_firm_ref": 0.06,
        "alpha_E": 1.8,
        "beta_RH": 1.2,
        "RH_ref": 90,
        "brix_min": 11,
        "brix_max": 17,
        "brix_g": 0.35,
        "brix_0_default": 11.0,
        "qual_brix_target": 15,
        "E0_int": 0.02,
        "Eref_prod": 0.12,
        "E_t0": 10,
        "E_g": 0.9,
        "E_auto": 0.35,
        "E_decay": 0.7,
        "Ea_E_J": 52000,
        "E_ext_shift": 2.0,
        "firmness_min": 3,
        "firmness_0_default": 45,
        "qual_firmness_threshold": 8,
    },
    "kiwi_baby": {
        "label": "Kiwi (Baby/Berry)",
        "Tref_C": 4.0,
        "Ea_J": 58000,
        "k_firm_ref": 0.14,
        "alpha_E": 3.2,
        "beta_RH": 2.0,
        "RH_ref": 95,
        "brix_min": 13,
        "brix_max": 20,
        "brix_g": 0.5,
        "brix_0_default": 14.5,
        "qual_brix_target": 17,
        "E0_int": 0.03,
        "Eref_prod": 0.22,
        "E_t0": 5,
        "E_g": 1.2,
        "E_auto": 0.55,
        "E_decay": 0.75,
        "Ea_E_J": 52000,
        "E_ext_shift": 2.6,
        "firmness_min": 2,
        "firmness_0_default": 28,
        "qual_firmness_threshold": 6,
    },
    "apple_golden": {
        "label": "Apple (Golden)",
        "Tref_C": 5.0,
        "Ea_J": 50000,
        "k_firm_ref": 0.025,
        "alpha_E": 0.8,
        "beta_RH": 0.8,
        "RH_ref": 90,
        "brix_min": 11.5,
        "brix_max": 15.5,
        "brix_g": 0.18,
        "brix_0_default": 12.0,
        "qual_brix_target": 13.5,
        "E0_int": 0.01,
        "Eref_prod": 0.1,
        "E_t0": 18,
        "E_g": 0.6,
        "E_auto": 0.35,
        "E_decay": 0.55,
        "Ea_E_J": 52000,
        "E_ext_shift": 1.8,
        "firmness_min": 12,
        "firmness_0_default": 72,
        "qual_firmness_threshold": 35,
    },
    "apple_reineta": {
        "label": "Apple (Reineta)",
        "Tref_C": 5.0,
        "Ea_J": 52000,
        "k_firm_ref": 0.035,
        "alpha_E": 1.1,
        "beta_RH": 1.0,
        "RH_ref": 90,
        "brix_min": 11.0,
        "brix_max": 14.0,
        "brix_g": 0.16,
        "brix_0_default": 11.5,
        "qual_brix_target": 12.5,
        "E0_int": 0.01,
        "Eref_prod": 0.13,
        "E_t0": 14,
        "E_g": 0.7,
        "E_auto": 0.4,
        "E_decay": 0.6,
        "Ea_E_J": 52000,
        "E_ext_shift": 2.0,
        "firmness_min": 10,
        "firmness_0_default": 65,
        "qual_firmness_threshold": 30,
    },
    "apple_gala": {
        "label": "Apple (Gala)",
        "Tref_C": 5.0,
        "Ea_J": 48000,
        "k_firm_ref": 0.04,
        "alpha_E": 1.3,
        "beta_RH": 0.9,
        "RH_ref": 90,
        "brix_min": 12.5,
        "brix_max": 17.0,
        "brix_g": 0.25,
        "brix_0_default": 13.0,
        "qual_brix_target": 14.5,
        "E0_int": 0.015,
        "Eref_prod": 0.18,
        "E_t0": 10,
        "E_g": 0.9,
        "E_auto": 0.5,
        "E_decay": 0.65,
        "Ea_E_J": 52000,
        "E_ext_shift": 2.2,
        "firmness_min": 9,
        "firmness_0_default": 60,
        "qual_firmness_threshold": 28,
    },
    "apple_fuji": {
        "label": "Apple (Fuji)",
        "Tref_C": 5.0,
        "Ea_J": 47000,
        "k_firm_ref": 0.018,
        "alpha_E": 0.6,
        "beta_RH": 0.7,
        "RH_ref": 90,
        "brix_min": 13.0,
        "brix_max": 19.0,
        "brix_g": 0.15,
        "brix_0_default": 14.0,
        "qual_brix_target": 16.0,
        "E0_int": 0.008,
        "Eref_prod": 0.06,
        "E_t0": 25,
        "E_g": 0.5,
        "E_auto": 0.25,
        "E_decay": 0.45,
        "Ea_E_J": 52000,
        "E_ext_shift": 1.4,
        "firmness_min": 15,
        "firmness_0_default": 80,
        "qual_firmness_threshold": 40,
    },
    "orange": {
        "label": "Orange",
        "Tref_C": 5.0,
        "Ea_J": 42000,
        "k_firm_ref": 0.01,
        "alpha_E": 0.15,
        "beta_RH": 0.35,
        "RH_ref": 90,
        "brix_min": 10.5,
        "brix_max": 13.5,
        "brix_g": 0.1,
        "brix_0_default": 11.5,
        "qual_brix_target": 12.2,
        "E0_int": 0.002,
        "Eref_prod": 0.01,
        "E_t0": 999,
        "E_g": 0.2,
        "E_auto": 0.0,
        "E_decay": 0.8,
        "Ea_E_J": 40000,
        "E_ext_shift": 0.5,
        "firmness_min": 35,
        "firmness_0_default": 55,
        "qual_firmness_threshold": 42,
    },
    "banana": {
        "label": "Banana",
        "Tref_C": 14.0,
        "Ea_J": 65000,
        "k_firm_ref": 0.09,
        "alpha_E": 2.2,
        "beta_RH": 1.0,
        "RH_ref": 90,
        "brix_min": 12.0,
        "brix_max": 22.0,
        "brix_g": 0.45,
        "brix_0_default": 12.5,
        "qual_brix_target": 19,
        "E0_int": 0.02,
        "Eref_prod": 0.35,
        "E_t0": 4,
        "E_g": 1.4,
        "E_auto": 0.7,
        "E_decay": 0.9,
        "Ea_E_J": 60000,
        "E_ext_shift": 3.0,
        "firmness_min": 5,
        "firmness_0_default": 80,
        "qual_firmness_threshold": 15,
    },
    "blueberry": {
        "label": "Blueberry",
        "Tref_C": 2.0,
        "Ea_J": 52000,
        "k_firm_ref": 0.03,
        "alpha_E": 0.1,
        "beta_RH": 1.6,
        "RH_ref": 95,
        "brix_min": 10.0,
        "brix_max": 14.0,
        "brix_g": 0.2,
        "brix_0_default": 11.5,
        "qual_brix_target": 12.5,
        "E0_int": 0.002,
        "Eref_prod": 0.01,
        "E_t0": 999,
        "E_g": 0.2,
        "E_auto": 0.0,
        "E_decay": 0.9,
        "Ea_E_J": 42000,
        "E_ext_shift": 0.4,
        "firmness_min": 6,
        "firmness_0_default": 30,
        "qual_firmness_threshold": 12,
    },
    "raspberry": {
        "label": "Raspberry",
        "Tref_C": 2.0,
        "Ea_J": 56000,
        "k_firm_ref": 0.06,
        "alpha_E": 0.12,
        "beta_RH": 2.2,
        "RH_ref": 95,
        "brix_min": 7.0,
        "brix_max": 12.0,
        "brix_g": 0.22,
        "brix_0_default": 9.5,
        "qual_brix_target": 10.0,
        "E0_int": 0.002,
        "Eref_prod": 0.01,
        "E_t0": 999,
        "E_g": 0.2,
        "E_auto": 0.0,
        "E_decay": 0.9,
        "Ea_E_J": 42000,
        "E_ext_shift": 0.4,
        "firmness_min": 2.5,
        "firmness_0_default": 18,
        "qual_firmness_threshold": 6,
    },
    "pear": {
        "label": "Pear",
        "Tref_C": 2.0,
        "Ea_J": 54000,
        "k_firm_ref": 0.05,
        "alpha_E": 1.6,
        "beta_RH": 1.2,
        "RH_ref": 92,
        "brix_min": 10.5,
        "brix_max": 16.5,
        "brix_g": 0.28,
        "brix_0_default": 11.5,
        "qual_brix_target": 14.0,
        "E0_int": 0.01,
        "Eref_prod": 0.22,
        "E_t0": 10,
        "E_g": 1.0,
        "E_auto": 0.6,
        "E_decay": 0.75,
        "Ea_E_J": 56000,
        "E_ext_shift": 2.3,
        "firmness_min": 4,
        "firmness_0_default": 55,
        "qual_firmness_threshold": 10,
    },
    "plum": {
        "label": "Plum",
        "Tref_C": 2.0,
        "Ea_J": 52000,
        "k_firm_ref": 0.06,
        "alpha_E": 1.0,
        "beta_RH": 1.0,
        "RH_ref": 92,
        "brix_min": 11.0,
        "brix_max": 20.0,
        "brix_g": 0.3,
        "brix_0_default": 12.5,
        "qual_brix_target": 16.5,
        "E0_int": 0.01,
        "Eref_prod": 0.14,
        "E_t0": 8,
        "E_g": 0.8,
        "E_auto": 0.45,
        "E_decay": 0.7,
        "Ea_E_J": 54000,
        "E_ext_shift": 2.0,
        "firmness_min": 3,
        "firmness_0_default": 40,
        "qual_firmness_threshold": 8,
    },
    "peach": {
        "label": "Peach",
        "Tref_C": 2.0,
        "Ea_J": 56000,
        "k_firm_ref": 0.08,
        "alpha_E": 1.4,
        "beta_RH": 1.1,
        "RH_ref": 92,
        "brix_min": 9.5,
        "brix_max": 18.0,
        "brix_g": 0.35,
        "brix_0_default": 11.0,
        "qual_brix_target": 15.0,
        "E0_int": 0.012,
        "Eref_prod": 0.22,
        "E_t0": 6,
        "E_g": 1.0,
        "E_auto": 0.55,
        "E_decay": 0.8,
        "Ea_E_J": 56000,
        "E_ext_shift": 2.4,
        "firmness_min": 2,
        "firmness_0_default": 35,
        "qual_firmness_threshold": 6,
    },
    "cherry": {
        "label": "Cherry",
        "Tref_C": 2.0,
        "Ea_J": 48000,
        "k_firm_ref": 0.045,
        "alpha_E": 0.05,
        "beta_RH": 1.6,
        "RH_ref": 95,
        "brix_min": 14.0,
        "brix_max": 20.0,
        "brix_g": 0.08,
        "brix_0_default": 16.0,
        "qual_brix_target": 18.0,
        "E0_int": 0.002,
        "Eref_prod": 0.01,
        "E_t0": 999,
        "E_g": 0.2,
        "E_auto": 0.0,
        "E_decay": 0.9,
        "Ea_E_J": 42000,
        "E_ext_shift": 0.4,
        "firmness_min": 4,
        "firmness_0_default": 28,
        "qual_firmness_threshold": 10,
    },
    "strawberry": {
        "label": "Strawberry",
        "Tref_C": 2.0,
        "Ea_J": 52000,
        "k_firm_ref": 0.12,
        "alpha_E": 0.05,
        "beta_RH": 2.4,
        "RH_ref": 95,
        "brix_min": 6.0,
        "brix_max": 10.5,
        "brix_g": 0.12,
        "brix_0_default": 7.5,
        "qual_brix_target": 9.0,
        "E0_int": 0.002,
        "Eref_prod": 0.01,
        "E_t0": 999,
        "E_g": 0.2,
        "E_auto": 0.0,
        "E_decay": 0.9,
        "Ea_E_J": 42000,
        "E_ext_shift": 0.4,
        "firmness_min": 1.5,
        "firmness_0_default": 12,
        "qual_firmness_threshold": 4.5,
    },
    "grape": {
        "label": "Grape",
        "Tref_C": 2.0,
        "Ea_J": 45000,
        "k_firm_ref": 0.02,
        "alpha_E": 0.05,
        "beta_RH": 1.8,
        "RH_ref": 92,
        "brix_min": 14.0,
        "brix_max": 22.0,
        "brix_g": 0.05,
        "brix_0_default": 16.0,
        "qual_brix_target": 18.0,
        "E0_int": 0.002,
        "Eref_prod": 0.01,
        "E_t0": 999,
        "E_g": 0.2,
        "E_auto": 0.0,
        "E_decay": 0.9,
        "Ea_E_J": 42000,
        "E_ext_shift": 0.4,
        "firmness_min": 3,
        "firmness_0_default": 20,
        "qual_firmness_threshold": 7,
    },
    "fig": {
        "label": "Fig",
        "Tref_C": 2.0,
        "Ea_J": 52000,
        "k_firm_ref": 0.11,
        "alpha_E": 0.2,
        "beta_RH": 1.8,
        "RH_ref": 95,
        "brix_min": 14.0,
        "brix_max": 26.0,
        "brix_g": 0.18,
        "brix_0_default": 16.0,
        "qual_brix_target": 20.0,
        "E0_int": 0.005,
        "Eref_prod": 0.05,
        "E_t0": 12,
        "E_g": 0.5,
        "E_auto": 0.15,
        "E_decay": 0.7,
        "Ea_E_J": 52000,
        "E_ext_shift": 1.0,
        "firmness_min": 1.2,
        "firmness_0_default": 10,
        "qual_firmness_threshold": 3.5,
    },
    "melon": {
        "label": "Melon",
        "Tref_C": 7.0,
        "Ea_J": 52000,
        "k_firm_ref": 0.06,
        "alpha_E": 0.9,
        "beta_RH": 0.9,
        "RH_ref": 90,
        "brix_min": 9.0,
        "brix_max": 16.0,
        "brix_g": 0.22,
        "brix_0_default": 10.5,
        "qual_brix_target": 13.5,
        "E0_int": 0.01,
        "Eref_prod": 0.1,
        "E_t0": 10,
        "E_g": 0.7,
        "E_auto": 0.35,
        "E_decay": 0.7,
        "Ea_E_J": 52000,
        "E_ext_shift": 1.8,
        "firmness_min": 2.0,
        "firmness_0_default": 25,
        "qual_firmness_threshold": 6.0,
    },
}

PRESETS_SOFIA = {
    "kiwi_hayward": {
        "label": "Kiwi (Hayward)",
        "Tref_C": 5.0,
        "Ea_J": 60000,
        "k_firm_ref": 0.06,
        "beta_RH": 1.2,
        "RH_ref": 90,
        "brix_min": 11,
        "brix_max": 17,
        "brix_g": 0.35,
        "brix_0_default": 11.0,
        "qual_brix_target": 15,
        "SL_ref": 30,
        "firmness_min": 2,
        "firmness_0_default": 18,
        "qual_firmness_threshold": 5,
        "acidity_0_default": 1.5,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "kiwi_baby": {
        "label": "Kiwi (Baby/Berry)",
        "Tref_C": 4.0,
        "Ea_J": 58000,
        "k_firm_ref": 0.14,
        "beta_RH": 2.0,
        "RH_ref": 95,
        "brix_min": 8.0,
        "brix_max": 18.0,
        "brix_g": 0.5,
        "brix_0_default": 8.0,
        "qual_brix_target": 17.0,
        "SL_ref": 45,
        "firmness_min": 1.5,
        "firmness_0_default": 40,
        "qual_firmness_threshold": 6.0,
        "acidity_0_default": 1.1,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "apple_fuji": {
        "label": "Apple (Fuji)",
        "Tref_C": 5.0,
        "Ea_J": 47000,
        "k_firm_ref": 0.018,
        "beta_RH": 0.7,
        "RH_ref": 90,
        "brix_min": 13.0,
        "brix_max": 17.0,
        "brix_g": 0.15,
        "brix_0_default": 13.0,
        "qual_brix_target": 16.0,
        "SL_ref": 180,
        "firmness_min": 25.0,
        "firmness_0_default": 85,
        "qual_firmness_threshold": 45.0,
        "acidity_0_default": 0.4,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "apple_golden": {
        "label": "Apple (Golden)",
        "Tref_C": 5.0,
        "Ea_J": 50000,
        "k_firm_ref": 0.025,
        "beta_RH": 0.8,
        "RH_ref": 90,
        "brix_min": 11.0,
        "brix_max": 14.5,
        "brix_g": 0.18,
        "brix_0_default": 11.0,
        "qual_brix_target": 13.5,
        "SL_ref": 120,
        "firmness_min": 20.0,
        "firmness_0_default": 70,
        "qual_firmness_threshold": 40.0,
        "acidity_0_default": 0.5,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "apple_gala": {
        "label": "Apple (Gala)",
        "Tref_C": 5.0,
        "Ea_J": 48000,
        "k_firm_ref": 0.04,
        "beta_RH": 0.9,
        "RH_ref": 90,
        "brix_min": 12.0,
        "brix_max": 15.0,
        "brix_g": 0.2,
        "brix_0_default": 12.0,
        "qual_brix_target": 14.5,
        "SL_ref": 90,
        "firmness_min": 16.0,
        "firmness_0_default": 70,
        "qual_firmness_threshold": 30.0,
        "acidity_0_default": 0.4,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "apple_reineta": {
        "label": "Apple (Reineta)",
        "Tref_C": 5.0,
        "Ea_J": 52000,
        "k_firm_ref": 0.035,
        "beta_RH": 1.0,
        "RH_ref": 90,
        "brix_min": 10.5,
        "brix_max": 13.5,
        "brix_g": 0.16,
        "brix_0_default": 10.5,
        "qual_brix_target": 12.5,
        "SL_ref": 90,
        "firmness_min": 18.0,
        "firmness_0_default": 65,
        "qual_firmness_threshold": 35.0,
        "acidity_0_default": 0.8,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "strawberry": {
        "label": "Strawberry",
        "Tref_C": 2.0,
        "Ea_J": 52000,
        "k_firm_ref": 0.12,
        "beta_RH": 2.4,
        "RH_ref": 95,
        "brix_min": 7.5,
        "brix_max": 8.0,
        "brix_g": 0.01,
        "brix_0_default": 7.5,
        "qual_brix_target": 7.5,
        "SL_ref": 7,
        "firmness_min": 1.0,
        "firmness_0_default": 5,
        "qual_firmness_threshold": 2.0,
        "acidity_0_default": 0.8,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "raspberry": {
        "label": "Raspberry",
        "Tref_C": 2.0,
        "Ea_J": 56000,
        "k_firm_ref": 0.06,
        "beta_RH": 2.2,
        "RH_ref": 95,
        "brix_min": 9.5,
        "brix_max": 10.0,
        "brix_g": 0.01,
        "brix_0_default": 9.5,
        "qual_brix_target": 9.5,
        "SL_ref": 7,
        "firmness_min": 1.5,
        "firmness_0_default": 6,
        "qual_firmness_threshold": 2.5,
        "acidity_0_default": 1.2,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "blueberry": {
        "label": "Blueberry",
        "Tref_C": 2.0,
        "Ea_J": 52000,
        "k_firm_ref": 0.03,
        "beta_RH": 1.6,
        "RH_ref": 95,
        "brix_min": 11.5,
        "brix_max": 12.0,
        "brix_g": 0.01,
        "brix_0_default": 11.5,
        "qual_brix_target": 11.5,
        "SL_ref": 21,
        "firmness_min": 3.0,
        "firmness_0_default": 10,
        "qual_firmness_threshold": 4.0,
        "acidity_0_default": 0.6,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "cherry": {
        "label": "Cherry",
        "Tref_C": 2.0,
        "Ea_J": 48000,
        "k_firm_ref": 0.045,
        "beta_RH": 1.6,
        "RH_ref": 95,
        "brix_min": 16.0,
        "brix_max": 16.5,
        "brix_g": 0.01,
        "brix_0_default": 16.0,
        "qual_brix_target": 16.0,
        "SL_ref": 21,
        "firmness_min": 8.0,
        "firmness_0_default": 15,
        "qual_firmness_threshold": 10.0,
        "acidity_0_default": 0.5,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "peach": {
        "label": "Peach",
        "Tref_C": 2.0,
        "Ea_J": 56000,
        "k_firm_ref": 0.08,
        "beta_RH": 1.1,
        "RH_ref": 92,
        "brix_min": 10.0,
        "brix_max": 14.0,
        "brix_g": 0.2,
        "brix_0_default": 10.0,
        "qual_brix_target": 13.0,
        "SL_ref": 14,
        "firmness_min": 4.0,
        "firmness_0_default": 40,
        "qual_firmness_threshold": 8.0,
        "acidity_0_default": 0.6,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "plum": {
        "label": "Plum",
        "Tref_C": 2.0,
        "Ea_J": 52000,
        "k_firm_ref": 0.06,
        "beta_RH": 1.0,
        "RH_ref": 92,
        "brix_min": 10.0,
        "brix_max": 16.0,
        "brix_g": 0.25,
        "brix_0_default": 10.0,
        "qual_brix_target": 15.0,
        "SL_ref": 21,
        "firmness_min": 5.0,
        "firmness_0_default": 35,
        "qual_firmness_threshold": 10.0,
        "acidity_0_default": 0.8,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "orange": {
        "label": "Orange",
        "Tref_C": 5.0,
        "Ea_J": 42000,
        "k_firm_ref": 0.01,
        "beta_RH": 0.35,
        "RH_ref": 90,
        "brix_min": 11.0,
        "brix_max": 11.5,
        "brix_g": 0.01,
        "brix_0_default": 11.0,
        "qual_brix_target": 11.0,
        "SL_ref": 90,
        "firmness_min": 20.0,
        "firmness_0_default": 50,
        "qual_firmness_threshold": 35.0,
        "acidity_0_default": 1.0,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "banana": {
        "label": "Banana",
        "Tref_C": 14.0,
        "Ea_J": 65000,
        "k_firm_ref": 0.09,
        "beta_RH": 1.0,
        "RH_ref": 90,
        "brix_min": 5.0,
        "brix_max": 20.0,
        "brix_g": 0.5,
        "brix_0_default": 5.0,
        "qual_brix_target": 19.0,
        "SL_ref": 21,
        "firmness_min": 5.0,
        "firmness_0_default": 80,
        "qual_firmness_threshold": 15.0,
        "acidity_0_default": 0.4,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "pear": {
        "label": "Pear",
        "Tref_C": 2.0,
        "Ea_J": 54000,
        "k_firm_ref": 0.05,
        "beta_RH": 1.2,
        "RH_ref": 92,
        "brix_min": 11.0,
        "brix_max": 15.0,
        "brix_g": 0.25,
        "brix_0_default": 11.0,
        "qual_brix_target": 14.0,
        "SL_ref": 90,
        "firmness_min": 6.0,
        "firmness_0_default": 50,
        "qual_firmness_threshold": 12.0,
        "acidity_0_default": 0.3,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "grape": {
        "label": "Grape",
        "Tref_C": 2.0,
        "Ea_J": 45000,
        "k_firm_ref": 0.02,
        "beta_RH": 1.8,
        "RH_ref": 92,
        "brix_min": 16.0,
        "brix_max": 16.5,
        "brix_g": 0.01,
        "brix_0_default": 16.0,
        "qual_brix_target": 16.0,
        "SL_ref": 45,
        "firmness_min": 5.0,
        "firmness_0_default": 15,
        "qual_firmness_threshold": 8.0,
        "acidity_0_default": 0.6,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "fig": {
        "label": "Fig",
        "Tref_C": 2.0,
        "Ea_J": 52000,
        "k_firm_ref": 0.11,
        "beta_RH": 1.8,
        "RH_ref": 95,
        "brix_min": 16.0,
        "brix_max": 20.0,
        "brix_g": 0.15,
        "brix_0_default": 16.0,
        "qual_brix_target": 19.0,
        "SL_ref": 7,
        "firmness_min": 1.0,
        "firmness_0_default": 8,
        "qual_firmness_threshold": 2.0,
        "acidity_0_default": 0.3,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
    "melon": {
        "label": "Melon",
        "Tref_C": 7.0,
        "Ea_J": 52000,
        "k_firm_ref": 0.06,
        "beta_RH": 0.9,
        "RH_ref": 90,
        "brix_min": 10.0,
        "brix_max": 14.0,
        "brix_g": 0.22,
        "brix_0_default": 10.0,
        "qual_brix_target": 13.5,
        "SL_ref": 21,
        "firmness_min": 5.0,
        "firmness_0_default": 20,
        "qual_firmness_threshold": 8.0,
        "acidity_0_default": 0.2,
        "acidity_min": 0.5,
        "k_acidity_ref": 0.02,
        "Ea_acidity_J": 55000,
        "qual_acidity_target": 1.0,
    },
}

MOLD_DEFAULTS = {
    "RH_mold_thr": 95.0,        # RH (%) from which significant risk starts
    "mold_rate_ref": 0.06,      # base rate (1/day) at Tref
    "mold_sens_RH": 10.0,       # sensitivity to RH surplus above threshold
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
}

PACKAGING_FACTORS = {
   "Granel (Sem embalagem)": 1.0,
   "Caixa de Cartão Aberta": 0.85,
   "Saco Plástico Perfurado": 0.45,
   "MAP (Atmosfera Modificada) / Plástico Selado": 0.10
}

STAKEHOLDER_PROFILES = {
    "Producer / Exporter": {
        "min_quality": 75,       # High overall quality required for export clearance
        "firm_multiplier": 1.4,  # Must be very firm to survive long transit
        "mold_limit": 0.01,      # Near-zero tolerance (mold spreads in shipping containers)
        "brix_multiplier": 0.75, # Can be harvested under-ripe (will ripen in transit)
        "ratio_multiplier": 0.7  # Can be more acidic at shipping time
    },
    "Retailer (Grocery Store)": {
        "min_quality": 65,       # Good visual and structural quality for display
        "firm_multiplier": 1.0,  # Standard firmness (ready for consumer handling)
        "mold_limit": 0.03,      # Very low tolerance on shelves
        "brix_multiplier": 0.95, # Must be sweet enough for immediate consumption
        "ratio_multiplier": 0.9  # Good sweet-to-acid balance
    },
    "Industry (Juices/Jellies)": {
        "min_quality": 20,       # Visuals don't matter much
        "firm_multiplier": 0.15,  # Can be very soft/overripe
        "mold_limit": 0.08,      # Slightly higher tolerance (sorted out in processing)
        "brix_multiplier": 1.0,  # Requires high sugar yield (but capped at 100% of target to avoid exceeding max brix)
        "ratio_multiplier": 1.0  # Sweeter is better (capped at 100% of target)
    }
}

for k in PRESETS_ACADEMIC:
    for kk, vv in MOLD_DEFAULTS.items():
        PRESETS_ACADEMIC[k].setdefault(kk, vv)
    if k in MOLD_BY_FRUIT:
        PRESETS_ACADEMIC[k].update(MOLD_BY_FRUIT[k])

for k in PRESETS_SOFIA:
    for kk, vv in MOLD_DEFAULTS.items():
        PRESETS_SOFIA[k].setdefault(kk, vv)
    if k in MOLD_BY_FRUIT:
        PRESETS_SOFIA[k].update(MOLD_BY_FRUIT[k])


# Helper to get the correct preset
def get_preset(fruit_key):
    if fruit_key in PRESETS_ACADEMIC:
        return PRESETS_ACADEMIC[fruit_key]
    if fruit_key in PRESETS_SOFIA:
        return PRESETS_SOFIA[fruit_key]
    raise KeyError(f"Preset {fruit_key} not found.")

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
        current_date = start_date + timedelta(days=i)
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
def run_simulation_prof_luis_paulo(fruit_key, T_c, E_ext_ppm, RH_pct, days, firmness_0_user, brix_0_user, custom_preset=None) -> tuple[float, float, float, float, dict]:
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
        tuple[float, float, float, float, dict]: The final quality index, remaining shelf life, final firmness, final brix, and the continuous arrays dictionary.
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
        p = PRESETS_ACADEMIC[fruit_key]
    max_sim_days = max(days + 200, 365)
    t = np.arange(0, max_sim_days + dt*0.5, dt)
    
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
    E_int[0] = float(p["E0_int"])

    Ea_E_J = float(p["Ea_E_J"])
    Eref_prod = float(p["Eref_prod"])            # maximum production (ppm/dia)
    E_decay = float(p["E_decay"])                 # remoção (1/dia)
    E_t0 = float(p["E_t0"])                       # gatilho sem E_ext (dias)
    E_g = float(p["E_g"])                          # inclinação do gatilho
    E_auto = float(p["E_auto"])                   # autocatálise
    E_ext_shift = float(p["E_ext_shift"])          # E_ext antecipa o gatilho

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
        # Low RH can reduce 'efficiency' (stress/dehydration)
        bRH = max(0.0, (RH_ref - RH_pct[i-1]) / 100.0)
        rRH = (1.0 - 0.6 * bRH)
        r = r0 * rT[i-1] * rRH * (1.0 + alpha_bE * E_total[i-1])
        x = max(0.01, brix[i-1] - brix_min)
        K = max(1e-6, (brix_max - brix_min))
        db = (r * x * (1.0 - x / K)) * dt
        brix[i] = min(brix_max, max(brix_min, brix[i-1] + db))

    # -------------------------------------------------------------------------
    # 4.6) Base QUALITY (0-100)
    # -------------------------------------------------------------------------
    firm_score = 1 / (1 + np.exp(-0.35 * (firmness - float(p["qual_firmness_threshold"]))))
    brix_score = np.exp(-((brix - float(p["qual_brix_target"]))**2) / 2)
    quality_base = 100 * (0.65 * firm_score + 0.35 * brix_score)

    # -------------------------------------------------------------------------
    # 4.7) BOLOR / PODRIDÃO (RH alta)
    # -------------------------------------------------------------------------
    # mold(t) grows when RH > RH_mold_thr:
    #   dm/dt = rate * (1 - m)
    # rate increases with temperature and RH surplus.
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
        
    idx_end = idx_days + 1
    arrays_dict = {
        "quality": quality[:idx_end].tolist(),
        "firmness": firmness[:idx_end].tolist(),
        "brix": brix[:idx_end].tolist(),
        "t": t[:idx_end].tolist()
    }
    return final_quality, remaining_SL, firmness[idx_days], brix[idx_days], arrays_dict

# SIM (Firmness, Brix, Acidity, VPD, Shelf Life & Mold) Sofia Machado
# =============================================================================
def run_simulation_sofia_machado(fruit_key: str, T_c: list[float], RH_pct: list[float], days: int,
                   firmness_0_user: float, brix_0_user: float, acidity_0_user: float, 
                   packaging_methods: Optional[list[str]] = None,
                   dt: int = 0.05, custom_preset: dict = None, current_owner_type: Optional[str] = None
                   ) -> tuple[float, float, float, float, dict]:
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
        current_owner_type (str | None, optional): Stakeholder profile. Defaults to None.

    Returns:
        tuple[float, float, float, float, dict]: The final quality index, remaining shelf life, final firmness, final brix, and the continuous arrays dictionary.
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
        p = PRESETS_SOFIA[fruit_key]
        
    if packaging_methods is None:
        packaging_methods = ["Granel (Sem embalagem)"] * days
    else:
        packaging_methods = [pm if pm is not None else "Granel (Sem embalagem)" for pm in packaging_methods]
        
    t = np.arange(0, days + dt*0.5, dt)
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
        x = max(0.01, brix[i-1] - brix_min)
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
    brix_score = np.exp(-((brix - float(p["qual_brix_target"]))**2) / 2.0)
    
    acidity_score = np.exp(-((acidity - float(p.get("qual_acidity_target", 1.0)))**2) / 0.5)
    maturation_index = brix / acidity
    target_ratio = float(p["qual_brix_target"]) / float(p.get("qual_acidity_target", 1.0))
    ratio_score = np.exp(-((maturation_index - target_ratio)**2) / 10.0)
    quality_base = 100 * (0.35 * firm_score + 0.35 * ratio_score + 0.15 * brix_score + 0.15 * acidity_score)

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
        VPD_deficit = max(VPD_thr - VPD[i-1], 0) # Lower VPD = Higher humidity
        VPD_factor = 1.0 - np.exp(-mold_sens_RH * VPD_deficit * 5.0)
        rate = mold_rate_ref * mold_T[i-1] * VPD_factor
        dm = (rate * (1.0 - mold[i-1])) * dt
        mold[i] = min(1.0, np.max(np.append(np.array(mold[i-1] + dm), 0)))

    profile = STAKEHOLDER_PROFILES.get(current_owner_type, STAKEHOLDER_PROFILES["Retailer (Grocery Store)"])
    
    target_brix = float(p["qual_brix_target"])
    target_acidity = float(p.get("qual_acidity_target", 1.0))
    target_ratio = target_brix / target_acidity
    
    firmness_limit = float(p["qual_firmness_threshold"]) * profile["firm_multiplier"]
    mold_limit = profile["mold_limit"]
    min_quality = profile["min_quality"]
    brix_limit = target_brix * profile["brix_multiplier"]
    ratio_limit = target_ratio * profile["ratio_multiplier"]
    
    marketable = np.zeros_like(t, dtype=bool)
    
    for i in range(len(t)):
        if (brix[i] >= brix_limit and 
            maturation_index[i] >= ratio_limit and
            quality_base[i] >= min_quality and 
            firmness[i] >= firmness_limit and 
            mold[i] <= mold_limit):
            
            marketable[i] = True
            
    mold_penalty = mold_max_penalty * mold
    quality = quality_base * (1.0 - mold_penalty)
    
    quality[~marketable] = 0

    remaining_SL = np.where(mold_penalty > 0, 0, remaining_SL)

    arrays_dict = {"quality": quality.tolist(), "quality_base": quality_base.tolist(), "firmness": firmness.tolist(), "brix": brix.tolist(), "acidity": acidity.tolist(), "ratio": maturation_index.tolist(), "t": t.tolist()}
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
    firmness: Optional[float] = None
    acidity: Optional[float] = None

class LotIdentification(BaseModel):
    lot_id: int
    batch_id: str
    culture_name: str
    fruit_type: str
    producer: str
    current_owner: str
    current_owner_type: Optional[str] = None
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
    if (raw_key in PRESETS_SOFIA or raw_key in PRESETS_ACADEMIC):
        fruit_key = raw_key
    elif (fruit_type in PRESETS_SOFIA or fruit_type in PRESETS_ACADEMIC):
        fruit_key = fruit_type
    elif (culture_name in PRESETS_SOFIA or culture_name in PRESETS_ACADEMIC):
        fruit_key = culture_name
    else:
        fruit_key = raw_key

    if (fruit_key not in PRESETS_SOFIA and fruit_key not in PRESETS_ACADEMIC):
        return JSONResponse(
            status_code=400,
            content={"detail": f"Unknown fruit key derived from fruit_type and culture_name: {fruit_key}. Valid keys: {list(set(list(PRESETS_SOFIA.keys()) + list(PRESETS_ACADEMIC.keys())))}"}
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
        
        # Orchestrator: academic model requires BOTH ethylene data AND academic preset
        has_ethylene = any(e is not None for e in E_ppm)
        has_academic_preset = fruit_key in PRESETS_ACADEMIC
        use_academic = has_ethylene and has_academic_preset

        if use_academic:
            E_ppm_filled = [e if e is not None else 0.0 for e in E_ppm]
            preset = PRESETS_ACADEMIC[fruit_key]
        else:
            preset = PRESETS_SOFIA[fruit_key]

        b0 = request.lot_identification.initial_metrics.soluble_solids_brix
        if b0 is None:
            b0 = preset["brix_0_default"]
        
        f0 = request.lot_identification.initial_metrics.firmness
        if f0 is None:
            f0 = preset["firmness_0_default"]
            
        a0 = request.lot_identification.initial_metrics.acidity
        if a0 is None:
            a0 = preset.get("acidity_0_default", 0.5)

        if use_academic:
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
                packaging_methods=packaging_methods,
                current_owner_type=request.lot_identification.current_owner_type
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
    acidity_0_default: Optional[float] = None
    acidity_min: Optional[float] = None
    k_acidity_ref: Optional[float] = None
    Ea_acidity_J: Optional[float] = None
    qual_acidity_target: Optional[float] = None
    SL_ref: Optional[float] = None
    E0_int: Optional[float] = None
    Eref_prod: Optional[float] = None
    E_t0: Optional[float] = None
    E_g: Optional[float] = None
    E_auto: Optional[float] = None
    E_decay: Optional[float] = None
    Ea_E_J: Optional[float] = None
    E_ext_shift: Optional[float] = None
    alpha_E: Optional[float] = None

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
    pdump = request.preset.model_dump(exclude_none=True)
    if "E0_int" in pdump:
        PRESETS_ACADEMIC[request.fruit_key] = pdump
    else:
        PRESETS_SOFIA[request.fruit_key] = pdump
    MOLD_BY_FRUIT[request.fruit_key] = request.mold_preset.model_dump()
    return {"message": "Preset added successfully", "fruit_key": request.fruit_key}

@app.get("/presets")
def get_presets():
    return {"fruits": list(set(list(PRESETS_SOFIA.keys()) + list(PRESETS_ACADEMIC.keys())))}

if __name__ == "__main__":
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8181)

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    try:
        server_thread.join()
    except KeyboardInterrupt:
        pass