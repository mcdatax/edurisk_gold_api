# Mapeo a nombres cortos para la  API, nombres originales del dataset UCI
FIELD_MAP = {
    "marital":          "Marital Status",
    "app_mode":         "Application mode",
    "app_order":        "Application order",
    "course":           "Course",
    "attendance":       "Daytime/evening attendance",
    "prev_qual":        "Previous qualification",
    "prev_grade":       "Previous qualification (grade)",
    "nationality":      "Nacionality",
    "mother_qual":      "Mother's qualification",
    "father_qual":      "Father's qualification",
    "mother_occ":       "Mother's occupation",
    "father_occ":       "Father's occupation",
    "admission_grade":  "Admission grade",
    "displaced":        "Displaced",
    "special_needs":    "Educational special needs",
    "debtor":           "Debtor",
    "tuition":          "Tuition fees up to date",
    "gender":           "Gender",
    "scholarship":      "Scholarship holder",
    "age":              "Age at enrollment",
    "international":    "International",
    "unemployment":     "Unemployment rate",
    "inflation":        "Inflation rate",
    "gdp":              "GDP",
}

REQUIRED_FIELDS = list(FIELD_MAP.keys())


def validate_and_map(data: dict):
    """
    Valida los campos requeridos y mapea nombres cortos a nombres UCI, es decir, en el formato que acepta el modelo.
    Retorna (datos_mapeados, lista_de_errores).
    """
    errors = []

    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        errors.append(f"Campos faltantes: {missing}")
        return {}, errors

    mapped = {FIELD_MAP[k]: data[k] for k in REQUIRED_FIELDS}
    return mapped, []