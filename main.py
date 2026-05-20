import os
import glob
import json
import logging
import time
import pandas as pd
from dotenv import load_dotenv
from extractor import extract_pdf_data

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN PRINCIPAL ---
ASIGNATURA_ACTUAL = "HISTORIA, GEOGRAFÍA Y CIENCIAS SOCIALES"  # Cambiar aquí para procesar otra asignatura
# -------------------------------

# Directorios y rutas
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(WORKSPACE_DIR, ASIGNATURA_ACTUAL)
CACHE_DIR = os.path.join(WORKSPACE_DIR, "output_cache")
BASES_DIR = os.path.join(WORKSPACE_DIR, "bases de datos planes y programas")
os.makedirs(BASES_DIR, exist_ok=True)
OUTPUT_EXCEL = os.path.join(BASES_DIR, f"planes_{ASIGNATURA_ACTUAL.lower().replace(' ', '_')}.xlsx")
OUTPUT_JSON = os.path.join(BASES_DIR, f"planes_{ASIGNATURA_ACTUAL.lower().replace(' ', '_')}.json")

# Asegurar directorios
os.makedirs(CACHE_DIR, exist_ok=True)

# Mapeo de códigos de archivos curriculares a nombres descriptivos en español
CURSO_MAP = {
    "110-1-MATEMÁTICA.pdf": "1° Básico",
    "110-2-MATEMÁTICA.pdf": "2° Básico",
    "110-3-MATEMÁTICA.pdf": "3° Básico",
    "110-4-MATEMÁTICA.pdf": "4° Básico",
    "110-5-MATEMÁTICA.pdf": "5° Básico",
    "110-6-MATEMÁTICA.pdf": "6° Básico",
    "110-7-MATEMÁTICA.pdf": "7° Básico",
    "110-8-MATEMÁTICA.pdf": "8° Básico",
    "310-1-MATEMÁTICA.pdf": "I Medio",
    "310-2-MATEMÁTICA.pdf": "II Medio",
    "310-3-MATEMÁTICA.pdf": "III Medio",
    "310-4-MATEMÁTICA.pdf": "IV Medio"
}

def obtener_nombre_curso(filename: str) -> str:
    """
    Retorna el nombre formateado del curso basado en el nombre del archivo.
    Si no está en el mapa, intenta deducirlo o retorna el nombre del archivo.
    """
    basename = os.path.basename(filename)
    if basename in CURSO_MAP:
        return CURSO_MAP[basename]
    
    # Intento de deducción inteligente
    parts = basename.split('-')
    if len(parts) >= 2:
        prefix = parts[0]
        level = parts[1]
        if prefix == "110":
            return f"{level}° Básico"
        elif prefix == "310":
            # Convertir a romano
            romanos = {1: "I", 2: "II", 3: "III", 4: "IV"}
            try:
                num = int(level)
                return f"{romanos.get(num, level)} Medio"
            except ValueError:
                return f"{level} Medio"
                
    return basename.replace(".pdf", "").replace("-", " ")

