from flask import Blueprint, jsonify
from datetime import datetime, timezone

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "model": "EduRisk RandomForest",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })