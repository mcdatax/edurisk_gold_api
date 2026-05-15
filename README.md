# 🎓 EduRisk API

<div align="center">

**REST API para predicción de riesgo de abandono universitario**  
*Flask · Gunicorn · Nginx · Docker · AWS EC2*

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Gunicorn](https://img.shields.io/badge/Gunicorn-25.3-499848?style=for-the-badge&logo=gunicorn&logoColor=white)](https://gunicorn.org)
[![Nginx](https://img.shields.io/badge/Nginx-alpine-009639?style=for-the-badge&logo=nginx&logoColor=white)](https://nginx.org)
[![Docker](https://img.shields.io/badge/Docker-29.1-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![AWS EC2](https://img.shields.io/badge/AWS-EC2-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com/ec2)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)

**🟢 API en producción: `http://16.170.110.117/health`**

</div>

---

## 📋 Tabla de contenidos

- [El proyecto](#-el-proyecto)
- [Arquitectura](#-arquitectura)
- [Endpoints](#-endpoints-de-la-api)
- [Ejecución en local](#-ejecución-en-local)
- [Despliegue con Docker](#-despliegue-con-docker)
- [Ejemplos de peticiones](#-ejemplos-de-peticiones)
- [Estructura](#️-estructura-del-proyecto)
- [Stack técnico](#-stack-técnico)
- [Equipo](#-equipo)

---

## 🎯 El proyecto

**EduRisk API** es la productivización del proyecto [EduRisk](https://github.com/mcdatax/edurisk) — sistema de predicción temprana de abandono universitario.

El modelo predice el riesgo **el día de la matrícula**, con solo datos administrativos disponibles en ese momento.

| Métrica | Valor |
|---|---|
| **Recall Dropout** | **0.6479** ← métrica principal |
| F1-weighted | 0.5973 |
| ROC-AUC macro | 0.7558 |
| Algoritmo | RandomForestClassifier |

---

## 🏗️ Arquitectura

```
Internet
    │
    ▼
┌─────────────────────┐
│   Nginx (puerto 80) │  ← Reverse proxy + Rate limiting (10r/m)
└────────┬────────────┘
         │ proxy_pass interno
         ▼
┌─────────────────────┐
│ Gunicorn (p. 5000)  │  ← WSGI producción · 2 workers
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│    Flask App        │  ← Rutas + validación + logging
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ RandomForest        │  ← Pipeline sklearn + DataProcessor
└─────────────────────┘
```

```
Mac ──docker buildx──▶ DockerHub (mcdataxdev)
                              │
                         docker pull
                              ▼
                    AWS EC2 t3.medium · Ubuntu 24.04
                    ┌──────────────────────────┐
                    │ edurisk-nginx  → :80 pub  │
                    │ edurisk-api   → :5000 int │
                    │ red: edurisk-net          │
                    └──────────────────────────┘
```

---

## 🔌 Endpoints de la API

**Base URL:** `http://16.170.110.117`

### `GET /health`
```bash
curl http://16.170.110.117/health
```
```json
{
  "model": "EduRisk RandomForest",
  "status": "ok",
  "timestamp": "2026-05-15T14:56:37.677012+00:00",
  "version": "1.0.0"
}
```

---

### `GET /student/<student_id>`
```bash
curl http://16.170.110.117/student/42
```
```json
{
  "student_id": 42,
  "age": 21,
  "gender": 1,
  "scholarship": 0,
  "tuition": 1
}
```

---

### `POST /predict`
```bash
curl -X POST http://16.170.110.117/predict \
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
```
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
| `prediction` | `Dropout` · `Enrolled` · `Graduate` |
| `probabilities` | Probabilidad por clase (suman 1.0) |
| `risk_level` | `Bajo` (<35%) · `Medio` (35-60%) · `Alto` (>60%) |

---

### `GET /predict`
Mismas features como query params:
```bash
curl "http://16.170.110.117/predict?age=20&tuition=1&debtor=0&..."
```

---

## 🚀 Ejecución en local

```bash
git clone https://github.com/mcdatax/edurisk-api.git
cd edurisk-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Añadir model/final_model.pkl (desde edurisk)
python run.py
```

API en `http://localhost:5000`

---

## 🐳 Despliegue con Docker

### Imágenes en DockerHub

```bash
docker pull mcdataxdev/edurisk-api:latest
docker pull mcdataxdev/edurisk-nginx:latest
```

### Levantar en producción

```bash
docker network create edurisk-net

docker run -d --name api --network edurisk-net \
  -e MODEL_PATH=model/final_model.pkl \
  -e FLASK_ENV=production \
  -e PORT=5000 \
  mcdataxdev/edurisk-api:latest

docker run -d --name nginx --network edurisk-net \
  -p 80:80 \
  mcdataxdev/edurisk-nginx:latest
```

### Reconstruir y publicar

```bash
# API
docker buildx build --platform linux/amd64 -t mcdataxdev/edurisk-api:latest --push .

# Nginx
docker buildx build --platform linux/amd64 \
  -f Dockerfile.nginx \
  -t mcdataxdev/edurisk-nginx:latest --push .
```

---

## 🗂️ Estructura del proyecto

```
edurisk-api/
├── app/
│   ├── __init__.py              ← create_app() · carga modelo al startup
│   ├── routes/
│   │   ├── health.py            ← GET /health
│   │   └── predict.py           ← POST /predict · GET /predict · GET /student/<id>
│   └── schemas/
│       └── predict.py           ← validación + mapeo de inputs
├── model/
│   └── final_model.pkl          ← no en git
├── nginx/
│   └── nginx.conf               ← reverse proxy + rate limiting
├── src/
│   ├── data_processing.py       ← DataProcessor + feature engineering
│   └── utils.py                 ← constantes + helpers
├── tests/
│   └── test_routes.py
├── Dockerfile                   ← python:3.11-slim + gunicorn
├── Dockerfile.nginx             ← nginx:alpine + nginx.conf
├── docker-compose.yml           ← desarrollo local
├── requirements.txt
└── run.py
```

---

## 🧱 Stack técnico

| Capa | Tecnología |
|---|---|
| Framework | Flask 3.1 |
| WSGI | Gunicorn 25.3 · 2 workers |
| Proxy | Nginx alpine · rate limit 10r/m |
| ML | scikit-learn 1.8 · RandomForest |
| Contenedores | Docker 29.1 |
| Registro | DockerHub mcdataxdev |
| Cloud | AWS EC2 t3.medium · Ubuntu 24.04 |

---

## 📄 Variables de entorno

| Variable | Default |
|---|---|
| `MODEL_PATH` | `model/final_model.pkl` |
| `FLASK_ENV` | `production` |
| `PORT` | `5000` |

---

## 👩‍💻 Equipo

**Manuel Correa** · Data Scientist & Data Engineer · Madrid  
🔗 [GitHub @mcdatax](https://github.com/mcdatax) · [DockerHub @mcdataxdev](https://hub.docker.com/u/mcdataxdev)

---

*Bootcamp Data Science · The Bridge · 2026 · Dataset UCI #697*