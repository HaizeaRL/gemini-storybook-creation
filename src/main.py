import pandas as pd
import os
from dotenv import load_dotenv
import google.generativeai as genai  # Para API key Gemini
import time
import shutil
from huggingface_hub import login
import re
import json

# -----------------------------
# Cargar variables de entorno
load_dotenv()

# Configurar API key de Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Falta GOOGLE_API_KEY en .env")
genai.configure(api_key=GOOGLE_API_KEY)

# Configurar HuggingFace API key
HF_API_KEY = os.getenv("HUGGING_FACE_API_KEY")
if not HF_API_KEY:
    raise ValueError("Falta HUGGING_FACE_API_KEY en .env")

login(token=HF_API_KEY)

def generate_prompt():
       
    if known == 1:        
        prompt = (
                f"Crea texto de un storybook corto de 8 páginas acerca con el siguiente guion: "
                f"La historia se basa en {name} que trabaja en {company} con el cargo de {funcion} en el departamento de {area}. "
                f"Su problema es que tiene muchos gastos acumulados y necesita una solución para digitalizarlos porque la gestión manual le lleva demasiado tiempo. "
                f"Un día escucha hablar del congreso {event} de {place} y decide acudir. Allí  conoce la solución de la empresa Sabbatic. "
                f"Al comprobar todo lo que puede ofrecerle la herramienta de Sabbatic, se da cuenta de que es la solución a todos sus problemas. "
                f"Usa un lenguaje cercano evitando la jerga popular como colega, etc, emplea lenguaje sencillo y descriptivo, apropiado para adultos. "
                f"Evita descripciones de personajes e imágenes y escríbelo en tiempo presente. Devuelve solo el cuento nada mas."
        )
    else:
        prompt = (
                f"Crea texto de un storybook corto de 8 páginas acerca con el siguiente guion: "
                f"La historia se basa en {name} que trabaja en {company}. "
                f"Su problema es que tiene muchos gastos acumulados y necesita una solución para digitalizarlos porque la gestión manual le lleva demasiado tiempo. "
                f"Un día escucha hablar del congreso {event} de {place} y decide acudir. Allí  conoce la solución de la empresa Sabbatic."
                f"Al comprobar todo lo que puede ofrecerle la herramienta de Sabbatic, se da cuenta de que es la solución a todos sus problemas. "
                f"Usa un lenguaje cercano evitando la jerga popular como colega, etc, emplea lenguaje sencillo y descriptivo, apropiado para adultos. "
                f"Evita descripciones de personajes e imágenes y escríbelo en tiempo presente. Devuelve solo el cuento nada mas."
            )
    return prompt

def cuento_a_json(cuento_texto: str) -> dict:
    """Convierte el texto generado de un cuento en formato JSON con título y páginas."""
    
    # Extraer título: primera línea que empieza con ## o **, pero NO contiene "Página"
    titulo_match = re.search(r'^(?:##|\*\*)\s*(?!Página\b)(.+)', cuento_texto, re.MULTILINE)
    if titulo_match:
        titulo = titulo_match.group(1).strip(" *")
    else:
        # Si no titulo por defecto
        titulo = "La transformación digital que cambió todo: Descubriendo Sabbatic"

     # Dividir texto en páginas
    paginas_raw = re.split(r'\*\*Página\s*\d+[:]*\s*\*\*', cuento_texto)

    # Eliminar primera entrada si contiene solo el título o está vacía
    if paginas_raw and (titulo in paginas_raw[0] or not paginas_raw[0].strip()):
        paginas_raw = paginas_raw[1:]

    # Construir lista de páginas
    paginas = []
    for i, pagina in enumerate(paginas_raw, start=1):
        pagina = pagina.strip()
        if pagina:
            paginas.append({f"pagina{i}": pagina})

    # Construir JSON final
    cuento_json = {
        "titulo": titulo,
        "num_pag": len(paginas),
        "paginas": paginas
    }

    return cuento_json

# -----------------------------
# MAIN
# -----------------------------
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
if not OUTPUT_DIR:
    raise ValueError("Falta OUTPUT_DIR en .env")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Generar prompt con parametros de entrada
known = int(os.getenv("KNOWN", 0))
name = os.getenv("NAME")
company = os.getenv("COMPANY")
funcion = os.getenv("FUNCTION")
area = os.getenv("AREA")
event = os.getenv("EVENT")
place = os.getenv("PLACE")


print(f"""PARAMETROS DE ENTRADA known: {known}, name: {name}, company: {company} , funcion:{funcion}, area:{area} event: {event} , place: {place}""")

prompt = generate_prompt()
print(f"\n PROMPT: {prompt}")

# 3. Generar cuento
inicio_tiempo = time.perf_counter()
try:
    # GEMINI: generar historia usando generate_content()
    model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp", system_instruction=prompt)
    response = model.generate_content("Genera el cuento completo con título incluido.")
    cuento_texto = response.text if hasattr(response, "text") else str(response)

    # genera json
    cuento_json = cuento_a_json(cuento_texto)
    #print(json.dumps(cuento_json, ensure_ascii=False, indent=2))

    # Crear carpeta SOLO si todo fue exitoso
    cuento_dir = os.path.join(OUTPUT_DIR, f"cuento_storybook_{str(known)}")
    os.makedirs(cuento_dir, exist_ok=True)

    cuento_path = os.path.join(cuento_dir, "cuento.txt")
    with open(cuento_path, "w", encoding="utf-8") as f:        
        f.write("--- Cuento ---\n")
        f.write(cuento_texto if cuento_texto else "Sin contenido generado.")
        f.write("\n-----------------\n")

    # Guardar JSON
    cuento_json_path = os.path.join(cuento_dir, "cuento.json")
    with open(cuento_json_path, "w", encoding="utf-8") as f:
        json.dump(cuento_json, f, ensure_ascii=False, indent=2)

    # Registrar tiempos
    fin_tiempo = time.perf_counter()
    duracion = round(fin_tiempo - inicio_tiempo, 2)
    log_path = os.path.join(OUTPUT_DIR, "tiempos_generacion.csv")
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding="utf-8") as log:
            log.write("Duracion_s\n")
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"{duracion}\n")

    print(f"\nCuento guardado en: {cuento_dir}. Tiempo necesitado {duracion} segundos.\n")

except Exception as e:
    print(f"Ocurrió un error en la creación del cuento: {e}")
    if os.path.exists(cuento_dir):            
        shutil.rmtree(cuento_dir)
        print(f"Carpeta vacía eliminada: {cuento_dir}")
