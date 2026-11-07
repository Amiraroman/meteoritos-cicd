"""Validación del CSV de meteoritos.

Reglas (ver README):
  - estructura: columnas requeridas y cantidad de campos por fila
  - id: entero positivo, obligatorio, único
  - name, recclass: texto obligatorio no vacío
  - mass (g): número finito >= 0 (si está disponible)
  - fall: solo "Fell" o "Found"
  - year: año entero entre 1 y 2026 (si está disponible), extraído de fechas completas
  - reclat: finito en [-90, 90] (si está disponible)
  - reclong: finito en [-180, 180] (si está disponible)

Datos faltantes: campo vacío, solo espacios, o uno de FALTANTES (sin distinguir
mayúsculas). Un faltante NUNCA se convierte en 0.
"""
import csv
import math
import re
import sys
from dataclasses import dataclass

COLUMNAS = ["id", "name", "recclass", "mass (g)", "fall", "year", "reclat", "reclong"]
FALLS = ("Fell", "Found")
ANIO_MIN, ANIO_MAX = 1, 2026
FALTANTES = {"", "na", "n/a", "nan", "null", "none", "-"}


@dataclass(frozen=True)
class ErrorValidacion:
    fila: int      # número de línea en el archivo (la cabecera es la fila 1)
    campo: str
    motivo: str

    def __str__(self):
        return f"Fila {self.fila}, campo '{self.campo}': {self.motivo}"


def es_faltante(valor):
    return valor is None or valor.strip().lower() in FALTANTES


def _numero_finito(texto):
    """Devuelve float finito o lanza ValueError."""
    try:
        n = float(texto.strip())
    except ValueError:
        raise ValueError(f"'{texto}' no es un número")
    if not math.isfinite(n):
        raise ValueError(f"'{texto}' no es un número finito")
    return n


def extraer_anio(texto):
    """Extrae el año de un texto: '1880', '01/01/1880 12:00:00 AM' o '1880-01-01'.

    Devuelve int o None si no se reconoce ningún formato.
    """
    t = texto.strip()
    if re.fullmatch(r"\d+", t):
        return int(t)
    m = re.fullmatch(r"\d{1,2}/\d{1,2}/(\d{1,4})(?:\s.*)?", t)  # MM/DD/YYYY [hora]
    if m:
        return int(m.group(1))
    m = re.fullmatch(r"(\d{1,4})-\d{1,2}-\d{1,2}(?:[T\s].*)?", t)  # YYYY-MM-DD
    if m:
        return int(m.group(1))
    return None


def parsear_id(texto):
    t = texto.strip()
    if not re.fullmatch(r"\d+", t) or int(t) <= 0:
        raise ValueError(f"'{texto}' no es un entero positivo")
    return int(t)


def parsear_masa(texto):
    n = _numero_finito(texto)
    if n < 0:
        raise ValueError(f"la masa no puede ser negativa ({texto})")
    return n


def parsear_rango(texto, minimo, maximo):
    n = _numero_finito(texto)
    if not (minimo <= n <= maximo):
        raise ValueError(f"{texto} fuera del rango [{minimo}, {maximo}]")
    return n


def parsear_anio(texto):
    a = extraer_anio(texto)
    if a is None:
        raise ValueError(f"no se pudo extraer un año de '{texto}'")
    if not (ANIO_MIN <= a <= ANIO_MAX):
        raise ValueError(f"año {a} fuera del rango [{ANIO_MIN}, {ANIO_MAX}]")
    return a


def convertir_fila(fila):
    """Convierte una fila (dict de str). Devuelve (registro tipado, [(campo, motivo)]).

    Los faltantes quedan como None (nunca 0)."""
    errores = []
    reg = {}

    def intentar(campo, f):
        try:
            return f()
        except ValueError as e:
            errores.append((campo, str(e)))
            return None

    reg["id"] = intentar("id", lambda: parsear_id(fila["id"]))
    for campo in ("name", "recclass"):
        v = fila[campo].strip()
        if not v:
            errores.append((campo, "texto obligatorio vacío"))
            reg[campo] = None
        else:
            reg[campo] = v

    def opcional(campo, parser):
        if es_faltante(fila[campo]):
            return None
        return intentar(campo, lambda: parser(fila[campo]))

    reg["mass (g)"] = opcional("mass (g)", parsear_masa)
    f = fila["fall"].strip()
    if f not in FALLS:
        errores.append(("fall", f"valor '{fila['fall']}' no permitido (solo Fell o Found)"))
        reg["fall"] = None
    else:
        reg["fall"] = f
    reg["year"] = opcional("year", parsear_anio)
    reg["reclat"] = opcional("reclat", lambda t: parsear_rango(t, -90, 90))
    reg["reclong"] = opcional("reclong", lambda t: parsear_rango(t, -180, 180))
    return reg, errores


def validar_archivo(ruta):
    """Valida todo el CSV. Devuelve (registros_validos_o_parciales, errores)."""
    errores = []
    registros = []
    with open(ruta, newline="", encoding="utf-8-sig") as fh:
        lector = csv.reader(fh)
        try:
            cabecera = [c.strip() for c in next(lector)]
        except StopIteration:
            return [], [ErrorValidacion(1, "estructura", "el archivo está vacío")]
        faltan = [c for c in COLUMNAS if c not in cabecera]
        if faltan:
            return [], [ErrorValidacion(1, "estructura", f"faltan columnas requeridas: {', '.join(faltan)}")]
        ids_vistos = {}
        for fila_num, campos in enumerate(lector, start=2):
            if not campos:  # línea en blanco
                errores.append(ErrorValidacion(fila_num, "estructura", "fila vacía"))
                continue
            if len(campos) != len(cabecera):
                errores.append(ErrorValidacion(
                    fila_num, "estructura",
                    f"se esperaban {len(cabecera)} campos y hay {len(campos)}"))
                continue
            fila = dict(zip(cabecera, campos))
            reg, errs = convertir_fila(fila)
            for campo, motivo in errs:
                errores.append(ErrorValidacion(fila_num, campo, motivo))
            if reg["id"] is not None:
                if reg["id"] in ids_vistos:
                    errores.append(ErrorValidacion(
                        fila_num, "id",
                        f"identificador {reg['id']} duplicado (ya aparece en la fila {ids_vistos[reg['id']]})"))
                else:
                    ids_vistos[reg["id"]] = fila_num
            reg["_fila"] = fila_num
            registros.append(reg)
    return registros, errores


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    ruta = argv[0] if argv else "datos/meteoritos.csv"
    registros, errores = validar_archivo(ruta)
    if errores:
        print(f"VALIDACIÓN FALLIDA: {len(errores)} error(es) en {ruta}", file=sys.stderr)
        for e in errores:
            print(f"  - {e}", file=sys.stderr)
            print(f"::error title=CSV inválido::{e}")  # anotación visible en GitHub Actions
        return 1
    print(f"Validación correcta: {len(registros)} registros en {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
