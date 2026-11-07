"""Pruebas con conjuntos de datos pequeños, independientes de datos/meteoritos.csv."""
import pytest

from analisis import calcular_indicadores, cargar, DatosInvalidos
from validacion import extraer_anio, validar_archivo

CABECERA = "id,name,recclass,mass (g),fall,year,reclat,reclong\n"


def escribir(tmp_path, filas):
    ruta = tmp_path / "t.csv"
    ruta.write_text(CABECERA + "".join(f + "\n" for f in filas), encoding="utf-8")
    return ruta


def test_registro_valido(tmp_path):
    ruta = escribir(tmp_path, ["1,Aachen,L5,21,Fell,01/01/1880 12:00:00 AM,50.775,6.08333"])
    registros, errores = validar_archivo(ruta)
    assert errores == []
    assert registros[0]["id"] == 1
    assert registros[0]["year"] == 1880
    assert registros[0]["mass (g)"] == 21.0


def test_indicadores_con_resultado_conocido(tmp_path):
    ruta = escribir(tmp_path, [
        "1,A,L5,10,Fell,1900,1,1",
        "2,B,L5,30,Found,1950,2,2",
        "3,C,H6,,Found,,,",
    ])
    ind = calcular_indicadores(cargar(ruta))
    assert ind["total"] == 3
    assert ind["fell"] == 1 and ind["found"] == 2
    assert ind["masa_media"] == 20.0          # (10 + 30) / 2, sin contar el faltante
    assert ind["top_clases"][0] == ("L5", 2)
    assert ind["top_masa"][0]["name"] == "B"
    assert ind["ultimos"][-1]["name"] == "C"


def test_dato_faltante_no_es_cero(tmp_path):
    ruta = escribir(tmp_path, ["1,A,L5,,Fell,,,", "2,B,L5,NA,Found,,0,0"])
    registros, errores = validar_archivo(ruta)
    assert errores == []
    assert registros[0]["mass (g)"] is None and registros[0]["reclat"] is None
    assert registros[1]["mass (g)"] is None
    assert registros[1]["reclat"] == 0.0 and registros[1]["reclong"] == 0.0  # 0 es coordenada válida
    ind = calcular_indicadores(registros)
    assert ind["sin_masa"] == 2 and ind["masa_media"] is None


def test_rechaza_masa_negativa(tmp_path):
    ruta = escribir(tmp_path, ["1,A,L5,-5,Fell,1900,1,1"])
    _, errores = validar_archivo(ruta)
    assert [(e.fila, e.campo) for e in errores] == [(2, "mass (g)")]
    with pytest.raises(DatosInvalidos):
        cargar(ruta)


@pytest.mark.parametrize("lat,lon,campo", [("91", "0", "reclat"), ("-90.5", "0", "reclat"),
                                           ("0", "181", "reclong"), ("0", "-200", "reclong")])
def test_rechaza_coordenadas_fuera_de_rango(tmp_path, lat, lon, campo):
    ruta = escribir(tmp_path, [f"1,A,L5,1,Fell,1900,{lat},{lon}"])
    _, errores = validar_archivo(ruta)
    assert [e.campo for e in errores] == [campo]


def test_rechaza_id_duplicado(tmp_path):
    ruta = escribir(tmp_path, ["1,A,L5,1,Fell,1900,1,1", "2,B,L5,1,Fell,1900,1,1", "1,C,L5,1,Fell,1900,1,1"])
    _, errores = validar_archivo(ruta)
    assert len(errores) == 1
    assert errores[0].fila == 4 and errores[0].campo == "id" and "duplicado" in errores[0].motivo


def test_otras_reglas(tmp_path):
    ruta = escribir(tmp_path, [
        "0,A,L5,1,Fell,1900,1,1",        # id no positivo
        "2,  ,L5,1,Fell,1900,1,1",       # name vacío tras quitar espacios
        "3,C,L5,1,Lost,1900,1,1",        # fall inválido
        "4,D,L5,1,Fell,2027,1,1",        # año fuera de rango
        "5,E,L5,inf,Fell,1900,1,1",      # masa no finita
        "6,F,L5,1,Fell",                 # campos de menos
    ])
    _, errores = validar_archivo(ruta)
    assert [(e.fila, e.campo) for e in errores] == [
        (2, "id"), (3, "name"), (4, "fall"), (5, "year"), (6, "mass (g)"), (7, "estructura")]


def test_estructura_columnas_faltantes(tmp_path):
    ruta = tmp_path / "t.csv"
    ruta.write_text("id,name\n1,A\n", encoding="utf-8")
    _, errores = validar_archivo(ruta)
    assert errores and errores[0].campo == "estructura"


@pytest.mark.parametrize("texto,esperado", [("1880", 1880), ("01/01/1880 12:00:00 AM", 1880),
                                            ("1880-01-01", 1880), ("abc", None)])
def test_extraer_anio(texto, esperado):
    assert extraer_anio(texto) == esperado
