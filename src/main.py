import pandas as pd
import os
from dotenv import load_dotenv
import google.generativeai as genai  # Para API key Gemini
import time
import shutil
from huggingface_hub import login
import re
import json
import boto3
import logging
from flask import Flask, request, jsonify

# -----------------------------
# Cargar variables de entorno
load_dotenv()

# carga Flask
app = Flask(__name__)

# Configura logging para pasar logs a CloudWatch
os.makedirs("/usr/local/app/logs", exist_ok=True)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("/usr/local/app/logs/app.log")
stream_handler = logging.StreamHandler()

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# Configurar S3 client
aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION", "eu-north-1")

s3 = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=aws_region
)

# Configurar API key de Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Falta GOOGLE_API_KEY en .env")
genai.configure(api_key=GOOGLE_API_KEY)

# Configurar HuggingFace API key
HF_API_KEY = os.getenv("HUGGING_FACE_API_KEY")
if not HF_API_KEY:
    raise ValueError("Falta HUGGING_FACE_API_KEY en .env")

# Recuperar bucket de AWS
S3_BUCKET = os.getenv("S3_BUCKET")  
if not S3_BUCKET:
    raise ValueError("Falta S3_BUCKET en .env")

login(token=HF_API_KEY)

# -----------------------------
# Funciones
# -----------------------------
def generate_prompt(params):
    """Genera prompt usando parámetros recibidos"""
    known = int(params.get("KNOWN", 0))
    name = params.get("NAME")
    company = params.get("COMPANY")
    funcion = params.get("FUNCTION")
    area = params.get("AREA")
    event = params.get("EVENT")
    place = params.get("PLACE")

    if known == 1:        
        prompt = (
            f"Crea texto de un storybook corto de 8 páginas acerca con el siguiente guion: "
            f"La historia se basa en {name} que trabaja en {company} con el cargo de {funcion} en el departamento de {area}. "
            f"Su problema es que tiene muchos gastos acumulados y necesita una solución para digitalizarlos porque la gestión manual le lleva demasiado tiempo. "
            f"Un día escucha hablar del congreso {event} de {place} y decide acudir. Allí conoce la solución de la empresa Sabbatic. "
            f"Al comprobar todo lo que puede ofrecerle la herramienta de Sabbatic, se da cuenta de que es la solución a todos sus problemas. "
            f"Usa un lenguaje cercano evitando la jerga popular como colega, etc, emplea lenguaje sencillo y descriptivo, apropiado para adultos. "
            f"Evita descripciones de personajes e imágenes y escríbelo en tiempo presente. Devuelve solo el cuento nada mas."
        )
    else:
        prompt = (
            f"Crea texto de un storybook corto de 8 páginas acerca con el siguiente guion: "
            f"La historia se basa en {name} que trabaja en {company}. "
            f"Su problema es que tiene muchos gastos acumulados y necesita una solución para digitalizarlos porque la gestión manual le lleva demasiado tiempo. "
            f"Un día escucha hablar del congreso {event} de {place} y decide acudir. Allí conoce la solución de la empresa Sabbatic."
            f"Al comprobar todo lo que puede ofrecerle la herramienta de Sabbatic, se da cuenta de que es la solución a todos sus problemas. "
            f"Usa un lenguaje cercano evitando la jerga popular como colega, etc, emplea lenguaje sencillo y descriptivo, apropiado para adultos. "
            f"Evita descripciones de personajes e imágenes y escríbelo en tiempo presente. Devuelve solo el cuento nada mas."
        )
    return prompt

def cuento_a_json(cuento_texto: str) -> dict:
    """Convierte el texto generado de un cuento en formato JSON con título y páginas."""
    
    titulo_match = re.search(r'^(?:##|\*\*)\s*(?!Página\b)(.+)', cuento_texto, re.MULTILINE)
    if titulo_match:
        titulo = titulo_match.group(1).strip(" *")
    else:
        titulo = "La transformación digital que cambió todo: Descubriendo Sabbatic"

    paginas_raw = re.split(r'\*\*Página\s*\d+[:]*\s*\*\*', cuento_texto)

    if paginas_raw and (titulo in paginas_raw[0] or not paginas_raw[0].strip()):
        paginas_raw = paginas_raw[1:]

    paginas = []
    for i, pagina in enumerate(paginas_raw, start=1):
        pagina = pagina.strip()
        if pagina:
            paginas.append({f"pagina{i}": pagina})

    cuento_json = {
        "titulo": titulo,
        "num_pag": len(paginas),
        "paginas": paginas
    }

    return cuento_json

def subir_a_s3(local_path, bucket, s3_key):
    s3.upload_file(local_path, bucket, s3_key)
    print(f"Archivo subido: s3://{bucket}/{s3_key}")
    logger.info(f"Archivo subido: s3://{bucket}/{s3_key}")

def generar_storybook(params):
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Extraer parámetros
    known = int(params.get("KNOWN", 0))
    name = params.get("NAME")
    company = params.get("COMPANY")
    funcion = params.get("FUNCTION")
    area = params.get("AREA")
    event = params.get("EVENT")
    place = params.get("PLACE")

    # Logs
    print(f"PARAMETROS DE ENTRADA known: {known}, name: {name}, company: {company}, funcion: {funcion}, area: {area}, event: {event}, place: {place}")
    logger.info(f"PARAMETROS DE ENTRADA known: {known}, name: {name}, company: {company}, funcion: {funcion}, area: {area}, event: {event}, place: {place}")

    # Prompt
    prompt = generate_prompt(params)
    print(f"\nPROMPT: {prompt}")
    logger.info(f"\nPROMPT: {prompt}")

    inicio_tiempo = time.perf_counter()

    # Generación
    model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp", system_instruction=prompt)
    response = model.generate_content("Genera el cuento completo con título incluido.")
    cuento_texto = response.text if hasattr(response, "text") else str(response)
    cuento_json = cuento_a_json(cuento_texto)

    # Guardar archivos
    cuento_dir = os.path.join(OUTPUT_DIR, f"cuento_storybook_{known}")
    os.makedirs(cuento_dir, exist_ok=True)

    cuento_path = os.path.join(cuento_dir, f"cuento_{name.replace(' ', '-')}_{company.replace(' ', '-')}.txt")
    with open(cuento_path, "w", encoding="utf-8") as f:
        f.write(cuento_texto)

    cuento_json_path = os.path.join(cuento_dir, f"cuento_{name.replace(' ', '-')}_{company.replace(' ', '-')}.json")
    with open(cuento_json_path, "w", encoding="utf-8") as f:
        json.dump(cuento_json, f, ensure_ascii=False, indent=2)

    subir_a_s3(cuento_path, S3_BUCKET, f"cuentos/{os.path.basename(cuento_path)}")
    subir_a_s3(cuento_json_path, S3_BUCKET, f"cuentos/{os.path.basename(cuento_json_path)}")

    duracion = round(time.perf_counter() - inicio_tiempo, 2)
    print(f"\nTiempo necesitado para crear cuento: {duracion} segundos.\n")
    logger.info(f"\nTiempo necesitado para crear cuento: {duracion} segundos.\n")

    return {"status": "ok", "duracion_segundos": duracion, "cuento_json": cuento_json}

# -----------------------------
# Endpoint POST
# -----------------------------
@app.route("/generar-cuento", methods=["GET"])
def generate():
    params = request.json
    if not params:
        return jsonify({"error": "JSON inválido o vacío"}), 400
    resultado = generar_storybook(params)
    return jsonify(resultado)

# -----------------------------
# Run Flask
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
