# 🎓 EduRisk API

<div align="center">

**REST API para predicción de riesgo de abandono universitario**  
*Productivización de un modelo ML — del notebook a producción real*

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Gunicorn](https://img.shields.io/badge/Gunicorn-25.3-499848?style=for-the-badge&logo=gunicorn&logoColor=white)](https://gunicorn.org)
[![Nginx](https://img.shields.io/badge/Nginx-alpine-009639?style=for-the-badge&logo=nginx&logoColor=white)](https://nginx.org)
[![Docker](https://img.shields.io/badge/Docker-29.1-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![AWS EC2](https://img.shields.io/badge/AWS-EC2-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com/ec2)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)

</div>

---

## 📋 Tabla de contenidos

- [El proyecto](#-el-proyecto)
- [Arquitectura](#-arquitectura)
- [Endpoints](#-endpoints-de-la-api)
- [Batch predictions](#-batch-predictions)
- [Ejecución en local](#-ejecución-en-local)
- [Despliegue con Docker](#-despliegue-con-docker)
- [Actualizar la API](#-actualizar-la-api-tras-cambios)
- [Estructura del proyecto](#️-estructura-del-proyecto)
- [Stack técnico](#-stack-técnico)
- [Equipo](#-equipo)

---

## 🎯 El proyecto

**EduRisk API** es la productivización de [EduRisk](https://github.com/mcdatax/edurisk) — un sistema de Machine Learning para predicción temprana de abandono universitario.

El modelo predice el riesgo de abandono **el día de la matrícula**, usando únicamente datos administrativos disponibles en ese momento — sin notas de semestres, sin información académica posterior. Esto permite que tutores intervengan antes de que sea tarde.

**Clases de predicción:** `Dropout` · `Enrolled` · `Graduate`

| Métrica | Valor | Justificación |
|---|---|---|
| **Recall Dropout** | **0.6479** | Métrica principal — un falso negativo (no detectar un abandono) tiene mayor coste que una intervención innecesaria |
| F1-weighted | 0.5973 | Equilibrio entre precisión y recall en las 3 clases |
| ROC-AUC macro | 0.7558 | Capacidad discriminativa global del modelo |
| Algoritmo | RandomForestClassifier | Mejor balance rendimiento/interpretabilidad en validación |

> **Modelo base:** [EduRisk](https://github.com/mcdatax/edurisk) — dataset UCI ML Repository #697 (Realinho et al., 2022)

---

## 🏗️ Arquitectura

El sistema sigue una arquitectura de producción en capas con separación de responsabilidades:

```
Internet
    │
    ▼
┌───────────────────────────────┐
│  Nginx (puerto 80 — público)  │  ← Reverse proxy
│  Rate limiting: 10 req/min    │     Solo puerto expuesto al mundo
└──────────────┬────────────────┘
               │ proxy_pass interno — puerto 5000 nunca expuesto
               ▼
┌───────────────────────────────┐
│  Gunicorn (puerto 5000)       │  ← Servidor WSGI de producción
│  2 workers síncronos          │     Reemplaza el servidor de desarrollo de Flask
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│  Flask App                    │  ← Lógica de negocio
│  Blueprints · Schemas         │     Arquitectura en capas (rutas / validación / negocio)
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│  DataProcessor + Pipeline     │  ← Feature engineering + modelo
│  RandomForestClassifier       │     sklearn Pipeline con ColumnTransformer
└───────────────────────────────┘
```

**Infraestructura:**

```
Mac local
  └── docker buildx ──▶ DockerHub (mcdataxdev)
                               │
                          docker pull
                               ▼
                     AWS EC2 t3.medium · Ubuntu 24.04 LTS
                     ┌─────────────────────────────────┐
                     │  edurisk-nginx  → :80  (público) │
                     │  edurisk-api   → :5000 (interno) │
                     │  red Docker: edurisk-net          │
                     │  auto-restart: systemd service    │
                     └─────────────────────────────────┘
```

**Por qué dos contenedores:**
- `edurisk-api` — Python + Flask + Gunicorn + modelo ML (~500 MB)
- `edurisk-nginx` — nginx:alpine + configuración (~8 MB)

Separar responsabilidades permite actualizar la API sin tocar Nginx y viceversa.

---

## 🔌 Endpoints de la API

| Método | Ruta | Tipo de parámetro | Descripción |
|---|---|---|---|
| GET | `/health` | — | Estado del servicio |
| GET | `/student/<id>` | Path param | Datos de un estudiante por ID |
| GET | `/predict` | Query params | Predicción rápida via URL |
| POST | `/predict` | JSON body | Predicción completa — endpoint principal |
| POST | `/predict/batch` | Form-data (CSV) | Predicción masiva — miles de estudiantes |

---

### `GET /health`

Comprueba que el servicio está activo y el modelo cargado.

```bash
curl http://<IP>/health
```

```json
{
  "model": "EduRisk RandomForest",
  "status": "ok",
  "timestamp": "2026-05-19T10:00:00.000000+00:00",
  "version": "1.0.0"
}
```

---

### `GET /student/<student_id>`

Devuelve datos de un estudiante simulado por ID (path param). En producción real consultaría una base de datos.

```bash
curl http://<IP>/student/42
```

```json
{
  "student_id": 42,
  "age": 21,
  "gender": 1,
  "scholarship": 0,
  "tuition": 1,
  "debtor": 0,
  "course": 9254,
  "admission_grade": 127.3
}
```

---

### `POST /predict`

Endpoint principal. Acepta los datos de un estudiante en JSON y devuelve la predicción con probabilidades y nivel de riesgo.

```bash
curl -X POST http://<IP>/predict \
  -H "Content-Type: application/json" \
  -d '{
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
| `prediction` | Clase predicha: `Dropout`, `Enrolled` o `Graduate` |
| `probabilities` | Probabilidad para cada clase (suman 1.0) |
| `risk_level` | `Bajo` (P(Dropout) < 35%) · `Medio` (35-60%) · `Alto` (> 60%) |

---

### `GET /predict`

Predicción vía query params — útil para pruebas rápidas desde el navegador.

```bash
curl "http://<IP>/predict?marital=1&app_mode=1&app_order=1&course=9254&attendance=1&prev_qual=1&prev_grade=122.0&nationality=1&mother_qual=19&father_qual=12&mother_occ=5&father_occ=9&admission_grade=127.3&displaced=0&special_needs=0&debtor=0&tuition=1&gender=1&scholarship=0&age=20&international=0&unemployment=10.8&inflation=1.4&gdp=1.74"
```

---

## 📦 Batch predictions

El endpoint `/predict/batch` acepta un CSV con cualquier número de estudiantes y devuelve todas las predicciones.

**Rendimiento:** 8.000 predicciones en ~1.45 segundos gracias a vectorización — `predict_proba()` recibe el DataFrame completo y numpy lo procesa en C compilado.

**Formatos de CSV aceptados:**
- Columnas UCI completas (`Marital Status`, `Age at enrollment`...)
- Columnas cortas de la API (`marital`, `age`...)

El endpoint detecta el formato automáticamente con `detect_csv_type()`.

**En Postman:**
- Method: `POST`
- URL: `http://<IP>/predict/batch`
- Body: `form-data` → key `file` (tipo `File`) → selecciona el CSV

**Respuesta:**

```json
{
  "total": 8000,
  "predictions": [
    {
      "student_index": 0,
      "prediction": "Dropout",
      "probabilities": {"Dropout": 0.5852, "Enrolled": 0.1993, "Graduate": 0.2155},
      "risk_level": "Medio"
    },
    ...
  ]
}
```

---

## 🚀 Ejecución en local

```bash
# Clonar el repositorio
git clone https://github.com/mcdatax/edurisk-api.git
cd edurisk-api

# Crear entorno virtual e instalar dependencias
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copiar el modelo desde el proyecto EduRisk
cp ../edurisk/models/final_model.pkl model/

# Configurar variables de entorno
cp .env.example .env

# Arrancar la API en modo desarrollo
python run.py
```

API disponible en `http://localhost:5000`

---

## 🐳 Despliegue con Docker

### Imágenes públicas en DockerHub

```bash
docker pull mcdataxdev/edurisk-api:latest
docker pull mcdataxdev/edurisk-nginx:latest
```

### Levantar en producción (recomendado — docker-compose)

```bash
# 1. Crear carpeta y entrar
mkdir ~/edurisk && cd ~/edurisk

# 2. Crear docker-compose.yml y .env (ver DEPLOY.md para el contenido completo)

# 3. Levantar
docker-compose up -d

# 4. Verificar
docker ps
curl http://localhost/health
```

### Levantar manualmente (alternativa)

```bash
docker network create edurisk-net

docker run -d --name api --network edurisk-net --restart=always \
  -e MODEL_PATH=model/final_model.pkl \
  -e FLASK_ENV=production \
  mcdataxdev/edurisk-api:latest

docker run -d --name nginx --network edurisk-net --restart=always \
  -p 80:80 \
  mcdataxdev/edurisk-nginx:latest
```

### Reconstruir imágenes

```bash
# API
docker buildx build --platform linux/amd64 -t mcdataxdev/edurisk-api:latest --push .

# Nginx (solo si cambiaste nginx.conf)
docker buildx build --platform linux/amd64 -f Dockerfile.nginx -t mcdataxdev/edurisk-nginx:latest --push .
```

> 📖 Para el manual completo de despliegue paso a paso, ver [DEPLOY.md](DEPLOY.md)

---

## 🔄 Actualizar la API tras cambios

El flujo siempre es Mac → DockerHub → EC2. Nunca se toca el código directamente en el servidor.

```bash
# 1. Guardar cambios en GitHub
git add .
git commit -m "feat: descripción del cambio"
git push

# 2. Rebuild y push de la nueva imagen
docker buildx build --platform linux/amd64 -t mcdataxdev/edurisk-api:latest --push .

# 3. En EC2 — descargar y reiniciar
cd ~/edurisk
docker-compose pull
docker-compose up -d
```

---

## 🗂️ Estructura del proyecto

```
edurisk-api/
│
├── app/
│   ├── __init__.py          ← create_app() — carga modelo al startup, configura logging
│   ├── routes/
│   │   ├── health.py        ← GET /health
│   │   └── predict.py       ← POST /predict · GET /predict · GET /student/<id> · POST /predict/batch
│   └── schemas/
│       └── predict.py       ← validación de inputs + mapeo nombres cortos → UCI
│
├── model/
│   └── final_model.pkl      ← Pipeline sklearn serializado (no en git)
│
├── nginx/
│   └── nginx.conf           ← reverse proxy + rate limiting (10 req/min por IP)
│
├── src/
│   ├── data_processing.py   ← DataProcessor: feature engineering (4 columnas engineered)
│   └── utils.py             ← constantes, mapeos, helpers, detect_csv_type
│
├── tests/
│   └── test_routes.py
│
├── docs/
│   └── deploy_manual.html   ← manual de despliegue interactivo
│
├── .env.example             ← plantilla de variables de entorno
├── .gitignore
├── Dockerfile               ← python:3.11-slim + gunicorn
├── Dockerfile.nginx         ← nginx:alpine + nginx.conf
├── docker-compose.yml       ← orquestación con healthcheck y límites de RAM
├── DEPLOY.md                ← manual completo de despliegue paso a paso
├── requirements.txt         ← dependencias directas con versiones pinadas
└── run.py                   ← entrypoint de la aplicación
```

---

## 🧱 Stack técnico

| Capa | Tecnología | Por qué |
|---|---|---|
| Framework | Flask 3.1 | Estándar en proyectos ML de producción |
| WSGI | Gunicorn 25.3 · 2 workers | Servidor de producción — reemplaza el dev server de Flask |
| Reverse proxy | Nginx alpine | Rate limiting, única IP pública, separa responsabilidades |
| ML | scikit-learn 1.8 · RandomForest | Mejor rendimiento en validación sobre datos de matrícula |
| Serialización | pickle (sklearn pipeline) | Preserva el ColumnTransformer y sus parámetros aprendidos |
| Contenedores | Docker 29.1 | Reproducible en cualquier servidor — zero dependency hell |
| Orquestación | docker-compose + systemd | Healthcheck, límites RAM, arranque automático tras reboot |
| Registro | DockerHub mcdataxdev | Imágenes públicas, despliegue sin clonar el repo |
| Cloud | AWS EC2 t3.medium · Ubuntu 24.04 | 2 vCPU + 4 GB RAM — suficiente para API + Nginx |

---

## 📄 Variables de entorno

Copia `.env.example` a `.env` y ajusta los valores:

| Variable | Default | Descripción |
|---|---|---|
| `MODEL_PATH` | `model/final_model.pkl` | Ruta al pipeline sklearn serializado |
| `FLASK_ENV` | `production` | Modo de Flask (`development` activa debug) |
| `PORT` | `5000` | Puerto interno de Gunicorn |

---

## 🔍 Decisiones técnicas destacadas

**Separación entrenamiento / producción:** el modelo se entrena en [EduRisk](https://github.com/mcdatax/edurisk) y se serializa. Esta API solo predice — nunca entrena.

**DataProcessor externo:** el pipeline sklearn incluye ColumnTransformer + RandomForest, pero el feature engineering (DataProcessor) se llama externamente antes de cada predicción. Una mejora futura sería envolver ese paso en un `FunctionTransformer` dentro del pipeline para hacerlo completamente autosuficiente.

**Batch vectorizado:** `predict_proba()` recibe el DataFrame completo en una sola llamada. numpy procesa todas las filas en C compilado — 8.000 predicciones en ~1.45 segundos. Un bucle fila a fila sería ~100x más lento.

**Rate limiting en Nginx:** 10 peticiones/minuto por IP con burst de 20. Protege el modelo de abuso sin necesidad de autenticación para un servicio de demo.

---

## 👩‍💻 Equipo

**Manuel Correa** · Data Scientist & Data Engineer · Madrid  
🔗 [GitHub @mcdatax](https://github.com/mcdatax) · [DockerHub @mcdataxdev](https://hub.docker.com/u/mcdataxdev)

---

*Bootcamp Data Science · The Bridge · Madrid 2026*  
*Modelo base: UCI ML Repository #697 — Realinho et al. (2022)*

---

## ⚡ Despliegue automático con User Data

La forma más rápida de desplegar — sin conectarte por SSH. Al crear la instancia EC2, pega el script en **Advanced Details → User Data** y en ~4 minutos la API estará disponible.

> **Qué es User Data:** AWS ejecuta este script como root una sola vez al arrancar la instancia por primera vez. Instala Docker, descarga las imágenes y configura el arranque automático — todo sin intervención manual. Es el primer paso hacia Infrastructure as Code.

### Cómo usarlo

**1.** En AWS Console → EC2 → Launch instance, configura la instancia normalmente (Ubuntu 24.04, t3.medium, puertos 22 y 80).

**2.** Antes de lanzar, despliega **Advanced Details** al final de la página y pega el script en el campo **User data**.

**3.** Lanza la instancia. Espera 3-4 minutos y prueba:

```bash
curl http://<IP_PUBLICA>/health
```

**4.** Si algo falla, conéctate por SSH y revisa el log:

```bash
cat /var/log/edurisk-setup.log
```

### Script

```bash
#!/bin/bash
# EduRisk API, User Data Script ==MCDATAX==
# Ubuntu 24.04 LTS · Docker + docker-compose + systemd
# Se ejecuta como root una sola vez al lanzar la instancia

set -e  # Para si cualquier comando falla
exec > /var/log/edurisk-setup.log 2>&1  # Guarda output para debugging

echo "=== Iniciando setup EduRisk API ==MCDATAX==="

# 1. Actualizar sistema
apt-get update -y
apt-get upgrade -y

# 2. Instalar Docker
apt-get install -y docker.io
systemctl enable --now docker

# Espera a que Docker esté listo
until docker info >/dev/null 2>&1; do
  echo "Esperando Docker..."
  sleep 2
done

# Añadir usuario ubuntu al grupo docker
usermod -aG docker ubuntu

# 3. Instalar docker-compose
curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 4. Crear carpeta del proyecto
mkdir -p /home/ubuntu/edurisk
cd /home/ubuntu/edurisk

# 5. Crear docker-compose.yml
cat > docker-compose.yml << 'EOF'
services:
  api:
    image: mcdataxdev/edurisk-api:latest
    expose:
      - "5000"
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://localhost:5000/health').status==200 else sys.exit(1)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    mem_limit: 1200m
    mem_reservation: 800m

  nginx:
    image: mcdataxdev/edurisk-nginx:latest
    ports:
      - "80:80"
    restart: unless-stopped
    depends_on:
      api:
        condition: service_healthy
    mem_limit: 128m
EOF

# 6. Crear .env
cat > .env << 'EOF'
MODEL_PATH=model/final_model.pkl
FLASK_ENV=production
PORT=5000
EOF

# 7. Ajustar permisos
chown -R ubuntu:ubuntu /home/ubuntu/edurisk

# 8. Crear servicio systemd para arranque automático tras reboot
cat > /etc/systemd/system/edurisk.service << 'EOF'
[Unit]
Description=EduRisk API
After=docker.service
Requires=docker.service

[Service]
WorkingDirectory=/home/ubuntu/edurisk
ExecStart=/usr/local/bin/docker-compose up
ExecStop=/usr/local/bin/docker-compose down
Restart=always
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

# 9. Habilitar y arrancar el servicio
systemctl daemon-reload
systemctl enable edurisk
systemctl start edurisk

echo "=== Setup completado ==MCDATAX== ==="
```