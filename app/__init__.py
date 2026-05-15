import logging
import pickle
import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)

    model_path = os.getenv("MODEL_PATH", "model/final_model.pkl")
    try:
        with open(model_path, "rb") as f:
            app.config["MODEL"] = pickle.load(f)
        logger.info(f"Modelo cargado desde {model_path}")
    except Exception as e:
        logger.error(f"Error cargando modelo: {e}")
        raise

    from app.routes.health import health_bp
    from app.routes.predict import predict_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(predict_bp)

    return app