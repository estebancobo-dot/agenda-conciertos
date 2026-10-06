"""Diagnóstico: qué webs de sala (data/salas_alias.json → "web") publican sus conciertos con datos estructurados
(schema.org Event en JSON-LD), que se pueden leer sin un lector propio para cada sala. Por cada web: la página
donde los encuentra, cuántos eventos futuros, cuántos con hora, con precio y con enlace de entradas. Respeta
robots.txt (el mismo lector que las agendas). Solo escribe en la salida.

Uso: python tools/diagnostico_salas_web.py [minutos máx.]
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper.salas_web import eventos_de_web, paginas_candidatas  # noqa: E402
from scraper.fetch import Fetcher  # noqa: E402

MINUTOS = float(sys.argv[1]) if len(sys.argv) > 1 else 14
fin = time.monotonic() + MINUTOS * 60
salas = [s for s in json.load(open(Path(__file__).resolve().parent.parent / "data" / "salas_alias.json"))["salas"]
         if s.get("web")]
hoy = time.strftime("%Y-%m-%d")
f = Fetcher()


def medir(s: dict) -> dict:
    out = {"sala": s["nombre"], "web": s["web"], "paginas": [], "eventos": []}
    for u in paginas_candidatas(s["web"]):
        if time.monotonic() > fin:
            break
        try:
            evs = eventos_de_web(f.get(u), u)
        except Exception as e:  # noqa: BLE001
            out["paginas"].append(f"{u} ({type(e).__name__})")
            continue
        futuros = [e for e in evs if e["fecha"] >= hoy]
        out["paginas"].append(f"{u} ({len(futuros)})")
        if len(futuros) > len(out["eventos"]):
            out["eventos"], out["mejor"] = futuros, u
    return out


with ThreadPoolExecutor(max_workers=8) as ex:
    filas = list(ex.map(medir, salas))
print("\n## Webs de sala con conciertos en datos estructurados\n")
print("sala | eventos futuros | con hora | con precio | con entradas | página")
for x in sorted(filas, key=lambda x: -len(x["eventos"])):
    e = x["eventos"]
    if e:
        print(f"{x['sala']} | {len(e)} | {sum(bool(v.get('hora')) for v in e)} | {sum(bool(v.get('precio')) for v in e)} | "
              f"{sum(bool(v.get('entradas')) for v in e)} | {x.get('mejor')}")
print("\n## Sin datos estructurados\n")
for x in filas:
    if not x["eventos"]:
        print(f"- {x['sala']}: {'; '.join(x['paginas'])[:200]}")
print("\n## Ejemplos")
for x in [x for x in filas if x["eventos"]][:12]:
    for v in x["eventos"][:2]:
        print(f"- [{x['sala']}] {v}")
