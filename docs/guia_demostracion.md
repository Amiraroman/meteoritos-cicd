# Guía de pruebas y demostración

Ejecuta cada paso desde la carpeta del repositorio. Lo más simple: añade las líneas al final del CSV desde VS Code (con un salto de línea antes). Si usas `echo`, deja un espacio antes de `>>` (el espacio final no afecta la validación).
Registros simulados: nombre con prefijo `SIM-`. El `id` válido debe ser nuevo (mira el último id del CSV y usa otro mayor).

Antes de cada prueba comprueba que el CSV termine con salto de línea.

## 0. Primera publicación
1. `python scripts/preparar_datos.py Meteorite_Landings.csv`, documenta anomalías.
2. Sube a GitHub, activa Pages (Source: GitHub Actions).
3. Anota los indicadores de la primera versión (total, Fell, Found, masa media, sin masa).
4. Captura: Actions (CI y CD verdes) + página.

## 1. Registro válido
```
echo 900001,SIM-Ficticio Altiplano,L5,12.5,Fell,2026,-16.5,-68.15 >> datos/meteoritos.csv
```
Local: `python -m pytest`, `python scripts/validacion.py`.
`git add . && git commit -m "Añade registro simulado válido" && git push`
Esperado: total +1; Fell +1; masa media recalculada con una masa más; «sin masa» igual; el registro aparece en la tabla de últimos 10.

## 2. Tres errores (por separado; corrige y envía entre uno y otro)
| Prueba | Línea a añadir | Mensaje esperado |
|---|---|---|
| Masa | `900002,SIM-Masa negativa,L5,-5,Found,2026,1,1` | campo 'mass (g)': la masa no puede ser negativa |
| Coordenada | `900003,SIM-Latitud,L5,5,Found,2026,95,1` | campo 'reclat': 95 fuera del rango |
| id duplicado | `1,SIM-Duplicado,L5,5,Found,2026,1,1` (id existente) | campo 'id': identificador 1 duplicado |

Para cada una: comprobación local (debe fallar con código 1) → commit + push → ver CI en rojo y CD *skipped* → la página sigue mostrando la última versión válida → eliminar la línea errónea (o reemplazarla) → commit + push → CI y CD verdes.

Nota: las pruebas unitarias (pytest) siguen pasando porque usan datos propios; el que falla es el paso «Validar el CSV completo».

## 3. En clase
Añade un registro inválido → push → muestra el bloqueo. Corrige → push → muestra el registro en la página. Prepárate para explicar `validacion.py` y `ci-cd.yml` (`needs: ci`).

## Datos para el informe
Guarda por cada captura: commit (hash corto) y URL de la ejecución de Actions (`https://github.com/<usuario>/meteoritos-cicd/actions/runs/<id>`).
