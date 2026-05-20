<!-- BEGIN:extractor-planes-rules -->
# Reglas del Proyecto Extractor-Planes

## 📋 Documentación Obligatoria de Procesos (Memoria IA)

Cada vez que se procese una asignatura, se realice un cambio en la configuración o se ajusten los prompts de extracción:

1. **ANTES de proponer cambios:** Leer TODOS los archivos en la carpeta `memoria-ia/` para entender qué asignaturas ya fueron procesadas y qué configuraciones se utilizaron para no repetir errores pasados.
2. **DESPUÉS de procesar o implementar:** Crear o actualizar un archivo markdown en `memoria-ia/` con el historial.
   - Formato recomendado para nuevos logs: `YYYY-MM-DD_HH-MM_Asignatura_Procesada.md`
   - Contenido: Asignatura procesada, cantidad de archivos, errores superados, y estado final.

## 🗄️ Estructura de Salida
- Todos los archivos Excel (`.xlsx`) y JSON (`.json`) generados deben guardarse siempre en la carpeta `bases de datos planes y programas/`.
<!-- END:extractor-planes-rules -->
