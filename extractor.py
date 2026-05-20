import os
import time
import json
import logging
import shutil
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Inicialización del cliente de Gemini
client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key)
        logger.info("Cliente de Gemini (SDK moderno google-genai) inicializado exitosamente.")
    except Exception as e:
        logger.error(f"Error al inicializar el cliente de Gemini: {str(e)}")
else:
    logger.warning("No se encontró GEMINI_API_KEY en las variables de entorno ni en el archivo .env. "
                   "Asegúrate de configurarla antes de ejecutar la extracción.")

# Definición del esquema estructurado usando Pydantic (método recomendado en google-genai)
class ObjetivoExtraccion(BaseModel):
    eje_curricular: str = Field(description="Eje curricular al que pertenece el OA (ej: Números y operaciones, Geometría, etc.)")
    num_oa: str = Field(description="Identificador del objetivo (ej: OA 1, OA 12)")
    descripcion_oa: str = Field(description="Texto completo y exacto del Objetivo de Aprendizaje (OA)")
    nivel_bloom: str = Field(description="Nivel cognitivo según Bloom (Recordar, Comprender, Aplicar, Analizar, Evaluar, Crear) basado en su verbo clave")
    indicadores: List[str] = Field(description="Lista de todos los indicadores de evaluación sugeridos para este OA en el documento")

class CursoExtraccion(BaseModel):
    curso: str = Field(description="Curso o nivel correspondiente al plan (ej: 1° Básico, I Medio)")
    asignatura: str = Field(description="Fijo en 'Matemática'")
    objetivos: List[ObjetivoExtraccion] = Field(description="Lista de Objetivos de Aprendizaje extraídos")

def upload_to_gemini(path: str) -> Optional[Any]:
    """
    Sube un archivo PDF local a la Files API de Gemini y espera a que termine de procesarse.
    Copia temporalmente el archivo a un path limpio (sin caracteres especiales)
    para evitar errores de codificación en Windows.
    """
    if not client:
        logger.error("Cliente de Gemini no inicializado. Configure su GEMINI_API_KEY.")
        return None
        
    # Ruta temporal en la raíz del proyecto para evitar errores de codificación de caracteres no-ASCII
    temp_path = "temp_gemini_upload.pdf"
    logger.info(f"Copiando temporalmente {path} a {temp_path} para evitar problemas de codificación de caracteres en Windows...")
    
    try:
        shutil.copy2(path, temp_path)
    except Exception as e:
        logger.error(f"Error al copiar archivo temporal: {str(e)}")
        return None
        
    try:
        # Usando la Files API del nuevo SDK sobre el path temporal limpio
        file = client.files.upload(file=temp_path)
        logger.info(f"Archivo subido con ID temporal: {file.name}")
        
        # Esperar a que el archivo sea procesado
        while file.state.name == "PROCESSING":
            logger.info("Procesando archivo en los servidores de Google... esperando 5 segundos...")
            time.sleep(5)
            file = client.files.get(name=file.name)
            
        if file.state.name == "FAILED":
            raise Exception("El procesamiento del archivo en Gemini falló.")
            
        logger.info(f"Archivo procesado con éxito en Gemini y listo para análisis.")
        return file
    except Exception as e:
        logger.error(f"Error al subir/procesar el archivo: {str(e)}")
        return None
    finally:
        # Eliminar la copia temporal local
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info(f"Archivo temporal local {temp_path} eliminado.")
            except Exception as e:
                logger.warning(f"No se pudo eliminar el archivo temporal local {temp_path}: {str(e)}")

def cleanup_gemini_file(file_name: str):
    """
    Elimina el archivo de la API de Gemini para mantener el espacio limpio.
    """
    if not client:
        return
    try:
        client.files.delete(name=file_name)
        logger.info(f"Archivo temporal {file_name} eliminado de Gemini Files API.")
    except Exception as e:
        logger.warning(f"No se pudo eliminar el archivo temporal {file_name}: {str(e)}")

