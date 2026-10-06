"""Diagnóstico: ¿cuántos conciertos más habría con un horizonte más largo que el actual (pipeline.HORIZONTE_DIAS)?
Lee todas las fuentes con un horizonte de un año, como la lectura diaria (robots.txt, ritmo, mismo lector) pero sin
guardar nada, y cuenta por web los conciertos a más de 120, 150, 180, 240 y 365 días, y cuánto tarda cada web
comparado con su última lectura normal (estado.json). Solo escribe en la salida.

Uso: python tools/diagnostico_horizonte.py [ids de fuentes que no leer, separados por comas]
"""
import copy
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper import pipeline  # noqa: E402
from scraper.fetch import Fetcher  # noqa: E402
from scraper.registry import FUENTES  # noqa: E402

SIN = set(filter(None, (sys.argv[1] if len(sys.argv) > 1 else "").split(",")))
CORTES = [120, 150, 180, 240, 365]
hoy = date.today()
estado = json.loads((pipeline.DATA / "estado.json").read_text()) if (pipeline.DATA / "estado.json").exists() else {}
antes = (estado.get("fuentes") or {}).get("_duracion") or {}
fuentes = [s for s in FUENTES if s.id not in SIN]
t0 = time.monotonic()
eventos, resultados = pipeline.rastrear(fuentes, Fetcher(), hoy, hoy + timedelta(days=365),
                                        copy.deepcopy(estado.get("fuentes") or {}), pausa_reintento=5)
print(f"\nLectura con horizonte de 365 días: {time.monotonic() - t0:.0f} s ({len(fuentes)} fuentes; sin leer: {sorted(SIN)})")

por_web = defaultdict(Counter)
total = Counter()
for sid, evs in eventos.items():
    for e in evs:
        dias = (e.fecha - hoy).days
        tramo = next((c for c in CORTES if dias <= c), 9999)
        por_web[sid][tramo] += 1
        total[tramo] += 1

print("\n## Conciertos leídos por distancia (días desde hoy), sin unir duplicados entre webs")
print("hasta 120 (lo de ahora) | 121-150 | 151-180 | 181-240 | 241-365")
print(" | ".join(str(total[c]) for c in CORTES))
print("\n## Webs con conciertos a más de 120 días")
print("web | ≤120 | 121-150 | 151-180 | 181-240 | 241-365 | segundos ahora (365) | segundos última lectura (120)")
for sid, k in sorted(por_web.items(), key=lambda kv: -sum(v for t, v in kv[1].items() if t > 120)):
    mas = sum(v for t, v in k.items() if t > 120)
    if not mas:
        continue
    seg = resultados.get(sid, {}).get("segundos", 0)
    print(f"{sid} | " + " | ".join(str(k[c]) for c in CORTES) + f" | {seg:.0f} | {float(antes.get(sid, 0)):.0f}")
print("\n## Webs que tardan bastante más que en la lectura normal")
for sid, r in sorted(resultados.items(), key=lambda kv: -kv[1].get("segundos", 0)):
    seg, prev = r.get("segundos", 0), float(antes.get(sid, 0))
    if seg > max(60, prev * 1.5):
        print(f"- {sid}: {seg:.0f} s (normal: {prev:.0f} s) · {r.get('estado')}")
print("\n## Webs que fallaron en esta lectura")
for sid, r in resultados.items():
    if not r.get("funciono"):
        print(f"- {sid}: {r.get('estado')} {str(r.get('error') or '')[:120]}")