def consolidar_resultados() -> bool:
    """
    Lee todos los archivos JSON de la caché, los consolida y los exporta a formatos
    Excel y JSON final con un diseño premium y formateado adecuado.
    """
    logger.info("Iniciando consolidación de datos...")
    cache_files = glob.glob(os.path.join(CACHE_DIR, "*.json"))
    
    if not cache_files:
        logger.warning("No se encontraron archivos en la caché para consolidar.")
        return False
        
    lista_objetivos_flatten = []
    lista_completa_jerarquica = []
    
    # Procesar cada archivo de caché
    for cache_file in cache_files:
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # FILTRO DE ASIGNATURA: Ignorar archivos que no correspondan
                cache_asignatura = data.get("asignatura", "")
                if cache_asignatura.upper() != ASIGNATURA_ACTUAL.upper():
                    continue

                lista_completa_jerarquica.append(data)
                
                curso = data.get("curso", "Desconocido")
                asignatura = cache_asignatura
                objetivos = data.get("objetivos", [])
                
                for obj in objetivos:
                    eje = obj.get("eje_curricular", "")
                    num_oa = obj.get("num_oa", "")
                    desc_oa = obj.get("descripcion_oa", "")
                    bloom = obj.get("nivel_bloom", "")
                    indicadores_lista = obj.get("indicadores", [])
                    
                    # Formatear la lista de indicadores como texto con viñetas y saltos de línea para Excel
                    if isinstance(indicadores_lista, list):
                        indicadores_str = "\n".join([f"• {ind.strip()}" for ind in indicadores_lista if ind.strip()])
                    else:
                        indicadores_str = str(indicadores_lista)
                        
                    lista_objetivos_flatten.append({
                        "Curso": curso,
                        "Asignatura": asignatura,
                        "Eje Curricular": eje,
                        "N° de OA": num_oa,
                        "Descripción del OA": desc_oa,
                        "Nivel Cognitivo (Bloom)": bloom,
                        "Indicadores de Evaluación": indicadores_str
                    })
        except Exception as e:
            logger.error(f"Error al leer el archivo de caché {cache_file}: {str(e)}")
            
    # 1. Exportar JSON consolidado
    try:
        with open(OUTPUT_JSON, "w", encoding="utf-8") as jf:
            json.dump(lista_completa_jerarquica, jf, indent=2, ensure_ascii=False)
        logger.info(f"Archivo JSON consolidado guardado en: {OUTPUT_JSON}")
    except Exception as e:
        logger.error(f"Error al escribir el archivo JSON consolidado: {str(e)}")

    # 2. Exportar Excel consolidado con estilo Premium
    if not lista_objetivos_flatten:
        logger.warning("No hay filas de datos para exportar a Excel.")
        return False
        
    try:
        df = pd.DataFrame(lista_objetivos_flatten)
        
        # Ordenar los datos por nivel/curso lógicamente
        # Para que Básica (1° a 8°) y Media (I a IV) queden ordenados
        orden_cursos = [
            "1° Básico", "2° Básico", "3° Básico", "4° Básico", 
            "5° Básico", "6° Básico", "7° Básico", "8° Básico",
            "I Medio", "II Medio", "III Medio", "IV Medio"
        ]
        
        df['Curso'] = pd.Categorical(df['Curso'], categories=orden_cursos, ordered=True)
        
        # Extraer el número de OA para realizar una ordenación numérica natural (ej: OA 2 antes de OA 10)
        import re
        def extraer_numero_oa(oa_str):
            if not isinstance(oa_str, str):
                return 999
            numeros = re.findall(r'\d+', oa_str)
            if numeros:
                return int(numeros[0])
            return 999
            
        df['_OA_num'] = df['N° de OA'].apply(extraer_numero_oa)
        df = df.sort_values(by=['Curso', 'Asignatura', '_OA_num']).reset_index(drop=True)
        df = df.drop(columns=['_OA_num'])
        
        # Escribir con Pandas a Excel usando OpenPyXL para dar formato premium
        writer = pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl')
        df.to_excel(writer, sheet_name='Planes Curriculares', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Planes Curriculares']
        
        # Aplicar estilos estéticos
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        
        # Fuentes y Colores
        font_family = "Segoe UI"
        header_font = Font(name=font_family, size=11, bold=True, color="FFFFFF")
        body_font = Font(name=font_family, size=10, color="333333")
        
        # Color azul profundo institucional para las matemáticas / educación
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        zebra_fill = PatternFill(start_color="F2F5F8", end_color="F2F5F8", fill_type="solid")
        
        # Bordes
        thin_border_side = Side(border_style="thin", color="D9D9D9")
        border_all = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
        
        # Alineaciones
        align_left = Alignment(horizontal="left", vertical="top", wrap_text=True)
        align_center = Alignment(horizontal="center", vertical="top", wrap_text=True)
        
        # Aplicar estilos a la cabecera
        for col_num in range(1, len(df.columns) + 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = align_center
            cell.border = border_all
            
        # Aplicar estilos a los datos
        for row_num in range(2, len(df) + 2):
            # Cebra intermitente para mejorar legibilidad
            use_zebra = (row_num % 2 == 0)
            
            for col_num in range(1, len(df.columns) + 1):
                cell = worksheet.cell(row=row_num, column=col_num)
                cell.font = body_font
                cell.border = border_all
                
                if use_zebra:
                    cell.fill = zebra_fill
                    
                # Aplicar alineación adecuada según columna
                col_name = df.columns[col_num - 1]
                if col_name in ["Curso", "Asignatura", "N° de OA", "Nivel Cognitivo (Bloom)"]:
                    cell.alignment = align_center
                else:
                    cell.alignment = align_left
                    
        # Configurar alturas de fila y anchos de columna automáticos adaptados
        worksheet.row_dimensions[1].height = 28 # Cabecera alta
        
        for row_num in range(2, len(df) + 2):
            # Darle buena altura para las celdas con multilínea de indicadores
            worksheet.row_dimensions[row_num].height = None # Auto
            
        # Definir anchos personalizados fijos y adaptados para que se vea premium
        column_widths = {
            "Curso": 14,
            "Asignatura": 14,
            "Eje Curricular": 22,
            "N° de OA": 12,
            "Descripción del OA": 50,
            "Nivel Cognitivo (Bloom)": 20,
            "Indicadores de Evaluación": 60
        }
        
        for col_idx, col_name in enumerate(df.columns, 1):
            col_letter = get_column_letter(col_idx)
            worksheet.column_dimensions[col_letter].width = column_widths.get(col_name, 20)
            
        # Guardar archivo Excel
        writer.close()
        logger.info(f"Archivo Excel consolidado y estilizado guardado en: {OUTPUT_EXCEL}")
        return True
    except Exception as e:
        logger.error(f"Error al escribir el archivo Excel consolidado: {str(e)}")
        return False

def main():
    """
    Función principal del orquestador del extractor.
    """
    # 1. Validar que la carpeta de entrada exista
    if not os.path.exists(PDF_DIR):
        logger.error(f"La carpeta {PDF_DIR} no existe. Por favor, créala y coloca los PDFs curriculares.")
        return
        
    # 2. Buscar PDFs en la carpeta
    pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    if not pdf_files:
        logger.error(f"No se encontraron archivos PDF en {PDF_DIR}.")
        return
        
    logger.info(f"Se detectaron {len(pdf_files)} archivos PDF para procesar.")
    
    # 3. Validar API Key
    api_key_check = os.getenv("GEMINI_API_KEY")
    if not api_key_check:
        logger.error("ADVERTENCIA: GEMINI_API_KEY no está configurada. "
                     "El script no podrá comunicarse con la API. Deteniendo el procesamiento.")
        return

    # 4. Procesar cada archivo PDF de forma secuencial con caché incremental
    total_procesados = 0
    total_omitidos = 0
    total_fallidos = 0
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        curso = obtener_nombre_curso(filename)
        
        # La clave de caché es el nombre del archivo sin extensión
        cache_key = filename.replace(".pdf", "")
        cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")
        
        logger.info("-" * 60)
        logger.info(f"Procesando: {filename} -> Asignado a: {curso}")
        
        # Verificar si ya está en caché
        if os.path.exists(cache_path):
            logger.info(f"El curso '{curso}' ({filename}) ya se encuentra en caché. Omitiendo extracción.")
            total_omitidos += 1
            continue
            
        # Extraer mediante Gemini con reintento automático
        MAX_REINTENTOS = 3
        exito = False
        
        for intento in range(1, MAX_REINTENTOS + 1):
            try:
                logger.info(f"Iniciando extracción con Gemini para: {curso} (intento {intento}/{MAX_REINTENTOS})...")
                resultado = extract_pdf_data(pdf_path)
                
                if resultado:
                    # Validar o forzar que el campo 'curso' sea el nombre legible
                    resultado["curso"] = curso
                    resultado["asignatura"] = ASIGNATURA_ACTUAL.capitalize()
                    
                    # Guardar en caché individual
                    with open(cache_path, "w", encoding="utf-8") as cf:
                        json.dump(resultado, cf, indent=2, ensure_ascii=False)
                        
                    logger.info(f"Extracción completada con éxito y guardada en caché para: {curso}")
                    total_procesados += 1
                    exito = True
                    break
                else:
                    # Sin resultado: posible 429 o error temporal
                    if intento < MAX_REINTENTOS:
                        espera = 30 * intento  # 30s, 60s, 90s (backoff)
                        logger.warning(f"Sin resultado para {curso}. Reintentando en {espera}s...")
                        time.sleep(espera)
                    else:
                        logger.error(f"No se obtuvo resultado de la extracción para: {curso} tras {MAX_REINTENTOS} intentos.")
                        total_fallidos += 1
            except Exception as e:
                if intento < MAX_REINTENTOS:
                    espera = 30 * intento
                    logger.warning(f"Error en intento {intento} para {curso}: {str(e)}. Reintentando en {espera}s...")
                    time.sleep(espera)
                else:
                    logger.error(f"Error inesperado al procesar {curso} tras {MAX_REINTENTOS} intentos: {str(e)}")
                    total_fallidos += 1
        
        if exito:
            # Pausa prudencial entre llamadas exitosas a la API (5 RPM = 1 cada 12s, usamos 20s por seguridad)
            time.sleep(20)
            
    logger.info("=" * 60)
    logger.info(f"Resumen de Procesamiento:\n"
                f" - Total Archivos: {len(pdf_files)}\n"
                f" - Procesados con éxito en esta sesión: {total_procesados}\n"
                f" - Recuperados de caché: {total_omitidos}\n"
                f" - Fallidos: {total_fallidos}")
    logger.info("=" * 60)
    
    # 5. Consolidar todos los resultados en los archivos finales
    exito_consolidador = consolidar_resultados()
    if exito_consolidador:
        logger.info("¡Proceso finalizado con éxito absoluto!")
        print(f"\nProceso finalizado. Archivos generados:\n"
              f"  - Excel (Premium): {OUTPUT_EXCEL}\n"
              f"  - JSON (Respaldo): {OUTPUT_JSON}\n")
    else:
        logger.error("El proceso de consolidación de resultados falló.")

if __name__ == "__main__":
    main()
