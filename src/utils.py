"""
utils.py
Constantes y funciones auxiliares compartidas por todo el proyecto.
"""

import numpy as np
import pandas as pd
from typing import Tuple, List



# Columnas post-matrícula — no disponibles en día 0
COLS_DROP = [
    'Curricular units 1st sem (credited)',
    'Curricular units 1st sem (enrolled)',
    'Curricular units 1st sem (evaluations)',
    'Curricular units 1st sem (approved)',
    'Curricular units 1st sem (grade)',
    'Curricular units 1st sem (without evaluations)',
    'Curricular units 2nd sem (credited)',
    'Curricular units 2nd sem (enrolled)',
    'Curricular units 2nd sem (evaluations)',
    'Curricular units 2nd sem (approved)',
    'Curricular units 2nd sem (grade)',
    'Curricular units 2nd sem (without evaluations)',
]

TARGET_COL    = 'Target'
TARGET_MAP    = {'Dropout': 0, 'Enrolled': 1, 'Graduate': 2}
TARGET_LABELS = {0: 'Dropout', 1: 'Enrolled', 2: 'Graduate'}
RISK_LABELS   = {0: 'Bajo', 1: 'Medio', 2: 'Alto'}

def decode_target(value: int) -> str:
    """Convierte target numérico a etiqueta legible."""
    return TARGET_LABELS.get(value, 'Desconocido')

def get_risk_level(proba_dropout: float) -> str:
    """Clasifica el nivel de riesgo según P(Dropout)."""
    if proba_dropout >= 0.60:
        return 'Alto'
    elif proba_dropout >= 0.35:
        return 'Medio'
    return 'Bajo'

COURSES = [33,171,8014,9003,9070,9085,9119,9130,9147,9238,9254,9500,9556,9670,9773,9853,9991]

def generate_random_student() -> dict:
    """
    Genera un estudiante aleatorio con valores plausibles
    basados en los rangos reales del dataset UCI #697.
    """
    return {
        'age':            int(np.random.choice([18,19,20,21,22,23,24,25,30,35,40])),
        'gender':         int(np.random.randint(0, 2)),
        'marital':        int(np.random.choice([1,2,3,4,5,6])),
        'displaced':      int(np.random.randint(0, 2)),
        'international':  int(np.random.randint(0, 2)),
        'special_needs':  int(np.random.randint(0, 2)),
        'scholarship':    int(np.random.randint(0, 2)),
        'debtor':         int(np.random.randint(0, 2)),
        'tuition':        int(np.random.randint(0, 2)),
        'admission_grade':round(float(np.random.uniform(95, 190)), 1),
        'prev_grade':     round(float(np.random.uniform(95, 190)), 1),
        'prev_qual':      int(np.random.choice(range(1, 44))),
        'course':         int(np.random.choice(COURSES)),
        'app_mode':       int(np.random.choice(range(1, 58))),
        'app_order':      int(np.random.randint(0, 10)),
        'attendance':     int(np.random.randint(0, 2)),
        'nationality':    int(np.random.choice(range(1, 110))),
        'mother_qual':    int(np.random.choice(range(1, 44))),
        'father_qual':    int(np.random.choice(range(1, 44))),
        'mother_occ':     int(np.random.choice(range(0, 195))),
        'father_occ':     int(np.random.choice(range(0, 195))),
        'unemployment':   round(float(np.random.uniform(7, 17)), 1),
        'inflation':      round(float(np.random.uniform(-1, 4)), 1),
        'gdp':            round(float(np.random.uniform(-5, 4)), 1),
    }

# Columnas mínimas obligatorias para que el sistema funcione
REQUIRED_COLS = [
    'Marital Status', 'Application mode', 'Application order',
    'Course', 'Daytime/evening attendance', 'Previous qualification',
    'Previous qualification (grade)', 'Nacionality',
    "Mother's qualification", "Father's qualification",
    "Mother's occupation", "Father's occupation",
    'Admission grade', 'Displaced', 'Educational special needs',
    'Debtor', 'Tuition fees up to date', 'Gender',
    'Scholarship holder', 'Age at enrollment', 'International',
    'Unemployment rate', 'Inflation rate', 'GDP'
]

# Columnas que indican que el CSV ya fue procesado
ENGINEERED_COLS = [
    'parents_qualification_avg', 'financial_risk',
    'age_group', 'is_first_choice'
]

def detect_csv_type(df: pd.DataFrame) -> Tuple[str, list]:

    """
    Detecta el tipo de CSV recibido.
    Retorna: 'raw' | 'processed' | 'invalid'
    """
    missing = [c for c in REQUIRED_COLS if c not in df.columns]

    if missing:
        return 'invalid', missing

    already_processed = all(c in df.columns for c in ENGINEERED_COLS)
    if already_processed:
        return 'processed', []

    return 'raw', []