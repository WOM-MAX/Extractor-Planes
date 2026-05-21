# Resumen de Sesión: 20 de Mayo de 2026

**Última actualización:** 20:16 GMT-4 (sesión tarde/noche)

## ✅ PROYECTO COMPLETADO - 10/10 Asignaturas

### Asignaturas Completadas ✅
| # | Asignatura | Archivos | Sesión | Excel | JSON |
|---|---|---|---|---|---|
| 1 | Matemática | 12 | Mañana | ✅ planes_matematica.xlsx | ✅ planes_matematica.json |
| 2 | Lenguaje | 12 | Mañana | ✅ planes_lenguaje.xlsx | ✅ planes_lenguaje.json |
| 3 | Ciencias Naturales | 10 | Mañana | ✅ planes_ciencias_naturales.xlsx | ✅ planes_ciencias_naturales.json |
| 4 | Historia, Geografía y CS | 12 | Mañana | ✅ planes_historia,_geografía_y_ciencias_sociales.xlsx | ✅ planes_historia,_geografía_y_ciencias_sociales.json |
| 5 | Artes Visuales | - | Tarde | ✅ planes_artes_visuales.xlsx | ✅ planes_artes_visuales.json |
| 6 | Educación Física y Salud | 12 | Tarde | ✅ planes_educación_física_y_salud.xlsx | ✅ planes_educación_física_y_salud.json |
| 7 | Inglés | 8 | Tarde | ✅ planes_inglés.xlsx | ✅ planes_inglés.json |
| 8 | Música | 13 | Tarde | ✅ planes_música.xlsx | ✅ planes_música.json |
| 9 | Orientación | 10 | Tarde | ✅ planes_orientación.xlsx | ✅ planes_orientación.json |
| 10 | Tecnología | 10 | Tarde | ✅ planes_tecnología.xlsx | ✅ planes_tecnología.json |

### Asignaturas Pendientes ❌
**NINGUNA** — Todas las asignaturas fueron procesadas exitosamente.

## Cambios Importantes Realizados en el Código
1. **`main.py` parametrizado:** La variable `ASIGNATURA_ACTUAL` en la línea 17 controla qué asignatura se procesa. Solo hay que cambiar ese string.
2. **Filtro anti-contaminación:** Se añadió un filtro en `consolidar_resultados()` que verifica la asignatura de cada archivo de caché antes de incluirlo en el Excel. Esto evita que datos de una asignatura se mezclen con otra.
3. **Reintento automático:** Se implementó lógica de reintento con backoff exponencial (30s, 60s, 90s) para manejar errores 429 de la API.
4. **Procesamiento paralelo:** ThreadPoolExecutor con 5 workers para la API de pago.
5. **Fix concurrencia:** Archivos temporales con UUID únicos para evitar conflictos entre hilos.
6. **Procesamiento multi-asignatura:** Lista `ASIGNATURAS` en lugar de variable individual.
7. **Salida unificada:** Todos los Excel/JSON se guardan en `bases de datos planes y programas/`.

## API Keys Utilizadas
1. `AIzaSyD-WnWe...` → Lenguaje + Ciencias Naturales (free tier, agotada)
2. `AIzaSyCnOx...` → Intentos fallidos de Historia (free tier, agotada)
3. `AIzaSyCX_r...` → Intentos fallidos de Historia (free tier, agotada)
4. `AIzaSyAg1H...` → Historia completada (free tier)
5. `AIzaSyCBBH...` → API de pago, primer intento (Artes Visuales)
6. `AIzaSyAOTc...` → API de pago, segundo intento (6 asignaturas restantes)

## Costo Final
- Google AI Studio prepago: $10 USD
- Consumo estimado: ~$2-3 USD
- Saldo restante estimado: ~$7-8 USD
