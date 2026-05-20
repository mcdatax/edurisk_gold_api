# CLAUDE.md — edurisk-api

Contexto persistente del proyecto para minimizar re-explicaciones entre conversaciones.

## Qué es

Productivización del modelo de **EduRisk** (predicción de abandono universitario, RandomForest multiclase: Dropout / Enrolled / Graduate). Este repo NO entrena — solo sirve el modelo ya entrenado vía API REST.

- **Repo dev (entrena)**: https://github.com/mcdatax/edurisk
- **Repo prod (sirve)**: https://github.com/mcdatax/edurisk-api ← este
- **DockerHub**: `mcdataxdev/edurisk-api`, `mcdataxdev/edurisk-nginx`
- **Despliegue**: AWS EC2 (Ubuntu 24.04, t3.small/medium)

## Enunciado del bootcamp

API Flask + modelo ML + despliegue público. Mínimo 4 rutas:
- `GET /health` — estado
- Ruta con **path param**
- Ruta con **query param**
- Ruta con **JSON body**

Manejo de errores básico, modelo cargado al inicio, URL pública, repo + requirements.txt + ejemplos curl.

## Arquitectura productiva

```
Internet → Nginx (80) → Gunicorn (5000, interno) → Flask → RandomForest
```

- **Nginx**: reverse proxy + rate limiting (10 r/m, burst 20). Único puerto expuesto al mundo.
- **Gunicorn**: WSGI server, 1 worker + 4 threads + `--preload` (decisión por t3.small de 2 GB RAM).
- **Flask**: lógica de negocio, blueprints `health` y `predict`.
- **Modelo**: `model/final_model.pkl` (Pipeline sklearn con ColumnTransformer dentro).

Los dos contenedores se comunican por red Docker interna `edurisk-net`. Puerto 5000 NUNCA público.

## Rutas

| Método | Ruta              | Tipo param      |
|--------|-------------------|-----------------|
| GET    | `/health`         | —               |
| GET    | `/student/<id>`   | path            |
| GET    | `/predict?...`    | query           |
| POST   | `/predict`        | JSON body       |

Schemas: `app/schemas/predict.py` mapea nombres cortos (API) → nombres UCI del dataset.

## Stack y decisiones (alineadas mercado ES)

| Capa             | Elección             | Razón                                              |
|------------------|----------------------|----------------------------------------------------|
| Framework API    | Flask                | Obligatorio por bootcamp (FastAPI sería senior)    |
| Gestor deps      | pip + venv           | requirements.txt obligatorio                       |
| WSGI server      | Gunicorn             | Estándar prod, no `flask run`                      |
| Reverse proxy    | Nginx                | Patrón estándar empresa                            |
| Containerización | Docker + Compose     | Reproducibilidad                                   |
| Registro img.    | DockerHub público    | Para portfolio (en empresa: ECR/Artifact Registry) |
| Cloud            | AWS EC2              | Ya tiene experiencia                               |
| Serializ. modelo | pickle (heredado)    | **Deuda técnica** — debería ser joblib o skops     |

## Errores junior detectados (pendientes de fix)

1. **`Dockerfile`** tiene comentario inline en `COPY requirements.txt . # ...` — Docker no admite comentarios inline.
2. **`Dockerfile` CMD roto** — formato exec array con comentarios entre líneas (JSON con `#` es inválido). Cae a shell form → no recibe SIGTERM correctamente.
3. **`Dockerfile.nginx`** tiene comentario inline (`FROM nginx:alpine # ...`).
4. **Falta usuario no-root** en Dockerfile (corre como root).
5. **Falta `.dockerignore`** — `COPY . .` mete `.git`, `.venv`, `__pycache__`, etc.
6. **`docker-compose.yml`** sin `restart: unless-stopped` → no rearranca al reiniciar EC2.
7. **Healthcheck usa `curl`** pero `python:3.11-slim` no lo trae → siempre unhealthy. Alternativa Python: `python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"`.
8. **`depends_on` sin `condition: service_healthy`** → nginx arranca antes que API, da 502 al inicio.
9. **Gunicorn 2 workers** en t3.small (2 GB RAM) — sklearn carga ~500 MB por worker. Causa OOM y SSH letra-por-letra al reiniciar. Fix: 1 worker + threads + `--preload`.
10. **pickle vs joblib**: usar joblib (estándar sklearn) o skops (seguridad).

## RAM y t3.small — diagnóstico SSH lento al reiniciar

Síntoma: tras reboot, SSH va letra-por-letra. Causa: **swap thrashing por OOM**. Soluciones aplicadas/recomendadas:

```bash
# 1. Añadir swap (en EC2)
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 2. Limitar RAM en compose (mem_limit: 1200m en api, 128m en nginx)
# 3. Gunicorn: 1 worker + 4 threads + --preload
# 4. Si presupuesto: subir a t3.medium (4 GB)
```

## Despliegue desde cero (EC2 nueva)

```bash
# 1. SSH
ssh -i ~/.ssh/key_edurisk_api.pem ubuntu@<IP>

# 2. Docker
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io
sudo systemctl start docker && sudo systemctl enable docker
sudo usermod -aG docker ubuntu
# exit + reconectar

# 3. Red + pulls
docker network create edurisk-net
docker pull mcdataxdev/edurisk-api:latest
docker pull mcdataxdev/edurisk-nginx:latest

# 4. Contenedores
docker run -d --name api --network edurisk-net --restart=always \
  -e MODEL_PATH=model/final_model.pkl -e FLASK_ENV=production -e PORT=5000 \
  mcdataxdev/edurisk-api:latest

docker run -d --name nginx --network edurisk-net --restart=always \
  -p 80:80 mcdataxdev/edurisk-nginx:latest

# 5. Verificar
docker ps
curl http://localhost/health
```

Security Group EC2: puertos **22** (SSH) y **80** (HTTP).

## Build & push imágenes (desde Mac M-series → linux/amd64)

```bash
# API
docker buildx build --platform linux/amd64 \
  -t mcdataxdev/edurisk-api:latest --push .

# Nginx
docker buildx build --platform linux/amd64 \
  -f Dockerfile.nginx -t mcdataxdev/edurisk-nginx:latest --push .
```

Mac M-series construye ARM por defecto, EC2 es amd64 → siempre `--platform linux/amd64`.

## Convenciones del proyecto

- Lógica de negocio (`_run_prediction`) separada del framework → reutilizable si en futuro se migra a FastAPI.
- Blueprints por dominio (`health.py`, `predict.py`).
- Schemas con validación + mapeo nombres cortos → UCI en `schemas/predict.py`.
- Logging vía `logging.basicConfig` (formato estructurado).
- Errores: 400 (body mal), 422 (validación), 500 (interno).

## Lo que NO va aquí (por diseño)

- **MLflow**: eliminado a propósito. MLflow es para experimentación/entrenamiento → vive en EduRisk, no en producción.
- **Reentrenamiento**: flujo correcto = EduRisk entrena → exporta `.pkl` → edurisk-api lo sirve.
- **Base de datos**: no hay persistencia de predicciones (sería siguiente paso: model monitoring).

## Estado actual / próximos pasos

- ✅ API en producción funcionando (4 rutas)
- ✅ Dockerizado y publicado en DockerHub
- ✅ Desplegado en EC2 con Nginx + Gunicorn + rate limiting
- ⚠️ Pendientes errores junior listados arriba (Dockerfile mal formateado, falta .dockerignore, healthcheck con curl, sin restart policy)
- 🔮 Futuro: integrar segundo modelo (proyecto del compañero) → arquitectura multi-modelo
