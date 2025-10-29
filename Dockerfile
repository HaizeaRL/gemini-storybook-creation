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

# Set the default command
CMD ["python", "src/main.py"]

