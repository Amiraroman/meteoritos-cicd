"""Genera el informe web estático en public/index.html a partir del CSV."""
import argparse
import os
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

from analisis import DatosInvalidos, calcular_indicadores, cargar

PREFIJO_SIMULADO = "SIM-"  # convención: registros simulados llevan este prefijo en name
FUENTE_URL = "https://data.nasa.gov/dataset/meteorite-landings"


def fmt_num(n, dec=0):
    if n is None:
        return "—"
    s = f"{n:,.{dec}f}"
    return s.replace(",", " ")  # separador de miles por espacio


def fmt_dato(v):
    return "—" if v is None else escape(str(v))


def es_simulado(reg):
    return reg["name"].startswith(PREFIJO_SIMULADO)


def nombre_html(reg):
    ins = ' <span class="sim">simulado</span>' if es_simulado(reg) else ""
    return escape(reg["name"]) + ins


def construir_html(ind, estudiante, commit, generado):
    maximo = max((n for _, n in ind["top_clases"]), default=1)
    barras = "\n".join(
        f'<div class="barra"><span class="et">{escape(c)}</span>'
        f'<span class="pista"><span class="rel" style="width:{100 * n / maximo:.1f}%"></span></span>'
        f'<span class="val">{fmt_num(n)}</span></div>'
        for c, n in ind["top_clases"]
    )
    filas_masa = "\n".join(
        f"<tr><td>{i}</td><td>{nombre_html(r)}</td><td>{escape(r['recclass'])}</td>"
        f"<td class='num'>{fmt_num(r['mass (g)'], 1)}</td></tr>"
        for i, r in enumerate(ind["top_masa"], 1)
    )
    filas_ult = "\n".join(
        f"<tr><td>{r['id']}</td><td>{nombre_html(r)}</td><td>{escape(r['recclass'])}</td>"
        f"<td class='num'>{fmt_num(r['mass (g)'], 1)}</td><td>{r['fall']}</td>"
        f"<td>{fmt_dato(r['year'])}</td><td>{fmt_dato(r['reclat'])}</td><td>{fmt_dato(r['reclong'])}</td></tr>"
        for r in ind["ultimos"]
    )
    commit_corto = escape(commit[:7]) if commit else "local"
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Meteoritos — informe CI/CD</title>
<style>
 body {{ font-family: system-ui, sans-serif; margin: 0; background: #f5f6f8; color: #1d2330; line-height: 1.5; }}
 header {{ background: #1d2330; color: #fff; padding: 24px 16px; }}
 header h1 {{ margin: 0 0 4px; font-size: 1.6rem; }}
 main {{ max-width: 960px; margin: 0 auto; padding: 16px; }}
 section {{ background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
 h2 {{ margin-top: 0; font-size: 1.2rem; }}
 .aviso {{ background: #fff4d6; border-left: 4px solid #e0a800; padding: 8px 12px; }}
 .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }}
 .kpi {{ background: #f0f3f9; border-radius: 6px; padding: 12px; }}
 .kpi b {{ display: block; font-size: 1.5rem; }}
 .kpi small {{ color: #555; }}
 .barra {{ display: flex; align-items: center; gap: 8px; margin: 4px 0; }}
 .et {{ width: 80px; flex: none; font-size: .9rem; }}
 .pista {{ flex: 1; background: #e6e9f0; border-radius: 4px; height: 18px; }}
 .rel {{ display: block; height: 100%; background: #3b6fd4; border-radius: 4px; }}
 .val {{ width: 64px; text-align: right; flex: none; font-variant-numeric: tabular-nums; }}
 .tabla {{ overflow-x: auto; }}
 table {{ border-collapse: collapse; width: 100%; font-size: .9rem; }}
 th, td {{ border-bottom: 1px solid #e1e4ea; padding: 6px 8px; text-align: left; white-space: nowrap; }}
 td.num {{ text-align: right; }}
 .sim {{ background: #e0a800; color: #000; font-size: .7rem; padding: 1px 6px; border-radius: 8px; }}
 footer {{ font-size: .85rem; color: #555; }}
</style>
</head>
<body>
<header>
 <h1>Meteoritos: validación y publicación automática</h1>
 <div>Estudiante: {escape(estudiante)}</div>
</header>
<main>
<section>
 <h2>Fuente de los datos</h2>
 <p>Meteorite Landings (NASA Open Data Portal, datos de The Meteoritical Society):
 <a href="{FUENTE_URL}">{FUENTE_URL}</a>. Muestra: primeras 20 000 filas de datos.</p>
 <p class="aviso"><b>Aviso:</b> los registros cuyo nombre empieza por «{PREFIJO_SIMULADO}» son
 <b>simulaciones educativas</b> añadidas para probar el sistema; no son datos reales de la NASA.</p>
</section>
<section>
 <h2>Indicadores</h2>
 <div class="kpis">
  <div class="kpi"><b>{fmt_num(ind['total'])}</b><small>Registros totales</small></div>
  <div class="kpi"><b>{fmt_num(ind['fell'])}</b><small>Fell (caída observada)</small></div>
  <div class="kpi"><b>{fmt_num(ind['found'])}</b><small>Found (hallazgo posterior)</small></div>
  <div class="kpi"><b>{fmt_num(ind['masa_media'], 2)} g</b><small>Masa media (solo valores disponibles)</small></div>
  <div class="kpi"><b>{fmt_num(ind['sin_masa'])}</b><small>Registros sin masa</small></div>
 </div>
</section>
<section>
 <h2>Diez clasificaciones más frecuentes</h2>
 <p>Cantidad de meteoritos por clasificación (recclass).</p>
 {barras}
</section>
<section>
 <h2>Diez meteoritos de mayor masa</h2>
 <div class="tabla"><table>
  <tr><th>#</th><th>Nombre</th><th>Clasificación</th><th>Masa (g)</th></tr>
  {filas_masa}
 </table></div>
</section>
<section>
 <h2>Últimos diez registros del CSV</h2>
 <div class="tabla"><table>
  <tr><th>id</th><th>Nombre</th><th>Clasificación</th><th>Masa (g)</th><th>Fall</th><th>Año</th><th>Latitud (°)</th><th>Longitud (°)</th></tr>
  {filas_ult}
 </table></div>
</section>
<footer>
 Generado: {escape(generado)} · Commit publicado: <code>{commit_corto}</code>
</footer>
</main>
</body>
</html>
"""


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default="datos/meteoritos.csv")
    p.add_argument("--salida", default="public")
    p.add_argument("--estudiante", default=os.environ.get("ESTUDIANTE", "NOMBRE DEL ESTUDIANTE"))
    p.add_argument("--commit", default=os.environ.get("GITHUB_SHA", ""))
    a = p.parse_args(argv)
    try:
        registros = cargar(a.csv)
    except DatosInvalidos as e:
        print(f"No se genera el sitio, CSV inválido:\n{e}")
        return 1
    ind = calcular_indicadores(registros)
    bolivia = timezone(timedelta(hours=-4))
    generado = datetime.now(bolivia).strftime("%Y-%m-%d %H:%M:%S (hora de Bolivia)")
    salida = Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "index.html").write_text(construir_html(ind, a.estudiante, a.commit, generado), encoding="utf-8")
    (salida / ".nojekyll").write_text("")
    print(f"Sitio generado en {salida / 'index.html'} ({ind['total']} registros)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
