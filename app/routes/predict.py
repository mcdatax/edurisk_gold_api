# 1. Librería estándar Python
import logging
import random

# 2. Librerías de terceros
import pandas as pd
from flask import Blueprint, jsonify, request, current_app

# 3. Módulos propios del proyecto
from app.schemas.predict import validate_and_map
from src.data_processing import DataProcessor
from src.utils import decode_target, get_risk_level, generate_random_student, detect_csv_type


logger = logging.getLogger(__name__)
predict_bp = Blueprint("predict", __name__)
processor = DataProcessor()


def _run_prediction(raw_data: dict):
    """Lógica central reutilizable por todas las opciones."""
    model = current_app.config["MODEL"]
    df = pd.DataFrame([raw_data])
    df_processed = processor.process(df)
    proba = model.predict_proba(df_processed)[0]
    prediction = int(proba.argmax())

    return {
        "prediction": decode_target(prediction),
        "probabilities": {
            "Dropout":  round(float(proba[0]), 4),
            "Enrolled": round(float(proba[1]), 4),
            "Graduate": round(float(proba[2]), 4),
        },
        "risk_level": get_risk_level(float(proba[0]))
    }


# POST /predict  (body JSON con nombres cortos)
@predict_bp.post("/predict")
def predict_post():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Body JSON requerido"}), 400

    mapped, errors = validate_and_map(data)
    if errors:
        return jsonify({"error": errors}), 422

    try:
        result = _run_prediction(mapped)
        logger.info(f"POST /predict ... {result['prediction']} (risk: {result['risk_level']})")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error en predicción: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500


# GET /predict  (query params)
@predict_bp.get("/predict")
def predict_get():
    try:
        data = {k: float(v) if '.' in v else int(v)
                for k, v in request.args.items()}
    except ValueError:
        return jsonify({"error": "Parámetros inválidos"}), 400

    mapped, errors = validate_and_map(data)
    if errors:
        return jsonify({"error": errors}), 422

    try:
        result = _run_prediction(mapped)
        logger.info(f"GET /predict ... {result['prediction']}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error en predicción: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

# POST /predict/batch
@predict_bp.post("/predict/batch")
def predict_batch():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "CSV requerido"}), 400

    df = pd.read_csv(file)

    
    csv_type, missing = detect_csv_type(df)

    if csv_type == "invalid":
        return jsonify({"error": f"Columnas faltantes: {missing}"}), 422

    results = []

    if csv_type == "raw":
        # CSV con nombres UCI completos, se debe procesar directamente.
        df_processed = processor.process(df)
        model = current_app.config["MODEL"]
        probas = model.predict_proba(df_processed)
        
        for i, proba in enumerate(probas):
            prediction = int(proba.argmax())
            results.append({
                "student_index": i,
                "prediction": decode_target(prediction),
                "probabilities": {
                    "Dropout":  round(float(proba[0]), 4),
                    "Enrolled": round(float(proba[1]), 4),
                    "Graduate": round(float(proba[2]), 4),
                },
                "risk_level": get_risk_level(float(proba[0]))
            })
    else:
        # CSV con nombres cortos
        for _, row in df.iterrows():
            mapped, errors = validate_and_map(row.to_dict()) # Si vienen los nombres cortos en las columnas, pasamos a estándar UCI porque el modelo fue entrenado con esos nombres
            if errors:
                results.append({"error": errors})
                continue
            results.append(_run_prediction(mapped))

    return jsonify({
        "total": len(results),
        "predictions": results
    })

# GET /student/<student_id>  (devuelve estudiante random)
@predict_bp.get("/student/<int:student_id>")
def get_student(student_id: int):
    """
    Simula consulta de estudiante por ID.
    En producción real: consultaría una DB.
    """

    random.seed(student_id)
    student = generate_random_student()
    student["student_id"] = student_id
    return jsonify(student)