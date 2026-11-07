"""Prepara datos/meteoritos.csv a partir del CSV original de la NASA (ejecutar UNA sola vez).

Uso:
    python scripts/preparar_datos.py Meteorite_Landings.csv

Toma las primeras 20 000 filas de datos (sin contar la cabecera), conserva orden y
campos faltantes, y deja solo las columnas requeridas. Luego informa de las
anomalías que detecte la validación, SIN corregirlas: documenta su tratamiento
en el informe antes de dar por buena la versión inicial.
"""
import csv
import sys
from pathlib import Path

from validacion import COLUMNAS, validar_archivo

N_FILAS = 20000


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 2
    origen = Path(argv[0])
    destino = Path("datos/meteoritos.csv")
    destino.parent.mkdir(exist_ok=True)
    with open(origen, newline="", encoding="utf-8-sig") as f, \
            open(destino, "w", newline="", encoding="utf-8") as g:
        lector = csv.DictReader(f)
        cabecera = [c.strip() for c in lector.fieldnames]
        print("Columnas del original:", cabecera)
        faltan = [c for c in COLUMNAS if c not in cabecera]
        if faltan:
            print(f"Faltan columnas {faltan}: renómbralas y documenta la adaptación.")
            return 1
        escritor = csv.writer(g, lineterminator="\n")
        escritor.writerow(COLUMNAS)
        n = 0
        for fila in lector:
            if n >= N_FILAS:
                break
            fila = {k.strip(): v for k, v in fila.items()}
            escritor.writerow([fila[c] for c in COLUMNAS])
            n += 1
    print(f"Escritas {n} filas en {destino}")
    _, errores = validar_archivo(destino)
    if errores:
        print(f"\nAtención: {len(errores)} anomalía(s) en los datos originales (documéntalas):")
        for e in errores[:50]:
            print(f"  - {e}")
        if len(errores) > 50:
            print(f"  ... y {len(errores) - 50} más")
    else:
        print("La validación no encontró anomalías.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