def extract_pdf_data(pdf_path: str) -> Optional[Dict[str, Any]]:
    """
    Extrae la información curricular de un PDF local usando Gemini 1.5 Flash (SDK moderno)
    y devuelve la estructura en formato JSON según el esquema CursoExtraccion.
    """
    if not client:
        logger.error("No se puede realizar la extracción porque el cliente de Gemini no está configurado.")
        return None

    # 1. Subir archivo a la API de archivos
    uploaded_file = upload_to_gemini(pdf_path)
    if not uploaded_file:
        logger.error(f"Abortando extracción para {pdf_path} debido a un fallo en la subida.")
        return None
        
    try:
        # 2. Configurar el modelo
        model_name = "gemini-2.5-flash"
        
        # Prompt del sistema para guiar a Gemini
        system_instruction = (
            "Eres un experto en currículum escolar y diseño pedagógico chileno. "
            "Tu tarea es analizar el documento PDF de Planes y Programas del Ministerio de Educación de Chile "
            "y extraer de forma estructurada toda la información curricular relacionada con los Objetivos de Aprendizaje (OA). "
            "Debes ser sumamente meticuloso y preciso, asegurándote de no inventar datos y de relacionar correctamente "
            "cada OA con sus respectivos Indicadores de Evaluación e identificando el Eje Curricular correspondiente. "
            "Para el 'nivel_bloom', debes analizar el verbo del OA y clasificarlo en uno de los niveles de la taxonomía "
            "de Bloom: 'Recordar', 'Comprender', 'Aplicar', 'Analizar', 'Evaluar' o 'Crear'."
        )
        
        # Prompt de usuario
        prompt = (
            "Analiza el PDF adjunto y extrae todos los Objetivos de Aprendizaje (OA) con sus respectivos "
            "ejes curriculares, descripciones, nivel en la taxonomía de Bloom e indicadores de evaluación sugeridos. "
            "Instrucciones específicas:\n"
            "1. Determina con precisión el Curso del documento (ej: '1° Básico', '8° Básico', 'I Medio', 'II Medio').\n"
            "2. Asignatura siempre es 'Matemática'.\n"
            "3. Eje Curricular: Identifica el eje curricular (ej: 'Números y operaciones', 'Patrones y álgebra', 'Geometría', 'Medición', 'Datos y probabilidades', 'Álgebra y funciones', etc.).\n"
            "4. num_oa: Debe ser 'OA X' donde X es el número del objetivo (ej: 'OA 1', 'OA 12').\n"
            "5. descripcion_oa: El texto exacto y completo del Objetivo de Aprendizaje.\n"
            "6. nivel_bloom: Analiza detenidamente el verbo cognitivo dominante del OA y clasifícalo en uno de los 6 niveles: Recordar, Comprender, Aplicar, Analizar, Evaluar, Crear.\n"
            "7. indicadores: Lista detallada con cada uno de los indicadores de evaluación asociados a ese OA específico en el programa. Extráelos de las secciones de las unidades o tablas del documento donde se listan los indicadores para cada OA."
        )
        
        logger.info(f"Enviando solicitud de análisis a {model_name}...")
        
        # Consumo con el SDK moderno
        response = client.models.generate_content(
            model=model_name,
            contents=[uploaded_file, prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=CursoExtraccion,
                temperature=0.1  # Baja temperatura para máxima consistencia y evitar alucinaciones
            )
        )
        
        # 3. Procesar y parsear la respuesta
        result_text = response.text
        logger.info("Respuesta de Gemini recibida con éxito.")
        
        try:
            data = json.loads(result_text)
            return data
        except json.JSONDecodeError as jde:
            logger.error(f"La respuesta de Gemini no es un JSON válido: {result_text}")
            return None
            
    except Exception as e:
        logger.error(f"Error durante la generación de contenido en Gemini: {str(e)}")
        return None
        
    finally:
        # 4. Limpieza del archivo en el servidor
        cleanup_gemini_file(uploaded_file.name)

# Bloque de pruebas local
if __name__ == "__main__":
    if not api_key:
        print("Configura tu GEMINI_API_KEY en el archivo .env para realizar una prueba.")
    else:
        test_file = "MATEMÁTICA/110-1-MATEMÁTICA.pdf"
        if os.path.exists(test_file):
            print(f"Iniciando prueba con {test_file}...")
            resultado = extract_pdf_data(test_file)
            if resultado:
                print("¡Extracción de prueba exitosa!")
                print(json.dumps(resultado, indent=2, ensure_ascii=False)[:1000] + "\n...")
            else:
                print("La extracción de prueba falló.")
        else:
            print(f"El archivo de prueba {test_file} no existe localmente.")
