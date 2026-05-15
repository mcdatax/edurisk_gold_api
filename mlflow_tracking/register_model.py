"""
Registra retroactivamente el modelo EduRisk en MLflow.
Ejecutar UNA VEZ: python -m mlflow_tracking.register_model
"""
import pickle
import mlflow
import mlflow.sklearn

mlflow.set_tracking_uri("./mlruns")
mlflow.set_experiment("edurisk-productivizacion")

MODEL_PATH = "model/final_model.pkl"

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

with mlflow.start_run(run_name="RandomForest-final-v1"):
    mlflow.log_param("model_type", "RandomForestClassifier")
    mlflow.log_param("features", 28)
    mlflow.log_metric("recall_dropout", 0.6479)
    mlflow.log_metric("f1_weighted",    0.5973)
    mlflow.log_metric("roc_auc_macro",  0.7558)
    mlflow.sklearn.log_model(model, artifact_path="model")
    print("✅ Modelo registrado en MLflow")