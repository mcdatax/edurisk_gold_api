# Es la imagen de python más pequeña, prefabricada por el equipo de python
FROM python:3.11-slim 

# WORKDIR es el directorio de trabajo, en este caso el directorio de la aplicación
WORKDIR /app 

COPY requirements.txt . # Copia el archivo de requirements.txt a la imagen

# Instala las dependencias del archivo requirements.txt
# --no-cache-dir es un argumento para no cachear las dependencias instaladas en la 
# imagen para evitar errores de dependencias conflictivas al hacer el build de la imagen 
# y no tener que descargar las dependencias cada vez que se hace el build de la imagen
RUN pip install --no-cache-dir -r requirements.txt 

# Copia el contenido del directorio actual a la imagen
COPY . . 

# Exponemos el puerto 5000 para que la aplicación pueda ser accesible desde el exterior
EXPOSE 5000 

# Gunicorn es un servidor WSGI que se encarga de ejecutar la aplicación Flask
CMD [
    "gunicorn", # Comando para ejecutar gunicorn
    "--bind", # Argumento para especificar la dirección IP de escucha
    "0.0.0.0:5000", # Dirección de escucha (cualquier dirección IP)
    "--workers", # Argumento para especificar el número de workers
    "2", # Número de workers (2 workers es el mínimo recomendado)
    "run:app"] # Nombre del archivo de la aplicación (run.py)