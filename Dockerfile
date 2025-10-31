# Usar imagen base ligera de Python
FROM python:3.11

# Crear directorio de trabajo
WORKDIR /usr/local/app

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crea carpeta de logs en el contenedor
RUN mkdir -p /home/ec2-user/app/logs

# Exponemos puerto para poder llamar desde fuera
EXPOSE 5000

# Set the default command
CMD ["python", "src/main.py"]

