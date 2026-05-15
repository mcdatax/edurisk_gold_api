# 🎓 EduRisk API

<div align="center">

**REST API para predicción de riesgo de abandono universitario**  
*Productivización del modelo EduRisk con Flask · MLflow · Docker · AWS EC2*

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![MLflow](https://img.shields.io/badge/MLflow-3.12-0194E2?style=for-the-badge&logo=mlflow&logoColor=white)](https://mlflow.org)
[![Docker](https://img.shields.io/badge/Docker-29.1-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![AWS EC2](https://img.shields.io/badge/AWS-EC2-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com/ec2)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)

</div>

---

## 📋 Tabla de contenidos

- [El proyecto](#-el-proyecto)
- [Arquitectura](#-arquitectura)
- [Endpoints de la API](#-endpoints-de-la-api)
- [Ejecución en local](#-ejecución-en-local)
- [Despliegue con Docker](#-despliegue-con-docker)
- [MLflow — tracking de experimentos](#-mlflow--tracking-de-experimentos)
- [Ejemplos de peticiones](#-ejemplos-de-peticiones)
- [Estructura del proyecto](#️-estructura-del-proyecto)
- [Stack técnico](#-stack-técnico)
- [Equipo](#-equipo)

---

## 🎯 El proyecto

**EduRisk API** es la productivización del proyecto de Machine Learning [EduRisk](https://github.com/mcdatax/edurisk) — un sistema de predicción temprana de abandono universitario.

El modelo predice el riesgo de abandono **el día de la matrícula**, con solo los datos administrativos disponibles en ese momento, dando tiempo real para que tutores intervengan antes de que sea tarde.

Esta API expone ese modelo como un servicio REST accesible públicamente, containerizado con Docker y desplegado en AWS EC2.

| Métrica del modelo | Valor |
|---|---|
| **Recall Dropout** | **0.6479** ← métrica principal |
| F1-weighted | 0.5973 |
| ROC-AUC macro | 0.7558 |
| Algoritmo | RandomForestClassifier |

> **¿Por qué Recall como métrica principal?** Un Falso Negativo (predecir "no abandona" cuando sí abandona) tiene coste alto: el tutor no interviene. Un Falso Positivo (intervenir innecesariamente) tiene coste bajo. Optimizamos Recall de la clase Dropout.

---

## 🏗️ Arquitectura

```
Cliente (Postman / curl / app web)
           │
           │  HTTP Request
           ▼
┌─────────────────────────────────┐
│         Flask API               │
│  ┌─────────────────────────┐   │
│  │   GET  /health          │   │
│  │   GET  /student/<id>    │   │
│  │   GET  /predict?params  │   │
│  │   POST /predict         │   │
│  └─────────────────────────┘   │
│           │                     │
│  ┌────────▼────────────────┐   │
│  │    Input Validation     │   │
│  │    (schemas/predict.py) │   │
│  └────────┬────────────────┘   │
│           │                     │
│  ┌────────▼────────────────┐   │
│  │    DataProcessor        │   │
│  │    Feature Engineering  │   │
│  │    (4 features nuevas)  │   │
│  └────────┬────────────────┘   │
│           │                     │
│  ┌────────▼────────────────┐   │
│  │   RandomForest Pipeline │   │
│  │   (sklearn + joblib)    │   │
│  └────────┬────────────────┘   │
│           │                     │
└───────────┼─────────────────────┘
            │
            ▼
     JSON Response
  { prediction, probabilities, risk_level }
```

```
Infraestructura:

Mac Local ──docker build──▶ DockerHub (mcdataxdev/edurisk-api)
                                    │
                               docker pull
                                    │
                                    ▼
                          AWS EC2 (t3.micro Ubuntu)
                          docker run -p 5000:5000
                                    │
                          http://<IP>:5000
```

---

## 🔌 Endpoints de la API

### `GET /health`
Comprueba el estado del servicio.

```
GET /health
```

**Respuesta:**
```json
{
  "model": "EduRisk RandomForest",
  "status": "ok",
  "timestamp": "2026-05-15T09:09:48.818854+00:00",
  "version": "1.0.0"
}
```

---

### `GET /student/<student_id>`
Consulta los datos de un estudiante por ID *(path param)*.

```
GET /student/42
```

**Respuesta:**
```json
{
  "student_id": 42,
  "age": 21,
  "gender": 1,
  "scholarship": 0,
  "tuition": 1,
  "debtor": 0,
  ...
}
```

---

### `GET /predict`
Predicción vía **query parameters** — útil para integraciones rápidas.

```
GET /predict?age=20&tuition=1&debtor=0&scholarship=0&admission_grade=127.3&...
```

---

### `POST /predict`
Predicción vía **JSON body** — endpoint principal de producción.

```
POST /predict
Content-Type: application/json
```

**Body:**
```json
{
  "marital": 1,
  "app_mode": 1,
  "app_order": 1,
  "course": 9254,
  "attendance": 1,
  "prev_qual": 1,
  "prev_grade": 122.0,
  "nationality": 1,
  "mother_qual": 19,
  "father_qual": 12,
  "mother_occ": 5,
  "father_occ": 9,
  "admission_grade": 127.3,
  "displaced": 0,
  "special_needs": 0,
  "debtor": 0,
  "tuition": 1,
  "gender": 1,
  "scholarship": 0,
  "age": 20,
  "international": 0,
  "unemployment": 10.8,
  "inflation": 1.4,
  "gdp": 1.74
}
```

**Respuesta:**
```json
{
  "prediction": "Enrolled",
  "probabilities": {
    "Dropout": 0.278,
    "Enrolled": 0.3894,
    "Graduate": 0.3326
  },
  "risk_level": "Bajo"
}
```

| Campo | Descripción |
|---|---|
| `prediction` | Clase predicha: `Dropout`, `Enrolled` o `Graduate` |
| `probabilities` | Probabilidad para cada clase (suman 1.0) |
| `risk_level` | `Bajo` (<35% dropout) · `Medio` (35-60%) · `Alto` (>60%) |

---

## 🚀 Ejecución en local

### Prerrequisitos
- Python 3.11+
- Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/mcdatax/edurisk-api.git
cd edurisk-api

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env           # editar si es necesario

# 5. Añadir el modelo (copiar desde edurisk o descargarlo)
# El modelo final_model.pkl debe estar en model/

# 6. Arrancar la API
python run.py
```

La API estará disponible en `http://localhost:5000`

---

## 🐳 Despliegue con Docker

### Local con Docker

```bash
# Construir imagen
docker build -t edurisk-api .

# Ejecutar contenedor
docker run -p 5000:5000 --env-file .env edurisk-api
```

### Con Docker Compose

```bash
docker-compose up
```

### Imagen pública en DockerHub

```bash
docker pull mcdataxdev/edurisk-api:latest
docker run -p 5000:5000 mcdataxdev/edurisk-api:latest
```

### Despliegue en AWS EC2

```bash
# En la instancia EC2 (Ubuntu + Docker instalado)
docker pull mcdataxdev/edurisk-api:latest
docker run -d -p 5000:5000 --restart=always --name edurisk-api mcdataxdev/edurisk-api:latest

# Verificar que está corriendo
docker ps

# Ver logs
docker logs edurisk-api
```

**URL pública:** `http://<IP_EC2>:5000`

---

## 📊 MLflow — tracking de experimentos

El proyecto incluye tracking con MLflow para registrar el modelo, sus parámetros y métricas.

```bash
# Registrar el modelo en MLflow
python -m mlflow_tracking.register_model

# Lanzar la UI de MLflow
mlflow ui --port 5001 --backend-store-uri ./mlruns
```

Abrir `http://localhost:5001` para ver el experimento `edurisk-productivizacion`.

**Métricas registradas:**

| Parámetro / Métrica | Valor |
|---|---|
| model_type | RandomForestClassifier |
| features | 28 |
| recall_dropout | 0.6479 |
| f1_weighted | 0.5973 |
| roc_auc_macro | 0.7558 |

---

## 📬 Ejemplos de peticiones

### curl

```bash
# Health check
curl http://localhost:5000/health

# Predicción POST
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "marital": 1, "app_mode": 1, "app_order": 1,
    "course": 9254, "attendance": 1, "prev_qual": 1,
    "prev_grade": 122.0, "nationality": 1,
    "mother_qual": 19, "father_qual": 12,
    "mother_occ": 5, "father_occ": 9,
    "admission_grade": 127.3, "displaced": 0,
    "special_needs": 0, "debtor": 0, "tuition": 1,
    "gender": 1, "scholarship": 0, "age": 20,
    "international": 0, "unemployment": 10.8,
    "inflation": 1.4, "gdp": 1.74
  }'

# Estudiante por ID
curl http://localhost:5000/student/42

# Predicción GET (query params)
curl "http://localhost:5000/predict?age=20&tuition=1&debtor=0&scholarship=0&admission_grade=127.3&marital=1&app_mode=1&app_order=1&course=9254&attendance=1&prev_qual=1&prev_grade=122.0&nationality=1&mother_qual=19&father_qual=12&mother_occ=5&father_occ=9&displaced=0&special_needs=0&gender=1&international=0&unemployment=10.8&inflation=1.4&gdp=1.74"
```

### Python

```python
import requests

url = "http://localhost:5000/predict"

student = {
    "marital": 1, "app_mode": 1, "app_order": 1,
    "course": 9254, "attendance": 1, "prev_qual": 1,
    "prev_grade": 122.0, "nationality": 1,
    "mother_qual": 19, "father_qual": 12,
    "mother_occ": 5, "father_occ": 9,
    "admission_grade": 127.3, "displaced": 0,
    "special_needs": 0, "debtor": 0, "tuition": 1,
    "gender": 1, "scholarship": 0, "age": 20,
    "international": 0, "unemployment": 10.8,
    "inflation": 1.4, "gdp": 1.74
}

response = requests.post(url, json=student)
print(response.json())
# {'prediction': 'Enrolled', 'probabilities': {...}, 'risk_level': 'Bajo'}
```

---

## 🗂️ Estructura del proyecto

```
edurisk-api/
│
├── app/
│   ├── __init__.py              ← Factory function create_app()
│   ├── routes/
│   │   ├── health.py            ← GET /health
│   │   └── predict.py           ← GET+POST /predict · GET /student/<id>
│   └── schemas/
│       └── predict.py           ← Validación y mapeo de inputs
│
├── mlflow_tracking/
│   └── register_model.py        ← Registra modelo en MLflow
│
├── model/
│   └── final_model.pkl          ← RandomForest serializado (no en git)
│
├── src/
│   ├── data_processing.py       ← DataProcessor: feature engineering
│   └── utils.py                 ← Constantes, mapeos, helpers
│
├── tests/
│   └── test_routes.py           ← Tests de los endpoints
│
├── .env                         ← Variables de entorno (no en git)
├── .gitignore
├── Dockerfile                   ← Imagen python:3.11-slim
├── docker-compose.yml           ← Desarrollo local
├── requirements.txt             ← Dependencias pinadas
└── run.py                       ← Entrypoint de la aplicación
```

---

## 🧱 Stack técnico

| Capa | Tecnología | Versión |
|---|---|---|
| API Framework | Flask | 3.0 |
| ML | scikit-learn | 1.4+ |
| Serialización | pickle | stdlib |
| Experiment tracking | MLflow | 3.12 |
| Containerización | Docker | 29.1 |
| Orquestación local | Docker Compose | v2 |
| Despliegue | AWS EC2 (t3.micro) | Ubuntu 24.04 |
| Registro de imágenes | DockerHub | mcdataxdev |
| Gestión de entorno | pip + venv | — |

---

## 📄 Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `MODEL_PATH` | Ruta al modelo serializado | `model/final_model.pkl` |
| `FLASK_ENV` | Entorno Flask | `development` |
| `PORT` | Puerto de la API | `5000` |

---

## 👩‍💻 Equipo

**Manuel Correa** · Data Scientist & Data Engineer  
📍 Madrid, España  
🔗 [GitHub @mcdatax](https://github.com/mcdatax) · [DockerHub @mcdataxdev](https://hub.docker.com/u/mcdataxdev)

---

## 🔗 Proyectos relacionados

- [EduRisk](https://github.com/mcdatax/edurisk) — Proyecto original de ML: EDA, entrenamiento, evaluación y app Streamlit
- *EduRisk FastAPI* — Fork con FastAPI + Pydantic (próximamente)

---

*Proyecto desarrollado durante el Bootcamp de Data Science en The Bridge (2026)*  
*Modelo basado en el dataset UCI ML Repository #697 — Realinho et al. (2022)*