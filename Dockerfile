# Usamos la imagen oficial de Python 3.12 como base
FROM python:3.12-slim

# Instalar FFmpeg
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos el código de la aplicación al contenedor
COPY . /app

# Instalamos las dependencias necesarias para el proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Exponemos el puerto que la aplicación usará (por defecto 8080 para GCP)
EXPOSE 8080

# Comando para iniciar la aplicación Flask
CMD ["python", "main.py"]
