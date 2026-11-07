# meteoritos-cicd

Sistema de CI/CD con GitHub Actions que valida una muestra de 20 000 registros de
*Meteorite Landings* (NASA / The Meteoritical Society), genera un informe web con Python y lo
publica en GitHub Pages **solo si todas las verificaciones pasan**.

- Fuente: https://data.nasa.gov/dataset/meteorite-landings
- Estudiante: _(escribe aquí tu nombre)_
- Sitio publicado: _(enlace a GitHub Pages)_

## Estructura

```
datos/meteoritos.csv          base utilizada por el sistema (incluida en Git)
scripts/validacion.py         reglas de validación (también es un comando: sale con código 1 si hay errores)
scripts/analisis.py           indicadores calculados desde el CSV
scripts/generar_sitio.py      genera public/index.html
scripts/preparar_datos.py     prepara el CSV inicial desde el original (se usa una sola vez)
tests/test_meteoritos.py      pruebas con datos pequeños e independientes
.github/workflows/ci-cd.yml   workflow: job CI (verificación) + job CD (publicación)
```

## Preparar los datos (una sola vez)

1. Descarga https://data.nasa.gov/docs/legacy/meteorite_landings/Meteorite_Landings.csv
2. Ejecuta `python scripts/preparar_datos.py Meteorite_Landings.csv`
3. Revisa las anomalías que informe y documenta su tratamiento antes del primer commit.
4. Haz commit de `datos/meteoritos.csv`. No vuelvas a descargarlo; el workflow usa ese archivo.

## Ejecutar localmente

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
python -m pytest -v                                   # pruebas
python scripts/validacion.py datos/meteoritos.csv     # validar el CSV completo
python scripts/generar_sitio.py                       # genera public/index.html
```

Variables opcionales de `generar_sitio.py`: `ESTUDIANTE` (nombre mostrado) y `GITHUB_SHA`
(commit mostrado); también existen `--estudiante` y `--commit`.

## Reglas de validación

| Campo | Regla |
|---|---|
| Estructura | Columnas requeridas presentes; cada fila con el mismo número de campos que la cabecera |
| id | Entero positivo, obligatorio, único |
| name, recclass | Texto no vacío tras quitar espacios |
| mass (g) | Número finito ≥ 0 si está disponible |
| fall | Solo `Fell` o `Found` (distingue mayúsculas) |
| year | Si está disponible, año entero entre 1 y 2026 |
| reclat / reclong | Finito en [−90, 90] / [−180, 180] si están disponibles |

**Datos faltantes:** campo vacío, solo espacios, o `NA`, `N/A`, `NaN`, `null`, `None`, `-`
(sin distinguir mayúsculas). Nunca se convierten en 0: se excluyen de la masa media y se cuentan
aparte. Una coordenada `0` es válida.

**Año:** la fuente lo trae como fecha completa (`01/01/1880 12:00:00 AM`). Se extrae el año de
formatos `MM/DD/AAAA [hora]`, `AAAA-MM-DD` o un entero simple.

**Registros simulados:** los registros de prueba añadidos al CSV llevan el prefijo `SIM-` en
`name`; el sitio los marca con la etiqueta «simulado».

Ante un error el programa imprime fila (número de línea del archivo; la cabecera es la 1), campo
y motivo, termina con código 1 y el job CI falla, de modo que CD se omite.

## CI/CD

Se ejecuta en cada push a `main` y manualmente (*Run workflow*).

- **CI — Verificación:** checkout → Python → dependencias → pytest → validar CSV → generar sitio → subir artefacto.
- **CD — Publicación:** `needs: ci`; despliega en GitHub Pages solo si CI terminó bien.

Configuración única en GitHub: *Settings → Pages → Source: GitHub Actions*. Opcional: define la
variable de repositorio `ESTUDIANTE` (*Settings → Secrets and variables → Actions → Variables*)
con tu nombre.
