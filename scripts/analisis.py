"""Cálculo de indicadores a partir del CSV (siempre desde el archivo de datos)."""
from collections import Counter

from validacion import validar_archivo


class DatosInvalidos(Exception):
    pass


def cargar(ruta):
    """Valida y devuelve los registros. Lanza DatosInvalidos si hay errores."""
    registros, errores = validar_archivo(ruta)
    if errores:
        raise DatosInvalidos("\n".join(str(e) for e in errores))
    return registros


def calcular_indicadores(registros, n_top=10):
    masas = [r["mass (g)"] for r in registros if r["mass (g)"] is not None]
    clases = Counter(r["recclass"] for r in registros)
    # desempate estable: más frecuentes primero, luego por nombre de clase
    top_clases = sorted(clases.items(), key=lambda kv: (-kv[1], kv[0]))[:n_top]
    con_masa = [r for r in registros if r["mass (g)"] is not None]
    top_masa = sorted(con_masa, key=lambda r: (-r["mass (g)"], r["id"]))[:n_top]
    return {
        "total": len(registros),
        "fell": sum(1 for r in registros if r["fall"] == "Fell"),
        "found": sum(1 for r in registros if r["fall"] == "Found"),
        "masa_media": (sum(masas) / len(masas)) if masas else None,
        "sin_masa": len(registros) - len(masas),
        "top_clases": top_clases,
        "top_masa": top_masa,
        "ultimos": registros[-n_top:],
    }
