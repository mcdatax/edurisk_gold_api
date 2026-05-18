# Imagen base oficial de Python en variante slim (~130 MB).
# Tag fijo (3.11) en vez de 'latest' garantiza builds reproducibles.
FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor.
WORKDIR /app

# Copia solo requirements.txt primero para aprovechar la caché de capas Docker:
# mientras no cambie este archivo, Docker reutiliza la capa del pip install
# y los builds tardan segundos en vez de minutos.
COPY requirements.txt .

# --no-cache-dir evita guardar la caché de pip dentro de la imagen → imagen más ligera.
RUN pip install --no-cache-dir -r requirements.txt

# Ahora el resto del código (esta capa sí cambia con cada commit).
COPY . .

# Usuario no-root: si la app se ve comprometida, el atacante no tiene root dentro del contenedor.
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Documenta el puerto interno. Nginx lo consumirá por red Docker, NO se expone al exterior.
EXPOSE 5000

# Gunicorn como servidor WSGI de producción.
# --workers 1 + --threads 4: en t3.small (2 GB RAM) un worker con sklearn cargado
#   ya consume ~500 MB. Varios workers provocan OOM y SSH letra-por-letra.
# --preload: el master carga la app y el modelo UNA vez antes de forkear workers.
#   Si en futuro subes a t3.medium con más workers, comparten memoria vía
#   copy-on-write en Linux (no duplica el modelo en RAM).
# --timeout 60: margen amplio para predicciones sklearn (en realidad son ms).
# --access-logfile -: logs de acceso a stdout para que 'docker logs' los muestre.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "60", "--preload", "--access-logfile", "-", "run:app"]
